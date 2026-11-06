import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';
import { IconTrash, IconPlus, IconLoader, IconFilter, IconReceipt, IconSortAscending, IconSortDescending, IconSearch, IconEdit } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import Swal from 'sweetalert2';
import { useDefaultDate } from '../hooks/useDefaultDate';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const CATEGORY_PRESETS = ['مصروفات عامة', 'إيجار', 'كهرباء ومياه', 'نقل ومشال', 'صيانة', 'نثريات'];

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
  const [category, setCategory] = useState('مصروفات عامة');
  const [categoryFilter, setCategoryFilter] = useState('');
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
    let filtered = expenses.filter(e => {
      const matchSearch = (e.description || '').toLowerCase().includes(searchQuery.toLowerCase());
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
        category: category || 'مصروفات عامة',
        amount: String(amount).replace(/,/g, ''),
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
      setCategory('مصروفات عامة');
      setEditingId(null);
      
      fetchExpenses();
      descInputRef.current?.focus();
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
    <StandardTablePageLayout
      title="المصروفات اليومية والشهرية"
      icon={IconReceipt}
      row1={
        <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
          {/* Month */}
          <div style={{ width: '90px' }} className="flex-shrink-0">
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">الشهر</span>
              <input 
                type="number" 
                className="form-control text-center fw-bold border-secondary-subtle px-1" 
                value={expenseMonth} 
                onChange={(e) => setExpenseMonth(e.target.value)} 
                min="1" 
                max="12" 
              />
            </div>
          </div>

          {/* Year */}
          <div style={{ width: '90px' }} className="flex-shrink-0">
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">السنة</span>
              <input 
                type="number" 
                className="form-control text-center fw-bold border-secondary-subtle px-1" 
                value={expenseYear} 
                onChange={(e) => setExpenseYear(e.target.value)} 
                min="2020" 
                max="2050" 
              />
            </div>
          </div>

          {/* Filter button */}
          <button className="btn btn-primary btn-sm px-2 fw-bold border-secondary-subtle flex-shrink-0 d-flex align-items-center gap-1" onClick={fetchExpenses} disabled={loading}>
            <IconFilter size={14} />
            <span>تصفية</span>
          </button>

          {/* Category Filter */}
          <div style={{ width: '130px' }} className="flex-shrink-0">
            <select
              className="form-select form-select-sm border-secondary-subtle fw-bold"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">كل التصنيفات</option>
              {CATEGORY_PRESETS.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Live Search */}
          <div className="flex-grow-1" style={{ minWidth: '150px' }}>
            <div className="input-icon">
              <span className="input-icon-addon"><IconSearch size={14}/></span>
              <input 
                type="text" 
                className="form-control form-control-sm border-secondary-subtle fw-bold" 
                placeholder="بحث في المصروفات..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
              />
            </div>
          </div>

          {/* Count Badge */}
          <span className="badge bg-secondary text-white rounded-pill px-2 py-1 tabular-nums flex-shrink-0">
            {filteredAndSortedExpenses.length} مصروف
          </span>

          {/* Total badge */}
          <div className="ms-auto flex-shrink-0 d-flex align-items-center">
            <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2" style={{ borderColor: '#adb5bd' }}>
              <span>إجمالي المصروفات:</span>
              <span className="text-danger fw-bolder fs-4 tabular-nums">{fmtNum(totalExpenses)}</span>
            </div>
          </div>
        </div>
      }
      row2={
        <form onSubmit={handleAddExpense} className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
          {/* Description */}
          <div className="flex-grow-1" style={{ minWidth: '180px' }}>
            <input 
              ref={descInputRef} 
              type="text" 
              className="form-control form-control-sm border-secondary-subtle fw-bold" 
              placeholder="البيان (اسم المصروف) *" 
              value={description} 
              onChange={(e) => setDescription(e.target.value)} 
              required 
            />
          </div>

          {/* Category */}
          <div style={{ width: '150px' }} className="flex-shrink-0">
            <input 
              type="text" 
              className="form-control form-control-sm border-secondary-subtle fw-bold" 
              list="expenseCategoryOptions" 
              value={category} 
              onChange={(e) => setCategory(e.target.value)} 
              placeholder="التصنيف (افتراضي: عامة)"
            />
            <datalist id="expenseCategoryOptions">
              {CATEGORY_PRESETS.map((cat) => (
                <option key={cat} value={cat} />
              ))}
            </datalist>
          </div>

          {/* Amount */}
          <div style={{ width: '120px' }} className="flex-shrink-0">
            <input 
              type="number" 
              step="1" 
              className="form-control form-control-sm fw-bold text-danger border-secondary-subtle text-center" 
              placeholder="المبلغ *" 
              value={amount} 
              onChange={(e) => setAmount(e.target.value)} 
              required 
            />
          </div>

          {/* Month/Year read-only indicator */}
          <div style={{ width: '90px' }} className="flex-shrink-0">
            <input 
              type="text" 
              className="form-control form-control-sm bg-light text-center text-muted border-secondary-subtle px-1 fw-bold" 
              value={`${expenseMonth}/${expenseYear}`} 
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
    >
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      {/* ── Table Card ── */}
      <div className="card shadow-sm border-secondary-subtle">
        <div className="table-responsive" style={{ overflow: 'visible' }}>
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
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold">{exp.id}</td>
                    <td className="text-start px-3 align-middle border-secondary-subtle fw-bold text-primary">{exp.description}</td>
                    <td className="text-center align-middle border-secondary-subtle">
                      <span className="badge bg-blue-lt text-primary fw-bold px-2 py-1">{exp.category || 'مصروفات عامة'}</span>
                    </td>
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
    </StandardTablePageLayout>
  );
}
