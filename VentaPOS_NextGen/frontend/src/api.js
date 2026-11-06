import axios from 'axios';
import { showAlert } from './utils/dialogUtils';

// إعداد النطاق الأساسي بناءً على عقد الـ API Contract (الإنتاج أو النفق المحلي للتطوير)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// اعتراض الطلبات لحقن ترويسات الأمان
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    const machineId = localStorage.getItem('machine_id') || 'DEV-MACHINE-001';
    const branchId = localStorage.getItem('branchId');

    if (token) {
      config.headers['Authorization'] = `Token ${token}`;
    }
    if (machineId) {
      config.headers['X-Machine-ID'] = machineId;
    }
    if (branchId) {
      config.headers['X-Branch-ID'] = branchId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// اعتراض الاستجابات للتعامل التلقائي مع حالات انتهاء الرخصة
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      (error.response?.status === 403 &&
        (error.response?.data?.error === 'license_expired' ||
          error.response?.data?.detail?.includes('الرخصة') ||
          error.response?.data?.message?.includes('الرخصة'))) ||
      error.response?.status === 402
    ) {
      showAlert(
        'انتهت صلاحية الرخصة. النظام يعمل حالياً في وضع القراءة فقط. يرجى تجديد الاشتراك لتسجيل عمليات جديدة.',
        'warning'
      );
      window.dispatchEvent(new CustomEvent('subscription_expired'));
    } else if (error.response && error.response.status === 401) {
      // 401 Unauthorized: Token is invalid (e.g. database wiped)
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
