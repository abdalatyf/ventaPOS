import React from 'react';
import { IconClockHour4, IconChevronUp, IconChevronDown, IconLoader, IconCheck } from '@tabler/icons-react';

export default function LedgerCommissionForm({
  showCommissionForm,
  setShowCommissionForm,
  commForm,
  setCommForm,
  handleCommissionSubmit,
  commSubmitting
}) {
  return (
    <div className="card shadow-sm border-0 h-100">
      <div className="card-header bg-white py-2 d-flex justify-content-between align-items-center">
        <span className="fw-bold text-dark d-flex align-items-center">
          <IconClockHour4 size={18} className="me-2 text-purple" style={{ color: '#6f42c1' }} />
          تعديل المندبة
          <span className="text-muted small ms-2">— تغيير عمولة البيع</span>
        </span>
        <button 
          type="button" 
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setShowCommissionForm(!showCommissionForm)}
        >
          {showCommissionForm ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
          <span className="ms-1">{showCommissionForm ? 'إخفاء' : 'تعديل المندبة'}</span>
        </button>
      </div>

      {showCommissionForm && (
        <div className="card-body bg-light-subtle p-3 border-top">
          <form onSubmit={handleCommissionSubmit} className="row g-2 align-items-end">
            <div className="col-4">
              <label className="form-label small mb-1 fw-bold">المندبة للقطعة <span className="text-danger">*</span></label>
              <input 
                type="number" 
                className="form-control form-control-sm" 
                placeholder="مثال: 50"
                min="0"
                value={commForm.amount}
                onChange={(e) => setCommForm({ ...commForm, amount: e.target.value })}
                required
              />
            </div>
            <div className="col-2">
              <label className="form-label small mb-1 fw-bold">شهر <span className="text-danger">*</span></label>
              <input 
                type="number" 
                className="form-control form-control-sm" 
                min="1" 
                max="12"
                value={commForm.month}
                onChange={(e) => setCommForm({ ...commForm, month: e.target.value })}
                required
              />
            </div>
            <div className="col-2">
              <label className="form-label small mb-1 fw-bold">سنة <span className="text-danger">*</span></label>
              <input 
                type="number" 
                className="form-control form-control-sm" 
                min="2020" 
                max="2100"
                value={commForm.year}
                onChange={(e) => setCommForm({ ...commForm, year: e.target.value })}
                required
              />
            </div>
            <div className="col-4">
              <button type="submit" className="btn btn-sm btn-primary w-100 fw-bold" disabled={commSubmitting}>
                {commSubmitting ? <IconLoader className="icon-spin me-1" size={16} /> : <IconCheck size={16} className="me-1" />}
                تطبيق المندبة
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
