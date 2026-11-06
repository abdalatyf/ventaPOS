import React from 'react';
import SuggestionList from './SuggestionList';

export default function PurchaseHeader({
  invoiceType,
  setInvoiceType,
  setItems,
  supplierRef,
  supplierQuery,
  setSupplierQuery,
  setSupplierId,
  triggerSuggestions,
  handleKeyDown,
  blurTimerRef,
  suppliers,
  activeInput,
  setActiveInput,
  suggestions,
  setSuggestions,
  activeIndex,
  handleSuggestionSelect,
  monthRef,
  yearRef,
  prodQueryRef,
  invoiceMonth,
  setInvoiceMonth,
  invoiceYear,
  setInvoiceYear,
  handleCartKD
}) {
  return (
    <div className="card shadow-sm mb-2" style={{ position: 'relative', zIndex: 30 }}>
      <div className="card-body p-3">
        <div className="row g-2 align-items-center">
          
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">نوع الفاتورة</label>
          </div>
          <div className="col-auto">
            <div className="d-flex gap-3 align-items-center h-100 px-2 py-1 border rounded bg-light border-secondary-subtle">
              <label className="form-check m-0 cursor-pointer d-flex align-items-center gap-1">
                <input 
                  className="form-check-input mt-0" 
                  type="radio" 
                  name="invoiceType" 
                  checked={invoiceType === 'PURCHASE'} 
                  onChange={() => setInvoiceType('PURCHASE')} 
                />
                <span className="form-check-label fw-bold text-success fs-4">شراء</span>
              </label>
              <label className="form-check m-0 cursor-pointer d-flex align-items-center gap-1">
                <input 
                  className="form-check-input mt-0" 
                  type="radio" 
                  name="invoiceType" 
                  checked={invoiceType === 'RETURN'} 
                  onChange={() => {
                    setInvoiceType('RETURN');
                    setItems([]);
                  }} 
                />
                <span className="form-check-label fw-bold text-danger fs-4">مرتجع</span>
              </label>
            </div>
          </div>

          <div className="col-auto ms-2">
            <label className="col-form-label fw-bold text-dark">المورد</label>
          </div>
          <div className="col d-flex align-items-center">
            <div className="position-relative flex-grow-1">
              <input
                type="text"
                ref={supplierRef}
                className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
                value={supplierQuery}
                autoComplete="off"
                onChange={e => {
                  setSupplierQuery(e.target.value);
                  setSupplierId('');
                  triggerSuggestions(e.target.value, 'supplier');
                }}
                onKeyDown={e => handleKeyDown(e, 'supplier')}
                onBlur={() => {
                  blurTimerRef.current = setTimeout(() => {
                    if (supplierQuery.trim() !== '') {
                      const exactMatch = suppliers.find(s => s.name === supplierQuery.trim());
                      if (exactMatch) {
                        setSupplierId(exactMatch.id);
                        setSupplierQuery(exactMatch.name);
                      }
                    }
                    setSuggestions([]);
                    setActiveInput('');
                  }, 200);
                }}
                placeholder="ابحث عن مورد..."
                onFocus={() => triggerSuggestions(supplierQuery, 'supplier')}
                style={{ borderColor: '#adb5bd' }}
              />
              <SuggestionList
                open={activeInput === 'supplier'}
                suggestions={suggestions}
                activeIndex={activeIndex}
                onSelect={s => handleSuggestionSelect(s, 'supplier')}
              />
            </div>
          </div>

          <div className="col-auto ms-2">
            <label className="col-form-label fw-bold text-dark">الشهر</label>
          </div>
          <div className="col-1">
            <input 
              ref={monthRef}
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
              value={invoiceMonth} 
              min="1"
              max="12"
              onChange={(e) => {
                const v = parseInt(e.target.value);
                if (v >= 1 && v <= 12) setInvoiceMonth(v);
                else if (e.target.value === '') setInvoiceMonth('');
              }} 
              onKeyDown={(e) => handleCartKD(e, yearRef)}
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>
          <div className="col-auto">
            <label className="col-form-label fw-bold text-dark">السنة</label>
          </div>
          <div className="col-1">
            <input 
              ref={yearRef}
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
              value={invoiceYear} 
              min="2000"
              onChange={(e) => setInvoiceYear(e.target.value)} 
              onKeyDown={(e) => handleCartKD(e, prodQueryRef)}
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>

        </div>
      </div>
    </div>
  );
}
