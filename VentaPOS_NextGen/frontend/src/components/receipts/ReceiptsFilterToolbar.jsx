import React from 'react';
import Autocomplete from '../Autocomplete';
import { IconRefresh, IconPrinter, IconEye, IconTrash } from '@tabler/icons-react';

export function ReceiptsFilterRow1({
  filters,
  handleFilterChange,
  handleSelectChange,
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
      {/* Month */}
      <div style={{ width: '80px' }} className="flex-shrink-0">
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
      <div style={{ width: '85px' }} className="flex-shrink-0">
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
      <div style={{ width: '75px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">من</span>
          <input 
            type="number" 
            className="form-control fw-bold border-secondary-subtle px-1 text-center" 
            name="receipt_from" 
            placeholder="رقم"
            value={filters.receipt_from} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Receipt To */}
      <div style={{ width: '75px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">إلى</span>
          <input 
            type="number" 
            className="form-control fw-bold border-secondary-subtle px-1 text-center" 
            name="receipt_to" 
            placeholder="رقم"
            value={filters.receipt_to} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Sale Type */}
      <div style={{ width: '95px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">النوع</span>
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
      <div className="flex-grow-1" style={{ minWidth: '110px' }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">العميل</span>
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

      {/* Phone */}
      <div style={{ width: '110px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">الهاتف</span>
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
      <div className="flex-grow-1" style={{ minWidth: '85px' }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">المنطقة</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle" 
            name="area" 
            placeholder="المنطقة"
            value={filters.area} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Address */}
      <div className="flex-grow-1" style={{ minWidth: '85px' }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">العنوان</span>
          <input 
            type="text" 
            className="form-control fw-bold border-secondary-subtle" 
            name="address" 
            placeholder="العنوان"
            value={filters.address} 
            onChange={handleFilterChange} 
          />
        </div>
      </div>

      {/* Salesperson Autocomplete */}
      <div style={{ width: '150px' }} className="flex-shrink-0">
        <div className="input-group input-group-sm flex-nowrap">
          <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">المندوب</span>
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
        className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1 fw-bold px-2 py-1 flex-shrink-0 border-secondary-subtle" 
        onClick={handleResetFilters} 
        disabled={loading} 
        title="إلغاء الفلاتر وإعادة الضبط"
      >
        <IconRefresh size={14} />
        <span>إلغاء</span>
      </button>
    </div>
  );
}

export function ReceiptsFilterRow2({
  salespersonName,
  setSalespersonName,
  setFilters,
  fetchReceipts,
  fetchSalespersonSuggestions,
  handleResetFilters,
  loading,
  totalInvoicesCount,
  totalAmountSum,
  selectedIds = [],
  handlePrint,
  handleBulkDelete,
  formatCurrency,
}) {
  return (
    <div className="d-flex align-items-center justify-content-between gap-2 w-100 flex-nowrap" style={{ overflow: 'visible' }}>
      <div className="d-flex align-items-center gap-2">
        {/* Salesperson Autocomplete */}
        <div style={{ width: '240px' }} className="flex-shrink-0">
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
              className="form-control fw-bold border-secondary-subtle"
            />
          </div>
        </div>

        {/* Reset button */}
        <button 
          type="button" 
          className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1 fw-bold px-2 py-1" 
          onClick={handleResetFilters} 
          disabled={loading} 
          title="إلغاء الفلاتر وإعادة الضبط"
          style={{ border: '1px solid #adb5bd' }}
        >
          <IconRefresh size={14} />
          <span>إلغاء الفلاتر</span>
        </button>

        {/* Results count badge */}
        <span className="badge bg-primary text-white rounded-pill px-2 py-1 fs-5">
          نتائج البحث: {totalInvoicesCount || 0} فاتورة
        </span>

        {/* Bulk Action Buttons */}
        {selectedIds.length > 0 && (
          <div className="d-flex align-items-center gap-1 border-start border-secondary-subtle ps-2 ms-1">
            <span className="badge bg-secondary-lt text-dark fw-bold px-2 py-1">
              محدد {selectedIds.length}
            </span>
            <button 
              type="button"
              className="btn btn-outline-success btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
              onClick={() => handlePrint && handlePrint(selectedIds, 'print')}
            >
              <IconPrinter size={14} />
              <span>طباعة محددة</span>
            </button>
            <button 
              type="button"
              className="btn btn-outline-primary btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
              onClick={() => handlePrint && handlePrint(selectedIds, 'view')}
            >
              <IconEye size={14} />
              <span>معاينة محددة</span>
            </button>
            <button 
              type="button"
              className="btn btn-outline-danger btn-sm fw-bold py-1 px-2 border-secondary-subtle d-flex align-items-center gap-1" 
              onClick={handleBulkDelete}
            >
              <IconTrash size={14} />
              <span>حذف محددة</span>
            </button>
          </div>
        )}
      </div>

      {/* Total Sales Badge on the left */}
      <div className="text-dark fw-bold fs-4 border px-3 py-1 bg-white rounded shadow-sm flex-shrink-0" style={{ borderColor: '#adb5bd' }}>
        إجمالي فواتير البيع:{' '}
        <span className="text-danger fw-bolder fs-4">
          {formatCurrency ? formatCurrency(totalAmountSum || 0) : (totalAmountSum || 0)}
        </span>
      </div>
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
