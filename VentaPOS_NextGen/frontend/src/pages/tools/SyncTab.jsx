import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  IconDeviceMobile, IconCloudUpload, IconDownload, IconCheck, 
  IconRefresh, IconUsb, IconChecklist, IconPencil, IconTrash
} from '@tabler/icons-react';
import Swal from 'sweetalert2';
import api from '../../api';
import AppAutocomplete from '../../components/common/AppAutocomplete';
import { alertDialog } from '../../utils/dialogUtils';

const SyncTab = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [pendingReceipts, setPendingReceipts] = useState([]);
  const [salespeople, setSalespeople] = useState([]);
  const [selectedSalesperson, setSelectedSalesperson] = useState('');
  const [salespersonText, setSalespersonText] = useState('');

  useEffect(() => {
    fetchPendingReceipts();
    fetchSalespeople();
  }, []);

  const fetchPendingReceipts = async () => {
    try {
      const res = await api.get('/tools/sync/pending-receipts/');
      setPendingReceipts(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error('Failed to fetch pending receipts:', err);
    }
  };

  const fetchSalespeople = async () => {
    try {
      const branchId = localStorage.getItem('branchId');
      const params = branchId ? { branch_id: branchId } : {};
      const res = await api.get('/salespersons/', { params });
      setSalespeople(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error('Failed to fetch salespersons:', err);
    }
  };

  const toggleDevice = async (id, currentStatus) => {
    try {
      await api.patch(`/salespersons/${id}/`, {
        is_device_active: !currentStatus
      });
      fetchSalespeople();
      Swal.fire({
        icon: 'success',
        title: !currentStatus ? 'تم تفعيل الجهاز' : 'تم إيقاف الجهاز',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 2000
      });
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'خطأ',
        text: 'فشل تغيير حالة الجهاز'
      });
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.post(`/tools/sync/approve-pending/${id}/`);
      fetchPendingReceipts();
      Swal.fire({
        icon: 'success',
        title: 'تم اعتماد الفاتورة وتحديث المخزون بنجاح',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000
      });
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'فشل الاعتماد',
        text: err.response?.data?.error || 'حدث خطأ أثناء اعتماد الفاتورة'
      });
    }
  };

  const handleEditPending = (id) => {
    navigate(`/pos?edit=${id}`);
  };

  const handleDeletePending = (id) => {
    Swal.fire({
      title: 'هل أنت متأكد؟',
      text: 'هل تريد حذف هذه الفاتورة المعلقة؟',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'نعم، احذف',
      cancelButtonText: 'إلغاء'
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await api.delete(`/receipts/${id}/`);
          fetchPendingReceipts();
          Swal.fire({
            icon: 'success',
            title: 'تم حذف الفاتورة بنجاح',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000
          });
        } catch (err) {
          Swal.fire({
            icon: 'error',
            title: 'خطأ',
            text: err.response?.data?.error || 'فشل حذف الفاتورة المعلقة'
          });
        }
      }
    });
  };

  const downloadJson = async () => {
    if (!selectedSalesperson) {
      Swal.fire({
        icon: 'info',
        title: 'يرجى اختيار المندوب',
        text: 'يرجى اختيار المندوب من القائمة أولاً لتخصيص ملف الموبايل.'
      });
      return;
    }
    try {
      const res = await api.get(`/tools/sync/export-items/?salesperson_id=${selectedSalesperson}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'mobile_config.json');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'خطأ',
        text: err.response?.data?.error || 'فشل تنزيل ملف الإعدادات'
      });
    }
  };

  const uploadJson = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('receipts_file', file);
    try {
      const res = await api.post('/tools/sync/import-receipts/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      Swal.fire({
        icon: 'success',
        title: 'تم الاستيراد',
        text: res.data?.message || 'تم رفع الفواتير بنجاح للمعالجة والاعتماد'
      });
      fetchPendingReceipts();
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'فشل الاستيراد',
        text: err.response?.data?.error || 'حدث خطأ أثناء استيراد الفواتير'
      });
    } finally {
      e.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="text-center p-5">
        <div className="spinner-border text-primary" />
      </div>
    );
  }

  return (
    <div dir="rtl">
      <div className="row g-4">
        {/* Offline Section (USB & JSON File Sync) */}
        <div className="col-12">
          <div className="card shadow-sm border border-secondary-subtle">
            <div className="card-header bg-white border-bottom-0 pt-4 pb-2 px-4">
              <h3 className="card-title fw-bold text-dark d-flex align-items-center">
                <IconDeviceMobile className="me-2 text-primary" /> المزامنة اليدوية للموبايل عبر USB أو ملفات JSON
              </h3>
            </div>
            <div className="card-body px-4">
              <p className="text-muted small mb-4">
                تُستخدم هذه الأدوات لتصدير الأصناف والعملاء إلى أجهزة الموبايل الميدانية واستيراد الفواتير بدون إنترنت per Red Line #1.
              </p>
              
              <div className="row g-4">
                <div className="col-md-6 border-start">
                  <h5 className="fw-bold text-secondary mb-3">1. ملف تهيئة الموبايل</h5>
                  <p className="text-muted small mb-2">يرجى اختيار المندوب لتخصيص ملف الإعدادات الخاص به:</p>
                  <div className="mb-3">
                    <AppAutocomplete
                      items={salespeople}
                      value={salespersonText}
                      onChange={(text) => {
                        setSalespersonText(text);
                        if (!text) setSelectedSalesperson('');
                      }}
                      onSelect={(item) => {
                        setSelectedSalesperson(item ? item.id : '');
                        setSalespersonText(item ? item.name : '');
                      }}
                      placeholder="-- ابحث عن المندوب أو اختر من القائمة --"
                      className="form-control border-secondary-subtle"
                    />
                  </div>
                  <div className="d-flex gap-2">
                    <button onClick={downloadJson} className="btn btn-outline-primary w-100">
                      <IconDownload className="me-2" /> تنزيل ملف الإعدادات
                    </button>
                    <button 
                      className="btn btn-outline-secondary w-100" 
                      onClick={() => alertDialog({ title: 'نقل عبر كابل USB', text: 'سيتم نقل الإعدادات مباشرة إلى جهاز الموبايل المتصل.' })}
                    >
                      <IconUsb className="me-2" /> نقل عبر USB
                    </button>
                  </div>
                </div>

                <div className="col-md-6">
                  <h5 className="fw-bold text-secondary mb-3">2. استيراد الفواتير من الموبايل</h5>
                  <p className="text-muted small mb-2">رفع ملف الفواتير المستخرجة من جهاز المندوب الميداني:</p>
                  <div className="d-flex gap-2 mt-4">
                    <label className="btn btn-primary w-100 cursor-pointer">
                      <IconCloudUpload className="me-2" /> رفع ملف JSON
                      <input type="file" accept=".json" className="d-none" onChange={uploadJson} />
                    </label>
                    <button 
                      className="btn btn-secondary w-100" 
                      onClick={() => alertDialog({ title: 'سحب عبر كابل USB', text: 'سيتم قراءة الفواتير مباشرة من جهاز الموبايل المتصل.' })}
                    >
                      <IconUsb className="me-2" /> سحب عبر USB
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pending Receipts Table */}
      <div className="card shadow-sm border border-secondary-subtle mt-4">
        <div className="card-header bg-white d-flex justify-content-between align-items-center py-3 px-4">
          <h4 className="fw-bold text-dark m-0 d-flex align-items-center gap-2">
            <IconChecklist className="text-primary" />
            الفواتير المعلقة بانتظار الاعتماد
            {pendingReceipts.length > 0 && (
              <span className="badge bg-warning text-dark rounded-pill px-2">
                {pendingReceipts.length}
              </span>
            )}
          </h4>
          <button className="btn btn-sm btn-outline-secondary" onClick={fetchPendingReceipts}>
            <IconRefresh size={16} className="me-1" /> تحديث الفواتير
          </button>
        </div>
        <div className="card-body p-0">
          {pendingReceipts.length === 0 ? (
            <div className="p-4 text-center text-muted">
              <IconCheck className="text-success me-2" />
              لا توجد فواتير معلقة حالياً بانتظار الاعتماد.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-bordered table-vcenter table-hover table-sm text-nowrap tabular-nums mb-0">
                <thead className="bg-light">
                  <tr>
                    <th className="border-secondary-subtle text-center">#</th>
                    <th className="border-secondary-subtle text-start px-3">العميل</th>
                    <th className="border-secondary-subtle text-center">المبلغ</th>
                    <th className="border-secondary-subtle text-center">المصدر</th>
                    <th className="border-secondary-subtle text-center">التاريخ</th>
                    <th className="border-secondary-subtle text-center">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingReceipts.map((p, idx) => (
                    <tr key={p.id}>
                      <td className="text-center">{idx + 1}</td>
                      <td className="text-start px-3 fw-bold">{p.customer_name || 'عميل نقدي'}</td>
                      <td className="text-center text-primary fw-bold">{Math.round(Number(p.total_amount || 0))} ج.م</td>
                      <td className="text-center">
                        <span className="badge bg-secondary-lt">{p.source || 'USB'}</span>
                      </td>
                      <td className="text-center text-muted small">
                        {p.created_at ? new Date(p.created_at).toLocaleString('en-US') : '—'}
                      </td>
                      <td className="text-center">
                        <div className="d-flex align-items-center justify-content-center gap-2">
                          <button 
                            className="btn btn-sm btn-success d-flex align-items-center gap-1"
                            onClick={() => handleApprove(p.id)}
                            title="اعتماد الفاتورة وتطبيقها على المخزون"
                          >
                            <IconCheck size={14} /> اعتماد
                          </button>
                          <button 
                            className="btn btn-sm btn-primary d-flex align-items-center gap-1"
                            onClick={() => handleEditPending(p.id)}
                            title="مراجعة وتعديل بيانات الفاتورة في نقطة البيع"
                          >
                            <IconPencil size={14} /> تعديل
                          </button>
                          <button 
                            className="btn btn-sm btn-outline-danger d-flex align-items-center gap-1"
                            onClick={() => handleDeletePending(p.id)}
                            title="حذف الفاتورة المعلقة"
                          >
                            <IconTrash size={14} /> حذف
                          </button>
                        </div>
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
  );
};

export default SyncTab;
