import React from 'react';
import { IconDeviceFloppy } from '@tabler/icons-react';

export default function POSTotalsSummary({
  handleSave,
  saving,
  isCashSale,
  items,
  hasItems,
  isBalanced,
  isUnbalanced,
  nextReceiptNumber,
  handleCashToggle,
  totalAmount,
  totalPayments,
  diff,
  fmt
}) {
  const itemsReady = hasItems !== undefined ? hasItems : (items && items.length > 0);

  return (
    <>
      {/* Save Button */}
      <div className="px-3 pb-3">
        <button
          className={`btn btn-lg w-100 fw-bold py-3 border-secondary-subtle ${(isCashSale && itemsReady) || isBalanced ? 'btn-success' : 'btn-secondary'}`}
          onClick={handleSave}
          disabled={saving || (!isCashSale && isUnbalanced) || (!isCashSale && !isBalanced) || (isCashSale && !itemsReady)}
          style={{ border: '1px solid #adb5bd' }}
        >
          {saving
            ? <><span className="spinner-border spinner-border-sm me-1"></span>جاري الحفظ...</>
            : <><IconDeviceFloppy size={20} className="me-1" />تأكيد البيع</>}
        </button>
      </div>

      <div className="card-body p-3 border-top bg-light" style={{ borderColor: '#dee2e6 !important' }}>

        {/* Receipt Number + Sale Type toggle */}
        <div className="row g-2 align-items-center mb-3">
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">رقم الوصل</label>
          </div>
          <div className="col-3">
            <input 
              type="text" 
              className="form-control py-1 fs-3 border-secondary-subtle bg-white text-muted text-center fw-bold" 
              value={nextReceiptNumber || 'تلقائي'} 
              readOnly 
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>
          <div className="col-auto me-auto">
            {/* spacer */}
          </div>
          <div className="col-auto">
            <div className="btn-group border rounded" style={{ borderColor: '#adb5bd' }}>
              <button 
                className={`btn btn-sm px-3 ${isCashSale ? 'btn-success' : 'btn-outline-success'}`}
                onClick={() => handleCashToggle(true)}
              >
                كاش
              </button>
              <button 
                className={`btn btn-sm px-3 ${!isCashSale ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => handleCashToggle(false)}
              >
                قسط
              </button>
            </div>
          </div>
        </div>

        {/* Sales Total | Payments Total | Difference */}
        <div 
          className={`rounded p-2 border ${isBalanced ? 'bg-success-lt border-success' : isUnbalanced ? 'bg-danger-lt border-danger' : 'bg-white'}`} 
          style={!isBalanced && !isUnbalanced ? { borderColor: '#adb5bd' } : {}}
        >
          <div className="row g-0 text-center">
            <div className="col-4 border-end" style={{ borderColor: '#adb5bd !important' }}>
              <div className="text-dark small fw-bold">المبيعات</div>
              <div className="fw-bold text-success fs-3">{fmt(totalAmount)}</div>
            </div>
            {!isCashSale && (
              <>
                <div className="col-4 border-end" style={{ borderColor: '#adb5bd !important' }}>
                  <div className="text-dark small fw-bold">الأقساط والمقدم</div>
                  <div className="fw-bold text-primary fs-3">{fmt(totalPayments)}</div>
                </div>
                <div className="col-4">
                  <div className="text-dark small fw-bold">الفرق</div>
                  <div className={`fw-bold fs-3 ${isBalanced ? 'text-success' : 'text-danger'}`}>
                    {isBalanced ? '✓' : fmt(Math.abs(diff))}
                  </div>
                </div>
              </>
            )}
            {isCashSale && (
              <div className="col-8 d-flex align-items-center justify-content-center">
                <span className="badge bg-success py-2 px-3 fw-bold fs-3">متزن</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </>
  );
}
