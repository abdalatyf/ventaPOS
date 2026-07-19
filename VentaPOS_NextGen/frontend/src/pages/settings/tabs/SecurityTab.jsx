import React, { useState } from 'react';
import { IconShieldLock, IconArrowLeft } from '@tabler/icons-react';
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

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.newPassword !== formData.confirmPassword) {
      setError('كلمة المرور الجديدة غير متطابقة!');
      setSuccess('');
      return;
    }
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await api.post('/auth/change-password/', {
        old_password: formData.oldPassword,
        new_password: formData.newPassword
      });
      setSuccess('تم تغيير كلمة المرور بنجاح');
      setFormData({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      setError(err.response?.data?.error || 'حدث خطأ أثناء تغيير كلمة المرور');
    } finally {
      setIsLoading(false);
    }
  };

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
        
        <form onSubmit={handleSubmit}>
          <div className="row g-3 align-items-start">
            <div className="col-md-4">
              <label className="form-label fw-bold">كلمة المرور الحالية</label>
              <input 
                type="password" 
                className="form-control" 
                name="oldPassword" 
                value={formData.oldPassword} 
                onChange={handleChange} 
                required 
                placeholder="******" 
                dir="ltr"
                disabled={isLoading}
              />
            </div>
            
            <div className="col-md-3">
              <label className="form-label fw-bold">كلمة المرور الجديدة</label>
              <input 
                type="password" 
                className="form-control" 
                name="newPassword" 
                value={formData.newPassword} 
                onChange={handleChange} 
                required 
                placeholder="******" 
                dir="ltr"
                disabled={isLoading}
              />
              <div className="form-text small">يفضل أن تكون قوية ومعقدة.</div>
            </div>
            
            <div className="col-md-3">
              <label className="form-label fw-bold">تأكيد الجديدة</label>
              <input 
                type="password" 
                className="form-control" 
                name="confirmPassword" 
                value={formData.confirmPassword} 
                onChange={handleChange} 
                required 
                placeholder="******" 
                dir="ltr"
                disabled={isLoading}
              />
            </div>
            
            <div className="col-md-2 mt-md-4 pt-md-2">
              <button type="submit" className="btn btn-warning w-100 fw-bold" disabled={isLoading}>
                {isLoading ? 'جاري التغيير...' : (
                  <>تغيير <IconArrowLeft size={18} className="ms-1" /></>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
