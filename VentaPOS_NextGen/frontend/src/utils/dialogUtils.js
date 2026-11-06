import Swal from 'sweetalert2';

/**
 * Standard SweetAlert2 Dialog Utilities for VentaPOS NextGen
 * Replacing native alert() and window.confirm().
 */

export const confirmDialog = async ({
  title = 'هل أنت متأكد؟',
  text = '',
  confirmButtonText = 'نعم، موافق',
  cancelButtonText = 'إلغاء',
  icon = 'warning',
  confirmButtonColor = '#d33',
  cancelButtonColor = '#6c757d'
} = {}) => {
  const result = await Swal.fire({
    title,
    text,
    icon,
    showCancelButton: true,
    confirmButtonText,
    cancelButtonText,
    confirmButtonColor,
    cancelButtonColor,
    reverseButtons: true
  });
  return result.isConfirmed;
};

export const alertDialog = async ({
  title = 'تنبيه',
  text = '',
  icon = 'info',
  confirmButtonText = 'حسناً',
  confirmButtonColor = '#123F68'
} = {}) => {
  return await Swal.fire({
    title,
    text,
    icon,
    confirmButtonText,
    confirmButtonColor
  });
};

export const confirmAction = confirmDialog;
export const showAlert = (text, icon = 'info', title = 'تنبيه') => alertDialog({ title, text, icon });

export default {
  confirmDialog,
  alertDialog,
  confirmAction,
  showAlert
};
