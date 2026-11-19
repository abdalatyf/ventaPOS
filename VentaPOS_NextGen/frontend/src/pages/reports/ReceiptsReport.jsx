import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { IconFilter, IconReceipt, IconRefresh } from '@tabler/icons-react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import ReportTable from '../../components/ReportTable';
import ReportAutocomplete from '../../components/ReportAutocomplete';
import DebouncedInput from '../../components/DebouncedInput';
import { fmtNum, toEnglish, formatMMYYYY } from '../../utils/formatUtils';

export default function ReceiptsReport() {
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [salespersons, setSalespersons] = useState([]);
  const [salespersonQuery, setSalespersonQuery] = useState('');
  
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  
  const [totalInvoicesCount, setTotalInvoicesCount] = useState(0);
  const [totalAmountSum, setTotalAmountSum] = useState(0);
  const [totalCashSum, setTotalCashSum] = useState(0);
  const [totalDownPaymentSum, setTotalDownPaymentSum] = useState(0);
  
  const [hasMoreUrl, setHasMoreUrl] = useState(null);

  const initialFilters = {
    sale_type: 'ALL',
    salesperson_id: '', 
    customer_name: '', 
    phone: '',
    area: '', 
    receipt_from: '', 
    receipt_to: ''
  };

  const [filters, setFilters] = useState(initialFilters);

  useEffect(() => {
    const fetchSalespersons = async () => {
      try {
        const res = await api.get('/salespersons/', { params: { branch_id: branchId } });
        setSalespersons(res.data.results || res.data || []);
      } catch (error) {
        console.error('Error fetching salespersons:', error);
      }
    };
    if (branchId) fetchSalespersons();
  }, [branchId]);

  useEffect(() => {
    let newSaleType = 'ALL';
    if (searchParams.get('is_cash_sale') === 'true') {
      newSaleType = 'CASH';
    } else if (searchParams.get('has_down_payment') === 'true') {
      newSaleType = 'HAS_DOWN_PAYMENT';
    } else if (searchParams.get('sale_type')) {
      newSaleType = searchParams.get('sale_type');
    }
    
    const spId = searchParams.get('salesperson_id') || '';
    const updatedFilters = { ...initialFilters, sale_type: newSaleType, salesperson_id: spId };
    setFilters(updatedFilters);
    fetchReceipts(updatedFilters);
  }, [year, month, branchId, searchParams]);

  useEffect(() => {
    if (filters.salesperson_id && salespersons.length > 0) {
      const found = salespersons.find(s => String(s.id) === String(filters.salesperson_id) || String(s.local_id) === String(filters.salesperson_id));
      if (found) setSalespersonQuery(found.name);
    } else if (!filters.salesperson_id) {
      setSalespersonQuery('');
    }
  }, [filters.salesperson_id, salespersons]);

  const getSalespersonName = useCallback((sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || sp.username || 'غير محدد';
    const found = salespersons.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `مندوب #${sp}`;
  }, [salespersons]);

  const fetchReceipts = async (currentFilters) => {
    if (!branchId) return;
    setLoading(true);
    setReceipts([]);
    try {
      const params = new URLSearchParams();
      params.append('branch_id', branchId);
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      
      if (currentFilters.salesperson_id) params.append('salesperson_id', currentFilters.salesperson_id);
      if (currentFilters.customer_name) params.append('customer_name', currentFilters.customer_name.trim());
      if (currentFilters.phone) params.append('phone_number', toEnglish(currentFilters.phone).trim());
      if (currentFilters.area) params.append('area', currentFilters.area.trim());
      if (currentFilters.receipt_from) params.append('receipt_from', toEnglish(currentFilters.receipt_from).trim());
      if (currentFilters.receipt_to) params.append('receipt_to', toEnglish(currentFilters.receipt_to).trim());
      
      if (currentFilters.sale_type === 'CASH') params.append('is_cash_sale', 'true');
      else if (currentFilters.sale_type === 'INSTALLMENT') params.append('is_cash_sale', 'false');
      else if (currentFilters.sale_type === 'HAS_DOWN_PAYMENT') params.append('has_down_payment', 'true');

      const res = await api.get(`/receipts/?${params.toString()}`);
      if (res.data) {
        const results = res.data.results || [];
        setReceipts(results);
        setHasMoreUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || results.length);
        
        const sumTotal = results.reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        const sumDown = results.reduce((acc, curr) => acc + (Number(curr.down_payment) || 0), 0);
        const sumCash = results.filter(r => r.is_cash_sale).reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        
        setTotalAmountSum(res.data.aggregate?.total_sales ?? res.data.total_amount_sum ?? sumTotal);
        setTotalCashSum(res.data.aggregate?.total_cash ?? sumCash);
        setTotalDownPaymentSum(res.data.aggregate?.total_down_payments ?? sumDown);
      }
    } catch (error) {
      console.error('Error fetching receipts:', error);
      toast.error('حدث خطأ أثناء تحميل تقرير الفواتير');
    } finally {
      setLoading(false);
    }
  };

  const loadMoreReceipts = async () => {
    if (!hasMoreUrl || loadingMore) return;
    setLoadingMore(true);
    try {
      const res = await api.get(hasMoreUrl);
      if (res.data && res.data.results) {
        const newResults = res.data.results;
        setReceipts(prev => [...prev, ...newResults]);
        setHasMoreUrl(res.data.next);
      }
    } catch (error) {
      console.error('Error loading more receipts:', error);
      toast.error('تعذر تحميل المزيد من الفواتير');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      fetchReceipts(newFilters);
      return newFilters;
    });
  };

  const tableContainerRef = useRef(null);
  const observer = useRef();
  const lastRowElementRef = useCallback(node => {
    if (loadingMore) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMoreUrl) {
        loadMoreReceipts();
      }
    }, {
      root: tableContainerRef.current || null,
      rootMargin: '100px'
    });
    if (node) observer.current.observe(node);
  }, [loadingMore, hasMoreUrl]);

  const columns = [
    { key: 'receipt_number', label: 'رقم الفاتورة', align: 'center', className: 'fw-bold' },
    { key: 'salesperson', label: 'المندوب', align: 'center', className: 'fw-bold text-nowrap' },
    { key: 'customer_name', label: 'العميل', align: 'start', className: 'px-2' },
    { key: 'phone', label: 'رقم الموبايل', align: 'center', className: 'text-nowrap', style: { minWidth: '130px' }, dir: 'ltr' },
    { key: 'area', label: 'المنطقة', align: 'center', className: 'text-nowrap', style: { minWidth: '130px' } },
    { key: 'down_payment', label: 'المقدم', align: 'center', className: 'text-nowrap' },
    { key: 'total_amount', label: 'الإجمالي', align: 'center', className: 'fw-bold text-primary text-nowrap fs-5' }
  ];

  const summaryCards = [
    { label: 'التاريخ', value: formatMMYYYY(month, year), color: 'primary' },
    { label: 'عدد الفواتير', value: fmtNum(totalInvoicesCount), color: 'primary', icon: IconReceipt },
    { label: 'إجمالي الكاش', value: fmtNum(totalCashSum), color: 'success' },
    { label: 'إجمالي المقدمات', value: fmtNum(totalDownPaymentSum), color: 'success' },
    { label: 'إجمالي المبيعات', value: fmtNum(totalAmountSum), color: 'primary' }
  ];

  const renderRow = ({ item: r, index }) => {
    const isCash = r.is_cash_sale;
    let custName = r.customer_name;
    let phone = r.phone_number;
    let area = r.area;
    if (!custName && r.items && r.items.length > 0) {
      custName = r.items[0].customer_name;
      phone = r.items[0].phone_number;
      area = r.items[0].area;
    }
    const salespersonName = getSalespersonName(r.salesperson);

    return (
      <tr key={r.id} ref={index === receipts.length - 1 ? lastRowElementRef : null}>
        <td className="text-center align-middle border-secondary-subtle">
          <a 
            href="#" 
            onClick={(e) => { 
              e.preventDefault(); 
              navigate(`/pos?edit=${r.id}`); 
            }} 
            className="drilldown-link text-decoration-none fw-bold text-primary" 
            dir="ltr"
          >
            {r.receipt_number || r.local_id}
          </a>
        </td>
        <td className="text-center align-middle border-secondary-subtle fw-bold text-nowrap">
          {salespersonName}
        </td>
        <td className="text-start px-2 align-middle border-secondary-subtle">
          {custName || 'بدون اسم'}
        </td>
        <td className="text-center align-middle border-secondary-subtle text-nowrap" style={{ minWidth: '130px' }} dir="ltr">
          {phone || '-'}
        </td>
        <td className="text-center align-middle border-secondary-subtle text-nowrap" style={{ minWidth: '130px' }}>
          {area || '-'}
        </td>
        <td className="text-center align-middle border-secondary-subtle text-nowrap">
          {isCash ? '-' : fmtNum(r.down_payment || 0)}
        </td>
        <td className="text-center align-middle border-secondary-subtle fw-bold text-primary text-nowrap fs-5">
          {fmtNum(r.total_amount || 0)}
        </td>
      </tr>
    );
  };

  const handleReceiptBoundBlur = (field) => {
    const rawFrom = String(filters.receipt_from ?? '').trim();
    const rawTo = String(filters.receipt_to ?? '').trim();
    let numFrom = rawFrom ? parseInt(rawFrom, 10) : null;
    let numTo = rawTo ? parseInt(rawTo, 10) : null;
    if (numFrom !== null && (isNaN(numFrom) || numFrom < 1)) numFrom = 1;
    if (numTo !== null && (isNaN(numTo) || numTo < 1)) numTo = 1;
    if (numFrom !== null && numTo !== null && numFrom > numTo) {
      if (field === 'receipt_from') numFrom = numTo;
      else numTo = numFrom;
    }
    const nextFrom = numFrom !== null ? String(numFrom) : '';
    const nextTo = numTo !== null ? String(numTo) : '';
    if (nextFrom !== rawFrom || nextTo !== rawTo) {
      setFilters(prev => {
        const nextFilters = { ...prev, receipt_from: nextFrom, receipt_to: nextTo };
        fetchReceipts(nextFilters);
        return nextFilters;
      });
    }
  };

  const subFiltersRow1 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Sale Type */}
      <div style={{ width: '165px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
          <select 
            name="sale_type" 
            className="form-select form-select-sm fw-bold border-secondary-subtle px-1 text-center" 
            value={filters.sale_type} 
            onChange={(e) => {
              const val = e.target.value;
              setFilters(prev => {
                const newFilters = { ...prev, sale_type: val };
                fetchReceipts(newFilters);
                return newFilters;
              });
            }}
          >
            <option value="ALL">جميع الأنواع</option>
            <option value="CASH">كاش فقط</option>
            <option value="INSTALLMENT">قسط فقط</option>
            <option value="HAS_DOWN_PAYMENT">بمقدم فقط</option>
          </select>
        </div>
      </div>

      {/* From Receipt */}
      <div style={{ width: '125px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من رقم</span>
          <DebouncedInput 
            type="number" 
            min={1}
            inputMode="numeric"
            dir="ltr"
            name="receipt_from" 
            className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
            placeholder="الكل"
            value={filters.receipt_from} 
            onChange={handleFilterChange} 
            onBlur={() => handleReceiptBoundBlur('receipt_from')}
          />
        </div>
      </div>

      {/* To Receipt */}
      <div style={{ width: '125px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى رقم</span>
          <DebouncedInput 
            type="number" 
            min={1}
            inputMode="numeric"
            dir="ltr"
            name="receipt_to" 
            className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1 hide-arrows" 
            placeholder="الكل"
            value={filters.receipt_to} 
            onChange={handleFilterChange} 
            onBlur={() => handleReceiptBoundBlur('receipt_to')}
          />
        </div>
      </div>

      {/* Salesperson */}
      <div className="flex-grow-1" style={{ minWidth: '200px' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المندوب</span>
          <ReportAutocomplete
            items={salespersons}
            value={salespersonQuery}
            onChange={(text) => {
              setSalespersonQuery(text);
              if (!text) {
                setFilters(prev => {
                  const newFilters = { ...prev, salesperson_id: '' };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
              }
            }}
            onSelect={(item) => {
              if (item) {
                setFilters(prev => {
                  const newFilters = { ...prev, salesperson_id: String(item.id || item.local_id) };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
                setSalespersonQuery(item.name || '');
              } else {
                setFilters(prev => {
                  const newFilters = { ...prev, salesperson_id: '' };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
                setSalespersonQuery('');
              }
            }}
            placeholder="جميع المناديب..."
            displayKey="name"
            searchKeys={['name', 'username', 'local_id']}
            idKey="id"
            allowClear={true}
            className="form-control form-control-sm fw-bold border-secondary-subtle"
          />
        </div>
      </div>
    </div>
  );

  const subFiltersRow2 = () => (
    <div className="d-flex align-items-center gap-2 flex-grow-1 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Customer Name */}
      <div className="flex-grow-1" style={{ minWidth: '170px' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العميل</span>
          <DebouncedInput 
            type="text" 
            name="customer_name" 
            className="form-control form-control-sm fw-bold border-secondary-subtle" 
            placeholder="اسم العميل..."
            value={filters.customer_name} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Phone (equal width to Area) */}
      <div style={{ width: '190px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الموبايل</span>
          <DebouncedInput 
            type="text" 
            name="phone" 
            className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1" 
            dir="ltr"
            placeholder="الموبايل..."
            value={filters.phone} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Area Autocomplete (equal width to Phone) */}
      <div style={{ width: '190px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المنطقة</span>
          <ReportAutocomplete
            value={filters.area || ''}
            onChange={(val) => {
              setFilters(prev => {
                const newFilters = { ...prev, area: val };
                fetchReceipts(newFilters);
                return newFilters;
              });
            }}
            onSelect={(item) => {
              if (!item) {
                setFilters(prev => {
                  const newFilters = { ...prev, area: '' };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
                return;
              }
              const val = typeof item === 'object' ? (item.area || item.name || '') : String(item);
              setFilters(prev => {
                const newFilters = { ...prev, area: val };
                fetchReceipts(newFilters);
                return newFilters;
              });
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
            className="form-control form-control-sm fw-bold border-secondary-subtle px-1"
          />
        </div>
      </div>

      {/* Reset */}
      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle d-flex align-items-center gap-1" 
        onClick={() => { 
          setFilters(initialFilters); 
          setSalespersonQuery(''); 
          fetchReceipts(initialFilters); 
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
        reportTitle="تقرير فواتير المبيعات"
        periodLabel={year && month ? formatMMYYYY(month, year) : undefined}
        onContainerRef={(node) => { tableContainerRef.current = node; }}
        columns={columns}
        data={receipts}
        loading={loading && receipts.length === 0}
        loadingMore={loadingMore}
        summaryCards={summaryCards}
        subFiltersRow1={subFiltersRow1}
        subFiltersRow2={subFiltersRow2}
        renderRow={renderRow}
        emptyMessage="لا توجد فواتير لهذه المعايير"
        emptyIcon={IconReceipt}
      />
    </div>
  );
}
