import React, { useEffect, useState } from 'react';
import api from '../api';

export default function SubscriptionWarningBanner() {
  const [licenseStatus, setLicenseStatus] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await api.get('/license/status/');
        if (res.data) {
          setLicenseStatus(res.data);
        }
      } catch (err) {
        console.error("Failed to fetch license status", err);
      }
    };
    
    // Check initially and also listen for updates (e.g. from POS Entry)
    fetchStatus();
    
    // Optional: Re-fetch periodically or when window gets focus
    const handleFocus = () => fetchStatus();
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  if (!licenseStatus) return null;

  // Render the warnings
  return (
    <>
      {licenseStatus.is_last_month && (
        <div className="bg-danger text-white text-center py-2 fw-bold" style={{ zIndex: 1050, position: 'relative' }}>
          الاشتراك ينتهي هذا الشهر! يرجى التواصل مع الدعم لتجديد الاشتراك لتجنب توقف النظام.
        </div>
      )}
      {licenseStatus.needs_support && (
        <div className="bg-warning text-dark text-center py-2 fw-bold" style={{ zIndex: 1050, position: 'relative' }}>
          رجاء كلم الدعم
        </div>
      )}
    </>
  );
}
