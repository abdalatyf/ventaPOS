import React from 'react';
import { IconTrash, IconDeviceFloppy } from '@tabler/icons-react';
import { fmtNum } from '../../utils/formatUtils';

export default function PurchaseItemsTable({
  items,
  handleRemoveItem,
  totalAmount,
  handleSaveInvoice,
  saving,
  isEdit
}) {
  return (
    <>
      {/* Cart Table */}
      <div className="table-responsive" style={{ minHeight: 200, maxHeight: 'calc(100vh - 380px)', overflowY: 'auto' }}>
        <table className="table table-sm table-vcenter table-hover card-table text-nowrap tabular-nums m-0 table-sticky-header">
          <thead className="bg-white">
            <tr>
              <th className="fw-bold bg-white text-secondary py-2 fs-5">اسم الصنف</th>
              <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">الكمية</th>
              <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">سعر الشراء</th>
              <th className="text-center fw-bold bg-white text-secondary py-2 fs-5">الإجمالي</th>
              <th className="text-center fw-bold w-1 bg-white text-secondary py-2 fs-5">حذف</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td className="fw-bold text-primary fs-4">{item.productName}</td>
                <td className="text-center fw-bold fs-4" dir="ltr">{item.quantity}</td>
                <td className="text-center fw-bold fs-4" dir="ltr">{fmtNum(item.purchase_price)}</td>
                <td className="text-center fw-bold text-danger fs-4" dir="ltr">{fmtNum(item.quantity * item.purchase_price)}</td>
                <td className="text-center">
                  <button className="btn btn-sm btn-outline-danger fw-bold px-2 py-1" onClick={() => handleRemoveItem(item.id)}>
                    <IconTrash size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan="5" className="text-center text-muted py-5 fw-bold fs-3">
                  لا يوجد أصناف. يرجى إضافة أصناف للفاتورة.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Bottom Card: Totals & Save */}
      <div className="card shadow-sm bg-light border-secondary-subtle mt-2">
        <div className="card-body p-3 d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <div className="fs-2 fw-bold text-dark">الإجمالي:</div>
            <div className="display-6 fw-bolder text-danger" dir="ltr">
              {fmtNum(totalAmount)}
            </div>
          </div>
          <div>
            <button 
              className="btn btn-lg fw-bold shadow-sm d-flex justify-content-center align-items-center gap-2 text-white px-5" 
              style={{ backgroundColor: '#1DA368', borderColor: '#1DA368' }}
              onClick={handleSaveInvoice} 
              disabled={saving || items.length === 0}
            >
              <IconDeviceFloppy size={24} />
              {saving ? 'جاري الحفظ...' : (isEdit ? 'تحديث الفاتورة' : 'حفظ الفاتورة')}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
