import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function SystemInit() {
  const [formData, setFormData] = useState({
    company_name: '',
    branch_name: '',
    password: '',
    license_code: '',
    phone1: '',
    phone2: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recoveryCode, setRecoveryCode] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if system is already initialized
    api.get('/init/').then(res => {
      if (res.data.initialized) {
        navigate('/login');
      }
    }).catch(err => {
      console.error(err);
    });
  }, [navigate]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    if (!formData.company_name || !formData.branch_name || !formData.password || !formData.license_code) {
      setError("الرجاء إدخال جميع البيانات الإلزامية بما فيها كود التفعيل.");
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/init/', formData);
      if (res.data.recovery_code) {
        setRecoveryCode(res.data.recovery_code);
      } else {
        navigate('/login');
      }
    } catch (err) {
      setError(err.response?.data?.error || "حدث خطأ أثناء التفعيل");
    } finally {
      setLoading(false);
    }
  };

  const finishInit = () => {
    navigate('/login');
  };

  if (recoveryCode) {
    return (
      <div className="page page-center" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
        <div className="container-fluid py-4 px-4">
          <div className="card shadow-lg border-0 text-center" style={{ borderRadius: '12px', maxWidth: '500px', margin: '0 auto' }}>
            <div className="card-header bg-success text-white py-4" style={{ borderRadius: '12px 12px 0 0' }}>
              <h2 className="fw-bold mb-0">تم تفعيل النظام بنجاح!</h2>
            </div>
            <div className="card-body p-4 bg-light">
              <div className="alert alert-warning text-dark text-start" role="alert" style={{ fontSize: '1.1rem' }}>
                <h4 className="alert-title fw-bold text-danger">⚠️ هام جداً! إحتفظ بهذا الكود</h4>
                في حال نسيان كلمة مرور النظام، هذا الكود هو الطريقة الوحيدة لاستعادتها. الرجاء تصوير الشاشة أو كتابته في مكان آمن:
                <div className="mt-3 text-center">
                  <span className="badge bg-dark fs-3 py-2 px-3">{recoveryCode}</span>
                </div>
              </div>
              <button className="btn btn-primary btn-lg fw-bold w-100 mt-3" onClick={finishInit}>
                موافق، انتقل للدخول
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page page-center" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-fluid py-4 px-4">
        <div className="card shadow-lg border-0" style={{ borderRadius: '12px', maxWidth: '700px', margin: '0 auto' }}>
          <div className="card-header bg-primary text-white text-center py-4" style={{ borderRadius: '12px 12px 0 0' }}>
            <h2 className="fw-bold mb-2">تفعيل VentaPOS الدائم</h2>
            <p className="mb-0 opacity-75">للبدء، يرجى إدخال كود التفعيل وإعداد بيانات المؤسسة وكلمة السر.</p>
          </div>
          <div className="card-body p-4 bg-light">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="form-label fw-bold text-success fs-5">كود التفعيل (License Code) <span className="text-danger">*</span></label>
                <input type="text" name="license_code" className="form-control form-control-lg border-success" placeholder="أدخل الكود هنا لتفعيل النسخة" value={formData.license_code} onChange={handleChange} required />
              </div>

              <hr />

              <div className="mb-3">
                <label className="form-label fw-bold">اسم الشركة / المؤسسة <span className="text-danger">*</span></label>
                <input type="text" name="company_name" className="form-control form-control-lg" value={formData.company_name} onChange={handleChange} required />
                <div className="form-text small">سيظهر بخط عريض أعلى البرنامج والفواتير.</div>
              </div>
              
              <div className="mb-3">
                <label className="form-label fw-bold">كلمة سر النظام <span className="text-danger">*</span></label>
                <input type="password" name="password" className="form-control form-control-lg" value={formData.password} onChange={handleChange} required />
                <div className="form-text small">هذه هي كلمة السر الرئيسية (والوحيدة) للدخول للبرنامج.</div>
              </div>

              <div className="mb-3">
                <label className="form-label fw-bold">اسم الفرع الرئيسي <span className="text-danger">*</span></label>
                <input type="text" name="branch_name" className="form-control form-control-lg" value={formData.branch_name} onChange={handleChange} required />
              </div>

              <div className="row">
                <div className="col-md-6 mb-3">
                  <label className="form-label fw-bold">رقم تليفون 1</label>
                  <input type="text" name="phone1" className="form-control" value={formData.phone1} onChange={handleChange} />
                </div>
                <div className="col-md-6 mb-3">
                  <label className="form-label fw-bold">رقم تليفون 2</label>
                  <input type="text" name="phone2" className="form-control" value={formData.phone2} onChange={handleChange} />
                </div>
              </div>

              <div className="form-footer mt-4">
                <button type="submit" className="btn btn-success w-100 btn-lg fw-bold shadow-sm" disabled={loading}>
                  {loading ? 'جاري التحقق والتفعيل...' : 'تفعيل النسخة وبدء العمل'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
