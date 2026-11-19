import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import { IconTrash, IconPlus, IconEdit, IconLoader, IconSortAscending, IconSortDescending, IconFileText, IconSearch } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import api from '../api';
import useSmartScroll from '../hooks/useSmartScroll';
import { useActiveBranch } from '../hooks/useActiveBranch';
import { fmt, parseNumber, parseStrictInt, parseWholeMoney, parseValidMonthYear, formatMMYYYY } from '../utils/formatUtils';
import { useStandardTableSlots } from './common/StandardTablePageLayout';

export default function InventoryTab() {
  const { setTableRef } = useSmartScroll();
  const { branchId, branchName } = useActiveBranch();
  const [items, setItems] = useState([]);
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
  const deletingRef = useRef(false);
  const fetchGenRef = useRef(0);
  const prevBranchIdRef = useRef(branchId);

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
  const [deleting, setDeleting] = useState(false);
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
    const reqGen = ++fetchGenRef.current;
    try {
      setLoading(true);
      const res = await api.get('/inventory-items/', { params: { branch_id: currentBranchId } });
      if (reqGen !== fetchGenRef.current) return;
      const list = Array.isArray(res.data?.results) ? res.data.results : (Array.isArray(res.data) ? res.data : []);
      setItems(list);
      setError(null);
    } catch (err) {
      if (reqGen !== fetchGenRef.current) return;
      console.error('Error fetching inventory items:', err);
      setError('فشل في جلب الأصناف. يرجى التأكد من اتصال الخادم.');
    } finally {
      if (reqGen === fetchGenRef.current) setLoading(false);
    }
  };

  useEffect(() => {
    const prevBranch = prevBranchIdRef.current;
    if (prevBranch !== branchId) {
      prevBranchIdRef.current = branchId;
      setEditingId(null);
      setDeleteModalOpen(false);
      setItemToDelete(null);
      setSearchQuery('');
      setItems([]);
      setFormData({
        name: '',
        qty: '',
        price: '',
        commission: '',
        startMonth: new Date().getMonth() + 1,
        startYear: new Date().getFullYear(),
      });
    }
    fetchItems();
  }, [currentBranchId, branchId]);

  const filteredItems = useMemo(() => {
    const list = Array.isArray(items) ? items : [];
    let filtered = list.filter(i => (i.name || '').toLowerCase().includes(searchQuery.toLowerCase()));
    
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
    if (submittingRef.current) return;
    submittingRef.current = true;

    try {
      const cleanName = formData.name.trim();
      if (!cleanName) {
        const msg = 'اسم الصنف مطلوب.';
        showError(msg);
        toast.error(msg);
        return;
      }

      const validDate = parseValidMonthYear(formData.startMonth, formData.startYear, { minYear: 2025, maxYear: 2100 });
      if (!validDate) {
        const msg = 'أدخل شهر وسنة بداية صحيحين (2025 فأحدث).';
        showError(msg);
        toast.error(msg);
        return;
      }

      const qtyTrimmed = String(formData.qty ?? '').trim();
      const qtyVal = qtyTrimmed === '' ? 0 : parseStrictInt(qtyTrimmed, { min: 0 });
      if (qtyVal === null) {
        const msg = 'الكمية يجب أن تكون رقمًا صحيحًا (0 أو أكثر).';
        showError(msg);
        toast.error(msg);
        return;
      }

      const priceTrimmed = String(formData.price ?? '').trim();
      const priceVal = priceTrimmed === '' ? 0 : parseWholeMoney(priceTrimmed, { min: 0 });
      if (priceVal === null) {
        const msg = 'سعر الشراء يجب أن يكون رقمًا صحيحًا (0 أو أكثر).';
        showError(msg);
        toast.error(msg);
        return;
      }

      const commTrimmed = String(formData.commission ?? '').trim();
      const commVal = commTrimmed === '' ? 0 : parseWholeMoney(commTrimmed, { min: 0 });
      if (commVal === null) {
        const msg = 'المندبة يجب أن تكون رقمًا صحيحًا (0 أو أكثر).';
        showError(msg);
        toast.error(msg);
        return;
      }

      const payload = {
        name: cleanName,
        initial_quantity: qtyVal,
        initial_purchase_price: priceVal,
        initial_commission_amount: commVal,
        initial_month: validDate.month,
        initial_year: validDate.year,
        branch: Number(currentBranchId),
      };

      try {
        setSubmitting(true);
        if (editingId) {
          const res = await api.put(`/inventory-items/${editingId}/`, payload);
          setItems(prev => prev.map(i => i.id === editingId ? res.data : i));
          setEditingId(null);
        } else {
          const res = await api.post('/inventory-items/', payload);
          setItems(prev => [...prev, res.data]);
        }
        resetForm();
        toast.success('تم الحفظ بنجاح');
      } catch (err) {
        console.error('Error saving item:', err);
        const errorMsg = err.response?.data?.detail || err.response?.data?.name?.[0] || err.response?.data?.error || err.message || 'حدث خطأ أثناء الحفظ.';
        showError(errorMsg);
        toast.error(errorMsg);
      }
    } finally {
      submittingRef.current = false;
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
    if (!itemToDelete || deletingRef.current) return;
    deletingRef.current = true;
    setDeleting(true);

    try {
      await api.delete(`/inventory-items/${itemToDelete.id}/`);
      const deletedId = itemToDelete.id;
      setItems(prev => prev.filter(i => i.id !== deletedId));
      setDeleteModalOpen(false);
      setItemToDelete(null);
      if (editingId === deletedId) resetForm();
    } catch (err) {
      console.error('Error deleting item:', err);
      setDeleteModalOpen(false);
      showError(err.response?.data?.detail || 'لا يمكن حذف هذا الصنف.');
    } finally {
      deletingRef.current = false;
      setDeleting(false);
    }
  };

  // Slot injection into StandardTablePageLayout
  const slotPortals = useStandardTableSlots({
    row2: (
      <form noValidate onSubmit={handleSubmit} onKeyDown={handleKeyDown} className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
        {/* Item Name */}
        <div className="flex-grow-1" style={{ minWidth: '160px' }}>
          <input 
            ref={nameInputRef} 
            type="text" 
            className="form-control form-control-sm border-secondary-subtle fw-bold" 
            name="name" 
            placeholder="اسم الصنف *" 
            value={formData.name} 
            onChange={handleInputChange} 
            disabled={submitting} 
            autoFocus 
          />
        </div>
        {/* Qty */}
        <div style={{ width: '85px' }} className="flex-shrink-0">
          <input 
            type="text"
            inputMode="numeric"
            dir="ltr"
            className="form-control form-control-sm border-secondary-subtle text-center fw-bold" 
            name="qty" 
            placeholder="الكمية" 
            value={formData.qty} 
            onChange={handleInputChange} 
            disabled={submitting} 
          />
        </div>
        {/* Price */}
        <div style={{ width: '100px' }} className="flex-shrink-0">
          <input 
            type="text"
            inputMode="numeric"
            dir="ltr"
            className="form-control form-control-sm border-secondary-subtle text-center fw-bold" 
            name="price" 
            placeholder="سعر الشراء" 
            value={formData.price} 
            onChange={handleInputChange} 
            disabled={submitting} 
          />
        </div>
        {/* Commission */}
        <div style={{ width: '90px' }} className="flex-shrink-0">
          <input 
            type="text"
            inputMode="numeric"
            dir="ltr"
            className="form-control form-control-sm border-secondary-subtle text-center fw-bold" 
            name="commission" 
            placeholder="المندبة" 
            value={formData.commission} 
            onChange={handleInputChange} 
            disabled={submitting} 
          />
        </div>
        {/* Month */}
        <div style={{ width: '70px' }} className="flex-shrink-0">
          <input 
            type="text"
            inputMode="numeric"
            dir="ltr"
            className="form-control form-control-sm border-secondary-subtle text-center fw-bold" 
            name="startMonth" 
            placeholder="شهر" 
            value={formData.startMonth} 
            onChange={handleInputChange} 
            disabled={submitting} 
          />
        </div>
        {/* Year */}
        <div style={{ width: '80px' }} className="flex-shrink-0">
          <input 
            type="text"
            inputMode="numeric"
            dir="ltr"
            className="form-control form-control-sm border-secondary-subtle text-center fw-bold" 
            name="startYear" 
            placeholder="سنة" 
            value={formData.startYear} 
            onChange={handleInputChange} 
            disabled={submitting} 
          />
        </div>
        {/* Submit / Cancel */}
        <div className="d-flex align-items-center gap-1 flex-shrink-0">
          <button type="submit" className={`btn btn-sm fw-bold px-3 py-1 d-flex align-items-center gap-1 border-secondary-subtle ${editingId ? 'btn-success' : 'btn-primary'}`} disabled={submitting}>
            {submitting ? <IconLoader className="icon-spin" size={14} /> : (editingId ? <IconEdit size={14} /> : <IconPlus size={14} />)}
            <span>{editingId ? 'حفظ' : 'إضافة'}</span>
          </button>
          {editingId && (
            <button type="button" className="btn btn-sm btn-outline-secondary fw-bold px-2 py-1 border-secondary-subtle" onClick={resetForm}>
              إلغاء
            </button>
          )}
        </div>
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
                placeholder="بحث حي عن الصنف..." 
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
              {filteredItems.length} صنف
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
                  <td colSpan="7" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center text-muted py-4">لا توجد أصناف مطابقة</td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.id} className={editingId === item.id ? 'bg-primary-lt' : ''}>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold">{item.id}</td>
                    <td className="text-start px-2 align-middle border-secondary-subtle fw-bold">{item.name}</td>
                    <td className="text-center align-middle border-secondary-subtle">
                      {fmt(item.initial_quantity || 0)}
                    </td>
                    <td className="text-center align-middle border-secondary-subtle">{fmt(item.initial_purchase_price || 0)}</td>
                    <td className="text-center align-middle border-secondary-subtle" dir="ltr">{formatMMYYYY(item.initial_month, item.initial_year)}</td>
                    <td className="text-center align-middle border-secondary-subtle">{fmt(item.initial_commission_amount || 0)}</td>
                    <td className="text-nowrap text-center align-middle border-secondary-subtle">
                      <Link to={`/product-ledger/${item.id}`} className="btn btn-sm btn-ghost-info me-1" title="كارت الصنف وسجل العمليات">
                        <IconFileText size={18} /> كارت الصنف
                      </Link>
                      <button type="button" className="btn btn-sm btn-ghost-primary me-1" title="تعديل الصنف" onClick={() => startEdit(item)} disabled={submitting || deleting}>
                        <IconEdit size={18} />
                      </button>
                      <button type="button" className="btn btn-sm btn-ghost-danger" title="حذف الصنف" onClick={() => confirmDelete(item)} disabled={deleting}>
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
              <button type="button" className="btn-close" onClick={() => setDeleteModalOpen(false)} style={{position: 'absolute', top: 15, left: 15}}></button>
              <div className="modal-body text-center py-4">
                <IconTrash className="text-danger mb-2" size={48} stroke={1.5} />
                <h3>تأكيد الحذف</h3>
                <div className="text-muted">هل تريد حذف الصنف "{itemToDelete?.name}"؟ <br/><strong className="text-danger">⚠️ سيتم حذف كل البيانات المرتبطة بهذا الصنف.</strong></div>
              </div>
              <div className="modal-footer">
                <div className="w-100">
                  <div className="row">
                    <div className="col"><button type="button" className="btn w-100" onClick={() => setDeleteModalOpen(false)} disabled={deleting}>إلغاء</button></div>
                    <div className="col"><button type="button" className="btn btn-danger w-100" onClick={handleDelete} disabled={deleting}>{deleting ? 'جاري الحذف...' : 'نعم، احذف'}</button></div>
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
