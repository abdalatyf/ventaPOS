import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import {
  IconSearch, IconRefresh, IconPlus, IconEye, IconReceipt, IconPrinter, IconFilter,
  IconTrash, IconDotsVertical, IconPencil, IconFileText, IconCalendar, IconUser,
  IconMapPin, IconPhone, IconCheck, IconX, IconCreditCard, IconCash
} from '@tabler/icons-react';

const ReceiptRow = React.memo(({
  r, index, isSelected, toggleSelect, handleContextMenu, toArabic, formatCurrency, getSalespersonName
}) => {
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
    <tr>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(r.id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        <button 
          className="btn btn-sm btn-icon btn-light border-secondary-subtle"
          onClick={(e) => handleContextMenu(e, r.id, rNum)}
        >
          <IconDotsVertical size={16} />
        </button>
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">{toArabic(rNum)}</td>
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
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '150px' }} title={addr}>
        {addr}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '200px' }} title={productsText}>
        {productsText}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {isCash ? '—' : toArabic(formatCurrency(r.down_payment))}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {isCash ? 'كاش' : toArabic(r.installment_system)}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {toArabic(formatCurrency(r.total_amount))}
      </td>
    </tr>
  );
}, (prevProps, nextProps) => {
  return prevProps.isSelected === nextProps.isSelected && prevProps.r === nextProps.r;
});

export default function SearchReceipts() {
  const navigate = useNavigate();

  const toArabic = (str) => {
    if (str === null || str === undefined) return '';
    return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
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

  const initialFilters = {
    receipt_number: '', salesperson_id: '', customer_name: '', phone: '',
    address: '', area: '', month: '', year: '',
    sale_type: 'ALL', receipt_from: '', receipt_to: ''
  };

  const [filters, setFilters] = useState(initialFilters);
  const [receipts, setReceipts] = useState([]);
  const [salespersons, setSalespersons] = useState([]);
  const [productsMap, setProductsMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(true);
  const [contextMenu, setContextMenu] = useState(null);
  
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

    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  }, []);

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
      if (currentFilters.sale_type && currentFilters.sale_type !== 'ALL') params.append('sale_type', currentFilters.sale_type);
      if (currentFilters.receipt_from) params.append('receipt_from', currentFilters.receipt_from);
      if (currentFilters.receipt_to) params.append('receipt_to', currentFilters.receipt_to);

      const res = await api.get(`/receipts/?${params.toString()}`);
      if (res.data && res.data.results) {
        setReceipts(res.data.results);
        setNextPageUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || 0);
        setTotalAmountSum(res.data.aggregate?.total_sales || 0);
        setGlobalAllIds(res.data.all_ids || []);
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
    if (!window.confirm(`هل أنت متأكد من حذف ${selectedIds.length} فاتورة؟`)) return;
    try {
      await api.post('/receipts/bulk_delete/', { receipt_ids: selectedIds });
      alert('تم الحذف بنجاح.');
      fetchReceipts(filters);
    } catch (error) {
      console.error('Error deleting receipts:', error);
      alert('حدث خطأ أثناء الحذف.');
    }
  };

  const handleDeleteSingle = async (id, num) => {
    if (!window.confirm(`هل أنت متأكد من حذف الفاتورة رقم ${num}؟`)) return;
    try {
      await api.delete(`/receipts/${id}/`);
      fetchReceipts(filters);
    } catch (error) {
      console.error('Error deleting receipt:', error);
      alert('حدث خطأ أثناء الحذف.');
    }
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

  const handleContextMenu = (e, rId, rNum) => {
    e.preventDefault();
    setContextMenu({ mouseX: e.clientX, mouseY: e.clientY, receiptId: rId, receiptNum: rNum });
  };



  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 100) {
      if (nextPageUrl && !loadingMore) {
        loadMoreReceipts();
      }
    }
  };

  const stickyThStyle = {
    position: 'sticky',
    top: 0,
    backgroundColor: '#f8f9fa',
    zIndex: 10,
    boxShadow: 'inset 0 -1px 0 #dee2e6'
  };

  return (
    <div className="px-3 pt-3 fs-3 d-flex flex-column flex-grow-1" dir="rtl" style={{ fontSize: '1.02rem', minHeight: 0 }}>
      
      {/* ── Page Header ── */}
      <div className="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary-subtle" style={{ borderColor: '#dee2e6 !important' }}>
        <h2 className="fw-bold text-dark m-0 fs-2 d-flex align-items-center gap-2">
          <IconReceipt size={28} className="text-primary" />
          دفتر المبيعات
        </h2>
        <div className="d-flex align-items-center gap-2">
          <button 
            className={`btn ${showFilters ? 'btn-secondary' : 'btn-outline-secondary'} d-flex align-items-center gap-1 fw-bold fs-4 py-2`}
            onClick={() => setShowFilters(!showFilters)}
            title="إظهار / إخفاء البحث"
          >
            <IconFilter size={20} />
            {showFilters ? 'إخفاء البحث' : 'إظهار البحث'}
          </button>
          <Link to="/pos" className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2">
            <IconPlus size={20} />
            <span>إضافة فاتورة جديدة</span>
          </Link>
        </div>
      </div>

      {/* ── Search Filters Panel ── */}
      {showFilters && (
      <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-body p-3">
          <form onSubmit={handleSearchSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
              
              {/* ── Row 1 (Sum: 7) ── */}
              <div style={{ gridColumn: 'span 1' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الشهر</span>
                  <select className="form-select fw-bold border-secondary-subtle px-1 text-center" name="month" value={filters.month} onChange={handleSelectChange}>
                    <option value="">الكل</option>
                    {MONTHS.map((m) => (
                      <option key={m.id} value={m.id}>{m.id}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 1' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">السنة</span>
                  <select className="form-select fw-bold border-secondary-subtle px-1 text-center" name="year" value={filters.year} onChange={handleSelectChange}>
                    <option value="">الكل</option>
                    {yearOptions.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 1' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle px-1 text-center" name="receipt_from" value={toArabic(filters.receipt_from)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 1' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle px-1 text-center" name="receipt_to" value={toArabic(filters.receipt_to)} onChange={handleFilterChange} />
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

              {/* Empty placeholder to complete the 8-column row so the next row breaks cleanly */}
              <div style={{ gridColumn: 'span 1' }}></div>

              {/* ── Row 2 (Sum: 8) ── */}
              <div style={{ gridColumn: 'span 3' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle" name="customer_name" value={toArabic(filters.customer_name)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 3' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العنوان</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle" name="address" value={toArabic(filters.address)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المنطقة</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle" name="area" value={toArabic(filters.area)} onChange={handleFilterChange} />
                </div>
              </div>

              {/* ── Row 3 (Sum: 8) ── */}
              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الهاتف</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="phone" value={toArabic(filters.phone)} onChange={handleFilterChange} />
                </div>
              </div>

              <div style={{ gridColumn: 'span 6' }} className="d-flex align-items-center gap-2 justify-content-end">
                <button type="button" className="btn btn-outline-secondary px-4 fw-bold fs-4 py-1" onClick={handleResetFilters} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                  <IconRefresh size={16} className="me-1" />
                  إعادة ضبط
                </button>
                <button type="submit" className="btn btn-primary px-5 fw-bold fs-4 py-1 border-secondary-subtle" disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                  <IconSearch size={16} className="me-1" />
                  {loading ? 'جاري البحث...' : 'بحث'}
                </button>
              </div>

            </div>
          </form>
        </div>
      </div>
      )}

      {/* ── Results Table ── */}
      <div className="card shadow-sm flex-grow-1 d-flex flex-column overflow-hidden" style={{ border: '1px solid #dee2e6', minHeight: 0 }}>
        <div className="card-header bg-light d-flex flex-wrap justify-content-between align-items-center py-2 gap-2" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <div className="text-dark fw-bold fs-3 d-flex align-items-center gap-2">
              نتائج البحث
              <span className="badge bg-primary text-white rounded-pill px-2 py-1">{toArabic(totalInvoicesCount)} فاتورة</span>
            </div>
            
            {receipts.length > 0 && (
              <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-3 ms-1">
                {selectedIds.length > 0 ? (
                  <>
                    <span className="fw-bold me-2">تم تحديد {toArabic(selectedIds.length)}</span>
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
              <span className="text-success fw-bolder fs-4">{toArabic(formatCurrency(totalAmountSum))}</span>
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
            className="table-responsive flex-grow-1 overflow-auto rounded" 
            style={{ border: '1px solid #dee2e6', minHeight: 0 }}
            onScroll={handleScroll}
          >
            <table className="table table-bordered table-vcenter table-hover mb-0">
              <thead className="sticky-top">
                <tr>
                  <th className="text-center w-1" style={stickyThStyle}>
                    <input 
                      type="checkbox" 
                      className="form-check-input" 
                      checked={receipts.length > 0 && selectedIds.length === (globalAllIds.length > 0 ? globalAllIds.length : receipts.length)} 
                      onChange={toggleSelectAll} 
                    />
                  </th>
                  <th className="text-center w-1" style={stickyThStyle}></th>
                  <th className="text-center" style={stickyThStyle}>#</th>
                  <th className="text-center" style={stickyThStyle}>التاريخ</th>
                  <th className="text-center" style={stickyThStyle}>المندوب</th>
                  <th className="text-start px-2" style={stickyThStyle}>العميل</th>
                  <th className="text-center" style={stickyThStyle}>الهاتف</th>
                  <th className="text-center" style={stickyThStyle}>المنطقة</th>
                  <th className="text-start px-2" style={stickyThStyle}>العنوان</th>
                  <th className="text-start px-2" style={stickyThStyle}>الأصناف</th>
                  <th className="text-center" style={stickyThStyle}>المقدم</th>
                  <th className="text-center" style={stickyThStyle}>النظام</th>
                  <th className="text-center" style={stickyThStyle}>الإجمالي</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r, index) => (
                  <ReceiptRow 
                    key={r.id || r.local_id || index}
                    r={r}
                    index={index}
                    isSelected={selectedIds.includes(r.id)}
                    toggleSelect={toggleSelect}
                    handleContextMenu={handleContextMenu}
                    toArabic={toArabic}
                    formatCurrency={formatCurrency}
                    getSalespersonName={getSalespersonName}
                  />
                ))}
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

      {/* ── Context Menu ── */}
      {contextMenu && (
        <div 
          className="dropdown-menu show shadow" 
          style={{ position: 'fixed', top: contextMenu.mouseY, left: contextMenu.mouseX, zIndex: 9999, border: '1px solid #dee2e6' }}
        >
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" onClick={() => { handlePdfSingle(contextMenu.receiptId, contextMenu.receiptNum); setContextMenu(null); }}>
            <IconFileText size={18} className="text-primary" /> فتح كـ PDF
          </button>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" onClick={() => { handlePrintSingle(contextMenu.receiptId, contextMenu.receiptNum); setContextMenu(null); }}>
            <IconPrinter size={18} className="text-success" /> طباعة
          </button>
          <div className="dropdown-divider border-secondary-subtle"></div>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" onClick={() => { handleEditSingle(contextMenu.receiptId, contextMenu.receiptNum); setContextMenu(null); }}>
            <IconPencil size={18} className="text-warning" /> تعديل
          </button>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 text-danger fw-bold" onClick={() => { handleDeleteSingle(contextMenu.receiptId, contextMenu.receiptNum); setContextMenu(null); }}>
            <IconTrash size={18} /> حذف
          </button>
        </div>
      )}


    </div>
  );
}
