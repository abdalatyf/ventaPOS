import React, { useState } from 'react';
import { IconClockHour4, IconPlus, IconX } from '@tabler/icons-react';
import { fmt } from '../utils/formatUtils';

export default function CommissionModal({ show, item, history, loading, onClose, onAddCommission, onDeleteCommission }) {
  const [newComm, setNewComm] = useState({ 
    amount: '', 
    month: new Date().getMonth() + 1, 
    year: new Date().getFullYear() 
  });

  if (!show || !item) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newComm.amount) return;
    onAddCommission({
      amount: fmt(newComm.amount),
      month: fmt(newComm.month),
      year: fmt(newComm.year)
    });
    setNewComm({ amount: '', month: new Date().getMonth() + 1, year: new Date().getFullYear() });
  };

  return (
    <div className="modal modal-blur fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content">
          <div className="modal-header bg-info-lt">
            <h5 className="modal-title d-flex align-items-center">
              <IconClockHour4 className="me-2" />
              سجل عمولة: <strong className="ms-2">{item.name}</strong>
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <form onSubmit={handleSubmit} className="mb-4 p-3 border rounded bg-light">
              <div className="fw-bold mb-2">إضافة عمولة جديدة:</div>
              <div className="row g-2 align-items-end">
                <div className="col-4">
                  <label className="form-label small">المبلغ</label>
                  <input type="number" className="form-control form-control-sm" value={newComm.amount} onChange={e => setNewComm({...newComm, amount: e.target.value})} step="0.01" required />
                </div>
                <div className="col-3">
                  <label className="form-label small">شهر</label>
                  <select className="form-select form-select-sm" value={newComm.month} onChange={e => setNewComm({...newComm, month: e.target.value})}>
                    {[...Array(12)].map((_, i) => <option key={i+1} value={i+1}>{i+1}</option>)}
                  </select>
                </div>
                <div className="col-3">
                  <label className="form-label small">سنة</label>
                  <input type="number" className="form-control form-control-sm" value={newComm.year} onChange={e => setNewComm({...newComm, year: e.target.value})} required />
                </div>
                <div className="col-2">
                  <button type="submit" className="btn btn-primary btn-sm w-100"><IconPlus size={16}/></button>
                </div>
              </div>
            </form>

            <div className="fw-bold mb-2">السجل التاريخي:</div>
            <table className="table table-sm table-bordered text-center">
              <thead className="table-light">
                <tr>
                  <th>التاريخ</th>
                  <th>المبلغ</th>
                  <th>حذف</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="3" className="text-center py-4"><div className="spinner-border spinner-border-sm text-primary"></div></td></tr>
                ) : history.length === 0 ? (
                  <tr><td colSpan="3" className="text-muted">لا يوجد سجلات</td></tr>
                ) : (
                  history.map(ch => (
                    <tr key={ch.id}>
                      <td>{ch.month}/{ch.year}</td>
                      <td className="text-primary fw-bold">{ch.amount}</td>
                      <td>
                        <button className="btn btn-ghost-danger btn-sm p-1" onClick={() => onDeleteCommission(ch.id)}>
                          <IconX size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
