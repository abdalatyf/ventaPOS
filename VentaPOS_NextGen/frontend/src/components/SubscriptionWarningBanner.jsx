import React, { useEffect, useState } from 'react';
import { getLicenseStatus } from '../api';

export default function SubscriptionWarningBanner() {
  const [licenseStatus, setLicenseStatus] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchStatus = async (forceRefresh = false) => {
      try {
        const data = await getLicenseStatus(forceRefresh);
        if (isMounted && data) {
          setLicenseStatus(data);
        }
      } catch (err) {
        console.error("Failed to fetch license status", err);
      }
    };
    
    // Initial fetch from shared cache
    fetchStatus();
    
    // Only re-fetch when license actually updates or subscription changes
    const handleUpdate = () => fetchStatus(true);
    window.addEventListener('license_updated', handleUpdate);
    window.addEventListener('subscription_expired', handleUpdate);

    return () => {
      isMounted = false;
      window.removeEventListener('license_updated', handleUpdate);
      window.removeEventListener('subscription_expired', handleUpdate);
    };
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
