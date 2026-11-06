import React, { useRef } from 'react';
import { toEnglish } from '../../utils/formatUtils';

/**
 * MonthYearPicker — Shared dual numeric input for Month & Year.
 *
 * Enforces Western ASCII 0-9 digits per GEMINI.md §4.4 and UI_UX_RULES.md §3.5.
 * Strictly avoids browser-native <input type="date"> or <input type="month">.
 */
export default function MonthYearPicker({
  month,
  year,
  onChange,
  disabled = false,
  monthRef = null,
  yearRef = null,
  monthLabel = 'الشهر',
  yearLabel = 'السنة',
  size = 'sm', // 'sm' or 'normal'
  className = '',
  onEnterYear = null,
}) {
  const localYearRef = useRef(null);
  const activeYearRef = yearRef || localYearRef;

  const handleMonthChange = (e) => {
    const raw = toEnglish(e.target.value);
    const clean = raw.replace(/\D/g, '');
    let val = clean ? parseInt(clean, 10) : '';
    if (val !== '' && val > 12) val = 12;
    if (val !== '' && val < 1 && clean.length > 0) val = 1;
    onChange({ month: val, year });
  };

  const handleYearChange = (e) => {
    const raw = toEnglish(e.target.value);
    const clean = raw.replace(/\D/g, '').slice(0, 4);
    const val = clean ? parseInt(clean, 10) : '';
    onChange({ month, year: val });
  };

  const handleMonthKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (activeYearRef.current) {
        activeYearRef.current.focus();
        activeYearRef.current.select?.();
      }
    }
  };

  const handleYearKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (onEnterYear) {
        e.preventDefault();
        onEnterYear(e);
      }
    }
  };

  const inputClass = size === 'sm' ? 'form-control form-control-sm' : 'form-control';

  return (
    <div className={`d-flex align-items-center gap-2 ${className}`} dir="rtl">
      <div className="d-flex align-items-center gap-1">
        {monthLabel && <label className="form-label text-muted small mb-0 text-nowrap">{monthLabel}:</label>}
        <input
          ref={monthRef}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          className={`${inputClass} text-center fw-bold tabular-nums`}
          style={{ width: '60px' }}
          value={month !== undefined && month !== null ? month : ''}
          onChange={handleMonthChange}
          onKeyDown={handleMonthKeyDown}
          placeholder="MM"
          disabled={disabled}
          autoComplete="off"
        />
      </div>

      <span className="text-muted fw-bold">/</span>

      <div className="d-flex align-items-center gap-1">
        {yearLabel && <label className="form-label text-muted small mb-0 text-nowrap">{yearLabel}:</label>}
        <input
          ref={activeYearRef}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          className={`${inputClass} text-center fw-bold tabular-nums`}
          style={{ width: '75px' }}
          value={year !== undefined && year !== null ? year : ''}
          onChange={handleYearChange}
          onKeyDown={handleYearKeyDown}
          placeholder="YYYY"
          disabled={disabled}
          autoComplete="off"
        />
      </div>
    </div>
  );
}
