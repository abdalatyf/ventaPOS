import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../../api';
import { useDefaultDate } from '../../hooks/useDefaultDate';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

export default function CashDrawerReport() {
  const [searchParams] = useSearchParams();
  const branchId = localStorage.getItem('branchId');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  
  const currentYear = defaultYear;
  const currentMonth = defaultMonth;

  const [year, setYear] = useState(searchParams.get('year') || currentYear);
  const [month, setMonth] = useState(searchParams.get('month') || currentMonth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('cashAndDown');

  const [data, setData] = useState({
    cash_sales: [],
    down_payments: [],
    collections: []
  });

  const years = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  const monthNames = [
    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
  ];

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    const branchId = localStorage.getItem('branchId');
    if (!branchId) {
      setError('الرجاء اختيار فرع أولاً.');
      setLoading(false);
      return;
    }
    try {
      const response = await api.get('/reports/cash-drawer/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month
        }
      });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError('فشل في جلب تقرير حركة درج الخزينة.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if(!dateLoading) {
      setYear(searchParams.get('year') || defaultYear);
      setMonth(searchParams.get('month') || defaultMonth);
    }
  }, [dateLoading, defaultYear, defaultMonth]);

  useEffect(() => {
    if(year && month) {
      fetchReport();
    }
  }, [year, month]);

  const formatDateToMonthYear = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return `${d.getMonth() + 1}/${d.getFullYear()}`;
    } catch (e) {
      return dateStr;
    }
  };

  const combinedInvoices = [
    ...(data.cash_sales || []).map(item => ({
      ...item,
      type: 'cash',
      displayDate: formatDateToMonthYear(item.sale_date)
    })),
    ...(data.down_payments || []).map(item => ({
      ...item,
      type: 'down',
      displayDate: formatDateToMonthYear(item.sale_date)
    }))
  ].sort((a, b) => new Date(a.sale_date) - new Date(b.sale_date));

  return (
    <div className="page-wrapper" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header d-print-none flex-shrink-0">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title text-primary">درج الخزينة</h2>
              <div className="text-muted mt-1">تفاصيل فواتير الكاش والمقدمات والتحصيلات</div>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <button className="btn btn-primary" onClick={() => window.print()}>
                طباعة التقرير
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body flex-grow-1 overflow-auto">
        <div className="container-fluid">
          {/* Filters Card */}
          <div className="card mb-3 d-print-none">
            <div className="card-body">
              <div className="row align-items-center">
                <div className="col-md-4">
                  <label className="form-label">السنة</label>
                  <select
                    className="form-select"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                  >
                    {years.map((y) => (
                      <option key={y} value={y}>
                        {y}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label">الشهر</label>
                  <select
                    className="form-select"
                    value={month}
                    onChange={(e) => setMonth(e.target.value)}
                  >
                    {months.map((m) => (
                      <option key={m} value={m}>
                        {monthNames[m - 1]} ({m})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4 text-md-end mt-4 mt-md-0">
                  <button className="btn btn-primary" onClick={fetchReport}>
                    تحديث البيانات
                  </button>
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status"></div>
              <div className="text-muted mt-2">جاري تحميل التقرير...</div>
            </div>
          ) : (
            <>
            <div className="card shadow-sm border-0">
              <div className="card-header bg-white border-bottom p-0">
                <ul className="nav nav-tabs nav-fill" role="tablist">
                  <li className="nav-item" role="presentation">
                    <button 
                      className={`nav-link fw-bold py-3 ${activeTab === 'cashAndDown' ? 'active bg-light text-primary' : 'text-secondary'}`}
                      onClick={() => setActiveTab('cashAndDown')}
                      type="button"
                    >
                      فواتير الكاش والمقدمات
                    </button>
                  </li>
                  <li className="nav-item" role="presentation">
                    <button 
                      className={`nav-link fw-bold py-3 ${activeTab === 'collections' ? 'active bg-light text-success' : 'text-secondary'}`}
                      onClick={() => setActiveTab('collections')}
                      type="button"
                    >
                      تحصيلات الأقساط
                    </button>
                  </li>
                </ul>
              </div>
              <div className="card-body p-0">
                {activeTab === 'cashAndDown' && (
                  <div className="table-responsive report-table-container">
                    <table className="table table-hover table-striped text-center align-middle mb-0">
                      <thead className="table-light">
                        <tr>
                          <th>رقم الفاتورة</th>
                          <th>اسم العميل</th>
                          <th>الإجمالي</th>
                          <th>المقدم</th>
                          <th>التاريخ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {combinedInvoices.length > 0 ? combinedInvoices.map((item, idx) => (
                          <tr key={idx}>
                            <td className="fw-bold">
                                <Link to={`/receipts/search?receipt_number=${item.receipt_number}`} className="drilldown-link text-primary text-decoration-none">
                                    #{item.receipt_number}
                                </Link>
                            </td>
                            <td className="fw-bold">{item.customer_name}</td>
                            <td className="fw-bold text-azure">{item.type === 'cash' ? fmtNum(item.amount) : fmtNum(item.total_amount)}</td>
                            <td className="text-success fw-bold">{item.type === 'cash' ? 'كاش' : fmtNum(item.down_payment)}</td>
                            <td className="text-muted">{item.displayDate}</td>
                          </tr>
                        )) : (
                          <tr><td colSpan="5" className="text-muted py-4 fw-bold">لا توجد حركات</td></tr>
                        )}
                      </tbody>
                      <tfoot className="table-primary fw-bold">
                        <tr>
                          <td colSpan="2">إجمالي فواتير الكاش والمقدمات</td>
                          <td colSpan="3" className="text-start fs-5">
                            {fmtNum(
                               combinedInvoices.reduce((acc, item) => acc + (item.type === 'cash' ? parseInt(item.amount || 0) : parseInt(item.down_payment || 0)), 0)
                            )}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}

                {activeTab === 'collections' && (
                  <div className="table-responsive report-table-container">
                    <table className="table table-hover table-striped text-center align-middle mb-0">
                      <thead className="table-light">
                        <tr>
                          <th>رقم الفاتورة</th>
                          <th>اسم العميل</th>
                          <th>المبلغ المحصل</th>
                          <th>التاريخ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.collections && data.collections.length > 0 ? data.collections.map((item, idx) => {
                          const d = new Date(item.payment_date);
                          const displayDate = `${d.getMonth() + 1}/${d.getFullYear()}`;
                          return (
                            <tr key={idx}>
                              <td className="fw-bold">
                                <Link to={`/receipts/search?receipt_number=${item.receipt_number}`} className="drilldown-link text-primary text-decoration-none">
                                    #{item.receipt_number}
                                </Link>
                              </td>
                              <td className="fw-bold">{item.customer_name}</td>
                              <td className="text-success fw-bold fs-3">{fmtNum(item.amount)}</td>
                              <td className="text-muted">{displayDate}</td>
                            </tr>
                          );
                        }) : (
                          <tr><td colSpan="4" className="text-muted py-4 fw-bold">لا توجد تحصيلات</td></tr>
                        )}
                      </tbody>
                      <tfoot className="table-success fw-bold">
                        <tr>
                          <td colSpan="2">إجمالي التحصيلات</td>
                          <td colSpan="2" className="text-start fs-5">
                            {fmtNum((data.collections || []).reduce((acc, item) => acc + parseInt(item.amount || 0), 0))}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>
            </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
