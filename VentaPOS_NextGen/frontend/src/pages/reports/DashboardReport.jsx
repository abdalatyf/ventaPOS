import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function DashboardReport() {
  const branchId = localStorage.getItem('selectedBranch');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  
  const currentYear = defaultYear;
  const currentMonth = defaultMonth;

  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(currentMonth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState({
    kpis: {
      safe_balance: '0.00',
      total_revenue: '0.00',
      total_cogs: '0.00',
      estimated_net_profit: '0.00',
      current_inventory_value: '0.00',
      low_stock_count: 0,
      avg_basket_size: '0.00'
    },
    cash_drawer_summary: {
      cash_sales_inflow: '0.00',
      down_payment_inflow: '0.00',
      collection_inflow: '0.00',
      total_cash_inflow: '0.00',
      operating_expenses: '0.00',
      auto_salaries: '0.00',
      net_cash_in_hand: '0.00'
    },
    top_products: [],
    top_areas: []
  });

  const navigate = useNavigate();

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
      const response = await api.get('/reports/dashboard/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month
        }
      });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError('فشل في جلب بيانات التقرير.');
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
              <h2 className="page-title">تقرير لوحة معلومات الأداء (التقارير)</h2>
              <div className="text-muted mt-1">متابعة المؤشرات المالية وحالة المخزون والمبيعات</div>
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
              {/* KPI Cards Grid */}
              <div className="row row-cards mb-3">
                {/* Safe Balance */}
                <div className="col-sm-6 col-lg-3">
                  <div 
                    className="card card-sm" 
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/cash-drawer?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-green text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M17 8v-3a1 1 0 0 0 -1 -1h-10a2 2 0 0 0 0 4h12a1 1 0 0 1 1 1v3m0 4v3a1 1 0 0 1 -1 1h-12a2 2 0 0 1 -2 -2v-12" /><path d="M20 12v4h-4a2 2 0 0 1 0 -4h4" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">نقدية الخزنة</div>
                          <div className="text-muted">
                            {fmt(data.kpis.safe_balance)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Total Revenue */}
                <div className="col-sm-6 col-lg-3">
                  <div 
                    className="card card-sm"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/profit-and-loss?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-blue text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M16.7 8a3 3 0 0 0 -2.7 -2h-4a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6h-4a3 3 0 0 1 -2.7 -2" /><path d="M12 3v3m0 12v3" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">المبيعات الإجمالية</div>
                          <div className="text-muted">
                            {fmt(data.kpis.total_revenue)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Total COGS */}
                <div className="col-sm-6 col-lg-3">
                  <div 
                    className="card card-sm"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/inventory?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-red text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 5m0 3a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v8a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3z" /><path d="M3 10l18 0" /><path d="M7 15l.01 0" /><path d="M11 15l2 0" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">تكلفة البضاعة</div>
                          <div className="text-muted">
                            {fmt(data.kpis.total_cogs)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Estimated Net Profit */}
                <div className="col-sm-6 col-lg-3">
                  <div 
                    className="card card-sm"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/profit-and-loss?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-purple text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 21l18 0" /><path d="M3 10l6 -6l6 6l6 -6" /><path d="M4 10l0 11" /><path d="M20 10l0 11" /><path d="M8 14l0 7" /><path d="M12 14l0 7" /><path d="M16 14l0 7" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">الأرباح المتوقعة</div>
                          <div className="text-muted">
                            {fmt(data.kpis.estimated_net_profit)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="row row-cards mb-3">
                {/* Current Inventory Value */}
                <div className="col-sm-6 col-lg-4">
                  <div 
                    className="card card-sm"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/inventory?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-yellow text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 3l8 4.5l0 9l-8 4.5l-8 -4.5l0 -9l8 -4.5" /><path d="M12 12l8 -4.5" /><path d="M12 12l0 9" /><path d="M12 12l-8 -4.5" /><path d="M16 5.25l-8 4.5" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">قيمة المخزن</div>
                          <div className="text-muted">
                            {fmt(data.kpis.current_inventory_value)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Low Stock Count */}
                <div className="col-sm-6 col-lg-4">
                  <div 
                    className="card card-sm"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/reports/inventory?year=${year}&month=${month}`)}
                  >
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-orange text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 9v2m0 4v.01" /><path d="M5 19h14a2 2 0 0 0 1.84 -2.75l-7.1 -12.25a2 2 0 0 0 -3.5 0l-7.1 12.25a2 2 0 0 0 1.75 2.75" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">الأصناف تحت الحد</div>
                          <div className="text-muted">{data.kpis.low_stock_count} أصناف</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Avg Basket Size */}
                <div className="col-sm-6 col-lg-4">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="row align-items-center">
                        <div className="col-auto">
                          <span className="bg-azure text-white avatar">
                            <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 19m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M17 19m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M17 17h-11v-14h-2" /><path d="M6 5l14 1l-1 7h-13" /></svg>
                          </span>
                        </div>
                        <div className="col">
                          <div className="font-weight-medium">متوسط السلة</div>
                          <div className="text-muted">
                            {fmt(data.kpis.avg_basket_size)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Cash Drawer Summary Section */}
              <div className="row mb-3">
                <div className="col-12">
                  <div className="card">
                    <div className="card-header bg-green-lt d-flex justify-content-between align-items-center">
                      <h3 className="card-title text-green">ملخص حركة الخزينة (هذا الشهر)</h3>
                      <button className="btn btn-sm btn-outline-success" onClick={() => navigate(`/reports/cash-drawer?year=${year}&month=${month}`)}>
                        عرض تفاصيل الخزينة
                      </button>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-md-6">
                          <h4 className="text-muted mb-3">المقبوضات (الداخل)</h4>
                          <div className="d-flex justify-content-between mb-2">
                            <span>المبيعات النقدية:</span>
                            <strong>{fmt(data.cash_drawer_summary.cash_sales_inflow)}</strong>
                          </div>
                          <div className="d-flex justify-content-between mb-2">
                            <span>مقدمات العقود الآجلة:</span>
                            <strong>{fmt(data.cash_drawer_summary.down_payment_inflow)}</strong>
                          </div>
                          <div className="d-flex justify-content-between mb-2">
                            <span>تحصيلات الأقساط:</span>
                            <strong>{fmt(data.cash_drawer_summary.collection_inflow)}</strong>
                          </div>
                          <hr />
                          <div className="d-flex justify-content-between text-green font-weight-bold">
                            <span>إجمالي النقدية الواردة:</span>
                            <span>{fmt(data.cash_drawer_summary.total_cash_inflow)}</span>
                          </div>
                        </div>
                        <div className="col-md-6 mt-4 mt-md-0 border-start">
                          <h4 className="text-muted mb-3">المدفوعات والمصروفات (الخارج)</h4>
                          <div className="d-flex justify-content-between mb-2">
                            <span>المصروفات التشغيلية:</span>
                            <strong className="text-danger">{fmt(data.cash_drawer_summary.operating_expenses)}</strong>
                          </div>
                          <div className="d-flex justify-content-between mb-2">
                            <span>الرواتب والعمولات التلقائية:</span>
                            <strong className="text-danger">{fmt(data.cash_drawer_summary.auto_salaries)}</strong>
                          </div>
                          <hr />
                          <div className="d-flex justify-content-between font-weight-bold" style={{ fontSize: '1.25rem' }}>
                            <span>صافي النقدية المتاحة:</span>
                            <span className="text-primary">{fmt(data.cash_drawer_summary.net_cash_in_hand)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tables Section */}
              <div className="row">
                {/* Top Products */}
                <div className="col-md-6 mb-3">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="card-title">المنتجات الأكثر مبيعاً</h3>
                    </div>
                    <div className="table-responsive">
                      <table className="table card-table table-vcenter text-nowrap">
                        <thead>
                          <tr>
                            <th>اسم الصنف</th>
                            <th>الكمية المباعة</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.top_products.length > 0 ? (
                            data.top_products.map((prod, index) => (
                              <tr key={index}>
                                <td>{prod.product_name}</td>
                                <td>{prod.quantity_sold} وحدة</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan="2" className="text-center text-muted py-3">
                                لا يوجد مبيعات منتجات في هذه الفترة.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Top Areas */}
                <div className="col-md-6 mb-3">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="card-title">المناطق الأكثر مبيعاً</h3>
                    </div>
                    <div className="table-responsive">
                      <table className="table card-table table-vcenter text-nowrap">
                        <thead>
                          <tr>
                            <th>المنطقة</th>
                            <th>قيمة المبيعات</th>
                            <th>عدد الفواتير</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.top_areas.length > 0 ? (
                            data.top_areas.map((area, index) => (
                              <tr key={index}>
                                <td>{area.area || 'غير محددة'}</td>
                                <td>{fmt(area.sales_value)}</td>
                                <td>{area.invoice_count} فواتير</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan="3" className="text-center text-muted py-3">
                                لا يوجد مبيعات مناطق في هذه الفترة.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

