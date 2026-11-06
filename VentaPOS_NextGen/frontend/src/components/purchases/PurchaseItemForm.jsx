import React from 'react';
import { IconShoppingCart } from '@tabler/icons-react';
import SuggestionList from './SuggestionList';
import api from '../../api';

export default function PurchaseItemForm({
  prodQueryRef,
  productQuery,
  setProductQuery,
  selectedProduct,
  setSelectedProduct,
  triggerSuggestions,
  handleKeyDown,
  activeInput,
  setActiveInput,
  suggestions,
  setSuggestions,
  activeIndex,
  handleSuggestionSelect,
  products,
  invoiceType,
  items,
  invoiceMonth,
  invoiceYear,
  blurTimerRef,
  qtyRef,
  quantity,
  setQuantity,
  toEnglish,
  handleCartKD,
  priceRef,
  purchasePrice,
  setPurchasePrice,
  handleAddItem
}) {
  return (
    <div className="card-body p-2 border-bottom bg-light" style={{ borderColor: '#dee2e6 !important', borderRadius: 'var(--bs-border-radius) var(--bs-border-radius) 0 0' }}>
      <div className="row g-2 align-items-center">
        
        <div className="col-auto">
          <label className="form-label fw-bold text-dark mb-0">الصنف</label>
        </div>
        <div className="col">
          <div className="position-relative">
            <input
              ref={prodQueryRef}
              type="text"
              className="form-control py-1 fs-3 border-secondary-subtle fw-bold"
              value={productQuery}
              autoComplete="off"
              onChange={e => {
                const val = e.target.value;
                setProductQuery(val);
                if (selectedProduct && selectedProduct.name !== val) {
                  setSelectedProduct(null);
                }
                triggerSuggestions(val, 'product');
              }}
              onKeyDown={e => handleKeyDown(e, 'product')}
              onFocus={() => triggerSuggestions(productQuery, 'product')}
              onBlur={() => { 
                if (!selectedProduct && productQuery.trim() !== '') {
                  const exactMatch = products.find(p => p.name === productQuery.trim());
                  if (exactMatch) {
                    setSelectedProduct(exactMatch);
                    if (invoiceType === 'RETURN') {
                      api.get(`/inventory-items/${exactMatch.id}/stock/?month=${invoiceMonth}&year=${invoiceYear}`)
                        .then(res => {
                          if (res.data && res.data.safe_available_qty !== undefined) {
                            const existing = items.find(i => i.inventory_item === exactMatch.id);
                            const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
                            setSelectedProduct(prev => prev && prev.id === exactMatch.id ? { 
                              ...prev, 
                              safe_qty: remaining,
                              bottleneck_month: res.data.bottleneck_month,
                              bottleneck_year: res.data.bottleneck_year
                            } : prev);
                          }
                        }).catch(() => {});
                    }
                  }
                }
                blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); 
              }}
              placeholder="ابحث عن صنف..."
              style={{ borderColor: '#adb5bd' }}
            />
            <SuggestionList
              open={activeInput === 'product'}
              suggestions={suggestions}
              activeIndex={activeIndex}
              onSelect={s => handleSuggestionSelect(s, 'product')}
            />
          </div>
        </div>

        <div className="col-auto">
          <label className="form-label fw-bold text-dark mb-0">الكمية</label>
        </div>
        <div className="col-2 position-relative text-center">
          <input 
            ref={qtyRef}
            type="text" 
            className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
            value={quantity} 
            onChange={(e) => setQuantity(toEnglish(e.target.value))} 
            onKeyDown={(e) => handleCartKD(e, priceRef)}
            dir="ltr"
            style={{ borderColor: '#adb5bd' }} 
          />
          {invoiceType === 'RETURN' && selectedProduct && selectedProduct.safe_qty !== undefined && (
            <div className="position-absolute text-success fw-bold mt-1" style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', left: '50%', transform: 'translateX(-50%)' }}>
              متاح: {selectedProduct.safe_qty}
            </div>
          )}
        </div>

        <div className="col-auto">
          <label className="form-label fw-bold text-dark mb-0">سعر الشراء</label>
        </div>
        <div className="col-2">
          <input 
            ref={priceRef}
            type="text" 
            className="form-control py-1 fs-3 border-secondary-subtle fw-bold text-center" 
            value={purchasePrice} 
            onChange={(e) => setPurchasePrice(toEnglish(e.target.value))} 
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddItem();
              }
            }}
            dir="ltr"
            style={{ borderColor: '#adb5bd' }} 
          />
        </div>

        <div className="col-auto">
          <button 
            className="btn btn-primary fw-bold fs-4 d-flex align-items-center gap-1" 
            onClick={handleAddItem}
            style={{ padding: '0.375rem 1rem' }}
          >
            إضافة <IconShoppingCart size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
