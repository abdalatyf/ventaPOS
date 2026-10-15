/**
 * formatUtils.js — Unified Formatting Utilities for VentaPOS NextGen
 * 
 * SSoT: REPORTS_AGREEMENT.md, UI_UX_RULES.md §6.3, PROJECT.md
 */

/**
 * (DEPRECATED) Converts Western ASCII digits (0-9) to Arabic-Indic digits (٠-٩).
 * Left in place temporarily to prevent import errors, but returns Western digits.
 * 
 * @param {string|number|null|undefined} val 
 * @returns {string}
 */
export const toArabic = (val) => {
  if (val === null || val === undefined) return '';
  return String(val);
};

/**
 * Converts Arabic-Indic digits (٠-٩) and Eastern Arabic digits (۰-۹) back to Western ASCII digits (0-9).
 * Also converts Arabic decimal separator (٫) to '.' and Arabic thousands separator (،) to ','.
 * Kept for backward compatibility in case old Arabic commas linger in inputs.
 * 
 * @param {string|number|null|undefined} val 
 * @returns {string}
 */
export const toEnglish = (val) => {
  if (val === null || val === undefined) return '';
  const map = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    '٫': '.', '،': ','
  };
  return String(val).replace(/[٠-٩۰-۹٫،]/g, (d) => map[d] || d);
};

/**
 * Safely parses any numeric input (Western or Arabic digits, strings with commas, floats) into a JavaScript Number.
 * Returns 0 if invalid, null, undefined, or NaN.
 * 
 * @param {string|number|null|undefined} val 
 * @returns {number}
 */
export const parseNumber = (val) => {
  if (val === null || val === undefined || val === '') return 0;
  if (typeof val === 'number') return isNaN(val) || !isFinite(val) ? 0 : val;
  
  // Normalize Arabic digits, decimal point (٫), and strip thousand separators
  let str = toEnglish(String(val)).trim();
  str = str.replace(/,/g, '');
  const cleanVal = str.replace(/[^\d.-]/g, '');
  const num = parseFloat(cleanVal);
  return isNaN(num) || !isFinite(num) ? 0 : num;
};

/**
 * Formats integers with comma thousand separators (e.g. 1,500).
 * Rounds floating point values using Math.round.
 * Handles null, undefined, NaN, and empty strings safely by returning "0".
 * 
 * @param {string|number|null|undefined} val 
 * @returns {string}
 */
export const fmtNum = (val) => {
  if (val === null || val === undefined || val === '') return '0';
  const num = parseNumber(val);
  if (isNaN(num) || !isFinite(num)) return '0';
  const rounded = Math.round(num);
  return rounded.toLocaleString('en-US');
};

/**
 * Returns localized YYYY/MM string with Western digits (e.g. "2026/08").
 * Uses leading zero for single-digit months.
 * 
 * @param {number|string|null|undefined} month 
 * @param {number|string|null|undefined} year 
 * @returns {string}
 */
export const formatMMYYYY = (month, year) => {
  if (!month && !year) return '';
  const cleanM = month ? toEnglish(String(month)).trim() : '';
  const cleanY = year ? toEnglish(String(year)).trim() : '';
  
  const parsedM = cleanM && !isNaN(Number(cleanM)) ? parseInt(cleanM, 10) : cleanM;
  const parsedY = cleanY && !isNaN(Number(cleanY)) ? cleanY : cleanY;
  
  if (parsedM && parsedY) {
    const paddedM = String(parsedM).padStart(2, '0');
    return `${parsedY}/${paddedM}`;
  }
  if (parsedM) return String(parsedM).padStart(2, '0');
  if (parsedY) return String(parsedY);
  return '';
};

/**
 * Formats monetary amounts with 2 decimal places and standard comma (,).
 * 
 * @param {string|number|null|undefined} val 
 * @returns {string}
 */
export const formatMoney = (val) => {
  const num = parseNumber(val);
  const formatted = num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return formatted;
};

// Aliases for backward compatibility
export const toArabicDigits = toArabic;
export const formatInteger = fmtNum;
export const formatMonthYear = formatMMYYYY;
export const fmt = fmtNum;

export default {
  toArabic,
  toEnglish,
  parseNumber,
  fmtNum,
  formatMMYYYY,
  formatMoney,
  toArabicDigits,
  formatInteger,
  formatMonthYear,
  fmt
};