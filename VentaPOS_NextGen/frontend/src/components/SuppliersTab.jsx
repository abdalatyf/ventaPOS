import React, { useState, useEffect, useRef } from 'react';
import { IconTrash, IconPlus, IconLoader, IconEdit, IconCheck, IconX, IconSortAscending, IconSortDescending, IconSearch } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import api from '../api';
import useSmartScroll from '../hooks/useSmartScroll';
import { useActiveBranch } from '../hooks/useActiveBranch';
import { useStandardTableSlots } from './common/StandardTablePageLayout';

export default function SuppliersTab() {
  const { setTableRef } = useSmartScroll();
  const { branchId, branchName } = useActiveBranch();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const showError = (msg) => {
    setError(msg);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => setError(null), 5000);
  };

  const currentBranchId = branchId || 1;
  const currentBranchName = branchName || 'الفرع الرئيسي';

  const submittingRef = useRef(false);
  const editSavingRef = useRef(false);
  const deletingRef = useRef(false);
  const fetchGenRef = useRef(0);
  const prevBranchIdRef = useRef(branchId);

  const nameInputRef = useRef(null);
  const [newSupplierName, setNewSupplierName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [supplierToDelete, setSupplierToDelete] = useState(null);

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

  const filteredAndSortedSuppliers = React.useMemo(() => {
    let filtered = suppliers.filter(s => (s.name || '').toLowerCase().includes(searchQuery.toLowerCase()));
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
  }, [suppliers, searchQuery, sortColumn, sortDirection]);

  const fetchSuppliers = async () => {
    const reqGen = ++fetchGenRef.current;
    try {
      setLoading(true);
      const res = await api.get('/suppliers/', { params: { branch_id: currentBranchId } });
      if (reqGen !== fetchGenRef.current) return;
      setSuppliers(res.data.results || res.data || []);
      setError(null);
    } catch (err) {
      if (reqGen !== fetchGenRef.current) return;
      console.error('Error fetching suppliers:', err);
      setError('فشل في جلب الموردين. يرجى التأكد من اتصال الخادم.');
    } finally {
      if (reqGen === fetchGenRef.current) setLoading(false);
    }
  };

  useEffect(() => {
    const prevBranch = prevBranchIdRef.current;
    if (prevBranch !== branchId) {
      prevBranchIdRef.current = branchId;
      setEditingId(null);
      setEditName('');
      setDeleteModalOpen(false);
      setSupplierToDelete(null);
      setSearchQuery('');
      setNewSupplierName('');
      setSuppliers([]);
    }
    fetchSuppliers();
  }, [currentBranchId, branchId]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (submittingRef.current) return;
    submittingRef.current = true;

    try {
      const cleanName = newSupplierName.trim();
      if (!cleanName) {
        const msg = 'اسم المورد مطلوب.';
        showError(msg);
        toast.error(msg);
        return;
      }

      try {
        setSubmitting(true);
        const res = await api.post('/suppliers/', { name: cleanName, branch: Number(currentBranchId) });
        setSuppliers(prev => [...prev, res.data]);
        setNewSupplierName('');
        toast.success('تم الحفظ بنجاح');
        nameInputRef.current?.focus();
      } catch (err) {
        console.error('Error adding supplier:', err);
        const errorMsg = err.response?.data?.detail || err.response?.data?.name?.[0] || 'حدث خطأ أثناء الإضافة.';
        showError(errorMsg);
        toast.error(errorMsg);
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  const startEdit = (s) => {
    setEditingId(s.id);
    setEditName(s.name);
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const saveEdit = async (id) => {
    if (editSavingRef.current) return;
    const cleanName = editName.trim();
    if (!cleanName) {
      toast.error('اسم المورد مطلوب.');
      return;
    }

    editSavingRef.current = true;
    try {
      const res = await api.put(`/suppliers/${id}/`, { name: cleanName, branch: Number(currentBranchId) });
      setSuppliers(prev => prev.map(s => s.id === id ? res.data : s));
      setEditingId(null);
    } catch (err) {
      console.error('Error updating supplier:', err);
      showError(err.response?.data?.detail || 'حدث خطأ أثناء التحديث.');
    } finally {
      editSavingRef.current = false;
    }
  };

  const confirmDelete = (supplier) => {
    setSupplierToDelete(supplier);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!supplierToDelete || deletingRef.current) return;
    deletingRef.current = true;

    try {
      await api.delete(`/suppliers/${supplierToDelete.id}/`);
      const deletedId = supplierToDelete.id;
      setSuppliers(prev => prev.filter(s => s.id !== deletedId));
      setDeleteModalOpen(false);
      setSupplierToDelete(null);
    } catch (err) {
      console.error('Error deleting supplier:', err);
      setDeleteModalOpen(false);
      showError(err.response?.data?.detail || 'لا يمكن حذف هذا المورد لارتباطه ببيانات أخرى.');
    } finally {
      deletingRef.current = false;
    }
  };

  // Slot injection into StandardTablePageLayout
  const slotPortals = useStandardTableSlots({
    row2: (
      <form noValidate onSubmit={handleAdd} className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
        <div className="flex-grow-1" style={{ minWidth: '200px' }}>
          <input 
            ref={nameInputRef} 
            type="text" 
            className="form-control form-control-sm border-secondary-subtle fw-bold" 
            value={newSupplierName} 
            onChange={(e) => setNewSupplierName(e.target.value)} 
            placeholder="اسم المورد / المصنع الجديد... *" 
            autoFocus 
            disabled={submitting || loading} 
          />
        </div>
        <button 
          type="submit" 
          className="btn btn-sm btn-primary fw-bold px-3 py-1 flex-shrink-0 d-flex align-items-center gap-1 border-secondary-subtle" 
          disabled={submitting || loading}
        >
          {submitting ? <IconLoader className="icon-spin" size={14} /> : <IconPlus size={14} />}
          <span>إضافة مورد</span>
        </button>
      </form>
    )
  });

  return (
    <div>
      {slotPortals}
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      {/* الجدول */}
      <div className="card shadow-sm border-secondary-subtle mb-0">
        {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
        <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
          <div className="d-flex align-items-center gap-2">
            <div className="input-icon position-relative" style={{ width: '260px' }}>
              <span className="input-icon-addon"><IconSearch size={14}/></span>
              <input 
                type="text" 
                className="form-control form-control-sm border-secondary-subtle fw-bold" 
                style={{ paddingLeft: searchQuery ? '2rem' : undefined }}
                placeholder="بحث حي عن مورد..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
              />
              {searchQuery && (
                <span
                  className="input-icon-addon cursor-pointer"
                  title="مسح الحقل"
                  onClick={() => setSearchQuery('')}
                  style={{
                    position: 'absolute',
                    left: '8px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 3,
                    cursor: 'pointer',
                    pointerEvents: 'auto',
                    color: '#6c757d',
                    fontSize: '14px',
                    lineHeight: 1,
                    padding: '2px 4px',
                  }}
                >
                  ✕
                </span>
              )}
            </div>
            <span className="badge bg-primary text-white rounded-pill px-2 py-1 tabular-nums flex-shrink-0">
              {filteredAndSortedSuppliers.length} مورد
            </span>
          </div>

          <div className="d-flex align-items-center">
            <span className="badge bg-light text-dark border border-secondary-subtle px-3 py-1 fs-5 fw-bold">
              الفرع: {currentBranchName}
            </span>
          </div>
        </div>

        {/* Row 2 of Table Card: Table Container */}
        <div ref={setTableRef} className="table-responsive report-table-container hide-vertical-scroll">
          <table className="table table-vcenter table-bordered table-hover text-nowrap table-sticky-header mb-0">
            <thead className="bg-light">
              <tr>
                <th className="w-1 text-center align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("id")}>رقم المورد {getSortIcon("id")}</th>
                <th className="text-start px-2 align-middle border-secondary-subtle" style={{cursor:"pointer"}} onClick={() => handleSort("name")}>اسم المورد {getSortIcon("name")}</th>
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
              ) : filteredAndSortedSuppliers.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center text-muted py-4">لا يوجد موردين مضافين</td>
                </tr>
              ) : (
                filteredAndSortedSuppliers.map((s) => {
                  const isEditing = editingId === s.id;
                  
                  if (isEditing) {
                    return (
                      <tr key={s.id} className="bg-light">
                        <td className="text-center align-middle border-secondary-subtle fw-bold text-muted">{s.id}</td>
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
                          <button className="btn btn-sm btn-success me-1" onClick={() => saveEdit(s.id)}>
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
                    <tr key={s.id}>
                      <td className="text-center align-middle border-secondary-subtle fw-bold text-muted">{s.id}</td>
                      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold">{s.name}</td>
                      <td className="text-center align-middle border-secondary-subtle">
                        <button className="btn btn-ghost-primary btn-sm" onClick={() => startEdit(s)}>
                          <IconEdit size={18} />
                        </button>
                      </td>
                      <td className="text-center align-middle border-secondary-subtle">
                        <button className="btn btn-ghost-danger btn-sm" onClick={() => confirmDelete(s)}>
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
