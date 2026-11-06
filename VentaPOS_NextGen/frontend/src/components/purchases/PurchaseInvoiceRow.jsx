import React from 'react';
import { IconDotsVertical } from '@tabler/icons-react';

const PurchaseInvoiceRow = React.memo(({
  r, index, isSelected, toggleSelect, handleContextMenu, formatCurrency, getSupplierName, innerRef
}) => {
  const rowKey = r.id || r.local_id || index;
  const rNum = r.invoice_number || r.local_id || r.id;
  const typeText = r.invoice_type === 'PURCHASE' ? 'شراء' : 'مرتجع';
  const supplierName = getSupplierName(r.supplier);
  const piecesCount = r.items ? r.items.reduce((acc, item) => acc + Number(item.quantity || 0), 0) : 0;
  const totalAmount = r.items ? r.items.reduce((acc, item) => acc + (item.quantity * item.purchase_price), 0) : 0;

  return (
    <tr ref={innerRef} onContextMenu={(e) => handleContextMenu(e, r.id, rNum)}>
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
          className="btn btn-sm btn-icon btn-light border-secondary-subtle"
          onClick={(e) => handleContextMenu(e, r.id, rNum)}
        >
          <IconDotsVertical size={16} />
        </button>
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold" dir="ltr">{rNum}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <span className={`badge ${r.invoice_type === 'PURCHASE' ? 'bg-success' : 'bg-danger'} text-white`}>{typeText}</span>
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold text-muted" dir="ltr">{`${r.invoice_month}/${r.invoice_year}`}</td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {supplierName}
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold">
        {piecesCount} قطعة
      </td>
      <td className="text-center px-2 align-middle border-secondary-subtle fw-bold text-danger">
        {formatCurrency(totalAmount)}
      </td>
    </tr>
  );
}, (prevProps, nextProps) => {
  return prevProps.isSelected === nextProps.isSelected && prevProps.r === nextProps.r;
});

export default PurchaseInvoiceRow;
