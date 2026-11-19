import React from 'react';
import { IconDotsVertical } from '@tabler/icons-react';
import { formatMMYYYY } from '../../utils/formatUtils';

const ReceiptRow = React.memo(React.forwardRef(({
  r, index, isSelected, isFocused, onRowFocus, toggleSelect, handleContextMenu, formatCurrency, getSalespersonName,
  handleEditSingle
}, ref) => {
  const rNum = r.receipt_number || r.local_id || r.id;
  const isCash = r.is_cash_sale !== false && r.sale_type !== 'INSTALLMENT';
  const phone = r.phone_number || r.customer_phone || r.phone || '—';
  const area = r.area || r.customer_area || '—';
  const addr = r.address || r.customer_address || '—';
  const productsText = r.products_text || '—';
  const custName = r.customer_name || 'عميل نقدي';
  const salespersonName = getSalespersonName(r.salesperson);
  const formattedSaleDate = formatMMYYYY(r.sale_month, r.sale_year) || '—';

  const handleRowClick = (e) => {
    if (e.target.closest('input[type="checkbox"]') || e.target.closest('button') || e.target.closest('.dropdown')) {
      return;
    }
    if (onRowFocus) onRowFocus(index);
    if (r.receipt_type !== 'RETURN') {
      handleEditSingle(r.id, rNum);
    }
  };

  return (
    <tr 
      ref={ref} 
      data-row-index={index}
      className={isFocused ? 'table-row-focused' : ''}
      onClick={handleRowClick}
      onContextMenu={(e) => handleContextMenu && handleContextMenu(e, r)}
      style={{ cursor: r.receipt_type !== 'RETURN' ? 'pointer' : 'default' }}
      title={r.receipt_type !== 'RETURN' ? 'انقر لتعديل الفاتورة، أو انقر بزر الفأرة الأيمن لخيارات الفاتورة' : ''}
    >
      <td className="text-center align-middle border-secondary-subtle" onClick={(e) => e.stopPropagation()}>
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(r.id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle" onClick={(e) => e.stopPropagation()}>
        <button 
          type="button"
          className="btn btn-sm btn-icon btn-light border-secondary-subtle"
          aria-label="خيارات الفاتورة"
          onClick={(e) => {
            e.stopPropagation();
            if (!handleContextMenu) return;
            const rect = e.currentTarget.getBoundingClientRect();
            handleContextMenu({
              preventDefault: () => {},
              clientX: rect.left,
              clientY: rect.bottom + 2,
            }, r);
          }}
        >
          <IconDotsVertical size={16} />
        </button>
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {rNum}
        {r.receipt_type === 'RETURN' && (
          <div className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle rounded-pill px-2 mt-1 d-block" style={{ fontSize: '0.7rem' }}>
            إشعار مرتجع
          </div>
        )}
        {r.has_returns && (
          <div className="badge bg-danger rounded-pill px-2 mt-1 d-block" style={{ fontSize: '0.7rem' }}>
            بها مرتجع
          </div>
        )}
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold text-primary" dir="ltr">
        {formattedSaleDate}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {salespersonName}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle">
        {custName}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr" style={{ minWidth: '125px' }}>{phone}</td>
      <td className="text-center align-middle border-secondary-subtle" style={{ minWidth: '125px' }}>
        {area}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '150px' }} title={addr}>
        {addr}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle text-truncate" style={{ maxWidth: '200px' }} title={productsText}>
        {productsText}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {isCash ? '—' : formatCurrency(r.down_payment)}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {isCash ? 'كاش' : r.installment_system}
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {formatCurrency(r.total_amount)}
      </td>
    </tr>
  );
}), (prevProps, nextProps) => {
  return (
    prevProps.isSelected === nextProps.isSelected &&
    prevProps.isFocused === nextProps.isFocused &&
    prevProps.r === nextProps.r
  );
});

export default ReceiptRow;
