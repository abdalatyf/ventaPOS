import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import Swal from 'sweetalert2';
import useSmartScroll from '../hooks/useSmartScroll';
import api from '../api';
import { IconReceipt, IconPlus } from '@tabler/icons-react';
import ReceiptsFilterToolbar, { ReceiptsFilterRow1, ReceiptsFilterRow2 } from '../components/receipts/ReceiptsFilterToolbar';
import ReceiptsTable from '../components/receipts/ReceiptsTable';
import ReceiptContextMenu from '../components/receipts/ReceiptContextMenu';
import PrintModal from '../components/common/PrintModal';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';

export default function SearchReceipts() {
  const { setTableRef } = useSmartScroll();
  const navigate = useNavigate();
  const location = useLocation();

  const handleReturnSingle = (id) => {
    navigate(`/receipts/return/${id}`);
  };

  const formatCurrency = (val) => {
    if (val === undefined || val === null || val === '') return '0';
    return Math.round(Number(val) || 0).toLocaleString('en-US');
  };

  const searchParams = new URLSearchParams(location.search);
  let saleTypeInitial = searchParams.get('sale_type') || 'ALL';
  if (searchParams.get('is_cash_sale') === 'true') saleTypeInitial = 'CASH';
  else if (searchParams.get('is_cash_sale') === 'false') saleTypeInitial = 'INSTALLMENT';

  const initialFilters = {
    month: searchParams.get('month') || '',
    year: searchParams.get('year') || '',
    sale_type: saleTypeInitial,
    customer_name: searchParams.get('customer_name') || '',
    phone: searchParams.get('phone') || '',
    address: searchParams.get('address') || '',
    area: searchParams.get('area') || '',
    salesperson_id: searchParams.get('salesperson') || '',
    receipt_from: searchParams.get('receipt_from') || '',
    receipt_to: searchParams.get('receipt_to') || '',
  };

  const [filters, setFilters] = useState(initialFilters);
  const [salespersonName, setSalespersonName] = useState('');
  const [receipts, setReceipts] = useState([]);
  const [salespersons, setSalespersons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const filterTimeout = useRef(null);

  const [totalInvoicesCount, setTotalInvoicesCount] = useState(0);
  const [totalAmountSum, setTotalAmountSum] = useState(0);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const [selectedIds, setSelectedIds] = useState([]);
  const [globalAllIds, setGlobalAllIds] = useState([]);
  const [printModalOpen, setPrintModalOpen] = useState(false);
  const [printModalIds, setPrintModalIds] = useState([]);

  const getSalespersonName = (sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || sp.username || 'غير محدد';
    const found = salespersons.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `بائع #${sp}`;
  };

  const fetchSalespersons = async () => {
    try {
      const currentBranchId = localStorage.getItem('branchId');
      const params = currentBranchId ? { branch_id: currentBranchId } : {};
      const res = await api.get('/salespersons/', { params });
      if (res.data && res.data.results) {
        setSalespersons(res.data.results);
      } else if (Array.isArray(res.data)) {
        setSalespersons(res.data);
      }
    } catch (error) {
      console.error('Error fetching salespersons:', error);
    }
  };

  const fetchReceipts = async (currentFilters) => {
    setLoading(true);
    setReceipts([]);
    setSelectedIds([]);
    try {
      const params = new URLSearchParams();
      const currentBranchId = localStorage.getItem('branchId');
      if (currentBranchId) params.append('branch_id', currentBranchId);
      if (currentFilters.month) params.append('month', currentFilters.month);
      if (currentFilters.year) params.append('year', currentFilters.year);
      if (currentFilters.salesperson_id) params.append('salesperson', currentFilters.salesperson_id);
      if (currentFilters.customer_name) params.append('customer_name', currentFilters.customer_name);
      if (currentFilters.phone) params.append('phone', currentFilters.phone);
      if (currentFilters.address) params.append('address', currentFilters.address);
      if (currentFilters.area) params.append('area', currentFilters.area);
      if (currentFilters.receipt_from) params.append('receipt_from', currentFilters.receipt_from);
      if (currentFilters.receipt_to) params.append('receipt_to', currentFilters.receipt_to);

      if (currentFilters.sale_type === 'CASH') {
        params.append('is_cash_sale', 'true');
      } else if (currentFilters.sale_type === 'INSTALLMENT') {
        params.append('is_cash_sale', 'false');
      }

      const res = await api.get(`/receipts/?${params.toString()}`);
      if (res.data && res.data.results) {
        setReceipts(res.data.results);
        setNextPageUrl(res.data.next);
        setTotalInvoicesCount(res.data.count || 0);
        setTotalAmountSum(res.data.aggregate?.total_sales ?? res.data.total_amount_sum ?? 0);
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

  const fetchSalespersonSuggestions = async (query) => {
    if (!query) return salespersons;
    const q = query.toLowerCase();
    return salespersons.filter(s => s.name && s.name.toLowerCase().includes(q));
  };

  useEffect(() => {
    fetchSalespersons();
    fetchReceipts(initialFilters);

    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => {
      window.removeEventListener('click', handleClick);
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
    };
  }, []);

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
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
      filterTimeout.current = setTimeout(() => {
        fetchReceipts(newFilters);
      }, 300);
      return newFilters;
    });
  };

  const handleResetFilters = () => {
    if (filterTimeout.current) clearTimeout(filterTimeout.current);
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

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    const result = await Swal.fire({
      title: 'هل أنت متأكد؟',
      text: `هل تريد حذف ${selectedIds.length} فاتورة؟`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء',
      confirmButtonColor: '#d33',
      cancelButtonColor: '#6c757d',
    });

    if (result.isConfirmed) {
      try {
        await api.post('/receipts/bulk_delete/', { receipt_ids: selectedIds });
        Swal.fire('تم الحذف!', 'تم حذف الفواتير بنجاح.', 'success');
        fetchReceipts(filters);
      } catch (error) {
        console.error('Error deleting receipts:', error);
        Swal.fire('خطأ', error.response?.data?.message || 'حدث خطأ أثناء الحذف.', 'error');
      }
    }
  };

  const handleDeleteSingle = async (id, num) => {
    const result = await Swal.fire({
      title: 'هل أنت متأكد؟',
      text: `هل تريد حذف الفاتورة رقم ${num}؟`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء',
      confirmButtonColor: '#d33',
      cancelButtonColor: '#6c757d',
    });

    if (result.isConfirmed) {
      try {
        await api.delete(`/receipts/${id}/`);
        Swal.fire('تم الحذف!', 'تم حذف الفاتورة بنجاح.', 'success');
        fetchReceipts(filters);
      } catch (error) {
        console.error('Error deleting receipt:', error);
        Swal.fire('خطأ', 'حدث خطأ أثناء الحذف.', 'error');
      }
    }
  };

  const handleEditSingle = (id, num) => {
    navigate(`/pos?edit=${id}`);
  };

  const handlePdfSingle = (id, num) => {
    handleOpenPrintModal([id]);
  };

  const handlePrintSingle = (id, num) => {
    handleOpenPrintModal([id]);
  };

  const handleOpenPrintModal = (ids) => {
    if (!ids || ids.length === 0) return;

    // Physical printing is strictly reserved for Installment Schedules. Standard cash receipts are not printed.
    const selectedReceipts = receipts.filter(r => ids.includes(r.id));
    const installmentReceipts = selectedReceipts.filter(r => !r.is_cash_sale);

    if (selectedReceipts.length > 0 && installmentReceipts.length === 0) {
      Swal.fire({
        icon: 'info',
        title: 'تنبيه الطباعة',
        text: 'الطباعة مخصصة فقط لجداول الأقساط (الفواتير الكاش ليس لها جدول طباعة).',
        confirmButtonText: 'حسناً',
        confirmButtonColor: '#123F68'
      });
      return;
    }

    const targetIds = installmentReceipts.length > 0 ? installmentReceipts.map(r => r.id) : ids;
    setPrintModalIds(targetIds);
    setPrintModalOpen(true);
  };

  const handlePrint = (ids, action = 'print') => {
    handleOpenPrintModal(ids);
  };

  const executeChunkReceipts = async (chunk, { action, targetPrinter }) => {
    const payload = {
      receipt_ids: chunk,
      action,
      target_printer: targetPrinter || null
    };
    await api.post('/receipts/desktop_print/', payload);
  };

  const handleContextMenu = (e, receipt) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, receipt });
  };

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
    <StandardTablePageLayout
      title="دفتر المبيعات"
      icon={IconReceipt}
      headerActions={
        <Link to="/pos" className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2">
          <IconPlus size={20} />
          <span>إضافة فاتورة جديدة</span>
        </Link>
      }
      row1={
        <ReceiptsFilterRow1
          filters={filters}
          handleFilterChange={handleFilterChange}
          handleSelectChange={handleSelectChange}
        />
      }
      row2={
        <ReceiptsFilterRow2
          filters={filters}
          handleFilterChange={handleFilterChange}
          salespersonName={salespersonName}
          setSalespersonName={setSalespersonName}
          setFilters={setFilters}
          fetchReceipts={fetchReceipts}
          fetchSalespersonSuggestions={fetchSalespersonSuggestions}
          handleResetFilters={handleResetFilters}
          loading={loading}
        />
      }
      modals={
        <>
          <ReceiptContextMenu
            contextMenu={contextMenu}
            handleEditSingle={handleEditSingle}
            handlePdfSingle={handlePdfSingle}
            handlePrintSingle={handlePrintSingle}
            handleReturnSingle={handleReturnSingle}
            handleDeleteSingle={handleDeleteSingle}
            closeContextMenu={() => setContextMenu(null)}
          />

          <PrintModal
            isOpen={printModalOpen}
            onClose={() => setPrintModalOpen(false)}
            title="طباعة جداول الأقساط"
            items={printModalIds}
            itemLabel="جدول أقساط"
            executeChunk={executeChunkReceipts}
          />
        </>
      }
    >
      <ReceiptsTable
        receipts={receipts}
        loading={loading}
        totalInvoicesCount={totalInvoicesCount}
        totalAmountSum={totalAmountSum}
        selectedIds={selectedIds}
        globalAllIds={globalAllIds}
        toggleSelect={toggleSelect}
        toggleSelectAll={toggleSelectAll}
        handlePrint={handlePrint}
        handleBulkDelete={handleBulkDelete}
        handleContextMenu={handleContextMenu}
        formatCurrency={formatCurrency}
        getSalespersonName={getSalespersonName}
        handleEditSingle={handleEditSingle}
        handlePdfSingle={handlePdfSingle}
        handlePrintSingle={handlePrintSingle}
        handleDeleteSingle={handleDeleteSingle}
        handleReturnSingle={handleReturnSingle}
        lastRowElementRef={lastRowElementRef}
        setTableRef={setTableRef}
        loadingMore={loadingMore}
      />
    </StandardTablePageLayout>
  );
}
