import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';
import { IconTrash, IconPlus, IconLoader, IconFilter, IconReceipt, IconSortAscending, IconSortDescending, IconSearch, IconEdit } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import Swal from 'sweetalert2';
import useSmartScroll from '../hooks/useSmartScroll';
import { useDefaultDate } from '../hooks/useDefaultDate';
import { useActiveBranch } from '../hooks/useActiveBranch';
import { parseWholeMoney, parseValidMonthYear, formatMMYYYY, toEnglish } from '../utils/formatUtils';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const CATEGORY_PRESETS = ['مصروفات عامة', 'إيجار', 'كهرباء ومياه', 'نقل ومشال', 'صيانة', 'نثريات'];

export default function Expenses() {
  const { setTableRef } = useSmartScroll();
  const { branchId } = useActiveBranch();
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate(branchId);
  const [searchParams] = useSearchParams();
  const descInputRef = useRef(null);
  const categoryInputRef = useRef(null);
  const amountInputRef = useRef(null);
  const submittingRef = useRef(false);
  const deletingRef = useRef(false);
  const fetchGenRef = useRef(0);
  const prevBranchIdRef = useRef(branchId);

  const handleEnterNext = (e, nextRef) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      nextRef?.current?.focus();
    }
  };

  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('مصروفات عامة');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [editingId, setEditingId] = useState(null);

  const availableCategories = React.useMemo(() => {
    const list = Array.isArray(expenses) ? expenses : [];
    const extra = list.map((e) => (e.category || '').trim()).filter(Boolean);
    return Array.from(new Set([...CATEGORY_PRESETS, ...extra]));
  }, [expenses]);

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
    const list = Array.isArray(expenses) ? expenses : [];
    let filtered = list.filter(e => {
      const matchSearch = (e.description || e.notes || '').toLowerCase().includes(searchQuery.toLowerCase());
      const matchCategory = !categoryFilter || (e.category || 'مصروفات عامة') === categoryFilter;
      return matchSearch && matchCategory;
    });
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
  }, [expenses, searchQuery, categoryFilter, sortColumn, sortDirection]);

  const [expenseMonth, setExpenseMonth] = useState(searchParams.get('month') || '');
  const [expenseYear, setExpenseYear] = useState(searchParams.get('year') || '');

  // Reset form state when switching branch
  useEffect(() => {
    const prevBranch = prevBranchIdRef.current;
    if (prevBranch === branchId) return;
    prevBranchIdRef.current = branchId;
    if (prevBranch === null) return;

    setEditingId(null);
    setDescription('');
    setAmount('');
    setCategory('مصروفات عامة');
    setCategoryFilter('');
    setSearchQuery('');
    setExpenses([]);
  }, [branchId]);

  useEffect(() => {
    if (!defaultLoading && expenseMonth === '' && expenseYear === '') {
      setExpenseMonth(searchParams.get('month') || defaultMonth);
      setExpenseYear(searchParams.get('year') || defaultYear);
    }
  }, [defaultLoading, defaultMonth, defaultYear]);

  const fetchExpenses = async () => {
    const validDate = parseValidMonthYear(expenseMonth, expenseYear, { minYear: 2000, maxYear: 2100 });
    if (!validDate) {
      toast.error('أدخل شهر وسنة صحيحين للتصفية.');
      return;
    }

    const reqGen = ++fetchGenRef.current;
    setLoading(true);
    try {
      const res = await api.get(`/expenses/?month=${validDate.month}&year=${validDate.year}`);
      if (reqGen !== fetchGenRef.current) return;
      const list = Array.isArray(res.data?.results) ? res.data.results : (Array.isArray(res.data) ? res.data : []);
      setExpenses(list);
      setError(null);
    } catch (err) {
      if (reqGen !== fetchGenRef.current) return;
      console.error(err);
      setError('حدث خطأ أثناء جلب البيانات.');
    } finally {
      if (reqGen === fetchGenRef.current) setLoading(false);
    }
  };

  useEffect(() => {
    if (expenseMonth && expenseYear) {
      const validDate = parseValidMonthYear(expenseMonth, expenseYear, { minYear: 2000, maxYear: 2100 });
      if (validDate) fetchExpenses();
    }
  }, [expenseMonth, expenseYear, branchId]);

  const handleAddExpense = async (e) => {
    e.preventDefault();
    if (submittingRef.current) return;
    submittingRef.current = true;

    try {
      const cleanDesc = description.trim();
      if (!cleanDesc) {
        toast.error('أدخل بيان المصروف.');
        descInputRef.current?.focus();
        return;
      }

      const validDate = parseValidMonthYear(expenseMonth, expenseYear, { minYear: 2000, maxYear: 2100 });
      if (!validDate) {
        toast.error('أدخل شهر وسنة صحيحين.');
        return;
      }

      const cleanAmount = parseWholeMoney(amount, { min: 1 });
      if (cleanAmount === null) {
        toast.error('أدخل مبلغ مصروف صحيح (1 على الأقل).');
        return;
      }

      try {
        setSubmitting(true);
        const payload = {
          description: cleanDesc,
          category: (category || '').trim() || 'مصروفات عامة',
          amount: cleanAmount,
          expense_month: validDate.month,
          expense_year: validDate.year
        };

        if (editingId) {
          await api.put(`/expenses/${editingId}/`, payload);
        } else {
          await api.post('/expenses/', payload);
        }

        toast.success('تم الحفظ بنجاح');
        setDescription('');
        setAmount('');
        setCategory('مصروفات عامة');
        setEditingId(null);

        fetchExpenses();
        descInputRef.current?.focus();
      } catch (err) {
        console.error(err);
        toast.error(err.response?.data?.detail || err.response?.data?.error || 'حدث خطأ أثناء حفظ المصروف.');
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  const handleEditClick = (exp) => {
    setEditingId(exp.id);
    setDescription(exp.description);
    setAmount(Math.round(Number(exp.amount || 0)).toString());
    setCategory(exp.category || 'مصروفات عامة');
    descInputRef.current?.focus();
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setDescription('');
    setAmount('');
    setCategory('مصروفات عامة');
  };

  const handleDelete = async (id) => {
    if (deletingRef.current) return;
    deletingRef.current = true;

    try {
      const result = await Swal.fire({
        title: 'هل أنت متأكد؟',
        text: 'هل أنت متأكد من حذف هذا المصروف؟',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، احذف',
        cancelButtonText: 'إلغاء'
      });

      if (result.isConfirmed) {
        try {
          await api.delete(`/expenses/${id}/`);
          setExpenses(prev => prev.filter(e => e.id !== id));
          if (editingId === id) handleCancelEdit();
          toast.success('تم حذف المصروف بنجاح');
        } catch (err) {
          console.error(err);
          toast.error('حدث خطأ أثناء الحذف.');
        }
      }
    } finally {
      deletingRef.current = false;
    }
  };

  const totalExpenses = expenses.reduce((sum, exp) => sum + Number(exp.amount || 0), 0);

  return (
    <StandardTablePageLayout
      title="المصروفات اليومية والشهرية"
      icon={IconReceipt}
      row1={
        <form noValidate onSubmit={handleAddExpense} className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
          {/* Description */}
          <div className="flex-grow-1" style={{ minWidth: '180px' }}>
            <input 
              ref={descInputRef} 
              type="text" 
              className="form-control form-control-sm border-secondary-subtle fw-bold" 
              placeholder="البيان (اسم المصروف) *" 
              value={description} 
              onChange={(e) => setDescription(e.target.value)} 
              onKeyDown={(e) => handleEnterNext(e, categoryInputRef)}
            />
          </div>

          {/* Category */}
          <div style={{ width: '150px' }} className="flex-shrink-0">
            <input 
              ref={categoryInputRef}
              type="text" 
              className="form-control form-control-sm border-secondary-subtle fw-bold" 
              list="expenseCategoryOptions" 
              value={category} 
              onChange={(e) => setCategory(e.target.value)} 
              onKeyDown={(e) => handleEnterNext(e, amountInputRef)}
              placeholder="التصنيف (افتراضي: عامة)"
            />
            <datalist id="expenseCategoryOptions">
              {availableCategories.map((cat) => (
                <option key={cat} value={cat} />
              ))}
            </datalist>
          </div>

          {/* Amount */}
          <div style={{ width: '120px' }} className="flex-shrink-0">
            <input 
              ref={amountInputRef}
              type="text"
              inputMode="numeric"
              dir="ltr"
              className="form-control form-control-sm fw-bold text-danger border-secondary-subtle text-center" 
              placeholder="المبلغ *" 
              value={amount} 
              onChange={(e) => setAmount(e.target.value)} 
            />
          </div>

          {/* Month/Year read-only indicator */}
          <div style={{ width: '100px' }} className="flex-shrink-0">
            <input 
              type="text" 
              dir="ltr"
              className="form-control form-control-sm bg-light text-center text-muted border-secondary-subtle px-1 fw-bold" 
              value={expenseMonth && expenseYear ? formatMMYYYY(expenseMonth, expenseYear) : ''} 
              readOnly 
              title="يُسجل في هذا الشهر"
            />
          </div>

          {/* Action Buttons */}
          <div className="d-flex align-items-center gap-1 flex-shrink-0">
            <button type="submit" className="btn btn-sm btn-success fw-bold px-3 py-1 d-flex align-items-center gap-1 border-secondary-subtle" disabled={submitting}>
              {submitting ? <IconLoader className="icon-spin" size={14} /> : <IconPlus size={14} />}
              <span>{editingId ? 'تعديل' : 'إضافة'}</span>
            </button>
            {editingId && (
              <button type="button" className="btn btn-sm btn-outline-secondary fw-bold px-2 py-1 border-secondary-subtle" onClick={handleCancelEdit}>
                إلغاء
              </button>
            )}
          </div>
        </form>
      }
      row2={
        <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
          {/* Month */}
          <div style={{ width: '115px' }} className="flex-shrink-0">
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الشهر</span>
              <input 
                type="number"
                min={1}
                max={12}
                inputMode="numeric"
                dir="ltr"
                className="form-control text-center fw-bold border-secondary-subtle px-1 hide-arrows" 
                value={expenseMonth} 
                onChange={(e) => setExpenseMonth(toEnglish(e.target.value))} 
                onBlur={() => {
                  const n = parseInt(expenseMonth, 10);
                  if (isNaN(n)) {
                    setExpenseMonth(String(defaultMonth || new Date().getMonth() + 1));
                  } else if (n < 1) {
                    setExpenseMonth('1');
                  } else if (n > 12) {
                    setExpenseMonth('12');
                  }
                }}
              />
            </div>
          </div>

          {/* Year */}
          <div style={{ width: '125px' }} className="flex-shrink-0">
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">السنة</span>
              <input 
                type="number"
                min={2020}
                max={2100}
                inputMode="numeric"
                dir="ltr"
                className="form-control text-center fw-bold border-secondary-subtle px-1 hide-arrows" 
                value={expenseYear} 
                onChange={(e) => setExpenseYear(toEnglish(e.target.value))} 
                onBlur={() => {
                  const n = parseInt(expenseYear, 10);
                  if (isNaN(n)) {
                    setExpenseYear(String(defaultYear || new Date().getFullYear()));
                  } else if (n < 2020) {
                    setExpenseYear('2020');
                  } else if (n > 2100) {
                    setExpenseYear('2100');
                  }
                }}
              />
            </div>
          </div>

          {/* Filter button */}
          <button type="button" className="btn btn-primary btn-sm px-3 fw-bold border-secondary-subtle flex-shrink-0 d-flex align-items-center gap-1" onClick={fetchExpenses} disabled={loading}>
            <IconFilter size={14} />
            <span>تصفية</span>
          </button>

          {/* Category Filter */}
          <div style={{ width: '160px' }} className="flex-shrink-0">
            <select
              className="form-select form-select-sm border-secondary-subtle fw-bold"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">كل التصنيفات</option>
              {availableCategories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Live Search */}
          <div className="flex-grow-1" style={{ minWidth: '180px' }}>
            <div className="input-icon position-relative">
              <span className="input-icon-addon"><IconSearch size={14}/></span>
              <input 
                type="text" 
                className="form-control form-control-sm border-secondary-subtle fw-bold" 
                style={{ paddingLeft: searchQuery ? '2rem' : undefined }}
                placeholder="بحث في المصروفات..." 
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
          </div>
        </div>
      }
    >
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      {/* ── Table Card ── */}
      <div className="card shadow-sm border-secondary-subtle mb-0">
        {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
        <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
          <div className="d-flex align-items-center gap-2">
            <span className="text-secondary fw-bold small">النتائج:</span>
            <span className="badge bg-primary text-white rounded-pill px-2 py-1 tabular-nums">
              {fmtNum(filteredAndSortedExpenses.length)} مصروف
            </span>
          </div>

          {/* Total badge */}
          <div className="d-flex align-items-center">
            <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2" style={{ borderColor: '#adb5bd' }}>
              <span>إجمالي المصروفات:</span>
              <span className="text-danger fw-bolder fs-4 tabular-nums">{fmtNum(totalExpenses)}</span>
            </div>
          </div>
        </div>

        {/* Row 2 of Table Card: Table Container */}
        <div ref={setTableRef} className="table-responsive report-table-container hide-vertical-scroll">
          <table className="table table-vcenter table-hover card-table table-bordered m-0 table-sticky-header text-nowrap tabular-nums" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th className="text-center w-1 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("id")}>رقم المصروف {getSortIcon("id")}</th>
                <th className="text-start px-3 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("description")}>البيان {getSortIcon("description")}</th>
                <th className="text-center border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("category")}>التصنيف {getSortIcon("category")}</th>
                <th className="text-end px-3 border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("amount")}>المبلغ {getSortIcon("amount")}</th>
                <th className="text-center border-secondary-subtle bg-light" style={{cursor:"pointer"}} onClick={() => handleSort("created_at")}>التاريخ {getSortIcon("created_at")}</th>
                <th className="text-center border-secondary-subtle bg-light" style={{width: '120px'}}>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : filteredAndSortedExpenses.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center text-muted py-5">
                    <IconReceipt size={48} className="text-muted opacity-50 mb-2" />
                    <h4 className="fw-bold">لا توجد مصروفات مسجلة في هذا الشهر</h4>
                  </td>
                </tr>
              ) : (
                filteredAndSortedExpenses.map((exp) => (
                  <tr key={exp.id}>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold">{fmtNum(exp.id)}</td>
                    <td className="text-start px-3 align-middle border-secondary-subtle fw-bold text-primary">{exp.description}</td>
                    <td className="text-center align-middle border-secondary-subtle">
                      <span className="badge bg-primary-lt text-primary fw-bold px-2 py-1">{exp.category || 'مصروفات عامة'}</span>
                    </td>
                    <td className="text-end px-3 align-middle border-secondary-subtle fw-bold text-danger fs-4">{fmtNum(exp.amount)}</td>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold" dir="ltr">{formatMMYYYY(exp.expense_month || expenseMonth, exp.expense_year || expenseYear)}</td>
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
    </StandardTablePageLayout>
  );
}
