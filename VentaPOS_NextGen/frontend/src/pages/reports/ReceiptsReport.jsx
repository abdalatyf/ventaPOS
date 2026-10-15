import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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

  const observer = useRef();
  const lastRowElementRef = useCallback(node => {
    if (loadingMore) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMoreUrl) {
        loadMoreReceipts();
      }
    });
    if (node) observer.current.observe(node);
  }, [loadingMore, hasMoreUrl]);

  const columns = [
    { key: 'receipt_number', label: 'رقم الفاتورة', align: 'center', className: 'fw-bold' },
    { key: 'salesperson', label: 'المندوب', align: 'center', className: 'fw-bold text-nowrap' },
    { key: 'customer_name', label: 'العميل', align: 'start', className: 'px-2' },
    { key: 'phone', label: 'رقم الموبايل', align: 'center', className: 'text-nowrap', dir: 'ltr' },
    { key: 'area', label: 'المنطقة', align: 'center', className: 'text-nowrap' },
    { key: 'down_payment', label: 'المقدم', align: 'center', className: 'text-nowrap' },
    { key: 'total_amount', label: 'الإجمالي', align: 'center', className: 'fw-bold text-primary text-nowrap fs-5' }
  ];

  const summaryCards = [
    { label: 'التاريخ', value: formatMMYYYY(month, year), color: 'secondary' },
    { label: 'عدد الفواتير', value: totalInvoicesCount, color: 'dark', icon: IconReceipt },
    { label: 'إجمالي الكاش', value: fmtNum(totalCashSum), color: 'success' },
    { label: 'إجمالي المقدمات', value: fmtNum(totalDownPaymentSum), color: 'info' },
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
    let dateStr = '';
    try {
      const dateObj = new Date(r.created_at || r.date);
      if (!isNaN(dateObj.getTime())) {
        dateStr = `${String(dateObj.getDate()).padStart(2, '0')}/${String(dateObj.getMonth() + 1).padStart(2, '0')}/${dateObj.getFullYear()}`;
      }
    } catch (e) {
      dateStr = r.created_at || r.date || '';
    }

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
        <td className="text-center align-middle border-secondary-subtle text-nowrap" dir="ltr">
          {phone || '-'}
        </td>
        <td className="text-center align-middle border-secondary-subtle text-nowrap">
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

  const renderFiltersGrid = () => (
    <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
      <div className="card-body p-3">
        <form onSubmit={(e) => { e.preventDefault(); fetchReceipts(filters); }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            {/* ── Row 1 ── */}
            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
                <select 
                  name="sale_type" 
                  className="form-select fw-bold border-secondary-subtle px-1 text-center" 
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
                  <option value="ALL">الكل</option>
                  <option value="CASH">كاش فقط</option>
                  <option value="INSTALLMENT">قسط فقط</option>
                  <option value="HAS_DOWN_PAYMENT">بمقدم فقط</option>
                </select>
              </div>
            </div>

            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المندوب</span>
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
                  placeholder="جميع المناديب"
                  displayKey="name"
                  searchKeys={['name', 'username', 'local_id']}
                  idKey="id"
                  allowClear={true}
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من فتورة</span>
                <DebouncedInput 
                  type="text" 
                  inputMode="numeric"
                  name="receipt_from" 
                  className="form-control fw-bold border-secondary-subtle text-center px-1" 
                  value={filters.receipt_from} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
                <DebouncedInput 
                  type="text" 
                  inputMode="numeric"
                  name="receipt_to" 
                  className="form-control fw-bold border-secondary-subtle text-center px-1" 
                  value={filters.receipt_to} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2" style={{ width: '70px' }}>الموبايل</span>
                <DebouncedInput 
                  type="text" 
                  name="phone" 
                  className="form-control fw-bold border-secondary-subtle text-center" 
                  dir="ltr"
                  value={filters.phone} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            {/* ── Row 2 ── */}
            <div style={{ gridColumn: 'span 4' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
                <DebouncedInput 
                  type="text" 
                  name="customer_name" 
                  className="form-control fw-bold border-secondary-subtle" 
                  value={filters.customer_name} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 4' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2" style={{ width: '70px' }}>المنطقة</span>
                <DebouncedInput 
                  type="text" 
                  name="area" 
                  className="form-control fw-bold border-secondary-subtle" 
                  value={filters.area} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
              <button type="button" className="btn btn-outline-secondary w-100 fw-bold fs-4 py-1" onClick={() => { 
                  setFilters(initialFilters); 
                  setSalespersonQuery(''); 
                  fetchReceipts(initialFilters); 
                }} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
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
      {renderFiltersGrid()}
      <ReportTable
        columns={columns}
        data={receipts}
        loading={loading && receipts.length === 0}
        summaryCards={summaryCards}
        renderRow={renderRow}
        emptyMessage="لا توجد فواتير لهذه المعايير"
        emptyIcon={IconReceipt}
      />
      {loadingMore && (
        <div className="text-center py-3">
          <div className="spinner-border spinner-border-sm text-primary" role="status"></div>
        </div>
      )}
    </div>
  );
}
