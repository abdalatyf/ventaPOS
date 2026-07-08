import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { fmt } from '../utils/formatUtils';

const Purchases = () => {
  const navigate = useNavigate();
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
          api.get('/inventory-items/').catch(() => ({ data: [] }))
        ]);
        const suppData = suppliersRes.data?.results || suppliersRes.data;
        const prodData = productsRes.data?.results || productsRes.data;
        setSuppliers(Array.isArray(suppData) ? suppData : []);
        setProducts(Array.isArray(prodData) ? prodData : []);
      } catch (err) {
        console.error("Error fetching initial data", err);
      } finally {
        setLoadingInitial(false);
      }
    };
    fetchInitialData();
  }, []);

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

  const handleRemoveItem = (id) => {
    setItems(items.filter(item => item.id !== id));
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
      await api.post('/purchase-invoices/', payload);
      alert('تم حفظ الفاتورة بنجاح!');
      navigate('/');
    } catch (err) {
      console.error("Error saving invoice", err);
      alert('حصل مشكلة أثناء حفظ الفاتورة.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">
                فواتير الشراء ومرتجع المصنع
              </h2>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/" className="btn btn-outline-secondary">
                العودة للرئيسية
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-fluid">
          
          {/* Invoice Basic Data Card */}
          <div className="card mb-3">
            <div className="card-header">
              <h3 className="card-title">البيانات الأساسية للفاتورة</h3>
            </div>
            <div className="card-body">
              <div className="row mb-3">
                <div className="col-md-6">
                  <div className="form-label">نوع الفاتورة</div>
                  <div>
                    <label className="form-check form-check-inline">
                      <input className="form-check-input" type="radio" name="invoiceType" 
                        checked={invoiceType === 'PURCHASE'} 
                        onChange={() => setInvoiceType('PURCHASE')} />
                      <span className="form-check-label">فاتورة شراء</span>
                    </label>
                    <label className="form-check form-check-inline">
                      <input className="form-check-input" type="radio" name="invoiceType" 
                        checked={invoiceType === 'RETURN'} 
                        onChange={() => setInvoiceType('RETURN')} />
                      <span className="form-check-label">مرتجع للمورد</span>
                    </label>
                  </div>
                </div>
                <div className="col-md-6">
                  <label className="form-label">المورد</label>
                  <select className="form-select" value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
                    <option value="">-- اختار المورد --</option>
                    {suppliers.map(sup => (
                      <option key={sup.id} value={sup.id}>{sup.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="row">
                <div className="col-md-6">
                  <label className="form-label">شهر الفاتورة</label>
                  <input type="number" className="form-control" value={invoiceMonth} onChange={(e) => setInvoiceMonth(e.target.value)} min="1" max="12" />
                </div>
                <div className="col-md-6">
                  <label className="form-label">سنة الفاتورة</label>
                  <input type="number" className="form-control" value={invoiceYear} onChange={(e) => setInvoiceYear(e.target.value)} min="2000" />
                </div>
              </div>
            </div>
          </div>

          {/* Add Items Card */}
          <div className="card mb-3">
            <div className="card-header">
              <h3 className="card-title">إدراج الأصناف في الفاتورة</h3>
            </div>
            <div className="card-body">
              <div className="row align-items-end">
                <div className="col-md-5 mb-3">
                  <label className="form-label">الصنف</label>
                  <input
                    className="form-control"
                    list="products-list"
                    placeholder="-- ابحث واختار الصنف --"
                    value={products.find(p => p.id === fmt(selectedProductId))?.name || selectedProductId}
                    onChange={(e) => {
                      const val = e.target.value;
                      const prod = products.find(p => p.name === val);
                      if (prod) {
                        setSelectedProductId(prod.id.toString());
                      } else {
                        setSelectedProductId(val); // will fail validation if not selected properly
                      }
                    }}
                  />
                  <datalist id="products-list">
                    {products.map(prod => (
                      <option key={prod.id} value={prod.name} />
                    ))}
                  </datalist>
                </div>
                <div className="col-md-3 mb-3">
                  <label className="form-label">الكمية</label>
                  <input type="number" className="form-control" value={quantity} onChange={(e) => setQuantity(e.target.value)} min="1" step="any" />
                </div>
                <div className="col-md-3 mb-3">
                  <label className="form-label">سعر الشراء</label>
                  <input type="number" className="form-control" value={purchasePrice} onChange={(e) => setPurchasePrice(e.target.value)} min="0" step="any" />
                </div>
                <div className="col-md-1 mb-3">
                  <button className="btn btn-primary w-100" onClick={handleAddItem}>إضافة</button>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Table Card */}
          <div className="card mb-3">
            <div className="card-header">
              <h3 className="card-title">الأصناف المدرجة</h3>
            </div>
            <div className="table-responsive">
              <table className="table card-table table-vcenter text-nowrap datatable">
                <thead>
                  <tr>
                    <th>اسم الصنف</th>
                    <th>الكمية</th>
                    <th>سعر الشراء</th>
                    <th>الإجمالي</th>
                    <th>الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.productName}</td>
                      <td>{item.quantity}</td>
                      <td>{item.purchase_price}</td>
                      <td>{(item.quantity * item.purchase_price)}</td>
                      <td>
                        <button className="btn btn-sm btn-outline-danger" onClick={() => handleRemoveItem(item.id)}>مسح</button>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan="5" className="text-center text-muted">لا يوجد أصناف في الفاتورة.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="card-footer d-flex justify-content-between align-items-center">
              <h4 className="m-0">إجمالي الفاتورة: {totalAmount}</h4>
              <button className="btn btn-success" onClick={handleSaveInvoice} disabled={saving || items.length === 0}>
                {saving ? 'جاري الحفظ...' : 'حفظ الفاتورة وتحديث المخزن'}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Purchases;
