import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';
import { IconTrash, IconPlus, IconLoader, IconFilter, IconCalendarEvent, IconReceipt } from '@tabler/icons-react';
import { useDefaultDate } from '../hooks/useDefaultDate';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const toArabic = (str) => {
  if (str === null || str === undefined) return '';
  return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
};

export default function Expenses() {
  const branchId = localStorage.getItem('branchId');
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate(branchId);
  const [searchParams] = useSearchParams();

  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [showModal, setShowModal] = useState(false);

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  
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
      await api.post('/expenses/', {
        description,
        amount: fmtNum(amount).replace(/,/g, ''), // Send raw number string
        expense_month: expenseMonth,
        expense_year: expenseYear
      });
      setDescription('');
      setAmount('');
      setShowModal(false);
      fetchExpenses();
    } catch (err) {
      console.error(err);
      alert('حدث خطأ أثناء إضافة المصروف.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المصروف؟')) return;
    try {
      await api.delete(`/expenses/${id}/`);
      setExpenses(expenses.filter(e => e.id !== id));
    } catch (err) {
      alert('حدث خطأ أثناء الحذف.');
    }
  };

  const totalExpenses = expenses.reduce((sum, exp) => sum + Number(exp.amount), 0);

  return (
    <div className="px-3 pt-3 fs-3 d-flex flex-column flex-grow-1" dir="rtl" style={{ fontSize: '1.02rem', minHeight: 0 }}>
      
      {/* ── Page Header ── */}
      <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle" style={{ borderColor: '#dee2e6 !important' }}>
        <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
          <IconReceipt size={28} className="text-primary" />
          المصروفات اليومية والشهرية
        </h2>
        <div className="d-flex align-items-center gap-2">
          <button 
            className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2"
            onClick={() => setShowModal(true)}
          >
            <IconPlus size={20} />
            <span>إضافة مصروف جديد</span>
          </button>
        </div>
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

      {/* ── Table Card ── */}
      <div className="card shadow-sm flex-grow-1 d-flex flex-column overflow-hidden border-secondary-subtle" style={{ minHeight: 0 }}>
        <div className="card-header bg-light d-flex justify-content-between align-items-center py-2" style={{ borderColor: '#dee2e6 !important' }}>
          <h3 className="card-title m-0 fw-bold d-flex align-items-center gap-2 text-dark">
            قائمة المصروفات
            <span className="badge bg-secondary text-white rounded-pill px-2 py-1 fs-5">شهر {toArabic(expenseMonth)} / {toArabic(expenseYear)}</span>
          </h3>
          <span className="badge bg-danger text-white fs-4 px-3 py-2 rounded shadow-sm border-secondary-subtle">
            الإجمالي: {toArabic(fmtNum(totalExpenses))}
          </span>
        </div>
        <div className="table-responsive flex-grow-1" style={{ overflowY: 'auto' }}>
          <table className="table table-vcenter table-hover card-table table-bordered m-0" style={{ borderCollapse: 'collapse' }}>
            <thead className="sticky-top bg-light" style={{ zIndex: 10 }}>
              <tr>
                <th className="text-center w-1 border-secondary-subtle bg-light">#</th>
                <th className="text-start px-3 border-secondary-subtle bg-light">البيان</th>
                <th className="text-end px-3 border-secondary-subtle bg-light">المبلغ</th>
                <th className="text-center border-secondary-subtle bg-light">التاريخ</th>
                <th className="text-center w-1 border-secondary-subtle bg-light">حذف</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="text-center py-5">
                    <div className="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center text-muted py-5">
                    <IconReceipt size={48} className="text-muted opacity-50 mb-2" />
                    <h4 className="fw-bold">لا توجد مصروفات مسجلة في هذا الشهر</h4>
                  </td>
                </tr>
              ) : (
                expenses.map((exp, idx) => (
                  <tr key={exp.id}>
                    <td className="text-center align-middle border-secondary-subtle fw-bold">{toArabic(idx + 1)}</td>
                    <td className="text-start px-3 align-middle border-secondary-subtle fw-bold text-primary">{exp.description}</td>
                    <td className="text-end px-3 align-middle border-secondary-subtle fw-bold text-danger fs-4">{toArabic(fmtNum(exp.amount))}</td>
                    <td className="text-center align-middle border-secondary-subtle text-muted fw-bold" dir="ltr">{toArabic(new Date(exp.created_at).toLocaleDateString('en-GB'))}</td>
                    <td className="text-center align-middle border-secondary-subtle">
                      <button className="btn btn-sm btn-outline-danger border-secondary-subtle fw-bold px-2 py-1" onClick={() => handleDelete(exp.id)}>
                        <IconTrash size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Add Modal ── */}
      {showModal && (
        <div className="modal modal-blur fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content shadow-lg border-0" style={{ borderRadius: '12px' }}>
              <div className="modal-header bg-light border-bottom border-secondary-subtle py-3">
                <h5 className="modal-title fw-bold text-primary d-flex align-items-center gap-2">
                  <IconPlus size={20} /> إضافة مصروف جديد
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              <div className="modal-body p-4">
                <form onSubmit={handleAddExpense}>
                  <div className="mb-3">
                    <label className="form-label fw-bold">البيان (اسم المصروف)</label>
                    <input 
                      type="text" 
                      className="form-control fw-bold border-secondary-subtle" 
                      value={description} 
                      onChange={(e) => setDescription(e.target.value)} 
                      required 
                      autoFocus
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-bold">المبلغ</label>
                    <input 
                      type="number" 
                      step="1"
                      className="form-control fw-bold text-center border-secondary-subtle text-danger fs-3" 
                      value={amount} 
                      onChange={(e) => setAmount(e.target.value)} 
                      required 
                    />
                  </div>
                  <div className="row mb-4">
                    <div className="col-6">
                      <label className="form-label fw-bold text-muted small mb-1">يُسجل في شهر</label>
                      <input type="number" className="form-control text-center border-secondary-subtle bg-light" value={expenseMonth} readOnly />
                    </div>
                    <div className="col-6">
                      <label className="form-label fw-bold text-muted small mb-1">يُسجل في سنة</label>
                      <input type="number" className="form-control text-center border-secondary-subtle bg-light" value={expenseYear} readOnly />
                    </div>
                  </div>
                  <div className="d-flex gap-2">
                    <button type="submit" className="btn btn-primary flex-grow-1 fw-bold fs-3 border-secondary-subtle shadow-sm" disabled={submitting}>
                      {submitting ? <IconLoader className="icon-spin" /> : 'حفظ وإضافة'}
                    </button>
                    <button type="button" className="btn btn-outline-secondary px-4 fw-bold border-secondary-subtle" onClick={() => setShowModal(false)}>
                      إلغاء
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
