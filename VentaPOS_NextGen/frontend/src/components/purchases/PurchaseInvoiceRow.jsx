import React from 'react';
import { IconDotsVertical } from '@tabler/icons-react';
import { formatMMYYYY, fmtNum } from '../../utils/formatUtils';

const PurchaseInvoiceRow = React.memo(({
  r, index, isSelected, isFocused, toggleSelect, handleContextMenu, formatCurrency, getSupplierName, innerRef
}) => {
  const rNum = r.invoice_number || r.local_id || r.id;
  const typeText = r.invoice_type === 'PURCHASE' ? 'شراء' : 'مرتجع';
  const supplierName = getSupplierName(r.supplier);
  const piecesCount = r.items ? r.items.reduce((acc, item) => acc + Math.round(Number(item.quantity || 0)), 0) : 0;
  const totalAmount = r.items ? r.items.reduce((acc, item) => acc + (Number(item.quantity || 0) * Number(item.purchase_price || 0)), 0) : 0;
  const formattedDate = formatMMYYYY(r.invoice_month, r.invoice_year) || '—';

  return (
    <tr ref={innerRef} data-row-index={index} className={isFocused ? 'table-row-focused' : ''} onContextMenu={(e) => handleContextMenu(e, r.id, rNum)}>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(r.id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        <button 
          type="button"
          className="btn btn-sm btn-icon btn-light border-secondary-subtle"
          aria-label="خيارات الفاتورة"
          onClick={(e) => {
            e.stopPropagation();
            handleContextMenu(e, r.id, rNum);
          }}
        >
          <IconDotsVertical size={16} />
        </button>
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold" dir="ltr">{rNum}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <span className={`badge ${r.invoice_type === 'PURCHASE' ? 'bg-success' : 'bg-danger'} text-white`}>{typeText}</span>
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold text-muted" dir="ltr">{formattedDate}</td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {supplierName}
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold">
        {fmtNum(piecesCount)} قطعة
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-danger">
        {formatCurrency(totalAmount)}
      </td>
    </tr>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.isSelected === nextProps.isSelected &&
    prevProps.isFocused === nextProps.isFocused &&
    prevProps.r === nextProps.r
  );
});

export default PurchaseInvoiceRow;
