import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { fmt } from '../utils/formatUtils';

const Inventory = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('add'); // 'add', 'edit', 'delete'
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({ name: '', quantity: 0, purchase_price: 0, initial_commission_amount: 0, initial_month: new Date().getMonth() + 1, initial_year: new Date().getFullYear() });

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/v1/inventory-items/');
      const data = res.data.results || res.data;
      const mappedData = (Array.isArray(data) ? data : []).map(item => ({
        ...item,
        quantity: item.initial_quantity,
        purchase_price: item.initial_purchase_price,
        commission: item.initial_commission_amount
      }));
      setItems(mappedData);
    } catch (err) {
      console.error("Failed to fetch inventory", err);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (type, item = null) => {
    setModalType(type);
    if (item) {
      setSelectedItem(item);
      setFormData(item);
    } else {
      setSelectedItem(null);
      setFormData({ name: '', quantity: 0, purchase_price: 0, initial_commission_amount: 0, initial_month: new Date().getMonth() + 1, initial_year: new Date().getFullYear() });
    }
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if ('quantity' in payload) {
        payload.initial_quantity = fmt(payload.quantity) || 0;
        delete payload.quantity;
      }
      if ('purchase_price' in payload) {
        payload.initial_purchase_price = fmt(payload.purchase_price) || 0;
        delete payload.purchase_price;
      }
      if ('initial_commission_amount' in payload) {
        payload.initial_commission_amount = fmt(payload.initial_commission_amount) || 0;
      }
      if ('initial_month' in payload) {
        payload.initial_month = fmt(payload.initial_month) || new Date().getMonth() + 1;
      }
      if ('initial_year' in payload) {
        payload.initial_year = fmt(payload.initial_year) || new Date().getFullYear();
      }

      if (modalType === 'add') {
        await api.post('/api/v1/inventory-items/', payload);
      } else if (modalType === 'edit') {
        await api.put(`/api/v1/inventory-items/${selectedItem.id}/`, payload);
      } else if (modalType === 'delete') {
        await api.delete(`/api/v1/inventory-items/${selectedItem.id}/`);
      }
      fetchInventory();
      setShowModal(false);
    } catch (err) {
      console.error("Failed to save", err);
      alert("حدث خطأ أثناء الحفظ. يرجى المحاولة مرة أخرى.");
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalInventoryValue = filteredItems.reduce((acc, item) => acc + (item.quantity * item.purchase_price), 0);

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">
                إدارة البضاعة
              </h2>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <div className="btn-list">
                <button onClick={() => openModal('add')} className="btn btn-primary d-none d-sm-inline-block">
                  <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 5l0 14" /><path d="M5 12l14 0" /></svg>
                  تسجيل صنف جديد
                </button>
                <Link to="/" className="btn btn-outline-secondary">
                  العودة للدفتر
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="page-body">
        <div className="container-fluid">
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-body">
              <div className="row align-items-center">
                <div className="col-md-6 mb-3 mb-md-0">
                  <div className="input-icon">
                    <span className="input-icon-addon">
                      <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><circle cx="10" cy="10" r="7" /><line x1="21" y1="21" x2="15" y2="15" /></svg>
                    </span>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="بحث باسم الصنف..." 
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      tabIndex="1"
                    />
                  </div>
                </div>
                <div className="col-md-6 text-md-end">
                  <h3 className="mb-0">
                    إجمالي قيمة المخزون: <span className="text-primary">{totalInventoryValue.toLocaleString()}</span>
                  </h3>
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm border-0">
            {loading ? (
              <div className="card-body text-center">
                <div className="spinner-border text-primary" role="status"></div>
                <div className="mt-2 text-muted">جاري تحميل البضاعة...</div>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table card-table table-vcenter text-nowrap datatable">
                  <thead>
                    <tr>
                      <th>اسم الصنف</th>
                      <th>الرصيد الحالي</th>
                      <th>سعر الشراء</th>
                      <th className="text-end">الإجراءات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.map(item => (
                      <tr key={item.id}>
                        <td>{item.name}</td>
                        <td>
                          <span className={`badge ${item.quantity <= 5 ? 'bg-danger-lt' : 'bg-success-lt'}`}>
                            {item.quantity} حتة
                          </span>
                        </td>
                        <td>{item.purchase_price}</td>
                        <td className="text-end">
                          <Link to={`/inventory/${item.id}`} className="btn btn-sm btn-outline-info me-2">
                            كارت الصنف
                          </Link>
                          <button onClick={() => openModal('edit', item)} className="btn btn-sm btn-outline-primary me-2">
                            تعديل
                          </button>
                          <button onClick={() => openModal('delete', item)} className="btn btn-sm btn-outline-danger">
                            مسح
                          </button>
                        </td>
                      </tr>
                    ))}
                    {filteredItems.length === 0 && (
                      <tr>
                        <td colSpan="4" className="text-center text-muted py-4">
                          مفيش بضاعة متسجلة لسه.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {modalType === 'add' && 'تسجيل صنف جديد'}
                  {modalType === 'edit' && 'تعديل بيانات الصنف'}
                  {modalType === 'delete' && 'تأكيد مسح الصنف'}
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)} aria-label="Close"></button>
              </div>
              <form onSubmit={handleSave}>
                <div className="modal-body">
                  {modalType === 'delete' ? (
                    <p>متأكد إنك عايز تمسح الصنف <strong>{selectedItem?.name}</strong> من البضاعة؟</p>
                  ) : (
                    <div className="row">
                      <div className="col-md-12 mb-3">
                        <label className="form-label">اسم الصنف</label>
                        <input type="text" className="form-control" name="name" value={formData.name} onChange={handleChange} required />
                      </div>
                      <div className="col-md-6 mb-3">
                        <label className="form-label">الرصيد الافتتاحي</label>
                        <input type="number" className="form-control" name="quantity" value={formData.quantity} onChange={handleChange} required disabled={modalType === 'edit'} />
                      </div>
                      <div className="col-md-6 mb-3">
                        <label className="form-label">سعر الشراء الافتتاحي (جنيه)</label>
                        <input type="number" step="0.01" className="form-control" name="purchase_price" value={formData.purchase_price} onChange={handleChange} required disabled={modalType === 'edit'} />
                      </div>
                      
                      {modalType === 'add' && (
                        <>
                          <div className="col-md-4 mb-3">
                            <label className="form-label">عمولة محصلة مسبقاً (جنيه)</label>
                            <input type="number" className="form-control" name="initial_commission_amount" value={formData.initial_commission_amount} onChange={handleChange} required />
                          </div>
                          <div className="col-md-4 mb-3">
                            <label className="form-label">شهر البداية</label>
                            <input type="number" className="form-control" name="initial_month" min="1" max="12" value={formData.initial_month} onChange={handleChange} required />
                          </div>
                          <div className="col-md-4 mb-3">
                            <label className="form-label">سنة البداية</label>
                            <input type="number" className="form-control" name="initial_year" value={formData.initial_year} onChange={handleChange} required />
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-link link-secondary" onClick={() => setShowModal(false)}>
                    إلغاء
                  </button>
                  <button type="submit" className={`btn ${modalType === 'delete' ? 'btn-danger' : 'btn-primary'} ms-auto`}>
                    {modalType === 'delete' ? 'أيوة، امسح' : 'حفظ التعديلات'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
