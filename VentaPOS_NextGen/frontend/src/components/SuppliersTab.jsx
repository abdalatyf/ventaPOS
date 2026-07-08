import React, { useState, useEffect } from 'react';
import { IconTrash, IconPlus, IconLoader } from '@tabler/icons-react';
import api from '../api';

export default function SuppliersTab() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newSupplierName, setNewSupplierName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [supplierToDelete, setSupplierToDelete] = useState(null);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/suppliers/');
      setSuppliers(res.data.results || res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching suppliers:', err);
      setError('فشل في جلب الموردين. يرجى التأكد من اتصال الخادم.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newSupplierName.trim()) return;
    
    try {
      setSubmitting(true);
      const res = await api.post('/suppliers/', { name: newSupplierName.trim() });
      setSuppliers([...suppliers, res.data]);
      setNewSupplierName('');
    } catch (err) {
      console.error('Error adding supplier:', err);
      alert(err.response?.data?.detail || err.response?.data?.name?.[0] || 'حدث خطأ أثناء الإضافة.');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = (supplier) => {
    setSupplierToDelete(supplier);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!supplierToDelete) return;

    try {
      await api.delete(`/suppliers/${supplierToDelete.id}/`);
      setSuppliers(suppliers.filter(s => s.id !== supplierToDelete.id));
      setDeleteModalOpen(false);
      setSupplierToDelete(null);
    } catch (err) {
      console.error('Error deleting supplier:', err);
      alert(err.response?.data?.detail || 'لا يمكن حذف هذا المورد لارتباطه ببيانات أخرى.');
    }
  };

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}

      {/* فورم الإضافة المفتوح دائماً */}
      <div className="card mb-3">
        <div className="card-body">
          <form onSubmit={handleAdd} className="row g-3 align-items-end">
            <div className="col-md-5">
              <label className="form-label">اسم المورد / المصنع <span className="text-danger">*</span></label>
              <input 
                type="text" 
                className="form-control" 
                value={newSupplierName}
                onChange={(e) => setNewSupplierName(e.target.value)}
                placeholder="أدخل اسم المورد..."
                required 
                disabled={submitting || loading}
              />
            </div>
            <div className="col-md-2">
              <button type="submit" className="btn btn-primary w-100" disabled={submitting || loading}>
                {submitting ? <IconLoader className="icon-spin me-2" size={18} /> : <IconPlus size={18} className="me-2" />}
                إضافة مورد
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
                <th>اسم المورد</th>
                <th className="w-1">حذف</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="3" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : suppliers.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center text-muted py-4">لا يوجد موردين مضافين</td>
                </tr>
              ) : (
                suppliers.map((s, index) => (
                  <tr key={s.id}>
                    <td className="text-muted">{index + 1}</td>
                    <td className="fw-bold">{s.name}</td>
                    <td>
                      <button 
                        className="btn btn-ghost-danger btn-sm"
                        onClick={() => confirmDelete(s)}
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
                <div className="text-muted">هل تريد حذف المورد "{supplierToDelete?.name}"؟</div>
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
