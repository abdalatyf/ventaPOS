import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../api';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function SalespersonPerformanceReport() {
  const [searchParams] = useSearchParams();
  const branchId = localStorage.getItem('selectedBranch');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  
  const currentYear = defaultYear;
  const currentMonth = defaultMonth;

  const [year, setYear] = useState(searchParams.get('year') || currentYear);
  const [month, setMonth] = useState(searchParams.get('month') || currentMonth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    totals: {
      grand_total_cash: '0.00',
      grand_total_credit: '0.00',
      grand_total_sales: '0.00',
      grand_total_collected: '0.00',
      grand_total_comm_sales: '0.00',
      grand_total_comm_coll: '0.00',
      grand_total_due: '0.00'
    },
    salespersons: []
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
      const response = await api.get('/reports/salesperson-performance/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month
        }
      });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError('فشل في جلب تقرير أداء المناديب.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [year, month]);

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">تقرير أداء وعمولات المناديب</h2>
              <div className="text-muted mt-1">متابعة مبيعات المناديب، التحصيلات، والعمولات المستحقة</div>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-fluid">
          {/* Filters Card */}
          <div className="card mb-3">
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
              {/* Summary KPIs */}
              <div className="row row-cards mb-3">
                <div className="col-sm-6 col-lg-3">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium">إجمالي المبيعات (نقدية + آجلة)</div>
                      <div className="text-muted text-xl font-bold">
                        {fmt(data.totals.grand_total_sales)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-3">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium">إجمالي التحصيلات</div>
                      <div className="text-muted text-xl font-bold">
                        {fmt(data.totals.grand_total_collected)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-3">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium">إجمالي عمولات المناديب</div>
                      <div className="text-muted text-xl font-bold">
                        {fmt(data.totals.grand_total_due)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-sm-6 col-lg-3">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium">المبيعات النقدية للمناديب</div>
                      <div className="text-muted text-xl font-bold">
                        {fmt(data.totals.grand_total_cash)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Salespeople Table */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">جدول أداء المناديب</h3>
                </div>
                <div className="table-responsive">
                  <table className="table table-vcenter table-mobile-md card-table">
                    <thead>
                      <tr>
                        <th>المندوب</th>
                        <th>عدد الفواتير</th>
                        <th>المبيعات النقدية</th>
                        <th>المبيعات الآجلة</th>
                        <th>إجمالي المبيعات</th>
                        <th>التحصيلات</th>
                        <th>عمولة المبيعات</th>
                        <th>عمولة التحصيل</th>
                        <th>صافي الراتب المستحق</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.salespersons.length > 0 ? (
                        data.salespersons.map((sp) => (
                          <tr key={sp.salesperson_id}>
                            <td data-label="المندوب">
                              <span className="font-weight-medium">{sp.name}</span>
                            </td>
                            <td data-label="عدد الفواتير">{sp.receipts_count}</td>
                            <td data-label="المبيعات النقدية">
                              {fmt(sp.cash_sales)}
                            </td>
                            <td data-label="المبيعات الآجلة">
                              {fmt(sp.credit_sales)}
                            </td>
                            <td data-label="إجمالي المبيعات">
                              <strong>
                                {fmt(sp.total_sales_val)}
                              </strong>
                            </td>
                            <td data-label="التحصيلات">
                              {fmt(sp.collected)}
                            </td>
                            <td data-label="عمولة المبيعات">
                              {fmt(sp.comm_sales)}
                            </td>
                            <td data-label="عمولة التحصيل">
                              {fmt(sp.comm_coll)}
                            </td>
                            <td data-label="صافي الراتب المستحق" className="text-green">
                              <strong>
                                {fmt(sp.due_salary)}
                              </strong>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="9" className="text-center text-muted py-4">
                            لا يوجد بيانات مناديب مسجلة لهذا الشهر.
                          </td>
                        </tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr className="bg-light font-weight-bold">
                        <td>الإجمالي العام</td>
                        <td>
                          {data.salespersons.reduce((acc, sp) => acc + sp.receipts_count, 0)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_cash)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_credit)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_sales)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_collected)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_comm_sales)}
                        </td>
                        <td>
                          {fmt(data.totals.grand_total_comm_coll)}
                        </td>
                        <td className="text-green">
                          {fmt(data.totals.grand_total_due)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

