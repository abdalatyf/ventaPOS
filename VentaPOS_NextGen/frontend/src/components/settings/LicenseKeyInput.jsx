import React, { useRef } from 'react';
import { IconKey } from '@tabler/icons-react';

export default function LicenseKeyInput({ onSubmit, isLoading }) {
  const inputRefs = [useRef(), useRef(), useRef(), useRef()];

  const handleChange = (e, index) => {
    const value = e.target.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    e.target.value = value;
    if (value.length === 4 && index < 3) {
      inputRefs[index + 1].current.focus();
    }
  };

  const handleKeyDown = (e, index) => {
    if (e.key === 'Backspace' && e.target.value.length === 0 && index > 0) {
      e.preventDefault();
      const prevInput = inputRefs[index - 1].current;
      prevInput.focus();
      prevInput.value = prevInput.value.slice(0, -1);
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').toUpperCase().replace(/[^A-Z0-9]/g, '');
    let start = 0;
    
    inputRefs.forEach((ref) => {
      if (start < pasteData.length && ref.current) {
        ref.current.value = pasteData.substring(start, start + 4);
        start += 4;
      }
    });
    
    const filledCount = Math.ceil(pasteData.length / 4);
    const focusIndex = Math.min(filledCount - 1, 3);
    if (focusIndex >= 0 && inputRefs[focusIndex].current) {
      inputRefs[focusIndex].current.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const parts = inputRefs.map(ref => ref.current?.value || '');
    const code = parts.join('-');
    if (onSubmit) {
      onSubmit(code);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="text-center">
      <label className="mb-4 text-muted fw-bold fs-5">أدخل كود التفعيل / التجديد:</label>
      <div 
        className="mb-4 d-flex gap-3 justify-content-center flex-wrap" 
        style={{ direction: 'ltr' }}
      >
        {inputRefs.map((ref, i) => (
          <React.Fragment key={i}>
            <input
              ref={ref}
              type="text"
              className="form-control text-center"
              maxLength={4}
              placeholder="XXXX"
              onChange={(e) => handleChange(e, i)}
              onKeyDown={(e) => handleKeyDown(e, i)}
              onPaste={handlePaste}
              style={{ 
                width: '100px', height: '60px', fontSize: '1.5rem', 
                fontWeight: 'bold', textTransform: 'uppercase', 
                letterSpacing: '3px', backgroundColor: '#f8f9fa',
                border: '2px solid #ced4da', borderRadius: '8px',
                transition: 'all 0.2s ease-in-out'
              }}
              onFocus={(e) => {
                e.target.style.backgroundColor = '#fff';
                e.target.style.borderColor = '#198754';
                e.target.style.transform = 'scale(1.05)';
              }}
              onBlur={(e) => {
                e.target.style.backgroundColor = '#f8f9fa';
                e.target.style.borderColor = '#ced4da';
                e.target.style.transform = 'scale(1)';
              }}
            />
            {i < 3 && <span className="align-self-center fs-2 fw-bold text-secondary">-</span>}
          </React.Fragment>
        ))}
      </div>
      <button 
        type="submit" 
        className="btn btn-success px-5 py-3 fw-bold fs-5 rounded-pill shadow"
        disabled={isLoading}
      >
        <IconKey className="me-2" />
        {isLoading ? 'جاري التنفيذ...' : 'تنفيذ العملية'}
      </button>
    </form>
  );
}
