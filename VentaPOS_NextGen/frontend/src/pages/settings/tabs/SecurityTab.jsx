import React, { useState, useEffect } from 'react';
import { IconShieldLock, IconArrowLeft, IconLockOpen, IconLock } from '@tabler/icons-react';
import api from '../../../api';

export default function SecurityTab() {
  const [formData, setFormData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasInitialPassword, setHasInitialPassword] = useState(false);
  const [isPasswordEnabled, setIsPasswordEnabled] = useState(false);
  const [checkingState, setCheckingState] = useState(true);

  useEffect(() => {
    const checkPasswordState = async () => {
      try {
        const res = await api.get('/auth/has-password/');
        setHasInitialPassword(res.data.has_password);
        setIsPasswordEnabled(res.data.has_password);
      } catch (err) {
        console.error("Failed to fetch password state", err);
      } finally {
        setCheckingState(false);
      }
    };
    checkPasswordState();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleToggle = () => {
    setIsPasswordEnabled(!isPasswordEnabled);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isPasswordEnabled && formData.newPassword !== formData.confirmPassword) {
      setError('كلمة المرور الجديدة غير متطابقة!');
      setSuccess('');
      return;
    }
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      // If we are disabling the password
      if (!isPasswordEnabled) {
        await api.post('/auth/change-password/', {
          old_password: formData.oldPassword,
          new_password: '' // empty means remove password
        });
        setSuccess('تم إلغاء كلمة المرور بنجاح، ستتمكن من الدخول المباشر.');
        setHasInitialPassword(false);
        setFormData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        // We are enabling or changing the password
        if (!formData.newPassword) {
          setError('الرجاء إدخال كلمة المرور الجديدة');
          setIsLoading(false);
          return;
        }
        await api.post('/auth/change-password/', {
          old_password: formData.oldPassword,
          new_password: formData.newPassword
        });
        setSuccess('تم تحديث كلمة المرور بنجاح.');
        setHasInitialPassword(true);
        setFormData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      }
    } catch (err) {
      setError(err.response?.data?.error || 'حدث خطأ أثناء تنفيذ العملية');
    } finally {
      setIsLoading(false);
    }
  };

  if (checkingState) {
    return <div className="text-center p-5"><div className="spinner-border text-primary"></div></div>;
  }

  return (
    <div className="card shadow-sm border-0 mb-4 animate__animated animate__fadeIn">
      <div className="card-header bg-dark text-white py-3">
        <h5 className="mb-0 fw-bold"><IconShieldLock className="me-2" /> أمان الحساب (تغيير كلمة المرور)</h5>
      </div>
      <div className="card-body">
        {error && (
          <div className="alert alert-danger shadow-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success shadow-sm">
            {success}
          </div>
        )}
        <div className="d-flex align-items-center mb-4 p-3 bg-light rounded border">
          <div className="form-check form-switch fs-4 mb-0" style={{ cursor: 'pointer' }}>
            <input 
              className="form-check-input shadow-none" 
              type="checkbox" 
              role="switch" 
              id="passwordToggle" 
              checked={isPasswordEnabled} 
              onChange={handleToggle} 
              style={{ cursor: 'pointer', width: '3rem', height: '1.5rem', marginTop: '0.2rem' }}
            />
            <label className="form-check-label fw-bold ms-3 me-4 text-dark" htmlFor="passwordToggle" style={{ cursor: 'pointer' }}>
              {isPasswordEnabled ? 'الحماية بكلمة سر مفعلة' : 'تسجيل الدخول المباشر (بدون كلمة سر)'}
            </label>
          </div>
          <div className="ms-auto">
            {isPasswordEnabled ? <IconLock className="text-success" size={32} /> : <IconLockOpen className="text-secondary" size={32} />}
          </div>
        </div>

        {/* If user HAS an initial password, and wants to DISABLE it, we ONLY ask for old password to confirm */}
        {hasInitialPassword && !isPasswordEnabled && (
          <form onSubmit={handleSubmit} className="animate__animated animate__fadeIn">
            <div className="alert alert-warning border-warning">
              ⚠️ أنت على وشك إلغاء كلمة المرور، مما سيسمح لأي شخص بفتح النظام مباشرة بدون حماية. يرجى إدخال كلمة المرور الحالية لتأكيد الإلغاء.
            </div>
            <div className="row g-3 align-items-end">
              <div className="col-md-5">
                <label className="form-label fw-bold">كلمة المرور الحالية لتأكيد الإلغاء</label>
                <input 
                  type="password" className="form-control form-control-lg" name="oldPassword" 
                  value={formData.oldPassword} onChange={handleChange} required dir="ltr" disabled={isLoading}
                />
              </div>
              <div className="col-md-3">
                <button type="submit" className="btn btn-danger btn-lg w-100 fw-bold" disabled={isLoading}>
                  {isLoading ? 'جاري الإلغاء...' : 'تأكيد الإلغاء'}
                </button>
              </div>
            </div>
          </form>
        )}

        {/* If the user is ENABLING password (or changing it) */}
        {isPasswordEnabled && (
          <form onSubmit={handleSubmit} className="animate__animated animate__fadeIn">
            <div className="row g-3 align-items-start">
              {hasInitialPassword && (
                <div className="col-md-4">
                  <label className="form-label fw-bold">كلمة المرور الحالية</label>
                  <input 
                    type="password" className="form-control" name="oldPassword" 
                    value={formData.oldPassword} onChange={handleChange} required dir="ltr" disabled={isLoading}
                  />
                </div>
              )}
              
              <div className={hasInitialPassword ? "col-md-3" : "col-md-5"}>
                <label className="form-label fw-bold text-success">كلمة المرور الجديدة</label>
                <input 
                  type="password" className="form-control" name="newPassword" 
                  value={formData.newPassword} onChange={handleChange} required dir="ltr" disabled={isLoading}
                />
                <div className="form-text small">يُفضل استخدام أرقام وحروف.</div>
              </div>
              
              <div className={hasInitialPassword ? "col-md-3" : "col-md-5"}>
                <label className="form-label fw-bold">تأكيد كلمة المرور الجديدة</label>
                <input 
                  type="password" className="form-control" name="confirmPassword" 
                  value={formData.confirmPassword} onChange={handleChange} required dir="ltr" disabled={isLoading}
                />
              </div>
              
              <div className="col-md-2 mt-md-4 pt-md-2">
                <button type="submit" className="btn btn-success w-100 fw-bold" disabled={isLoading}>
                  {isLoading ? 'جاري الحفظ...' : (
                    <>حفظ <IconArrowLeft size={18} className="ms-1" /></>
                  )}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
