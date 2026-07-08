import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../api';
import { IconArrowRight, IconPrinter } from '@tabler/icons-react';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function ProfitAndLossReport() {
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [reportMonth, setReportMonth] = useState('');
  const [reportYear, setReportYear] = useState('');
  
  const [showTotalsOnly, setShowTotalsOnly] = useState(false);

  useEffect(() => {
    if (!defaultLoading && reportMonth === '' && reportYear === '') {
      setReportMonth(defaultMonth);
      setReportYear(defaultYear);
    }
  }, [defaultLoading, defaultMonth, defaultYear]);

  useEffect(() => {
    if (reportMonth && reportYear) {
      fetchReport();
    }
  }, [reportMonth, reportYear]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const branchId = localStorage.getItem('branchId');
      const res = await api.get(`/reports/profit-and-loss/?branch_id=${branchId}&month=${reportMonth}&year=${reportYear}`);
      setData(res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('حدث خطأ أثناء جلب تقرير الأرباح والخسائر.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">تقرير الأرباح والخسائر</h2>
              <div className="text-muted mt-1">تفصيل الإيرادات، التكاليف، وصافي الربح للمبيعات</div>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <button className="btn btn-primary me-2" onClick={handlePrint}>
                <IconPrinter className="me-2" /> طباعة
              </button>
              <Link to="/reports" className="btn btn-secondary">
                <IconArrowRight className="me-2" /> رجوع
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="container-fluid">
          
          <div className="card mb-4 d-print-none">
            <div className="card-body">
              <div className="row align-items-end">
                <div className="col-md-3 mb-3 mb-md-0">
                  <label className="form-label">الشهر</label>
                  <input type="number" className="form-control" value={reportMonth} onChange={(e) => setReportMonth(e.target.value)} min="1" max="12" />
                </div>
                <div className="col-md-3 mb-3 mb-md-0">
                  <label className="form-label">السنة</label>
                  <input type="number" className="form-control" value={reportYear} onChange={(e) => setReportYear(e.target.value)} min="2020" max="2050" />
                </div>
                <div className="col-md-3 mb-3 mb-md-0">
                  <label className="form-check form-switch mt-4">
                    <input className="form-check-input" type="checkbox" checked={showTotalsOnly} onChange={(e) => setShowTotalsOnly(e.target.checked)} />
                    <span className="form-check-label fw-bold">عرض الإجماليات فقط</span>
                  </label>
                </div>
                <div className="col-md-3">
                  <button className="btn btn-primary w-100" onClick={fetchReport}>تحديث</button>
                </div>
              </div>
            </div>
          </div>

          {error && <div className="alert alert-danger">{error}</div>}

          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status"></div>
            </div>
          ) : data ? (
            <>
              {/* Summary Profitability Card */}
              <div className="card mb-4 bg-primary-lt">
                <div className="card-header font-weight-bold">
                  <h3 className="card-title text-primary">ملخص الأرباح والخسائر العام للفترة</h3>
                </div>
                <div className="card-body">
                  <div className="row text-center">
                    <div className="col-md-2 col-6 mb-3">
                      <div className="text-muted font-weight-medium">إجمالي الإيرادات</div>
                      <div className="text-xl font-bold text-azure">{fmt(data.summary.grand_revenue)}</div>
                    </div>
                    <div className="col-md-2 col-6 mb-3">
                      <div className="text-muted font-weight-medium">إجمالي التكلفة</div>
                      <div className="text-xl font-bold text-red">{fmt(data.summary.grand_cost)}</div>
                    </div>
                    <div className="col-md-3 col-6 mb-3">
                      <div className="text-muted font-weight-medium">إجمالي عمولات المناديب</div>
                      <div className="text-xl font-bold text-orange">{fmt(data.summary.grand_commission)}</div>
                    </div>
                    <div className="col-md-2 col-6 mb-3">
                      <div className="text-muted font-weight-medium">مصروفات تشغيلية</div>
                      <div className="text-xl font-bold text-secondary">{fmt(data.summary.expenses_total)}</div>
                    </div>
                    <div className="col-md-3 col-12 mb-3 border-right">
                      <div className="text-muted font-weight-bold">صافي الربح النهائي</div>
                      <div className="text-2xl font-black text-green">{fmt(data.summary.net_profit_final)}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Cash Sales Profitability Table */}
              <div className="card mb-4">
                <div className="card-header bg-green-lt">
                  <h3 className="card-title text-green">أرباح مبيعات الكاش</h3>
                </div>
                <div className="table-responsive report-table-container">
                  <table className="table table-vcenter card-table table-bordered text-center align-middle mb-0">
                    <thead className="table-light">
                      {showTotalsOnly ? (
                        <tr>
                          <th>الصنف</th>
                          <th>الكمية</th>
                          <th>اجمالي المبيعات</th>
                          <th>اجمالي التكلفة</th>
                          <th>اجمالي عمولة البيع</th>
                          <th>الربح النهائي</th>
                        </tr>
                      ) : (
                        <tr>
                          <th>الصنف</th>
                          <th>الكمية</th>
                          <th>سعر البيع</th>
                          <th>التكلفة</th>
                          <th>العمولة</th>
                          <th>الربح</th>
                        </tr>
                      )}
                    </thead>
                    <tbody>
                      {data.cash_sales_profitability && data.cash_sales_profitability.length > 0 ? (
                        data.cash_sales_profitability.map((item, index) => {
                          if (showTotalsOnly) {
                            return (
                              <tr key={index}>
                                <td className="fw-bold">{item.name}</td>
                                <td>{fmt(item.qty)}</td>
                                <td className="fw-bold text-azure">{fmt(item.total_rev)}</td>
                                <td className="text-danger">{fmt(item.total_cost)}</td>
                                <td className="text-warning">{fmt(item.total_sales_comm)}</td>
                                <td className="text-success font-weight-bold">{fmt(item.total_profit)}</td>
                              </tr>
                            );
                          }
                          return (
                            <React.Fragment key={index}>
                              <tr className="bg-light">
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0">{item.name}</td>
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0">{fmt(item.qty)}</td>
                                <td className="text-muted"><small>متوسط الوحدة</small> <br/> {fmt(item.avg_sell)}</td>
                                <td className="text-muted"><small>تكلفة الوحدة</small> <br/> {fmt(item.cost_per_unit)}</td>
                                <td className="text-muted"><small>عمولة الوحدة</small> <br/> {fmt(item.sales_comm_per_unit)}</td>
                                <td className="text-muted"><small>متوسط ربح القطعة</small> <br/> {fmt(item.avg_profit)}</td>
                              </tr>
                              <tr>
                                <td className="fw-bold text-azure"><small className="text-muted d-block">إجمالي مبيعات</small>{fmt(item.total_rev)}</td>
                                <td className="fw-bold text-danger"><small className="text-muted d-block">إجمالي تكلفة</small>{fmt(item.total_cost)}</td>
                                <td className="fw-bold text-warning"><small className="text-muted d-block">إجمالي عمولة</small>{fmt(item.total_sales_comm)}</td>
                                <td className="fw-bold text-success fs-3"><small className="text-muted d-block">إجمالي الربح</small>{fmt(item.total_profit)}</td>
                              </tr>
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={showTotalsOnly ? 6 : 6} className="text-center text-muted py-3">لا توجد مبيعات كاش</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Installment Sales Profitability Table */}
              <div className="card">
                <div className="card-header bg-azure-lt">
                  <h3 className="card-title text-azure">أرباح مبيعات القسط</h3>
                </div>
                <div className="table-responsive report-table-container">
                  <table className="table table-vcenter card-table table-bordered text-center align-middle mb-0">
                    <thead className="table-light">
                      {showTotalsOnly ? (
                        <tr>
                          <th>الصنف</th>
                          <th>الكمية</th>
                          <th>اجمالي المبيعات</th>
                          <th>اجمالي التكلفة</th>
                          <th>عمولة بيع وتحصيل</th>
                          <th>الربح النهائي</th>
                        </tr>
                      ) : (
                        <tr>
                          <th>الصنف</th>
                          <th>الكمية</th>
                          <th>سعر البيع</th>
                          <th>التكلفة</th>
                          <th>العمولة</th>
                          <th>الربح</th>
                        </tr>
                      )}
                    </thead>
                    <tbody>
                      {data.installment_sales_profitability && data.installment_sales_profitability.length > 0 ? (
                        data.installment_sales_profitability.map((item, index) => {
                          if (showTotalsOnly) {
                            return (
                              <tr key={index}>
                                <td className="fw-bold">{item.name}</td>
                                <td>{fmt(item.qty)}</td>
                                <td className="fw-bold text-azure">{fmt(item.total_rev)}</td>
                                <td className="text-danger">{fmt(item.total_cost)}</td>
                                <td className="text-warning">{fmt((item.total_sales_comm || 0) + (item.total_coll_comm || 0))}</td>
                                <td className="text-success font-weight-bold">{fmt(item.total_profit)}</td>
                              </tr>
                            );
                          }
                          return (
                            <React.Fragment key={index}>
                              <tr className="bg-light">
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0">{item.name}</td>
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0">{fmt(item.qty)}</td>
                                <td className="text-muted"><small>متوسط الوحدة</small> <br/> {fmt(item.avg_sell)}</td>
                                <td className="text-muted"><small>تكلفة الوحدة</small> <br/> {fmt(item.cost_per_unit)}</td>
                                <td className="text-muted"><small>عمولة الوحدة</small> <br/> {fmt(item.sales_comm_per_unit)}</td>
                                <td className="text-muted"><small>متوسط ربح القطعة</small> <br/> {fmt(item.avg_profit)}</td>
                              </tr>
                              <tr>
                                <td className="fw-bold text-azure"><small className="text-muted d-block">إجمالي مبيعات</small>{fmt(item.total_rev)}</td>
                                <td className="fw-bold text-danger"><small className="text-muted d-block">إجمالي تكلفة</small>{fmt(item.total_cost)}</td>
                                <td className="fw-bold text-warning"><small className="text-muted d-block">إجمالي عمولة (بيع+تحصيل)</small>{fmt((item.total_sales_comm || 0) + (item.total_coll_comm || 0))}</td>
                                <td className="fw-bold text-success fs-3"><small className="text-muted d-block">إجمالي الربح</small>{fmt(item.total_profit)}</td>
                              </tr>
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={showTotalsOnly ? 6 : 6} className="text-center text-muted py-3">لا توجد مبيعات قسط</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
