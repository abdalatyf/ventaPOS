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

  // Recovery State
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryCode, setRecoveryCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [recoveryError, setRecoveryError] = useState('');
  const [recoverySuccess, setRecoverySuccess] = useState('');

  useEffect(() => {
    // Attempt Auto-Login for Demo Mode
    api.post('/auth/demo/').then(demoRes => {
      // Success means we are in Demo mode!
      localStorage.setItem('token', demoRes.data.token);
      localStorage.setItem('company_name', demoRes.data.company_name);
      navigate('/select-branch', { replace: true });
    }).catch(err => {
      // If it fails, it means the system is ACTIVATED. We must stay on Login screen.
      setCheckingInit(false);
      
      // Try to get the real company name for display
      api.get('/company-settings/').then(res => {
        if (res.data.name) setCompanyName(res.data.name);
      }).catch(e => {
        // Ignore 401s since we are logged out
      });
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
        setError('تعذر الاتصال بالخادم. كلمة المرور قد تكون خاطئة.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRecoverySubmit = async (e) => {
    e.preventDefault();
    setRecoveryError('');
    setRecoverySuccess('');
    setLoading(true);

    try {
      const response = await api.post('/auth/recover/', { 
        recovery_code: recoveryCode, 
        new_password: newPassword 
      });
      setRecoverySuccess(response.data.message || 'تم تغيير كلمة المرور بنجاح.');
      setTimeout(() => setShowRecovery(false), 2000);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        setRecoveryError(err.response.data.error);
      } else {
        setRecoveryError('تعذر التحقق من كود الاسترداد.');
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
            {!showRecovery ? (
              <>
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
                <div className="text-center text-muted mt-3">
                  <a href="#" onClick={(e) => { e.preventDefault(); setShowRecovery(true); }}>نسيت كلمة المرور؟</a>
                </div>
              </>
            ) : (
              <>
                <h3 className="text-center mb-4 text-warning fw-bold">استعادة كلمة المرور</h3>
                
                {recoveryError && <div className="alert alert-danger" role="alert">{recoveryError}</div>}
                {recoverySuccess && <div className="alert alert-success" role="alert">{recoverySuccess}</div>}

                <form onSubmit={handleRecoverySubmit}>
                  <div className="mb-3">
                    <label className="form-label fw-bold text-muted">كود الاسترداد (Recovery Code)</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="مثال: VNTA-ABCD-1234" 
                      value={recoveryCode}
                      onChange={(e) => setRecoveryCode(e.target.value)}
                      required 
                    />
                  </div>
                  <div className="mb-4">
                    <label className="form-label fw-bold text-muted">كلمة المرور الجديدة</label>
                    <input 
                      type="password" 
                      className="form-control" 
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required 
                    />
                  </div>
                  <div className="form-footer mt-4 d-flex gap-2">
                    <button type="button" className="btn btn-light flex-grow-1" onClick={() => setShowRecovery(false)}>
                      إلغاء
                    </button>
                    <button type="submit" className="btn btn-warning flex-grow-1 fw-bold" disabled={loading}>
                      {loading ? 'جاري...' : 'تغيير كلمة المرور'}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
