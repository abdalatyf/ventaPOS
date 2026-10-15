import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import Swal from 'sweetalert2';
import useSmartScroll from '../hooks/useSmartScroll';
import api from '../api';
import Autocomplete from '../components/Autocomplete';
import {
  IconSearch, IconRefresh, IconPlus, IconEye, IconReceipt, IconPrinter, IconFilter,
  IconTrash, IconDotsVertical, IconPencil, IconFileText, IconCalendar, IconUser,
  IconMapPin, IconPhone, IconCheck, IconX, IconCreditCard, IconCash, IconArrowBackUp
} from '@tabler/icons-react';

const ReceiptRow = React.memo(React.forwardRef(({
  r, index, isSelected, toggleSelect, handleContextMenu, formatCurrency, getSalespersonName,
  handleEditSingle, handlePdfSingle, handlePrintSingle, handleDeleteSingle, handleReturnSingle
}, ref) => {
  const rowKey = r.id || r.local_id || index;
  const rNum = r.receipt_number || r.local_id || r.id;
  const isCash = r.is_cash_sale !== false && r.sale_type !== 'INSTALLMENT';
  const phone = r.phone_number || r.customer_phone || r.phone || '—';
  const area = r.area || r.customer_area || '—';
  const addr = r.address || r.customer_address || '—';
  const productsText = r.products_text || '—';
  const custName = r.customer_name || 'عميل نقدي';
  const salespersonName = getSalespersonName(r.salesperson);

  return (
    <tr ref={ref}>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(r.id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        <div className="dropdown">
          <button 
            className="btn btn-sm btn-icon btn-light border-secondary-subtle"
            data-bs-toggle="dropdown"
          >
            <IconDotsVertical size={16} />
          </button>
          <div className="dropdown-menu dropdown-menu-end shadow-sm">
            {r.receipt_type !== 'RETURN' && (
              <button className="dropdown-item" onClick={() => handleEditSingle(r.id, rNum)}>
                تعديل الفاتورة
              </button>
            )}
            <button className="dropdown-item" onClick={() => handlePdfSingle(r.id, rNum)}>
              عرض الفاتورة
            </button>
            {r.receipt_type !== 'RETURN' && !r.is_cash_sale && (
              <button className="dropdown-item" onClick={() => handlePrintSingle(r.id, rNum)}>
                طباعة كقسط
              </button>
            )}
            {r.receipt_type !== 'RETURN' && (
              <>
                <div className="dropdown-divider"></div>
                <button className="dropdown-item text-secondary" onClick={() => handleReturnSingle(r.id, rNum)}>
                  إنشاء مرتجع
                </button>
              </>
            )}
            <div className="dropdown-divider"></div>
            <button className="dropdown-item text-danger" onClick={() => handleDeleteSingle(r.id, rNum)}>
              حذف الفاتورة
            </button>
          </div>
        </div>
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {rNum}
        {r.has_returns && (
          <div className="badge bg-danger rounded-pill px-2 mt-1" style={{ fontSize: '0.7rem' }}>
            بها مرتجع
          </div>
        )}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="rtl">
        <span className="fw-bold text-primary">{r.sale_month}</span>
        <span className="mx-1 text-muted">/</span>
        <span className="fw-bold">{r.sale_year}</span>
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {salespersonName}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle">
        {custName}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">{phone}</td>
      <td className="text-center align-middle border-secondary-subtle">
        {area}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '150px' }} title={addr}>
        {addr}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '200px' }} title={productsText}>
        {productsText}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {isCash ? '—' : formatCurrency(r.down_payment)}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {isCash ? 'كاش' : r.installment_system}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {formatCurrency(r.total_amount)}
      </td>
    </tr>
  );
}), (prevProps, nextProps) => {
  return prevProps.isSelected === nextProps.isSelected && prevProps.r === nextProps.r;
});

export default function SearchReceipts() {
  const { setTableRef } = useSmartScroll();
  const navigate = useNavigate();
  const location = useLocation();

  const handleReturnSingle = (id) => {
    navigate(`/receipts/return/${id}`);
  };

  

  const formatCurrency = (val) => {
    if (val === undefined || val === null || val === '') return '0';
    return Math.round(Number(val)).toString();
  };

  const getSalespersonName = (sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || sp.username || 'غير محدد';
    const found = salespersons.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `بائع #${sp}`;
  };

  const MONTHS = [
    { id: 1, name: 'يناير' }, { id: 2, name: 'فبراير' }, { id: 3, name: 'مارس' },
    { id: 4, name: 'أبريل' }, { id: 5, name: 'مايو' }, { id: 6, name: 'يونيو' },
    { id: 7, name: 'يوليو' }, { id: 8, name: 'أغسطس' }, { id: 9, name: 'سبتمبر' },
    { id: 10, name: 'أكتوبر' }, { id: 11, name: 'نوفمبر' }, { id: 12, name: 'ديسمبر' }
  ];

  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const searchParams = new URLSearchParams(location.search);
  
  let saleTypeInitial = searchParams.get('sale_type') || 'ALL';
  if (searchParams.get('is_cash_sale') === 'true') saleTypeInitial = 'CASH';
  else if (searchParams.get('is_cash_sale') === 'false') saleTypeInitial = 'INSTALLMENT';

  const initialFilters = {
    receipt_number: searchParams.get('receipt_number') || '', 
    salesperson_id: searchParams.get('salesperson_id') || '', 
    customer_name: searchParams.get('customer_name') || '', 
    phone: searchParams.get('phone') || '',
    address: searchParams.get('address') || '', 
    area: searchParams.get('area') || '', 
    month: searchParams.get('month') || '', 
    year: searchParams.get('year') || '',
    sale_type: saleTypeInitial, 
    receipt_from: searchParams.get('receipt_from') || '', 
    receipt_to: searchParams.get('receipt_to') || ''
  };

  const [filters, setFilters] = useState(initialFilters);
  const [salespersonName, setSalespersonName] = useState('');
  const [receipts, setReceipts] = useState([]);
  const [salespersons, setSalespersons] = useState([]);
  const [productsMap, setProductsMap] = useState({});
  const [loading, setLoading] = useState(false);
  // Native Bootstrap Dropdown used for actions
  const [totalInvoicesCount, setTotalInvoicesCount] = useState(0);
  const [totalAmountSum, setTotalAmountSum] = useState(0);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const [selectedIds, setSelectedIds] = useState([]);
  const [globalAllIds, setGlobalAllIds] = useState([]);

  useEffect(() => {
    fetchSalespersons();
    fetchInventory();
    fetchReceipts(initialFilters);
  }, []);

  const fetchSalespersons = async () => {
    try {
      const res = await api.get('/salespersons/');
      const list = res.data?.results || res.data || [];
      if (Array.isArray(list)) {
        setSalespersons(list);
        if (initialFilters.salesperson_id) {
          const found = list.find(s => String(s.id) === String(initialFilters.salesperson_id) || String(s.local_id) === String(initialFilters.salesperson_id));
          if (found) setSalespersonName(found.name);
        }
      }
    } catch (error) {
      console.error('Error fetching salespersons:', error);
    }
  };

  const fetchSalespersonSuggestions = async (query) => {
    try {
      const res = await api.get('/salespersons/', { params: { search: query } });
      const data = res.data?.results || res.data;
      if (Array.isArray(data)) {
        return data.filter(s => !query || s.name?.toLowerCase().includes(query.toLowerCase()));
      }
      return [];
    } catch (error) {
      console.error('Error fetching salesperson suggestions:', error);
      return [];
    }
  };

  const fetchInventory = async () => {
    try {
      const res = await api.get('/inventory-items/?limit=1000');
      const data = res.data?.results || res.data;
      if (Array.isArray(data)) {
        const pMap = {};
        data.forEach(p => pMap[p.id] = p.name);
        setProductsMap(pMap);
      }
    } catch (error) {
      console.error('Error fetching inventory:', error);
    }
  };

  const fetchReceipts = async (currentFilters) => {
    setLoading(true);
    setReceipts([]);
    setSelectedIds([]);
    try {
      const params = new URLSearchParams();
      if (currentFilters.month) params.append('month', currentFilters.month);
      if (currentFilters.year) params.append('year', currentFilters.year);
      if (currentFilters.salesperson_id) params.append('salesperson', currentFilters.salesperson_id);
      if (currentFilters.customer_name) params.append('customer_name', currentFilters.customer_name);
      if (currentFilters.phone) params.append('phone', currentFilters.phone);
      if (currentFilters.address) params.append('address', currentFilters.address);
      if (currentFilters.area) params.append('area', currentFilters.area);
      if (currentFilters.sale_type && currentFilters.sale_type !== 'ALL') {
        params.append('is_cash_sale', currentFilters.sale_type === 'CASH' ? 'true' : 'false');
      }
      if (currentFilters.receipt_from) params.append('receipt_from', currentFilters.receipt_from);
      if (currentFilters.receipt_to) params.append('receipt_to', currentFilters.receipt_to);

      const res = await api.get(`/receipts/?${params.toString()}`);
      if (res.data && res.data.results) {
        setReceipts(res.data.results);
        setNextPageUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || 0);
        setTotalAmountSum(res.data.aggregate?.total_sales || 0);
        const allIds = res.data.all_ids || [];
        setGlobalAllIds(allIds);
        setSelectedIds(allIds.length > 0 ? allIds : res.data.results.map(r => r.id));
      }
    } catch (error) {
      console.error('Error fetching receipts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMoreReceipts = async () => {
    if (!nextPageUrl || loadingMore) return;
    setLoadingMore(true);
    try {
      const res = await api.get(nextPageUrl);
      if (res.data && res.data.results) {
        setReceipts(prev => [...prev, ...res.data.results]);
        setNextPageUrl(res.data.next);
      }
    } catch (error) {
      console.error('Error loading more receipts:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const filterTimeout = useRef(null);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    const enVal = String(value).replace(/[٠١٢٣٤٥٦٧٨٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
    setFilters(prev => {
      const newFilters = { ...prev, [name]: enVal };
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
      filterTimeout.current = setTimeout(() => {
        fetchReceipts(newFilters);
      }, 300);
      return newFilters;
    });
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      fetchReceipts(newFilters);
      return newFilters;
    });
  };

  const handleResetFilters = () => {
    setSalespersonName('');
    setFilters(initialFilters);
    fetchReceipts(initialFilters);
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const toggleSelectAll = () => {
    const targetLength = globalAllIds.length > 0 ? globalAllIds.length : receipts.length;
    if (selectedIds.length === targetLength) {
      setSelectedIds([]);
    } else {
      setSelectedIds(globalAllIds.length > 0 ? globalAllIds : receipts.map(r => r.id));
    }
  };

  const handlePrint = async (ids, action = "print") => {
    if (ids.length === 0) return;
    try {
      const res = await api.post('/receipts/bulk_pdf/', { receipt_ids: ids, action });
      if (res.data && res.data.pdf_url) {
        window.open(res.data.pdf_url, '_blank');
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('حدث خطأ أثناء إنشاء الـ PDF.');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    Swal.fire({
      title: 'هل أنت متأكد؟',
      text: `هل تريد حذف ${selectedIds.length} فاتورة؟`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء'
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await api.post('/receipts/bulk_delete/', { receipt_ids: selectedIds });
          fetchReceipts(filters);
        } catch (error) {
          console.error('Error deleting receipts:', error);
          alert('حدث خطأ أثناء الحذف.');
        }
      }
    });
  };

  const handleDeleteSingle = async (id, num) => {
    Swal.fire({
      title: 'هل أنت متأكد؟',
      text: `هل تريد حذف الفاتورة رقم ${num}؟`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء'
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await api.delete(`/receipts/${id}/`);
          fetchReceipts(filters);
        } catch (error) {
          console.error('Error deleting receipt:', error);
          alert('حدث خطأ أثناء الحذف.');
        }
      }
    });
  };

  const handleEditSingle = (id, num) => {
    navigate(`/pos?edit=${id}`);
  };

  const handlePdfSingle = (id, num) => {
    handlePrint([id], "view");
  };

  const handlePrintSingle = (id, num) => {
    handlePrint([id], "print");
  };

  // Context menu logic replaced by Native Bootstrap Dropdown



  const observer = useRef();
  const lastRowElementRef = useCallback(node => {
    if (loading || loadingMore) return;
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && nextPageUrl) {
        loadMoreReceipts();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [loading, loadingMore, nextPageUrl]);

  return (
    <div className="px-3 pt-3 fs-3 native-page-scroll flex-column flex-grow-1" dir="rtl" style={{ fontSize: '1.02rem' }}>
      
      {/* ── Page Header ── */}
      <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle" style={{ borderColor: '#dee2e6 !important' }}>
        <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
          <IconReceipt size={28} className="text-primary" />
          دفتر المبيعات
        </h2>
        <div className="d-flex align-items-center gap-2">
          <Link to="/pos" className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2">
            <IconPlus size={20} />
            <span>إضافة فاتورة جديدة</span>
          </Link>
        </div>
      </div>

      {/* ── Search Filters Panel ── */}
      <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-body p-3">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            {/* ── Row 1 (Sum: 10) ── */}
            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الشهر</span>
                <input 
                  type="number" 
                  className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                  name="month" 
                  min="1" 
                  max="12" 
                  placeholder="الكل"
                  value={filters.month} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">السنة</span>
                <input 
                  type="number" 
                  className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                  name="year" 
                  placeholder="الكل"
                  value={filters.year} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من</span>
                <input 
                  type="number" 
                  className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                  name="receipt_from" 
                  value={filters.receipt_from} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
                <input 
                  type="number" 
                  className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                  name="receipt_to" 
                  value={filters.receipt_to} 
                  onChange={handleFilterChange} 
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المندوب</span>
                <Autocomplete
                  value={salespersonName}
                  onChange={(val) => {
                    setSalespersonName(val);
                    if (!val) {
                      setFilters(prev => {
                        const newFilters = { ...prev, salesperson_id: '' };
                        fetchReceipts(newFilters);
                        return newFilters;
                      });
                    }
                  }}
                  onSelect={(item) => {
                    setSalespersonName(item.name);
                    setFilters(prev => {
                      const newFilters = { ...prev, salesperson_id: item.id || item.local_id };
                      fetchReceipts(newFilters);
                      return newFilters;
                    });
                  }}
                  fetchSuggestions={fetchSalespersonSuggestions}
                  placeholder="جميع البائعين"
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
                <select className="form-select fw-bold border-secondary-subtle px-1 text-center" name="sale_type" value={filters.sale_type} onChange={handleSelectChange}>
                  <option value="ALL">الكل</option>
                  <option value="CASH">كاش</option>
                  <option value="INSTALLMENT">قسط</option>
                </select>
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الهاتف</span>
                <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="phone" value={filters.phone} onChange={handleFilterChange} />
              </div>
            </div>

            {/* ── Row 2 (Sum: 10) ── */}
            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
                <input type="text" className="form-control fw-bold border-secondary-subtle" name="customer_name" value={filters.customer_name} onChange={handleFilterChange} />
              </div>
            </div>

            <div style={{ gridColumn: 'span 3' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العنوان</span>
                <input type="text" className="form-control fw-bold border-secondary-subtle" name="address" value={filters.address} onChange={handleFilterChange} />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المنطقة</span>
                <input type="text" className="form-control fw-bold border-secondary-subtle" name="area" value={filters.area} onChange={handleFilterChange} />
              </div>
            </div>

            <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
              <button type="button" className="btn btn-outline-secondary w-100 fw-bold fs-4 py-1" onClick={handleResetFilters} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                <IconRefresh size={16} className="me-1" />
                إعادة ضبط
              </button>
            </div>

          </div>
        </div>
      </div>

      {/* ── Results Table ── */}
      <div className="card shadow-sm mb-3 flex-grow-1" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-header bg-light d-flex flex-wrap justify-content-between align-items-center py-2 gap-2 sticky-toolbar" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <div className="text-dark fw-bold fs-3 d-flex align-items-center gap-2">
              نتائج البحث
              <span className="badge bg-primary text-white rounded-pill px-2 py-1">{totalInvoicesCount} فاتورة</span>
            </div>
            
            {receipts.length > 0 && (
              <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-3 ms-1">
                {selectedIds.length > 0 ? (
                  <>
                    <span className="fw-bold me-2">تم تحديد {selectedIds.length}</span>
                    <button className="btn btn-outline-success btn-sm fw-bold py-1 px-2 border-secondary-subtle" onClick={() => handlePrint(selectedIds, 'print')}>
                      <IconPrinter size={16} className="me-1" /> طباعة محددة
                    </button>
                    <button className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle" onClick={() => handlePrint(selectedIds, 'view')}>
                      <IconEye size={16} className="me-1" /> معاينة محددة
                    </button>
                    <button className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle" onClick={handleBulkDelete}>
                      <IconTrash size={16} className="me-1" /> حذف محددة
                    </button>
                  </>
                ) : (
                  <span className="text-muted small">حدد فواتير للإجراءات الجماعية</span>
                )}
              </div>
            )}
          </div>

          {receipts.length > 0 && (
            <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
              إجمالي المبيعات:{' '}
              <span className="text-success fw-bolder fs-4">{formatCurrency(totalAmountSum)}</span>
            </div>
          )}
        </div>

        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary mb-3"></div>
            <div className="text-secondary fw-bold fs-3">جاري تحميل الفواتير...</div>
          </div>
        ) : receipts.length === 0 ? (
          <div className="card-body text-center py-5">
            <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
            <h4 className="text-muted fw-bold">لا توجد فواتير مطابقة لمعايير البحث</h4>
          </div>
        ) : (
          <div 
            ref={setTableRef}
            className="table-responsive hybrid-scroll-container rounded" 
            style={{ overflowY: 'auto', overflowX: 'auto', scrollbarGutter: 'stable', border: '1px solid #dee2e6' }}
          >
            <table className="table table-bordered table-vcenter table-hover table-sticky-header mb-0 text-nowrap">
              <thead>
                <tr>
                  <th className="text-center w-1">
                    <input 
                      type="checkbox" 
                      className="form-check-input" 
                      checked={receipts.length > 0 && selectedIds.length === (globalAllIds.length > 0 ? globalAllIds.length : receipts.length)} 
                      onChange={toggleSelectAll} 
                    />
                  </th>
                  <th className="text-center w-1"></th>
                  <th className="text-center">#</th>
                  <th className="text-center">التاريخ</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-start px-2">العميل</th>
                  <th className="text-center">الهاتف</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-start px-2">العنوان</th>
                  <th className="text-start px-2">الأصناف</th>
                  <th className="text-center">المقدم</th>
                  <th className="text-center">النظام</th>
                  <th className="text-center">الإجمالي</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r, index) => {
                  const isLastRow = receipts.length === index + 1;
                  return (
                    <ReceiptRow 
                      key={r.id || r.local_id || index}
                      r={r}
                      index={index}
                      isSelected={selectedIds.includes(r.id)}
                      toggleSelect={toggleSelect}
                      
                      formatCurrency={formatCurrency}
                      getSalespersonName={getSalespersonName}
                      handlePdfSingle={handlePdfSingle}
                      handlePrintSingle={handlePrintSingle}
                      handleEditSingle={handleEditSingle}
                      handleReturnSingle={handleReturnSingle}
                      handleDeleteSingle={handleDeleteSingle}
                      ref={isLastRow ? lastRowElementRef : null}
                    />
                  );
                })}
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
