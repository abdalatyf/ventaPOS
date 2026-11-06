import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconSearch, IconRefresh, IconPrinter, IconTrash } from '@tabler/icons-react';

export function PurchaseFilterRow1({
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
  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Invoice Type */}
      <div style={{ width: '130px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">النوع</span>
          <select 
            className="form-select fw-bold border-secondary-subtle px-1" 
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
      <div style={{ width: '130px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">رقم الفاتورة</span>
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
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">الشهر</span>
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
      <div style={{ width: '90px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">السنة</span>
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
      <div className="flex-grow-1" style={{ minWidth: '160px' }}>
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
        className="btn btn-outline-secondary btn-sm fw-bold px-2 py-1 flex-shrink-0 d-flex align-items-center gap-1 border-secondary-subtle" 
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

export function PurchaseFilterRow2({
  totalInvoicesCount,
  selectedIds = [],
  handleOpenPrintModal,
  handleBulkDelete,
  totalAmountSum,
  formatCurrency
}) {
  return (
    <div className="d-flex align-items-center justify-content-between w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Right / Start: Count badge & bulk actions */}
      <div className="d-flex align-items-center gap-2">
        <span className="text-secondary fw-bold small">النتائج:</span>
        <span className="badge bg-primary text-white rounded-pill px-2 py-1 tabular-nums">{totalInvoicesCount} فاتورة</span>

        {selectedIds.length > 0 && (
          <div className="d-flex align-items-center gap-2 border-start border-secondary-subtle ps-2 ms-1">
            <span className="fw-bold small me-1">تم تحديد {selectedIds.length}</span>
            {handleOpenPrintModal && (
              <button 
                className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
                onClick={() => handleOpenPrintModal(selectedIds)}
              >
                <IconPrinter size={14} /> طباعة محددة
              </button>
            )}
            <button 
              className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
              onClick={handleBulkDelete}
            >
              <IconTrash size={14} /> حذف محددة
            </button>
          </div>
        )}
      </div>

      {/* Left / End: Total purchases badge */}
      <div className="d-flex align-items-center">
        <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm d-flex align-items-center gap-2" style={{ borderColor: '#adb5bd' }}>
          <span>إجمالي فواتير الشراء:</span>
          <span className="text-danger fw-bolder fs-4 tabular-nums">{formatCurrency(totalAmountSum)}</span>
        </div>
      </div>
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
