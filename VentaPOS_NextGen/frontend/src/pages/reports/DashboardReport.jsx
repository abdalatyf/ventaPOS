import React, { useState, useEffect, useContext } from 'react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { useNavigate } from 'react-router-dom';
import { IconWallet, IconTrendingUp, IconBox, IconAlertTriangle } from '@tabler/icons-react';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

export default function DashboardReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();

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
          month: month
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
  }, [year, month, branchId]);

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center h-100">
        <div className="spinner-border text-primary" role="status"></div>
        <div className="text-muted ms-3 fw-bold">جاري تحميل بيانات الملخص...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="alert alert-danger" role="alert">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-3">
      <div className="row g-4">
        
        {/* تفاصيل المكسب */}
        <div className="col-lg-6">
          <div className="card border-0 h-100 shadow-sm">
            <div className="card-header bg-primary text-white fw-bold py-2">
              <IconTrendingUp size={18} className="me-2" /> تفاصيل المكسب
            </div>
            <div className="table-responsive">
              <table className="table table-vcenter table-hover card-table m-0">
                <tbody>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?year=${year}&month=${month}`)}>
                    <td>إجمالي المبيعات</td>
                    <td className="text-end fw-bold text-primary">{fmtNum(data.kpis.total_revenue)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?year=${year}&month=${month}`)}>
                    <td className="text-danger">تكلفة البضاعة (سعر الشراء)</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.kpis.total_cogs)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?year=${year}&month=${month}`)}>
                    <td className="text-danger">إجمالي المندبة</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.kpis.total_sales_commissions)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/profit-and-loss?year=${year}&month=${month}`)}>
                    <td className="text-danger">إجمالي عمولة التحصيل</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.kpis.total_collection_commissions)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/expenses?year=${year}&month=${month}`)}>
                    <td className="text-danger">إجمالي المصروفات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.cash_drawer_summary.operating_expenses)}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr className="bg-primary-subtle border-top border-primary">
                    <td className="fw-bold text-primary border-0">صافي المكسب</td>
                    <td className="text-end fw-bold fs-3 text-primary border-0">{fmtNum(data.kpis.estimated_net_profit)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* تفاصيل السيولة */}
        <div className="col-lg-6">
          <div className="card border-0 h-100 shadow-sm">
            <div className="card-header bg-success text-white fw-bold py-2">
              <IconWallet size={18} className="me-2" /> تفاصيل السيولة
            </div>
            <div className="table-responsive">
              <table className="table table-vcenter table-hover card-table m-0">
                <tbody>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?year=${year}&month=${month}&is_cash_sale=true`)}>
                    <td>(+) مبيعات كاش</td>
                    <td className="text-end fw-bold">{fmtNum(data.cash_drawer_summary.cash_sales_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/receipts?year=${year}&month=${month}&has_down_payment=true`)}>
                    <td>(+) المقدمات</td>
                    <td className="text-end fw-bold">{fmtNum(data.cash_drawer_summary.down_payment_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/installments?year=${year}&month=${month}`)}>
                    <td>(+) التحصيل</td>
                    <td className="text-end fw-bold">{fmtNum(data.cash_drawer_summary.collection_inflow)}</td>
                  </tr>
                  <tr className="bg-success-subtle fw-bold text-success border-top border-success">
                    <td>(=) إجمالي الوارد</td>
                    <td className="text-end">{fmtNum(data.cash_drawer_summary.total_cash_inflow)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/purchases?year=${year}&month=${month}`)}>
                    <td className="text-danger">(-) إجمالي المشتريات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.cash_drawer_summary.total_purchases)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/salesperson?year=${year}&month=${month}`)}>
                    <td className="text-danger">(-) إجمالي المرتبات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.cash_drawer_summary.auto_salaries)}</td>
                  </tr>
                  <tr className="cursor-pointer" onClick={() => navigate(`/reports/expenses?year=${year}&month=${month}`)}>
                    <td className="text-danger">(-) إجمالي المصروفات</td>
                    <td className="text-end text-danger fw-bold">- {fmtNum(data.cash_drawer_summary.operating_expenses)}</td>
                  </tr>
                  <tr className="bg-danger-subtle fw-bold text-danger border-top border-danger">
                    <td>(=) إجمالي الصادر</td>
                    <td className="text-end">
                      - {fmtNum((data.cash_drawer_summary.total_purchases || 0) + (data.cash_drawer_summary.auto_salaries || 0) + (data.cash_drawer_summary.operating_expenses || 0))}
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr className="bg-light">
                    <td className="fw-bold text-dark border-0">صافي السيولة</td>
                    <td className="text-end fw-bold fs-3 text-dark border-0">{fmtNum(data.cash_drawer_summary.net_cash_in_hand)}</td>
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
