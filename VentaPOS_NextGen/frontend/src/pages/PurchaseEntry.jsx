import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import { fmt } from '../utils/formatUtils';
import { IconShoppingCart, IconFileInvoice, IconTrash, IconDeviceFloppy } from '@tabler/icons-react';

const PurchaseEntry = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Invoice Data
  const [invoiceType, setInvoiceType] = useState('PURCHASE');
  const [supplierId, setSupplierId] = useState('');
  const [invoiceMonth, setInvoiceMonth] = useState(new Date().getMonth() + 1);
  const [invoiceYear, setInvoiceYear] = useState(new Date().getFullYear());
  
  // Current Item to Add
  const [selectedProductId, setSelectedProductId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');

  // Added Items
  const [items, setItems] = useState([]);
  
  // Saving state
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [suppliersRes, productsRes] = await Promise.all([
          api.get('/suppliers/').catch(() => ({ data: [] })),
          api.get('/inventory-items/?limit=1000').catch(() => ({ data: [] }))
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
      }
    };
    fetchInitialData();
  }, [id]);

  const handleAddItem = () => {
    if (!selectedProductId || !quantity || !purchasePrice) {
      alert('برجاء إدخال بيانات الصنف بالكامل.');
      return;
    }

    const product = products.find(p => p.id === fmt(selectedProductId));
    if (!product) return;

    const newItem = {
      id: Date.now(), // temporary id for UI
      inventory_item: fmt(selectedProductId),
      productName: product.name,
      quantity: fmt(quantity),
      purchase_price: fmt(purchasePrice)
    };

    setItems([...items, newItem]);
    
    // Reset current item fields
    setSelectedProductId('');
    setQuantity('');
    setPurchasePrice('');
  };

  const handleRemoveItem = (itemId) => {
    setItems(items.filter(item => item.id !== itemId));
  };

  const totalAmount = items.reduce((sum, item) => sum + (item.quantity * item.purchase_price), 0);

  const handleSaveInvoice = async () => {
    if (!supplierId) {
      alert('برجاء اختيار المورد.');
      return;
    }
    if (items.length === 0) {
      alert('برجاء إضافة أصناف للفاتورة.');
      return;
    }

    const payload = {
      supplier: fmt(supplierId),
      invoice_type: invoiceType,
      invoice_month: fmt(invoiceMonth),
      invoice_year: fmt(invoiceYear),
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
        alert('تم تحديث الفاتورة بنجاح!');
      } else {
        await api.post('/purchase-invoices/', payload);
        alert('تم حفظ الفاتورة بنجاح!');
      }
      navigate('/search-purchases');
    } catch (err) {
      console.error("Error saving invoice", err);
      alert('حصل مشكلة أثناء حفظ الفاتورة.');
    } finally {
      setSaving(false);
    }
  };

  if (loadingInitial) {
    return (
      <div className="page-wrapper" dir="rtl">
        <div className="page-body text-center mt-5 pt-5">
          <div className="spinner-border text-primary" role="status"></div>
          <div className="mt-2 fw-bold text-muted">جاري تحميل البيانات...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper" dir="rtl">
      <div className="page-header d-print-none flex-shrink-0">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title text-primary fw-bold">
                {id ? 'تعديل فاتورة مشتريات / مرتجع مصنع' : 'إضافة فاتورة مشتريات / مرتجع مصنع'}
              </h2>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/search-purchases" className="btn btn-outline-secondary fw-bold">
                العودة للدفتر
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-fluid">
          <div className="row">
            
            {/* ── Products Section (Left/Right) 60% ── */}
            <div className="col-lg-8 col-md-7 d-flex flex-column mb-3">
              <div className="card shadow-sm border-secondary-subtle">
                <div className="card-header bg-light py-2">
                  <h3 className="card-title m-0 fw-bold d-flex align-items-center gap-2">
                    <IconShoppingCart size={20} className="text-primary" /> الأصناف والمنتجات
                  </h3>
                </div>
                <div className="card-body py-2">
                  <div className="row align-items-end g-2">
                    <div className="col-md-5">
                      <label className="form-label fw-bold small mb-1">الصنف</label>
                      <input
                        className="form-control form-control-sm fw-bold border-secondary-subtle"
                        list="products-list"
                        placeholder="-- ابحث واختار الصنف --"
                        value={products.find(p => p.id === fmt(selectedProductId))?.name || selectedProductId}
                        onChange={(e) => {
                          const val = e.target.value;
                          const prod = products.find(p => p.name === val);
                          if (prod) {
                            setSelectedProductId(prod.id.toString());
                          } else {
                            setSelectedProductId(val);
                          }
                        }}
                      />
                      <datalist id="products-list">
                        {products.map(prod => (
                          <option key={prod.id} value={prod.name} />
                        ))}
                      </datalist>
                    </div>
                    <div className="col-md-3">
                      <label className="form-label fw-bold small mb-1">الكمية</label>
                      <input type="number" className="form-control form-control-sm text-center fw-bold border-secondary-subtle" value={quantity} onChange={(e) => setQuantity(e.target.value)} min="1" step="any" />
                    </div>
                    <div className="col-md-2">
                      <label className="form-label fw-bold small mb-1">سعر الشراء</label>
                      <input type="number" className="form-control form-control-sm text-center fw-bold border-secondary-subtle" value={purchasePrice} onChange={(e) => setPurchasePrice(e.target.value)} min="0" step="any" />
                    </div>
                    <div className="col-md-2">
                      <button className="btn btn-primary btn-sm w-100 fw-bold" onClick={handleAddItem}>إضافة</button>
                    </div>
                  </div>
                </div>
                <div className="table-responsive border-top border-secondary-subtle">
                  <table className="table table-vcenter table-hover card-table m-0">
                    <thead className="bg-light">
                      <tr>
                        <th className="fw-bold bg-light">اسم الصنف</th>
                        <th className="text-center fw-bold bg-light">الكمية</th>
                        <th className="text-center fw-bold bg-light">سعر الشراء</th>
                        <th className="text-center fw-bold bg-light">الإجمالي</th>
                        <th className="text-center fw-bold w-1 bg-light">حذف</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <tr key={item.id}>
                          <td className="fw-bold text-primary">{item.productName}</td>
                          <td className="text-center fw-bold">{item.quantity}</td>
                          <td className="text-center fw-bold">{item.purchase_price}</td>
                          <td className="text-center fw-bold text-danger">{(item.quantity * item.purchase_price)}</td>
                          <td className="text-center">
                            <button className="btn btn-sm btn-outline-danger fw-bold px-2 py-1" onClick={() => handleRemoveItem(item.id)}>
                              <IconTrash size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                      {items.length === 0 && (
                        <tr>
                          <td colSpan="5" className="text-center text-muted py-5 fw-bold fs-3">لا يوجد أصناف. يرجى إضافة أصناف للفاتورة.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* ── Invoice Data Section (Right/Left) 40% ── */}
            <div className="col-lg-4 col-md-5 d-flex flex-column mb-3">
              <div className="card shadow-sm border-secondary-subtle mb-3">
                <div className="card-header bg-light py-2">
                  <h3 className="card-title m-0 fw-bold d-flex align-items-center gap-2">
                    <IconFileInvoice size={20} className="text-primary" /> تفاصيل الفاتورة
                  </h3>
                </div>
                <div className="card-body">
                  <div className="mb-3">
                    <label className="form-label fw-bold">نوع الفاتورة</label>
                    <div className="d-flex gap-3">
                      <label className="form-check m-0">
                        <input className="form-check-input" type="radio" name="invoiceType" 
                          checked={invoiceType === 'PURCHASE'} 
                          onChange={() => setInvoiceType('PURCHASE')} />
                        <span className="form-check-label fw-bold text-success">شراء</span>
                      </label>
                      <label className="form-check m-0">
                        <input className="form-check-input" type="radio" name="invoiceType" 
                          checked={invoiceType === 'RETURN'} 
                          onChange={() => setInvoiceType('RETURN')} />
                        <span className="form-check-label fw-bold text-danger">مرتجع</span>
                      </label>
                    </div>
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-bold">المورد</label>
                    <select className="form-select fw-bold border-secondary-subtle" value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
                      <option value="">-- اختار المورد --</option>
                      {suppliers.map(sup => (
                        <option key={sup.id} value={sup.id}>{sup.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="row">
                    <div className="col-6">
                      <label className="form-label fw-bold">شهر الفاتورة</label>
                      <input type="number" className="form-control text-center fw-bold border-secondary-subtle" value={invoiceMonth} onChange={(e) => setInvoiceMonth(e.target.value)} min="1" max="12" />
                    </div>
                    <div className="col-6">
                      <label className="form-label fw-bold">سنة الفاتورة</label>
                      <input type="number" className="form-control text-center fw-bold border-secondary-subtle" value={invoiceYear} onChange={(e) => setInvoiceYear(e.target.value)} min="2000" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Total & Actions */}
              <div className="card shadow-sm border-secondary-subtle">
                <div className="card-body text-center bg-light rounded">
                  <h3 className="m-0 fw-bold mb-3">إجمالي الفاتورة</h3>
                  <div className="display-5 fw-bolder text-danger mb-4">
                    {totalAmount.toLocaleString()}
                  </div>
                  <button 
                    className="btn btn-success btn-lg w-100 fw-bold shadow-sm d-flex justify-content-center align-items-center gap-2" 
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
        </div>
      </div>
    </div>
  );
};

export default PurchaseEntry;
