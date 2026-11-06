import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconMapPin, IconFilter, IconRefresh, IconUser } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import DebouncedInput from '../../components/DebouncedInput';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function AreasReport() {
  const { year, month, branchId, registerPrintHandler } = useContext(ReportsContext);

  const [areas, setAreas] = useState([]);
  const [summary, setSummary] = useState({
    total_sales: 0,
    net_sales: 0,
    total_returns_amount: 0,
    total_down_payments: 0,
    total_due_installments: 0,
    total_invoices_count: 0,
    areas_count: 0,
    top_area: '-',
  });

  const [salespersons, setSalespersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters - salesperson and area
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonName, setSalespersonName] = useState('');
  const [areaFilter, setAreaFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch salespersons for autocomplete
  useEffect(() => {
    const fetchSalespersons = async () => {
      if (!branchId) return;
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersons(res.data.results || res.data || []);
      } catch (err) {
        console.error('Failed to load salespersons:', err);
      }
    };
    fetchSalespersons();
  }, [branchId]);

  const fetchAreasReport = async () => {
    if (!branchId) return;

    setLoading(true);
    setError(null);

    const params = {
      branch_id: branchId,
    };
    if (year) params.year = year;
    if (month) params.month = month;
    if (salespersonId) params.salesperson_id = salespersonId;
    if (areaFilter) params.area = areaFilter;

    try {
      const res = await api.get('/reports/areas/', { params });
      setAreas(res.data.areas || []);
      setSummary(res.data.summary || {});
    } catch (err) {
      console.error('Error fetching areas report:', err);
      setError(err.response?.data?.detail || 'حدث خطأ أثناء تحميل تقرير المناطق.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreasReport();
  }, [branchId, year, month, salespersonId, areaFilter]);

  // Client-side quick search filter
  const filteredAreas = useMemo(() => {
    if (!searchQuery.trim()) return areas;
    const q = searchQuery.trim().toLowerCase();
    return areas.filter((row) =>
      String(row.area || '').toLowerCase().includes(q) ||
      String(row.salespersons_display || '').toLowerCase().includes(q)
    );
  }, [areas, searchQuery]);

  const handleResetFilters = () => {
    setSalespersonId('');
    setSalespersonName('');
    setAreaFilter('');
    setSearchQuery('');
  };

  // Register print handler for ReportsLayout print button
  useEffect(() => {
    if (!registerPrintHandler) return;
    registerPrintHandler(() => {
      api.post('/reports/desktop_print/', {
        title: 'تقرير المناطق والتحصيل الجغرافي',
        branch_id: branchId,
        period_label: year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined,
        action: 'view',
        filters_summary: [
          salespersonName ? { label: 'المندوب', value: salespersonName } : null,
          areaFilter ? { label: 'المنطقة', value: areaFilter } : null,
        ].filter(Boolean),
        kpis: [
          { label: 'إجمالي المبيعات', value: `${fmtNum(summary.total_sales || 0)} ج.م`, color: 'success' },
          { label: 'صافي المبيعات', value: `${fmtNum(summary.net_sales || 0)} ج.م`, color: 'primary' },
          { label: 'المقدمات', value: `${fmtNum(summary.total_down_payments || 0)} ج.م`, color: 'info' },
          { label: 'الأقساط المستحقة', value: `${fmtNum(summary.total_due_installments || 0)} ج.م`, color: 'warning' },
          { label: 'المرتجعات', value: `${fmtNum(summary.total_returns_amount || 0)} ج.م`, color: 'danger' },
          { label: 'عدد المناطق', value: fmtNum(summary.areas_count || 0), color: 'secondary' },
        ],
        columns: [
          { key: 'index', label: 'م', width: '40px', align: 'center' },
          { key: 'area', label: 'المنطقة', align: 'start' },
          { key: 'invoices_count', label: 'الفواتير', align: 'center' },
          { key: 'cash_sales', label: 'مبيعات نقدي', align: 'center' },
          { key: 'installment_sales', label: 'مبيعات تقسيط', align: 'center' },
          { key: 'gross_sales', label: 'إجمالي المبيعات', align: 'center' },
          { key: 'down_payments', label: 'المقدمات', align: 'center' },
          { key: 'due_installments_month', label: 'الأقساط المستحقة', align: 'center' },
          { key: 'returns_amount', label: 'المرتجعات', align: 'center' },
          { key: 'net_sales', label: 'صافي المبيعات', align: 'center' },
          { key: 'salespersons_display', label: 'المناديب النشطين', align: 'start' },
        ],
        rows: filteredAreas.map((r, idx) => ({
          index: idx + 1,
          area: r.area,
          invoices_count: r.invoices_count,
          cash_sales: fmtNum(r.cash_sales || 0),
          installment_sales: fmtNum(r.installment_sales || 0),
          gross_sales: fmtNum(r.gross_sales || 0),
          down_payments: fmtNum(r.down_payments || 0),
          due_installments_month: fmtNum(r.due_installments_month || 0),
          returns_amount: fmtNum(r.returns_amount || 0),
          net_sales: fmtNum(r.net_sales || 0),
          salespersons_display: r.salespersons_display,
        })),
      }).catch(err => console.error('Error opening report print modal:', err));
    });
  }, [registerPrintHandler, branchId, year, month, salespersonName, areaFilter, summary, filteredAreas]);

  const summaryCards = [
    { label: 'إجمالي المبيعات', value: `${fmtNum(summary.total_sales || 0)} ج.م`, color: 'success' },
    { label: 'صافي المبيعات', value: `${fmtNum(summary.net_sales || 0)} ج.م`, color: 'primary' },
    { label: 'إجمالي المقدمات', value: `${fmtNum(summary.total_down_payments || 0)} ج.م`, color: 'info' },
    { label: 'الأقساط المستحقة بالشهر', value: `${fmtNum(summary.total_due_installments || 0)} ج.م`, color: 'warning' },
    { label: 'إجمالي المرتجعات', value: `${fmtNum(summary.total_returns_amount || 0)} ج.م`, color: 'danger' },
    { label: 'عدد المناطق النشطة', value: fmtNum(summary.areas_count || 0), color: 'secondary' },
  ];

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Salesperson Autocomplete */}
      <div style={{ width: '240px' }} className="flex-shrink-0">
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

      {/* Area Autocomplete */}
      <div style={{ width: '240px' }} className="flex-shrink-0">
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
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Search Input */}
      <div className="flex-grow-1" style={{ minWidth: '200px' }}>
        <DebouncedInput
          type="text"
          className="form-control form-control-sm border-secondary-subtle fw-bold"
          placeholder="بحث سريع باسم المنطقة أو المندوب..."
          value={searchQuery}
          onChange={(val) => setSearchQuery(val)}
        />
      </div>

      {/* Refresh Button */}
      <button
        type="button"
        className="btn btn-sm btn-primary px-3 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1 fw-bold"
        onClick={fetchAreasReport}
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
      key: 'area',
      label: 'المنطقة',
      align: 'start',
      className: 'fw-bold text-dark px-2',
      render: (r) => r.area || 'غير محدد',
      getValue: (r) => r.area || '',
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
      key: 'cash_sales',
      label: 'مبيعات نقدي (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-success',
      render: (r) => fmtNum(r.cash_sales || 0),
      getValue: (r) => r.cash_sales || 0,
    },
    {
      key: 'installment_sales',
      label: 'مبيعات تقسيط (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-info',
      render: (r) => fmtNum(r.installment_sales || 0),
      getValue: (r) => r.installment_sales || 0,
    },
    {
      key: 'gross_sales',
      label: 'إجمالي المبيعات (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-dark',
      render: (r) => fmtNum(r.gross_sales || 0),
      getValue: (r) => r.gross_sales || 0,
    },
    {
      key: 'down_payments',
      label: 'المقدمات (ج.م)',
      align: 'center',
      className: 'tabular-nums text-muted',
      render: (r) => fmtNum(r.down_payments || 0),
      getValue: (r) => r.down_payments || 0,
    },
    {
      key: 'due_installments_month',
      label: 'الأقساط المستحقة (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-warning',
      render: (r) => fmtNum(r.due_installments_month || 0),
      getValue: (r) => r.due_installments_month || 0,
    },
    {
      key: 'returns_amount',
      label: 'المرتجعات (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-danger',
      render: (r) => fmtNum(r.returns_amount || 0),
      getValue: (r) => r.returns_amount || 0,
    },
    {
      key: 'net_sales',
      label: 'صافي المبيعات (ج.م)',
      align: 'center',
      className: 'tabular-nums fw-bold text-primary',
      render: (r) => fmtNum(r.net_sales || 0),
      getValue: (r) => r.net_sales || 0,
    },
    {
      key: 'salespersons_display',
      label: 'المناديب النشطين',
      align: 'start',
      className: 'text-muted small px-2',
      render: (r) => r.salespersons_display || '-',
      getValue: (r) => r.salespersons_display || '',
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
        reportTitle="تقرير المناطق والتحصيل الجغرافي"
        periodLabel={year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined}
        columns={columns}
        data={filteredAreas}
        loading={loading}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        sortableColumns={[
          { id: 'area', label: 'المنطقة' },
          { id: 'invoices_count', label: 'الفواتير' },
          { id: 'gross_sales', label: 'إجمالي المبيعات' },
          { id: 'due_installments_month', label: 'الأقساط المستحقة' },
          { id: 'net_sales', label: 'صافي المبيعات' },
        ]}
        defaultSortRules={[{ id: 1, column: 'net_sales', dir: 'desc' }]}
        emptyMessage="لا توجد بيانات مناطق مطابقة"
        emptyIcon={IconMapPin}
      />
    </div>
  );
}
