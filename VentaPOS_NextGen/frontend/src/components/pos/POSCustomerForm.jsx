import React from 'react';
import SuggestionList from '../purchases/SuggestionList';

const Field = ({ label, children, labelCol = 'col-sm-3', inputCol = 'col-sm-9', className = '' }) => (
  <div className={`row mb-2 align-items-center ${className}`}>
    <label className={`${labelCol} col-form-label fw-bold text-dark pe-1`}>{label}</label>
    <div className={inputCol}>{children}</div>
  </div>
);

export default function POSCustomerForm({
  saleMonth,
  setSaleMonth,
  saleYear,
  setSaleYear,
  salespersonRef,
  salespersonQuery,
  setSalespersonQuery,
  setSalespersonId,
  triggerSuggestions,
  handleKeyDown,
  blurTimerRef,
  salespersons,
  activeInput,
  setActiveInput,
  suggestions,
  setSuggestions,
  activeIndex,
  handleSuggestionSelect,
  keepSalesperson,
  setKeepSalesperson,
  isCashSale,
  custNameRef,
  customerName,
  setCustomerName,
  phoneNumber,
  setPhoneNumber,
  area,
  setArea,
  address,
  setAddress
}) {
  return (
    <div className="card shadow-sm mb-2" style={{ position: 'relative', zIndex: 30 }}>
      <div className="card-body p-3">

        {/* Row 1: Month | Year | Salesperson */}
        <div className="row g-2 mb-2 align-items-center">
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">الشهر</label>
          </div>
          <div className="col-2">
            <input 
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
              value={saleMonth} 
              min="1" 
              max="12" 
              onChange={e => {
                const v = parseInt(e.target.value);
                if (v >= 1 && v <= 12) setSaleMonth(v);
                else if (e.target.value === '') setSaleMonth('');
              }} 
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">السنة</label>
          </div>
          <div className="col-2">
            <input 
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
              value={saleYear} 
              min="2020" 
              onChange={e => setSaleYear(e.target.value)} 
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">المندوب</label>
          </div>
          <div className="col d-flex align-items-center gap-2">
            <div className="position-relative flex-grow-1">
              <input
                type="text"
                ref={salespersonRef}
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                value={salespersonQuery}
                autoComplete="off"
                onChange={e => {
                  setSalespersonQuery(e.target.value);
                  setSalespersonId('');
                  triggerSuggestions(e.target.value, 'salesperson');
                }}
                onKeyDown={e => handleKeyDown(e, 'salesperson')}
                onBlur={() => {
                  blurTimerRef.current = setTimeout(() => {
                    if (salespersonQuery.trim() !== '') {
                      const exactMatch = salespersons.find(s => s.name === salespersonQuery.trim());
                      if (exactMatch) {
                        setSalespersonId(exactMatch.id);
                        setSalespersonQuery(exactMatch.name);
                      }
                    }
                    setSuggestions([]);
                    setActiveInput('');
                  }, 200);
                }}
                placeholder="ابحث عن مندوب..."
                onFocus={() => triggerSuggestions(salespersonQuery, 'salesperson')}
                style={{ borderColor: '#adb5bd' }}
              />
              <SuggestionList
                open={activeInput === 'salesperson'}
                suggestions={suggestions}
                activeIndex={activeIndex}
                onSelect={s => handleSuggestionSelect(s, 'salesperson')}
              />
            </div>
            <div className="form-check m-0 d-flex align-items-center gap-1">
              <input 
                className="form-check-input mt-0" 
                type="checkbox" 
                id="keepSalespersonCheck" 
                checked={keepSalesperson}
                onChange={e => setKeepSalesperson(e.target.checked)}
              />
              <label className="form-check-label fw-bold text-nowrap fs-4" htmlFor="keepSalespersonCheck">
                تثبيت
              </label>
            </div>
          </div>
        </div>

        {/* Rows 2-4: Customer fields (Hidden in cash mode) */}
        {!isCashSale && (
          <>
            {/* Customer Name */}
            <Field label="اسم العميل" labelCol="col-sm-2" inputCol="col-sm-10" className="mb-2">
              <div className="position-relative">
                <input
                  type="text"
                  id="input_name"
                  ref={custNameRef}
                  className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                  value={customerName}
                  autoComplete="off"
                  onChange={e => { setCustomerName(e.target.value); triggerSuggestions(e.target.value, 'name'); }}
                  onKeyDown={e => handleKeyDown(e, 'name')}
                  onFocus={() => triggerSuggestions(customerName, 'name')}
                  onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                  style={{ borderColor: '#adb5bd' }}
                />
                <SuggestionList
                  open={activeInput === 'name'}
                  suggestions={suggestions}
                  activeIndex={activeIndex}
                  onSelect={s => handleSuggestionSelect(s, 'name')}
                />
              </div>
            </Field>

            {/* Phone & Area */}
            <div className="row g-2 mb-2 align-items-center">
              <div className="col-auto">
                <label className="col-form-label fw-bold text-dark">هاتف</label>
              </div>
              <div className="col-4">
                <div className="position-relative">
                  <input
                    type="tel"
                    id="input_phone"
                    className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold"
                    value={phoneNumber}
                    dir="ltr"
                    onChange={e => setPhoneNumber(e.target.value)}
                    onKeyDown={e => handleKeyDown(e, 'phone')}
                    onFocus={() => triggerSuggestions(phoneNumber, 'phone')}
                    onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                    style={{ borderColor: '#adb5bd' }}
                  />
                  <SuggestionList
                    open={activeInput === 'phone'}
                    suggestions={suggestions}
                    activeIndex={activeIndex}
                    onSelect={s => handleSuggestionSelect(s, 'phone')}
                  />
                </div>
              </div>
              <div className="col-auto">
                <label className="col-form-label fw-bold text-dark">المنطقة</label>
              </div>
              <div className="col">
                <div className="position-relative">
                  <input
                    type="text"
                    className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                    id="input_area"
                    value={area}
                    onChange={e => { setArea(e.target.value); triggerSuggestions(e.target.value, 'area'); }}
                    onKeyDown={e => handleKeyDown(e, 'area')}
                    onFocus={() => triggerSuggestions(area, 'area')}
                    onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                    style={{ borderColor: '#adb5bd' }}
                  />
                  <SuggestionList
                    open={activeInput === 'area'}
                    suggestions={suggestions}
                    activeIndex={activeIndex}
                    onSelect={s => handleSuggestionSelect(s, 'area')}
                  />
                </div>
              </div>
            </div>

            {/* Address */}
            <Field label="العنوان" labelCol="col-sm-2" inputCol="col-sm-10" className="mb-0">
              <div className="position-relative">
                <input
                  id="input_address"
                  type="text"
                  className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                  value={address}
                  onChange={e => { setAddress(e.target.value); triggerSuggestions(e.target.value, 'address'); }}
                  onKeyDown={e => handleKeyDown(e, 'address')}
                  onFocus={() => triggerSuggestions(address, 'address')}
                  onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                  style={{ borderColor: '#adb5bd' }}
                />
                <SuggestionList
                  open={activeInput === 'address'}
                  suggestions={suggestions}
                  activeIndex={activeIndex}
                  onSelect={s => handleSuggestionSelect(s, 'address')}
                />
              </div>
            </Field>
          </>
        )}

        {/* Area only in cash mode */}
        {isCashSale && (
          <div className="row g-2 align-items-center">
            <div className="col-auto">
              <label className="col-form-label fw-bold text-dark">المنطقة</label>
            </div>
            <div className="col-5">
              <div className="position-relative">
                <input
                  type="text"
                  className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                  id="input_area"
                  value={area}
                  onChange={e => { setArea(e.target.value); triggerSuggestions(e.target.value, 'area'); }}
                  onKeyDown={e => handleKeyDown(e, 'area')}
                  onFocus={() => triggerSuggestions(area, 'area')}
                  onBlur={() => { blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); }}
                  style={{ borderColor: '#adb5bd' }}
                />
                <SuggestionList
                  open={activeInput === 'area'}
                  suggestions={suggestions}
                  activeIndex={activeIndex}
                  onSelect={s => handleSuggestionSelect(s, 'area')}
                />
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
