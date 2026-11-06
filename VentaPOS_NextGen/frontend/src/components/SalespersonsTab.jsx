import React, { useState, useEffect, useRef } from 'react';
import { IconTrash, IconPlus, IconEdit, IconCheck, IconX, IconLoader, IconSortAscending, IconSortDescending, IconSearch } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import api from '../api';
import useSmartScroll from '../hooks/useSmartScroll';
import { useStandardTableSlots } from './common/StandardTablePageLayout';

export default function SalespersonsTab() {
  const { setTableRef } = useSmartScroll();
  const [salespersons, setSalespersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const showError = (msg) => {
    setError(msg);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => setError(null), 5000);
  };
  
  const currentBranchId = localStorage.getItem('branchId') || 1;
  const currentBranchName = localStorage.getItem('branchName') || 'الفرع الرئيسي';

  // Add state
  const nameInputRef = useRef(null);
  const [newName, setNewName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  
  // Delete state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [spToDelete, setSpToDelete] = useState(null);

  // Sort and Search
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

  const filteredAndSortedSalespersons = React.useMemo(() => {
    let filtered = salespersons.filter(sp => (sp.name || '').toLowerCase().includes(searchQuery.toLowerCase()));
    filtered.sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();
      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return filtered;
  }, [salespersons, searchQuery, sortColumn, sortDirection]);

  const fetchSalespersons = async () => {
    try {
      setLoading(true);
      const res = await api.get('/salespersons/', { params: { branch_id: currentBranchId } });
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
  }, [currentBranchId]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    
    try {
      setSubmitting(true);
      const payload = {
        name: newName.trim(),
      };
      if (currentBranchId) {
        payload.branch = currentBranchId;
      }
      
      const res = await api.post('/salespersons/', payload);
      setSalespersons([...salespersons, res.data]);
      setNewName('');
      toast.success('تم الحفظ بنجاح');
      nameInputRef.current?.focus();
    } catch (err) {
      console.error('Error adding salesperson:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.name?.[0] || 'حدث خطأ أثناء الإضافة.';
      showError(errorMsg);
      toast.error(errorMsg);
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
    if (!editName.trim()) return;
    
    try {
      const res = await api.put(`/salespersons/${id}/`, { name: editName.trim() });
      setSalespersons(salespersons.map(sp => sp.id === id ? res.data : sp));
      setEditingId(null);
    } catch (err) {
      console.error('Error updating salesperson:', err);
      showError(err.response?.data?.detail || 'حدث خطأ أثناء التحديث.');
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
      setDeleteModalOpen(false);
      showError(err.response?.data?.detail || 'لا يمكن حذف هذا المندوب لارتباطه ببيانات أخرى.');
    }
  };

  // Slot injection into StandardTablePageLayout
  const slotPortals = useStandardTableSlots({
    row1Extra: (
      <div className="d-flex align-items-center gap-2 ms-auto flex-nowrap" style={{ overflow: 'visible' }}>
        <div className="input-icon" style={{ width: '220px' }}>
          <span className="input-icon-addon"><IconSearch size={14}/></span>
          <input 
            type="text" 
            className="form-control form-control-sm border-secondary-subtle fw-bold" 
            placeholder="بحث حي عن مندوب..." 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
          />
        </div>
        <span className="badge bg-secondary text-white rounded-pill px-2 py-1 tabular-nums flex-shrink-0">
          {filteredAndSortedSalespersons.length} مندوب
        </span>
      </div>
    ),
    row2: (
      <form onSubmit={handleAdd} className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
        <div className="flex-grow-1" style={{ minWidth: '200px' }}>
          <input 
            ref={nameInputRef} 
            type="text" 
            className="form-control form-control-sm border-secondary-subtle fw-bold" 
            value={newName} 
            onChange={(e) => setNewName(e.target.value)} 
            placeholder="اسم المندوب الجديد... *" 
            required 
            autoFocus 
            disabled={submitting || loading} 
          />
        </div>
        <div className="text-muted small flex-shrink-0 px-2">
          فرع: <strong>{currentBranchName}</strong>
        </div>
        <button 
          type="submit" 
          className="btn btn-sm btn-primary fw-bold px-3 py-1 flex-shrink-0 d-flex align-items-center gap-1 border-secondary-subtle" 
          disabled={submitting || loading}
        >
          {submitting ? <IconLoader className="icon-spin" size={14} /> : <IconPlus size={14} />}
          <span>إضافة مندوب</span>
        </button>
      </form>
    )
  });

  return (
    <div>
      {slotPortals}
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      {/* الجدول */}
      <div className="card shadow-sm border-secondary-subtle">
        <div ref={setTableRef} className="table-responsive report-table-container">
          <table className="table table-vcenter table-bordered table-hover text-nowrap table-sticky-header mb-0">
            <thead className="bg-light">
              <tr>
                <th className="w-1 text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("id")}>رقم المندوب {getSortIcon("id")}</th>
                <th className="text-start px-2 align-middle border-secondary-subtle">الاسم</th>
                <th className="w-1 text-center align-middle border-secondary-subtle">تعديل</th>
                <th className="w-1 text-center align-middle border-secondary-subtle">حذف</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : filteredAndSortedSalespersons.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center text-muted py-4">لا يوجد مناديب في هذا الفرع</td>
                </tr>
              ) : (
                filteredAndSortedSalespersons.map((sp) => {
                  const isEditing = editingId === sp.id;
                  
                  if (isEditing) {
                    return (
                      <tr key={sp.id} className="bg-light">
                        <td className="text-center align-middle border-secondary-subtle fw-bold text-muted">{sp.id}</td>
                        <td className="text-start px-2 align-middle border-secondary-subtle">
                          <input 
                            type="text" 
                            className="form-control form-control-sm border-secondary-subtle fw-bold" 
                            value={editName} 
                            onChange={(e) => setEditName(e.target.value)}
                            autoFocus
                          />
                        </td>
                        <td colSpan="2" className="text-nowrap text-center align-middle border-secondary-subtle">
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
                      <td className="text-center align-middle border-secondary-subtle fw-bold text-muted">{sp.id}</td>
                      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold">{sp.name}</td>
                      <td className="text-center align-middle border-secondary-subtle">
                        <button className="btn btn-ghost-primary btn-sm" onClick={() => startEdit(sp)}>
                          <IconEdit size={18} />
                        </button>
                      </td>
                      <td className="text-center align-middle border-secondary-subtle">
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
