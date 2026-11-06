import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { IconDatabase } from '@tabler/icons-react';
import { getLicenseStatus } from '../api';
import QuickRestoreModal from './common/QuickRestoreModal';

export default function DemoBanner() {
  const [isDemo, setIsDemo] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    let isMounted = true;

    const checkStatus = (forceRefresh = false) => {
      getLicenseStatus(forceRefresh).then(data => {
        if (isMounted) {
          setIsDemo(Boolean(data?.is_demo));
        }
      }).catch(() => {
        if (isMounted) {
          setIsDemo(false);
        }
      });
    };

    checkStatus();
    const handleUpdate = () => checkStatus(true);
    window.addEventListener('license_updated', handleUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener('license_updated', handleUpdate);
    };
  }, []);

  if (!isDemo) return null;
  
  // Don't show on init or login
  if (location.pathname === '/init' || location.pathname === '/login') return null;

  return (
    <>
      <div className="bg-warning text-dark text-center py-2 px-3 fw-bold shadow-sm d-flex justify-content-center align-items-center flex-wrap gap-2" style={{ zIndex: 1050, position: 'relative' }}>
        <span>
          ⚠️ أنت الآن في الوضع التجريبي (لن يتم حفظ البيانات بعد إغلاق البرنامج). لتجربة النسخة الكاملة مجاناً لمدة شهرين، تواصل معنا.
        </span>
        <div className="d-flex align-items-center gap-2">
          <button 
            className="btn btn-sm btn-dark fw-bold"
            onClick={() => navigate('/settings?tab=subscription')}
          >
            تفعيل البرنامج
          </button>
          <button 
            className="btn btn-sm btn-outline-dark fw-bold d-flex align-items-center gap-1"
            onClick={() => setShowRestoreModal(true)}
          >
            <IconDatabase size={16} />
            استعادة نسخة احتياطية
          </button>
        </div>
      </div>
      <QuickRestoreModal isOpen={showRestoreModal} onClose={() => setShowRestoreModal(false)} />
    </>
  );
}
