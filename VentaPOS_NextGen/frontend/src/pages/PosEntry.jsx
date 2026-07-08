import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { fmt } from '../utils/formatUtils';

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
  const [salespersons, setSalespersons] = useState([]);
  const [cart, setCart] = useState([]);
  
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null); // { id, value, max }
  const [selectedQuantity, setSelectedQuantity] = useState(1);
  const [selectedPrice, setSelectedPrice] = useState('');

  // Installment groups
  const [groups, setGroups] = useState([
    { amount: '', count: '' },
    { amount: '', count: '' },
    { amount: '', count: '' }
  ]);

  const [schedule, setSchedule] = useState([]);

  // Cash Sale Toggle
  const [isCashSale, setIsCashSale] = useState(false);

  // Suggestions state
  const [productSearchTerm, setProductSearchTerm] = useState('');
  const [productSuggestions, setProductSuggestions] = useState([]);
  const [nameSuggestions, setNameSuggestions] = useState([]);
  const [phoneSuggestions, setPhoneSuggestions] = useState([]);
  const [areaSuggestions, setAreaSuggestions] = useState([]);
  const [addressSuggestions, setAddressSuggestions] = useState([]);

  const [showProductSuggestions, setShowProductSuggestions] = useState(false);
  const [showNameSuggestions, setShowNameSuggestions] = useState(false);
  const [showPhoneSuggestions, setShowPhoneSuggestions] = useState(false);
  const [showAreaSuggestions, setShowAreaSuggestions] = useState(false);
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);

  const addBtnRef = useRef(null);

  // Fetch Salespersons on mount
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const spRes = await api.get('/salespersons/').catch(() => ({ data: [] }));
        const spData = spRes.data?.results || spRes.data;
        setSalespersons(Array.isArray(spData) ? spData : []);
      } catch (e) {
        console.error("Failed to fetch initial data", e);
      }
    };
    fetchInitial();
  }, []);

  // Debounced search for Name
  useEffect(() => {
    if (customer.name.trim().length < 1) {
      setNameSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await api.get('/customer-suggestions/', {
          params: {
            term: customer.name,
            field: 'name',
            salesperson_id: customer.salesperson_id,
            current_area: customer.area
          }
        });
        setNameSuggestions(res.data || []);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [customer.name, customer.salesperson_id, customer.area]);

  // Debounced search for Phone
  useEffect(() => {
    if (customer.phone.trim().length < 1) {
      setPhoneSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await api.get('/customer-suggestions/', {
          params: {
            term: customer.phone,
            field: 'phone',
            salesperson_id: customer.salesperson_id,
            current_area: customer.area,
            current_name: customer.name
          }
        });
        setPhoneSuggestions(res.data || []);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [customer.phone, customer.salesperson_id, customer.area, customer.name]);

  // Debounced search for Area
  useEffect(() => {
    if (customer.area.trim().length < 1) {
      setAreaSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await api.get('/customer-suggestions/', {
          params: {
            term: customer.area,
            field: 'area',
            salesperson_id: customer.salesperson_id
          }
        });
        setAreaSuggestions(res.data || []);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [customer.area, customer.salesperson_id]);

  // Debounced search for Address
  useEffect(() => {
    if (customer.address.trim().length < 1) {
      setAddressSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await api.get('/customer-suggestions/', {
          params: {
            term: customer.address,
            field: 'address',
            salesperson_id: customer.salesperson_id,
            current_area: customer.area,
            current_name: customer.name
          }
        });
        setAddressSuggestions(res.data || []);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [customer.address, customer.salesperson_id, customer.area, customer.name]);

  // Debounced search for Product
  useEffect(() => {
    if (productSearchTerm.trim().length < 1) {
      setProductSuggestions([]);
      return;
    }
    if (selectedProduct && productSearchTerm === selectedProduct.value) {
      setProductSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      try {
        let branchId = localStorage.getItem('branchId');
        if (!branchId) {
          const branchRes = await api.get('/branches/').catch(() => ({ data: [] }));
          const branches = branchRes.data?.results || branchRes.data;
          if (branches && branches.length > 0) {
            branchId = branches[0].id;
            localStorage.setItem('branchId', branchId);
          }
        }
        if (!branchId) return;

        const res = await api.get('/product-suggestions/', {
          params: {
            term: productSearchTerm,
            branch_id: branchId,
            month: date.month,
            year: date.year
          }
        });
        setProductSuggestions(res.data || []);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [productSearchTerm, date.month, date.year, selectedProduct]);

  // Recalculate schedule (starts on sale_month + 1)
  useEffect(() => {
    const newSchedule = [];
    let currentMonth = fmt(date.month);
    let currentYear = fmt(date.year);

    currentMonth++;
    if (currentMonth > 12) {
      currentMonth = 1;
      currentYear++;
    }

    groups.forEach((g) => {
      const count = fmt(g.count) || 0;
      const amount = fmt(g.amount) || 0;
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

  const handleSelectProduct = async (prod) => {
    setSelectedProductId(prod.id);
    setSelectedProduct(prod);
    setProductSearchTerm(prod.value);
    setShowProductSuggestions(false);
    
    // Fetch product details to get price
    try {
      const res = await api.get(`/inventory-items/${prod.id}/`);
      if (res.data) {
        setSelectedPrice(res.data.initial_purchase_price || '');
      }
    } catch (err) {
      console.error("Failed to fetch product details", err);
    }
  };

  const handleSelectName = (val) => {
    setCustomer(c => ({...c, name: val}));
    setShowNameSuggestions(false);
    setNameSuggestions([]);
  };

  const handleSelectPhone = (val) => {
    setCustomer(c => ({...c, phone: val}));
    setShowPhoneSuggestions(false);
    setPhoneSuggestions([]);
  };

  const handleSelectArea = (val) => {
    setCustomer(c => ({...c, area: val}));
    setShowAreaSuggestions(false);
    setAreaSuggestions([]);
  };

  const handleSelectAddress = (val) => {
    setCustomer(c => ({...c, address: val}));
    setShowAddressSuggestions(false);
    setAddressSuggestions([]);
  };

  const addToCart = async () => {
    if (!selectedProductId || !selectedQuantity || !selectedPrice) return;
    if (!selectedProduct) return;

    const maxStock = selectedProduct.max;
    const qtyToAdd = fmt(selectedQuantity);
    
    const existingIdx = cart.findIndex(c => c.id === selectedProductId);
    const existingQty = existingIdx >= 0 ? cart[existingIdx].quantity : 0;
    const newTotalQty = existingQty + qtyToAdd;

    if (newTotalQty > maxStock) {
      alert(`الكمية المطلوبة (مع اللي في السلة) أكتر من البضاعة المتاحة في المخزن للفترة دي. المتاح هو ${maxStock} بس.`);
      return;
    }

    // Add to cart
    const newCart = [...cart];
    if (existingIdx >= 0) {
      newCart[existingIdx].quantity = newTotalQty;
      newCart[existingIdx].price = fmt(selectedPrice);
    } else {
      newCart.push({ 
        id: selectedProductId, 
        name: selectedProduct.value,
        quantity: qtyToAdd, 
        price: fmt(selectedPrice) 
      });
    }
    setCart(newCart);
    
    // Reset selections
    setSelectedProductId('');
    setSelectedProduct(null);
    setProductSearchTerm('');
    setSelectedQuantity(1);
    setSelectedPrice('');
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
  const dpAmount = fmt(downPayment) || 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (cart.length === 0) {
      alert("لا توجد بضاعة في الفاتورة!");
      return;
    }

    if (!isCashSale) {
      const expectedTotal = dpAmount + totalInstallments;
      if (Math.abs(totalCart - expectedTotal) > 0.01) {
        alert(`الإجمالي خطأ!
إجمالي الفاتورة: ${totalCart}
المقدم + الأقساط: ${expectedTotal}
يجب أن يكون المجموع متطابقاً.`);
        return;
      }
    }

    const activeGroups = groups.filter(g => fmt(g.count) > 0 && fmt(g.amount) > 0);
    const installmentSystemStr = activeGroups.map(g => `${fmt(g.amount)}*${fmt(g.count)}`).join(" + ");

    const payload = {
      customer_name: isCashSale ? "عميل نقدي" : customer.name,
      phone_number: isCashSale ? "" : customer.phone,
      address: isCashSale ? "" : customer.address,
      area: isCashSale ? "" : customer.area,
      salesperson: isCashSale ? null : (customer.salesperson_id || null),
      is_cash_sale: isCashSale,
      total_amount: totalCart,
      down_payment: isCashSale ? totalCart : dpAmount,
      sale_month: date.month,
      sale_year: date.year,
      items: cart.map(c => ({ 
        inventory_item_id: c.id, 
        quantity: c.quantity, 
        unit_price: c.price 
      })),
      installments: isCashSale ? [] : schedule.map(s => ({
        payment_month: s.month,
        payment_year: s.year,
        amount: s.amount
      })),
      installment_system: isCashSale ? "" : installmentSystemStr
    };

    try {
      await api.post('/receipts/', payload);
      alert('تم حفظ الفاتورة بنجاح!');
      navigate('/');
    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.error || error.response?.data?.detail || error.message;
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
        <div className="container-fluid">
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
        <div className="container-fluid">
          <form onSubmit={handleSubmit}>
            
            {/* Cash Sale Toggle */}
            <div className="card mb-3">
              <div className="card-body">
                <label className="form-check form-switch mb-0">
                  <input className="form-check-input" type="checkbox" checked={isCashSale} onChange={e => setIsCashSale(e.target.checked)} />
                  <span className="form-check-label fw-bold">بيع نقدي بالكامل (كاش بدون أقساط)</span>
                </label>
              </div>
            </div>

            <div className="row row-cards">
              
              {/* Customer Info */}
              {!isCashSale && (
                <div className="col-md-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="card-title">بيانات العميل</h3>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-12 col-md-6 mb-3">
                          <label className="form-label">اسم العميل</label>
                          <div style={{ position: 'relative' }}>
                            <input 
                              type="text" 
                              className="form-control" 
                              required={!isCashSale} 
                              autoFocus 
                              placeholder="اكتب اسم العميل" 
                              value={customer.name} 
                              onChange={(e) => setCustomer({...customer, name: e.target.value})} 
                              onFocus={() => setShowNameSuggestions(true)}
                              onBlur={() => setTimeout(() => setShowNameSuggestions(false), 200)}
                              tabIndex="1" 
                            />
                            {showNameSuggestions && nameSuggestions.length > 0 && (
                              <div className="list-group" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}>
                                {nameSuggestions.map((item, idx) => (
                                  <button key={idx} type="button" className="list-group-item list-group-item-action text-start" onClick={() => handleSelectName(item.value)}>
                                    {item.value}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="col-12 col-md-6 mb-3">
                          <label className="form-label">تليفون العميل</label>
                          <div style={{ position: 'relative' }}>
                            <input 
                              type="text" 
                              className="form-control" 
                              placeholder="رقم التليفون" 
                              value={customer.phone} 
                              onChange={(e) => setCustomer({...customer, phone: e.target.value})} 
                              onFocus={() => setShowPhoneSuggestions(true)}
                              onBlur={() => setTimeout(() => setShowPhoneSuggestions(false), 200)}
                              tabIndex="2" 
                            />
                            {showPhoneSuggestions && phoneSuggestions.length > 0 && (
                              <div className="list-group" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}>
                                {phoneSuggestions.map((item, idx) => (
                                  <button key={idx} type="button" className="list-group-item list-group-item-action text-start" onClick={() => handleSelectPhone(item.value)}>
                                    {item.value}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="col-12 col-md-4 mb-3">
                          <label className="form-label">المنطقة</label>
                          <div style={{ position: 'relative' }}>
                            <input 
                              type="text" 
                              className="form-control" 
                              placeholder="المنطقة" 
                              value={customer.area} 
                              onChange={(e) => setCustomer({...customer, area: e.target.value})} 
                              onFocus={() => setShowAreaSuggestions(true)}
                              onBlur={() => setTimeout(() => setShowAreaSuggestions(false), 200)}
                              tabIndex="3" 
                            />
                            {showAreaSuggestions && areaSuggestions.length > 0 && (
                              <div className="list-group" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}>
                                {areaSuggestions.map((item, idx) => (
                                  <button key={idx} type="button" className="list-group-item list-group-item-action text-start" onClick={() => handleSelectArea(item.value)}>
                                    {item.value}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="col-12 col-md-4 mb-3">
                          <label className="form-label">العنوان</label>
                          <div style={{ position: 'relative' }}>
                            <input 
                              type="text" 
                              className="form-control" 
                              placeholder="العنوان بالكامل" 
                              value={customer.address} 
                              onChange={(e) => setCustomer({...customer, address: e.target.value})} 
                              onFocus={() => setShowAddressSuggestions(true)}
                              onBlur={() => setTimeout(() => setShowAddressSuggestions(false), 200)}
                              tabIndex="4" 
                            />
                            {showAddressSuggestions && addressSuggestions.length > 0 && (
                              <div className="list-group" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}>
                                {addressSuggestions.map((item, idx) => (
                                  <button key={idx} type="button" className="list-group-item list-group-item-action text-start" onClick={() => handleSelectAddress(item.value)}>
                                    {item.value}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
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
              )}

              {/* Start Date & Products */}
              <div className={isCashSale ? "col-12" : "col-md-6"}>
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
                        <div style={{ position: 'relative' }}>
                          <input 
                            type="text" 
                            className="form-control" 
                            placeholder="ابحث عن الصنف..." 
                            value={productSearchTerm} 
                            onChange={e => {
                              setProductSearchTerm(e.target.value);
                              if (selectedProductId) {
                                setSelectedProductId('');
                                setSelectedProduct(null);
                              }
                            }}
                            onFocus={() => setShowProductSuggestions(true)}
                            onBlur={() => setTimeout(() => setShowProductSuggestions(false), 200)}
                            tabIndex="7"
                          />
                          {showProductSuggestions && productSuggestions.length > 0 && (
                            <div className="list-group" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}>
                              {productSuggestions.map((p, idx) => (
                                <button 
                                  key={idx} 
                                  type="button" 
                                  className="list-group-item list-group-item-action text-start" 
                                  onClick={() => handleSelectProduct(p)}
                                >
                                  {p.value} - {p.max} متاح
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
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
                        <div className="mt-2 text-end fw-bold text-success" style={{fontSize: '1.2rem'}}>إجمالي الفاتورة: {totalCart}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Installment Groups & Downpayment */}
              {!isCashSale && (
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
              )}

              {isCashSale && (
                <div className="col-12 text-end mt-3">
                  <button type="submit" className="btn btn-success btn-lg px-5" tabIndex="30">حفظ الفاتورة</button>
                </div>
              )}

            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PosEntry;

