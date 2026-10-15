import React, { useState, useEffect, useContext, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { IconFilter, IconReceipt, IconPrinter, IconSearch, IconRefresh, IconCalendarEvent } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum, toEnglish, formatMMYYYY } from '../../utils/formatUtils';

export default function InstallmentsReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [salespersonId, setSalespersonId] = useState('');
  const [salespersonQuery, setSalespersonQuery] = useState('');
  const [salespersonsList, setSalespersonsList] = useState([]);
  
  const [saleFromYear, setSaleFromYear] = useState('');
  const [saleFromMonth, setSaleFromMonth] = useState('');
  const [saleToYear, setSaleToYear] = useState('');
  const [saleToMonth, setSaleToMonth] = useState('');
  
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [area, setArea] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState({ total_installments_amount: 0, installments_count: 0, installments: [] });

  const [selectedIds, setSelectedIds] = useState([]);

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
      const cleanFromMonth = toEnglish(saleFromMonth).trim();
      const cleanFromYear = toEnglish(saleFromYear).trim();
      const cleanToMonth = toEnglish(saleToMonth).trim();
      const cleanToYear = toEnglish(saleToYear).trim();

      const res = await api.get('/reports/installments/', {
        params: {
          branch_id: branchId,
          year: year || undefined,
          month: month || undefined,
          salesperson_id: salespersonId || undefined,
          sale_from_year: cleanFromYear || undefined,
          sale_from_month: cleanFromMonth || undefined,
          sale_to_year: cleanToYear || undefined,
          sale_to_month: cleanToMonth || undefined,
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
    if (year && month && branchId) {
      fetchData();
    }
  }, [year, month, branchId, salespersonId, saleFromMonth, saleFromYear, saleToMonth, saleToYear, customerName, phone, area]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  const handleResetFilters = () => {
    setSalespersonId('');
    setSalespersonQuery('');
    setSaleFromYear('');
    setSaleFromMonth('');
    setSaleToYear('');
    setSaleToMonth('');
    setCustomerName('');
    setPhone('');
    setArea('');
  };

  const handlePrintSelected = () => {
    if (selectedIds.length === 0) return;
    alert(`سيتم طباعة إيصالات الأقساط المحددة (${selectedIds.length})`);
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

  const renderFiltersGrid = () => (
    <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
      <div className="card-body p-3">
        <form onSubmit={handleSearchSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            {/* ── Row 1 ── */}
            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المندوب</span>
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
                  placeholder="جميع المناديب"
                  displayKey="name"
                  searchKeys={['name', 'local_id']}
                  idKey="id"
                  allowClear={true}
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">بيع من</span>
                <DebouncedInput 
                  type="number"
                  min="1" max="12"
                  className="form-control fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
                  placeholder="شهر" 
                  value={saleFromMonth} 
                  onChange={(e) => setSaleFromMonth(toEnglish(e.target.value))} 
                />
                <span className="input-group-text bg-light text-muted px-1">/</span>
                <DebouncedInput 
                  type="number"
                  min="2000" max="2100"
                  className="form-control fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
                  placeholder="سنة" 
                  value={saleFromYear} 
                  onChange={(e) => setSaleFromYear(toEnglish(e.target.value))} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
                <DebouncedInput 
                  type="number"
                  min="1" max="12"
                  className="form-control fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
                  placeholder="شهر" 
                  value={saleToMonth} 
                  onChange={(e) => setSaleToMonth(toEnglish(e.target.value))} 
                />
                <span className="input-group-text bg-light text-muted px-1">/</span>
                <DebouncedInput 
                  type="number"
                  min="2000" max="2100"
                  className="form-control fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
                  placeholder="سنة" 
                  value={saleToYear} 
                  onChange={(e) => setSaleToYear(toEnglish(e.target.value))} 
                />
              </div>
            </div>
            
            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2" style={{ width: '70px' }}>الموبايل</span>
                <DebouncedInput 
                  type="text" 
                  className="form-control fw-bold border-secondary-subtle text-center" 
                  dir="ltr"
                  placeholder="رقم الموبايل" 
                  value={phone} 
                  onChange={(e) => setPhone(e.target.value)} 
                />
              </div>
            </div>
            
            {/* ── Row 2 ── */}
            <div style={{ gridColumn: 'span 4' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
                <DebouncedInput 
                  type="text" 
                  className="form-control fw-bold border-secondary-subtle" 
                  placeholder="اسم العميل" 
                  value={customerName} 
                  onChange={(e) => setCustomerName(e.target.value)} 
                />
              </div>
            </div>
            
            <div style={{ gridColumn: 'span 4' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المنطقة</span>
                <DebouncedInput 
                  type="text" 
                  className="form-control fw-bold border-secondary-subtle" 
                  placeholder="المنطقة" 
                  value={area} 
                  onChange={(e) => setArea(e.target.value)} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
              <button 
                type="button" 
                className="btn btn-outline-secondary w-100 fw-bold fs-4 py-1" 
                onClick={() => { handleResetFilters(); }} 
                title="إعادة ضبط الفلاتر"
                style={{ border: '1px solid #adb5bd' }}
              >
                <IconRefresh size={16} className="me-1" />
                إعادة ضبط
              </button>
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
        data={data.installments || []}
        loading={loading}
        sortableColumns={sortableColumns}
        defaultSortRules={defaultSortRules}
        summaryCards={summaryCards}
        checkboxSelection={true}
        idField="payment_id"
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        headerToolbarExtra={
          selectedIds.length > 0 && (
            <button 
              className="btn btn-sm btn-outline-primary fw-bold px-3 py-1 d-flex align-items-center gap-1" 
              onClick={handlePrintSelected}
            >
              <IconPrinter size={16} /> طباعة المحدد ({selectedIds.length})
            </button>
          )
        }
        emptyMessage="لا توجد تحصيلات أقساط مطابقة للمعايير المحددة"
        emptyIcon={IconReceipt}
      />
    </div>
  );
}
