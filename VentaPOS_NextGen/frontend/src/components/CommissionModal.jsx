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
      amount: newComm.amount,
      month: newComm.month,
      year: newComm.year
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
              سجل المندبة: <strong className="ms-2">{item.name}</strong>
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <form onSubmit={handleSubmit} className="mb-4 p-3 border rounded bg-light">
              <div className="fw-bold mb-2">تغيير المندبة بدءا من شهر معين:</div>
              <div className="row g-2 align-items-end">
                <div className="col-4">
                  <label className="form-label small">المبلغ</label>
                  <input type="number" className="form-control form-control-sm" value={newComm.amount} onChange={e => setNewComm({...newComm, amount: e.target.value})} step="0.01" required />
                </div>
                <div className="col-3">
                  <label className="form-label small">شهر</label>
                  <input 
                    type="number" 
                    className="form-control form-control-sm" 
                    value={newComm.month} 
                    min="1" 
                    max="12" 
                    placeholder="شهر" 
                    onChange={e => setNewComm({...newComm, month: e.target.value === '' ? '' : Number(e.target.value)})} 
                    required 
                  />
                </div>
                <div className="col-3">
                  <label className="form-label small">سنة</label>
                  <input 
                    type="number" 
                    className="form-control form-control-sm" 
                    value={newComm.year} 
                    min="2000" 
                    max="2100" 
                    placeholder="سنة" 
                    onChange={e => setNewComm({...newComm, year: e.target.value === '' ? '' : Number(e.target.value)})} 
                    required 
                  />
                </div>
                <div className="col-2">
                  <button type="submit" className="btn btn-primary btn-sm w-100"><IconPlus size={16}/></button>
                </div>
              </div>
            </form>

            <div className="fw-bold mb-2">سجل تغيير المندبة:</div>
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
                      <td>{ch.year}/{ch.month}</td>
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
