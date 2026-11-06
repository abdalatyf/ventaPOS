import React, { useState, useEffect, useContext, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { IconFilter, IconReceipt, IconPrinter, IconSearch, IconRefresh, IconCalendarEvent } from '@tabler/icons-react';
import toast from 'react-hot-toast';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import DebouncedInput from '../../components/DebouncedInput';
import PrintModal from '../../components/common/PrintModal';
import { fmtNum, toEnglish, formatMMYYYY } from '../../utils/formatUtils';

export default function InstallmentsReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const [salespersonsList, setSalespersonsList] = useState([]);
  
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [area, setArea] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState({ total_installments_amount: 0, installments_count: 0, installments: [] });

  const [selectedIds, setSelectedIds] = useState([]);
  const [printModalOpen, setPrintModalOpen] = useState(false);
  const [printReceiptIds, setPrintReceiptIds] = useState([]);

  useEffect(() => {
    const spId = searchParams.get('salesperson_id');
    if (spId) setSalespersonId(spId);
  }, [searchParams]);

  useEffect(() => {
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersonsList(res.data.results || res.data || []);
      } catch (err) {
        console.error("Failed to load salespersons", err);
      }
    };
    if (branchId) fetchSalespersons();
  }, [branchId]);

  useEffect(() => {
    if (salespersonId && salespersonsList.length > 0) {
      const found = salespersonsList.find(s => String(s.id) === String(salespersonId) || String(s.local_id) === String(salespersonId));
      if (found) setSalespersonQuery(found.name);
    } else if (!salespersonId) {
      setSalespersonQuery('');
    }
  }, [salespersonId, salespersonsList]);

  const fetchData = async () => {
    if (!branchId) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/reports/installments/', {
        params: {
          branch_id: branchId,
          year: year || undefined,
          month: month || undefined,
          salesperson_id: salespersonId || undefined,
          customer_name: customerName ? toEnglish(customerName).trim() : undefined,
          phone: phone ? toEnglish(phone).trim() : undefined,
          area: area ? area.trim() : undefined,
        }
      });
      setData(res.data || { total_installments_amount: 0, installments_count: 0, installments: [] });
      setSelectedIds([]);
    } catch (err) {
      console.error('Error fetching installments report:', err);
      setError(err.response?.data?.detail || 'حدث خطأ أثناء تحميل بيانات الأقساط');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (branchId) {
      fetchData();
    }
  }, [year, month, branchId, salespersonId, customerName, phone, area]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  const handleResetFilters = () => {
    setSalespersonId('');
    setSalespersonQuery('');
    setCustomerName('');
    setPhone('');
    setArea('');
  };

  const handlePrintSelected = () => {
    if (selectedIds.length === 0) return;
    const selectedRows = (data.installments || []).filter(inst => selectedIds.includes(inst.payment_id));
    const receiptIds = [...new Set(selectedRows.map(r => r.receipt_id).filter(Boolean))];
    if (receiptIds.length === 0) {
      toast.error('لم يتم العثور على فواتير صالحة للطباعة');
      return;
    }
    setPrintReceiptIds(receiptIds);
    setPrintModalOpen(true);
  };

  const executeChunkReceipts = async (chunk, { action, targetPrinter }) => {
    const payload = {
      receipt_ids: chunk,
      action,
      target_printer: targetPrinter || null
    };
    await api.post('/receipts/desktop_print/', payload);
  };

  // Helper for displaying sale_date in MM/YYYY format
  const formatSaleDate = (rawSaleDate) => {
    if (!rawSaleDate) return '-';
    // If format is YYYY/MM or YYYY-MM
    const parts = String(rawSaleDate).split(/[\/\-]/);
    if (parts.length >= 2) {
      if (parts[0].length === 4) {
        // YYYY/MM
        return formatMMYYYY(parts[1], parts[0]);
      } else {
        // MM/YYYY
        return formatMMYYYY(parts[0], parts[1]);
      }
    }
    return rawSaleDate;
  };

  // Helper for displaying due date in MM/YYYY format
  const formatDueDate = (rawDate) => {
    if (!rawDate) return '-';
    try {
      const d = new Date(rawDate);
      if (!isNaN(d.getTime())) {
        return formatMMYYYY(d.getMonth() + 1, d.getFullYear());
      }
    } catch (e) {
      // fallback
    }
    return rawDate;
  };

  const columns = [
    { 
      key: 'receipt_num', 
      label: 'رقم الفاتورة', 
      align: 'center', 
      className: 'text-nowrap fw-bold', 
      render: (row) => (
        <a 
          href="#" 
          onClick={(e) => { 
            e.preventDefault(); 
            navigate(`/pos?edit=${row.receipt_id}`); 
          }} 
          className="drilldown-link text-decoration-none fw-bold text-primary" 
          dir="ltr"
          title="فتح وتعديل الفاتورة في نقطة البيع"
        >
          {row.receipt_num}
        </a>
      )
    },
    { 
      key: 'area', 
      label: 'المنطقة', 
      align: 'center', 
      className: 'text-nowrap', 
      render: (row) => row.area || '-' 
    },
    { 
      key: 'customer_name', 
      label: 'اسم العميل', 
      align: 'start', 
      className: 'fw-bold text-primary px-2',
      render: (row) => row.customer_name || 'بدون اسم'
    },
    { 
      key: 'phone', 
      label: 'رقم الموبايل', 
      align: 'center', 
      className: 'text-muted text-nowrap', 
      dir: 'ltr', 
      render: (row) => row.phone || '-' 
    },
    { 
      key: 'amount', 
      label: 'مبلغ القسط', 
      align: 'center', 
      className: 'fw-bold text-success text-nowrap fs-5', 
      render: (row) => fmtNum(row.amount || 0)
    },
    { 
      key: 'salesperson_name', 
      label: 'المندوب', 
      align: 'center', 
      className: 'fw-semibold text-nowrap',
      render: (row) => row.salesperson_name || 'بدون مندوب'
    },
    { 
      key: 'sale_date', 
      label: 'تاريخ البيع', 
      align: 'center', 
      className: 'text-nowrap', 
      dir: 'ltr', 
      render: (row) => formatSaleDate(row.sale_date) 
    }
  ];

  const summaryCards = [
    {
      label: 'تاريخ الدفع',
      value: formatMMYYYY(month, year),
      color: 'info',
      icon: IconCalendarEvent
    },
    { 
      label: 'عدد الأقساط', 
      value: data.installments_count || (data.installments || []).length, 
      color: 'dark', 
      icon: IconReceipt 
    },
    { 
      label: 'إجمالي التحصيل', 
      value: fmtNum(data.total_installments_amount || 0), 
      color: 'success',
      icon: IconReceipt
    }
  ];

  const sortableColumns = [
    { id: 'receipt_num', label: 'رقم الفاتورة' },
    { id: 'area', label: 'المنطقة' },
    { id: 'customer_name', label: 'اسم العميل' },
    { id: 'phone', label: 'رقم الموبايل' },
    { id: 'amount', label: 'مبلغ القسط' },
    { id: 'salesperson_name', label: 'المندوب' },
    { id: 'sale_date', label: 'تاريخ البيع' }
  ];

  const defaultSortRules = [
    { id: 1, column: 'salesperson_name', dir: 'asc' },
    { id: 2, column: 'area', dir: 'asc' },
    { id: 3, column: 'customer_name', dir: 'asc' }
  ];

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Salesperson */}
      <div style={{ width: '220px' }} className="flex-shrink-0">
        <ReportAutocomplete
          items={salespersonsList}
          value={salespersonQuery}
          onChange={(text) => {
            setSalespersonQuery(text);
            if (!text) setSalespersonId('');
          }}
          onSelect={(item) => {
            if (item) {
              setSalespersonId(String(item.id || item.local_id));
              setSalespersonQuery(item.name || '');
            } else {
              setSalespersonId('');
              setSalespersonQuery('');
            }
          }}
          placeholder="جميع المناديب..."
          displayKey="name"
          searchKeys={['name', 'local_id']}
          idKey="id"
          allowClear={true}
          className="form-control form-control-sm fw-bold border-secondary-subtle"
        />
      </div>

      {/* Customer Name */}
      <div className="flex-grow-1" style={{ minWidth: '160px' }}>
        <DebouncedInput 
          type="text" 
          className="form-control form-control-sm fw-bold border-secondary-subtle" 
          placeholder="اسم العميل..." 
          value={customerName} 
          onChange={(e) => setCustomerName(e.target.value)} 
        />
      </div>

      {/* Area Autocomplete */}
      <div style={{ width: '180px' }} className="flex-shrink-0">
        <ReportAutocomplete
          value={area}
          onChange={(val) => setArea(val)}
          onSelect={(item) => {
            const val = typeof item === 'object' ? (item.area || item.name || '') : String(item);
            setArea(val);
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
          placeholder="المنطقة..."
          className="form-control form-control-sm fw-bold border-secondary-subtle"
        />
      </div>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Phone */}
      <div style={{ width: '140px' }} className="flex-shrink-0">
        <DebouncedInput 
          type="text" 
          className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1" 
          dir="ltr"
          placeholder="الموبايل..." 
          value={phone} 
          onChange={(e) => setPhone(e.target.value)} 
        />
      </div>

      {/* Reset */}
      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1" 
        onClick={handleResetFilters} 
        disabled={loading}
        title="إعادة ضبط"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>

      {/* Print Selected Invoices */}
      {selectedIds.length > 0 && (
        <button 
          type="button"
          className="btn btn-sm btn-outline-primary fw-bold px-3 py-1 d-flex align-items-center gap-1 flex-shrink-0 border-secondary-subtle" 
          onClick={handlePrintSelected}
        >
          <IconPrinter size={15} />
          <span>طباعة جداول المحدد ({selectedIds.length})</span>
        </button>
      )}
    </div>
  );

  return (
    <div className="w-100 p-0">
      {error && <div className="alert alert-danger mb-2 py-1">{error}</div>}
      
      <ReportTable
        reportTitle="تقرير تحصيلات الأقساط"
        periodLabel={year && month ? `${year}/${String(month).padStart(2, '0')}` : undefined}
        columns={columns}
        data={data.installments || []}
        loading={loading}
        sortableColumns={sortableColumns}
        defaultSortRules={defaultSortRules}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        checkboxSelection={true}
        idField="payment_id"
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        emptyMessage="لا توجد تحصيلات أقساط مطابقة للمعايير المحددة"
        emptyIcon={IconReceipt}
      />

      <PrintModal
        isOpen={printModalOpen}
        onClose={() => setPrintModalOpen(false)}
        title="طباعة جداول الأقساط"
        items={printReceiptIds}
        itemLabel="جدول قسط"
        executeChunk={executeChunkReceipts}
      />
    </div>
  );
}
