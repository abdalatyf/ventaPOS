import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconPackage, IconFilter, IconRefresh, IconArrowBackUp } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum } from '../../utils/formatUtils';

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

  const summaryCards = [
    { label: 'صافي المشتريات', value: `${fmtNum(summary.total_purchases_amount || 0)} ج.م`, color: 'primary' },
    { label: 'فواتير الشراء', value: fmtNum(summary.total_purchases_count || 0), color: 'success' },
    { label: 'مرتجعات الشراء', value: fmtNum(summary.total_returns_count || 0), color: 'warning' },
    { label: 'قيمة المرتجع', value: `${fmtNum(summary.total_returns_amount || 0)} ج.م`, color: 'danger' },
    { label: 'صافي القطع', value: `${fmtNum(summary.total_items_quantity || 0)} قطعة`, color: 'info' },
    { label: 'عدد الموردين', value: fmtNum(summary.suppliers_count || 0), color: 'secondary' },
  ];

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Supplier Dropdown */}
      <div style={{ width: '180px' }} className="flex-shrink-0">
        <select
          className="form-select form-select-sm border-secondary-subtle fw-bold"
          value={selectedSupplier}
          onChange={(e) => setSelectedSupplier(e.target.value)}
        >
          <option value="">جميع الموردين</option>
          {suppliers.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      {/* Invoice Type */}
      <div style={{ width: '140px' }} className="flex-shrink-0">
        <select
          className="form-select form-select-sm border-secondary-subtle fw-bold text-center"
          value={invoiceType}
          onChange={(e) => setInvoiceType(e.target.value)}
        >
          <option value="ALL">جميع الأنواع</option>
          <option value="PURCHASE">شراء فقط</option>
          <option value="RETURN">مرتجع فقط</option>
        </select>
      </div>

      {/* Invoice From/To */}
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <input
          type="number"
          className="form-control form-control-sm text-center border-secondary-subtle fw-bold px-1"
          placeholder="من رقم"
          value={invoiceFrom}
          onChange={(e) => setInvoiceFrom(e.target.value)}
        />
      </div>
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <input
          type="number"
          className="form-control form-control-sm text-center border-secondary-subtle fw-bold px-1"
          placeholder="إلى رقم"
          value={invoiceTo}
          onChange={(e) => setInvoiceTo(e.target.value)}
        />
      </div>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Item Query */}
      <div className="flex-grow-1" style={{ minWidth: '180px' }}>
        <DebouncedInput
          type="text"
          className="form-control form-control-sm border-secondary-subtle fw-bold"
          placeholder="بحث في الأصناف..."
          value={itemQuery}
          onChange={(val) => setItemQuery(val)}
        />
      </div>

      {/* Filter Button */}
      <button
        type="button"
        className="btn btn-sm btn-primary px-3 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1 fw-bold"
        onClick={fetchPurchases}
      >
        <IconFilter size={14} />
        <span>تصفية</span>
      </button>

      {/* Reset Button */}
      <button
        type="button"
        className="btn btn-sm btn-outline-secondary px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1"
        onClick={handleResetFilters}
        title="إعادة ضبط"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>
    </div>
  );

  const columns = [
    {
      key: 'invoice_number',
      label: 'رقم الفاتورة',
      align: 'center',
      className: 'fw-bold tabular-nums',
      render: (inv) => `#${inv.invoice_number}`,
      getValue: (inv) => `#${inv.invoice_number}`,
    },
    {
      key: 'invoice_type',
      label: 'النوع',
      align: 'center',
      render: (inv) =>
        inv.invoice_type === 'RETURN' ? (
          <span className="badge bg-warning-lt text-warning fw-bold d-inline-flex align-items-center gap-1">
            <IconArrowBackUp size={14} />
            مرتجع مشتريات
          </span>
        ) : (
          <span className="badge bg-success-lt text-success fw-bold d-inline-flex align-items-center gap-1">
            <IconPackage size={14} />
            فاتورة شراء
          </span>
        ),
      getValue: (inv) => (inv.invoice_type === 'RETURN' ? 'مرتجع مشتريات' : 'فاتورة شراء'),
    },
    {
      key: 'supplier_name',
      label: 'المورد',
      align: 'start',
      className: 'fw-bold text-dark px-2',
      render: (inv) => inv.supplier_name || 'غير محدد',
    },
    {
      key: 'items_summary',
      label: 'الأصناف المشتراة',
      align: 'start',
      className: 'text-muted small px-2',
      render: (inv) => inv.items_summary || '-',
    },
    {
      key: 'total_units',
      label: 'إجمالي القطع',
      align: 'center',
      className: 'tabular-nums fw-bold',
      render: (inv) => fmtNum(inv.total_units || 0),
    },
    {
      key: 'invoice_date',
      label: 'التاريخ',
      align: 'center',
      className: 'tabular-nums text-muted',
      render: (inv) => inv.invoice_date || '-',
    },
    {
      key: 'total_cost',
      label: 'الإجمالي (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-primary',
      render: (inv) => fmtNum(inv.total_cost || 0),
      format: 'currency',
    },
  ];

  return (
    <div className="w-100 p-0">
      {error && (
        <div className="alert alert-danger py-2 mb-2">
          {error}
        </div>
      )}

      <ReportTable
        reportTitle="تقرير فواتير المشتريات"
        periodLabel={year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined}
        columns={columns}
        data={filteredInvoices}
        loading={loading}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        sortableColumns={[
          { id: 'invoice_number', label: 'رقم الفاتورة' },
          { id: 'supplier_name', label: 'المورد' },
          { id: 'total_units', label: 'إجمالي القطع' },
          { id: 'total_cost', label: 'الإجمالي' },
        ]}
        defaultSortRules={[{ id: 1, column: 'invoice_number', dir: 'desc' }]}
        emptyMessage="لا توجد فواتير مشتريات مطابقة"
        emptyIcon={IconPackage}
      />
    </div>
  );
}
