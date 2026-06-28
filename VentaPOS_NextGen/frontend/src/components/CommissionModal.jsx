import React, { useState } from 'react';

const CommissionModal = ({ show, onClose, onSave }) => {
  const [newCommission, setNewCommission] = useState({ month: '', year: '', amount: 0 });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(newCommission);
    setNewCommission({ month: '', year: '', amount: 0 });
  };

  if (!show) return null;

  return (
    <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              إضافة مندبة جديدة (بأثر رجعي)
            </h5>
            <button type="button" className="btn-close" onClick={onClose} aria-label="Close"></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
               <div className="row">
                  <div className="col-md-6 mb-3">
                     <label className="form-label">الشهر</label>
                     <input type="number" min="1" max="12" className="form-control" placeholder="مثال: 06" value={newCommission.month} onChange={e => setNewCommission({...newCommission, month: e.target.value})} required />
                  </div>
                  <div className="col-md-6 mb-3">
                     <label className="form-label">السنة</label>
                     <input type="number" min="2000" className="form-control" placeholder="مثال: 2026" value={newCommission.year} onChange={e => setNewCommission({...newCommission, year: e.target.value})} required />
                  </div>
                  <div className="col-md-12 mb-3">
                     <label className="form-label">قيمة المندبة (جنيه)</label>
                     <input type="number" step="0.01" className="form-control" value={newCommission.amount} onChange={e => setNewCommission({...newCommission, amount: e.target.value})} required />
                  </div>
               </div>
               <p className="text-muted mb-0 mt-2" style={{ fontSize: '0.85rem' }}>
                 * سيتم تسجيل المندبة في الدفاتر بناءً على الشهر والسنة المحددين (آلة الزمن).
               </p>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-link link-secondary" onClick={onClose}>
                إلغاء
              </button>
              <button type="submit" className="btn btn-primary ms-auto">
                تسجيل المندبة
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CommissionModal;
