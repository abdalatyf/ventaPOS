import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';
import { IconTrash, IconPlus, IconLoader, IconFilter, IconCalendarEvent, IconReceipt, IconSortAscending, IconSortDescending, IconSearch, IconEdit } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import Swal from 'sweetalert2';
import { useDefaultDate } from '../hooks/useDefaultDate';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};



export default function Expenses() {
  const branchId = localStorage.getItem('branchId');
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate(branchId);
  const [searchParams] = useSearchParams();
  const descInputRef = useRef(null);

  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [editingId, setEditingId] = useState(null);

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

  const filteredAndSortedExpenses = React.useMemo(() => {
    let filtered = expenses.filter(e => (e.description || '').toLowerCase().includes(searchQuery.toLowerCase()));
    filtered.sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];
      if (sortColumn === 'amount') {
          valA = Number(valA);
          valB = Number(valB);
      } else if (sortColumn === 'created_at') {
          valA = new Date(valA).getTime();
          valB = new Date(valB).getTime();
      } else if (typeof valA === 'string') {
          valA = valA.toLowerCase();
          valB = (valB || '').toLowerCase();
      }
      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return filtered;
  }, [expenses, searchQuery, sortColumn, sortDirection]);

  const [expenseMonth, setExpenseMonth] = useState(searchParams.get('month') || '');
  const [expenseYear, setExpenseYear] = useState(searchParams.get('year') || '');

  useEffect(() => {
    if (!defaultLoading && expenseMonth === '' && expenseYear === '') {
      setExpenseMonth(searchParams.get('month') || defaultMonth);
      setExpenseYear(searchParams.get('year') || defaultYear);
    }
  }, [defaultLoading, defaultMonth, defaultYear]);

  useEffect(() => {
    if (expenseMonth && expenseYear) {
      fetchExpenses();
    }
  }, [expenseMonth, expenseYear]);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/expenses/?month=${expenseMonth}&year=${expenseYear}`);
      setExpenses(res.data.results || res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('حدث خطأ أثناء جلب البيانات.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    if (!description || !amount) return;

    try {
      setSubmitting(true);
      const payload = {
        description,
        amount: String(amount).replace(/,/g, ''), // Send raw number string
        expense_month: expenseMonth,
        expense_year: expenseYear
      };

      if (editingId) {
        await api.put(`/expenses/${editingId}/`, payload);
      } else {
        await api.post('/expenses/', payload);
      }

      toast.success('تم الحفظ بنجاح');
      setDescription('');
      setAmount('');
      setEditingId(null);
      
      fetchExpenses();
      descInputRef.current?.focus();

      // Close accordion if open
      const collapseEl = document.getElementById('collapseAddExpense');
      if (collapseEl && window.bootstrap) {
        const bsCollapse = window.bootstrap.Collapse.getInstance(collapseEl);
        if (bsCollapse) bsCollapse.hide();
      }
    } catch (err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حفظ المصروف.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditClick = (exp) => {
    setEditingId(exp.id);
    setDescription(exp.description);
    setAmount(exp.amount);
    
    // Open accordion
    const collapseEl = document.getElementById('collapseAddExpense');
    if (collapseEl && window.bootstrap) {
      const bsCollapse = window.bootstrap.Collapse.getOrCreateInstance(collapseEl);
      bsCollapse.show();
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setDescription('');
    setAmount('');
    const collapseEl = document.getElementById('collapseAddExpense');
    if (collapseEl && window.bootstrap) {
      const bsCollapse = window.bootstrap.Collapse.getInstance(collapseEl);
      if (bsCollapse) bsCollapse.hide();
    }
  };

  const handleDelete = async (id) => {
    Swal.fire({
      title: 'هل أنت متأكد؟',
      text: 'هل أنت متأكد من حذف هذا المصروف؟',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء'
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await api.delete(`/expenses/${id}/`);
          setExpenses(expenses.filter(e => e.id !== id));
          toast.success('تم حذف المصروف بنجاح');
        } catch (err) {
          console.error(err);
          toast.error('حدث خطأ أثناء الحذف.');
        }
      }
    });
  };

  const totalExpenses = expenses.reduce((sum, exp) => sum + Number(exp.amount), 0);

  return (
    <div className="native-page-scroll px-3 pt-3 fs-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      
      {/* ── Page Header ── */}
      <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle" style={{ borderColor: '#dee2e6 !important' }}>
        <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
          <IconReceipt size={28} className="text-primary" />
          المصروفات اليومية والشهرية
        </h2>
      </div>

      {/* ── Filters Card ── */}
      <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-body p-3">
          <div className="d-flex align-items-center gap-3">
            <div className="input-group input-group-sm" style={{ width: '200px' }}>
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">
                <IconCalendarEvent size={16} className="me-1" />
                الشهر
              </span>
              <input 
                type="number" 
                className="form-control text-center fw-bold border-secondary-subtle" 
                value={expenseMonth} 
                onChange={(e) => setExpenseMonth(e.target.value)} 
                min="1" 
                max="12" 
              />
            </div>
            <div className="input-group input-group-sm" style={{ width: '200px' }}>
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">
                <IconCalendarEvent size={16} className="me-1" />
                السنة
              </span>
              <input 
                type="number" 
                className="form-control text-center fw-bold border-secondary-subtle" 
                value={expenseYear} 
                onChange={(e) => setExpenseYear(e.target.value)} 
                min="2020" 
                max="2050" 
              />
            </div>
            <button className="btn btn-primary btn-sm px-3 fw-bold border-secondary-subtle" onClick={fetchExpenses} disabled={loading}>
              <IconFilter size={16} className="me-1" />
              تصفية
            </button>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* ── Accordion ── */}
      <div className="accordion mb-3 shadow-sm" id="addExpenseAccordion">
        <div className="accordion-item">
          <h2 className="accordion-header" id="headingAddExpense">
            <button className="accordion-button collapsed py-2 bg-light" type="button" data-bs-toggle="collapse" data-bs-target="#collapseAddExpense" aria-expanded="false" aria-controls="collapseAddExpense">
              <span className="fw-bold text-success d-flex align-items-center">
                <IconPlus size={18} className="me-2"/> {editingId ? 'تعديل المصروف' : 'إضافة مصروف جديد'}
              </span>
            </button>
          </h2>
          <div id="collapseAddExpense" className="accordion-collapse collapse" aria-labelledby="headingAddExpense" data-bs-parent="#addExpenseAccordion">
            <div className="accordion-body p-2 bg-white">
              <form onSubmit={handleAddExpense} className="row g-2 align-items-end">
                <div className="col-md-5">
                  <label className="form-label small mb-1">البيان (اسم المصروف) <span className="text-danger">*</span></label>
                  <input ref={descInputRef} type="text" className="form-control form-control-sm" value={description} onChange={(e) => setDescription(e.target.value)} required autoFocus />
                </div>
                <div className="col-md-3">
                  <label className="form-label small mb-1">المبلغ <span className="text-danger">*</span></label>
                  <input type="number" step="1" className="form-control form-control-sm fw-bold text-danger" value={amount} onChange={(e) => setAmount(e.target.value)} required />
                </div>
                <div className="col-md-2">
                  <label className="form-label small mb-1">يُسجل في</label>
                  <input type="text" className="form-control form-control-sm bg-light text-center text-muted" value={`${expenseMonth}/${expenseYear}`} readOnly />
                </div>
                <div className="col-md-2 d-flex flex-column gap-2">
                  <button type="submit" className="btn btn-sm btn-success w-100" disabled={submitting}>
                    {submitting ? <IconLoader className="icon-spin" size={16} /> : <IconPlus size={16} />}
                    <span className="ms-1">{editingId ? 'حفظ التعديل' : 'حفظ المصروف'}</span>
                  </button>
                  {editingId && (
                    <button type="button" className="btn btn-sm btn-outline-secondary w-100" onClick={handleCancelEdit}>
                      إلغاء التعديل
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* ── Table Card ── */}
      <div className="card shadow-sm border-secondary-subtle">
        <div className="card-header bg-light d-flex justify-content-between align-items-center py-2 sticky-toolbar" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <h3 className="card-title m-0 fw-bold d-flex align-items-center gap-2 text-dark">
              قائمة المصروفات
              <span className="badge bg-secondary text-white rounded-pill px-2 py-1 fs-5">شهر {expenseMonth} / {expenseYear}</span>
            </h3>
            <div className="input-icon ms-3" style={{width: '250px'}}>
              <span className="input-icon-addon"><IconSearch size={16}/></span>
              <input type="text" className="form-control form-control-sm border-secondary-subtle" placeholder="بحث في المصروفات..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            </div>
          </div>
          <span className="badge bg-danger text-white fs-4 px-3 py-2 rounded shadow-sm border-secondary-subtle">
            الإجمالي: {fmtNum(totalExpenses)}
          </span>
        </div>
        <div className="table-responsive">
          <table className="table table-vcenter table-hover card-table table-bordered m-0 table-sticky-header" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th className="text-center w-1 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("id")}>رقم المصروف {getSortIcon("id")}</th>
                <th className="text-start px-3 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("description")}>البيان {getSortIcon("description")}</th>
                <th className="text-end px-3 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("amount")}>المبلغ {getSortIcon("amount")}</th>
                <th className="text-center border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("created_at")}>التاريخ {getSortIcon("created_at")}</th>
                <th className="text-center border-secondary-subtle bg-light" style={{width: '120px'}}>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : filteredAndSortedExpenses.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center text-muted py-5">
                    <IconReceipt size={48} className="text-muted opacity-50 mb-2" />
                    <h4 className="fw-bold">لا توجد مصروفات مسجلة في هذا الشهر</h4>
                  </td>
                </tr>
              ) : (
                filteredAndSortedExpenses.map((exp, idx) => (
                  <tr key={exp.id}>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold">{exp.id}</td>
                    <td className="text-start px-3 align-middle border-secondary-subtle fw-bold text-primary">{exp.description}</td>
                    <td className="text-end px-3 align-middle border-secondary-subtle fw-bold text-danger fs-4">{fmtNum(exp.amount)}</td>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold" dir="ltr">{new Date(exp.created_at).toLocaleDateString('en-GB')}</td>
                    <td className="text-center align-middle border-secondary-subtle">
                      <div className="btn-group">
                        <button className="btn btn-sm btn-outline-primary border-secondary-subtle fw-bold px-2 py-1" onClick={() => handleEditClick(exp)} title="تعديل">
                          <IconEdit size={16} />
                        </button>
                        <button className="btn btn-sm btn-outline-danger border-secondary-subtle fw-bold px-2 py-1" onClick={() => handleDelete(exp.id)} title="حذف">
                          <IconTrash size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
