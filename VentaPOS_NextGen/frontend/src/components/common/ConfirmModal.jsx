import React from 'react';

/**
 * Declarative Tabler Confirmation Modal
 */
export default function ConfirmModal({
  isOpen,
  title = 'تأكيد الإجراء',
  message = 'هل أنت متأكد من المتابعة؟',
  confirmText = 'تأكيد',
  cancelText = 'إلغاء',
  danger = false,
  onConfirm,
  onCancel,
  children,
}) {
  if (!isOpen) return null;

  return (
    <div
      className="modal fade show d-block"
      tabIndex="-1"
      role="dialog"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)', zIndex: 1060 }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onCancel?.();
        if (e.key === 'Enter') onConfirm?.();
      }}
    >
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content shadow-lg border border-secondary-subtle">
          <div className="modal-header border-bottom">
            <h5 className="modal-title fw-bold text-dark">{title}</h5>
            <button
              type="button"
              className="btn-close"
              aria-label="Close"
              onClick={onCancel}
            />
          </div>
          <div className="modal-body py-4">
            {message && <p className="mb-0 text-secondary fs-5">{message}</p>}
            {children}
          </div>
          <div className="modal-footer border-top d-flex justify-content-between">
            <button
              type="button"
              className="btn btn-outline-secondary px-4"
              onClick={onCancel}
            >
              {cancelText}
            </button>
            <button
              type="button"
              className={`btn ${danger ? 'btn-danger' : 'btn-primary'} px-4`}
              onClick={onConfirm}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
