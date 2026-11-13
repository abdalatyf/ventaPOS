import React, { useMemo, useRef, useState } from 'react';
import useSmartScroll from '../../hooks/useSmartScroll';
import { IconReceipt, IconPrinter, IconTrash } from '@tabler/icons-react';
import PurchaseInvoiceRow from './PurchaseInvoiceRow';
import { fmtNum } from '../../utils/formatUtils';

export default function PurchaseTable({
  invoices,
  loading,
  totalInvoicesCount,
  totalAmountSum,
  selectedIds,
  globalAllIds,
  toggleSelect,
  toggleSelectAll,
  selectAllMatching,
  handleOpenPrintModal,
  handleBulkDelete,
  handleContextMenu,
  formatCurrency,
  getSupplierName,
  lastRowElementRef,
  setTableRef: externalSetTableRef,
  loadingMore
}) {
  const { setTableRef: internalSetTableRef } = useSmartScroll();
  const tableContainerElemRef = useRef(null);
  const [focusedRowIndex, setFocusedRowIndex] = useState(-1);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const isAllMatchingSelected = globalAllIds.length > 0 && selectedIds.length === globalAllIds.length;
  const isCurrentPageSelected = invoices.length > 0 && invoices.every(r => selectedSet.has(r.id));
  const isPartiallySelected = selectedIds.length > 0 && !isAllMatchingSelected && !isCurrentPageSelected;

  const handleSetTableRef = (node) => {
    tableContainerElemRef.current = node;
    if (externalSetTableRef) {
      externalSetTableRef(node);
    } else {
      internalSetTableRef(node);
    }
  };

  const scrollRowIntoView = (idx) => {
    const container = tableContainerElemRef.current;
    if (!container) return;
    const row = container.querySelector(`tbody tr[data-row-index="${idx}"]`);
    if (row) row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };

  const handleKeyDown = (e) => {
    if (!invoices || invoices.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedRowIndex(prev => {
        const next = Math.min(prev + 1, invoices.length - 1);
        scrollRowIntoView(next);
        return next;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedRowIndex(prev => {
        const next = Math.max(prev - 1, 0);
        scrollRowIntoView(next);
        return next;
      });
    } else if (e.key === ' ' && focusedRowIndex >= 0) {
      e.preventDefault();
      const row = invoices[focusedRowIndex];
      if (row) toggleSelect(row.id);
    }
  };

  return (
    <div className="card shadow-sm border-secondary-subtle rounded bg-white mb-0">
      {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
      <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
        <div className="d-flex align-items-center gap-2 flex-nowrap overflow-auto hide-vertical-scroll" style={{ minWidth: 0 }}>
          <span className="text-secondary fw-bold small flex-shrink-0">النتائج:</span>
          <span className="badge bg-primary text-white rounded-pill px-2 py-1 tabular-nums flex-shrink-0">{fmtNum(totalInvoicesCount || 0)} فاتورة</span>

          {selectedIds.length > 0 && (
            <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-2 ms-1 flex-shrink-0">
              <span className="fw-bold small me-1">تم تحديد {fmtNum(selectedIds.length)}</span>
              {handleOpenPrintModal && (
                <button 
                  type="button"
                  className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                  onClick={() => handleOpenPrintModal(selectedIds)}
                >
                  <IconPrinter size={14} /> طباعة محددة
                </button>
              )}
              <button 
                type="button"
                className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={handleBulkDelete}
              >
                <IconTrash size={14} /> حذف محددة
              </button>
            </div>
          )}
        </div>

        <div className="d-flex align-items-center flex-shrink-0">
          <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2" style={{ borderColor: '#adb5bd' }}>
            <span>إجمالي فواتير الشراء:</span>
            <span className="text-danger fw-bolder fs-4 tabular-nums">{formatCurrency(totalAmountSum || 0)}</span>
          </div>
        </div>
      </div>

      {/* Two-Tier Selection Alert Strip (Sticky below toolbar) */}
      {selectedIds.length > 0 && totalInvoicesCount > invoices.length && (
        <div className="sticky-selection-strip bg-light border-bottom px-3 py-1 text-center small fw-bold text-dark d-flex align-items-center justify-content-center gap-2 d-print-none">
          {isAllMatchingSelected ? (
            <>
              <span>تم تحديد كافة الـ {fmtNum(totalInvoicesCount)} فاتورة المطابقة للبحث.</span>
              <button type="button" className="btn btn-link btn-sm p-0 fw-bold text-danger text-decoration-none" onClick={() => toggleSelectAll && toggleSelectAll()}>
                إلغاء التحديد
              </button>
            </>
          ) : (
            <>
              <span>تم تحديد {fmtNum(selectedIds.length)} فاتورة في هذه الصفحة.</span>
              <button type="button" className="btn btn-link btn-sm p-0 fw-bold text-primary text-decoration-none" onClick={() => selectAllMatching && selectAllMatching()}>
                تحديد كافة الـ {fmtNum(totalInvoicesCount)} فاتورة المطابقة للبحث
              </button>
            </>
          )}
        </div>
      )}

      {/* Row 2 of Table Card: Table Container */}
      <div
        ref={handleSetTableRef}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="table-responsive report-table-container hide-vertical-scroll flex-grow-1 focus-ring-none"
        style={{ outline: 'none' }}
      >
        <table className="table table-sm table-bordered table-vcenter table-hover table-sticky-header text-nowrap tabular-nums mb-0">
          <thead className="bg-light">
            <tr>
              <th className="text-center w-1">
                <input 
                  type="checkbox" 
                  className="form-check-input" 
                  checked={invoices.length > 0 && (isCurrentPageSelected || isAllMatchingSelected)}
                  ref={el => { if (el) el.indeterminate = isPartiallySelected; }}
                  onChange={toggleSelectAll} 
                />
              </th>
              <th className="text-center w-1"></th>
              <th className="text-center">رقم الفاتورة</th>
              <th className="text-center">النوع</th>
              <th className="text-center">التاريخ</th>
              <th className="text-center">المورد</th>
              <th className="text-center px-2">إجمالي القطع</th>
              <th className="text-center">الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" className="text-center py-5">
                  <div className="spinner-border text-primary mb-2"></div>
                  <div className="text-secondary fw-bold fs-4">جاري تحميل الفواتير...</div>
                </td>
              </tr>
            ) : invoices.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center py-5">
                  <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
                  <h4 className="text-muted fw-bold mb-0">لا توجد فواتير مطابقة لمعايير البحث</h4>
                </td>
              </tr>
            ) : (
              invoices.map((r, index) => {
                const isLast = index === invoices.length - 1;
                return (
                  <PurchaseInvoiceRow 
                    key={r.id || r.local_id || index}
                    r={r}
                    index={index}
                    isSelected={selectedSet.has(r.id)}
                    isFocused={focusedRowIndex === index}
                    toggleSelect={toggleSelect}
                    handleContextMenu={handleContextMenu}
                    formatCurrency={formatCurrency}
                    getSupplierName={getSupplierName}
                    innerRef={isLast ? lastRowElementRef : null}
                  />
                );
              })
            )}
            {loadingMore && (
              <tr>
                <td colSpan="8" className="text-center py-3">
                  <div className="spinner-border spinner-border-sm text-primary"></div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
