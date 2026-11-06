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
    <div className="card shadow-sm border-secondary-subtle mb-3 flex-grow-1">
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
          </tbody>
        </table>
        {loadingMore && (
          <div className="text-center py-3">
            <div className="spinner-border text-primary"></div>
          </div>
        )}
      </div>
    </div>
  );
}
