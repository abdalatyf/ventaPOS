import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconCalculator, IconFilter, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function AveragesReport() {
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
        console.error('Error fetching averages report:', err);
        setError('حدث خطأ أثناء جلب تقرير المتوسطات.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [year, month, branchId, salespersonId]);

  const { items, rawCombined } = useMemo(() => {
    if (!data) return { items: [], rawCombined: [] };

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

    return { items: filtered, rawCombined: combined };
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
      label: 'الكمية', 
      align: 'center', 
      render: (row) => row.qty || 0
    },
    { 
      key: 'avg_sell', 
      label: 'متوسط سعر البيع', 
      align: 'center', 
      className: 'fw-bold',
      render: (row) => fmtNum(row.avg_sell || 0)
    },
    { 
      key: 'cost_per_unit', 
      label: 'تكلفة الوحدة', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => fmtNum(row.cost_per_unit || 0)
    },
    { 
      key: 'sales_comm_per_unit', 
      label: 'متوسط المندبة', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => fmtNum(row.sales_comm_per_unit || 0)
    },
    { 
      key: 'coll_comm_per_unit', 
      label: 'متوسط عمولة التحصيل', 
      align: 'center', 
      className: 'text-danger fw-semibold', 
      render: (row) => row.sale_type === 'cash' ? 'كاش' : fmtNum(row.coll_comm_per_unit || 0)
    },
    { 
      key: 'avg_profit', 
      label: 'متوسط المكسب للقطعة', 
      align: 'center', 
      className: 'text-success fw-bolder fs-4', 
      render: (row) => {
        const profit = row.avg_profit !== undefined 
          ? row.avg_profit 
          : ((row.avg_sell || 0) - (row.cost_per_unit || 0) - (row.sales_comm_per_unit || 0) - (row.coll_comm_per_unit || 0));
        return fmtNum(profit);
      }
    }
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
      <ReportTable
        columns={columns}
        data={items}
        loading={loading}
        summaryCards={[]}
        sortableColumns={[
          { id: 'name', label: 'الصنف' },
          { id: 'qty', label: 'الكمية' },
          { id: 'avg_sell', label: 'متوسط سعر البيع' },
          { id: 'cost_per_unit', label: 'تكلفة الوحدة' },
          { id: 'sales_comm_per_unit', label: 'متوسط المندبة' },
          { id: 'coll_comm_per_unit', label: 'متوسط عمولة التحصيل' },
          { id: 'avg_profit', label: 'متوسط المكسب' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'avg_sell', dir: 'desc' },
          { id: 2, column: 'qty', dir: 'desc' }
        ]}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        emptyMessage="لا توجد بيانات متوسطات لهذه الفترة"
        emptyIcon={IconCalculator}
      />
    </div>
  );
}
