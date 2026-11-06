import React, { useState, useEffect, useContext, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { IconUser, IconReceipt, IconCoin, IconCash, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import { fmtNum } from '../../utils/formatUtils';

export default function SalespersonPerformanceReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const [data, setData] = useState({ salespersons: [], totals: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSalesperson, setSelectedSalesperson] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!year || !month || !branchId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await api.get('/reports/salesperson-performance/', {
          params: { branch_id: branchId, year, month }
        });
        setData(res.data || { salespersons: [], totals: {} });
      } catch (err) {
        console.error('Error fetching salesperson performance report:', err);
        setError('حدث خطأ أثناء جلب تقرير أداء المناديب.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [year, month, branchId]);

  const items = useMemo(() => {
    if (!data) return [];
    if (Array.isArray(data.salespersons)) return data.salespersons;
    if (Array.isArray(data.results)) return data.results;
    return [];
  }, [data]);

  const processedItems = useMemo(() => {
    if (selectedSalesperson) {
      const selectedId = selectedSalesperson.salesperson_id || selectedSalesperson.id;
      return items.filter(sp => String(sp.salesperson_id || sp.id) === String(selectedId));
    }
    if (!searchQuery.trim()) return items;
    const query = searchQuery.toLowerCase();
    return items.filter(sp => 
      String(sp.name || '').toLowerCase().includes(query) || 
      String(sp.local_id || sp.salesperson_id || '').toLowerCase().includes(query)
    );
  }, [items, searchQuery, selectedSalesperson]);

  const totals = useMemo(() => {
    return processedItems.reduce((acc, curr) => ({
      receipts: acc.receipts + (Number(curr.receipts_count) || 0),
      cash: acc.cash + (Number(curr.cash_sales) || 0),
      credit: acc.credit + (Number(curr.credit_sales) || 0),
      down_payments: acc.down_payments + (Number(curr.down_payments) || 0),
      sales: acc.sales + (Number(curr.total_sales_val) || 0),
      collected: acc.collected + (Number(curr.collected) || 0),
      comm_sales: acc.comm_sales + (Number(curr.comm_sales) || 0),
      comm_coll: acc.comm_coll + (Number(curr.comm_coll) || 0),
      due_salary: acc.due_salary + (Number(curr.due_salary) || 0),
    }), {
      receipts: 0, cash: 0, credit: 0, down_payments: 0, sales: 0, collected: 0, comm_sales: 0, comm_coll: 0, due_salary: 0
    });
  }, [processedItems]);

  const summaryCards = [
    { label: 'إجمالي الفواتير', value: totals.receipts, color: 'dark', icon: IconReceipt },
    { label: 'مبيعات كاش', value: fmtNum(totals.cash), color: 'success', icon: IconCash },
    { label: 'مبيعات قسط', value: fmtNum(totals.credit), color: 'warning', icon: IconCoin },
    { label: 'إجمالي المقدمات', value: fmtNum(totals.down_payments), color: 'info' },
    { label: 'إجمالي المبيعات', value: fmtNum(totals.sales), color: 'primary' },
    { label: 'إجمالي التحصيل', value: fmtNum(totals.collected), color: 'success' },
    { label: 'إجمالي المرتبات المستحقة', value: fmtNum(totals.due_salary), color: 'danger' }
  ];

  const columns = [
    { 
      key: 'name', 
      label: 'اسم المندوب', 
      align: 'start', 
      className: 'fw-bold text-dark px-2',
      render: (row) => row.name || 'بدون اسم'
    },
    { 
      key: 'receipts_count', 
      label: 'عدد الفواتير', 
      align: 'center', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${spId}`} 
            className="text-decoration-none badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1 fs-5 fw-bold"
            title="عرض فواتير المندوب"
          >
            {row.receipts_count}
          </Link>
        );
      }
    },
    { 
      key: 'cash_sales', 
      label: 'كاش', 
      align: 'center', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${spId}&is_cash_sale=true`} 
            className="text-decoration-none text-success fw-bold"
            title="عرض مبيعات الكاش"
          >
            {fmtNum(row.cash_sales)}
          </Link>
        );
      }
    },
    { 
      key: 'credit_sales', 
      label: 'قسط', 
      align: 'center', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${spId}&is_cash_sale=false`} 
            className="text-decoration-none text-warning fw-bold"
            title="عرض مبيعات القسط"
          >
            {fmtNum(row.credit_sales)}
          </Link>
        );
      }
    },
    { 
      key: 'down_payments', 
      label: 'المقدمات', 
      align: 'center', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${spId}&has_down_payment=true`} 
            className="text-decoration-none text-info fw-bold"
            title="عرض فواتير المقدمات"
          >
            {fmtNum(row.down_payments)}
          </Link>
        );
      }
    },
    { 
      key: 'total_sales_val', 
      label: 'إجمالي المبيعات', 
      align: 'center', 
      className: 'fw-bold bg-light', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/receipts?year=${year}&month=${month}&salesperson_id=${spId}`} 
            className="text-decoration-none text-primary fw-bolder"
            title="عرض جميع مبيعات المندوب"
          >
            {fmtNum(row.total_sales_val)}
          </Link>
        );
      }
    },
    { 
      key: 'collected', 
      label: 'تحصيل', 
      align: 'center', 
      className: 'fw-bold text-success border-start border-end', 
      render: (row) => {
        const spId = row.salesperson_id || row.id;
        return (
          <Link 
            to={`/reports/installments?year=${year}&month=${month}&salesperson_id=${spId}`} 
            className="text-decoration-none text-success fw-bolder"
            title="عرض تحصيلات المندوب"
          >
            {fmtNum(row.collected)}
          </Link>
        );
      }
    },
    { 
      key: 'comm_sales', 
      label: 'المندبة', 
      align: 'center', 
      className: 'fw-bold text-primary', 
      render: (row) => fmtNum(row.comm_sales)
    },
    { 
      key: 'comm_coll', 
      label: 'عمولة تحصيل', 
      align: 'center', 
      className: 'fw-bold text-primary', 
      render: (row) => fmtNum(row.comm_coll)
    },
    { 
      key: 'due_salary', 
      label: 'المرتب المستحق', 
      align: 'center', 
      className: 'fw-bold text-dark bg-light-subtle fs-4', 
      render: (row) => fmtNum(row.due_salary)
    }
  ];

  const renderHeader = ({ toggleSort, getColSortDir } = {}) => {
    const getSortArrow = (colKey) => {
      if (!getColSortDir) return null;
      const dir = getColSortDir(colKey);
      return dir === 'asc' ? ' ↑' : dir === 'desc' ? ' ↓' : '';
    };

    return (
      <>
        <tr>
          <th 
            rowSpan="2" 
            className="text-start px-3 align-middle bg-light sortable-th"
            onClick={() => toggleSort && toggleSort('name')}
            title="انقر للترتيب"
          >
            اسم المندوب{getSortArrow('name')}
          </th>
          <th 
            rowSpan="2" 
            className="text-center align-middle bg-light sortable-th"
            onClick={() => toggleSort && toggleSort('receipts_count')}
            title="انقر للترتيب"
          >
            عدد الفواتير{getSortArrow('receipts_count')}
          </th>
          <th colSpan="4" className="text-center bg-light">أداء المبيعات</th>
          <th 
            rowSpan="2" 
            className="text-center text-success border-start border-end align-middle bg-light sortable-th" 
            style={{ minWidth: '110px' }}
            onClick={() => toggleSort && toggleSort('collected')}
            title="انقر للترتيب"
          >
            تحصيل {month}/{year}{getSortArrow('collected')}
          </th>
          <th colSpan="3" className="text-center table-primary">تفاصيل المرتب</th>
        </tr>
        <tr className="report-sticky-header level-2">
          <th 
            className="text-center small text-muted sortable-th"
            onClick={() => toggleSort && toggleSort('cash_sales')}
            title="انقر للترتيب"
          >
            كاش{getSortArrow('cash_sales')}
          </th>
          <th 
            className="text-center small text-muted sortable-th"
            onClick={() => toggleSort && toggleSort('credit_sales')}
            title="انقر للترتيب"
          >
            قسط{getSortArrow('credit_sales')}
          </th>
          <th 
            className="text-center small text-muted sortable-th"
            onClick={() => toggleSort && toggleSort('down_payments')}
            title="انقر للترتيب"
          >
            المقدمات{getSortArrow('down_payments')}
          </th>
          <th 
            className="text-center small fw-bold text-primary bg-light sortable-th"
            onClick={() => toggleSort && toggleSort('total_sales_val')}
            title="انقر للترتيب"
          >
            إجمالي المبيعات{getSortArrow('total_sales_val')}
          </th>
          <th 
            className="text-center small text-primary table-primary sortable-th"
            onClick={() => toggleSort && toggleSort('comm_sales')}
            title="انقر للترتيب"
          >
            المندبة{getSortArrow('comm_sales')}
          </th>
          <th 
            className="text-center small text-primary table-primary sortable-th"
            onClick={() => toggleSort && toggleSort('comm_coll')}
            title="انقر للترتيب"
          >
            عمولة تحصيل{getSortArrow('comm_coll')}
          </th>
          <th 
            className="text-center small fw-bold text-dark bg-light-subtle sortable-th"
            onClick={() => toggleSort && toggleSort('due_salary')}
            title="انقر للترتيب"
          >
            المرتب المستحق{getSortArrow('due_salary')}
          </th>
        </tr>
      </>
    );
  };

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      <div style={{ width: '260px' }} className="flex-shrink-0">
        <ReportAutocomplete
          items={items}
          value={searchQuery}
          onChange={(text) => {
            setSearchQuery(text);
            if (!text) setSelectedSalesperson(null);
          }}
          onSelect={(sp) => {
            setSelectedSalesperson(sp);
            if (sp) setSearchQuery(sp.name || '');
          }}
          placeholder="ابحث عن مندوب..."
          displayKey="name"
          idKey="salesperson_id"
          searchKeys={['name', 'local_id', 'salesperson_id']}
          allowClear={true}
          className="form-control form-control-sm fw-bold border-secondary-subtle"
        />
      </div>

      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1" 
        onClick={() => {
          setSearchQuery('');
          setSelectedSalesperson(null);
        }}
        disabled={loading}
        title="إعادة ضبط"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      <div className="text-muted small fw-bold d-flex align-items-center gap-2">
        <span>الفترة: {year}/{String(month).padStart(2, '0')}</span>
        <span>•</span>
        <span>إجمالي عدد المناديب النشطين: {processedItems.length}</span>
      </div>
    </div>
  );

  return (
    <div className="w-100 p-0">
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}

      <ReportTable
        columns={columns}
        data={processedItems}
        loading={loading}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        sortableColumns={[
          { id: 'name', label: 'اسم المندوب' },
          { id: 'receipts_count', label: 'عدد الفواتير' },
          { id: 'cash_sales', label: 'مبيعات كاش' },
          { id: 'credit_sales', label: 'مبيعات قسط' },
          { id: 'down_payments', label: 'المقدمات' },
          { id: 'total_sales_val', label: 'إجمالي المبيعات' },
          { id: 'collected', label: 'التحصيل' },
          { id: 'comm_sales', label: 'المندبة' },
          { id: 'comm_coll', label: 'عمولة تحصيل' },
          { id: 'due_salary', label: 'المرتب المستحق' }
        ]}
        defaultSortRules={[
          { id: 1, column: 'total_sales_val', dir: 'desc' }
        ]}
        renderHeader={renderHeader}
        emptyMessage="لا توجد بيانات أداء للمناديب في هذه الفترة"
        emptyIcon={IconUser}
      />
    </div>
  );
}
