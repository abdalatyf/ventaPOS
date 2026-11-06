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

// Shared license cache and in-flight request deduplication
let cachedLicenseStatus = null;
let inFlightLicensePromise = null;

export const clearLicenseCache = () => {
  cachedLicenseStatus = null;
  inFlightLicensePromise = null;
};

export const getLicenseStatus = async (forceRefresh = false) => {
  if (!forceRefresh && cachedLicenseStatus) {
    return cachedLicenseStatus;
  }
  if (inFlightLicensePromise) {
    return inFlightLicensePromise;
  }
  inFlightLicensePromise = api.get('/license/status/')
    .then((res) => {
      cachedLicenseStatus = res.data || {};
      inFlightLicensePromise = null;
      return cachedLicenseStatus;
    })
    .catch((err) => {
      inFlightLicensePromise = null;
      throw err;
    });
  return inFlightLicensePromise;
};

if (typeof window !== 'undefined') {
  window.addEventListener('license_updated', clearLicenseCache);
  window.addEventListener('subscription_expired', clearLicenseCache);
}

export default api;
