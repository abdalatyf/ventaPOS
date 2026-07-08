import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api';
import logo from '../assets/venta.png';

export default function Login() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingInit, setCheckingInit] = useState(true);
  const [companyName, setCompanyName] = useState('Venta POS');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if the system is initialized and get company name
    api.get('/init/').then(res => {
      if (!res.data.initialized) {
        navigate('/init', { replace: true }); // Force setup if not initialized
      } else {
        if (res.data.company_name) {
          setCompanyName(res.data.company_name);
        }
        setCheckingInit(false);
      }
    }).catch(err => {
      console.error('Error checking initialization:', err);
      setCheckingInit(false);
    });

    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('reason') === 'expired') {
      setError('انتهت جلسة الدخول أو الاشتراك، يرجى تسجيل الدخول مجدداً.');
    }
  }, [navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/local/', { password });
      
      const { token, company_name } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('company_name', company_name);
      
      // On success, redirect to branch selection gateway
      navigate('/select-branch');
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('تعذر الاتصال بالخادم. يرجى المحاولة لاحقاً.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (checkingInit) {
    return (
      <div className="page page-center" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
        <div className="container-fluid px-4 py-4 text-center">
          <div className="spinner-border text-primary" role="status"></div>
          <div className="mt-3 text-muted">جاري فحص حالة النظام...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-center" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-fluid px-4 py-4">
        <div className="text-center mb-4">
          <img src={logo} height="80" alt="Venta POS" />
          <h2 className="mt-3 text-dark fw-bold">{companyName}</h2>
          <p className="text-muted">نظام إدارة المبيعات والتقسيط المتقدم - VentaPOS</p>
        </div>

        <div className="card card-md shadow-sm border-0" style={{ borderRadius: '12px' }}>
          <div className="card-body">
            <h3 className="text-center mb-4 text-primary fw-bold">تسجيل الدخول</h3>
            
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="form-label fw-bold text-muted">كلمة المرور</label>
                <input 
                  type="password" 
                  className="form-control form-control-lg" 
                  placeholder="أدخل كلمة سر النظام" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required 
                />
              </div>
              <div className="form-footer mt-4">
                <button type="submit" className="btn btn-primary w-100 btn-lg fw-bold" disabled={loading}>
                  {loading ? 'جاري الدخول...' : 'تسجيل الدخول'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
