import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconSearch, IconRefresh } from '@tabler/icons-react';

export function PurchaseFilterRow1({
  filters,
  handleFilterChange,
  handleSelectChange
}) {
  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Invoice Type */}
      <div style={{ width: '160px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">النوع</span>
          <select 
            className="form-select fw-bold border-secondary-subtle px-2" 
            name="invoice_type" 
            value={filters.invoice_type} 
            onChange={handleSelectChange}
          >
            <option value="ALL">الكل</option>
            <option value="PURCHASE">شراء</option>
            <option value="RETURN">مرتجع</option>
          </select>
        </div>
      </div>

      {/* Invoice Number */}
      <div style={{ width: '180px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">رقم الفاتورة</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle text-center px-1" 
            dir="ltr" 
            name="invoice_number" 
            value={filters.invoice_number} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Month */}
      <div style={{ width: '120px' }} className="flex-shrink-0">
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
      <div style={{ width: '120px' }} className="flex-shrink-0">
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
    </div>
  );
}

export function PurchaseFilterRow2({
  supplierSearchQuery,
  handleSupplierQueryChange,
  handleSupplierSelect,
  fetchSupplierSuggestions,
  handleSearchSubmit,
  handleResetFilters,
  loading
}) {
  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Supplier Autocomplete */}
      <div className="flex-grow-1" style={{ minWidth: '240px' }}>
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المورد</span>
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

      {/* Reset Button */}
      <button 
        type="button" 
        className="btn btn-outline-secondary btn-sm fw-bold px-3 py-1 flex-shrink-0 d-flex align-items-center gap-1 border-secondary-subtle" 
        onClick={handleResetFilters} 
        disabled={loading}
        title="إعادة ضبط"
      >
        <IconRefresh size={14} />
        <span>إعادة ضبط</span>
      </button>

      {/* Search Submit Button */}
      <button 
        type="button" 
        className="btn btn-primary btn-sm fw-bold px-3 py-1 flex-shrink-0 d-flex align-items-center gap-1 border-secondary-subtle" 
        onClick={handleSearchSubmit} 
        disabled={loading}
      >
        <IconSearch size={14} />
        <span>{loading ? 'بحث...' : 'بحث'}</span>
      </button>
    </div>
  );
}

export default function PurchaseFilterToolbar(props) {
  if (props.showFilters === false) return null;
  return (
    <div className="card shadow-sm border-0 mb-3 bg-white p-3">
      <PurchaseFilterRow1 {...props} />
      <div className="mt-2 pt-2 border-top">
        <PurchaseFilterRow2 {...props} />
      </div>
    </div>
  );
}

