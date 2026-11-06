import React from 'react';
import useSmartScroll from '../../hooks/useSmartScroll';
import { IconReceipt, IconPrinter, IconTrash } from '@tabler/icons-react';
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
  handleOpenPrintModal,
  handleBulkDelete,
  handleContextMenu,
  formatCurrency,
  getSupplierName,
  lastRowElementRef,
  loadingMore
}) {
  const { setTableRef } = useSmartScroll();

  return (
    <div className="card shadow-sm border-secondary-subtle rounded bg-white mb-0">
      {/* Row 1 of Table Card: Sticky Toolbar directly above <thead> */}
      <div className="sticky-toolbar border-bottom px-3 d-flex align-items-center justify-content-between gap-2 d-print-none">
        <div className="d-flex align-items-center gap-2">
          <span className="text-secondary fw-bold small">النتائج:</span>
          <span className="badge bg-primary text-white rounded-pill px-2 py-1 tabular-nums">{totalInvoicesCount || 0} فاتورة</span>

          {selectedIds.length > 0 && (
            <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-2 ms-1">
              <span className="fw-bold small me-1">تم تحديد {selectedIds.length}</span>
              {handleOpenPrintModal && (
                <button 
                  className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                  onClick={() => handleOpenPrintModal(selectedIds)}
                >
                  <IconPrinter size={14} /> طباعة محددة
                </button>
              )}
              <button 
                className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={handleBulkDelete}
              >
                <IconTrash size={14} /> حذف محددة
              </button>
            </div>
          )}
        </div>

        <div className="d-flex align-items-center">
          <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2" style={{ borderColor: '#adb5bd' }}>
            <span>إجمالي فواتير الشراء:</span>
            <span className="text-danger fw-bolder fs-4 tabular-nums">{formatCurrency(totalAmountSum || 0)}</span>
          </div>
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
                    isSelected={selectedIds.includes(r.id)}
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
