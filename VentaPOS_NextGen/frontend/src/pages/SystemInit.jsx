import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function SystemInit() {
  const [formData, setFormData] = useState({
    company_name: '',
    branch_name: '',
    password: '',
    phone1: '',
    phone2: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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
    
    if (!formData.company_name || !formData.branch_name || !formData.password) {
      setError("الرجاء إدخال اسم الشركة واسم الفرع وكلمة المرور.");
      setLoading(false);
      return;
    }

    try {
      await api.post('/init/', formData);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.error || "حدث خطأ أثناء التهيئة");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page page-center" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-fluid py-4 px-4">
        <div className="card shadow-lg border-0" style={{ borderRadius: '12px' }}>
          <div className="card-header bg-primary text-white text-center py-4" style={{ borderRadius: '12px 12px 0 0' }}>
            <h2 className="fw-bold mb-2">مرحباً بك في VentaPOS!</h2>
            <p className="mb-0 opacity-75">للبدء، يرجى إعداد بيانات المؤسسة وكلمة سر النظام.</p>
          </div>
          <div className="card-body p-4 bg-light">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label fw-bold">اسم الشركة / المؤسسة <span className="text-danger">*</span></label>
                <input type="text" name="company_name" className="form-control form-control-lg" value={formData.company_name} onChange={handleChange} required />
                <div className="form-text small">سيظهر بخط عريض أعلى البرنامج والفواتير.</div>
              </div>
              
              <div className="mb-3">
                <label className="form-label fw-bold">كلمة سر النظام <span className="text-danger">*</span></label>
                <input type="password" name="password" className="form-control form-control-lg" value={formData.password} onChange={handleChange} required />
                <div className="form-text small">سيطلب منك إدخالها عند الدخول للبرنامج في كل مرة.</div>
              </div>

              <div className="mb-3">
                <label className="form-label fw-bold">اسم الفرع الرئيسي <span className="text-danger">*</span></label>
                <input type="text" name="branch_name" className="form-control form-control-lg" value={formData.branch_name} onChange={handleChange} required />
                <div className="form-text small">سيتم إنشاء هذا كأول فرع للنظام.</div>
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
                  {loading ? 'جاري الحفظ...' : 'حفظ البيانات وبدء العمل'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
