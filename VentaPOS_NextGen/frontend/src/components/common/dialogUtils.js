import Swal from 'sweetalert2';

/**
 * Tabler-styled modal dialog utilities for VentaPOS NextGen.
 * Clean replacement for browser native window.confirm() and window.alert().
 */

export const confirmDialog = async ({
  title = 'تأكيد الإجراء',
  message = 'هل أنت متأكد من المتابعة؟',
  confirmText = 'تأكيد',
  cancelText = 'إلغاء',
  danger = false,
} = {}) => {
  const result = await Swal.fire({
    title,
    text: message,
    icon: danger ? 'warning' : 'question',
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    reverseButtons: true,
    buttonsStyling: false,
    customClass: {
      popup: 'shadow-lg border border-secondary-subtle rounded-3 p-4',
      title: 'fw-bold fs-3 text-dark mb-2',
      htmlContainer: 'text-secondary fs-5 mb-4',
      confirmButton: `btn ${danger ? 'btn-danger' : 'btn-success'} px-4 py-2 ms-2`,
      cancelButton: 'btn btn-outline-secondary px-4 py-2',
      actions: 'd-flex justify-content-center gap-2 mt-2',
    },
  });

  return Boolean(result.isConfirmed);
};

export const alertDialog = async ({
  title = 'تنبيه',
  message = '',
  type = 'info',
  confirmText = 'حسناً',
} = {}) => {
  await Swal.fire({
    title,
    text: message,
    icon: type,
    confirmButtonText: confirmText,
    buttonsStyling: false,
    customClass: {
      popup: 'shadow-lg border border-secondary-subtle rounded-3 p-4',
      title: 'fw-bold fs-3 text-dark mb-2',
      htmlContainer: 'text-secondary fs-5 mb-4',
      confirmButton: 'btn btn-primary px-4 py-2',
    },
  });
};
