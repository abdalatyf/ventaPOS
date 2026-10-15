import React from 'react';
import CompanyTab from './settings/tabs/CompanyTab';
import { useNavigate } from 'react-router-dom';

export default function ActivationSetup() {
  const navigate = useNavigate();

  return (
    <div className="page page-center" style={{ backgroundColor: '#f1f5f9', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-tight py-4" style={{ maxWidth: '800px' }}>
        <div className="text-center mb-4">
          <h2 className="fw-bold mb-2">تهانينا! تم تفعيل VentaPOS بنجاح 🎉</h2>
          <p className="mb-0 opacity-75 fs-5">يرجى إدخال بيانات مؤسستك الحقيقية الآن لإضافتها على الإيصالات (يمكنك تعديلها لاحقاً).</p>
        </div>
        
        <div className="card shadow-lg border-0 rounded-4">
          <div className="card-body p-5">
            {/* We reuse CompanyTab but maybe we need a hook to know when it saves to redirect? 
                Since CompanyTab handles its own saving, we can just let it save.
                Actually, to redirect, we can add a simple wrapper or just let them click a button to continue after saving. */}
            <CompanyTab isFirstSetup={true} onSetupComplete={() => {
                navigate('/');
                window.location.reload(); // Reload to clear the SetupGuard state
            }} />
          </div>
        </div>
      </div>
    </div>
  );
}
