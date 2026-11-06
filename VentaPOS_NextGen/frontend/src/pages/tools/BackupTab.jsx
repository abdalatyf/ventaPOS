import React, { useState } from 'react';
import { IconDatabaseExport, IconDatabaseImport, IconShieldCheck, IconAlertCircle } from '@tabler/icons-react';
import Swal from 'sweetalert2';
import api from '../../api';

const BackupTab = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState(null);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await api.get('/tools/backup/download/', {
        responseType: 'blob'
      });
      
      const contentDisposition = res.headers['content-disposition'];
      let filename = 'Backup.sqlite3';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      Swal.fire({
        icon: 'error',
        title: 'خطأ',
        text: 'فشل تنزيل النسخة الاحتياطية. يرجى مراجعة إعدادات الخادم.'
      });
    } finally {
      setDownloading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    Swal.fire({
      title: 'تحذير هام: استعادة قاعدة البيانات',
      text: 'استعادة النسخة الاحتياطية ستستبدل البيانات الحالية بالكامل ببيانات الملف المرفوع. هل أنت متأكد من رغبتك في المتابعة؟',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#6c757d',
      confirmButtonText: 'نعم، استعد البيانات الآن',
      cancelButtonText: 'إلغاء'
    }).then(async (swalResult) => {
      if (swalResult.isConfirmed) {
        setUploading(true);
        setResult(null);

        const formData = new FormData();
        formData.append('backup_file', file);

        try {
          const res = await api.post('/tools/backup/upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          setResult({ type: 'success', message: res.data.message });
          setFile(null);
          
          if (res.data?.status === 'pending_restart') {
            Swal.fire({
              icon: 'warning',
              title: 'إعادة تشغيل البرنامج مطلوبة',
              text: res.data.message,
              confirmButtonText: 'حسناً، فهمت',
              confirmButtonColor: '#123F68'
            });
          } else {
            Swal.fire({
              icon: 'success',
              title: 'تمت الاستعادة بنجاح',
              text: res.data.message,
              confirmButtonText: 'تحديث البرنامج الآن'
            }).then(() => {
              window.location.reload();
            });
          }
        } catch (err) {
          const errorMsg = err.response?.data?.error || 'حدث خطأ غير متوقع أثناء استعادة النسخة';
          setResult({ type: 'error', message: errorMsg });
          Swal.fire({
            icon: 'error',
            title: 'فشل الاستعادة',
            text: errorMsg
          });
        } finally {
          setUploading(false);
        }
      }
    });
  };

  return (
    <div className="row g-4" dir="rtl">
      {/* Download Backup */}
      <div className="col-md-6">
        <div className="card h-100 shadow-sm border border-secondary-subtle text-center p-4">
          <div className="card-body">
            <div className="avatar avatar-xl bg-success-lt rounded-circle mb-4 mx-auto">
              <IconDatabaseExport size={36} className="text-success" />
            </div>
            <h3 className="fw-bold text-dark mb-2">تنزيل نسخة احتياطية</h3>
            <p className="text-muted small mb-4 px-3">
              قم بحفظ نسخة احتياطية فورية (Hot Backup) من كافة بيانات النظام الحالية لتأمينها والاحتفاظ بها محلياً.
            </p>
            <button 
              className="btn btn-success btn-lg px-5 fw-bold" 
              onClick={handleDownload}
              disabled={downloading}
            >
              {downloading ? 'جاري تجهيز النسخة...' : 'تنزيل الآن'}
            </button>
          </div>
        </div>
      </div>

      {/* Restore Backup */}
      <div className="col-md-6">
        <div className="card h-100 shadow-sm border border-secondary-subtle p-4 text-center">
          <div className="card-body">
            <div className="avatar avatar-xl bg-danger-lt rounded-circle mb-4 mx-auto">
              <IconDatabaseImport size={36} className="text-danger" />
            </div>
            <h3 className="fw-bold text-dark mb-2">استعادة النظام</h3>
            <p className="text-muted small mb-4 px-3">
              ارفع ملف نسخة سابقة (.sqlite3 أو .db). سيقوم النظام بفحص الملف آلياً وتطبيقه بأمان فوراً.
            </p>
            
            <form onSubmit={handleUpload}>
              <div className="input-group mb-3 px-4">
                <input 
                  type="file" 
                  className="form-control border-secondary-subtle" 
                  accept=".sqlite3,.db" 
                  onChange={(e) => setFile(e.target.files[0])}
                  disabled={uploading}
                  required
                />
              </div>
              <button 
                type="submit" 
                className="btn btn-danger btn-lg px-5 fw-bold"
                disabled={!file || uploading}
              >
                {uploading ? 'جاري فحص وتطبيق النسخة...' : 'استعادة النظام'}
              </button>
            </form>

            {result && (
              <div className={`alert alert-${result.type === 'success' ? 'success' : 'danger'} mt-4 d-flex align-items-center text-start border-0 rounded-3`}>
                {result.type === 'success' ? <IconShieldCheck className="me-2 flex-shrink-0" /> : <IconAlertCircle className="me-2 flex-shrink-0" />}
                <div className="fw-bold">{result.message}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackupTab;
