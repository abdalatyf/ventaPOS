import React, { useState, useEffect, useMemo } from 'react';
import { IconTrash, IconPlus, IconEdit, IconClockHour4, IconX, IconLoader } from '@tabler/icons-react';
import CommissionModal from './CommissionModal';
import api from '../api';
import { fmt } from '../utils/formatUtils';

export default function InventoryTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Branch context (simulated or fetched)
  const currentBranchId = localStorage.getItem('branchId') || 1;

  const [searchQuery, setSearchQuery] = useState('');
  
  // Form state
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    qty: '',
    price: '',
    commission: '',
    startMonth: new Date().getMonth() + 1,
    startYear: new Date().getFullYear(),
  });

  // Delete state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);

  // Commission Modal state
  const [commissionModalOpen, setCommissionModalOpen] = useState(false);
  const [commissionItem, setCommissionItem] = useState(null);
  const [commissionHistory, setCommissionHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await api.get('/inventory-items/');
      setItems(res.data.results || res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching inventory items:', err);
      setError('فشل في جلب الأصناف. يرجى التأكد من اتصال الخادم.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter(i => i.name.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [items, searchQuery]);

  const totalValue = useMemo(() => {
    return filteredItems.reduce((sum, item) => sum + ((item.current_stock ?? item.initial_quantity) * fmt(item.initial_purchase_price || 0)), 0);
  }, [filteredItems]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.startMonth || !formData.startYear) {
      alert('البيانات الأساسية مطلوبة');
      return;
    }

    const payload = {
      name: formData.name.trim(),
      initial_quantity: fmt(formData.qty) || 0,
      initial_purchase_price: fmt(formData.price) || 0,
      initial_commission_amount: fmt(formData.commission) || 0,
      initial_month: fmt(formData.startMonth),
      initial_year: fmt(formData.startYear),
    };

    if (currentBranchId && currentBranchId !== 1 && currentBranchId !== '1') {
      payload.branch = currentBranchId;
    }

    try {
      setSubmitting(true);
      if (editingId) {
        const res = await api.put(`/inventory-items/${editingId}/`, payload);
        setItems(items.map(i => i.id === editingId ? res.data : i));
        setEditingId(null);
      } else {
        const res = await api.post('/inventory-items/', payload);
        setItems([...items, res.data]);
      }
      resetForm();
    } catch (err) {
      console.error('Error saving item:', err);
      alert(err.response?.data?.detail || 'حدث خطأ أثناء الحفظ.');
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setFormData({
      name: item.name,
      qty: item.initial_quantity?.toString() || '0',
      price: item.initial_purchase_price?.toString() || '0',
      commission: item.initial_commission_amount?.toString() || '0',
      startMonth: item.initial_month,
      startYear: item.initial_year,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      name: '',
      qty: '',
      price: '',
      commission: '',
      startMonth: new Date().getMonth() + 1,
      startYear: new Date().getFullYear(),
    });
  };

  const confirmDelete = (item) => {
    setItemToDelete(item);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;

    try {
      await api.delete(`/inventory-items/${itemToDelete.id}/`);
      setItems(items.filter(i => i.id !== itemToDelete.id));
      setDeleteModalOpen(false);
      setItemToDelete(null);
      if (editingId === itemToDelete.id) resetForm();
    } catch (err) {
      console.error('Error deleting item:', err);
      alert(err.response?.data?.detail || 'لا يمكن حذف هذا الصنف.');
    }
  };

  const openCommissionModal = async (item) => {
    setCommissionItem(item);
    setCommissionModalOpen(true);
    setLoadingHistory(true);
    
    try {
      const res = await api.get(`/commission-histories/?inventory_item=${item.id}`);
      // Ensure we map the API response to what the Modal expects (amount, month, year)
      const mapped = (res.data.results || res.data).map(h => ({
        id: h.id,
        amount: fmt(h.commission_amount),
        month: h.activation_month,
        year: h.activation_year
      }));
      setCommissionHistory(mapped);
    } catch (err) {
      console.error('Error fetching commission history', err);
      setCommissionHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleAddCommission = async (newComm) => {
    try {
      const payload = {
        inventory_item: commissionItem.id,
        commission_amount: newComm.amount,
        activation_month: newComm.month,
        activation_year: newComm.year,
      };
      const res = await api.post('/commission-histories/', payload);
      
      const savedRecord = {
        id: res.data.id,
        amount: fmt(res.data.commission_amount),
        month: res.data.activation_month,
        year: res.data.activation_year,
      };
      
      const updatedHistory = [...commissionHistory, savedRecord].sort((a, b) => (a.year - b.year) || (a.month - b.month));
      setCommissionHistory(updatedHistory);
      
      // Update local item current commission for display (approximate)
      const latest = updatedHistory[updatedHistory.length - 1];
      setItems(items.map(i => i.id === commissionItem.id ? { ...i, initial_commission_amount: latest.amount } : i));
      
    } catch (err) {
      console.error('Error adding commission', err);
      alert('فشل إضافة العمولة');
    }
  };

  const handleDeleteCommission = async (recordId) => {
    try {
      await api.delete(`/commission-histories/${recordId}/`);
      const updatedHistory = commissionHistory.filter(h => h.id !== recordId);
      setCommissionHistory(updatedHistory);
      
      // Update local item current commission for display (approximate)
      const latest = updatedHistory.length > 0 ? updatedHistory[updatedHistory.length - 1] : { amount: commissionItem.initial_commission_amount };
      setItems(items.map(i => i.id === commissionItem.id ? { ...i, initial_commission_amount: latest.amount } : i));
    } catch (err) {
      console.error('Error deleting commission', err);
      alert('فشل حذف العمولة');
    }
  };

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}

      {/* الشريط العلوي للبحث */}
      <div className="row mb-3 align-items-center">
        <div className="col-md-6">
          <div className="input-icon">
            <span className="input-icon-addon"><svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><circle cx="10" cy="10" r="7" /><line x1="21" y1="21" x2="15" y2="15" /></svg></span>
            <input 
              type="text" 
              className="form-control" 
              placeholder="بحث حي عن الصنف..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="col-md-6 text-md-end mt-2 mt-md-0">
          <span className="me-4 text-muted">عدد الأصناف: <strong>{filteredItems.length}</strong></span>
          <span className="text-muted">إجمالي التكلفة: <strong className="text-primary">{totalValue.toLocaleString()}</strong></span>
        </div>
      </div>

      {/* فورم الإضافة / التعديل */}
      <div className={`card mb-3 ${editingId ? 'border-primary' : ''}`}>
        <div className="card-header bg-transparent pb-2 pt-3">
          <h3 className="card-title text-primary fw-bold">
            {editingId ? `تعديل الصنف: ${formData.name}` : 'إضافة صنف جديد'}
          </h3>
          {editingId && (
            <div className="card-actions">
              <button className="btn btn-sm btn-ghost-secondary" onClick={resetForm}>إلغاء التعديل</button>
            </div>
          )}
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit} className="row g-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">اسم الصنف <span className="text-danger">*</span></label>
              <input type="text" className="form-control" name="name" value={formData.name} onChange={handleInputChange} disabled={submitting} required />
            </div>
            <div className="col-md-2">
              <label className="form-label">الرصيد الافتتاحي</label>
              <input type="number" className="form-control" name="qty" value={formData.qty} onChange={handleInputChange} min="0" disabled={submitting} />
            </div>
            <div className="col-md-2">
              <label className="form-label">سعر الشراء الافتتاحي</label>
              <input type="number" className="form-control" name="price" value={formData.price} onChange={handleInputChange} step="0.01" disabled={submitting} />
            </div>
            <div className="col-md-2">
              <label className="form-label">العمولة الافتتاحية</label>
              <input type="number" className="form-control" name="commission" value={formData.commission} onChange={handleInputChange} step="0.01" disabled={submitting} />
            </div>
            
            <div className="col-md-2"></div>

            <div className="col-md-2 mt-2">
              <label className="form-label">شهر البداية</label>
              <select className="form-select" name="startMonth" value={formData.startMonth} onChange={handleInputChange} disabled={submitting} required>
                {[...Array(12)].map((_, i) => <option key={i+1} value={i+1}>{i+1}</option>)}
              </select>
            </div>
            <div className="col-md-2 mt-2">
              <label className="form-label">سنة البداية</label>
              <input type="number" className="form-control" name="startYear" value={formData.startYear} onChange={handleInputChange} disabled={submitting} required />
            </div>
            
            <div className="col-md-8 text-end mt-2">
              <button type="submit" className={`btn ${editingId ? 'btn-success' : 'btn-primary'}`} disabled={submitting}>
                {submitting ? <IconLoader className="icon-spin me-2" size={18} /> : (editingId ? <IconEdit size={18} className="me-2" /> : <IconPlus size={18} className="me-2" />)}
                {editingId ? 'حفظ التعديلات' : 'حفظ في المخزن'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* الجدول */}
      <div className="card">
        <div className="table-responsive">
          <table className="table table-vcenter card-table table-striped table-hover">
            <thead>
              <tr>
                <th className="w-1">م</th>
                <th>الصنف</th>
                <th>الكمية الحالية</th>
                <th>سعر الشراء الافتتاحي</th>
                <th>التكلفة الكلية</th>
                <th>البداية</th>
                <th>العمولة الافتتاحية</th>
                <th className="text-center">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center text-muted py-4">لا توجد أصناف مطابقة</td>
                </tr>
              ) : (
                filteredItems.map((item, index) => {
                  const currentQty = item.current_stock ?? item.initial_quantity;
                  const total = currentQty * fmt(item.initial_purchase_price || 0);
                  
                  return (
                    <tr key={item.id} className={editingId === item.id ? 'bg-primary-lt' : ''}>
                      <td className="text-muted">{index + 1}</td>
                      <td className="fw-bold">{item.name}</td>
                      <td>
                        <span className={`badge ${currentQty <= 5 ? 'bg-danger' : 'bg-success'} me-2`}> </span>
                        {currentQty}
                      </td>
                      <td>{fmt(item.initial_purchase_price || 0)}</td>
                      <td className="text-muted">{total.toLocaleString()}</td>
                      <td>{item.initial_month}/{item.initial_year}</td>
                      <td>{fmt(item.initial_commission_amount || 0)}</td>
                      <td className="text-nowrap text-center">
                        <button className="btn btn-sm btn-ghost-info me-1" title="آلة زمن العمولة" onClick={() => openCommissionModal(item)}>
                          <IconClockHour4 size={18} /> العمولة
                        </button>
                        <button className="btn btn-sm btn-ghost-primary me-1" onClick={() => startEdit(item)}>
                          <IconEdit size={18} />
                        </button>
                        <button className="btn btn-sm btn-ghost-danger" onClick={() => confirmDelete(item)}>
                          <IconTrash size={18} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* مودال تأكيد الحذف */}
      {deleteModalOpen && (
        <div className="modal modal-blur fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-sm modal-dialog-centered" role="document">
            <div className="modal-content">
              <button type="button" className="btn-close" onClick={() => setDeleteModalOpen(false)} style={{position: 'absolute', top: 15, left: 15}}></button>
              <div className="modal-body text-center py-4">
                <IconTrash className="text-danger mb-2" size={48} stroke={1.5} />
                <h3>تأكيد الحذف</h3>
                <div className="text-muted">هل تريد حذف الصنف "{itemToDelete?.name}"؟ <br/><strong className="text-danger">⚠️ سيتم حذف كل بيانات العمولة المرتبطة.</strong></div>
              </div>
              <div className="modal-footer">
                <div className="w-100">
                  <div className="row">
                    <div className="col"><button className="btn w-100" onClick={() => setDeleteModalOpen(false)}>إلغاء</button></div>
                    <div className="col"><button className="btn btn-danger w-100" onClick={handleDelete}>نعم، احذف</button></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* مودال العمولة (المستقل) */}
      <CommissionModal 
        show={commissionModalOpen}
        item={commissionItem}
        history={commissionHistory}
        loading={loadingHistory}
        onClose={() => setCommissionModalOpen(false)}
        onAddCommission={handleAddCommission}
        onDeleteCommission={handleDeleteCommission}
      />
    </div>
  );
}
