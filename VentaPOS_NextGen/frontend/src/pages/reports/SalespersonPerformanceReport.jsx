import React, { useState, useEffect, useContext, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { IconSearch, IconSortAscending, IconSortDescending } from '@tabler/icons-react';
import useSmartScroll from '../../hooks/useSmartScroll';
import { fmt } from '../../utils/formatUtils';

export default function SalespersonPerformanceReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const { setTableRef } = useSmartScroll();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    totals: {},
    salespersons: []
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumn, setSortColumn] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');

  const fetchReport = async () => {
    if (!year || !month || !branchId) return;

    setLoading(true);
    setError('');
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
  }, [year, month, branchId]);

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

  const processedItems = useMemo(() => {
    if (!data.salespersons) return [];
    
    // 1. Filter
    let filtered = data.salespersons.filter(item => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (item.name && item.name.toLowerCase().includes(q));
    });

    // 2. Sort
    filtered.sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];

      if (valA === undefined || valA === null) valA = '';
      if (valB === undefined || valB === null) valB = '';

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [data.salespersons, searchQuery, sortColumn, sortDirection]);

  // Dynamically calculate totals based on filtered items
  const computedTotals = useMemo(() => {
    return processedItems.reduce((acc, sp) => {
      acc.receipts_count += (sp.receipts_count || 0);
      acc.cash_sales += Number(sp.cash_sales || 0);
      acc.credit_sales += Number(sp.credit_sales || 0);
      acc.total_sales += Number(sp.total_sales_val || 0);
      acc.total_collected += Number(sp.collected || 0);
      acc.sales_commission += Number(sp.comm_sales || 0);
      acc.collection_commission += Number(sp.comm_coll || 0);
      acc.total_due += Number(sp.due_salary || 0);
      return acc;
    }, {
      receipts_count: 0, cash_sales: 0, credit_sales: 0, total_sales: 0,
      total_collected: 0, sales_commission: 0, collection_commission: 0, total_due: 0
    });
  }, [processedItems]);

  const stickyThStyle = { top: 0, backgroundColor: '#f8f9fa', zIndex: 10, boxShadow: 'inset 0 -1px 0 #dee2e6', whiteSpace: 'nowrap', cursor: 'pointer' };

  return (
    <div className="native-page-scroll d-flex flex-column" style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <div className="page-body flex-grow-1 d-flex flex-column mb-0 mt-3">
        <div className="container-fluid flex-grow-1 d-flex flex-column">
          
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h2 className="page-title m-0 fw-bold text-primary">أداء المناديب</h2>
          </div>

          {/* Filters Row */}
          <div className="card mb-3 d-print-none border-secondary-subtle">
            <div className="card-body py-2 px-3">
              <div className="row g-2 align-items-center">
                <div className="col-md-4">
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                      <IconSearch size={16} className="me-1" /> المندوب
                    </span>
                    <input
                      type="text"
                      className="form-control form-control-sm border-secondary-subtle fw-bold"
                      placeholder="ابحث باسم المندوب..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
                <div className="col-md-auto ms-auto">
                  <button className="btn btn-sm btn-primary fw-bold px-4" onClick={fetchReport}>
                    تحديث البيانات
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Removed Sticky Totals Toolbar per request */}

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {loading ? (
            <div className="card shadow-sm border-0 flex-grow-1 d-flex align-items-center justify-content-center">
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status"></div>
                <div className="text-muted mt-2 fw-bold fs-3">جاري تحميل أداء المناديب...</div>
              </div>
            </div>
          ) : (
            <>
              {/* Salespersons Table */}
              <div className="card shadow-sm border-secondary-subtle flex-grow-1 d-flex flex-column mb-3" style={{ minHeight: 0 }}>
                <div 
                  ref={setTableRef}
                  className="table-responsive hide-vertical-scroll flex-grow-1 rounded"
                  style={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto', overflowX: 'auto' }}
                >
                  <table className="table table-bordered table-vcenter table-hover text-nowrap mb-0">
                    <thead className="sticky-top align-middle">
                      <tr>
                        <th rowSpan="2" className="text-center px-2 bg-light" style={{...stickyThStyle, zIndex: 11}} onClick={() => handleSort('local_id')}>
                          رقم المندوب {getSortIcon('local_id')}
                        </th>
                        <th rowSpan="2" className="text-start px-2 bg-light" style={{...stickyThStyle, zIndex: 11}} onClick={() => handleSort('name')}>
                          المندوب {getSortIcon('name')}
                        </th>
                        <th rowSpan="2" className="text-center bg-light" style={{...stickyThStyle, zIndex: 11}} onClick={() => handleSort('receipts_count')}>
                          عدد الوصلات {getSortIcon('receipts_count')}
                        </th>
                        <th colSpan="3" className="text-center" style={{...stickyThStyle, zIndex: 11}}>
                          أداء المبيعات
                        </th>
                        <th rowSpan="2" className="text-center text-primary border-start border-end" style={{...stickyThStyle, zIndex: 11}} onClick={() => handleSort('collected')}>
                          تحصيل {month}/{year} {getSortIcon('collected')}
                        </th>
                        <th colSpan="3" className="text-center table-primary" style={{...stickyThStyle, zIndex: 11}}>
                          تفاصيل المرتب
                        </th>
                      </tr>
                      <tr>
                        <th className="text-center small text-muted" style={{...stickyThStyle, top: '40px', zIndex: 10}} onClick={() => handleSort('cash_sales')}>
                          كاش {getSortIcon('cash_sales')}
                        </th>
                        <th className="text-center small text-muted" style={{...stickyThStyle, top: '40px', zIndex: 10}} onClick={() => handleSort('credit_sales')}>
                          قسط {getSortIcon('credit_sales')}
                        </th>
                        <th className="text-center small fw-bold text-dark bg-light" style={{...stickyThStyle, top: '40px', zIndex: 10}} onClick={() => handleSort('total_sales_val')}>
                          إجمالي المبيعات {getSortIcon('total_sales_val')}
                        </th>
                        <th className="text-center small text-primary table-primary" style={{...stickyThStyle, top: '40px', zIndex: 10}} onClick={() => handleSort('comm_sales')}>
                          المندبة {getSortIcon('comm_sales')}
                        </th>
                        <th className="text-center small text-primary table-primary" style={{...stickyThStyle, top: '40px', zIndex: 10}} onClick={() => handleSort('comm_coll')}>
                          عمولة تحصيل {getSortIcon('comm_coll')}
                        </th>
                        <th className="text-center small fw-bold text-white bg-dark" style={{...stickyThStyle, top: '40px', zIndex: 10, borderColor: '#212529'}} onClick={() => handleSort('due_salary')}>
                          المرتب {getSortIcon('due_salary')}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {processedItems.length > 0 ? (
                        processedItems.map((sp, index) => (
                          <tr key={sp.salesperson_id}>
                            <td className="text-center fw-bold text-muted">
                              {sp.local_id || (index + 1)}
                            </td>
                            <td className="text-start px-2 fw-bold text-dark">
                              {sp.name}
                            </td>
                            <td className="text-center">
                              <Link to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${sp.salesperson_id}`} className="text-decoration-none badge bg-primary-lt px-2 py-1 fs-5">
                                {sp.receipts_count}
                              </Link>
                            </td>
                            <td className="text-center text-muted">
                              <Link to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${sp.salesperson_id}&is_cash_sale=true`} className="text-decoration-none text-success fw-bold">
                                {fmt(sp.cash_sales)}
                              </Link>
                            </td>
                            <td className="text-center text-muted">
                              <Link to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${sp.salesperson_id}&is_cash_sale=false`} className="text-decoration-none text-warning fw-bold">
                                {fmt(sp.credit_sales)}
                              </Link>
                            </td>
                            <td className="text-center fw-bold bg-light">
                              <Link to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${sp.salesperson_id}`} className="text-decoration-none text-primary fw-bold">
                                {fmt(sp.total_sales_val)}
                              </Link>
                            </td>
                            <td className="text-center fw-bold text-primary border-start border-end">
                              <Link to={`/reports/installments?year=${year}&month=${month}&salesperson_id=${sp.salesperson_id}`} className="text-decoration-none text-success fw-bold">
                                {fmt(sp.collected)}
                              </Link>
                            </td>
                            <td className="text-center text-primary bg-primary-subtle">
                              <Link to={`/reports/profit-and-loss?year=${year}&month=${month}`} className="text-decoration-none fw-bold" style={{ color: '#0d6efd' }}>
                                {fmt(sp.comm_sales)}
                              </Link>
                            </td>
                            <td className="text-center text-primary bg-primary-subtle fw-bold">{fmt(sp.comm_coll)}</td>
                            <td className="text-center fw-bold text-white bg-dark fs-5" style={{ borderColor: '#212529' }}>
                              {fmt(sp.due_salary)}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="10" className="text-center text-muted py-5 fw-bold">
                            لا يوجد نشاط للمناديب مطابق للبحث في هذه الفترة.
                          </td>
                        </tr>
                      )}
                    </tbody>
                    {processedItems.length > 0 && (
                      <tfoot>
                        <tr className="table-dark fw-bold fs-5">
                          <td colSpan="2" className="text-start px-2">الإجمالي الكلي</td>
                          <td className="text-center text-info">
                            <Link to={`/reports/receipts?year=${year}&month=${month}`} className="text-decoration-none text-info fw-bolder">
                              {computedTotals.receipts_count}
                            </Link>
                          </td>
                          <td className="text-center text-success">
                            <Link to={`/reports/receipts?year=${year}&month=${month}&is_cash_sale=true`} className="text-decoration-none text-success fw-bolder">
                              {fmt(computedTotals.cash_sales)}
                            </Link>
                          </td>
                          <td className="text-center text-warning">
                            <Link to={`/reports/receipts?year=${year}&month=${month}&is_cash_sale=false`} className="text-decoration-none text-warning fw-bolder">
                              {fmt(computedTotals.credit_sales)}
                            </Link>
                          </td>
                          <td className="text-center text-warning">
                            <Link to={`/reports/receipts?year=${year}&month=${month}`} className="text-decoration-none text-warning fw-bolder">
                              {fmt(computedTotals.total_sales)}
                            </Link>
                          </td>
                          <td className="text-center text-info">
                            <Link to={`/reports/installments?year=${year}&month=${month}`} className="text-decoration-none text-info fw-bolder">
                              {fmt(computedTotals.total_collected)}
                            </Link>
                          </td>
                          <td className="text-center">
                            <Link to={`/reports/profit-and-loss?year=${year}&month=${month}`} className="text-decoration-none text-white fw-bolder">
                              {fmt(computedTotals.sales_commission)}
                            </Link>
                          </td>
                          <td className="text-center">{fmt(computedTotals.collection_commission)}</td>
                          <td className="text-center bg-danger text-white border-danger fs-4">{fmt(computedTotals.total_due)}</td>
                        </tr>
                      </tfoot>
                    )}
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

