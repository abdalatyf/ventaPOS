import React, { useState, useEffect, useContext, useMemo } from 'react';
import { IconBox, IconPackage, IconCoin } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function InventoryMovementReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const [data, setData] = useState({ items: [], total_inventory_value: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const [salespersonsList, setSalespersonsList] = useState([]);

  useEffect(() => {
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersonsList(res.data.results || res.data || []);
      } catch (err) {
        console.error('Error fetching salespersons list:', err);
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
        const res = await api.get('/reports/inventory-movement/', {
          params: {
            year,
            month,
            branch_id: branchId,
            salesperson_id: salespersonId || undefined
          }
        });
        setData(res.data || { items: [], total_inventory_value: 0 });
      } catch (err) {
        console.error('Error fetching inventory movement report:', err);
        setError(err.response?.data?.detail || 'حدث خطأ أثناء تحميل حركة المخزون');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [year, month, branchId, salespersonId]);

  const items = useMemo(() => {
    if (!data) return [];
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.results)) return data.results;
    return [];
  }, [data]);

  const processedItems = useMemo(() => {
    if (selectedProduct) {
      const selectedId = selectedProduct.product_id || selectedProduct.id;
      return items.filter(item => String(item.product_id || item.id) === String(selectedId));
    }
    if (!searchQuery.trim()) return items;
    const query = searchQuery.toLowerCase();
    return items.filter(item => 
      String(item.product_name || '').toLowerCase().includes(query) || 
      String(item.product_id || item.id || '').toLowerCase().includes(query)
    );
  }, [items, searchQuery, selectedProduct]);

  const totals = useMemo(() => {
    return processedItems.reduce((acc, curr) => {
      const opening = Number(curr.opening_stock) || 0;
      const purchases = Number(curr.purchases) || 0;
      const sales_returns = Number(curr.sales_returns || curr.surplus) || 0;
      const sales = Number(curr.sales) || 0;
      const purchase_returns = Number(curr.purchase_returns || curr.returns) || 0;
      const deficit = Number(curr.deficit) || 0;
      const final_stock = Number(curr.final_stock) || 0;
      const total_value = Number(curr.total_value) || (final_stock * (Number(curr.unit_cost) || 0));

      return {
        opening_stock: acc.opening_stock + opening,
        purchases: acc.purchases + purchases,
        sales_returns: acc.sales_returns + sales_returns,
        sales: acc.sales + sales,
        purchase_returns: acc.purchase_returns + purchase_returns,
        deficit: acc.deficit + deficit,
        final_stock: acc.final_stock + final_stock,
        total_value: acc.total_value + total_value
      };
    }, {
      opening_stock: 0,
      purchases: 0,
      sales_returns: 0,
      sales: 0,
      purchase_returns: 0,
      deficit: 0,
      final_stock: 0,
      total_value: 0
    });
  }, [processedItems]);

  const columns = [
    { 
      key: 'product_name', 
      label: 'الصنف', 
      align: 'start', 
      className: 'fw-bold text-dark px-2',
      render: (row) => row.product_name || 'بدون اسم'
    },
    { 
      key: 'opening_stock', 
      label: 'رصيد أول', 
      align: 'center', 
      render: (row) => row.opening_stock || 0
    },
    { 
      key: 'purchases', 
      label: 'المشتريات (+)', 
      align: 'center', 
      className: 'text-success fw-bold', 
      render: (row) => `+${row.purchases || 0}` 
    },
    { 
      key: 'sales_returns', 
      label: 'مرتجع مبيعات (+)', 
      align: 'center', 
      className: 'text-success fw-bold', 
      render: (row) => `+${row.sales_returns || row.surplus || 0}` 
    },
    { 
      key: 'sales', 
      label: 'المبيعات (-)', 
      align: 'center', 
      className: 'text-dark fw-bold', 
      render: (row) => `-${row.sales || 0}` 
    },
    { 
      key: 'purchase_returns', 
      label: 'مرتجع مشتريات (-)', 
      align: 'center', 
      className: 'text-danger fw-bold', 
      render: (row) => `-${row.purchase_returns || row.returns || 0}` 
    },
    { 
      key: 'deficit', 
      label: 'العجز (-)', 
      align: 'center', 
      className: 'text-danger fw-bold', 
      render: (row) => `-${row.deficit || 0}` 
    },
    { 
      key: 'final_stock', 
      label: 'رصيد آخر', 
      align: 'center', 
      render: (row) => (
        <span className="badge bg-info-subtle text-info border border-info-subtle fw-bolder fs-5 px-3 py-1">
          {row.final_stock || 0}
        </span>
      )
    },
    { 
      key: 'unit_cost', 
      label: 'تكلفة الوحدة', 
      align: 'center', 
      className: 'text-muted', 
      render: (row) => fmtNum(row.unit_cost || 0)
    },
    { 
      key: 'total_value', 
      label: 'إجمالي القيمة', 
      align: 'center', 
      className: 'fw-bold text-success fs-5', 
      render: (row) => fmtNum(row.total_value || 0)
    },
  ];

  const summaryCards = [
    { label: 'رصيد أول', value: totals.opening_stock, color: 'dark', icon: IconBox },
    { label: 'المشتريات (+)', value: totals.purchases, color: 'success' },
    { label: 'مرتجع مبيعات (+)', value: totals.sales_returns, color: 'success' },
    { label: 'المبيعات (-)', value: totals.sales, color: 'primary' },
    { label: 'مرتجع مشتريات (-)', value: totals.purchase_returns, color: 'danger' },
    { label: 'العجز (-)', value: totals.deficit, color: 'danger' },
    { label: 'رصيد آخر', value: totals.final_stock, color: 'info', icon: IconPackage },
    { label: 'إجمالي القيمة', value: fmtNum(totals.total_value || data.total_inventory_value), color: 'success', icon: IconCoin }
  ];

  const renderFiltersGrid = () => (
    <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
      <div className="card-body p-3">
        <form onSubmit={(e) => e.preventDefault()}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            <div style={{ gridColumn: 'span 5' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '80px' }}>الصنف</span>
                <ReportAutocomplete
                  items={items}
                  value={searchQuery}
                  onChange={(text) => {
                    setSearchQuery(text);
                    if (!text) setSelectedProduct(null);
                  }}
                  onSelect={(prod) => {
                    setSelectedProduct(prod);
                    if (prod) setSearchQuery(prod.product_name || '');
                  }}
                  placeholder="ابحث عن صنف..."
                  displayKey="product_name"
                  idKey="product_id"
                  searchKeys={['product_name', 'product_id', 'id']}
                  allowClear={true}
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 5' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '80px' }}>المندوب</span>
                <ReportAutocomplete
                  items={salespersonsList}
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
                  placeholder="جميع المناديب"
                  displayKey="name"
                  idKey="id"
                  searchKeys={['name', 'local_id']}
                  allowClear={true}
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>

          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="container-fluid p-0 d-flex flex-column" dir="rtl" style={{ minHeight: 'calc(100vh - 100px)' }}>
      {error && <div className="alert alert-danger mb-3">{error}</div>}
      
      {renderFiltersGrid()}

      <ReportTable
        columns={columns}
        data={processedItems}
        loading={loading}
        summaryCards={summaryCards}
        sortableColumns={[
          { id: 'product_name', label: 'الصنف' },
          { id: 'opening_stock', label: 'رصيد أول' },
          { id: 'purchases', label: 'المشتريات' },
          { id: 'sales', label: 'المبيعات' },
          { id: 'final_stock', label: 'رصيد آخر' },
          { id: 'unit_cost', label: 'تكلفة الوحدة' },
          { id: 'total_value', label: 'إجمالي القيمة' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'sales', dir: 'desc' },
          { id: 2, column: 'final_stock', dir: 'desc' }
        ]}
        emptyMessage="لا توجد حركة للمخزون في هذه الفترة"
        emptyIcon={IconBox}
      />
    </div>
  );
}
