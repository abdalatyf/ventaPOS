import React, { useMemo, useRef, useState } from 'react';
import { IconReceipt, IconPrinter, IconEye, IconTrash } from '@tabler/icons-react';
import ReceiptRow from './ReceiptRow';
import { fmtNum } from '../../utils/formatUtils';

export default function ReceiptsTable({
  receipts,
  loading,
  totalInvoicesCount,
  totalAmountSum,
  selectedIds,
  globalAllIds,
  toggleSelect,
  toggleSelectAll,
  handlePrint,
  handleBulkDelete,
  handleContextMenu,
  formatCurrency,
  getSalespersonName,
  handleEditSingle,
  handlePdfSingle,
  handlePrintSingle,
  handleDeleteSingle,
  handleReturnSingle,
  lastRowElementRef,
  setTableRef,
  loadingMore,
  selectAllMatching
}) {
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const [focusedRowIndex, setFocusedRowIndex] = useState(-1);
  const tableContainerElemRef = useRef(null);

  const targetCount = globalAllIds.length > 0 ? globalAllIds.length : receipts.length;
  const isAllMatchingSelected = targetCount > 0 && selectedIds.length === targetCount;
  const isPartiallySelected = selectedIds.length > 0 && selectedIds.length < targetCount;

  const handleSetTableRef = (node) => {
    tableContainerElemRef.current = node;
    if (setTableRef) setTableRef(node);
  };

  const scrollRowIntoView = (idx) => {
    const container = tableContainerElemRef.current;
    if (!container) return;
    const row = container.querySelector(`tbody tr[data-row-index="${idx}"]`);
    if (row) row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };

  const handleKeyDown = (e) => {
    if (!receipts || receipts.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedRowIndex(prev => {
        const next = Math.min(prev + 1, receipts.length - 1);
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
      const row = receipts[focusedRowIndex];
      if (row) toggleSelect(row.id);
    } else if (e.key === 'Enter' && focusedRowIndex >= 0) {
      const row = receipts[focusedRowIndex];
      if (row && row.receipt_type !== 'RETURN') {
        e.preventDefault();
        handleEditSingle(row.id, row.receipt_number || row.local_id || row.id);
      }
    }
  };

  return (
    <div className="card shadow-sm border-secondary-subtle mb-0 flex-grow-1">
      {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
      <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
        <div className="d-flex align-items-center gap-2 flex-nowrap overflow-auto hide-vertical-scroll" style={{ minWidth: 0 }}>
          <span className="badge bg-primary text-white rounded-pill px-2 py-1 fs-5 flex-shrink-0">
            نتائج البحث: {fmtNum(totalInvoicesCount || 0)} فاتورة
          </span>

          {selectedIds.length > 0 && (
            <div className="d-flex align-items-center gap-1 border-start border-secondary-subtle ps-2 ms-1 flex-shrink-0">
              <span className="badge bg-secondary-lt text-dark fw-bold px-2 py-1">
                محدد {fmtNum(selectedIds.length)}
              </span>
              <button 
                type="button"
                className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={() => handlePrint && handlePrint(selectedIds, 'print')}
              >
                <IconPrinter size={14} />
                <span>طباعة محددة</span>
              </button>
              <button 
                type="button"
                className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={() => handlePrint && handlePrint(selectedIds, 'view')}
              >
                <IconEye size={14} />
                <span>معاينة محددة</span>
              </button>
              <button 
                type="button"
                className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={handleBulkDelete}
              >
                <IconTrash size={14} />
                <span>حذف محددة</span>
              </button>
            </div>
          )}
        </div>

        <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm flex-shrink-0" style={{ borderColor: '#adb5bd' }}>
          إجمالي فواتير البيع:{' '}
          <span className="text-primary fw-bolder fs-4">
            {formatCurrency ? formatCurrency(totalAmountSum || 0) : fmtNum(totalAmountSum || 0)}
          </span>
        </div>
      </div>

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
                  checked={isAllMatchingSelected}
                  ref={el => { if (el) el.indeterminate = isPartiallySelected; }}
                  onChange={toggleSelectAll} 
                />
              </th>
              <th className="text-center w-1"></th>
              <th className="text-center">رقم الوصل</th>
              <th className="text-center">تاريخ البيع</th>
              <th className="text-center">المندوب</th>
              <th className="text-start px-2">اسم العميل</th>
              <th className="text-center" style={{ minWidth: '125px' }}>الهاتف</th>
              <th className="text-center" style={{ minWidth: '125px' }}>المنطقة</th>
              <th className="text-start px-2">العنوان</th>
              <th className="text-start px-2">الأصناف</th>
              <th className="text-center">المقدم</th>
              <th className="text-center">نظام القسط</th>
              <th className="text-center">الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="13" className="text-center py-5">
                  <div className="spinner-border text-primary mb-2"></div>
                  <div className="text-secondary fw-bold fs-4">جاري تحميل الفواتير...</div>
                </td>
              </tr>
            ) : receipts.length === 0 ? (
              <tr>
                <td colSpan="13" className="text-center py-5">
                  <IconReceipt size={48} className="text-muted mb-2 opacity-50" />
                  <h4 className="text-muted fw-bold mb-0">لا توجد فواتير مطابقة لمعايير البحث</h4>
                </td>
              </tr>
            ) : (
              receipts.map((r, index) => {
                const isLast = index === receipts.length - 1;
                return (
                  <ReceiptRow 
                    key={r.id || r.local_id || index}
                    ref={isLast ? lastRowElementRef : null}
                    r={r}
                    index={index}
                    isSelected={selectedSet.has(r.id)}
                    isFocused={focusedRowIndex === index}
                    onRowFocus={setFocusedRowIndex}
                    toggleSelect={toggleSelect}
                    handleContextMenu={handleContextMenu}
                    formatCurrency={formatCurrency}
                    getSalespersonName={getSalespersonName}
                    handleEditSingle={handleEditSingle}
                    handlePdfSingle={handlePdfSingle}
                    handlePrintSingle={handlePrintSingle}
                    handleDeleteSingle={handleDeleteSingle}
                    handleReturnSingle={handleReturnSingle}
                  />
                );
              })
            )}
            {loadingMore && (
              <tr>
                <td colSpan="13" className="text-center py-3">
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
