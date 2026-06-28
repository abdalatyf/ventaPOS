import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';

const PosEntry = () => {
  const navigate = useNavigate();

  const [customer, setCustomer] = useState({
    name: '',
    phone: '',
    address: '',
    area: '',
    salesperson_id: ''
  });

  const [date, setDate] = useState({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });

  const [downPayment, setDownPayment] = useState('');

  // Cart and products
  const [inventory, setInventory] = useState([]);
  const [salespersons, setSalespersons] = useState([]);
  const [cart, setCart] = useState([]);
  
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedQuantity, setSelectedQuantity] = useState(1);
  const [selectedPrice, setSelectedPrice] = useState('');

  // Installment groups
  const [groups, setGroups] = useState([
    { amount: '', count: '' },
    { amount: '', count: '' },
    { amount: '', count: '' }
  ]);

  const [schedule, setSchedule] = useState([]);

  const addBtnRef = useRef(null);

  // Fetch Inventory and Salespersons on mount
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [invRes, spRes] = await Promise.all([
          api.get('/api/v1/inventory-items/').catch(() => ({ data: [] })),
          api.get('/api/v1/salespersons/').catch(() => ({ data: [] }))
        ]);
        const invData = invRes.data?.results || invRes.data;
        const spData = spRes.data?.results || spRes.data;
        setInventory(Array.isArray(invData) ? invData : []);
        setSalespersons(Array.isArray(spData) ? spData : []);
      } catch (e) {
        console.error("Failed to fetch initial data", e);
      }
    };
    fetchInitial();
  }, []);

  // Update selected price when product changes
  useEffect(() => {
    if (selectedProductId) {
      const prod = inventory.find(p => p.id === parseInt(selectedProductId));
      if (prod) {
        setSelectedPrice(prod.price);
        setSelectedQuantity(1);
      }
    } else {
      setSelectedPrice('');
      setSelectedQuantity(1);
    }
  }, [selectedProductId, inventory]);

  // Recalculate schedule
  useEffect(() => {
    const newSchedule = [];
    let currentMonth = parseInt(date.month);
    let currentYear = parseInt(date.year);

    groups.forEach((g) => {
      const count = parseInt(g.count) || 0;
      const amount = parseFloat(g.amount) || 0;
      if (count > 0 && amount > 0) {
        for (let i = 0; i < count; i++) {
          newSchedule.push({
            month: currentMonth,
            year: currentYear,
            amount: amount
          });
          currentMonth++;
          if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
          }
        }
      }
    });
    setSchedule(newSchedule);
  }, [groups, date]);

  const addToCart = async () => {
    if (!selectedProductId || !selectedQuantity || !selectedPrice) return;
    const prod = inventory.find(p => p.id === parseInt(selectedProductId));
    if (!prod) return;

    try {
      // Validation: Get safe available qty for the given month/year
      const res = await api.get(`/api/v1/inventory-items/${prod.id}/get_safe_available_qty/`, {
        params: { month: date.month, year: date.year }
      });
      
      let safeAvailable = 0;
      if (typeof res.data === 'object') {
        safeAvailable = res.data.safe_available_qty ?? res.data.available_qty ?? 0;
      } else {
        safeAvailable = parseInt(res.data) || 0;
      }

      const qtyToAdd = parseInt(selectedQuantity);
      
      const existingIdx = cart.findIndex(c => c.id === prod.id);
      const existingQty = existingIdx >= 0 ? cart[existingIdx].quantity : 0;
      const newTotalQty = existingQty + qtyToAdd;

      if (newTotalQty > safeAvailable) {
        alert(`لا يمكن الإضافة. الكمية المطلوبة ستتخطى المتاح (${safeAvailable}) في هذا الشهر!`);
        return;
      }

      // Add to cart
      const newCart = [...cart];
      if (existingIdx >= 0) {
        newCart[existingIdx].quantity = newTotalQty;
        // Optionally update price if user changed it
        newCart[existingIdx].price = parseFloat(selectedPrice);
      } else {
        newCart.push({ 
          ...prod, 
          quantity: qtyToAdd, 
          price: parseFloat(selectedPrice) 
        });
      }
      setCart(newCart);
      
      // Reset selections
      setSelectedProductId('');
      setSelectedQuantity(1);
      setSelectedPrice('');
      
    } catch (e) {
      console.error(e);
      alert("حدث خطأ أثناء التأكد من رصيد الصنف. تأكد من اتصال الخادم.");
    }
  };

  const removeFromCart = (index) => {
    setCart(cart.filter((_, i) => i !== index));
  };

  const handleGroupChange = (index, field, value) => {
    const newGroups = [...groups];
    newGroups[index][field] = value;
    setGroups(newGroups);
  };

  const totalCart = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const totalInstallments = schedule.reduce((sum, item) => sum + item.amount, 0);
  const dpAmount = parseFloat(downPayment) || 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (cart.length === 0) {
      alert("لا توجد بضاعة في الفاتورة!");
      return;
    }

    // Validation
    const expectedTotal = dpAmount + totalInstallments;
    // adding a small epsilon check for floating point
    if (Math.abs(totalCart - expectedTotal) > 0.01) {
      alert(`الإجمالي خطأ!
إجمالي الفاتورة: ${totalCart}
المقدم + الأقساط: ${expectedTotal}
يجب أن يكون المجموع متطابقاً.`);
      return;
    }

    const payload = {
      customer_name: customer.name,
      customer_phone: customer.phone,
      customer_address: customer.address,
      customer_area: customer.area,
      salesperson_id: customer.salesperson_id || null,
      branch_id: 1, // Defaulting to 1 for now or we can omit
      is_cash_sale: schedule.length === 0,
      total_amount: totalCart,
      down_payment: dpAmount,
      sale_month: date.month,
      sale_year: date.year,
      items: cart.map(c => ({ 
        inventory_item_id: c.id, 
        quantity: c.quantity, 
        unit_price: c.price 
      })),
      installments: schedule.map(s => ({
        payment_month: s.month,
        payment_year: s.year,
        amount: s.amount
      }))
    };

    try {
      await api.post('/api/v1/receipts/', payload);
      alert('تم حفظ الفاتورة بنجاح!');
      navigate('/');
    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.error || error.message;
      alert('خطأ أثناء حفظ الفاتورة: ' + msg);
    }
  };

  const handleKeyDownCart = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addToCart();
    }
  };

  return (
    <div className="page-wrapper" dir="rtl">
      <div className="page-header d-print-none">
        <div className="container-xl">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">
                نقطة البيع (الفاتورة)
              </h2>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/" className="btn btn-secondary" tabIndex="-1">
                العودة للدفتر
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-xl">
          <form onSubmit={handleSubmit}>
            <div className="row row-cards">
              
              {/* Customer Info */}
              <div className="col-md-6">
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">بيانات العميل</h3>
                  </div>
                  <div className="card-body">
                    <div className="row">
                      <div className="col-12 col-md-6 mb-3">
                        <label className="form-label">اسم العميل</label>
                        <input type="text" className="form-control" required autoFocus placeholder="اكتب اسم العميل" value={customer.name} onChange={(e) => setCustomer({...customer, name: e.target.value})} tabIndex="1" />
                      </div>
                      <div className="col-12 col-md-6 mb-3">
                        <label className="form-label">تليفون العميل</label>
                        <input type="text" className="form-control" placeholder="رقم التليفون" value={customer.phone} onChange={(e) => setCustomer({...customer, phone: e.target.value})} tabIndex="2" />
                      </div>
                      <div className="col-12 col-md-4 mb-3">
                        <label className="form-label">المنطقة</label>
                        <input type="text" className="form-control" placeholder="المنطقة" value={customer.area} onChange={(e) => setCustomer({...customer, area: e.target.value})} tabIndex="3" />
                      </div>
                      <div className="col-12 col-md-4 mb-3">
                        <label className="form-label">العنوان</label>
                        <input type="text" className="form-control" placeholder="العنوان بالكامل" value={customer.address} onChange={(e) => setCustomer({...customer, address: e.target.value})} tabIndex="4" />
                      </div>
                      <div className="col-12 col-md-4 mb-3">
                        <label className="form-label">المندوب / مسؤول المبيعات</label>
                        <select className="form-select" value={customer.salesperson_id} onChange={(e) => setCustomer({...customer, salesperson_id: e.target.value})} tabIndex="5">
                          <option value="">-- اختياري --</option>
                          {salespersons.map(sp => (
                            <option key={sp.id} value={sp.id}>{sp.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Start Date & Products */}
              <div className="col-md-6">
                <div className="card mb-3">
                  <div className="card-header">
                    <h3 className="card-title">تاريخ البيع / بداية التقسيط</h3>
                  </div>
                  <div className="card-body">
                    <div className="row g-2">
                      <div className="col-6">
                        <label className="form-label">الشهر</label>
                        <select className="form-select" value={date.month} onChange={e => setDate({...date, month: e.target.value})} tabIndex="5">
                          {[...Array(12)].map((_, i) => (
                            <option key={i+1} value={i+1}>{i+1}</option>
                          ))}
                        </select>
                      </div>
                      <div className="col-6">
                        <label className="form-label">السنة</label>
                        <input type="number" className="form-control" value={date.year} onChange={e => setDate({...date, year: e.target.value})} tabIndex="6" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">البضاعة (الخزنة)</h3>
                  </div>
                  <div className="card-body">
                    <div className="row g-2 mb-3">
                      <div className="col-5">
                        <label className="form-label">الصنف</label>
                        <select className="form-select" value={selectedProductId} onChange={e => setSelectedProductId(e.target.value)} tabIndex="7">
                          <option value="">اختر الصنف...</option>
                          {inventory.map(p => (
                            <option key={p.id} value={p.id}>{p.name} - {p.stock} متاح</option>
                          ))}
                        </select>
                      </div>
                      <div className="col-2">
                        <label className="form-label">الكمية</label>
                        <input type="number" className="form-control" min="1" value={selectedQuantity} onChange={e => setSelectedQuantity(e.target.value)} onKeyDown={handleKeyDownCart} tabIndex="8" />
                      </div>
                      <div className="col-3">
                        <label className="form-label">سعر البيع</label>
                        <input type="number" step="0.01" className="form-control" value={selectedPrice} onChange={e => setSelectedPrice(e.target.value)} onKeyDown={handleKeyDownCart} tabIndex="9" />
                      </div>
                      <div className="col-2 d-flex align-items-end">
                        <button type="button" className="btn btn-primary w-100" onClick={addToCart} tabIndex="10" ref={addBtnRef}>إضافة</button>
                      </div>
                    </div>
                    
                    {cart.length > 0 && (
                      <div className="table-responsive">
                        <table className="table table-vcenter table-nowrap">
                          <thead>
                            <tr>
                              <th>الصنف</th>
                              <th>الكمية</th>
                              <th>سعر الوحدة</th>
                              <th>الإجمالي</th>
                              <th></th>
                            </tr>
                          </thead>
                          <tbody>
                            {cart.map((item, idx) => (
                              <tr key={idx}>
                                <td>{item.name}</td>
                                <td>{item.quantity}</td>
                                <td>{item.price}</td>
                                <td>{item.price * item.quantity}</td>
                                <td>
                                  <button type="button" className="btn btn-sm btn-danger" onClick={() => removeFromCart(idx)} tabIndex="-1">حذف</button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="mt-2 text-end fw-bold text-success" style={{fontSize: '1.2rem'}}>إجمالي الفاتورة: {totalCart} جنيه</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Installment Groups & Downpayment */}
              <div className="col-12">
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">الماليات: المقدم ونظام التقسيط</h3>
                  </div>
                  <div className="card-body">
                    <div className="row">
                      <div className="col-md-6 border-end">
                        <div className="mb-4">
                          <label className="form-label fw-bold text-primary" style={{fontSize: '1.1rem'}}>المقدم (كاش)</label>
                          <input type="number" step="0.01" className="form-control form-control-lg" placeholder="قيمة المقدم المدفوع حالاً" 
                            value={downPayment} onChange={e => setDownPayment(e.target.value)} tabIndex="11" />
                        </div>
                        
                        <h4 className="mb-3">نظام التقسيط (٣ مجموعات اختياري)</h4>
                        {groups.map((group, idx) => (
                          <div className="row g-2 mb-3 align-items-end" key={idx}>
                            <div className="col">
                              <label className="form-label">القسط (جنيه) م{idx + 1}</label>
                              <input type="number" step="0.01" className="form-control" placeholder="الفلوس" 
                                value={group.amount} onChange={e => handleGroupChange(idx, 'amount', e.target.value)} tabIndex={12 + (idx * 2)} />
                            </div>
                            <div className="col-auto d-flex align-items-center mb-1">
                              <strong>x</strong>
                            </div>
                            <div className="col">
                              <label className="form-label">عدد الشهور م{idx + 1}</label>
                              <input type="number" className="form-control" placeholder="الشهور"
                                value={group.count} onChange={e => handleGroupChange(idx, 'count', e.target.value)} tabIndex={13 + (idx * 2)} />
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="col-md-6 ps-md-4">
                        <h4>شكل الدفتر بعد التقسيط</h4>
                        <div className="table-responsive bg-light p-2 rounded border" style={{ maxHeight: '250px', overflowY: 'auto' }}>
                          <table className="table table-vcenter table-nowrap table-sm">
                            <thead>
                              <tr>
                                <th>#</th>
                                <th>الشهر / السنة</th>
                                <th>المبلغ</th>
                              </tr>
                            </thead>
                            <tbody>
                              {schedule.length > 0 ? schedule.map((s, idx) => (
                                <tr key={idx}>
                                  <td>{idx + 1}</td>
                                  <td>{String(s.month).padStart(2, '0')} / {s.year}</td>
                                  <td className="fw-bold">{s.amount} ج</td>
                                </tr>
                              )) : (
                                <tr>
                                  <td colSpan="3" className="text-center text-muted py-3">بيع كاش (لا يوجد أقساط)</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                        
                        <div className="mt-3 p-3 bg-blue-lt rounded">
                          <div className="d-flex justify-content-between mb-2">
                            <span>إجمالي الفاتورة:</span>
                            <span className="fw-bold">{totalCart} ج</span>
                          </div>
                          <div className="d-flex justify-content-between mb-2">
                            <span>المقدم المدفوع:</span>
                            <span className="fw-bold">{dpAmount} ج</span>
                          </div>
                          <div className="d-flex justify-content-between mb-2">
                            <span>إجمالي الأقساط:</span>
                            <span className="fw-bold">{totalInstallments} ج</span>
                          </div>
                          <hr className="my-2" />
                          <div className="d-flex justify-content-between">
                            <strong>المجموع (المقدم + الأقساط):</strong>
                            <strong className={Math.abs(totalCart - (dpAmount + totalInstallments)) > 0.01 ? 'text-danger' : 'text-success'}>
                              {dpAmount + totalInstallments} ج
                            </strong>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="card-footer text-end">
                    <button type="submit" className="btn btn-success btn-lg px-5" tabIndex="30">حفظ الفاتورة</button>
                  </div>
                </div>
              </div>

            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PosEntry;
