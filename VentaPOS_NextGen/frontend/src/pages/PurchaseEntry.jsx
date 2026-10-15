import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api';
import { fmt } from '../utils/formatUtils';
import { IconShoppingCart, IconFileInvoice, IconTrash, IconDeviceFloppy } from '@tabler/icons-react';

// ── Arabic Digits Conversion Helpers ──────────────────────────────────────────


const toEnglish = (str) => {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(/×/g, '*')
    .replace(/،/g, ',');
};

// ── Suggestion List Component ────────────────────────────────────────────────
const SuggestionList = ({ open, suggestions, activeIndex, onSelect }) => {
  if (!open || !suggestions.length) return null;
  const activeItemRef = useRef(null);
  
  useEffect(() => {
    if (open && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex, open]);

  return (
    <ul tabIndex="-1" className="list-group shadow position-absolute w-100 bg-white"
      onMouseDown={(e) => e.preventDefault()}
      style={{ zIndex: 1055, top: '100%', maxHeight: 200, overflowY: 'auto', border: '1px solid #d8dee4' }}>
      {suggestions.map((s, i) => (
        <li
          key={i}
          className={`list-group-item list-group-item-action py-2 cursor-pointer border-bottom ${i === activeIndex ? '' : 'bg-white'}`} style={i === activeIndex ? { backgroundColor: '#f1f5f9', color: '#1e293b' } : {}}
          onMouseDown={() => onSelect(s)}
          ref={i === activeIndex ? activeItemRef : null}
        >
          {typeof s === 'string' ? s : (
            <>
              <div className="fw-bold">{s.name || s.value || ''}</div>
            </>
          )}
        </li>
      ))}
    </ul>
  );
};

const PurchaseEntry = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Invoice Data
  const [invoiceType, setInvoiceType] = useState('PURCHASE');
  const [supplierId, setSupplierId] = useState('');
  const [supplierQuery, setSupplierQuery] = useState('');
  const [invoiceMonth, setInvoiceMonth] = useState(new Date().getMonth() + 1);
  const [invoiceYear, setInvoiceYear] = useState(new Date().getFullYear());
  
  // Current Item to Add
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productQuery, setProductQuery] = useState('');
  const [quantity, setQuantity] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');

  // Added Items
  const [items, setItems] = useState([]);
  
  // Saving state
  const [saving, setSaving] = useState(false);

  // ── Autocomplete / Suggestions State
  const [suggestions, setSuggestions] = useState([]);
  const [activeInput, setActiveInput] = useState(''); // 'supplier', 'product'
  const [activeIndex, setActiveIndex] = useState(-1);
  const blurTimerRef = useRef(null);

  // ── Refs for Keyboard Navigation ──
  const supplierRef = useRef(null);
  const monthRef = useRef(null);
  const yearRef = useRef(null);
  const prodQueryRef = useRef(null);
  const qtyRef = useRef(null);
  const priceRef = useRef(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [suppliersRes, productsRes] = await Promise.all([
          api.get('/suppliers/').catch(() => ({ data: [] })),
          api.get('/inventory-items/?limit=5000').catch(() => ({ data: [] }))
        ]);
        const suppData = suppliersRes.data?.results || suppliersRes.data;
        const prodData = productsRes.data?.results || productsRes.data;
        
        const supps = Array.isArray(suppData) ? suppData : [];
        const prods = Array.isArray(prodData) ? prodData : [];
        setSuppliers(supps);
        setProducts(prods);

        // If in edit mode, fetch the invoice
        if (id) {
          const invRes = await api.get(`/purchase-invoices/${id}/`);
          const inv = invRes.data;
          
          setInvoiceType(inv.invoice_type || 'PURCHASE');
          setSupplierId(inv.supplier || '');
          const existingSupplier = supps.find(s => s.id === inv.supplier);
          if (existingSupplier) setSupplierQuery(existingSupplier.name);
          
          setInvoiceMonth(inv.invoice_month || new Date().getMonth() + 1);
          setInvoiceYear(inv.invoice_year || new Date().getFullYear());
          
          if (inv.items) {
            const mappedItems = inv.items.map(i => {
              const p = prods.find(pr => pr.id === i.inventory_item);
              return {
                id: i.id || Date.now() + Math.random(),
                inventory_item: i.inventory_item,
                productName: p ? p.name : `صنف #${i.inventory_item}`,
                quantity: i.quantity,
                purchase_price: i.purchase_price
              };
            });
            setItems(mappedItems);
          }
        }
      } catch (err) {
        console.error("Error fetching initial data", err);
      } finally {
        setLoadingInitial(false);
        setTimeout(() => {
          supplierRef.current?.focus();
        }, 150);
      }
    };
    fetchInitialData();
  }, [id]);

  // ── Dynamic Suggestions Search (Local Array Filtering) ─────────────────────
  const triggerSuggestions = (val, fieldType) => {
    clearTimeout(blurTimerRef.current);
    const term = toEnglish(val).trim().toLowerCase();

    if (fieldType === 'supplier') {
      const filtered = suppliers.filter(s => s.name && s.name.toLowerCase().includes(term));
      setSuggestions(filtered.slice(0, 10)); // Limit to 10 for performance
      setActiveInput(fieldType);
      setActiveIndex(-1);
    } else if (fieldType === 'product') {
      const filtered = products.filter(p => p.name && p.name.toLowerCase().includes(term));
      setSuggestions(filtered.slice(0, 10));
      setActiveInput(fieldType);
      setActiveIndex(-1);
    }
  };

  const handleSuggestionSelect = (item, fieldType) => {
    if (fieldType === 'supplier') {
      setSupplierId(item.id);
      setSupplierQuery(item.name);
      setTimeout(() => monthRef.current?.focus(), 50);
    } else if (fieldType === 'product') {
      setSelectedProduct(item);
      setProductQuery(item.name);
      
      // Fetch available quantity if it's a RETURN
      if (invoiceType === 'RETURN') {
        api.get(`/inventory-items/${item.id}/stock/?month=${invoiceMonth}&year=${invoiceYear}`)
           .then(res => {
             if (res.data && res.data.safe_available_qty !== undefined) {
               const existing = items.find(i => i.inventory_item === item.id);
               const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
               setSelectedProduct(prev => prev && prev.id === item.id ? { 
                 ...prev, 
                 safe_qty: remaining,
                 bottleneck_month: res.data.bottleneck_month,
                 bottleneck_year: res.data.bottleneck_year
               } : prev);
             }
           }).catch(() => {});
      }

      // Wait a bit, then move focus to Quantity
      setTimeout(() => qtyRef.current?.focus(), 50);
    }
    setSuggestions([]);
    setActiveInput('');
    setActiveIndex(-1);
  };

  const handleKeyDown = (e, fieldType) => {
    if (activeInput !== fieldType || !suggestions.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex > -1) {
        handleSuggestionSelect(suggestions[activeIndex], fieldType);
      } else if (suggestions.length > 0) {
        handleSuggestionSelect(suggestions[0], fieldType);
      }
    }
  };

  const handleCartKD = (e, nextRef) => { 
    if (e.key === 'Enter') { 
      e.preventDefault(); 
      nextRef.current?.focus(); 
    } 
  };

  const handleAddItem = async () => {
    const qtyEng = toEnglish(quantity);
    const priceEng = toEnglish(purchasePrice);

    let currentProduct = selectedProduct;
    // If the user typed exactly a product name but didn't select from dropdown
    if (!currentProduct && productQuery.trim() !== '') {
      const exactMatch = products.find(p => p.name === productQuery.trim());
      if (exactMatch) {
        currentProduct = exactMatch;
      } else {
        toast.error('يرجى اختيار منتج مسجل أولاً.');
        prodQueryRef.current?.focus();
        return;
      }
    } else if (!currentProduct) {
      toast.error('يرجى اختيار منتج مسجل أولاً.');
      prodQueryRef.current?.focus();
      return;
    }

    if (!qtyEng || parseInt(qtyEng) < 1) {
      toast.error('الكمية يجب أن تكون 1 على الأقل.');
      qtyRef.current?.focus();
      return;
    }

    if (!priceEng || parseFloat(priceEng) <= 0) {
      toast.error('أدخل سعر صحيح.');
      priceRef.current?.focus();
      return;
    }

    const reqQty = parseInt(qtyEng);
    let safeQty = currentProduct.safe_qty;

    if (invoiceType === 'RETURN') {
      if (safeQty !== undefined) {
        if (reqQty > safeQty) {
          toast.error(`الكمية المطلوبة أكبر من المتاح: ${safeQty}`);
          return;
        }
      } else {
        // Fallback fetch if not loaded yet
        let retries = 3;
        while (retries > 0) {
          try {
            const res = await api.get(`/inventory-items/${currentProduct.id}/stock/?month=${invoiceMonth}&year=${invoiceYear}`);
            if (res.data && res.data.safe_available_qty !== undefined) {
              const existing = items.find(i => i.inventory_item === currentProduct.id);
              safeQty = res.data.safe_available_qty - (existing ? existing.quantity : 0);
              if (reqQty > safeQty) {
                toast.error(`الكمية المطلوبة أكبر من المتاح: ${safeQty}`);
                return;
              }
            }
            break;
          } catch {
            retries--;
            if (retries > 0) await new Promise(r => setTimeout(r, 50));
          }
        }
      }
    }

    const existing = items.find(i => i.inventory_item === currentProduct.id);

    if (existing) {
      setItems(items.map(i => i.inventory_item === currentProduct.id
        ? { ...i, quantity: reqQty + i.quantity, purchase_price: parseFloat(priceEng) } : i));
    } else {
      setItems([...items, {
        id: Date.now(),
        inventory_item: currentProduct.id,
        productName: currentProduct.name,
        quantity: reqQty,
        purchase_price: parseFloat(priceEng)
      }]);
    }
    
    // Reset current item fields and focus back to product input
    setSelectedProduct(null);
    setProductQuery('');
    setQuantity('');
    setPurchasePrice('');
    
    setTimeout(() => {
      prodQueryRef.current?.focus();
    }, 50);
  };

  const handleRemoveItem = (itemId) => {
    setItems(items.filter(item => item.id !== itemId));
  };

  const totalAmount = items.reduce((sum, item) => sum + (item.quantity * item.purchase_price), 0);

  const handleSaveInvoice = async () => {
    if (!supplierId) {
      toast.error('برجاء اختيار المورد.');
      supplierRef.current?.focus();
      return;
    }
    if (items.length === 0) {
      toast.error('برجاء إضافة أصناف للفاتورة.');
      prodQueryRef.current?.focus();
      return;
    }

    const payload = {
      supplier: parseInt(supplierId),
      invoice_type: invoiceType,
      invoice_month: parseInt(toEnglish(invoiceMonth)),
      invoice_year: parseInt(toEnglish(invoiceYear)),
      items: items.map(item => ({
        inventory_item: item.inventory_item,
        quantity: item.quantity,
        purchase_price: item.purchase_price
      }))
    };

    try {
      setSaving(true);
      if (id) {
        await api.put(`/purchase-invoices/${id}/`, payload);
        toast.success('تم تحديث الفاتورة بنجاح');
      } else {
        await api.post('/purchase-invoices/', payload);
        toast.success('تم حفظ الفاتورة بنجاح');
      }
      navigate('/search-purchases');
    } catch (err) {
      console.error("Error saving invoice", err);
      toast.error(err.response?.data?.error || 'حصل مشكلة أثناء حفظ الفاتورة.');
    } finally {
      setSaving(false);
    }
  };

  if (loadingInitial) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <div className="spinner-border text-primary" role="status"></div>
      </div>
    );
  }

  return (
    <div className="container-fluid pb-3 px-3 fs-3 pt-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      
      {/* ── Page Header ── */}
      <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle" style={{ borderColor: '#dee2e6 !important' }}>
        <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
          <IconFileInvoice size={28} className="text-primary" />
          {id ? 'تعديل فاتورة / مرتجع مصنع' : 'إضافة فاتورة مشتريات / مرتجع مصنع'}
        </h2>
        <div className="d-flex align-items-center gap-2">
          <Link to="/search-purchases" className="btn btn-outline-secondary fw-bold border-secondary-subtle py-2">
            العودة للدفتر
          </Link>
        </div>
      </div>


      {/* ── Top Card: Invoice Meta (Supplier, Date, Type) ── */}
      <div className="card premium-card mb-2" style={{ position: 'relative', zIndex: 30 }}>
        <div className="card-body p-3">
          <div className="row g-2 align-items-center">
            
            <div className="col-auto">
              <label className="col-form-label fw-bold text-dark">نوع الفاتورة</label>
            </div>
            <div className="col-auto">
              <div className="d-flex gap-3 align-items-center h-100 px-2 py-1 border rounded bg-light border-secondary-subtle">
                <label className="form-check m-0 cursor-pointer d-flex align-items-center gap-1">
                  <input className="form-check-input mt-0" type="radio" name="invoiceType" 
                    checked={invoiceType === 'PURCHASE'} 
                    onChange={() => setInvoiceType('PURCHASE')} />
                  <span className="form-check-label fw-bold text-success fs-4">شراء</span>
                </label>
                <label className="form-check m-0 cursor-pointer d-flex align-items-center gap-1">
                  <input className="form-check-input mt-0" type="radio" name="invoiceType" 
                    checked={invoiceType === 'RETURN'} 
                    onChange={() => {
                      setInvoiceType('RETURN');
                      // Clear items if we toggle to avoid bad state
                      setItems([]);
                    }} />
                  <span className="form-check-label fw-bold text-danger fs-4">مرتجع</span>
                </label>
              </div>
            </div>

            <div className="col-auto ms-2">
              <label className="col-form-label fw-bold text-dark">المورد</label>
            </div>
            <div className="col d-flex align-items-center">
              <div className="position-relative flex-grow-1">
                <input
                  type="text"
                  ref={supplierRef}
                  className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                  value={supplierQuery}
                  autoComplete="off"
                  onChange={e => {
                    setSupplierQuery(e.target.value);
                    setSupplierId(''); // Clear ID if user types manually
                    triggerSuggestions(e.target.value, 'supplier');
                  }}
                  onKeyDown={e => handleKeyDown(e, 'supplier')}
                  onBlur={() => {
                    blurTimerRef.current = setTimeout(() => {
                      if (supplierQuery.trim() !== '') {
                        const exactMatch = suppliers.find(s => s.name === supplierQuery.trim());
                        if (exactMatch) {
                          setSupplierId(exactMatch.id);
                          setSupplierQuery(exactMatch.name);
                        }
                      }
                      setSuggestions([]);
                      setActiveInput('');
                    }, 200);
                  }}
                  placeholder="ابحث عن مورد..."
                  onFocus={() => triggerSuggestions(supplierQuery, 'supplier')}
                  style={{ borderColor: '#adb5bd' }}
                />
                <SuggestionList
                  open={activeInput === 'supplier'}
                  suggestions={suggestions}
                  activeIndex={activeIndex}
                  onSelect={s => handleSuggestionSelect(s, 'supplier')}
                />
              </div>
            </div>

            <div className="col-auto ms-2">
              <label className="col-form-label fw-bold text-dark">الشهر</label>
            </div>
            <div className="col-1">
              <input 
                ref={monthRef}
                type="number" 
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
                value={invoiceMonth} 
                min="1"
                max="12"
                onChange={(e) => {
                  const v = parseInt(e.target.value);
                  if (v >= 1 && v <= 12) setInvoiceMonth(v);
                  else if (e.target.value === '') setInvoiceMonth('');
                }} 
                onKeyDown={(e) => handleCartKD(e, yearRef)}
                style={{ borderColor: '#adb5bd' }} 
              />
            </div>
            <div className="col-auto">
              <label className="col-form-label fw-bold text-dark">السنة</label>
            </div>
            <div className="col-1">
              <input 
                ref={yearRef}
                type="number" 
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
                value={invoiceYear} 
                min="2000"
                onChange={(e) => setInvoiceYear(e.target.value)} 
                onKeyDown={(e) => handleCartKD(e, prodQueryRef)}
                style={{ borderColor: '#adb5bd' }} 
              />
            </div>

          </div>
        </div>
      </div>

      {/* ── Middle Card: Products Section ── */}
      <div className="card premium-card mb-2" style={{ position: 'relative', zIndex: 20 }}>
        
        {/* Product Entry Bar */}
        <div className="card-body p-2 border-bottom bg-light" style={{ borderColor: '#dee2e6 !important', borderRadius: 'var(--bs-border-radius) var(--bs-border-radius) 0 0' }}>
          <div className="row g-2 align-items-center">
            
            <div className="col-auto">
              <label className="form-label fw-bold text-dark mb-0">الصنف</label>
            </div>
            <div className="col">
              <div className="position-relative">
                <input
                  ref={prodQueryRef}
                  type="text"
                  className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                  value={productQuery}
                  autoComplete="off"
                  onChange={e => {
                    const val = e.target.value;
                    setProductQuery(val);
                    if (selectedProduct && selectedProduct.name !== val) {
                      setSelectedProduct(null);
                    }
                    triggerSuggestions(val, 'product');
                  }}
                  onKeyDown={e => handleKeyDown(e, 'product')}
                  onFocus={() => triggerSuggestions(productQuery, 'product')}
                  onBlur={() => { 
                    if (!selectedProduct && productQuery.trim() !== '') {
                      const exactMatch = products.find(p => p.name === productQuery.trim());
                      if (exactMatch) {
                        setSelectedProduct(exactMatch);
                        // Fetch available quantity if it's a RETURN
                        if (invoiceType === 'RETURN') {
                          api.get(`/inventory-items/${exactMatch.id}/stock/?month=${invoiceMonth}&year=${invoiceYear}`)
                            .then(res => {
                              if (res.data && res.data.safe_available_qty !== undefined) {
                                const existing = items.find(i => i.inventory_item === exactMatch.id);
                                const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
                                setSelectedProduct(prev => prev && prev.id === exactMatch.id ? { 
                                  ...prev, 
                                  safe_qty: remaining,
                                  bottleneck_month: res.data.bottleneck_month,
                                  bottleneck_year: res.data.bottleneck_year
                                } : prev);
                              }
                            }).catch(() => {});
                        }
                      }
                    }
                    blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); 
                  }}
                  placeholder="ابحث عن صنف..."
                  style={{ borderColor: '#adb5bd' }}
                />
                <SuggestionList
                  open={activeInput === 'product'}
                  suggestions={suggestions}
                  activeIndex={activeIndex}
                  onSelect={s => handleSuggestionSelect(s, 'product')}
                />
              </div>
            </div>

            <div className="col-auto">
              <label className="form-label fw-bold text-dark mb-0">الكمية</label>
            </div>
            <div className="col-2 position-relative text-center">
              <input 
                ref={qtyRef}
                type="text" 
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
                value={quantity} 
                onChange={(e) => setQuantity(toEnglish(e.target.value))} 
                onKeyDown={(e) => handleCartKD(e, priceRef)}
                dir="ltr"
                style={{ borderColor: '#adb5bd' }} 
              />
              {invoiceType === 'RETURN' && selectedProduct && selectedProduct.safe_qty !== undefined && (
                <div className="position-absolute text-success fw-bold mt-1" style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', left: '50%', transform: 'translateX(-50%)' }}>
                  متاح: {selectedProduct.safe_qty}
                </div>
              )}
            </div>

            <div className="col-auto">
              <label className="form-label fw-bold text-dark mb-0">سعر الشراء</label>
            </div>
            <div className="col-2">
              <input 
                ref={priceRef}
                type="text" 
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
                value={purchasePrice} 
                onChange={(e) => setPurchasePrice(toEnglish(e.target.value))} 
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddItem();
                  }
                }}
                dir="ltr"
                style={{ borderColor: '#adb5bd' }} 
              />
            </div>

            <div className="col-auto">
              <button 
                className="btn btn-primary fw-bold fs-4 d-flex align-items-center gap-1" 
                onClick={handleAddItem}
                style={{ padding: '0.375rem 1rem' }}
              >
                إضافة <IconShoppingCart size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Cart Table */}
        <div className="table-responsive">
          <table className="table table-sm table-vcenter table-hover card-table m-0">
            <thead className="bg-white">
              <tr>
                <th className="fw-bold bg-white text-secondary py-2 fs-5">اسم الصنف</th>
                <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">الكمية</th>
                <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">سعر الشراء</th>
                <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">الإجمالي</th>
                <th className="text-center fw-bold w-1 bg-white text-secondary py-2 fs-5">حذف</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="fw-bold text-primary fs-4">{item.productName}</td>
                  <td className="text-center fw-bold fs-4" dir="ltr">{item.quantity}</td>
                  <td className="text-center fw-bold fs-4" dir="ltr">{item.purchase_price}</td>
                  <td className="text-center fw-bold text-danger fs-4" dir="ltr">{item.quantity * item.purchase_price}</td>
                  <td className="text-center">
                    <button className="btn btn-sm btn-outline-danger fw-bold px-2 py-1" onClick={() => handleRemoveItem(item.id)}>
                      <IconTrash size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center text-muted py-5 fw-bold fs-3">
                    لا يوجد أصناف. يرجى إضافة أصناف للفاتورة.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Bottom Card: Totals & Save ── */}
      <div className="card premium-card bg-light border-secondary-subtle">
        <div className="card-body p-3 d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <div className="fs-2 fw-bold text-dark">الإجمالي:</div>
            <div className="display-6 fw-bolder text-danger" dir="ltr">
              {totalAmount.toLocaleString('en-US')}
            </div>
          </div>
          <div>
            <button 
              className="btn btn-lg fw-bold shadow-sm d-flex justify-content-center align-items-center gap-2 text-white px-5" 
              style={{ backgroundColor: '#1DA368', borderColor: '#1DA368' }}
              onClick={handleSaveInvoice} 
              disabled={saving || items.length === 0}
            >
              <IconDeviceFloppy size={24} />
              {saving ? 'جاري الحفظ...' : (id ? 'تحديث الفاتورة' : 'حفظ الفاتورة')}
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};

export default PurchaseEntry;
