import React from 'react';

export default function POSInstallmentBox({
  isCashSale,
  downPayment,
  setDownPayment,
  installmentDesc,
  systems,
  handleSystemChange,
  toEnglish,
  fmt
}) {
  return (
    <div className="card-body p-3">
      {/* Installment Mode */}
      {!isCashSale && (
        <>
          <div className="row g-2 mb-3 align-items-center">
            <div className="col-auto">
              <label className="col-form-label fw-bold text-dark">المقدم</label>
            </div>
            <div className="col-3">
              <input 
                type="text" 
                className="form-control py-1 fs-3 border-secondary-subtle text-success fw-bold text-center"
                value={downPayment}
                onChange={e => setDownPayment(e.target.value)}
                style={{ borderColor: '#adb5bd' }} 
              />
            </div>
            <div className="col-auto">
              <label className="col-form-label fw-bold text-dark">نظام القسط</label>
            </div>
            <div className="col">
              <input 
                type="text" 
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-muted bg-light"
                value={installmentDesc}
                readOnly
                disabled
                style={{ borderColor: '#adb5bd' }} 
              />
            </div>
          </div>

          {/* 3x2 Installment Calculator with Placeholders */}
          <div className="row g-2 mb-3">
            {systems.map((sys, idx) => (
              <div key={idx} className="col-4">
                <div className="border rounded p-2 text-center bg-light" style={{ borderColor: '#adb5bd' }}>
                  <div className="text-dark small fw-bold mb-1">نظام {idx + 1}</div>
                  <input 
                    type="text" 
                    className="form-control py-1 fs-3 border-secondary-subtle text-center mb-1 fw-bold"
                    value={sys.count}
                    placeholder={`شهر ${idx + 1}`}
                    onChange={e => handleSystemChange(idx, 'count', e.target.value)}
                    style={{ borderColor: '#adb5bd' }} 
                  />
                  <input 
                    type="text" 
                    className="form-control py-1 fs-3 border-secondary-subtle text-center text-primary fw-bold"
                    value={sys.amount}
                    placeholder={`مبلغ ${idx + 1}`}
                    onChange={e => handleSystemChange(idx, 'amount', e.target.value)}
                    style={{ borderColor: '#adb5bd' }} 
                  />
                  {sys.count && sys.amount && (
                    <div className="text-success small mt-1 fw-bold border-top pt-1" style={{ borderColor: '#adb5bd' }}>
                      {fmt((parseInt(toEnglish(sys.count))||0)*(parseFloat(toEnglish(sys.amount))||0))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Cash Mode */}
      {isCashSale && (
        <div className="alert alert-success py-3 text-center mb-3 fw-bold border border-success">
          كاش — لا توجد أقساط ومقدم
        </div>
      )}
    </div>
  );
}
