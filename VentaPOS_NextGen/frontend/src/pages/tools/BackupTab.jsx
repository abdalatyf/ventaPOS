import React, { useState } from 'react';
import { IconDatabaseExport, IconDatabaseImport, IconShieldCheck, IconAlertCircle } from '@tabler/icons-react';
import axios from 'axios';

const BackupTab = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://127.0.0.1:8000/api/v1/tools/backup/download/', {
        headers: { Authorization: `Token ${token}` },
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
    } catch (err) {
      alert("فشل تنزيل النسخة الاحتياطية");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('backup_file', file);

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('http://127.0.0.1:8000/api/v1/tools/backup/upload/', formData, {
        headers: { Authorization: `Token ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      setResult({ type: 'success', message: res.data.message });
      setFile(null);
    } catch (err) {
      setResult({ type: 'error', message: err.response?.data?.error || 'حدث خطأ غير متوقع' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="row g-4">
      {/* Download Backup */}
      <div className="col-md-6">
        <div className="card h-100 border-0 shadow-sm rounded-4 text-center p-4 hover-shadow transition-all">
          <div className="card-body">
            <div className="avatar avatar-xl bg-success-lt rounded-circle mb-4 mx-auto">
              <IconDatabaseExport size={36} className="text-success" />
            </div>
            <h3 className="fw-bold text-dark mb-2">تنزيل نسخة احتياطية</h3>
            <p className="text-muted small mb-4 px-3">
              قم بحفظ نسخة احتياطية (Hot Backup) من كافة بيانات النظام الحالية لتأمينها والاحتفاظ بها محلياً.
            </p>
            <button className="btn btn-success btn-lg rounded-pill px-5 fw-bold" onClick={handleDownload}>
              تنزيل الآن
            </button>
          </div>
        </div>
      </div>

      {/* Restore Backup */}
      <div className="col-md-6">
        <div className="card h-100 border-0 shadow-sm rounded-4 p-4 text-center hover-shadow transition-all">
          <div className="card-body">
            <div className="avatar avatar-xl bg-danger-lt rounded-circle mb-4 mx-auto">
              <IconDatabaseImport size={36} className="text-danger" />
            </div>
            <h3 className="fw-bold text-dark mb-2">استعادة النظام</h3>
            <p className="text-muted small mb-4 px-3">
              ارفع ملف نسخة سابقة. سيقوم النظام بفحص الملف آلياً (Integrity Check) وتطبيقه بأمان عند إعادة التشغيل.
            </p>
            
            <form onSubmit={handleUpload}>
              <div className="input-group mb-3 px-4">
                <input 
                  type="file" 
                  className="form-control" 
                  accept=".sqlite3,.db" 
                  onChange={(e) => setFile(e.target.files[0])}
                  disabled={uploading}
                  required
                />
              </div>
              <button 
                type="submit" 
                className="btn btn-danger btn-lg rounded-pill px-5 fw-bold"
                disabled={!file || uploading}
              >
                {uploading ? 'جاري فحص ورفع النسخة...' : 'استعادة النظام'}
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
