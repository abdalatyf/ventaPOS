import React, { useState, useEffect } from 'react';
import { IconDeviceMobile, IconCloudUpload, IconDownload, IconCheck, IconAlertTriangle, IconRefresh, IconUsb, IconCloudDataConnection } from '@tabler/icons-react';
import axios from 'axios';

const SyncTab = () => {
  const [isOnlineEnabled, setIsOnlineEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pendingReceipts, setPendingReceipts] = useState([]);
  const [salespeople, setSalespeople] = useState([]);
  const [selectedSalesperson, setSelectedSalesperson] = useState('');
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchLicenseStatus();
    fetchPendingReceipts();
    fetchSalespeople();
  }, []);

  const fetchLicenseStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://127.0.0.1:8000/api/v1/license/status/', {
        headers: { Authorization: `Token ${token}` }
      });
      // Assuming response has is_online or similar. We default to true if it succeeds for now
      setIsOnlineEnabled(res.data.is_active && res.data.is_pro);
    } catch (err) {
      console.error("Failed to fetch license", err);
      // Fallback
      setIsOnlineEnabled(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingReceipts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://127.0.0.1:8000/api/v1/pending-external-receipts/', {
        headers: { Authorization: `Token ${token}` }
      });
      setPendingReceipts(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSalespeople = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://127.0.0.1:8000/api/v1/salespersons/', {
        headers: { Authorization: `Token ${token}` }
      });
      setSalespeople(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error(err);
    }
  };

  const toggleDevice = async (id, currentStatus) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`http://127.0.0.1:8000/api/v1/salespersons/${id}/`, {
        is_device_active: !currentStatus
      }, {
        headers: { Authorization: `Token ${token}` }
      });
      fetchSalespeople();
    } catch (err) {
      alert("فشل تغيير حالة الجهاز");
    }
  };

  const handleApprove = async (id) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`http://127.0.0.1:8000/api/v1/tools/sync/approve-pending/${id}/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      fetchPendingReceipts();
      alert('تم الاعتماد بنجاح!');
    } catch (err) {
      alert(err.response?.data?.error || 'حدث خطأ');
    }
  };

  const downloadJson = async () => {
    if (!selectedSalesperson) {
      alert("يرجى اختيار المندوب من القائمة أولاً لتخصيص ملف الموبايل");
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`http://127.0.0.1:8000/api/v1/tools/sync/export-items/?salesperson_id=${selectedSalesperson}`, {
        headers: { Authorization: `Token ${token}` },
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'mobile_config.json');
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      alert(err.response?.data?.error || "فشل تنزيل ملف الإعدادات");
    }
  };

  const uploadJson = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('receipts_file', file);
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://127.0.0.1:8000/api/v1/tools/sync/import-receipts/', formData, {
        headers: { Authorization: `Token ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      alert('تم رفع الفواتير بنجاح للمعالجة');
      fetchPendingReceipts();
    } catch (err) {
      alert(err.response?.data?.error || 'حدث خطأ');
    }
  };

  if (loading) return <div className="text-center p-5"><div className="spinner-border text-primary" /></div>;

  return (
    <div>
      <div className="row g-4">
        {/* Offline Section */}
        <div className="col-md-6">
          <div className="card h-100 border-0 shadow-sm rounded-4">
            <div className="card-header bg-white border-bottom-0 pt-4 pb-2 px-4">
              <h3 className="card-title fw-bold text-dark d-flex align-items-center">
                <IconDeviceMobile className="me-2 text-primary" /> الموبايل المحلّي (Offline)
              </h3>
            </div>
            <div className="card-body px-4">
              <p className="text-muted small mb-4">
                تُستخدم هذه الأدوات لنقل الأصناف واستقبال الفواتير من أجهزة الموبايل التي تعمل بدون إنترنت.
              </p>
              
              <div className="mb-4">
                <h5 className="fw-bold text-secondary mb-3">1. ملف تهيئة الموبايل</h5>
                <p className="text-muted small mb-2">يرجى اختيار المندوب لتخصيص ملف الإعدادات الخاص به:</p>
                <div className="mb-3">
                  <select 
                    className="form-select border-primary" 
                    value={selectedSalesperson} 
                    onChange={e => setSelectedSalesperson(e.target.value)}
                  >
                    <option value="">-- اختر المندوب --</option>
                    {(salespeople || []).map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div className="d-flex gap-2">
                  <button onClick={downloadJson} className="btn btn-outline-primary w-100 rounded-3">
                    <IconDownload className="me-2" /> تنزيل ملف الإعدادات
                  </button>
                  <button className="btn btn-outline-secondary w-100 rounded-3" onClick={() => alert("سيتم نقل الإعدادات مباشرة عبر الكابل")}>
                    <IconUsb className="me-2" /> نقل عبر USB
                  </button>
                </div>
              </div>

              <div>
                <h5 className="fw-bold text-secondary mb-3">2. استيراد الفواتير من الموبايل</h5>
                <div className="d-flex gap-2">
                  <label className="btn btn-primary w-100 rounded-3 cursor-pointer">
                    <IconCloudUpload className="me-2" /> رفع ملف JSON
                    <input type="file" accept=".json" className="d-none" onChange={uploadJson} />
                  </label>
                  <button className="btn btn-secondary w-100 rounded-3" onClick={() => alert("سيتم قراءة الفواتير من الجهاز المتصل")}>
                    <IconUsb className="me-2" /> سحب عبر USB
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Online Section */}
        <div className="col-md-6">
          <div className="card h-100 border-0 shadow-sm rounded-4 position-relative overflow-hidden">
            {!isOnlineEnabled && (
              <div className="position-absolute w-100 h-100 d-flex flex-column align-items-center justify-content-center" style={{ background: 'rgba(255,255,255,0.85)', zIndex: 10, backdropFilter: 'blur(3px)' }}>
                <IconAlertTriangle size={48} className="text-warning mb-3" />
                <h3 className="fw-bold text-dark">غير متاح في باقتك</h3>
                <p className="text-muted text-center px-4">ميزة الربط السحابي والأجهزة المساعدة الأونلاين تتطلب اشتراك باقة الأونلاين (برو).</p>
                <button className="btn btn-warning rounded-pill px-4 mt-2">تفعيل أو ترقية الباقة</button>
              </div>
            )}
            <div className="card-header bg-white border-bottom-0 pt-4 pb-2 px-4 d-flex justify-content-between align-items-center">
              <h3 className="card-title fw-bold text-dark d-flex align-items-center mb-0">
                <IconCloudDataConnection className="me-2 text-success" /> الربط السحابي (Online)
                <span className={`badge ms-3 ${isOnlineEnabled ? 'bg-success' : 'bg-secondary'}`}>
                  {isOnlineEnabled ? 'متصل' : 'غير متصل'}
                </span>
              </h3>
              <button className="btn btn-sm btn-outline-success rounded-pill" onClick={() => { fetchPendingReceipts(); fetchSalespeople(); }}>
                <IconRefresh size={16} className="me-1" /> تحديث
              </button>
            </div>
            <div className="card-body px-4">
              <p className="text-muted small mb-4">
                إدارة الأجهزة المساعدة واعتماد الفواتير القادمة عبر الإنترنت.
              </p>
              
              <h5 className="fw-bold text-secondary mb-3">إدارة الأجهزة (الموبايلات)</h5>
              <div className="table-responsive mb-4">
                <table className="table table-vcenter table-sm">
                  <thead>
                    <tr>
                      <th>اسم المندوب / الجهاز</th>
                      <th>حالة الاتصال</th>
                      <th>إجراء</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(salespeople || []).map(s => (
                      <tr key={s.id}>
                        <td>{s.name}</td>
                        <td>
                          {s.is_device_active ? (
                            <span className="badge bg-success-lt">نشط</span>
                          ) : (
                            <span className="badge bg-danger-lt">موقوف</span>
                          )}
                        </td>
                        <td>
                          <button 
                            className={`btn btn-sm ${s.is_device_active ? 'btn-outline-danger' : 'btn-outline-success'} rounded-3`}
                            onClick={() => toggleDevice(s.id, s.is_device_active)}
                          >
                            {s.is_device_active ? 'إيقاف' : 'تفعيل'}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {salespeople?.length === 0 && (
                      <tr><td colSpan="3" className="text-center text-muted">لا توجد أجهزة مسجلة</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              <h5 className="fw-bold text-secondary mb-3 mt-4">الفواتير المعلقة بانتظار الاعتماد</h5>
              {pendingReceipts?.length === 0 ? (
                <div className="alert alert-success d-flex align-items-center border-0 rounded-3 bg-success-lt">
                  <IconCheck className="me-2" /> لا توجد فواتير معلقة حالياً.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-vcenter table-hover card-table">
                    <thead>
                      <tr>
                        <th>المصدر</th>
                        <th>التاريخ</th>
                        <th>الإجراء</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(pendingReceipts || []).map(p => (
                        <tr key={p.id}>
                          <td>{p.source}</td>
                          <td>{new Date(p.created_at).toLocaleString('ar-EG')}</td>
                          <td>
                            <button className="btn btn-sm btn-success rounded-3" onClick={() => handleApprove(p.id)}>
                              اعتماد
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SyncTab;
