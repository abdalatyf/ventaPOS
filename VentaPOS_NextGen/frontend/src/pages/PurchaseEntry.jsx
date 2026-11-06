import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../api';
import { IconFileInvoice } from '@tabler/icons-react';
import PurchaseHeader from '../components/purchases/PurchaseHeader';
import PurchaseItemForm from '../components/purchases/PurchaseItemForm';
import PurchaseItemsTable from '../components/purchases/PurchaseItemsTable';
import { 
  toEnglish, 
  checkSafeStockForReturn, 
  fetchPurchaseEntryInitialData 
} from '../components/purchases/purchaseUtils';

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
  const [saving, setSaving] = useState(false);

  // Autocomplete / Suggestions State
  const [suggestions, setSuggestions] = useState([]);
  const [activeInput, setActiveInput] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const blurTimerRef = useRef(null);

  // Refs for Keyboard Navigation
  const supplierRef = useRef(null);
  const monthRef = useRef(null);
  const yearRef = useRef(null);
  const prodQueryRef = useRef(null);
  const qtyRef = useRef(null);
  const priceRef = useRef(null);

  useEffect(() => {
    fetchPurchaseEntryInitialData(id).then(({ supps, prods, invoiceData }) => {
      setSuppliers(supps);
      setProducts(prods);

      if (invoiceData) {
        setInvoiceType(invoiceData.invoice_type || 'PURCHASE');
        setSupplierId(invoiceData.supplier || '');
        const existingSupplier = supps.find(s => s.id === invoiceData.supplier);
        if (existingSupplier) setSupplierQuery(existingSupplier.name);
        
        setInvoiceMonth(invoiceData.invoice_month || new Date().getMonth() + 1);
        setInvoiceYear(invoiceData.invoice_year || new Date().getFullYear());
        
        if (invoiceData.items) {
          setItems(invoiceData.items.map(i => {
            const p = prods.find(pr => pr.id === i.inventory_item);
            return {
              id: i.id || Date.now() + Math.random(),
              inventory_item: i.inventory_item,
              productName: p ? p.name : `صنف #${i.inventory_item}`,
              quantity: i.quantity,
              purchase_price: i.purchase_price
            };
          }));
        }
      }
    }).catch(err => {
      console.error("Error fetching initial data", err);
    }).finally(() => {
      setLoadingInitial(false);
      setTimeout(() => { supplierRef.current?.focus(); }, 150);
    });
  }, [id]);

  const triggerSuggestions = (val, fieldType) => {
    clearTimeout(blurTimerRef.current);
    const term = toEnglish(val).trim().toLowerCase();

    if (fieldType === 'supplier') {
      const filtered = suppliers.filter(s => s.name && s.name.toLowerCase().includes(term));
      setSuggestions(filtered.slice(0, 10));
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
    const existing = items.find(i => i.inventory_item === currentProduct.id);

    if (invoiceType === 'RETURN') {
      if (currentProduct.safe_qty !== undefined) {
        if (reqQty > currentProduct.safe_qty) {
          toast.error(`الكمية المطلوبة أكبر من المتاح: ${currentProduct.safe_qty}`);
          return;
        }
      } else {
        const check = await checkSafeStockForReturn(currentProduct.id, reqQty, invoiceMonth, invoiceYear, existing ? existing.quantity : 0);
        if (!check.ok) {
          toast.error(check.error);
          return;
        }
      }
    }

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
    
    setSelectedProduct(null);
    setProductQuery('');
    setQuantity('');
    setPurchasePrice('');
    setTimeout(() => prodQueryRef.current?.focus(), 50);
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
      
      {/* Page Header */}
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

      {/* Top Card: Invoice Meta */}
      <PurchaseHeader
        invoiceType={invoiceType}
        setInvoiceType={setInvoiceType}
        setItems={setItems}
        supplierRef={supplierRef}
        supplierQuery={supplierQuery}
        setSupplierQuery={setSupplierQuery}
        setSupplierId={setSupplierId}
        triggerSuggestions={triggerSuggestions}
        handleKeyDown={handleKeyDown}
        blurTimerRef={blurTimerRef}
        suppliers={suppliers}
        activeInput={activeInput}
        setActiveInput={setActiveInput}
        suggestions={suggestions}
        setSuggestions={setSuggestions}
        activeIndex={activeIndex}
        handleSuggestionSelect={handleSuggestionSelect}
        monthRef={monthRef}
        yearRef={yearRef}
        prodQueryRef={prodQueryRef}
        invoiceMonth={invoiceMonth}
        setInvoiceMonth={setInvoiceMonth}
        invoiceYear={invoiceYear}
        setInvoiceYear={setInvoiceYear}
        handleCartKD={handleCartKD}
      />

      {/* Middle Card: Products Section */}
      <div className="card shadow-sm mb-2" style={{ position: 'relative', zIndex: 20 }}>
        <PurchaseItemForm
          prodQueryRef={prodQueryRef}
          productQuery={productQuery}
          setProductQuery={setProductQuery}
          selectedProduct={selectedProduct}
          setSelectedProduct={setSelectedProduct}
          triggerSuggestions={triggerSuggestions}
          handleKeyDown={handleKeyDown}
          activeInput={activeInput}
          setActiveInput={setActiveInput}
          suggestions={suggestions}
          setSuggestions={setSuggestions}
          activeIndex={activeIndex}
          handleSuggestionSelect={handleSuggestionSelect}
          products={products}
          invoiceType={invoiceType}
          items={items}
          invoiceMonth={invoiceMonth}
          invoiceYear={invoiceYear}
          blurTimerRef={blurTimerRef}
          qtyRef={qtyRef}
          quantity={quantity}
          setQuantity={setQuantity}
          toEnglish={toEnglish}
          handleCartKD={handleCartKD}
          priceRef={priceRef}
          purchasePrice={purchasePrice}
          setPurchasePrice={setPurchasePrice}
          handleAddItem={handleAddItem}
        />

        <PurchaseItemsTable
          items={items}
          handleRemoveItem={handleRemoveItem}
          totalAmount={totalAmount}
          handleSaveInvoice={handleSaveInvoice}
          saving={saving}
          isEdit={!!id}
        />
      </div>

    </div>
  );
};

export default PurchaseEntry;
