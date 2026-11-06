import React, { useState, useRef } from 'react';
import { IconUpload, IconDatabase, IconAlertCircle, IconCheck } from '@tabler/icons-react';
import api from '../../api';

export default function QuickRestoreModal({ isOpen, onClose }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.endsWith('.sqlite3') && !selected.name.endsWith('.db')) {
        setError('يرجى اختيار ملف نسخة احتياطية صالح بامتداد .sqlite3 أو .db');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleRestore = async () => {
    if (!file) {
      setError('يرجى اختيار ملف النسخة الاحتياطية أولاً');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    const formData = new FormData();
    formData.append('backup_file', file);

    try {
      const res = await api.post('/tools/backup/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Clear local session cache
      localStorage.removeItem('token');
      localStorage.removeItem('branchId');
      localStorage.removeItem('branchName');
      localStorage.removeItem('company_name');

      if (res.data?.pending_restart) {
        setSuccessMsg('تم تجهيز النسخة الاحتياطية بنجاح! يرجى إعادة تشغيل البرنامج لتطبيق التغييرات.');
      } else {
        setSuccessMsg(res.data?.message || 'تمت استعادة النسخة الاحتياطية بنجاح! سيتم الانتقال لتسجيل الدخول.');
      }

      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err) {
      console.error('Restore error:', err);
      setError(err.response?.data?.error || err.response?.data?.detail || 'فشل استعادة النسخة الاحتياطية.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1060 }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content text-end" dir="rtl">
          <div className="modal-header d-flex justify-content-between align-items-center">
            <h5 className="modal-title d-flex align-items-center gap-2 fw-bold text-primary">
              <IconDatabase size={22} />
              استعادة نسخة احتياطية (.sqlite3)
            </h5>
            <button type="button" className="btn-close m-0" onClick={onClose} disabled={loading}></button>
          </div>
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger d-flex align-items-center gap-2 py-2 mb-3">
                <IconAlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
                <IconCheck size={18} />
                <span>{successMsg}</span>
              </div>
            )}

            <div className="text-muted small mb-3">
              سيتم فحص ملف قاعدة البيانات واستبدال البيانات الحالية بالنسخة المحددة. (يتم أخذ لقطة أمان احتياطية تلقائياً قبل الاستبدال).
            </div>

            <div className="mb-3">
              <label className="form-label fw-bold">اختر ملف النسخة الاحتياطية:</label>
              <input
                ref={fileInputRef}
                type="file"
                className="form-control"
                accept=".sqlite3,.db"
                onChange={handleFileChange}
                disabled={loading}
              />
              {file && (
                <div className="text-success small mt-1 fw-bold">
                  الملف المحدد: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} ميجابايت)
                </div>
              )}
            </div>
          </div>
          <div className="modal-footer d-flex justify-content-between">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              إلغاء
            </button>
            <button
              type="button"
              className="btn btn-primary d-flex align-items-center gap-2 fw-bold"
              onClick={handleRestore}
              disabled={!file || loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  جاري الاستعادة...
                </>
              ) : (
                <>
                  <IconUpload size={18} />
                  بدء الاستعادة الآن
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
