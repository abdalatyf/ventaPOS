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
  const currentZoom = (typeof document !== 'undefined' && parseFloat(document.body?.style?.zoom)) || 1.0;
  const maxW = (typeof window !== 'undefined' ? window.innerWidth / currentZoom : 1280) - 180;
  const maxH = (typeof window !== 'undefined' ? window.innerHeight / currentZoom : 720) - 220;
  const top = Math.max(8, Math.min(contextMenu.y / currentZoom, maxH));
  const left = Math.max(8, Math.min(contextMenu.x / currentZoom, maxW));

  return (
    <div 
      className="dropdown-menu show shadow" 
      style={{ 
        position: 'fixed',
        top: `${top}px`, 
        left: `${left}px`, 
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
