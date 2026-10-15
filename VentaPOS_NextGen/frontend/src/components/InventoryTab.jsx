import React, { useState, useEffect, useMemo, useRef } from 'react';
import { IconTrash, IconPlus, IconEdit, IconClockHour4, IconX, IconLoader, IconSortAscending, IconSortDescending } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import CommissionModal from './CommissionModal';
import api from '../api';
import { fmt, parseNumber } from '../utils/formatUtils';

export default function InventoryTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const showError = (msg) => {
    setError(msg);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => setError(null), 5000);
  };
  
  // Branch context (simulated or fetched)
  const currentBranchId = localStorage.getItem('branchId') || 1;

  const [searchQuery, setSearchQuery] = useState('');

  const [sortColumn, setSortColumn] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (column) => {
    if (sortColumn !== column) return null;
    return sortDirection === 'asc' ? <IconSortAscending size={16} className="ms-1" /> : <IconSortDescending size={16} className="ms-1" />;
  };
  
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

  const nameInputRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.target.tagName !== 'BUTTON') {
      e.preventDefault();
      const form = e.target.form;
      if (!form) return;
      const index = Array.prototype.indexOf.call(form.elements, e.target);
      for (let i = index + 1; i < form.elements.length; i++) {
        if (!form.elements[i].disabled && form.elements[i].type !== 'hidden') {
          form.elements[i].focus();
          break;
        }
      }
    }
  };

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
    let filtered = items.filter(i => i.name.toLowerCase().includes(searchQuery.toLowerCase()));
    
    filtered.sort((a, b) => {
      let valA, valB;
      
      if (sortColumn === 'date') {
        valA = (a.initial_year || 0) * 100 + (a.initial_month || 0);
        valB = (b.initial_year || 0) * 100 + (b.initial_month || 0);
      } else {
        valA = a[sortColumn];
        valB = b[sortColumn];
        if (sortColumn !== 'name') {
          valA = parseNumber(valA || 0);
          valB = parseNumber(valB || 0);
        }
      }

      if (valA === undefined || valA === null) valA = '';
      if (valB === undefined || valB === null) valB = '';

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    
    return filtered;
  }, [items, searchQuery, sortColumn, sortDirection]);



  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.startMonth || !formData.startYear) {
      const msg = 'البيانات الأساسية مطلوبة';
      showError(msg);
      toast.error(msg);
      return;
    }

    const payload = {
      name: formData.name.trim(),
      initial_quantity: Math.round(parseNumber(formData.qty)) || 0,
      initial_purchase_price: Math.round(parseNumber(formData.price)) || 0,
      initial_commission_amount: Math.round(parseNumber(formData.commission)) || 0,
      initial_month: Math.round(parseNumber(formData.startMonth)),
      initial_year: Math.round(parseNumber(formData.startYear)),
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
      toast.success('تم الحفظ بنجاح');
    } catch (err) {
      console.error('Error saving item:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'حدث خطأ أثناء الحفظ.';
      showError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setFormData({
      name: item.name,
      qty: Math.round(Number(item.initial_quantity || 0)).toString(),
      price: Math.round(Number(item.initial_purchase_price || 0)).toString(),
      commission: Math.round(Number(item.initial_commission_amount || 0)).toString(),
      startMonth: item.initial_month,
      startYear: item.initial_year,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => nameInputRef.current && nameInputRef.current.focus(), 100);
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
    if (nameInputRef.current) nameInputRef.current.focus();
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
      setDeleteModalOpen(false);
      showError(err.response?.data?.detail || 'لا يمكن حذف هذا الصنف.');
    }
  };

  const openCommissionModal = async (item) => {
    setCommissionItem(item);
    setCommissionModalOpen(true);
    setLoadingHistory(true);
    
    try {
      const res = await api.get(`/commission-histories/?item_id=${item.id}`);
      // Ensure we map the API response to what the Modal expects (amount, month, year)
      const mapped = (res.data.results || res.data).map(h => ({
        id: h.id,
        amount: fmt(h.commission_amount),
        month: Number(h.activation_month),
        year: Number(h.activation_year)
      })).sort((a, b) => (a.year - b.year) || (a.month - b.month));
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
        item: commissionItem.id,
        commission_amount: newComm.amount,
        activation_month: newComm.month,
        activation_year: newComm.year,
      };
      const res = await api.post('/commission-histories/', payload);
      
      const savedRecord = {
        id: res.data.id,
        amount: fmt(res.data.commission_amount),
        month: Number(res.data.activation_month),
        year: Number(res.data.activation_year),
      };
      
      const updatedHistory = [...commissionHistory, savedRecord].sort((a, b) => (a.year - b.year) || (a.month - b.month));
      setCommissionHistory(updatedHistory);
      
      // Update local item current commission for display (approximate)
      const latest = updatedHistory[updatedHistory.length - 1];
      setItems(items.map(i => i.id === commissionItem.id ? { ...i, initial_commission_amount: latest.amount } : i));
      
    } catch (err) {
      console.error('Error adding commission', err);
      const errorMsg = err.response?.data?.detail || err.message || 'فشل إضافة العمولة';
      showError(errorMsg);
      toast.error(errorMsg);
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
      showError('فشل حذف العمولة');
    }
  };

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}



      <div className="accordion mb-3 shadow-sm" id="addInventoryAccordion">
        <div className={`accordion-item ${editingId ? 'border-primary' : ''}`}>
          <h2 className="accordion-header" id="headingAddInventory">
            <button className={`accordion-button ${editingId ? '' : 'collapsed'} py-2 bg-light`} type="button" data-bs-toggle="collapse" data-bs-target="#collapseAddInventory" aria-expanded={editingId ? 'true' : 'false'} aria-controls="collapseAddInventory">
              <span className="fw-bold text-primary d-flex align-items-center">
                {editingId ? <IconEdit size={18} className="me-2"/> : <IconPlus size={18} className="me-2"/>}
                {editingId ? `تعديل الصنف: ${formData.name}` : 'إضافة صنف جديد'}
              </span>
            </button>
          </h2>
          <div id="collapseAddInventory" className={`accordion-collapse collapse ${editingId ? 'show' : ''}`} aria-labelledby="headingAddInventory" data-bs-parent="#addInventoryAccordion">
            <div className="accordion-body p-2 bg-white">
              <form onSubmit={handleSubmit} onKeyDown={handleKeyDown} className="row g-2 align-items-end">
                <div className="col-md-2">
                  <label className="form-label small mb-1">اسم الصنف <span className="text-danger">*</span></label>
                  <input type="text" className="form-control form-control-sm" name="name" value={formData.name} onChange={handleInputChange} disabled={submitting} required autoFocus ref={nameInputRef} />
                </div>
                <div className="col-md-1">
                  <label className="form-label small mb-1">الكمية</label>
                  <input type="number" className="form-control form-control-sm" name="qty" value={formData.qty} onChange={handleInputChange} min="0" disabled={submitting} />
                </div>
                <div className="col-md-2">
                  <label className="form-label small mb-1">سعر الشراء</label>
                  <input type="number" className="form-control form-control-sm" name="price" value={formData.price} onChange={handleInputChange} min="0" disabled={submitting} />
                </div>
                <div className="col-md-2">
                  <label className="form-label small mb-1">المندبة</label>
                  <input type="number" className="form-control form-control-sm" name="commission" value={formData.commission} onChange={handleInputChange} disabled={submitting} />
                </div>
                <div className="col-md-1">
                  <label className="form-label small mb-1">شهر</label>
                  <input 
                    type="number" 
                    className="form-control form-control-sm" 
                    name="startMonth" 
                    value={formData.startMonth} 
                    min="1" 
                    max="12" 
                    placeholder="شهر" 
                    onChange={handleInputChange} 
                    disabled={submitting} 
                    required 
                  />
                </div>
                <div className="col-md-1">
                  <label className="form-label small mb-1">سنة</label>
                  <input 
                    type="number" 
                    className="form-control form-control-sm" 
                    name="startYear" 
                    value={formData.startYear} 
                    min="2000" 
                    max="2100" 
                    placeholder="سنة" 
                    onChange={handleInputChange} 
                    disabled={submitting} 
                    required 
                  />
                </div>
                <div className="col-md-3 d-flex align-items-end gap-1">
                  <button type="submit" className={`btn btn-sm w-100 ${editingId ? 'btn-success' : 'btn-primary'}`} disabled={submitting}>
                    {submitting ? <IconLoader className="icon-spin" size={16} /> : (editingId ? <IconEdit size={16} /> : <IconPlus size={16} />)}
                    <span className="ms-1">{editingId ? 'حفظ' : 'إضافة'}</span>
                  </button>
                  {editingId && (
                    <button type="button" className="btn btn-sm btn-ghost-secondary px-2" onClick={resetForm}>إلغاء</button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      
      <div className="d-flex justify-content-between align-items-center mb-2">
        <div className="input-icon w-50">
          <span className="input-icon-addon"><svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><circle cx="10" cy="10" r="7" /><line x1="21" y1="21" x2="15" y2="15" /></svg></span>
          <input 
            type="text" 
            className="form-control form-control-sm border-secondary-subtle" 
            placeholder="بحث حي عن الصنف..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="text-end">
          <span className="text-muted small">عدد الأصناف: <strong>{filteredItems.length}</strong></span>
        </div>
      </div>

      {/* الجدول */}
      <div className="card shadow-sm" style={{ border: '1px solid #dee2e6' }}>
        <table className="table table-vcenter table-bordered table-hover text-nowrap table-sticky-header mb-0">
            <thead className="bg-light">
              <tr>
                <th className="w-1 text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("id")}>رقم الصنف {getSortIcon("id")}</th>
                <th className="text-start px-2 align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("name")}>الصنف {getSortIcon("name")}</th>
                <th className="text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("initial_quantity")}>الكمية أول مدة {getSortIcon("initial_quantity")}</th>
                <th className="text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("initial_purchase_price")}>سعر الشراء أول مدة {getSortIcon("initial_purchase_price")}</th>
                <th className="text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("date")}>البداية {getSortIcon("date")}</th>
                <th className="text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("initial_commission_amount")}>المندبة أول مدة {getSortIcon("initial_commission_amount")}</th>
                <th className="text-center align-middle border-secondary-subtle">إجراءات</th>
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
                  const initialQty = item.initial_quantity || 0;
                  const total = initialQty * parseNumber(item.initial_purchase_price || 0);
                  
                  return (
                    <tr key={item.id} className={editingId === item.id ? 'bg-primary-lt' : ''}>
                      <td className="text-center align-middle border-secondary-subtle text-muted fw-bold">{item.id}</td>
                      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold">{item.name}</td>
                      <td className="text-center align-middle border-secondary-subtle">
                        {initialQty}
                      </td>
                      <td className="text-center align-middle border-secondary-subtle">{fmt(item.initial_purchase_price || 0)}</td>
                      <td className="text-center align-middle border-secondary-subtle">{item.initial_year}/{item.initial_month}</td>
                      <td className="text-center align-middle border-secondary-subtle">{fmt(item.initial_commission_amount || 0)}</td>
                      <td className="text-nowrap text-center align-middle border-secondary-subtle">
                        <button className="btn btn-sm btn-ghost-info me-1" title="آلة زمن المندبة" onClick={() => openCommissionModal(item)}>
                          <IconClockHour4 size={18} /> المندبة
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
