import axios from 'axios';

// إعداد النطاق الأساسي بناءً على عقد الـ API Contract (الإنتاج أو النفق المحلي للتطوير)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// اعتراض الطلبات لحقن ترويسات الأمان والتحقق المتعدد (Multi-Tenant & JWT Bearer)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    // Fallback to '1234' for local testing if not logged in
    const companyCode = localStorage.getItem('company_code') || '1234'; 
    const machineId = localStorage.getItem('machine_id') || 'DEV-MACHINE-001';
    const branchId = localStorage.getItem('branchId');

    if (token) {
      config.headers['Authorization'] = `Token ${token}`;
    }
    if (companyCode) {
      config.headers['X-Company-Code'] = companyCode;
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

// اعتراض الاستجابات للتعامل التلقائي مع حالات انتهاء رخصة الباقة والاشتراك
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 403) {
      const errorMessage = error.response.data?.detail || error.response.data?.message || '';
      
      // التقاط انتهاء الاشتراك السحابي للتوجيه المباشر لشاشة التفعيل كما نص عقد الـ API
      if (errorMessage.includes('الاشتراك السحابي انتهى') || errorMessage.includes('expired')) {
        localStorage.removeItem('token'); // تنظيف التوكن منتهي الصلاحية
        window.dispatchEvent(new CustomEvent('subscription_expired'));
        
        // التوجيه التلقائي لصفحة تسجيل الدخول أو التنشيط مع تمرير السبب
        if (window.location.pathname !== '/login') {
          window.location.href = '/login?reason=expired';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
