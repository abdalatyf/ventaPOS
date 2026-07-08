import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { IconTrash, IconPlus, IconLoader, IconCheck } from '@tabler/icons-react';
import { fmt } from '../utils/formatUtils';
import { useDefaultDate } from '../hooks/useDefaultDate';

export default function Expenses() {
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate();

  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  
  const [expenseMonth, setExpenseMonth] = useState('');
  const [expenseYear, setExpenseYear] = useState('');

  useEffect(() => {
    if (!defaultLoading && expenseMonth === '' && expenseYear === '') {
      setExpenseMonth(defaultMonth);
      setExpenseYear(defaultYear);
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
        amount: fmt(amount),
        expense_month: fmt(expenseMonth),
        expense_year: fmt(expenseYear)
      });
      setDescription('');
      setAmount('');
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

  const totalExpenses = expenses.reduce((sum, exp) => sum + fmt(exp.amount), 0);

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">
                المصروفات اليومية والشهرية
              </h2>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-fluid">
          {error && <div className="alert alert-danger">{error}</div>}

          <div className="row">
            <div className="col-12 col-md-4 mb-3">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">إضافة مصروف جديد</h3>
                </div>
                <div className="card-body">
                  <form onSubmit={handleAddExpense}>
                    <div className="mb-3">
                      <label className="form-label fw-bold">البيان (اسم المصروف)</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        value={description} 
                        onChange={(e) => setDescription(e.target.value)} 
                        required 
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold">المبلغ</label>
                      <input 
                        type="number" 
                        step="1"
                        className="form-control" 
                        value={amount} 
                        onChange={(e) => setAmount(e.target.value)} 
                        required 
                      />
                    </div>
                    <div className="row mb-3">
                      <div className="col-6">
                        <label className="form-label fw-bold">الشهر</label>
                        <input type="number" className="form-control" value={expenseMonth} onChange={(e) => setExpenseMonth(e.target.value)} min="1" max="12" required />
                      </div>
                      <div className="col-6">
                        <label className="form-label fw-bold">السنة</label>
                        <input type="number" className="form-control" value={expenseYear} onChange={(e) => setExpenseYear(e.target.value)} min="2020" max="2050" required />
                      </div>
                    </div>
                    <button type="submit" className="btn btn-primary w-100 mt-2" disabled={submitting}>
                      {submitting ? <IconLoader className="icon-spin" /> : <IconPlus />} إضافة المصروف
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-12 col-md-8">
              <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h3 className="card-title">قائمة المصروفات (شهر {expenseMonth} سنة {expenseYear})</h3>
                  <span className="badge bg-danger text-white fs-4 p-2">
                    الإجمالي: {totalExpenses}
                  </span>
                </div>
                <div className="table-responsive report-table-container">
                  <table className="table table-vcenter card-table table-striped">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>البيان</th>
                        <th>المبلغ</th>
                        <th>التاريخ</th>
                        <th className="w-1">حذف</th>
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
                          <td colSpan="5" className="text-center text-muted py-4">لا يوجد مصروفات مسجلة في هذا الشهر</td>
                        </tr>
                      ) : (
                        expenses.map((exp, idx) => (
                          <tr key={exp.id}>
                            <td className="text-muted">{idx + 1}</td>
                            <td className="fw-bold">{exp.description}</td>
                            <td className="text-danger fw-bold">{fmt(exp.amount)}</td>
                            <td className="text-muted small">{new Date(exp.created_at).toLocaleDateString('ar-EG')}</td>
                            <td>
                              <button className="btn btn-sm btn-ghost-danger" onClick={() => handleDelete(exp.id)}>
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
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
