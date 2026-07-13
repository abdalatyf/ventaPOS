import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../api';
import { IconArrowRight, IconPrinter, IconSearch, IconFilter, IconUser, IconReceipt } from '@tabler/icons-react';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function ProfitAndLossReport() {
  const { setTableRef } = useSmartScroll();
  const navigate = useNavigate();
  const { defaultMonth, defaultYear, loading: defaultLoading } = useDefaultDate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [reportMonth, setReportMonth] = useState('');
  const [reportYear, setReportYear] = useState('');
  
  // Filters
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersons, setSalespersons] = useState([]);
  const [saleTypeFilter, setSaleTypeFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showTotalsOnly, setShowTotalsOnly] = useState(false);

  // Initial Date
  useEffect(() => {
    if (!defaultLoading && reportMonth === '' && reportYear === '') {
      setReportMonth(defaultMonth);
      setReportYear(defaultYear);
    }
  }, [defaultLoading, defaultMonth, defaultYear]);

  // Fetch Salespersons
  useEffect(() => {
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/inventory/salespersons/');
        if (res.data && res.data.results) {
          setSalespersons(res.data.results);
        } else if (Array.isArray(res.data)) {
          setSalespersons(res.data);
        }
      } catch (err) {
        console.error('Failed to fetch salespersons', err);
      }
    };
    fetchSalespersons();
  }, []);

  // Fetch Report Data
  useEffect(() => {
    if (reportMonth && reportYear) {
      fetchReport();
    }
  }, [reportMonth, reportYear, salespersonId]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const branchId = localStorage.getItem('branchId');
      let url = `/reports/profit-and-loss/?branch_id=${branchId}&month=${reportMonth}&year=${reportYear}`;
      if (salespersonId) {
        url += `&salesperson_id=${salespersonId}`;
      }
      const res = await api.get(url);
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

  // Process and Filter Data
  const processedData = useMemo(() => {
    if (!data) return { items: [], totals: {} };

    // Combine cash and installment into one array
    const combined = [
      ...(data.cash_sales_profitability || []).map(item => ({ ...item, sale_type: 'cash' })),
      ...(data.installment_sales_profitability || []).map(item => ({ ...item, sale_type: 'installment' }))
    ];

    // Apply Frontend Filters
    const filtered = combined.filter(item => {
      if (saleTypeFilter !== 'all' && item.sale_type !== saleTypeFilter) return false;
      if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });

    // Recalculate Totals
    let grandRev = 0;
    let grandCost = 0;
    let grandComm = 0;

    filtered.forEach(item => {
      grandRev += item.total_rev || 0;
      grandCost += item.total_cost || 0;
      grandComm += (item.total_sales_comm || 0) + (item.total_coll_comm || 0);
    });

    // Expenses are not filtered by frontend query, but we keep the fetched value
    const expenses = data.summary?.expenses_total || 0;
    const netProfit = grandRev - grandCost - grandComm - expenses;

    return {
      items: filtered,
      totals: {
        revenue: grandRev,
        cost: grandCost,
        commission: grandComm,
        expenses: expenses,
        profit: netProfit
      }
    };
  }, [data, saleTypeFilter, searchQuery]);

  return (
    <div className="page-wrapper">
      {/* Page Header */}
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">تقرير الأرباح والخسائر</h2>
              <div className="text-muted mt-1">تفصيل المبيعات، التكاليف، وصافي المكسب</div>
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
          
          {/* Filters Row (Compact) */}
          <div className="card mb-3 d-print-none border-secondary-subtle">
            <div className="card-body py-3">
              <div className="row g-3 align-items-end">
                <div className="col-md-2">
                  <label className="form-label mb-1">الشهر</label>
                  <input
                    type="number"
                    className="form-control form-control-sm border-secondary-subtle"
                    value={reportMonth}
                    onChange={(e) => setReportMonth(e.target.value)}
                    min="1" max="12"
                  />
                </div>
                <div className="col-md-2">
                  <label className="form-label mb-1">السنة</label>
                  <input
                    type="number"
                    className="form-control form-control-sm border-secondary-subtle"
                    value={reportYear}
                    onChange={(e) => setReportYear(e.target.value)}
                  />
                </div>
                
                <div className="col-md-2">
                  <label className="form-label mb-1">المندوب</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconUser size={16} /></span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle"
                      value={salespersonId}
                      onChange={(e) => setSalespersonId(e.target.value)}
                    >
                      <option value="">كل المناديب</option>
                      {salespersons.map(s => (
                        <option key={s.id} value={s.id}>{s.name || s.username}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="col-md-2">
                  <label className="form-label mb-1">نوع البيع</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconFilter size={16} /></span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle"
                      value={saleTypeFilter}
                      onChange={(e) => setSaleTypeFilter(e.target.value)}
                    >
                      <option value="all">الكل</option>
                      <option value="cash">كاش فقط</option>
                      <option value="installment">قسط فقط</option>
                    </select>
                  </div>
                </div>

                <div className="col-md-3">
                  <label className="form-label mb-1">بحث بصنف</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconSearch size={16} /></span>
                    <input
                      type="text"
                      className="form-control form-control-sm border-secondary-subtle"
                      placeholder="ابحث باسم الصنف..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>

                <div className="col-md-1">
                  <label className="form-check form-switch mt-3 mb-0" style={{ cursor: 'pointer' }}>
                    <input
                      className="form-check-input"
                      type="checkbox"
                      checked={showTotalsOnly}
                      onChange={() => setShowTotalsOnly(!showTotalsOnly)}
                    />
                    <span className="form-check-label" style={{ fontSize: '0.85rem' }}>إجماليات</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Error & Loading */}
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status"></div>
              <div className="mt-2 text-muted">جاري تحميل التقرير...</div>
            </div>
          )}

          {/* Report Content */}
          {!loading && !error && data ? (
            <>
              {/* Compact Totals Cards */}
              <div className="row g-2 mb-3">
                <div className="col-sm-6 col-md-3">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body py-3">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-azure text-white avatar avatar-sm">
                            <IconReceipt size={18} />
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium text-muted">المبيعات</div>
                          <div className="fs-3 fw-bolder text-azure">{fmt(processedData.totals.revenue)}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="col-sm-6 col-md-3">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body py-3">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-danger text-white avatar avatar-sm">
                            <IconReceipt size={18} />
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium text-muted">التكلفة</div>
                          <div className="fs-3 fw-bolder text-danger">{fmt(processedData.totals.cost)}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="col-sm-6 col-md-3">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body py-3">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-warning text-white avatar avatar-sm">
                            <IconReceipt size={18} />
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium text-muted">مصروفات</div>
                          <Link to="/reports/expenses" className="fs-3 fw-bolder text-warning text-decoration-none">
                            {fmt(processedData.totals.expenses)}
                          </Link>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="col-sm-6 col-md-3">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body py-3">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-success text-white avatar avatar-sm">
                            <IconReceipt size={18} />
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium text-muted">المكسب</div>
                          <div className="fs-3 fw-bolder text-success">{fmt(processedData.totals.profit)}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Unified Table */}
              <div className="card border-secondary-subtle shadow-sm">
                <div ref={setTableRef} className="table-responsive hide-vertical-scroll">
                  <table className="table table-vcenter card-table table-bordered text-center align-middle mb-0">
                    <thead className="table-light sticky-top" style={{ zIndex: 2 }}>
                      {showTotalsOnly ? (
                        <tr>
                          <th>الصنف</th>
                          <th>نوع البيع</th>
                          <th>الكمية</th>
                          <th>إجمالي المبيعات</th>
                          <th>إجمالي التكلفة</th>
                          <th>إجمالي مندبة</th>
                          <th>عمولة تحصيل</th>
                          <th>المكسب النهائي</th>
                        </tr>
                      ) : (
                        <tr>
                          <th>الصنف</th>
                          <th>نوع البيع</th>
                          <th>الكمية</th>
                          <th>سعر البيع / الإجمالي</th>
                          <th>التكلفة / الإجمالي</th>
                          <th>مندبة / الإجمالي</th>
                          <th>عمولة تحصيل / الإجمالي</th>
                          <th>المكسب / الإجمالي</th>
                        </tr>
                      )}
                    </thead>
                    <tbody>
                      {processedData.items.length > 0 ? (
                        processedData.items.map((item, index) => {
                          const isCash = item.sale_type === 'cash';
                          const typeBadgeClass = isCash ? "badge bg-success-lt" : "badge bg-warning-lt";
                          const typeText = isCash ? "كاش" : "قسط";
                          
                          if (showTotalsOnly) {
                            return (
                              <tr key={`${item.id}-${item.sale_type}`}>
                                <td className="text-start px-3">
                                  <a href="#" onClick={(e) => e.preventDefault()} className="text-decoration-none fw-bold text-dark">
                                    {item.name}
                                  </a>
                                </td>
                                <td><span className={typeBadgeClass}>{typeText}</span></td>
                                <td className="fw-bold">{fmt(item.qty)}</td>
                                <td className="fw-bolder text-azure">{fmt(item.total_rev)}</td>
                                <td className="text-danger fw-bolder">{fmt(item.total_cost)}</td>
                                <td className="text-warning fw-bolder">{fmt(item.total_sales_comm)}</td>
                                <td className="text-warning fw-bolder">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.total_coll_comm || 0)}
                                </td>
                                <td className="text-success fw-bolder fs-4">{fmt(item.total_profit)}</td>
                              </tr>
                            );
                          }
                          
                          return (
                            <React.Fragment key={`${item.id}-${item.sale_type}`}>
                              <tr className="bg-light">
                                <td rowSpan={2} className="text-start px-3 bg-white border-bottom-0">
                                  <a href="#" onClick={(e) => e.preventDefault()} className="text-decoration-none fw-bold fs-4 text-dark">
                                    {item.name}
                                  </a>
                                </td>
                                <td rowSpan={2} className="bg-white border-bottom-0">
                                  <span className={typeBadgeClass}>{typeText}</span>
                                </td>
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0">{fmt(item.qty)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold">{fmt(item.avg_sell)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold">{fmt(item.cost_per_unit)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold">{fmt(item.sales_comm_per_unit)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.coll_comm_per_unit || 0)}
                                </td>
                                <td className="text-muted border-secondary-subtle fw-bold">{fmt(item.avg_profit)}</td>
                              </tr>
                              <tr>
                                <td className="fw-bolder text-azure border-secondary-subtle bg-azure-lt">{fmt(item.total_rev)}</td>
                                <td className="fw-bolder text-danger border-secondary-subtle bg-danger-lt">{fmt(item.total_cost)}</td>
                                <td className="fw-bolder text-warning border-secondary-subtle bg-warning-lt">{fmt(item.total_sales_comm)}</td>
                                <td className="fw-bolder text-warning border-secondary-subtle bg-warning-lt">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.total_coll_comm || 0)}
                                </td>
                                <td className="fw-bolder text-success fs-3 border-secondary-subtle bg-success-lt">{fmt(item.total_profit)}</td>
                              </tr>
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={showTotalsOnly ? 8 : 8} className="text-center text-muted py-4">لا توجد بيانات مطابقة للبحث</td>
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
