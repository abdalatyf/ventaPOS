import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconSearch, IconRefresh } from '@tabler/icons-react';

export default function PurchaseFilterToolbar({
  showFilters,
  filters,
  handleFilterChange,
  handleSelectChange,
  supplierSearchQuery,
  handleSupplierQueryChange,
  handleSupplierSelect,
  fetchSupplierSuggestions,
  handleSearchSubmit,
  handleResetFilters,
  loading
}) {
  if (!showFilters) return null;

  return (
    <div className="card shadow-sm border-0 mb-3 bg-white">
      <div className="card-body p-3">
        <form onSubmit={handleSearchSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '0.75rem', alignItems: 'center' }}>
            
            {/* Row 1: Invoice Type */}
            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '80px' }}>نوع الفاتورة</span>
                <select className="form-select fw-bold border-secondary-subtle" name="invoice_type" value={filters.invoice_type} onChange={handleSelectChange}>
                  <option value="ALL">الكل</option>
                  <option value="PURCHASE">فاتورة شراء</option>
                  <option value="RETURN">مرتجع للمورد</option>
                </select>
              </div>
            </div>

            {/* Invoice Number */}
            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>رقم الفاتورة</span>
                <input type="text" className="form-control fw-bold border-secondary-subtle text-center" dir="ltr" name="invoice_number" value={filters.invoice_number} onChange={handleFilterChange} />
              </div>
            </div>

            {/* Month */}
            <div style={{ gridColumn: 'span 1' }}>
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الشهر</span>
                <input
                  type="number"
                  min="1"
                  max="12"
                  className="form-control fw-bold border-secondary-subtle text-center px-1"
                  name="month"
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
                  min="2000"
                  max="2100"
                  className="form-control fw-bold border-secondary-subtle text-center px-1"
                  name="year"
                  placeholder="الكل"
                  value={filters.year}
                  onChange={handleFilterChange}
                />
              </div>
            </div>

            {/* Supplier Autocomplete */}
            <div style={{ gridColumn: 'span 2' }}>
              <div className="input-group input-group-sm flex-nowrap">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle" style={{ width: '70px' }}>المورد</span>
                <Autocomplete
                  value={supplierSearchQuery}
                  onChange={handleSupplierQueryChange}
                  onSelect={handleSupplierSelect}
                  fetchSuggestions={fetchSupplierSuggestions}
                  placeholder="جميع الموردين"
                  className="form-control form-control-sm fw-bold border-secondary-subtle"
                />
              </div>
            </div>

            {/* Submit / Reset Buttons */}
            <div style={{ gridColumn: 'span 8' }} className="d-flex align-items-center gap-2 justify-content-end mt-2">
              <button type="button" className="btn btn-outline-secondary px-4 fw-bold fs-4 py-1" onClick={handleResetFilters} disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                <IconRefresh size={16} className="me-1" />
                إعادة ضبط
              </button>
              <button type="submit" className="btn btn-primary px-5 fw-bold fs-4 py-1 border-secondary-subtle" disabled={loading} style={{ border: '1px solid #adb5bd' }}>
                <IconSearch size={16} className="me-1" />
                {loading ? 'جاري البحث...' : 'بحث'}
              </button>
            </div>

          </div>
        </form>
      </div>
    </div>
  );
}
