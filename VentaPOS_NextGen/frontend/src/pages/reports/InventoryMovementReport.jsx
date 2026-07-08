import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../../api';
import { fmt } from '../../utils/formatUtils';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export default function InventoryMovementReport() {
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
    total_inventory_value: '0.00',
    total_adjustments_count: 0,
    items: []
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
      const response = await api.get('/reports/inventory-movement/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month
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
    fetchReport();
  }, [year, month]);

  return (
    <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">تقرير حركة وجرد المخزن</h2>
              <div className="text-muted mt-1">متابعة أرصدة البضاعة (أول وآخر المدة)، المشتريات، المبيعات، والتسويات</div>
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
                <div className="col-md-6">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium text-secondary">إجمالي قيمة المخزون الحالية</div>
                      <div className="text-muted text-2xl font-bold text-green">
                        {fmt(data.total_inventory_value)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="card card-sm">
                    <div className="card-body">
                      <div className="font-weight-medium text-secondary">إجمالي عدد تسويات المخزون (عجز/زيادة)</div>
                      <div className="text-muted text-2xl font-bold text-orange">
                        {data.total_adjustments_count} تسويات
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Inventory Table */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">جدول حركة المخزون للأصناف</h3>
                </div>
                <div className="table-responsive">
                  <table className="table table-vcenter table-mobile-md card-table table-striped">
                    <thead>
                      <tr>
                        <th>الصنف</th>
                        <th>الكمية قبل {month}/{year}</th>
                        <th>المشتريات</th>
                        <th>المرتجعات</th>
                        <th>المبيعات</th>
                        <th>الزيادة (+)</th>
                        <th>العجز (-)</th>
                        <th>الكمية بعد {month}/{year}</th>
                        <th>تكلفة الوحدة</th>
                        <th>إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length > 0 ? (
                        data.items.map((item) => (
                          <tr key={item.product_id}>
                            <td data-label="الصنف">
                              <strong>{item.product_name}</strong>
                            </td>
                            <td data-label="رصيد أول المدة">{item.opening_stock}</td>
                            <td data-label="المشتريات" className="text-green">+{item.purchases}</td>
                            <td data-label="المرتجعات" className="text-red">-{item.returns}</td>
                            <td data-label="المبيعات">-{item.sales}</td>
                            <td data-label="الزيادة (+)" className="text-green">+{item.surplus}</td>
                            <td data-label="العجز (-)" className="text-red">-{item.deficit}</td>
                            <td data-label="رصيد آخر المدة">
                              <span className="badge bg-blue-lt font-weight-bold">{item.final_stock}</span>
                            </td>
                            <td data-label="تكلفة الوحدة">
                              {fmt(item.unit_cost)}
                            </td>
                            <td data-label="إجمالي القيمة" className="font-weight-bold">
                              {fmt(item.total_value)}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="10" className="text-center text-muted py-4">
                            لا يوجد أصناف في المخزن لهذه الفترة.
                          </td>
                        </tr>
                      )}
                    </tbody>
                    <tfoot>
                      <tr className="bg-light font-weight-bold">
                        <td>الإجمالي العام</td>
                        <td>
                          {data.items.reduce((acc, item) => acc + item.opening_stock, 0)}
                        </td>
                        <td className="text-green">
                          +{data.items.reduce((acc, item) => acc + item.purchases, 0)}
                        </td>
                        <td className="text-red">
                          -{data.items.reduce((acc, item) => acc + item.returns, 0)}
                        </td>
                        <td>
                          -{data.items.reduce((acc, item) => acc + item.sales, 0)}
                        </td>
                        <td className="text-green">
                          +{data.items.reduce((acc, item) => acc + item.surplus, 0)}
                        </td>
                        <td className="text-red">
                          -{data.items.reduce((acc, item) => acc + item.deficit, 0)}
                        </td>
                        <td>
                          {data.items.reduce((acc, item) => acc + item.final_stock, 0)}
                        </td>
                        <td>-</td>
                        <td className="text-green">
                          {fmt(data.total_inventory_value)}
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
