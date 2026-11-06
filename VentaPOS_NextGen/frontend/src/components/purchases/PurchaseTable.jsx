import React from 'react';
import useSmartScroll from '../../hooks/useSmartScroll';
import { IconReceipt } from '@tabler/icons-react';
import PurchaseInvoiceRow from './PurchaseInvoiceRow';

export default function PurchaseTable({
  invoices,
  loading,
  selectedIds,
  globalAllIds,
  toggleSelect,
  toggleSelectAll,
  handleContextMenu,
  formatCurrency,
  getSupplierName,
  lastRowElementRef,
  loadingMore
}) {
  const { setTableRef } = useSmartScroll();

  return (
    <div className="card shadow-sm border-secondary-subtle rounded bg-white mb-3">
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
