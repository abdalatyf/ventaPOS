import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../api';
import { IconSearch, IconFilter, IconUser, IconReceipt, IconSortAscending, IconSortDescending, IconFileAnalytics } from '@tabler/icons-react';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function ProfitAndLossReport() {
  const { setTableRef } = useSmartScroll();
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
  
  // Report Type: 'both', 'average', 'total'
  const [reportType, setReportType] = useState('both');

  // Sorting
  const [sortColumn, setSortColumn] = useState('local_id');
  const [sortDirection, setSortDirection] = useState('asc');

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
        const res = await api.get('/salespersons/');
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

  // Process and Filter Data
  const processedData = useMemo(() => {
    if (!data) return { items: [], totals: {} };

    // Combine cash and installment into one array
    let combined = [
      ...(data.cash_sales_profitability || []).map(item => ({ ...item, sale_type: 'cash' })),
      ...(data.installment_sales_profitability || []).map(item => ({ ...item, sale_type: 'installment' }))
    ];

    // Apply Frontend Filters
    let filtered = combined.filter(item => {
      if (saleTypeFilter !== 'all' && item.sale_type !== saleTypeFilter) return false;
      if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });

    // Apply Sorting
    filtered.sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    // Recalculate Totals
    let grandRev = 0;
    let grandCost = 0;
    let grandComm = 0;
    let grandSalesComm = 0;
    let grandCollComm = 0;

    filtered.forEach(item => {
      grandRev += item.total_rev || 0;
      grandCost += item.total_cost || 0;
      grandSalesComm += item.total_sales_comm || 0;
      grandCollComm += item.total_coll_comm || 0;
    });
    
    grandComm = grandSalesComm + grandCollComm;

    // Expenses are not filtered by frontend query, but we keep the fetched value
    const expenses = data.summary?.expenses_total || 0;
    const netProfit = grandRev - grandCost - grandComm - expenses;

    return {
      items: filtered,
      totals: {
        revenue: grandRev,
        cost: grandCost,
        salesCommission: grandSalesComm,
        collCommission: grandCollComm,
        expenses: expenses,
        profit: netProfit
      }
    };
  }, [data, saleTypeFilter, searchQuery, sortColumn, sortDirection]);

  return (
    <div className="page-wrapper">
      <div className="page-body mt-3">
        <div className="container-fluid">
          
          {/* Filters Row */}
          <div className="card mb-3 d-print-none border-secondary-subtle">
            <div className="card-body py-3">
              <div className="row g-3 align-items-end">
                
                <div className="col-md-3">
                  <label className="form-label mb-1">المندوب</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconUser size={16} /></span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold"
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

                <div className="col-md-3">
                  <label className="form-label mb-1">نوع التقرير</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconFileAnalytics size={16} /></span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold"
                      value={reportType}
                      onChange={(e) => setReportType(e.target.value)}
                    >
                      <option value="both">التفاصيل والإجماليات</option>
                      <option value="average">المتوسط للوحدة فقط</option>
                      <option value="total">الإجماليات فقط</option>
                    </select>
                  </div>
                </div>

                <div className="col-md-3">
                  <label className="form-label mb-1">نوع البيع</label>
                  <div className="input-icon">
                    <span className="input-icon-addon"><IconFilter size={16} /></span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold"
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
                      className="form-control form-control-sm border-secondary-subtle fw-bold"
                      placeholder="ابحث باسم الصنف..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
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
              {/* 6 Compact Totals Cards in one row */}
              <div className="row g-2 mb-3">
                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center">
                      <div className="font-weight-medium text-muted mb-1" style={{ fontSize: '0.8rem' }}>المبيعات</div>
                      <div className="fs-4 fw-bolder text-azure">{fmt(processedData.totals.revenue)}</div>
                    </div>
                  </div>
                </div>

                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center">
                      <div className="font-weight-medium text-muted mb-1" style={{ fontSize: '0.8rem' }}>سعر الشراء</div>
                      <div className="fs-4 fw-bolder text-danger">{fmt(processedData.totals.cost)}</div>
                    </div>
                  </div>
                </div>

                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center">
                      <div className="font-weight-medium text-muted mb-1" style={{ fontSize: '0.8rem' }}>إجمالي مندبة</div>
                      <div className="fs-4 fw-bolder text-warning">{fmt(processedData.totals.salesCommission)}</div>
                    </div>
                  </div>
                </div>

                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center">
                      <div className="font-weight-medium text-muted mb-1" style={{ fontSize: '0.8rem' }}>إجمالي تحصيل</div>
                      <div className="fs-4 fw-bolder text-warning">{fmt(processedData.totals.collCommission)}</div>
                    </div>
                  </div>
                </div>

                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center">
                      <div className="font-weight-medium text-muted mb-1" style={{ fontSize: '0.8rem' }}>المصروفات</div>
                      <Link to="/reports/expenses" className="fs-4 fw-bolder text-muted text-decoration-none d-block">
                        {fmt(processedData.totals.expenses)}
                      </Link>
                    </div>
                  </div>
                </div>

                <div className="col-2">
                  <div className="card card-sm border-secondary-subtle">
                    <div className="card-body p-2 text-center bg-success-lt">
                      <div className="font-weight-bold text-success mb-1" style={{ fontSize: '0.8rem' }}>المكسب النهائي</div>
                      <div className="fs-4 fw-bolder text-success">{fmt(processedData.totals.profit)}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Unified Table */}
              <div className="card border-secondary-subtle shadow-sm">
                <div ref={setTableRef} className="table-responsive hide-vertical-scroll">
                  <table className="table table-vcenter card-table table-bordered text-center align-middle mb-0">
                    <thead className="table-light sticky-top" style={{ zIndex: 2 }}>
                      <tr>
                        <th onClick={() => handleSort('local_id')} style={{ cursor: 'pointer' }}>
                          رقم الصنف {getSortIcon('local_id')}
                        </th>
                        <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                          الصنف {getSortIcon('name')}
                        </th>
                        <th onClick={() => handleSort('sale_type')} style={{ cursor: 'pointer' }}>
                          نوع البيع {getSortIcon('sale_type')}
                        </th>
                        <th onClick={() => handleSort('qty')} style={{ cursor: 'pointer' }}>
                          الكمية {getSortIcon('qty')}
                        </th>
                        <th onClick={() => handleSort('total_rev')} style={{ cursor: 'pointer' }}>
                          {reportType === 'both' ? 'سعر البيع / الإجمالي' : (reportType === 'total' ? 'إجمالي المبيعات' : 'سعر البيع')} {getSortIcon('total_rev')}
                        </th>
                        <th onClick={() => handleSort('total_cost')} style={{ cursor: 'pointer' }}>
                          {reportType === 'both' ? 'التكلفة / الإجمالي' : (reportType === 'total' ? 'إجمالي التكلفة' : 'التكلفة')} {getSortIcon('total_cost')}
                        </th>
                        <th onClick={() => handleSort('total_sales_comm')} style={{ cursor: 'pointer' }}>
                          {reportType === 'both' ? 'مندبة / الإجمالي' : (reportType === 'total' ? 'إجمالي مندبة' : 'عمولة مندبة')} {getSortIcon('total_sales_comm')}
                        </th>
                        <th onClick={() => handleSort('total_coll_comm')} style={{ cursor: 'pointer' }}>
                          {reportType === 'both' ? 'عمولة تحصيل / الإجمالي' : (reportType === 'total' ? 'إجمالي تحصيل' : 'عمولة تحصيل')} {getSortIcon('total_coll_comm')}
                        </th>
                        <th onClick={() => handleSort('total_profit')} style={{ cursor: 'pointer' }}>
                          {reportType === 'both' ? 'المكسب / الإجمالي' : (reportType === 'total' ? 'إجمالي المكسب' : 'المكسب')} {getSortIcon('total_profit')}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {processedData.items.length > 0 ? (
                        processedData.items.map((item) => {
                          const isCash = item.sale_type === 'cash';
                          const typeBadgeClass = isCash ? "badge bg-success-lt" : "badge bg-warning-lt";
                          const typeText = isCash ? "كاش" : "قسط";
                          
                          if (reportType === 'total') {
                            return (
                              <tr key={`${item.id}-${item.sale_type}`}>
                                <td className="text-muted fw-bold">{item.local_id || '-'}</td>
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
                          
                          if (reportType === 'average') {
                            return (
                              <tr key={`${item.id}-${item.sale_type}`} className="bg-white">
                                <td className="text-muted fw-bold">{item.local_id || '-'}</td>
                                <td className="text-start px-3">
                                  <a href="#" onClick={(e) => e.preventDefault()} className="text-decoration-none fw-bold fs-4 text-dark">
                                    {item.name}
                                  </a>
                                </td>
                                <td>
                                  <span className={typeBadgeClass}>{typeText}</span>
                                </td>
                                <td className="fw-bold fs-4">{fmt(item.qty)}</td>
                                <td className="text-muted fw-bold">{fmt(item.avg_sell)}</td>
                                <td className="text-muted fw-bold">{fmt(item.cost_per_unit)}</td>
                                <td className="text-muted fw-bold">{fmt(item.sales_comm_per_unit)}</td>
                                <td className="text-muted fw-bold">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.coll_comm_per_unit || 0)}
                                </td>
                                <td className="text-muted fw-bold">{fmt(item.avg_profit)}</td>
                              </tr>
                            );
                          }

                          // Both
                          return (
                            <React.Fragment key={`${item.id}-${item.sale_type}`}>
                              <tr className="bg-light">
                                <td rowSpan={2} className="text-muted fw-bold bg-white border-bottom-0 align-middle">{item.local_id || '-'}</td>
                                <td rowSpan={2} className="text-start px-3 bg-white border-bottom-0 align-middle">
                                  <a href="#" onClick={(e) => e.preventDefault()} className="text-decoration-none fw-bold fs-4 text-dark">
                                    {item.name}
                                  </a>
                                </td>
                                <td rowSpan={2} className="bg-white border-bottom-0 align-middle">
                                  <span className={typeBadgeClass}>{typeText}</span>
                                </td>
                                <td rowSpan={2} className="fw-bold fs-4 bg-white border-bottom-0 align-middle">{fmt(item.qty)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold py-2">{fmt(item.avg_sell)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold py-2">{fmt(item.cost_per_unit)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold py-2">{fmt(item.sales_comm_per_unit)}</td>
                                <td className="text-muted border-secondary-subtle fw-bold py-2">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.coll_comm_per_unit || 0)}
                                </td>
                                <td className="text-muted border-secondary-subtle fw-bold py-2">{fmt(item.avg_profit)}</td>
                              </tr>
                              <tr>
                                <td className="fw-bolder text-azure border-secondary-subtle bg-azure-lt py-2">{fmt(item.total_rev)}</td>
                                <td className="fw-bolder text-danger border-secondary-subtle bg-danger-lt py-2">{fmt(item.total_cost)}</td>
                                <td className="fw-bolder text-warning border-secondary-subtle bg-warning-lt py-2">{fmt(item.total_sales_comm)}</td>
                                <td className="fw-bolder text-warning border-secondary-subtle bg-warning-lt py-2">
                                  {isCash ? <span className="text-muted fs-5">كاش</span> : fmt(item.total_coll_comm || 0)}
                                </td>
                                <td className="fw-bolder text-success border-secondary-subtle bg-success-lt py-2">{fmt(item.total_profit)}</td>
                              </tr>
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan="9" className="text-center text-muted py-4">لا توجد بيانات مطابقة للبحث</td>
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
