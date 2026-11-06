import React from 'react';
import { IconReceipt, IconTrash, IconPrinter } from '@tabler/icons-react';
import PurchaseInvoiceRow from './PurchaseInvoiceRow';

export default function PurchaseTable({
  invoices,
  loading,
  totalInvoicesCount,
  totalAmountSum,
  selectedIds,
  globalAllIds,
  toggleSelect,
  toggleSelectAll,
  handleBulkDelete,
  handleContextMenu,
  handleOpenPrintModal,
  formatCurrency,
  getSupplierName,
  lastRowElementRef,
  loadingMore
}) {
  return (
    <div className="card shadow-sm border-0 rounded bg-white mt-3 has-sticky-toolbar">
      <div className="card-header bg-light d-flex flex-wrap justify-content-between align-items-center py-2 gap-2 rounded-top border-bottom border-secondary-subtle sticky-toolbar">
        <div className="d-flex align-items-center gap-3">
          <div className="text-dark fw-bold fs-3 d-flex align-items-center gap-2">
            نتائج البحث
            <span className="badge bg-primary text-white rounded-pill px-2 py-1">{totalInvoicesCount} فاتورة</span>
          </div>
          
          {invoices.length > 0 && (
            <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-3 ms-1">
              {selectedIds.length > 0 ? (
                <>
                  <span className="fw-bold me-2">تم تحديد {selectedIds.length}</span>
                  {handleOpenPrintModal && (
                    <button className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" onClick={() => handleOpenPrintModal(selectedIds)}>
                      <IconPrinter size={16} /> طباعة محددة
                    </button>
                  )}
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
            <span className="text-danger fw-bolder fs-4">{formatCurrency(totalAmountSum)}</span>
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
        <div>
          <table className="table table-sm table-bordered table-vcenter table-hover table-sticky-header text-nowrap tabular-nums mb-0">
            <thead>
              <tr>
                <th className="text-center w-1">
                  <input 
                    type="checkbox" 
                    className="form-check-input" 
                    checked={invoices.length > 0 && selectedIds.length === (globalAllIds.length > 0 ? globalAllIds.length : invoices.length)} 
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
              {invoices.map((r, index) => {
                const isLast = index === invoices.length - 1;
                return (
                  <PurchaseInvoiceRow 
                    key={r.id || r.local_id || index}
                    r={r}
                    index={index}
                    isSelected={selectedIds.includes(r.id)}
                    toggleSelect={toggleSelect}
                    handleContextMenu={handleContextMenu}
                    formatCurrency={formatCurrency}
                    getSupplierName={getSupplierName}
                    innerRef={isLast ? lastRowElementRef : null}
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
