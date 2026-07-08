import React, { useState, useEffect } from 'react';
import { IconTrash, IconPlus, IconLoader } from '@tabler/icons-react';
import api from '../api';

export default function BranchesTab() {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newBranchName, setNewBranchName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [branchToDelete, setBranchToDelete] = useState(null);

  const fetchBranches = async () => {
    try {
      setLoading(true);
      const res = await api.get('/branches/');
      setBranches(res.data.results || res.data); // Support both paginated and flat lists
      setError(null);
    } catch (err) {
      console.error('Error fetching branches:', err);
      setError('فشل في جلب الفروع. يرجى التأكد من اتصال الخادم.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBranches();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newBranchName.trim()) return;
    
    try {
      setSubmitting(true);
      const res = await api.post('/branches/', { name: newBranchName.trim() });
      setBranches([...branches, res.data]);
      setNewBranchName('');
    } catch (err) {
      console.error('Error adding branch:', err);
      alert(err.response?.data?.detail || err.response?.data?.name?.[0] || 'حدث خطأ أثناء الإضافة.');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = (branch) => {
    setBranchToDelete(branch);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!branchToDelete) return;
    
    try {
      await api.delete(`/branches/${branchToDelete.id}/`);
      setBranches(branches.filter(b => b.id !== branchToDelete.id));
      setDeleteModalOpen(false);
      setBranchToDelete(null);
    } catch (err) {
      console.error('Error deleting branch:', err);
      alert(err.response?.data?.detail || 'لا يمكن حذف هذا الفرع لارتباطه ببيانات أخرى.');
    }
  };

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}
      
      {/* فورم الإضافة المفتوح دائماً */}
      <div className="card mb-3">
        <div className="card-body">
          <form onSubmit={handleAdd} className="row g-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">اسم الفرع <span className="text-danger">*</span></label>
              <input 
                type="text" 
                className="form-control" 
                value={newBranchName}
                onChange={(e) => setNewBranchName(e.target.value)}
                placeholder="أدخل اسم الفرع..."
                required 
                disabled={submitting || loading}
              />
            </div>
            <div className="col-md-2">
              <button type="submit" className="btn btn-primary w-100" disabled={submitting || loading}>
                {submitting ? <IconLoader className="icon-spin me-2" size={18} /> : <IconPlus size={18} className="me-2" />}
                إضافة فرع
              </button>
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
                <th>اسم الفرع</th>
                <th className="w-1">إجراء</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="3" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : branches.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center text-muted py-4">لا توجد فروع مضافة</td>
                </tr>
              ) : (
                branches.map((b, index) => (
                  <tr key={b.id}>
                    <td className="text-muted">{index + 1}</td>
                    <td className="fw-bold">{b.name}</td>
                    <td>
                      <button 
                        className="btn btn-ghost-danger btn-sm"
                        onClick={() => confirmDelete(b)}
                      >
                        <IconTrash size={18} />
                      </button>
                    </td>
                  </tr>
                ))
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
                <div className="text-muted">هل تريد حذف فرع "{branchToDelete?.name}"؟</div>
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
