import React from 'react';
import { IconAlertTriangle, IconChevronUp, IconChevronDown, IconLoader, IconCheck } from '@tabler/icons-react';

export default function LedgerDeficitForm({
  showDeficitForm,
  setShowDeficitForm,
  deficitForm,
  setDeficitForm,
  handleDeficitSubmit,
  deficitSubmitting
}) {
  return (
    <div className="card shadow-sm border-0 h-100">
      <div className="card-header bg-white py-2 d-flex justify-content-between align-items-center">
        <span className="fw-bold text-dark d-flex align-items-center">
          <IconAlertTriangle size={18} className="me-2 text-warning" />
          تسجيل عجز في البضاعة
          <span className="text-muted small ms-2">— خصم رصيد وقيمة شرائية</span>
        </span>
        <button 
          type="button" 
          className="btn btn-sm btn-outline-warning fw-semibold"
          onClick={() => setShowDeficitForm(!showDeficitForm)}
        >
          {showDeficitForm ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
          <span className="ms-1">{showDeficitForm ? 'إخفاء' : 'تسجيل عجز'}</span>
        </button>
      </div>

      {showDeficitForm && (
        <div className="card-body bg-light-subtle p-3 border-top">
          <form onSubmit={handleDeficitSubmit} className="row g-2 align-items-end">
            <div className="col-3">
              <label className="form-label small mb-1 fw-bold">كمية العجز <span className="text-danger">*</span></label>
              <input 
                type="number" 
                className="form-control form-control-sm" 
                placeholder="مثال: 2"
                min="1"
                value={deficitForm.quantity}
                onChange={(e) => setDeficitForm({ ...deficitForm, quantity: e.target.value })}
                required
                autoFocus
              />
            </div>
            <div className="col-2">
              <label className="form-label small mb-1 fw-bold">شهر <span className="text-danger">*</span></label>
              <input 
                type="number" 
                className="form-control form-control-sm" 
                min="1" 
                max="12"
                value={deficitForm.month}
                onChange={(e) => setDeficitForm({ ...deficitForm, month: e.target.value })}
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
                value={deficitForm.year}
                onChange={(e) => setDeficitForm({ ...deficitForm, year: e.target.value })}
                required
              />
            </div>
            <div className="col-3">
              <label className="form-label small mb-1">السبب / البيان</label>
              <input 
                type="text" 
                className="form-control form-control-sm" 
                placeholder="تلف، كسر، فاقد..."
                value={deficitForm.reason}
                onChange={(e) => setDeficitForm({ ...deficitForm, reason: e.target.value })}
              />
            </div>
            <div className="col-2">
              <button type="submit" className="btn btn-sm btn-warning w-100 fw-bold" disabled={deficitSubmitting}>
                {deficitSubmitting ? <IconLoader className="icon-spin me-1" size={16} /> : <IconCheck size={16} />}
                تأكيد
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
