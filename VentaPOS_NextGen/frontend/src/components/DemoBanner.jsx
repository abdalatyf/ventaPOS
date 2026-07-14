import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../api';

export default function DemoBanner() {
  const [isDemo, setIsDemo] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if we are in demo mode by hitting the init endpoint
    api.get('/init/').then(res => {
      if (!res.data.initialized) {
        setIsDemo(true);
      } else {
        setIsDemo(false);
      }
    }).catch(() => {
      setIsDemo(false);
    });
  }, [location.pathname]);

  if (!isDemo) return null;
  
  // Don't show on init or login
  if (location.pathname === '/init' || location.pathname === '/login') return null;

  return (
    <div className="bg-warning text-dark text-center py-2 px-3 fw-bold shadow-sm d-flex justify-content-center align-items-center" style={{ zIndex: 1050, position: 'relative' }}>
      <span className="me-3">
        ⚠️ أنت الآن في الوضع التجريبي (لن يتم حفظ البيانات بعد إغلاق البرنامج). لتجربة النسخة الكاملة مجاناً لمدة شهرين، تواصل معنا.
      </span>
      <button 
        className="btn btn-sm btn-dark ms-3 fw-bold"
        onClick={() => navigate('/init')}
      >
        تفعيل البرنامج
      </button>
    </div>
  );
}
