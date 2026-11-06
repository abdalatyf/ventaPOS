import React from 'react';

export default function ReceiptContextMenu({
  contextMenu,
  handleEditSingle,
  handlePdfSingle,
  handlePrintSingle,
  handleReturnSingle,
  handleDeleteSingle,
  closeContextMenu
}) {
  if (!contextMenu || !contextMenu.receipt) return null;

  const r = contextMenu.receipt;
  const rNum = r.receipt_number || r.local_id || r.id;

  return (
    <div 
      className="dropdown-menu show shadow" 
      style={{ 
        position: 'fixed',
        top: `${contextMenu.y}px`, 
        left: `${contextMenu.x}px`, 
        zIndex: 1060,
        minWidth: '160px'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {r.receipt_type !== 'RETURN' && (
        <button 
          className="dropdown-item" 
          onClick={() => { 
            handleEditSingle(r.id, rNum); 
            closeContextMenu(); 
          }}
        >
          تعديل الفاتورة
        </button>
      )}
      {!r.is_cash_sale && (
        <button 
          className="dropdown-item" 
          onClick={() => { 
            handlePdfSingle(r.id, rNum); 
            closeContextMenu(); 
          }}
        >
          معاينة PDF
        </button>
      )}
      {r.receipt_type !== 'RETURN' && !r.is_cash_sale && (
        <button 
          className="dropdown-item" 
          onClick={() => { 
            handlePrintSingle(r.id, rNum); 
            closeContextMenu(); 
          }}
        >
          طباعة كقسط
        </button>
      )}
      {r.receipt_type !== 'RETURN' && (
        <>
          <div className="dropdown-divider"></div>
          <button 
            className="dropdown-item text-secondary" 
            onClick={() => { 
              handleReturnSingle(r.id, rNum); 
              closeContextMenu(); 
            }}
          >
            إنشاء مرتجع
          </button>
        </>
      )}
      <div className="dropdown-divider"></div>
      <button 
        className="dropdown-item text-danger" 
        onClick={() => { 
          handleDeleteSingle(r.id, rNum); 
          closeContextMenu(); 
        }}
      >
        حذف الفاتورة
      </button>
    </div>
  );
}
