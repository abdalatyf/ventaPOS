import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconRefresh } from '@tabler/icons-react';
import api from '../../api';

function clampNumberFilter(rawVal, min, max) {
  const s = String(rawVal ?? '').trim();
  if (!s) return '';
  const n = parseInt(s, 10);
  if (isNaN(n)) return '';
  let clamped = n;
  if (min !== undefined && clamped < min) clamped = min;
  if (max !== undefined && clamped > max) clamped = max;
  return String(clamped);
}

export function ReceiptsFilterRow1({
  filters,
  handleFilterChange,
  handleSelectChange,
}) {
  const handleMonthBlur = () => {
    const clamped = clampNumberFilter(filters.month, 1, 12);
    if (clamped !== String(filters.month ?? '')) {
      handleFilterChange({ target: { name: 'month', value: clamped } });
    }
  };

  const handleYearBlur = () => {
    const clamped = clampNumberFilter(filters.year, 2020, 2100);
    if (clamped !== String(filters.year ?? '')) {
      handleFilterChange({ target: { name: 'year', value: clamped } });
    }
  };

  const handleFromBlur = () => {
    let clamped = clampNumberFilter(filters.receipt_from, 1);
    const toVal = clampNumberFilter(filters.receipt_to, 1);
    if (clamped && toVal && Number(clamped) > Number(toVal)) {
      clamped = toVal;
    }
    if (clamped !== String(filters.receipt_from ?? '')) {
      handleFilterChange({ target: { name: 'receipt_from', value: clamped } });
    }
  };

  const handleToBlur = () => {
    let clamped = clampNumberFilter(filters.receipt_to, 1);
    const fromVal = clampNumberFilter(filters.receipt_from, 1);
    if (clamped && fromVal && Number(clamped) < Number(fromVal)) {
      clamped = fromVal;
    }
    if (clamped !== String(filters.receipt_to ?? '')) {
      handleFilterChange({ target: { name: 'receipt_to', value: clamped } });
    }
  };

  const hasCustomer = Boolean(filters.customer_name && String(filters.customer_name).trim().length > 0);

  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Month */}
      <div style={{ width: '108px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">شهر</span>
          <input 
            type="number"
            min={1}
            max={12}
            inputMode="numeric"
            dir="ltr"
            className="form-control fw-bold border-secondary-subtle px-1 text-center hide-arrows" 
            name="month" 
            placeholder="الكل"
            value={filters.month} 
            onChange={handleFilterChange} 
            onBlur={handleMonthBlur}
          />
        </div>
      </div>

      {/* Year */}
      <div style={{ width: '115px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">سنة</span>
          <input 
            type="number"
            min={2020}
            max={2100}
            inputMode="numeric"
            dir="ltr"
            className="form-control fw-bold border-secondary-subtle px-1 text-center hide-arrows" 
            name="year" 
            placeholder="الكل"
            value={filters.year} 
            onChange={handleFilterChange} 
            onBlur={handleYearBlur}
          />
        </div>
      </div>

      {/* Receipt From */}
      <div style={{ width: '120px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من رقم</span>
          <input 
            type="number"
            min={1}
            inputMode="numeric"
            dir="ltr"
            className="form-control fw-bold border-secondary-subtle px-1 text-center hide-arrows" 
            name="receipt_from" 
            placeholder="الكل"
            value={filters.receipt_from} 
            onChange={handleFilterChange} 
            onBlur={handleFromBlur}
          />
        </div>
      </div>

      {/* Receipt To */}
      <div style={{ width: '120px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى رقم</span>
          <input 
            type="number"
            min={1}
            inputMode="numeric"
            dir="ltr"
            className="form-control fw-bold border-secondary-subtle px-1 text-center hide-arrows" 
            name="receipt_to" 
            placeholder="الكل"
            value={filters.receipt_to} 
            onChange={handleFilterChange} 
            onBlur={handleToBlur}
          />
        </div>
      </div>

      {/* Sale Type */}
      <div style={{ width: '130px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
          <select 
            className="form-select fw-bold border-secondary-subtle px-1 text-center" 
            name="sale_type" 
            value={filters.sale_type} 
            onChange={handleSelectChange}
          >
            <option value="ALL">الكل</option>
            <option value="CASH">كاش</option>
            <option value="INSTALLMENT">قسط</option>
          </select>
        </div>
      </div>

      {/* Customer Name */}
      <div className="flex-grow-1" style={{ minWidth: '180px' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العميل</span>
          <div className="position-relative flex-grow-1" style={{ minWidth: 0 }}>
            <input 
              type="text" 
              className="form-control form-control-sm fw-bold border-secondary-subtle" 
              style={{ paddingLeft: hasCustomer ? '2rem' : undefined }}
              name="customer_name" 
              placeholder="اسم العميل..."
              value={filters.customer_name} 
              onChange={handleFilterChange} 
            />
            {hasCustomer && (
              <span
                className="input-icon-addon cursor-pointer"
                title="مسح الحقل"
                onClick={() => handleFilterChange({ target: { name: 'customer_name', value: '' } })}
                style={{
                  position: 'absolute',
                  left: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 3,
                  cursor: 'pointer',
                  pointerEvents: 'auto',
                  color: '#6c757d',
                  fontSize: '14px',
                  lineHeight: 1,
                  padding: '2px 4px',
                }}
              >
                ✕
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ReceiptsFilterRow2({
  filters,
  handleFilterChange,
  salespersonName,
  setSalespersonName,
  setFilters,
  fetchReceipts,
  fetchSalespersonSuggestions,
  handleResetFilters,
  loading,
}) {
  const hasPhone = Boolean(filters.phone && String(filters.phone).trim().length > 0);
  const hasAddress = Boolean(filters.address && String(filters.address).trim().length > 0);

  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Phone (equal width to Area) */}
      <div className="flex-grow-1" style={{ minWidth: '170px', flexBasis: '0' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الهاتف</span>
          <div className="position-relative flex-grow-1" style={{ minWidth: 0 }}>
            <input 
              type="text" 
              className="form-control form-control-sm fw-bold border-secondary-subtle text-center px-1" 
              style={{ paddingLeft: hasPhone ? '2rem' : undefined }}
              dir="ltr" 
              name="phone" 
              placeholder="رقم الهاتف"
              value={filters.phone} 
              onChange={handleFilterChange} 
            />
            {hasPhone && (
              <span
                className="input-icon-addon cursor-pointer"
                title="مسح الحقل"
                onClick={() => handleFilterChange({ target: { name: 'phone', value: '' } })}
                style={{
                  position: 'absolute',
                  left: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 3,
                  cursor: 'pointer',
                  pointerEvents: 'auto',
                  color: '#6c757d',
                  fontSize: '14px',
                  lineHeight: 1,
                  padding: '2px 4px',
                }}
              >
                ✕
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Area Autocomplete (equal width to Phone) */}
      <div className="flex-grow-1" style={{ minWidth: '170px', flexBasis: '0' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المنطقة</span>
          <Autocomplete
            value={filters.area || ''}
            onChange={(val) => {
              handleFilterChange({ target: { name: 'area', value: val } });
            }}
            onSelect={(item) => {
              if (!item) {
                handleFilterChange({ target: { name: 'area', value: '' } });
                return;
              }
              const selectedArea = typeof item === 'object' ? (item.area || item.name || '') : String(item);
              handleFilterChange({ target: { name: 'area', value: selectedArea } });
            }}
            fetchSuggestions={async (query) => {
              try {
                const res = await api.get('/customer-suggestions/', {
                  params: { field: 'area', term: query || '' }
                });
                const data = res.data || [];
                return data.map(i => typeof i === 'object' ? i : { name: i, id: i });
              } catch {
                return [];
              }
            }}
            placeholder="المنطقة / القرية"
            className="form-control form-control-sm fw-bold border-secondary-subtle px-1"
          />
        </div>
      </div>

      {/* Address */}
      <div className="flex-grow-1" style={{ minWidth: '160px', flexBasis: '0' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العنوان</span>
          <div className="position-relative flex-grow-1" style={{ minWidth: 0 }}>
            <input 
              type="text" 
              className="form-control form-control-sm fw-bold border-secondary-subtle" 
              style={{ paddingLeft: hasAddress ? '2rem' : undefined }}
              name="address" 
              placeholder="العنوان بالتفصيل"
              value={filters.address} 
              onChange={handleFilterChange} 
            />
            {hasAddress && (
              <span
                className="input-icon-addon cursor-pointer"
                title="مسح الحقل"
                onClick={() => handleFilterChange({ target: { name: 'address', value: '' } })}
                style={{
                  position: 'absolute',
                  left: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  zIndex: 3,
                  cursor: 'pointer',
                  pointerEvents: 'auto',
                  color: '#6c757d',
                  fontSize: '14px',
                  lineHeight: 1,
                  padding: '2px 4px',
                }}
              >
                ✕
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Salesperson Autocomplete */}
      <div style={{ width: '220px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المندوب</span>
          <Autocomplete
            value={salespersonName}
            onChange={(val) => {
              setSalespersonName(val);
              if (!val) {
                setFilters(prev => {
                  const newFilters = { ...prev, salesperson_id: '' };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
              }
            }}
            onSelect={(item) => {
              if (!item) {
                setSalespersonName('');
                setFilters(prev => {
                  const newFilters = { ...prev, salesperson_id: '' };
                  fetchReceipts(newFilters);
                  return newFilters;
                });
                return;
              }
              setSalespersonName(item.name || '');
              setFilters(prev => {
                const newFilters = { ...prev, salesperson_id: item.id || item.local_id };
                fetchReceipts(newFilters);
                return newFilters;
              });
            }}
            fetchSuggestions={fetchSalespersonSuggestions}
            placeholder="جميع المناديب"
            className="form-control form-control-sm fw-bold border-secondary-subtle px-1"
          />
        </div>
      </div>

      {/* Reset button */}
      <button 
        type="button" 
        className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1 fw-bold px-3 py-1 flex-shrink-0 border-secondary-subtle" 
        onClick={handleResetFilters} 
        disabled={loading} 
        title="إلغاء الفلاتر وإعادة الضبط"
      >
        <IconRefresh size={14} />
        <span>إلغاء الفلاتر</span>
      </button>
    </div>
  );
}

export default function ReceiptsFilterToolbar(props) {
  return (
    <div className="d-flex flex-column gap-2">
      <ReceiptsFilterRow1 {...props} />
      <ReceiptsFilterRow2 {...props} />
    </div>
  );
}
