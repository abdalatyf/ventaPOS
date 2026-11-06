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
            إجمالي فواتير البيع:{' '}
            <span className="text-danger fw-bolder fs-4">{formatCurrency(totalAmountSum)}</span>
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
        <div ref={setTableRef} className="table-responsive flex-grow-1">
          <table className="table table-sm table-bordered table-vcenter table-hover table-sticky-header text-nowrap tabular-nums mb-0">
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
              {receipts.map((r, index) => {
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
  );
}
