import React from 'react';
import { IconDotsVertical } from '@tabler/icons-react';

const ReceiptRow = React.memo(React.forwardRef(({
  r, index, isSelected, toggleSelect, handleContextMenu, formatCurrency, getSalespersonName,
  handleEditSingle, handlePdfSingle, handlePrintSingle, handleDeleteSingle, handleReturnSingle
}, ref) => {
  const rowKey = r.id || r.local_id || index;
  const rNum = r.receipt_number || r.local_id || r.id;
  const isCash = r.is_cash_sale !== false && r.sale_type !== 'INSTALLMENT';
  const phone = r.phone_number || r.customer_phone || r.phone || '—';
  const area = r.area || r.customer_area || '—';
  const addr = r.address || r.customer_address || '—';
  const productsText = r.products_text || '—';
  const custName = r.customer_name || 'عميل نقدي';
  const salespersonName = getSalespersonName(r.salesperson);

  const handleRowClick = (e) => {
    if (e.target.closest('input[type="checkbox"]') || e.target.closest('.dropdown')) {
      return;
    }
    if (r.receipt_type !== 'RETURN') {
      handleEditSingle(r.id, rNum);
    }
  };

  return (
    <tr 
      ref={ref} 
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
        <div className="dropdown">
          <button 
            className="btn btn-sm btn-icon btn-light border-secondary-subtle"
            data-bs-toggle="dropdown"
          >
            <IconDotsVertical size={16} />
          </button>
          <div className="dropdown-menu dropdown-menu-end shadow-sm">
            {r.receipt_type !== 'RETURN' && (
              <button className="dropdown-item" onClick={() => handleEditSingle(r.id, rNum)}>
                تعديل الفاتورة
              </button>
            )}
            <button className="dropdown-item" onClick={() => handlePdfSingle(r.id, rNum)}>
              معاينة PDF
            </button>
            {r.receipt_type !== 'RETURN' && !r.is_cash_sale && (
              <button className="dropdown-item" onClick={() => handlePrintSingle(r.id, rNum)}>
                طباعة كقسط
              </button>
            )}
            {r.receipt_type !== 'RETURN' && (
              <>
                <div className="dropdown-divider"></div>
                <button className="dropdown-item text-secondary" onClick={() => handleReturnSingle(r.id, rNum)}>
                  إنشاء مرتجع
                </button>
              </>
            )}
            <div className="dropdown-divider"></div>
            <button className="dropdown-item text-danger" onClick={() => handleDeleteSingle(r.id, rNum)}>
              حذف الفاتورة
            </button>
          </div>
        </div>
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
      <td className="text-center align-middle border-secondary-subtle" dir="rtl">
        <span className="fw-bold text-primary">{r.sale_month}</span>
        <span className="mx-1 text-muted">/</span>
        <span className="fw-bold">{r.sale_year}</span>
      </td>
      <td className="text-center align-middle border-secondary-subtle">
        {salespersonName}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle">
        {custName}
      </td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">{phone}</td>
      <td className="text-center align-middle border-secondary-subtle">
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
  return prevProps.isSelected === nextProps.isSelected && prevProps.r === nextProps.r;
});

export default ReceiptRow;
