import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { IconSearch, IconRefresh, IconReceipt } from '@tabler/icons-react';

const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const toArabic = (str) => {
  if (str === null || str === undefined) return '';
  return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
};

// --- Receipt Row Component ---
const ReceiptRow = React.memo(React.forwardRef(({ r, index, getSalespersonName, navigate }, ref) => {
  const rNum = r.receipt_number || r.local_id || r.id;
  const isCash = r.is_cash_sale !== false && r.sale_type !== 'INSTALLMENT';
  const phone = r.phone_number || r.customer_phone || r.phone || '—';
  const area = r.area || r.customer_area || '—';
  const custName = r.customer_name || 'عميل نقدي';
  const salespersonName = getSalespersonName(r.salesperson);

  const handleRowClick = () => {
    navigate(`/pos?edit=${r.id}`);
  };

  return (
    <tr ref={ref}>
      <td className="text-center align-middle border-secondary-subtle fw-bold">
        <a href="#" onClick={(e) => { e.preventDefault(); handleRowClick(); }} className="text-decoration-none text-primary" dir="ltr">
          {toArabic(rNum)}
        </a>
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {(() => {
          const d = new Date(r.created_at || r.date);
          return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
        })()}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {salespersonName}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle">
        {custName}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">{toArabic(phone)}</td>
      <td className="text-center align-middle border-secondary-subtle">
        {area}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {isCash ? '—' : toArabic(fmtNum(r.down_payment))}
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold text-primary">
        {toArabic(fmtNum(r.total_amount))}
      </td>
    </tr>
  );
}), (prevProps, nextProps) => prevProps.r === nextProps.r);

export default function ReceiptsReport() {
  const { setTableRef } = useSmartScroll();
  const { year, month, branchId } = useContext(ReportsContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [salespersons, setSalespersons] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  
  const [totalInvoicesCount, setTotalInvoicesCount] = useState(0);
  const [totalAmountSum, setTotalAmountSum] = useState(0);
  const [totalCashSum, setTotalCashSum] = useState(0);
  const [totalDownPaymentSum, setTotalDownPaymentSum] = useState(0);

  const [hasMoreUrl, setHasMoreUrl] = useState(null);
  const tableContainerRef = useRef(null);

  const initialFilters = {
    sale_type: 'ALL', // ALL, CASH, INSTALLMENT, HAS_DOWN_PAYMENT
    salesperson_id: '', 
    customer_name: '', 
    phone: '',
    area: '', 
    receipt_from: '', 
    receipt_to: ''
  };

  const [filters, setFilters] = useState(initialFilters);

  useEffect(() => {
    fetchSalespersons();
  }, []);

  // Sync URL params to filters and fetch automatically when navigating from Dashboard
  useEffect(() => {
    let newSaleType = 'ALL';
    if (searchParams.get('is_cash_sale') === 'true') {
      newSaleType = 'CASH';
    } else if (searchParams.get('has_down_payment') === 'true') {
      newSaleType = 'HAS_DOWN_PAYMENT';
    } else if (searchParams.get('sale_type')) {
      newSaleType = searchParams.get('sale_type');
    }
    
    const updatedFilters = { ...initialFilters, sale_type: newSaleType };
    setFilters(updatedFilters);
    fetchReceipts(updatedFilters);
  }, [year, month, branchId, searchParams]);

  const fetchSalespersons = async () => {
    try {
      const res = await api.get('/salespersons/');
      if (res.data && res.data.results) {
        setSalespersons(res.data.results);
      } else if (Array.isArray(res.data)) {
        setSalespersons(res.data);
      }
    } catch (error) {
      console.error('Error fetching salespersons:', error);
    }
  };

  const getSalespersonName = useCallback((sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || sp.username || 'غير محدد';
    const found = salespersons.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `بائع #${sp}`;
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
      if (currentFilters.customer_name) params.append('customer_name', currentFilters.customer_name);
      if (currentFilters.phone) params.append('phone_number', currentFilters.phone);
      if (currentFilters.area) params.append('area', currentFilters.area);
      if (currentFilters.receipt_from) params.append('receipt_from', currentFilters.receipt_from);
      if (currentFilters.receipt_to) params.append('receipt_to', currentFilters.receipt_to);
      
      if (currentFilters.sale_type === 'CASH') {
        params.append('is_cash_sale', 'true');
      } else if (currentFilters.sale_type === 'INSTALLMENT') {
        params.append('is_cash_sale', 'false');
      } else if (currentFilters.sale_type === 'HAS_DOWN_PAYMENT') {
        params.append('has_down_payment', 'true');
      }

      const res = await api.get(`/receipts/?${params.toString()}`);
      if (res.data && res.data.results) {
        const results = res.data.results;
        setReceipts(results);
        setHasMoreUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || 0);
        
        let allReceiptsForTotals = results;
        
        const sumTotal = results.reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        const sumDown = results.reduce((acc, curr) => acc + (Number(curr.down_payment) || 0), 0);
        const sumCash = results.filter(r => r.is_cash_sale).reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        
        setTotalAmountSum(res.data.aggregate?.total_sales || sumTotal);
        setTotalCashSum(res.data.aggregate?.total_cash || sumCash);
        setTotalDownPaymentSum(res.data.aggregate?.total_down_payments || sumDown);
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
        
        // Update local sums
        const sumTotal = newResults.reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        const sumDown = newResults.reduce((acc, curr) => acc + (Number(curr.down_payment) || 0), 0);
        const sumCash = newResults.filter(r => r.is_cash_sale).reduce((acc, curr) => acc + (Number(curr.total_amount) || 0), 0);
        
        setTotalAmountSum(prev => prev + sumTotal);
        setTotalCashSum(prev => prev + sumCash);
        setTotalDownPaymentSum(prev => prev + sumDown);
      }
    } catch (error) {
      console.error('Error loading more receipts:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    const enVal = String(value).replace(/[٠١٢٣٤٥٦٧٨٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
    setFilters(prev => ({ ...prev, [name]: enVal }));
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchReceipts(filters);
  };

  const handleResetFilters = () => {
    setFilters(initialFilters);
    fetchReceipts(initialFilters);
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

  return (
    <div className="p-3 fs-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      
      {/* ── Search Filters Panel ── */}
      <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-body p-3">
          <form onSubmit={handleSearchSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
              
              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">نوع البيع</span>
                  <select className="form-select fw-bold border-secondary-subtle px-1 text-center" name="sale_type" value={filters.sale_type} onChange={handleSelectChange}>
                    <option value="ALL">الكل</option>
                    <option value="CASH">كاش</option>
                    <option value="INSTALLMENT">قسط</option>
                    <option value="HAS_DOWN_PAYMENT">فواتير بها مقدمات</option>
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المندوب</span>
                  <select className="form-select fw-bold border-secondary-subtle" name="salesperson_id" value={filters.salesperson_id} onChange={handleSelectChange}>
                    <option value="">جميع البائعين</option>
                    {salespersons.map((sp) => (
                      <option key={sp.id || sp.local_id} value={sp.id || sp.local_id}>{sp.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">رقم الفاتورة من</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle px-1 text-center" name="receipt_from" value={toArabic(filters.receipt_from)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle px-1 text-center" name="receipt_to" value={toArabic(filters.receipt_to)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle" name="customer_name" value={toArabic(filters.customer_name)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">رقم الموبايل</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="phone" value={toArabic(filters.phone)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المنطقة</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle" name="area" value={toArabic(filters.area)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
                <button type="button" className="btn btn-outline-secondary px-3 fw-bold fs-4 py-1" onClick={handleResetFilters} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                  <IconRefresh size={16} className="me-1" />
                  إعادة ضبط
                </button>
                <button type="submit" className="btn btn-primary px-4 fw-bold fs-4 py-1 border-secondary-subtle" disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                  <IconSearch size={16} className="me-1" />
                  {loading ? 'جاري...' : 'بحث'}
                </button>
              </div>

            </div>
          </form>
        </div>
      </div>

      {/* ── Results Table ── */}
      <div className="card shadow-sm" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-header sticky-toolbar bg-light d-flex flex-wrap justify-content-between align-items-center py-2 gap-2" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <div className="text-dark fw-bold fs-3 d-flex align-items-center gap-2">
              نتائج البحث
              <span className="badge bg-primary text-white rounded-pill px-2 py-1">{toArabic(totalInvoicesCount)} فاتورة</span>
            </div>
          </div>

          {receipts.length > 0 && (
            <div className="d-flex gap-3">
              {(filters.sale_type === 'ALL' || filters.sale_type === 'CASH') && (
                <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
                  إجمالي الكاش:{' '}
                  <span className="text-success fw-bolder fs-4">{toArabic(fmtNum(totalCashSum))}</span>
                </div>
              )}
              {(filters.sale_type === 'ALL' || filters.sale_type === 'INSTALLMENT' || filters.sale_type === 'HAS_DOWN_PAYMENT') && (
                <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
                  إجمالي المقدمات:{' '}
                  <span className="text-warning fw-bolder fs-4">{toArabic(fmtNum(totalDownPaymentSum))}</span>
                </div>
              )}
              <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
                الإجمالي الكلي:{' '}
                <span className="text-primary fw-bolder fs-4">{toArabic(fmtNum(totalAmountSum))}</span>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary mb-3"></div>
            <div className="text-secondary fw-bold fs-3">جاري تحميل الفواتير...</div>
          </div>
        ) : (
          <div
            ref={setTableRef}
            className="table-responsive hide-vertical-scroll" 
            style={{ 
              border: '1px solid #dee2e6',
              overflowY: 'auto',
              overflowX: 'auto'
            }}
          >
            <style>
              {`
                /* Hide vertical scrollbar but keep horizontal */
                .hide-vertical-scroll::-webkit-scrollbar { width: 0px; height: 8px; }
                .hide-vertical-scroll::-webkit-scrollbar-track { background: #f1f1f1; }
                .hide-vertical-scroll::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
                .hide-vertical-scroll::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
                .hide-vertical-scroll { scrollbar-width: thin; }
                
                /* Hybrid Sticky Header */
                .hybrid-sticky-header th {
                  position: sticky !important;
                  top: 0 !important;
                  z-index: 1010;
                  background-color: #f8f9fa !important;
                  box-shadow: inset 0 -1px 0 var(--tblr-border-color);
                }
              `}
            </style>
            <table className="table hybrid-sticky-header table-bordered table-vcenter table-hover mb-0 text-nowrap">
              <thead className="bg-light">
                <tr>
                  <th className="text-center">رقم الفاتورة</th>
                  <th className="text-center">التاريخ</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-start px-2">العميل</th>
                  <th className="text-center">رقم الموبايل</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-center">المقدم</th>
                  <th className="text-center">الإجمالي</th>
                </tr>
              </thead>
              <tbody>
                {receipts.length > 0 ? receipts.map((r, index) => {
                  if (receipts.length === index + 1) {
                    return (
                      <ReceiptRow 
                        key={r.id || r.local_id || index}
                        r={r}
                        index={index}
                        getSalespersonName={getSalespersonName}
                        navigate={navigate}
                        ref={lastRowElementRef}
                      />
                    );
                  }
                  return (
                    <ReceiptRow 
                      key={r.id || r.local_id || index}
                      r={r}
                      index={index}
                      getSalespersonName={getSalespersonName}
                      navigate={navigate}
                    />
                  );
                }) : (
                  <tr>
                    <td colSpan="8" className="text-center py-5">
                      <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
                      <h4 className="text-muted fw-bold">لا توجد فواتير مطابقة لمعايير البحث</h4>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {loadingMore && (
              <div className="text-center py-3">
                <div className="spinner-border text-primary"></div>
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  );
}
