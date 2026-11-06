import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import Swal from 'sweetalert2';
import api from '../api';
import { IconReceipt, IconPlus } from '@tabler/icons-react';
import { PurchaseFilterRow1, PurchaseFilterRow2 } from '../components/purchases/PurchaseFilterToolbar';
import PurchaseTable from '../components/purchases/PurchaseTable';
import PurchaseContextMenu from '../components/purchases/PurchaseContextMenu';
import PrintModal from '../components/common/PrintModal';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';
import { fetchSuppliersList, fetchProductsMap } from '../components/purchases/purchaseUtils';

export default function SearchPurchases() {
  const formatCurrency = (val) => {
    if (val === undefined || val === null || val === '') return '0';
    return Math.round(Number(val) || 0).toLocaleString('en-US');
  };

  const initialFilters = {
    invoice_number: '', supplier_id: '', month: '', year: '', invoice_type: 'ALL'
  };

  const [filters, setFilters] = useState(initialFilters);
  const [supplierSearchQuery, setSupplierSearchQuery] = useState('');
  const [invoices, setInvoices] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [productsMap, setProductsMap] = useState({});
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

  // Infinite Scroll Observer
  const observer = useRef();
  const lastRowElementRef = useCallback(node => {
    if (loadingMore) return;
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && nextPageUrl) {
        loadMoreInvoices();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [loadingMore, nextPageUrl]);

  useEffect(() => {
    fetchSuppliersList().then(setSuppliers);
    fetchProductsMap().then(setProductsMap);
    fetchInvoices(initialFilters);

    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => {
      window.removeEventListener('click', handleClick);
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
    };
  }, []);

  const getSupplierName = (sp) => {
    if (!sp) return 'غير محدد';
    if (typeof sp === 'object') return sp.name || 'غير محدد';
    const found = suppliers.find(s => s.id === Number(sp) || s.local_id === Number(sp) || s.id === sp);
    return found ? found.name : `مورد #${sp}`;
  };

  const fetchInvoices = async (currentFilters) => {
    setLoading(true);
    setInvoices([]);
    setSelectedIds([]);
    try {
      const params = new URLSearchParams();
      const currentBranchId = localStorage.getItem('branchId');
      if (currentBranchId) params.append('branch_id', currentBranchId);
      if (currentFilters.month) params.append('month', currentFilters.month);
      if (currentFilters.year) params.append('year', currentFilters.year);
      if (currentFilters.supplier_id) params.append('supplier', currentFilters.supplier_id);
      if (currentFilters.invoice_number) params.append('invoice_number', currentFilters.invoice_number);
      if (currentFilters.invoice_type && currentFilters.invoice_type !== 'ALL') {
        params.append('invoice_type', currentFilters.invoice_type);
      }

      const res = await api.get(`/purchase-invoices/?${params.toString()}`);
      if (res.data && res.data.results) {
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
    setFilters(prev => {
      const newFilters = { ...prev, [name]: enVal };
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
      filterTimeout.current = setTimeout(() => { fetchInvoices(newFilters); }, 300);
      return newFilters;
    });
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => {
      const newFilters = { ...prev, [name]: value };
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
      filterTimeout.current = setTimeout(() => { fetchInvoices(newFilters); }, 300);
      return newFilters;
    });
  };

  const fetchSupplierSuggestions = async (query) => {
    if (!query) return [];
    try {
      const res = await api.get(`/suppliers/?search=${encodeURIComponent(query)}`);
      const results = res.data?.results || res.data;
      if (Array.isArray(results) && results.length > 0) return results;
      return suppliers.filter(s => s.name && s.name.toLowerCase().includes(query.toLowerCase()));
    } catch (error) {
      return suppliers.filter(s => s.name && s.name.toLowerCase().includes(query.toLowerCase()));
    }
  };

  const handleSupplierQueryChange = (val) => {
    setSupplierSearchQuery(val);
    if (!val.trim()) {
      setFilters(prev => {
        const newFilters = { ...prev, supplier_id: '' };
        if (filterTimeout.current) clearTimeout(filterTimeout.current);
        filterTimeout.current = setTimeout(() => { fetchInvoices(newFilters); }, 300);
        return newFilters;
      });
    }
  };

  const handleSupplierSelect = (item) => {
    if (!item) return;
    setSupplierSearchQuery(item.name || '');
    setFilters(prev => {
      const newFilters = { ...prev, supplier_id: item.id };
      if (filterTimeout.current) clearTimeout(filterTimeout.current);
      filterTimeout.current = setTimeout(() => { fetchInvoices(newFilters); }, 300);
      return newFilters;
    });
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (filterTimeout.current) clearTimeout(filterTimeout.current);
    fetchInvoices(filters);
  };

  const handleResetFilters = () => {
    if (filterTimeout.current) clearTimeout(filterTimeout.current);
    setSupplierSearchQuery('');
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
        for (const id of selectedIds) {
          await api.delete(`/purchase-invoices/${id}/`);
        }
        toast.success('تم حذف الفواتير بنجاح.');
        fetchInvoices(filters);
      } catch (error) {
        toast.error('حدث خطأ أثناء الحذف.');
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
        await api.delete(`/purchase-invoices/${id}/`);
        toast.success('تم حذف الفاتورة بنجاح.');
        fetchInvoices(filters);
      } catch (error) {
        toast.error('حدث خطأ أثناء الحذف.');
      }
    }
  };

  const handleOpenPrintModal = (ids) => {
    if (!ids || ids.length === 0) return;
    setPrintModalIds(ids);
    setPrintModalOpen(true);
  };

  const executeChunkPurchases = async (chunk, { action, targetPrinter }) => {
    const payload = {
      invoice_ids: chunk,
      action,
      target_printer: targetPrinter || null
    };
    await api.post('/purchase-invoices/desktop_print/', payload);
  };

  const handleContextMenu = (e, rId, rNum) => {
    e.preventDefault();
    setContextMenu({ mouseX: e.clientX, mouseY: e.clientY, invoiceId: rId, invoiceNum: rNum });
  };

  return (
    <StandardTablePageLayout
      title="دفتر فواتير الشراء ومرتجع المصنع"
      icon={IconReceipt}
      headerActions={
        <Link to="/purchases/new" className="btn btn-success d-flex align-items-center gap-1 fw-bold fs-4 border-secondary-subtle py-2">
          <IconPlus size={20} />
          <span>إضافة فاتورة جديدة</span>
        </Link>
      }
      row1={
        <PurchaseFilterRow1
          filters={filters}
          handleFilterChange={handleFilterChange}
          handleSelectChange={handleSelectChange}
          supplierSearchQuery={supplierSearchQuery}
          handleSupplierQueryChange={handleSupplierQueryChange}
          handleSupplierSelect={handleSupplierSelect}
          fetchSupplierSuggestions={fetchSupplierSuggestions}
          handleSearchSubmit={handleSearchSubmit}
          handleResetFilters={handleResetFilters}
          loading={loading}
        />
      }
      modals={
        <>
          <PurchaseContextMenu 
            contextMenu={contextMenu} 
            handleDeleteSingle={handleDeleteSingle} 
            handlePrintSingle={(id) => handleOpenPrintModal([id])}
            onClose={() => setContextMenu(null)} 
          />

          <PrintModal
            isOpen={printModalOpen}
            onClose={() => setPrintModalOpen(false)}
            title="طباعة فواتير الشراء / المرتجع"
            items={printModalIds}
            itemLabel="فاتورة شراء"
            executeChunk={executeChunkPurchases}
          />
        </>
      }
    >
      <PurchaseTable
        invoices={invoices}
        loading={loading}
        totalInvoicesCount={totalInvoicesCount}
        totalAmountSum={totalAmountSum}
        selectedIds={selectedIds}
        globalAllIds={globalAllIds}
        toggleSelect={toggleSelect}
        toggleSelectAll={toggleSelectAll}
        handleOpenPrintModal={handleOpenPrintModal}
        handleBulkDelete={handleBulkDelete}
        handleContextMenu={handleContextMenu}
        formatCurrency={formatCurrency}
        getSupplierName={getSupplierName}
        lastRowElementRef={lastRowElementRef}
        loadingMore={loadingMore}
      />
    </StandardTablePageLayout>
  );
}
