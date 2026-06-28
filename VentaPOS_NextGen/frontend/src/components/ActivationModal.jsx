import React, { useState } from 'react';
import { IconKey, IconCheck, IconX } from '@tabler/icons-react';
import api from '../api';

const ActivationModal = ({ isOpen, onClose }) => {
  const [code, setCode] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleActivate = async (e) => {
    e.preventDefault();
    if (!code || code.length !== 16) {
      setErrorMessage('يرجى إدخال كود التفعيل بشكل صحيح (١٦ حرف ورقم).');
      return;
    }
    
    setStatus('loading');
    setErrorMessage('');

    try {
      const response = await api.post('/api/v1/license/activate/', { license_code: code });
      if (response.status === 200) {
        setStatus('success');
        setTimeout(() => {
          onClose(); // Auto close on success
          window.location.reload(); // Reload to refresh state (could be handled via react state but reload is simple and solid for license)
        }, 1500);
      }
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.response?.data?.error || 'التفعيل فشل، راجع الكود وجرب تاني.');
    }
  };

  return (
    <div className="modal modal-blur fade show d-block" tabIndex="-1" role="dialog" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content shadow-lg border-0 rounded-4" style={{ overflow: 'hidden' }}>
          
          <div className="modal-header bg-primary text-white border-0 py-4">
            <div className="d-flex align-items-center">
              <span className="avatar bg-white text-primary rounded-circle me-3">
                <IconKey size={24} />
              </span>
              <div>
                <h5 className="modal-title fw-bold fs-3 mb-0">النظام غير مفعل</h5>
                <p className="mb-0 text-white-50 small">يرجى تفعيل النسخة</p>
              </div>
            </div>
          </div>

          <div className="modal-body p-5">
            <div className="text-center mb-4">
              <h3 className="fw-medium mb-2">دخل كود التفعيل</h3>
              <p className="text-muted">انتهت النسخة التجريبية، يرجى إدخال كود التفعيل للاستمرار في استخدام VentaPOS.</p>
            </div>

            <form onSubmit={handleActivate}>
              <div className="mb-4">
                <label className="form-label fw-bold">كود التفعيل</label>
                <input 
                  type="text" 
                  className={`form-control form-control-lg text-center fw-bold font-monospace tracking-wide ${status === 'error' ? 'is-invalid' : ''}`} 
                  placeholder="XXXX-XXXX-XXXX-XXXX" 
                  value={code}
                  onChange={(e) => {
                    // Auto-format to uppercase and allow only alphanumeric/dashes (formatting logic can be improved)
                    const val = e.target.value.replace(/[^a-zA-Z0-9-]/g, '').toUpperCase();
                    setCode(val);
                    if(status === 'error') setStatus('idle');
                  }}
                  maxLength={19} // 16 chars + 3 dashes
                  autoFocus
                />
                {status === 'error' && (
                  <div className="invalid-feedback d-block mt-2 text-center">
                    {errorMessage}
                  </div>
                )}
              </div>

              <div className="d-grid mt-4">
                <button 
                  type="submit" 
                  className={`btn btn-lg btn-primary fw-bold ${status === 'loading' ? 'btn-loading' : ''} ${status === 'success' ? 'btn-success' : ''}`}
                  disabled={status === 'loading' || status === 'success'}
                >
                  {status === 'success' ? (
                    <><IconCheck className="me-2" /> تم التفعيل بنجاح</>
                  ) : (
                    <><IconKey className="me-2" /> فعل النسخة</>
                  )}
                </button>
              </div>
            </form>
          </div>
          
          <div className="modal-footer bg-light border-0 justify-content-center py-3">
            <span className="text-muted small">
              هل تحتاج إلى مساعدة؟ تواصل مع الدعم الفني.
            </span>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ActivationModal;
