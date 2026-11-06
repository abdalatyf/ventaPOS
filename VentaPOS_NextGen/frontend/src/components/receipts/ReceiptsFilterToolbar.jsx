import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconRefresh } from '@tabler/icons-react';

export default function ReceiptsFilterToolbar({
  filters,
  handleFilterChange,
  handleSelectChange,
  salespersonName,
  setSalespersonName,
  setFilters,
  fetchReceipts,
  fetchSalespersonSuggestions,
  handleResetFilters,
  loading
}) {
  return (
    <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
      <div className="card-body p-3">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
          
          {/* Month */}
          <div style={{ gridColumn: 'span 1' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الشهر</span>
              <input 
                type="number" 
                className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                name="month" 
                min="1" 
                max="12" 
                placeholder="الكل"
                value={filters.month} 
                onChange={handleFilterChange} 
              />
            </div>
          </div>

          {/* Year */}
          <div style={{ gridColumn: 'span 1' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">السنة</span>
              <input 
                type="number" 
                className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                name="year" 
                placeholder="الكل"
                value={filters.year} 
                onChange={handleFilterChange} 
              />
            </div>
          </div>

          {/* Receipt From */}
          <div style={{ gridColumn: 'span 1' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">من</span>
              <input 
                type="number" 
                className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                name="receipt_from" 
                value={filters.receipt_from} 
                onChange={handleFilterChange} 
              />
            </div>
          </div>

          {/* Receipt To */}
          <div style={{ gridColumn: 'span 1' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">إلى</span>
              <input 
                type="number" 
                className="form-control fw-bold border-secondary-subtle px-1 text-center" 
                name="receipt_to" 
                value={filters.receipt_to} 
                onChange={handleFilterChange} 
              />
            </div>
          </div>

          {/* Salesperson Autocomplete */}
          <div style={{ gridColumn: 'span 3' }}>
            <div className="input-group input-group-sm flex-nowrap">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المندوب</span>
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
                  setSalespersonName(item.name);
                  setFilters(prev => {
                    const newFilters = { ...prev, salesperson_id: item.id || item.local_id };
                    fetchReceipts(newFilters);
                    return newFilters;
                  });
                }}
                fetchSuggestions={fetchSalespersonSuggestions}
                placeholder="جميع البائعين"
                className="form-control fw-bold border-secondary-subtle"
              />
            </div>
          </div>

          {/* Sale Type */}
          <div style={{ gridColumn: 'span 1' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
              <select className="form-select fw-bold border-secondary-subtle px-1 text-center" name="sale_type" value={filters.sale_type} onChange={handleSelectChange}>
                <option value="ALL">الكل</option>
                <option value="CASH">كاش</option>
                <option value="INSTALLMENT">قسط</option>
              </select>
            </div>
          </div>

          {/* Phone */}
          <div style={{ gridColumn: 'span 2' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الهاتف</span>
              <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="phone" value={filters.phone} onChange={handleFilterChange} />
            </div>
          </div>

          {/* Customer Name */}
          <div style={{ gridColumn: 'span 3' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>العميل</span>
              <input type="text" className="form-control fw-bold border-secondary-subtle" name="customer_name" value={filters.customer_name} onChange={handleFilterChange} />
            </div>
          </div>

          {/* Address */}
          <div style={{ gridColumn: 'span 3' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العنوان</span>
              <input type="text" className="form-control fw-bold border-secondary-subtle" name="address" value={filters.address} onChange={handleFilterChange} />
            </div>
          </div>

          {/* Area */}
          <div style={{ gridColumn: 'span 2' }}>
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المنطقة</span>
              <input type="text" className="form-control fw-bold border-secondary-subtle" name="area" value={filters.area} onChange={handleFilterChange} />
            </div>
          </div>

          {/* Reset button */}
          <div style={{ gridColumn: 'span 2' }} className="d-flex align-items-center gap-2 justify-content-end">
            <button type="button" className="btn btn-outline-secondary w-100 fw-bold fs-4 py-1" onClick={handleResetFilters} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
              <IconRefresh size={16} className="me-1" />
              إعادة ضبط
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
