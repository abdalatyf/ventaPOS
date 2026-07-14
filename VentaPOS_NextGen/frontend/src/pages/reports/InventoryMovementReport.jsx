import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../api';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';
import { IconCalendarEvent, IconBarcode, IconUser, IconSortAscending, IconSortDescending } from '@tabler/icons-react';

export default function InventoryMovementReport() {
  const { setTableRef } = useSmartScroll();
  const [searchParams] = useSearchParams();
  const branchId = localStorage.getItem('selectedBranch');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  
  const currentYear = defaultYear;
  const currentMonth = defaultMonth;

  const [year, setYear] = useState(searchParams.get('year') || currentYear);
  const [month, setMonth] = useState(searchParams.get('month') || currentMonth);
  const [searchQuery, setSearchQuery] = useState('');
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersons, setSalespersons] = useState([]);
  
  const [sortColumn, setSortColumn] = useState('local_id');
  const [sortDirection, setSortDirection] = useState('asc');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    total_inventory_value: '0.00',
    total_adjustments_count: 0,
    items: []
  });

  const years = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

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
      const response = await api.get('/reports/inventory-movement/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month,
          salesperson_id: salespersonId || undefined
        }
      });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError('فشل في جلب تقرير حركة المخزون.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!dateLoading) {
      fetchReport();
    }
  }, [year, month, salespersonId, dateLoading]);

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
    if (!data.items) return [];
    
    // 1. Filter
    let filtered = data.items.filter(item => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        (item.product_name && item.product_name.toLowerCase().includes(q)) ||
        (item.local_id && item.local_id.toString().includes(q))
      );
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
  }, [data.items, searchQuery, sortColumn, sortDirection]);

  // Calculations for totals
  const totals = useMemo(() => {
    return processedItems.reduce((acc, item) => {
      acc.opening_stock += (item.opening_stock || 0);
      acc.purchases += (item.purchases || 0);
      acc.returns += (item.returns || 0);
      acc.sales += (item.sales || 0);
      acc.surplus += (item.surplus || 0);
      acc.deficit += (item.deficit || 0);
      acc.final_stock += (item.final_stock || 0);
      return acc;
    }, {
      opening_stock: 0, purchases: 0, returns: 0, sales: 0,
      surplus: 0, deficit: 0, final_stock: 0
    });
  }, [processedItems]);

  const stickyThStyle = { top: 0, backgroundColor: '#f8f9fa', zIndex: 10, boxShadow: 'inset 0 -1px 0 #dee2e6', whiteSpace: 'nowrap', cursor: 'pointer' };

  return (
    <div className="native-page-scroll d-flex flex-column" style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <div className="page-body flex-grow-1 d-flex flex-column mb-0 mt-3">
        <div className="container-fluid flex-grow-1 d-flex flex-column">
          
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h2 className="page-title m-0 fw-bold text-primary">جرد المخزن</h2>
          </div>

          {/* Filters Row (Static) */}
          <div className="card mb-3 d-print-none border-secondary-subtle">
            <div className="card-body py-2 px-3">
              <div className="row g-2 align-items-center">
                
                <div className="col-md-2">
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                      <IconCalendarEvent size={16} className="me-1" /> السنة
                    </span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold text-center"
                      value={year}
                      onChange={(e) => setYear(e.target.value)}
                    >
                      {years.map((y) => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                </div>

                <div className="col-md-2">
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                      <IconCalendarEvent size={16} className="me-1" /> الشهر
                    </span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold text-center"
                      value={month}
                      onChange={(e) => setMonth(e.target.value)}
                    >
                      {months.map((m) => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                </div>

                <div className="col-md-3">
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                      <IconUser size={16} className="me-1" /> المندوب
                    </span>
                    <select
                      className="form-select form-select-sm border-secondary-subtle fw-bold"
                      value={salespersonId}
                      onChange={(e) => setSalespersonId(e.target.value)}
                    >
                      <option value="">كل المناديب</option>
                      {salespersons.map((sp) => (
                        <option key={sp.id} value={sp.id}>
                          {sp.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="col-md-3">
                  <div className="input-group input-group-sm">
                    <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                      <IconBarcode size={16} className="me-1" /> الصنف
                    </span>
                    <input
                      type="text"
                      className="form-control form-control-sm border-secondary-subtle fw-bold"
                      placeholder="رقم الصنف أو الاسم..."
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

          {/* Sticky Totals Toolbar */}
          {!loading && !error && (
            <div className="sticky-toolbar d-print-none mb-3" style={{ top: 'var(--navbar-height, 64px)', zIndex: 1020 }}>
              <div className="row g-2 flex-nowrap overflow-auto hide-vertical-scroll pb-1">
                {[
                  { label: 'الكمية قبل', value: totals.opening_stock, color: 'text-dark' },
                  { label: 'المشتريات (+)', value: totals.purchases, color: 'text-success' },
                  { label: 'المرتجعات (-)', value: totals.returns, color: 'text-danger' },
                  { label: 'المبيعات (-)', value: totals.sales, color: 'text-primary' },
                  { label: 'الزيادة (+)', value: totals.surplus, color: 'text-success' },
                  { label: 'العجز (-)', value: totals.deficit, color: 'text-danger' },
                  { label: 'الكمية بعد', value: totals.final_stock, color: 'text-info fw-bolder', bg: 'bg-info-lt border-info' },
                  { label: 'إجمالي القيمة', value: fmt(data.total_inventory_value), color: 'text-success fw-bolder', bg: 'bg-success-lt border-success' }
                ].map((stat, idx) => (
                  <div className="col" key={idx} style={{ minWidth: '130px' }}>
                    <div className={`card card-sm shadow-sm text-center h-100 ${stat.bg || 'bg-white border-secondary-subtle'}`}>
                      <div className="card-body py-2 px-1">
                        <div className="text-muted fs-6 fw-bold mb-1">{stat.label}</div>
                        <div className={`fs-4 fw-bold ${stat.color}`}>{stat.value}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {loading ? (
            <div className="card shadow-sm border-0 flex-grow-1 d-flex align-items-center justify-content-center">
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status"></div>
                <div className="text-muted mt-2 fw-bold fs-3">جاري تحميل التقرير...</div>
              </div>
            </div>
          ) : (
            <>
              {/* Inventory Table */}
              <div className="card shadow-sm border-secondary-subtle flex-grow-1 d-flex flex-column mb-3" style={{ minHeight: 0 }}>
                <div 
                  ref={setTableRef}
                  className="table-responsive hide-vertical-scroll flex-grow-1 rounded"
                  style={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto', overflowX: 'auto' }}
                >
                  <table className="table table-bordered table-vcenter table-hover text-nowrap mb-0">
                    <thead className="sticky-top">
                      <tr>
                        <th className="text-center px-2" style={stickyThStyle} onClick={() => handleSort('local_id')}>
                          رقم الصنف {getSortIcon('local_id')}
                        </th>
                        <th className="text-start px-2" style={stickyThStyle} onClick={() => handleSort('product_name')}>
                          الصنف {getSortIcon('product_name')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('opening_stock')}>
                          الكمية قبل {getSortIcon('opening_stock')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('purchases')}>
                          المشتريات {getSortIcon('purchases')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('returns')}>
                          المرتجعات {getSortIcon('returns')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('sales')}>
                          المبيعات {getSortIcon('sales')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('surplus')}>
                          الزيادة (+) {getSortIcon('surplus')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('deficit')}>
                          العجز (-) {getSortIcon('deficit')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('final_stock')}>
                          الكمية بعد {getSortIcon('final_stock')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('unit_cost')}>
                          تكلفة الوحدة {getSortIcon('unit_cost')}
                        </th>
                        <th className="text-center" style={stickyThStyle} onClick={() => handleSort('total_value')}>
                          إجمالي القيمة {getSortIcon('total_value')}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {processedItems.length > 0 ? (
                        processedItems.map((item) => (
                          <tr key={item.product_id}>
                            <td className="text-center fw-bold text-muted">{item.local_id || '-'}</td>
                            <td className="text-start px-2 fw-bold">{item.product_name}</td>
                            <td className="text-center">{item.opening_stock}</td>
                            <td className="text-center text-success">+{item.purchases}</td>
                            <td className="text-center text-danger">-{item.returns}</td>
                            <td className="text-center">-{item.sales}</td>
                            <td className="text-center text-success">+{item.surplus}</td>
                            <td className="text-center text-danger">-{item.deficit}</td>
                            <td className="text-center">
                              <span className="badge bg-info-lt text-info border border-info fw-bolder fs-5 px-3 py-1">{item.final_stock}</span>
                            </td>
                            <td className="text-center text-muted">{fmt(item.unit_cost)}</td>
                            <td className="text-center fw-bold text-success">{fmt(item.total_value)}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="11" className="text-center text-muted py-5 fw-bold">
                            لا يوجد أصناف مطابقة للبحث.
                          </td>
                        </tr>
                      )}
                    </tbody>
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
