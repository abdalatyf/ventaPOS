import React, { useState, useEffect } from 'react';
import { IconCalendarCheck, IconCheck, IconX, IconCloudCheck } from '@tabler/icons-react';
import MachineIdDisplay from '../../../components/settings/MachineIdDisplay';
import LicenseKeyInput from '../../../components/settings/LicenseKeyInput';
import api from '../../../api';

export default function SubscriptionTab() {
  const [machineId, setMachineId] = useState('جاري التحميل...');
  const [licenseInfo, setLicenseInfo] = useState({
    isValid: false,
    expiryDate: null,
    daysRemaining: 0,
    isOnlineActive: false,
    onlineExpiryDate: null,
    totalBalance: 0
  });
  const [isActivating, setIsActivating] = useState(false);

  const fetchLicenseStatus = async () => {
    try {
      const response = await api.get('/license/status/');
      const data = response.data;
      if (data) {
        setMachineId(data.machine_id || 'غير متوفر');
        
        let days = 0;
        if (data.expiry_date) {
          const diff = new Date(data.expiry_date).getTime() - new Date().getTime();
          days = Math.max(0, Math.ceil(diff / (1000 * 3600 * 24)));
        }

        setLicenseInfo({
          isValid: data.status === 'active',
          expiryDate: data.expiry_date,
          daysRemaining: days,
          totalBalance: data.total_invoices_balance || 0,
          isOnlineActive: false, // Not implemented in current API response
          onlineExpiryDate: null
        });
      }
    } catch (error) {
      console.error("Failed to fetch license status", error);
    }
  };

  useEffect(() => {
    fetchLicenseStatus();
  }, []);

  const handleActivation = async (code) => {
    setIsActivating(true);
    try {
      const response = await api.post('/license/activate/', { license_code: code });
      alert(response.data?.message || 'تم التفعيل بنجاح');
      await fetchLicenseStatus();
    } catch (error) {
      alert(error.response?.data?.error || 'حدث خطأ أثناء التفعيل');
    } finally {
      setIsActivating(false);
    }
  };

  const historyRecords = [
    { id: 1, type: 'تفعيل جديد', product: 'رخصة محلية', date: '2024-01-01 10:00', status: 'ناجح' },
    { id: 2, type: 'تجديد', product: 'خدمات الأونلاين', date: '2025-01-05 14:30', status: 'ناجح' }
  ];

  return (
    <div className="animate__animated animate__fadeIn">
      {/* Machine ID */}
      <MachineIdDisplay machineId={machineId} />

      {/* Subscription Cards */}
      <div className="row mb-4">
        {/* Expiry Card */}
        <div className="col-md-4 mb-3">
          <div className="card text-white bg-info h-100 shadow-sm border-0">
            <div className="card-body text-center">
              <h1 className="display-6"><IconCalendarCheck size={48} /></h1>
              <h6 className="card-title mt-2 opacity-75">صلاحية النظام</h6>
              <p className="card-text fw-bold fs-5">
                {licenseInfo.expiryDate ? `حتى ${licenseInfo.expiryDate}` : 'مدى الحياة ∞'}
              </p>
              {licenseInfo.expiryDate && (
                <small className="badge bg-white text-info rounded-pill px-3">
                  {licenseInfo.daysRemaining > 0 ? `متبقي ${licenseInfo.daysRemaining} يوم` : 'منتهي'}
                </small>
              )}
            </div>
          </div>
        </div>

        {/* Status Card */}
        <div className="col-md-4 mb-3">
          <div className={`card text-white ${licenseInfo.isValid ? 'bg-primary' : 'bg-danger'} h-100 shadow-sm border-0`}>
            <div className="card-body text-center">
              <h1 className="display-6">
                {licenseInfo.isValid ? <IconCheck size={48} /> : <IconX size={48} />}
              </h1>
              <h6 className="card-title mt-2 opacity-75">حالة النظام</h6>
              <p className="card-text fw-bold fs-5">
                {licenseInfo.isValid ? 'ساري ويعمل' : 'منتهي / متوقف'}
              </p>
            </div>
          </div>
        </div>

        {/* Online Services Card */}
        <div className="col-md-4 mb-3">
          <div className={`card text-white ${licenseInfo.isOnlineActive ? 'bg-success' : 'bg-secondary'} h-100 shadow-sm border-0`}>
            <div className="card-body text-center">
              <h1 className="display-6"><IconCloudCheck size={48} /></h1>
              <h6 className="card-title mt-2 opacity-75">خدمات الأونلاين</h6>
              <p className="card-text fw-bold fs-5">
                {licenseInfo.isOnlineActive ? 'نشطة' : 'غير مفعلة'}
              </p>
              {licenseInfo.isOnlineActive && (
                <small className="badge bg-white text-success rounded-pill px-3">
                  تنتهي: {licenseInfo.onlineExpiryDate}
                </small>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Activation Area */}
      <div className="card shadow border-success mb-4 border-0">
        <div className="card-header bg-success text-white fw-bold">
          ⚡ منطقة التفعيل الموحدة
        </div>
        <div className="card-body py-5 bg-light">
          <LicenseKeyInput onSubmit={handleActivation} isLoading={isActivating} />
        </div>
      </div>

      {/* History Table */}
      <div className="card shadow-sm border-0 mb-4">
        <div className="card-header bg-white fw-bold text-muted border-bottom-0">
          سجل العمليات السابقة
        </div>
        <div className="table-responsive">
          <table className="table table-striped table-hover mb-0 text-center align-middle">
            <thead className="table-light">
              <tr>
                <th className="py-3">العملية</th>
                <th>التفاصيل</th>
                <th>التاريخ</th>
                <th>ملاحظات</th>
              </tr>
            </thead>
            <tbody>
              {historyRecords.length > 0 ? (
                historyRecords.map(record => (
                  <tr key={record.id}>
                    <td className="py-3">
                      <span className="badge bg-secondary rounded-pill px-3">{record.type}</span>
                    </td>
                    <td className="fw-bold">{record.product}</td>
                    <td className="text-muted small" dir="ltr">{record.date}</td>
                    <td><span className="text-muted">{record.status}</span></td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="text-muted py-4">سيبدأ السجل بالظهور مع العملية القادمة.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
