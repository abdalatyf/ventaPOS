import React from 'react';
import { IconReceipt, IconPrinter, IconEye, IconTrash } from '@tabler/icons-react';
import ReceiptRow from './ReceiptRow';

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
  loadingMore
}) {
  return (
    <div className="card shadow-sm border-secondary-subtle mb-0 flex-grow-1">
      {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
      <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
        <div className="d-flex align-items-center gap-2">
          <span className="badge bg-primary text-white rounded-pill px-2 py-1 fs-5">
            نتائج البحث: {totalInvoicesCount || 0} فاتورة
          </span>

          {selectedIds.length > 0 && (
            <div className="d-flex align-items-center gap-1 border-start border-secondary-subtle ps-2 ms-1">
              <span className="badge bg-secondary-lt text-dark fw-bold px-2 py-1">
                محدد {selectedIds.length}
              </span>
              <button 
                type="button"
                className="btn btn-outline-success btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
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
          <span className="text-danger fw-bolder fs-4">
            {formatCurrency ? formatCurrency(totalAmountSum || 0) : (totalAmountSum || 0)}
          </span>
        </div>
      </div>

      {/* Row 2 of Table Card: Table Container */}
      <div ref={setTableRef} className="table-responsive report-table-container flex-grow-1">
        <table className="table table-sm table-bordered table-vcenter table-hover table-sticky-header text-nowrap tabular-nums mb-0">
          <thead className="bg-light">
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
              <th className="text-center">رقم الوصل</th>
              <th className="text-center">تاريخ البيع</th>
              <th className="text-center">المندوب</th>
              <th className="text-start px-2">اسم العميل</th>
              <th className="text-center">الهاتف</th>
              <th className="text-center">المنطقة</th>
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
                    isSelected={selectedIds.includes(r.id)}
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
