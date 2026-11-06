import React, { useState } from 'react';
import CompanyTab from './settings/tabs/CompanyTab';
import { useNavigate } from 'react-router-dom';
import { IconDatabase } from '@tabler/icons-react';
import QuickRestoreModal from '../components/common/QuickRestoreModal';

export default function ActivationSetup() {
  const navigate = useNavigate();
  const [showRestoreModal, setShowRestoreModal] = useState(false);

  return (
    <div className="page page-center" style={{ backgroundColor: '#f1f5f9', minHeight: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-tight py-4" style={{ maxWidth: '800px' }}>
        <div className="text-center mb-4">
          <h2 className="fw-bold mb-2">تهانينا! تم تفعيل VentaPOS بنجاح 🎉</h2>
          <p className="mb-0 opacity-75 fs-5">يرجى إدخال بيانات مؤسستك الحقيقية الآن لإضافتها على الإيصالات (يمكنك تعديلها لاحقاً).</p>
        </div>
        
        <div className="card shadow-lg border-0 rounded-4 mb-3">
          <div className="card-body p-5">
            <CompanyTab isFirstSetup={true} onSetupComplete={() => {
                localStorage.removeItem('branchId');
                localStorage.removeItem('branchName');
                window.dispatchEvent(new CustomEvent('license_updated'));
                navigate('/select-branch', { replace: true });
            }} />
          </div>
        </div>

        <div className="text-center">
          <button
            type="button"
            className="btn btn-outline-primary d-inline-flex align-items-center gap-2 fw-bold"
            onClick={() => setShowRestoreModal(true)}
          >
            <IconDatabase size={18} />
            أو هل تمتلك نسخة احتياطية سابقة؟ استعادة نسخة احتياطية (.sqlite3)
          </button>
        </div>
      </div>
      <QuickRestoreModal isOpen={showRestoreModal} onClose={() => setShowRestoreModal(false)} />
    </div>
  );
}
