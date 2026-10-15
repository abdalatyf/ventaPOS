import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { IconCalendarCheck, IconCheck, IconX, IconCloudCheck } from '@tabler/icons-react';
import MachineIdDisplay from '../../../components/settings/MachineIdDisplay';
import LicenseKeyInput from '../../../components/settings/LicenseKeyInput';
import api from '../../../api';

export default function SubscriptionTab() {
  const navigate = useNavigate();
  const [machineId, setMachineId] = useState('جاري التحميل...');
  const [licenseInfo, setLicenseInfo] = useState({
    isValid: false,
    expiryDate: null,
    daysRemaining: 0,
    isOnlineActive: false,
    onlineExpiryDate: null,
    is_last_month: false,
    needs_support: false
  });
  const [historyRecords, setHistoryRecords] = useState([]);
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
          isOnlineActive: false,
          onlineExpiryDate: null,
          is_last_month: data.is_last_month || false,
          needs_support: data.needs_support || false
        });
      }
      
      // Fetch history
      const historyRes = await api.get('/license-history/');
      if (historyRes.data && historyRes.data.results) {
        setHistoryRecords(historyRes.data.results);
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
      alert(response.data?.message || 'تم التفعيل بنجاح! جاري تحويلك لصفحة التهيئة.');
      navigate('/activation-setup', { replace: true });
    } catch (error) {
      alert(error.response?.data?.error || 'حدث خطأ أثناء التفعيل');
    } finally {
      setIsActivating(false);
    }
  };

  return (
    <div className="animate__animated animate__fadeIn">
      {/* Machine ID */}
      <MachineIdDisplay machineId={machineId} />

      {/* Alert Box for System Status */}
      {licenseInfo.needs_support && (
        <div className="alert alert-danger shadow-sm border-0" role="alert">
          <div className="d-flex">
            <div><IconX className="me-3" size={24} /></div>
            <div>
              <h4 className="alert-title fw-bold">تنبيه هام جداً</h4>
              <div className="text-muted">نظامك معلق حالياً، <strong>رجاء كلم الدعم</strong> في أقرب وقت.</div>
            </div>
          </div>
        </div>
      )}

      {licenseInfo.is_last_month && !licenseInfo.needs_support && (
        <div className="alert alert-warning shadow-sm border-0" role="alert">
          <div className="d-flex">
            <div><IconCalendarCheck className="me-3" size={24} /></div>
            <div>
              <h4 className="alert-title fw-bold">اقترب موعد التجديد</h4>
              <div className="text-muted">هذا هو الشهر الأخير في اشتراكك الحالي. يرجى تجديد الاشتراك لضمان عدم توقف النظام.</div>
            </div>
          </div>
        </div>
      )}

      {/* Subscription Cards */}
      <div className="row mb-4">
        {/* Expiry Card */}
        <div className="col-md-4 mb-3">
          <div className="card text-white bg-info h-100 shadow-sm border-0">
            <div className="card-body text-center">
              <h1 className="display-6"><IconCalendarCheck size={48} /></h1>
              <h6 className="card-title mt-2 opacity-75">صلاحية النظام</h6>
              <p className="card-text fw-bold fs-5">
                {!licenseInfo.isValid 
                  ? 'غير محددة' 
                  : licenseInfo.expiryDate 
                    ? `حتى ${licenseInfo.expiryDate}` 
                    : 'مدى الحياة ∞'}
              </p>
              {licenseInfo.isValid && licenseInfo.expiryDate && (
                <small className="badge bg-white text-info rounded-pill px-3">
                  {licenseInfo.daysRemaining > 0 ? `متبقي ${licenseInfo.daysRemaining} يوم` : 'منتهي'}
                </small>
              )}
            </div>
          </div>
        </div>

        {/* Status Card */}
        <div className="col-md-4 mb-3">
          <div className={`card h-100 shadow-sm border-0 ${
            licenseInfo.needs_support || !licenseInfo.isValid ? 'bg-danger text-white' : 
            licenseInfo.is_last_month ? 'bg-warning text-dark' : 'bg-primary text-white'
          }`}>
            <div className="card-body text-center">
              <h1 className="display-6">
                {licenseInfo.needs_support || !licenseInfo.isValid ? <IconX size={48} /> : 
                 licenseInfo.is_last_month ? <IconCalendarCheck size={48} /> : <IconCheck size={48} />}
              </h1>
              <h6 className="card-title mt-2 opacity-75">حالة النظام</h6>
              <p className="card-text fw-bold fs-5">
                {licenseInfo.needs_support ? 'يتطلب الدعم' :
                 !licenseInfo.isValid ? (historyRecords.length === 0 ? 'الوضع التجريبي' : 'منتهي / متوقف') :
                 licenseInfo.is_last_month ? 'الشهر الأخير' : 'ساري ويعمل'}
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
                <th className="py-3">الرقم</th>
                <th>كود التفعيل</th>
                <th>التاريخ</th>
                <th>ملاحظات</th>
              </tr>
            </thead>
            <tbody>
              {historyRecords.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-4 text-muted">لا توجد عمليات سابقة</td>
                </tr>
              ) : (
                historyRecords.map((record) => (
                  <tr key={record.id}>
                    <td className="fw-bold">{record.id}</td>
                    <td>{record.license_code || '---'}</td>
                    <td>{new Date(record.created_at).toLocaleString('ar-EG')}</td>
                    <td>
                      <span className="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-pill">
                        ناجح
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
