import React from 'react';
import { Link } from 'react-router-dom';
import { IconPencil, IconTrash, IconPrinter } from '@tabler/icons-react';

export default function PurchaseContextMenu({ contextMenu, handleDeleteSingle, handlePrintSingle, onClose }) {
  if (!contextMenu) return null;

  return (
    <div 
      className="dropdown-menu show shadow" 
      style={{ position: 'fixed', top: contextMenu.mouseY, left: contextMenu.mouseX, zIndex: 9999, border: '1px solid #dee2e6' }}
    >
      {handlePrintSingle && (
        <button 
          className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold text-dark"
          onClick={() => {
            handlePrintSingle(contextMenu.invoiceId);
            onClose();
          }}
        >
          <IconPrinter size={18} className="text-primary" /> طباعة / معاينة الفاتورة
        </button>
      )}
      <Link className="dropdown-item d-flex align-items-center gap-2 py-2 fw-bold" to={`/purchases/edit/${contextMenu.invoiceId}`}>
        <IconPencil size={18} className="text-secondary" /> تعديل
      </Link>
      <div className="dropdown-divider"></div>
      <button 
        className="dropdown-item d-flex align-items-center gap-2 py-2 text-danger fw-bold" 
        onClick={() => { 
          handleDeleteSingle(contextMenu.invoiceId, contextMenu.invoiceNum); 
          onClose(); 
        }}
      >
        <IconTrash size={18} /> حذف
      </button>
    </div>
  );
}
