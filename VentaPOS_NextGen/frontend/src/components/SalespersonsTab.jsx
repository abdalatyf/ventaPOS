import React, { useState, useEffect } from 'react';
import { IconTrash, IconPlus, IconEdit, IconCheck, IconX, IconLoader } from '@tabler/icons-react';
import api from '../api';

export default function SalespersonsTab() {
  const [salespersons, setSalespersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Branch context (simulated or fetched)
  const currentBranchId = localStorage.getItem('branchId') || 1; // Assuming default branch ID 1
  const currentBranchName = localStorage.getItem('branchName') || 'الفرع الرئيسي';

  // Add state
  const [newName, setNewName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  
  // Delete state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [spToDelete, setSpToDelete] = useState(null);

  const fetchSalespersons = async () => {
    try {
      setLoading(true);
      const res = await api.get('/salespersons/');
      setSalespersons(res.data.results || res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching salespersons:', err);
      setError('فشل في جلب المناديب. يرجى التأكد من اتصال الخادم.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSalespersons();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    
    try {
      setSubmitting(true);
      const payload = {
        name: newName.trim(),
      };
      if (currentBranchId && currentBranchId !== 1 && currentBranchId !== '1') {
        payload.branch = currentBranchId;
      }
      
      const res = await api.post('/salespersons/', payload);
      setSalespersons([...salespersons, res.data]);
      setNewName('');
    } catch (err) {
      console.error('Error adding salesperson:', err);
      alert(err.response?.data?.detail || err.response?.data?.name?.[0] || 'حدث خطأ أثناء الإضافة.');
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (sp) => {
    setEditingId(sp.id);
    setEditName(sp.name);
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const saveEdit = async (id) => {
    if (!editName.trim()) return; // منع الحفظ إذا كان الاسم فارغاً
    
    try {
      const res = await api.put(`/salespersons/${id}/`, { name: editName.trim() });
      setSalespersons(salespersons.map(sp => sp.id === id ? res.data : sp));
      setEditingId(null);
    } catch (err) {
      console.error('Error updating salesperson:', err);
      alert(err.response?.data?.detail || 'حدث خطأ أثناء التحديث.');
    }
  };

  const confirmDelete = (sp) => {
    setSpToDelete(sp);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!spToDelete) return;

    try {
      await api.delete(`/salespersons/${spToDelete.id}/`);
      setSalespersons(salespersons.filter(sp => sp.id !== spToDelete.id));
      setDeleteModalOpen(false);
      setSpToDelete(null);
    } catch (err) {
      console.error('Error deleting salesperson:', err);
      alert(err.response?.data?.detail || 'لا يمكن حذف هذا المندوب لارتباطه ببيانات أخرى.');
    }
  };

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}

      {/* فورم الإضافة */}
      <div className="card mb-3">
        <div className="card-body">
          <form onSubmit={handleAdd} className="row g-3 align-items-end">
            <div className="col-md-5">
              <label className="form-label">اسم المندوب <span className="text-danger">*</span></label>
              <input 
                type="text" 
                className="form-control" 
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="اسم المندوب..."
                required 
                disabled={submitting || loading}
              />
            </div>
            <div className="col-md-3">
              <button type="submit" className="btn btn-primary w-100" disabled={submitting || loading}>
                {submitting ? <IconLoader className="icon-spin me-2" size={18} /> : <IconPlus size={18} className="me-2" />}
                إضافة مندوب
              </button>
            </div>
            <div className="col-12 mt-2">
              <small className="text-muted">
                ملاحظة: سيتم تعيين المندوب للفرع الحالي: <strong>{currentBranchName}</strong>
              </small>
            </div>
          </form>
        </div>
      </div>

      {/* الجدول */}
      <div className="card">
        <div className="table-responsive">
          <table className="table table-vcenter card-table table-striped">
            <thead>
              <tr>
                <th className="w-1">م</th>
                <th>الاسم</th>
                <th className="w-1 text-center">تعديل</th>
                <th className="w-1 text-center">حذف</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : salespersons.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center text-muted py-4">لا يوجد مناديب في هذا الفرع</td>
                </tr>
              ) : (
                salespersons.map((sp, index) => {
                  const isEditing = editingId === sp.id;
                  
                  if (isEditing) {
                    return (
                      <tr key={sp.id} className="bg-light">
                        <td className="text-muted">{index + 1}</td>
                        <td>
                          <input 
                            type="text" 
                            className="form-control form-control-sm" 
                            value={editName} 
                            onChange={(e) => setEditName(e.target.value)}
                            autoFocus
                          />
                        </td>
                        <td colSpan="2" className="text-nowrap text-center">
                          <button className="btn btn-sm btn-success me-1" onClick={() => saveEdit(sp.id)}>
                            <IconCheck size={16} />
                          </button>
                          <button className="btn btn-sm btn-ghost-secondary" onClick={cancelEdit}>
                            <IconX size={16} />
                          </button>
                        </td>
                      </tr>
                    );
                  }

                  return (
                    <tr key={sp.id}>
                      <td className="text-muted">{index + 1}</td>
                      <td className="fw-bold">{sp.name}</td>
                      <td className="text-center">
                        <button className="btn btn-ghost-primary btn-sm" onClick={() => startEdit(sp)}>
                          <IconEdit size={18} />
                        </button>
                      </td>
                      <td className="text-center">
                        <button className="btn btn-ghost-danger btn-sm" onClick={() => confirmDelete(sp)}>
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
              <div className="modal-body text-center py-4">
                <IconTrash className="text-danger mb-2" size={48} stroke={1.5} />
                <h3>تأكيد الحذف</h3>
                <div className="text-muted">هل تريد حذف المندوب "{spToDelete?.name}"؟</div>
              </div>
              <div className="modal-footer">
                <div className="w-100">
                  <div className="row">
                    <div className="col">
                      <button className="btn w-100" onClick={() => setDeleteModalOpen(false)}>إلغاء</button>
                    </div>
                    <div className="col">
                      <button className="btn btn-danger w-100" onClick={handleDelete}>نعم، احذف</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
