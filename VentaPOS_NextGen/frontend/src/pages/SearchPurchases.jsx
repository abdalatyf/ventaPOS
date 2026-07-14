import useSmartScroll from '../hooks/useSmartScroll';
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import {
  IconSearch, IconRefresh, IconPlus, IconEye, IconReceipt, IconPrinter, IconFilter,
  IconTrash, IconDotsVertical, IconPencil, IconFileText, IconCalendar, IconUser,
  IconMapPin, IconPhone, IconCheck, IconX, IconCreditCard, IconCash
} from '@tabler/icons-react';

const InvoiceRow = React.memo(({
  r, index, isSelected, toggleSelect, handleContextMenu, toArabic, formatCurrency, getSupplierName
}) => {
  const rowKey = r.id || r.local_id || index;
  const rNum = r.invoice_number || r.local_id || r.id;
  const typeText = r.invoice_type === 'PURCHASE' ? 'شراء' : 'مرتجع';
  const supplierName = getSupplierName(r.supplier);
  const piecesCount = r.items ? r.items.reduce((acc, item) => acc + Number(item.quantity || 0), 0) : 0;
  const totalAmount = r.items ? r.items.reduce((acc, item) => acc + (item.quantity * item.purchase_price), 0) : 0;

  return (
    <tr onContextMenu={(e) => handleContextMenu(e, r.id, rNum)}>
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
      <td className="text-center align-middle border-secondary-subtle fw-bold" dir="ltr">{toArabic(rNum)}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <span className={`badge ${r.invoice_type === 'PURCHASE' ? 'bg-success' : 'bg-danger'} text-white`}>{typeText}</span>
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold text-muted" dir="ltr">{r.created_at ? toArabic(new Date(r.created_at).toLocaleDateString('en-GB')) : `${toArabic(r.invoice_month)}/${toArabic(r.invoice_year)}`}</td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {supplierName}
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold">
        {toArabic(piecesCount)} قطعة
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-danger">
        {toArabic(formatCurrency(totalAmount))}
      </td>
    </tr>
  );
}, (prevProps, nextProps) => {
  return prevProps.isSelected === nextProps.isSelected && prevProps.r === nextProps.r;
});

export default function SearchPurchases() {
  const { setTableRef } = useSmartScroll();
  const navigate = useNavigate();

  const toArabic = (str) => {
    if (str === null || str === undefined) return '';
    return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
  };

  const formatCurrency = (val) => {
    if (val === undefined || val === null || val === '') return '0';
    return Math.round(Number(val)).toString();
  };

  const getSupplierName = (sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || 'غير محدد';
    const found = suppliers.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `مورد #${sp}`;
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
    invoice_number: '', supplier_id: '', month: '', year: '', invoice_type: 'ALL'
  };

  const [filters, setFilters] = useState(initialFilters);
  const [invoices, setInvoices] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
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
    fetchSuppliers();
    fetchInventory();
    fetchInvoices(initialFilters);

    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  }, []);

  const fetchSuppliers = async () => {
    try {
      const res = await api.get('/suppliers/');
      if (res.data && res.data.results) {
        setSuppliers(res.data.results);
      } else if (Array.isArray(res.data)) {
        setSuppliers(res.data);
      }
    } catch (error) {
      console.error('Error fetching suppliers:', error);
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

  const fetchInvoices = async (currentFilters) => {
    setLoading(true);
    setInvoices([]);
    setSelectedIds([]);
    try {
      const params = new URLSearchParams();
      if (currentFilters.month) params.append('month', currentFilters.month);
      if (currentFilters.year) params.append('year', currentFilters.year);
      if (currentFilters.supplier_id) params.append('supplier', currentFilters.supplier_id);
      if (currentFilters.invoice_number) params.append('invoice_number', currentFilters.invoice_number);
      if (currentFilters.invoice_type && currentFilters.invoice_type !== 'ALL') {
        params.append('invoice_type', currentFilters.invoice_type);
      }

      const res = await api.get(`/purchase-invoices/?${params.toString()}`);
      if (res.data && res.data.results) {
        // Map product names
        const enrichedInvoices = res.data.results.map(inv => ({
          ...inv,
          items: inv.items ? inv.items.map(i => ({
            ...i,
            inventory_item_name: productsMap[i.inventory_item] || `صنف #${i.inventory_item}`
          })) : []
        }));
        setInvoices(enrichedInvoices);
        setNextPageUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || 0);
        setTotalAmountSum(res.data.aggregate?.total_purchases || 0);
        const allIds = res.data.all_ids || [];
        setGlobalAllIds(allIds);
        setSelectedIds(allIds.length > 0 ? allIds : enrichedInvoices.map(r => r.id));
      }
    } catch (error) {
      console.error('Error fetching purchase invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  // When productsMap changes, enrich existing invoices
  useEffect(() => {
    if (invoices.length > 0 && Object.keys(productsMap).length > 0) {
      setInvoices(prev => prev.map(inv => ({
        ...inv,
        items: inv.items ? inv.items.map(i => ({
          ...i,
          inventory_item_name: productsMap[i.inventory_item] || `صنف #${i.inventory_item}`
        })) : []
      })));
    }
  }, [productsMap]);

  const loadMoreInvoices = async () => {
    if (!nextPageUrl || loadingMore) return;
    setLoadingMore(true);
    try {
      const res = await api.get(nextPageUrl);
      if (res.data && res.data.results) {
        const enrichedInvoices = res.data.results.map(inv => ({
          ...inv,
          items: inv.items ? inv.items.map(i => ({
            ...i,
            inventory_item_name: productsMap[i.inventory_item] || `صنف #${i.inventory_item}`
          })) : []
        }));
        setInvoices(prev => [...prev, ...enrichedInvoices]);
        setNextPageUrl(res.data.next);
      }
    } catch (error) {
      console.error('Error loading more invoices:', error);
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
    fetchInvoices(filters);
  };

  const handleResetFilters = () => {
    setFilters(initialFilters);
    fetchInvoices(initialFilters);
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const toggleSelectAll = () => {
    const targetLength = globalAllIds.length > 0 ? globalAllIds.length : invoices.length;
    if (selectedIds.length === targetLength) {
      setSelectedIds([]);
    } else {
      setSelectedIds(globalAllIds.length > 0 ? globalAllIds : invoices.map(r => r.id));
    }
  };

  const handlePrint = async (ids, action = "print") => {
    if (ids.length === 0) return;
    try {
      const res = await api.post('/purchase-invoices/desktop_print/', { invoice_ids: ids, action });
      if (res.data && res.data.message) {
        // The backend handles opening the PDF via os.startfile locally.
        console.log(res.data.message);
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('حدث خطأ أثناء إنشاء الـ PDF.');
    }
  };

  const handlePrintSingle = (id, num) => {
    handlePrint([id], "print");
  };

  const handleViewSingle = (id, num) => {
    handlePrint([id], "view");
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!window.confirm(`هل أنت متأكد من حذف ${selectedIds.length} فاتورة؟`)) return;
    try {
      // Assuming you might add bulk delete for purchases, but for now we loop
      for(const id of selectedIds) {
        await api.delete(`/purchase-invoices/${id}/`);
      }
      alert('تم الحذف بنجاح.');
      fetchInvoices(filters);
    } catch (error) {
      console.error('Error deleting invoices:', error);
      alert('حدث خطأ أثناء الحذف.');
    }
  };

  const handleDeleteSingle = async (id, num) => {
    if (!window.confirm(`هل أنت متأكد من حذف الفاتورة رقم ${num}؟`)) return;
    try {
      await api.delete(`/purchase-invoices/${id}/`);
      fetchInvoices(filters);
    } catch (error) {
      console.error('Error deleting invoice:', error);
      alert('حدث خطأ أثناء الحذف.');
    }
  };

  const handleContextMenu = (e, rId, rNum) => {
    e.preventDefault();
    setContextMenu({ mouseX: e.clientX, mouseY: e.clientY, invoiceId: rId, invoiceNum: rNum });
  };

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 100) {
      if (nextPageUrl && !loadingMore) {
        loadMoreInvoices();
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
          دفتر فواتير الشراء ومرتجع المصنع
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
          <Link to="/purchases/new" className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2">
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
              
              {/* ── Row 1 ── */}
              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '80px' }}>نوع الفاتورة</span>
                  <select className="form-select fw-bold border-secondary-subtle" name="invoice_type" value={filters.invoice_type} onChange={handleSelectChange}>
                    <option value="ALL">الكل</option>
                    <option value="PURCHASE">فاتورة شراء</option>
                    <option value="RETURN">مرتجع للمورد</option>
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>رقم الفاتورة</span>
                  <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="invoice_number" value={toArabic(filters.invoice_number)} onChange={handleFilterChange} />
                </div>
              </div>

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

              <div style={{ gridColumn: 'span 2' }}>
                <div className="input-group input-group-sm">
                  <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المورد</span>
                  <select className="form-select fw-bold border-secondary-subtle" name="supplier_id" value={filters.supplier_id} onChange={handleSelectChange}>
                    <option value="">جميع الموردين</option>
                    {suppliers.map((sp) => (
                      <option key={sp.id || sp.local_id} value={sp.id || sp.local_id}>{sp.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ gridColumn: 'span 8' }} className="d-flex align-items-center gap-2 justify-content-end mt-2">
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
            
            {invoices.length > 0 && (
              <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-3 ms-1">
                {selectedIds.length > 0 ? (
                  <>
                    <span className="fw-bold me-2">تم تحديد {toArabic(selectedIds.length)}</span>
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

          {invoices.length > 0 && (
            <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm" style={{ borderColor: '#adb5bd !important' }}>
              إجمالي فواتير الشراء:{' '}
              <span className="text-danger fw-bolder fs-4">{toArabic(formatCurrency(totalAmountSum))}</span>
            </div>
          )}
        </div>

        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary mb-3"></div>
            <div className="text-secondary fw-bold fs-3">جاري تحميل الفواتير...</div>
          </div>
        ) : invoices.length === 0 ? (
          <div className="card-body text-center py-5">
            <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
            <h4 className="text-muted fw-bold">لا توجد فواتير مطابقة لمعايير البحث</h4>
          </div>
        ) : (
          <div 
            ref={setTableRef}
            className="table-responsive hide-vertical-scroll flex-grow-1 rounded" 
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
                      checked={invoices.length > 0 && selectedIds.length === (globalAllIds.length > 0 ? globalAllIds.length : invoices.length)} 
                      onChange={toggleSelectAll} 
                    />
                  </th>
                  <th className="text-center w-1" style={stickyThStyle}></th>
                  <th className="text-center" style={stickyThStyle}>رقم الفاتورة</th>
                  <th className="text-center" style={stickyThStyle}>النوع</th>
                  <th className="text-center" style={stickyThStyle}>التاريخ</th>
                  <th className="text-center" style={stickyThStyle}>المورد</th>
                  <th className="text-center px-2" style={stickyThStyle}>إجمالي القطع</th>
                  <th className="text-center" style={stickyThStyle}>الإجمالي</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((r, index) => (
                  <InvoiceRow 
                    key={r.id || r.local_id || index}
                    r={r}
                    index={index}
                    isSelected={selectedIds.includes(r.id)}
                    toggleSelect={toggleSelect}
                    handleContextMenu={handleContextMenu}
                    toArabic={toArabic}
                    formatCurrency={formatCurrency}
                    getSupplierName={getSupplierName}
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
          <Link className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" to={`/purchases/edit/${contextMenu.invoiceId}`}>
            <IconPencil size={18} className="text-primary" /> تعديل
          </Link>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" onClick={() => { handlePrintSingle(contextMenu.invoiceId, contextMenu.invoiceNum); setContextMenu(null); }}>
            <IconPrinter size={18} className="text-success" /> طباعة
          </button>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" onClick={() => { handleViewSingle(contextMenu.invoiceId, contextMenu.invoiceNum); setContextMenu(null); }}>
            <IconEye size={18} className="text-info" /> معاينة PDF
          </button>
          <div className="dropdown-divider"></div>
          <button className="dropdown-item d-flex align-items-center gap-2 py-2 text-danger fw-bold" onClick={() => { handleDeleteSingle(contextMenu.invoiceId, contextMenu.invoiceNum); setContextMenu(null); }}>
            <IconTrash size={18} /> حذف
          </button>
        </div>
      )}

    </div>
  );
}
