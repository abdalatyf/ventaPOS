import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconPackage, IconFilter, IconRefresh, IconArrowBackUp } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum, formatMMYYYY } from '../../utils/formatUtils';

export default function PurchasesReport() {
  const { year, month, branchId } = useContext(ReportsContext);

  const [invoices, setInvoices] = useState([]);
  const [summary, setSummary] = useState({
    total_purchases_amount: 0,
    gross_purchases_amount: 0,
    total_purchases_count: 0,
    total_returns_count: 0,
    total_returns_amount: 0,
    total_items_quantity: 0,
    suppliers_count: 0,
  });

  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [invoiceType, setInvoiceType] = useState('ALL');
  const [invoiceFrom, setInvoiceFrom] = useState('');
  const [invoiceTo, setInvoiceTo] = useState('');
  const [itemQuery, setItemQuery] = useState('');

  // Fetch suppliers list once for the dropdown
  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const res = await api.get('/suppliers/');
        setSuppliers(res.data.results || res.data || []);
      } catch (err) {
        console.error('Failed to load suppliers:', err);
      }
    };
    fetchSuppliers();
  }, []);

  const fetchPurchases = async () => {
    if (!branchId) return;

    setLoading(true);
    setError(null);

    const params = {
      branch_id: branchId,
    };
    if (year) params.year = year;
    if (month) params.month = month;
    if (selectedSupplier) params.supplier_id = selectedSupplier;
    if (invoiceType !== 'ALL') params.invoice_type = invoiceType;
    if (invoiceFrom) params.invoice_from = invoiceFrom;
    if (invoiceTo) params.invoice_to = invoiceTo;

    try {
      const res = await api.get('/reports/purchases/', { params });
      setInvoices(res.data.invoices || []);
      setSummary(res.data.summary || {});
    } catch (err) {
      console.error('Error fetching purchases report:', err);
      setError(err.response?.data?.detail || 'حدث خطأ أثناء تحميل تقرير المشتريات.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
  }, [branchId, year, month, selectedSupplier, invoiceType, invoiceFrom, invoiceTo]);

  // Client-side text filter on items_summary
  const filteredInvoices = useMemo(() => {
    if (!itemQuery.trim()) return invoices;
    const q = itemQuery.trim().toLowerCase();
    return invoices.filter((inv) =>
      String(inv.items_summary || '').toLowerCase().includes(q) ||
      String(inv.supplier_name || '').toLowerCase().includes(q)
    );
  }, [invoices, itemQuery]);

  const handleResetFilters = () => {
    setSelectedSupplier('');
    setInvoiceType('ALL');
    setInvoiceFrom('');
    setInvoiceTo('');
    setItemQuery('');
  };

  return (
    <div className="d-flex flex-column gap-3">
      {/* 6 KPI Summary Cards */}
      <div className="row g-2">
        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-primary border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">صافي المشتريات</div>
              <div className="h3 mb-0 fw-bold text-primary tabular-nums mt-1">
                {fmtNum(summary.total_purchases_amount || 0)} <span className="fs-6">ج.م</span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-success border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">فواتير الشراء</div>
              <div className="h3 mb-0 fw-bold text-success tabular-nums mt-1">
                {fmtNum(summary.total_purchases_count || 0)}
              </div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-warning border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">مرتجعات الشراء</div>
              <div className="h3 mb-0 fw-bold text-warning tabular-nums mt-1">
                {fmtNum(summary.total_returns_count || 0)}
              </div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-danger border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">قيمة المرتجع</div>
              <div className="h3 mb-0 fw-bold text-danger tabular-nums mt-1">
                {fmtNum(summary.total_returns_amount || 0)} <span className="fs-6">ج.م</span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-info border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">صافي القطع</div>
              <div className="h3 mb-0 fw-bold text-info tabular-nums mt-1">
                {fmtNum(summary.total_items_quantity || 0)} <span className="fs-6">قطعة</span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-4 col-xl-2">
          <div className="card shadow-sm border-0 border-start border-secondary border-3">
            <div className="card-body p-2">
              <div className="text-muted small fw-bold">عدد الموردين</div>
              <div className="h3 mb-0 fw-bold text-secondary tabular-nums mt-1">
                {fmtNum(summary.suppliers_count || 0)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="card shadow-sm border-0">
        <div className="card-body p-2">
          <div className="row g-2 align-items-center">
            <div className="col-12 col-md-3">
              <select
                className="form-select form-select-sm"
                value={selectedSupplier}
                onChange={(e) => setSelectedSupplier(e.target.value)}
              >
                <option value="">جميع الموردين</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div className="col-6 col-md-2">
              <select
                className="form-select form-select-sm"
                value={invoiceType}
                onChange={(e) => setInvoiceType(e.target.value)}
              >
                <option value="ALL">الكل (شراء ومرتجع)</option>
                <option value="PURCHASE">فواتير شراء فقط</option>
                <option value="RETURN">مرتجعات مشتريات فقط</option>
              </select>
            </div>

            <div className="col-6 col-md-2">
              <DebouncedInput
                type="text"
                className="form-control form-control-sm"
                placeholder="بحث في الأصناف..."
                value={itemQuery}
                onChange={(val) => setItemQuery(val)}
              />
            </div>

            <div className="col-6 col-md-2 d-flex gap-1">
              <input
                type="number"
                className="form-control form-control-sm text-center"
                placeholder="من رقم"
                value={invoiceFrom}
                onChange={(e) => setInvoiceFrom(e.target.value)}
              />
              <input
                type="number"
                className="form-control form-control-sm text-center"
                placeholder="إلى رقم"
                value={invoiceTo}
                onChange={(e) => setInvoiceTo(e.target.value)}
              />
            </div>

            <div className="col-6 col-md-3 d-flex justify-content-end gap-2">
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
                onClick={handleResetFilters}
              >
                <IconRefresh size={14} />
                إعادة ضبط
              </button>
              <button
                type="button"
                className="btn btn-sm btn-primary d-flex align-items-center gap-1 fw-bold"
                onClick={fetchPurchases}
              >
                <IconFilter size={14} />
                تصفية
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="alert alert-danger py-2">
          {error}
        </div>
      )}

      {/* Mode B Sticky Table */}
      <ReportTable loading={loading} isEmpty={filteredInvoices.length === 0} emptyText="لا توجد فواتير مشتريات مطابقة">
        <thead className="table-sticky-header">
          <tr>
            <th style={{ width: '10%' }}>رقم الفاتورة</th>
            <th style={{ width: '12%' }}>النوع</th>
            <th style={{ width: '18%' }}>المورد</th>
            <th style={{ width: '30%' }}>الأصناف المشتراة</th>
            <th style={{ width: '10%' }} className="text-center">إجمالي القطع</th>
            <th style={{ width: '10%' }} className="text-center">التاريخ</th>
            <th style={{ width: '10%' }} className="text-end">الإجمالي (ج.م)</th>
          </tr>
        </thead>
        <tbody>
          {filteredInvoices.map((inv) => (
            <tr key={inv.id}>
              <td className="fw-bold tabular-nums">#{inv.invoice_number}</td>
              <td>
                {inv.invoice_type === 'RETURN' ? (
                  <span className="badge bg-warning-lt text-warning fw-bold d-inline-flex align-items-center gap-1">
                    <IconArrowBackUp size={14} />
                    مرتجع مشتريات
                  </span>
                ) : (
                  <span className="badge bg-success-lt text-success fw-bold d-inline-flex align-items-center gap-1">
                    <IconPackage size={14} />
                    فاتورة شراء
                  </span>
                )}
              </td>
              <td className="fw-bold text-dark">{inv.supplier_name}</td>
              <td className="text-muted small">{inv.items_summary}</td>
              <td className="text-center tabular-nums fw-bold">{fmtNum(inv.total_units || 0)}</td>
              <td className="text-center tabular-nums text-muted">{inv.invoice_date}</td>
              <td className="text-end tabular-nums fw-bold text-primary">
                {fmtNum(inv.total_cost || 0)}
              </td>
            </tr>
          ))}
        </tbody>
      </ReportTable>
    </div>
  );
}
