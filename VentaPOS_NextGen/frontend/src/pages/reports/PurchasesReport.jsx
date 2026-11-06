import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconPackage, IconFilter, IconRefresh, IconArrowBackUp } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function PurchasesReport() {
  const { year, month, branchId, registerPrintHandler } = useContext(ReportsContext);

  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({
    total_purchases_amount: 0,
    gross_purchases_amount: 0,
    total_purchases_count: 0,
    total_returns_count: 0,
    total_returns_amount: 0,
    total_items_quantity: 0,
    suppliers_count: 0,
    distinct_products_count: 0,
  });

  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters - ONLY PurchasesReport has supplier filter
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedProductName, setSelectedProductName] = useState('');
  const [invoiceType, setInvoiceType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch branch-scoped suppliers list
  useEffect(() => {
    const fetchSuppliers = async () => {
      if (!branchId) return;
      try {
        const res = await api.get('/suppliers/', { params: { branch_id: branchId } });
        setSuppliers(res.data.results || res.data || []);
      } catch (err) {
        console.error('Failed to load suppliers:', err);
      }
    };
    fetchSuppliers();
  }, [branchId]);

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
    if (selectedProductId) params.item_id = selectedProductId;
    if (invoiceType !== 'ALL') params.invoice_type = invoiceType;

    try {
      const res = await api.get('/reports/purchases/', { params });
      setItems(res.data.items || []);
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
  }, [branchId, year, month, selectedSupplier, selectedProductId, invoiceType]);

  // Client-side text filter on item_name and supplier_name
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;
    const q = searchQuery.trim().toLowerCase();
    return items.filter((row) =>
      String(row.item_name || '').toLowerCase().includes(q) ||
      String(row.supplier_name || '').toLowerCase().includes(q)
    );
  }, [items, searchQuery]);

  const handleResetFilters = () => {
    setSelectedSupplier('');
    setSelectedProductId('');
    setSelectedProductName('');
    setInvoiceType('ALL');
    setSearchQuery('');
  };

  // Register print handler for ReportsLayout print button
  useEffect(() => {
    if (!registerPrintHandler) return;
    registerPrintHandler(() => {
      api.post('/reports/desktop_print/', {
        title: 'تقرير المشتريات والموردين',
        branch_id: branchId,
        period_label: year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined,
        action: 'view',
        filters_summary: [
          selectedSupplier ? { label: 'المورد', value: suppliers.find(s => s.id === Number(selectedSupplier))?.name || selectedSupplier } : null,
          selectedProductName ? { label: 'الصنف', value: selectedProductName } : null,
          invoiceType !== 'ALL' ? { label: 'نوع الفاتورة', value: invoiceType === 'PURCHASE' ? 'شراء' : 'مرتجع' } : null,
        ].filter(Boolean),
        kpis: [
          { label: 'صافي المشتريات', value: `${fmtNum(summary.total_purchases_amount || 0)} ج.م`, color: 'primary' },
          { label: 'إجمالي الشراء', value: `${fmtNum(summary.gross_purchases_amount || 0)} ج.م`, color: 'success' },
          { label: 'إجمالي المرتجع', value: `${fmtNum(summary.total_returns_amount || 0)} ج.م`, color: 'danger' },
          { label: 'صافي القطع', value: fmtNum(summary.total_items_quantity || 0), color: 'info' },
          { label: 'عدد الأصناف', value: fmtNum(summary.distinct_products_count || 0), color: 'secondary' },
          { label: 'عدد الموردين', value: fmtNum(summary.suppliers_count || 0), color: 'warning' },
        ],
        columns: [
          { key: 'index', label: 'م', width: '40px', align: 'center' },
          { key: 'item_name', label: 'اسم الصنف', align: 'start' },
          { key: 'supplier_name', label: 'اسم المورد', align: 'start' },
          { key: 'invoices_count', label: 'الفواتير', align: 'center' },
          { key: 'purchased_qty', label: 'كمية الشراء', align: 'center' },
          { key: 'returned_qty', label: 'كمية المرتجع', align: 'center' },
          { key: 'net_qty', label: 'صافي الكمية', align: 'center' },
          { key: 'avg_unit_cost', label: 'متوسط السعر', align: 'center' },
          { key: 'gross_purchases', label: 'إجمالي الشراء', align: 'center' },
          { key: 'returns_amount', label: 'إجمالي المرتجع', align: 'center' },
          { key: 'net_purchases', label: 'صافي المشتريات', align: 'center' },
        ],
        rows: filteredItems.map((r, idx) => ({
          index: idx + 1,
          item_name: r.item_name,
          supplier_name: r.supplier_name,
          invoices_count: r.invoices_count,
          purchased_qty: fmtNum(r.purchased_qty || 0),
          returned_qty: fmtNum(r.returned_qty || 0),
          net_qty: fmtNum(r.net_qty || 0),
          avg_unit_cost: fmtNum(r.avg_unit_cost || 0),
          gross_purchases: fmtNum(r.gross_purchases || 0),
          returns_amount: fmtNum(r.returns_amount || 0),
          net_purchases: fmtNum(r.net_purchases || 0),
        })),
      }).catch(err => console.error('Error opening report print modal:', err));
    });
  }, [registerPrintHandler, branchId, year, month, selectedSupplier, selectedProductName, invoiceType, summary, filteredItems, suppliers]);

  const summaryCards = [
    { label: 'صافي المشتريات', value: `${fmtNum(summary.total_purchases_amount || 0)} ج.م`, color: 'primary' },
    { label: 'إجمالي الشراء', value: `${fmtNum(summary.gross_purchases_amount || 0)} ج.م`, color: 'success' },
    { label: 'إجمالي المرتجع', value: `${fmtNum(summary.total_returns_amount || 0)} ج.م`, color: 'danger' },
    { label: 'صافي القطع المشتراة', value: `${fmtNum(summary.total_items_quantity || 0)} قطعة`, color: 'info' },
    { label: 'عدد الأصناف', value: fmtNum(summary.distinct_products_count || 0), color: 'secondary' },
    { label: 'عدد الموردين', value: fmtNum(summary.suppliers_count || 0), color: 'warning' },
  ];

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Supplier Dropdown - ONLY PurchasesReport has supplier filter */}
      <div style={{ width: '220px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المورد</span>
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
      </div>

      {/* Product Autocomplete */}
      <div style={{ width: '260px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الصنف</span>
          <ReportAutocomplete
            value={selectedProductName}
            onChange={(val) => {
              setSelectedProductName(val);
              if (!val) setSelectedProductId('');
            }}
            onSelect={(item) => {
              setSelectedProductName(item.name || '');
              setSelectedProductId(item.id || '');
            }}
            fetchSuggestions={async (query) => {
              try {
                const res = await api.get('/inventory-items/', {
                  params: { branch_id: branchId, search: query, limit: 10 }
                });
                return res.data?.results || res.data || [];
              } catch {
                return [];
              }
            }}
            placeholder="جميع الأصناف..."
            className="form-control fw-bold border-secondary-subtle px-1"
          />
        </div>
      </div>

      {/* Invoice Type */}
      <div style={{ width: '150px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
          <select
            className="form-select form-select-sm border-secondary-subtle fw-bold text-center"
            value={invoiceType}
            onChange={(e) => setInvoiceType(e.target.value)}
          >
            <option value="ALL">الكل</option>
            <option value="PURCHASE">شراء فقط</option>
            <option value="RETURN">مرتجع فقط</option>
          </select>
        </div>
      </div>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Search Input */}
      <div className="flex-grow-1" style={{ minWidth: '200px' }}>
        <DebouncedInput
          type="text"
          className="form-control form-control-sm border-secondary-subtle fw-bold"
          placeholder="بحث سريع باسم الصنف أو المورد..."
          value={searchQuery}
          onChange={(val) => setSearchQuery(val)}
        />
      </div>

      {/* Refresh Button */}
      <button
        type="button"
        className="btn btn-sm btn-primary px-3 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1 fw-bold"
        onClick={fetchPurchases}
      >
        <IconFilter size={14} />
        <span>تحديث</span>
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
      key: 'index',
      label: '#',
      align: 'center',
      className: 'tabular-nums text-muted w-1',
      render: (_, idx) => idx + 1,
      getValue: (_, idx) => idx + 1,
    },
    {
      key: 'item_name',
      label: 'اسم الصنف',
      align: 'start',
      className: 'fw-bold text-dark px-2',
      render: (r) => r.item_name || 'غير محدد',
      getValue: (r) => r.item_name || '',
    },
    {
      key: 'supplier_name',
      label: 'اسم المورد',
      align: 'start',
      className: 'fw-bold text-secondary px-2',
      render: (r) => r.supplier_name || 'مورد عام',
      getValue: (r) => r.supplier_name || '',
    },
    {
      key: 'invoices_count',
      label: 'الفواتير',
      align: 'center',
      className: 'tabular-nums fw-bold',
      render: (r) => fmtNum(r.invoices_count || 0),
      getValue: (r) => r.invoices_count || 0,
    },
    {
      key: 'purchased_qty',
      label: 'كمية الشراء',
      align: 'center',
      className: 'tabular-nums fw-bold text-success',
      render: (r) => fmtNum(r.purchased_qty || 0),
      getValue: (r) => r.purchased_qty || 0,
    },
    {
      key: 'returned_qty',
      label: 'كمية المرتجع',
      align: 'center',
      className: 'tabular-nums fw-bold text-danger',
      render: (r) => fmtNum(r.returned_qty || 0),
      getValue: (r) => r.returned_qty || 0,
    },
    {
      key: 'net_qty',
      label: 'صافي الكمية',
      align: 'center',
      className: 'tabular-nums fw-bold text-dark',
      render: (r) => fmtNum(r.net_qty || 0),
      getValue: (r) => r.net_qty || 0,
    },
    {
      key: 'avg_unit_cost',
      label: 'متوسط السعر (ج.م)',
      align: 'center',
      className: 'tabular-nums text-muted',
      render: (r) => fmtNum(r.avg_unit_cost || 0),
      getValue: (r) => r.avg_unit_cost || 0,
    },
    {
      key: 'gross_purchases',
      label: 'إجمالي الشراء (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-success',
      render: (r) => fmtNum(r.gross_purchases || 0),
      getValue: (r) => r.gross_purchases || 0,
    },
    {
      key: 'returns_amount',
      label: 'إجمالي المرتجع (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-danger',
      render: (r) => fmtNum(r.returns_amount || 0),
      getValue: (r) => r.returns_amount || 0,
    },
    {
      key: 'net_purchases',
      label: 'صافي المشتريات (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-primary',
      render: (r) => fmtNum(r.net_purchases || 0),
      getValue: (r) => r.net_purchases || 0,
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
        reportTitle="تقرير المشتريات والموردين"
        periodLabel={year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined}
        columns={columns}
        data={filteredItems}
        loading={loading}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        sortableColumns={[
          { id: 'item_name', label: 'اسم الصنف' },
          { id: 'supplier_name', label: 'اسم المورد' },
          { id: 'net_qty', label: 'صافي الكمية' },
          { id: 'net_purchases', label: 'صافي المشتريات' },
        ]}
        defaultSortRules={[{ id: 1, column: 'net_purchases', dir: 'desc' }]}
        emptyMessage="لا توجد مشتريات مطابقة"
        emptyIcon={IconPackage}
      />
    </div>
  );
}
