import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { IconWallet, IconTrendingUp } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { fmtNum } from '../../utils/formatUtils';
import { useStandardTableSlots } from '../../components/common/StandardTablePageLayout';
import ReportAutocomplete from '../../components/ReportAutocomplete';

export default function DashboardReport() {
  const { year, month, branchId, registerPrintHandler } = useContext(ReportsContext);
  const navigate = useNavigate();

  const [salespersons, setSalespersons] = useState([]);
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonName, setSalespersonName] = useState('');
  const [areaFilter, setAreaFilter] = useState('');

  useEffect(() => {
    if (!branchId) return;
    api.get('/salespersons/', { params: { branch_id: branchId } })
      .then(res => setSalespersons(res.data.results || res.data || []))
      .catch(() => {});
  }, [branchId]);

  const slotPortals = useStandardTableSlots({
    row1Extra: (
      <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
        <div style={{ width: '220px' }} className="flex-shrink-0">
          <div className="input-group input-group-sm flex-nowrap">
            <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المندوب</span>
            <ReportAutocomplete
              value={salespersonName}
              onChange={(val) => {
                setSalespersonName(val);
                if (!val) setSalespersonId('');
              }}
              onSelect={(item) => {
                setSalespersonName(item.name || '');
                setSalespersonId(item.id || item.local_id || '');
              }}
              items={salespersons}
              placeholder="جميع المناديب..."
              className="form-control fw-bold border-secondary-subtle px-1"
            />
          </div>
        </div>
        <div style={{ width: '220px' }} className="flex-shrink-0">
          <div className="input-group input-group-sm flex-nowrap">
            <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المنطقة</span>
            <ReportAutocomplete
              value={areaFilter}
              onChange={(val) => setAreaFilter(val)}
              onSelect={(item) => {
                const val = typeof item === 'object' ? (item.area || item.name || '') : String(item);
                setAreaFilter(val);
              }}
              fetchSuggestions={async (query) => {
                try {
                  const res = await api.get('/customer-suggestions/', {
                    params: { field: 'area', term: query || '', branch_id: branchId }
                  });
                  const data = res.data || [];
                  return data.map(i => typeof i === 'object' ? i : { name: i, id: i });
                } catch {
                  return [];
                }
              }}
              placeholder="جميع المناطق..."
              className="form-control fw-bold border-secondary-subtle px-1"
            />
          </div>
        </div>
        {(salespersonId || areaFilter) && (
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary px-2 py-1 flex-shrink-0 border-secondary-subtle"
            onClick={() => {
              setSalespersonId('');
              setSalespersonName('');
              setAreaFilter('');
            }}
          >
            إلغاء الفلاتر
          </button>
        )}
      </div>
    ),
    row2: (
      <div className="text-muted fw-bold small d-flex align-items-center justify-content-between w-100">
        <span>الفترة المحددة: {year}/{String(month).padStart(2, '0')}</span>
        <span>ملخص الأداء المالي والتشغيلي الشامل للفرع</span>
      </div>
    )
  });

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    if (!year || !month || !branchId) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/reports/dashboard/', {
        params: {
          branch_id: branchId,
          year: year,
          month: month,
          salesperson_id: salespersonId || undefined,
          area: areaFilter || undefined,
        }
      });
      setData(response.data);
    } catch (err) {
      console.error("Error fetching dashboard report:", err);
      setError("حدث خطأ أثناء جلب بيانات التقرير. يرجى المحاولة مرة أخرى.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [year, month, branchId, salespersonId, areaFilter]);

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center p-5" style={{ minHeight: '300px' }}>
        <div className="spinner-border text-primary" role="status"></div>
        <div className="text-muted ms-3 fw-bold">جاري تحميل بيانات الملخص...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3">
        <div className="alert alert-danger" role="alert">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const dateParams = `year=${year}&month=${month}`;
  const kpis = data.kpis || {};
  const cashSummary = data.cash_drawer_summary || {};

  const totalOutgoing = (Number(cashSummary.total_purchases) || 0) + 
                        (Number(cashSummary.sales_returns_cash) || 0) +
                        (Number(cashSummary.auto_salaries) || 0) + 
                        (Number(cashSummary.operating_expenses) || 0);

  return (
    <div className="container-fluid p-0">
      {slotPortals}
      <div className="row g-3">
        
        {/* تفاصيل المكسب (P&L Breakdown) */}
        <div className="col-lg-6">
          <div className="card shadow-sm border-secondary-subtle h-100">
            <div className="card-header bg-primary text-white fw-bold py-2 d-flex align-items-center">
              <IconTrendingUp size={20} className="me-2" />
              <span>تفاصيل المكسب</span>
            </div>
            <div className="table-responsive">
              <table className="table table-vcenter table-hover card-table text-nowrap tabular-nums m-0">
                <tbody>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?${dateParams}`)} title="عرض فواتير المبيعات">
                    <td className="fw-semibold">إجمالي المبيعات</td>
                    <td className="text-end fw-bold text-primary">{fmtNum(kpis.total_revenue)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?${dateParams}`)} title="عرض الأرباح والخسائر">
                    <td className="text-danger">تكلفة البضاعة (سعر الشراء)</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(kpis.total_cogs)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?${dateParams}`)} title="عرض المندبة في الأرباح والخسائر">
                    <td className="text-danger">إجمالي المندبة</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(kpis.total_sales_commissions)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?${dateParams}`)} title="عرض عمولة التحصيل في الأرباح والخسائر">
                    <td className="text-danger">إجمالي عمولة التحصيل</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(kpis.total_collection_commissions)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/expenses?${dateParams}`)} title="عرض تقرير المصروفات">
                    <td className="text-danger">إجمالي المصروفات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(cashSummary.operating_expenses)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/inventory?${dateParams}`)} title="عرض حركة المخزون والعجز">
                    <td className="text-danger">خسائر العجز</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(kpis.total_deficit_loss || 0)}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr className="bg-primary-subtle border-top border-primary">
                    <td className="fw-bold text-primary border-0 fs-4">صافي المكسب</td>
                    <td className="text-end fw-bold fs-3 text-primary border-0">{fmtNum(kpis.estimated_net_profit)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* تفاصيل السيولة (Cash Drawer Breakdown) */}
        <div className="col-lg-6">
          <div className="card shadow-sm border-secondary-subtle h-100">
            <div className="card-header bg-success text-white fw-bold py-2 d-flex align-items-center">
              <IconWallet size={20} className="me-2" />
              <span>تفاصيل السيولة</span>
            </div>
            <div className="table-responsive">
              <table className="table table-vcenter table-hover card-table text-nowrap tabular-nums m-0">
                <tbody>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?${dateParams}&is_cash_sale=true`)} title="عرض مبيعات الكاش">
                    <td>(+) مبيعات كاش</td>
                    <td className="text-end fw-bold text-success">{fmtNum(cashSummary.cash_sales_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?${dateParams}&has_down_payment=true`)} title="عرض فواتير المقدمات">
                    <td>(+) المقدمات</td>
                    <td className="text-end fw-bold text-success">{fmtNum(cashSummary.down_payment_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/installments?${dateParams}`)} title="عرض تحصيلات الأقساط">
                    <td>(+) التحصيل</td>
                    <td className="text-end fw-bold text-success">{fmtNum(cashSummary.collection_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/purchases?${dateParams}&invoice_type=RETURN`)} title="عرض مرتجع المشتريات">
                    <td>(+) مرتجع مشتريات</td>
                    <td className="text-end fw-bold text-success">{fmtNum(cashSummary.purchase_returns_total)}</td>
                  </tr>
                  <tr className="bg-success-subtle fw-bold text-success border-top border-success">
                    <td>(=) إجمالي الوارد</td>
                    <td className="text-end fw-bolder">{fmtNum(cashSummary.total_cash_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/purchases?${dateParams}&invoice_type=PURCHASE`)} title="عرض فواتير المشتريات">
                    <td className="text-danger">(-) إجمالي المشتريات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(cashSummary.total_purchases)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?${dateParams}&receipt_type=RETURN`)} title="عرض مرتجع المبيعات">
                    <td className="text-danger">(-) مرتجع مبيعات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(cashSummary.sales_returns_cash)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/salesperson?${dateParams}`)} title="عرض مرتبات المناديب">
                    <td className="text-danger">(-) إجمالي المرتبات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(cashSummary.auto_salaries)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/expenses?${dateParams}`)} title="عرض تقرير المصروفات">
                    <td className="text-danger">(-) إجمالي المصروفات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(cashSummary.operating_expenses)}</td>
                  </tr>
                  <tr className="bg-danger-subtle fw-bold text-danger border-top border-danger">
                    <td>(=) إجمالي الصادر</td>
                    <td className="text-end fw-bolder">- {fmtNum(totalOutgoing)}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr className="bg-light border-top">
                    <td className="fw-bold text-dark border-0 fs-4">صافي السيولة</td>
                    <td className="text-end fw-bold fs-3 text-dark border-0">{fmtNum(cashSummary.net_cash_in_hand)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
