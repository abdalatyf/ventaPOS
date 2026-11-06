import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconCalculator, IconFilter, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function ProfitAndLossReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [productQuery, setProductQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  const [saleTypeFilter, setSaleTypeFilter] = useState('all');
  
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const [salespersons, setSalespersons] = useState([]);

  useEffect(() => {
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersons(res.data.results || res.data || []);
      } catch (err) {
        console.error('Error fetching salespersons:', err);
      }
    };
    if (branchId) fetchSalespersons();
  }, [branchId]);

  useEffect(() => {
    const fetchReport = async () => {
      if (!year || !month || !branchId) return;
      setLoading(true);
      setError(null);
      try {
        let url = `/reports/profit-and-loss/?branch_id=${branchId}&month=${month}&year=${year}`;
        if (salespersonId) url += `&salesperson_id=${salespersonId}`;
        const res = await api.get(url);
        setData(res.data);
      } catch (err) {
        console.error('Error fetching profit and loss report:', err);
        setError('حدث خطأ أثناء جلب تقرير الأرباح والخسائر.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [year, month, branchId, salespersonId]);

  const { items, rawCombined, totals } = useMemo(() => {
    if (!data) return { items: [], rawCombined: [], totals: { revenue: 0, cost: 0, salesCommission: 0, collCommission: 0, expenses: 0, deficitLoss: 0, profit: 0 } };

    const cashItems = (data.cash_sales_profitability || []).map(item => ({ ...item, sale_type: 'cash' }));
    const installmentItems = (data.installment_sales_profitability || []).map(item => ({ ...item, sale_type: 'installment' }));
    const combined = [...cashItems, ...installmentItems];

    let filtered = combined.filter(item => {
      if (saleTypeFilter !== 'all' && item.sale_type !== saleTypeFilter) return false;
      if (selectedProduct) {
        return String(item.id) === String(selectedProduct.id);
      }
      if (productQuery.trim()) {
        const query = productQuery.toLowerCase();
        return String(item.name || '').toLowerCase().includes(query) || String(item.id || '').toLowerCase().includes(query);
      }
      return true;
    });

    let grandRev = 0, grandCost = 0, grandSalesComm = 0, grandCollComm = 0;
    filtered.forEach(item => {
      grandRev += Number(item.total_rev) || 0;
      grandCost += Number(item.total_cost) || 0;
      grandSalesComm += Number(item.total_sales_comm) || 0;
      grandCollComm += Number(item.total_coll_comm) || 0;
    });
    
    const expenses = Number(data.summary?.expenses_total) || 0;
    const deficitLoss = Number(data.summary?.deficit_loss) || 0;
    const netProfit = grandRev - grandCost - grandSalesComm - grandCollComm - expenses - deficitLoss;

    return {
      items: filtered,
      rawCombined: combined,
      totals: {
        revenue: grandRev,
        cost: grandCost,
        salesCommission: grandSalesComm,
        collCommission: grandCollComm,
        expenses: expenses,
        deficitLoss: deficitLoss,
        profit: netProfit
      }
    };
  }, [data, saleTypeFilter, productQuery, selectedProduct]);

  // Unique products for autocomplete
  const uniqueProducts = useMemo(() => {
    const map = new Map();
    rawCombined.forEach(p => {
      if (!map.has(p.id)) {
        map.set(p.id, { id: p.id, name: p.name });
      }
    });
    return Array.from(map.values());
  }, [rawCombined]);

  const columns = [
    { 
      key: 'name', 
      label: 'الصنف', 
      align: 'start', 
      className: 'fw-bold text-primary text-wrap px-2',
      render: (row) => row.name || 'بدون اسم'
    },
    { 
      key: 'qty', 
      label: 'الكمية المباعة', 
      align: 'center', 
      render: (row) => row.qty || 0
    },
    { 
      key: 'total_rev', 
      label: 'إجمالي الإيراد', 
      align: 'center', 
      className: 'fw-bold',
      render: (row) => fmtNum(row.total_rev || 0)
    },
    { 
      key: 'total_cost', 
      label: 'إجمالي التكلفة', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => fmtNum(row.total_cost || 0)
    },
    { 
      key: 'total_sales_comm', 
      label: 'إجمالي المندبة', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => fmtNum(row.total_sales_comm || 0)
    },
    { 
      key: 'total_coll_comm', 
      label: 'إجمالي عمولة التحصيل', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => row.sale_type === 'cash' ? 'كاش' : fmtNum(row.total_coll_comm || 0)
    },
    { 
      key: 'total_profit', 
      label: 'إجمالي المكسب', 
      align: 'center', 
      className: 'text-success fw-bolder fs-4', 
      render: (row) => {
        const profit = row.total_profit !== undefined 
          ? row.total_profit 
          : ((row.total_rev || 0) - (row.total_cost || 0) - (row.total_sales_comm || 0) - (row.total_coll_comm || 0));
        return fmtNum(profit);
      }
    }
  ];

  const summaryCards = [
    { label: 'المبيعات', value: fmtNum(totals.revenue), color: 'primary' },
    { label: 'التكلفة (-)', value: fmtNum(totals.cost), color: 'danger' },
    { label: 'المندبة (-)', value: fmtNum(totals.salesCommission), color: 'warning' },
    { label: 'عمولة التحصيل (-)', value: fmtNum(totals.collCommission), color: 'warning' },
    { label: 'المصروفات (-)', value: fmtNum(totals.expenses), color: 'danger' },
    { label: 'خسائر العجز (-)', value: fmtNum(totals.deficitLoss), color: 'danger' },
    { label: 'صافي الربح', value: fmtNum(totals.profit), color: totals.profit >= 0 ? 'success' : 'danger' }
  ];

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Search Product */}
      <div className="flex-grow-1" style={{ minWidth: '220px' }}>
        <ReportAutocomplete
          items={uniqueProducts}
          value={productQuery}
          onChange={(text) => {
            setProductQuery(text);
            if (!text) setSelectedProduct(null);
          }}
          onSelect={(prod) => {
            setSelectedProduct(prod);
            if (prod) setProductQuery(prod.name || '');
          }}
          placeholder="ابحث عن صنف..."
          displayKey="name"
          idKey="id"
          searchKeys={['name', 'id']}
          allowClear={true}
          className="form-control form-control-sm fw-bold border-secondary-subtle"
        />
      </div>

      {/* Sale Type Select */}
      <div style={{ width: '150px' }} className="flex-shrink-0">
        <select 
          className="form-select form-select-sm fw-bold border-secondary-subtle text-center" 
          value={saleTypeFilter}
          onChange={(e) => setSaleTypeFilter(e.target.value)}
        >
          <option value="all">جميع المبيعات</option>
          <option value="cash">كاش فقط</option>
          <option value="installment">قسط فقط</option>
        </select>
      </div>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Salesperson Autocomplete */}
      <div style={{ width: '220px' }} className="flex-shrink-0">
        <ReportAutocomplete
          items={salespersons}
          value={salespersonQuery}
          onChange={(text) => {
            setSalespersonQuery(text);
            if (!text) setSalespersonId('');
          }}
          onSelect={(sp) => {
            if (sp) {
              setSalespersonId(String(sp.id || sp.local_id));
              setSalespersonQuery(sp.name || '');
            } else {
              setSalespersonId('');
              setSalespersonQuery('');
            }
          }}
          placeholder="تصفية حسب المندوب..."
          displayKey="name"
          idKey="id"
          searchKeys={['name', 'local_id']}
          allowClear={true}
          className="form-control form-control-sm fw-bold border-secondary-subtle"
        />
      </div>

      {/* Reset */}
      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1" 
        onClick={() => {
          setProductQuery('');
          setSelectedProduct(null);
          setSaleTypeFilter('all');
          setSalespersonId('');
          setSalespersonQuery('');
        }}
        disabled={loading}
        title="إعادة ضبط"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>
    </div>
  );

  return (
    <div className="w-100 p-0">
      {error && <div className="alert alert-danger mb-3">{error}</div>}
      
      <ReportTable
        reportTitle="تقرير الأرباح والخسائر"
        periodLabel={year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined}
        columns={columns}
        data={items}
        loading={loading}
        summaryCards={summaryCards}
        sortableColumns={[
          { id: 'name', label: 'الصنف' },
          { id: 'qty', label: 'الكمية المباعة' },
          { id: 'total_rev', label: 'إجمالي الإيراد' },
          { id: 'total_cost', label: 'إجمالي التكلفة' },
          { id: 'total_sales_comm', label: 'إجمالي المندبة' },
          { id: 'total_coll_comm', label: 'إجمالي عمولة التحصيل' },
          { id: 'total_profit', label: 'إجمالي المكسب' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'total_profit', dir: 'desc' }
        ]}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        emptyMessage="لا توجد بيانات أرباح وخسائر لهذه الفترة"
        emptyIcon={IconCalculator}
      />
    </div>
  );
}
