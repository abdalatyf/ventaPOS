import React, { useState } from 'react';
import { IconClipboard, IconCheck } from '@tabler/icons-react';

export default function MachineIdDisplay({ machineId }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(machineId || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card shadow-sm mb-4 border-0">
      <div className="card-header bg-white fw-bold">🆔 بصمة الجهاز (Machine ID)</div>
      <div className="card-body">
        <p className="text-muted small mb-2">انسخ هذا الكود وأرسله للدعم الفني لتفعيل النظام أو الدفع.</p>
        <div className="input-group input-group-lg" style={{ border: '2px dashed #0d6efd', backgroundColor: '#f0f8ff', borderRadius: '10px', padding: '10px' }}>
          <input 
            type="text" 
            className="form-control text-center" 
            value={machineId || ''}
            readOnly
            style={{ fontFamily: "'Consolas', monospace", fontSize: '1.4rem', fontWeight: 900, backgroundColor: 'transparent', border: 'none' }}
          />
          <button 
            className={`btn px-4 fw-bold ${copied ? 'btn-success' : 'btn-primary'}`}
            style={{ borderRadius: '8px' }} 
            type="button"
            onClick={copyToClipboard}
          >
            {copied ? (
              <>تم النسخ <IconCheck size={18} className="ms-1" /></>
            ) : (
              <>نسخ <IconClipboard size={18} className="ms-1" /></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
