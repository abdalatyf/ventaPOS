import React from 'react';
import { IconTrash } from '@tabler/icons-react';
import SuggestionList from '../purchases/SuggestionList';
import api from '../../api';
import { fmtNum } from '../../utils/formatUtils';

export default function POSItemsTable({
  itemError,
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
  saleMonth,
  saleYear,
  items,
  setItems,
  blurTimerRef,
  qtyRef,
  quantity,
  setQuantity,
  handleCartKD,
  priceRef,
  sellPrice,
  setSellPrice,
  handleAddItem
}) {
  return (
    <div className="card shadow-sm mb-2" style={{ position: 'relative', zIndex: 20 }}>
      {/* Product Entry Bar */}
      <div className="card-body p-2 border-bottom bg-light" style={{ borderColor: '#dee2e6 !important' }}>
        {itemError && <div className="alert alert-danger py-1 mb-2 small fw-bold">{itemError}</div>}
        <div className="row g-2 align-items-center mb-4">
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
                  if (selectedProduct && selectedProduct.value !== val) {
                    setSelectedProduct(null);
                  }
                  triggerSuggestions(val, 'product');
                }}
                onKeyDown={e => handleKeyDown(e, 'product')}
                onFocus={() => triggerSuggestions(productQuery, 'product')}
                onBlur={() => { 
                  if (!selectedProduct && productQuery.trim() !== '') {
                    const exactMatch = suggestions.find(p => p.value === productQuery.trim());
                    const fetchStockForMatch = (match) => {
                      api.get(`/inventory-items/${match.id}/stock/?month=${saleMonth}&year=${saleYear}`)
                         .then(res => {
                           if (res.data && res.data.safe_available_qty !== undefined) {
                             const existing = items.find(i => i.inventory_item === match.id);
                             const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
                             setSelectedProduct({ 
                               ...match, 
                               safe_qty: remaining,
                               bottleneck_month: res.data.bottleneck_month,
                               bottleneck_year: res.data.bottleneck_year
                             });
                           }
                         }).catch(() => {});
                    };

                    if (exactMatch) {
                      fetchStockForMatch(exactMatch);
                    } else {
                      const bId = localStorage.getItem('branchId') || '';
                      api.get(`/product-suggestions/?term=${encodeURIComponent(productQuery.trim())}&month=${saleMonth}&year=${saleYear}&branch_id=${bId}`)
                         .then(res => {
                           const fallbackMatch = res.data.find(p => p.value === productQuery.trim());
                           if (fallbackMatch) fetchStockForMatch(fallbackMatch);
                         }).catch(() => {});
                    }
                  }
                  blurTimerRef.current = setTimeout(() => { setSuggestions([]); setActiveInput(''); }, 200); 
                }}
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
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle text-center fw-bold"
              value={quantity} 
              min="1"
              onChange={e => setQuantity(e.target.value)}
              onKeyDown={e => handleCartKD(e, priceRef)}
              style={{ borderColor: '#adb5bd' }} 
            />
            {selectedProduct && selectedProduct.safe_qty !== undefined && (
              <div className="position-absolute text-success fw-bold mt-1" style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', left: '50%', transform: 'translateX(-50%)' }}>
                متاح: {selectedProduct.safe_qty}
                {selectedProduct.bottleneck_month && (
                  <span className="text-warning ms-1">
                    (مقيد بسبب كمية شهر {selectedProduct.bottleneck_month}/{selectedProduct.bottleneck_year})
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="col-auto">
            <label className="form-label fw-bold text-dark mb-0">السعر</label>
          </div>
          <div className="col-2">
            <input 
              ref={priceRef} 
              type="number" 
              className="form-control py-1 fs-3 border-secondary-subtle text-danger fw-bold text-center"
              value={sellPrice}
              onChange={e => setSellPrice(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddItem(); } }}
              style={{ borderColor: '#adb5bd' }} 
            />
          </div>
          <div className="col-auto">
            <button 
              className="btn btn-success d-flex align-items-center justify-content-center fw-bold p-0" 
              onClick={handleAddItem} 
              style={{ width: '36px', height: '36px', fontSize: '1.5rem', border: '1px solid #adb5bd' }}
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Cart Items Table */}
      <div className="table-responsive" style={{ minHeight: 200, maxHeight: 'calc(100vh - 380px)', overflowY: 'auto' }}>
        <table className="table table-vcenter table-hover table-sm text-nowrap tabular-nums mb-0 table-sticky-header">
          <thead className="table-light border-bottom">
            <tr>
              <th>#</th>
              <th>الصنف</th>
              <th className="text-center">الكمية</th>
              <th className="text-center">السعر</th>
              <th className="text-center">الإجمالي</th>
              <th className="w-1"></th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr><td colSpan="6" className="text-center py-5 text-muted fw-bold">لا توجد أصناف مضافة</td></tr>
            ) : (
              items.map((item, idx) => (
                <tr key={item.id} className="border-bottom">
                  <td className="text-muted small">{idx + 1}</td>
                  <td className="fw-bold text-dark">
                    <div>{item.productName}</div>
                  </td>
                  <td className="text-center fw-bold">{item.quantity}</td>
                  <td className="text-center text-success fw-bold">{fmtNum(item.sell_price)}</td>
                  <td className="text-center text-primary fw-bold">{fmtNum(item.quantity * item.sell_price)}</td>
                  <td>
                    <button 
                      className="btn btn-outline-danger btn-icon btn-sm"
                      onClick={() => setItems(items.filter(i => i.id !== item.id))}
                    >
                      <IconTrash size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
