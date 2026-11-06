import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconRefresh } from '@tabler/icons-react';

export function ReceiptsFilterRow1({
  filters,
  handleFilterChange,
  handleSelectChange,
}) {
  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Month */}
      <div style={{ width: '100px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">شهر</span>
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
      <div style={{ width: '105px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">سنة</span>
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
      <div style={{ width: '110px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">من رقم</span>
          <input 
            type="number" 
            className="form-control fw-bold border-secondary-subtle px-1 text-center" 
            name="receipt_from" 
            placeholder="الكل"
            value={filters.receipt_from} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Receipt To */}
      <div style={{ width: '110px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">إلى رقم</span>
          <input 
            type="number" 
            className="form-control fw-bold border-secondary-subtle px-1 text-center" 
            name="receipt_to" 
            placeholder="الكل"
            value={filters.receipt_to} 
            onChange={handleFilterChange} 
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
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العميل</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle" 
            name="customer_name" 
            placeholder="اسم العميل..."
            value={filters.customer_name} 
            onChange={handleFilterChange} 
          />
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
  return (
    <div className="d-flex align-items-center gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      {/* Phone */}
      <div style={{ width: '150px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">الهاتف</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle text-center px-1" 
            dir="ltr" 
            name="phone" 
            placeholder="رقم الهاتف"
            value={filters.phone} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Area */}
      <div className="flex-grow-1" style={{ minWidth: '140px' }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">المنطقة</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle" 
            name="area" 
            placeholder="المنطقة / القرية"
            value={filters.area} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Address */}
      <div className="flex-grow-1" style={{ minWidth: '160px' }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">العنوان</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle" 
            name="address" 
            placeholder="العنوان بالتفصيل"
            value={filters.address} 
            onChange={handleFilterChange} 
          />
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
              setSalespersonName(item.name);
              setFilters(prev => {
                const newFilters = { ...prev, salesperson_id: item.id || item.local_id };
                fetchReceipts(newFilters);
                return newFilters;
              });
            }}
            fetchSuggestions={fetchSalespersonSuggestions}
            placeholder="جميع المناديب"
            className="form-control fw-bold border-secondary-subtle px-1"
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
