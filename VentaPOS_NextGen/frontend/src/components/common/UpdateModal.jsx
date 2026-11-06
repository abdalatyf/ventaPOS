import React, { useState, useEffect } from 'react';
import { 
  IconCloudDownload, 
  IconCheck, 
  IconAlertCircle, 
  IconLoader, 
  IconRefresh, 
  IconSparkles,
  IconShieldCheck
} from '@tabler/icons-react';
import api from '../../api';

/**
 * UpdateModal — Production Update Modal Dialog
 * Checks for updates against GitHub releases, displays release notes, and triggers verified updater installation.
 */
export default function UpdateModal({ isOpen, onClose }) {
  const [checking, setChecking] = useState(false);
  const [applying, setApplying] = useState(false);
  const [updateInfo, setUpdateInfo] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const checkForUpdates = async () => {
    setChecking(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const res = await api.get('/system/check-update/');
      setUpdateInfo(res.data);
    } catch (err) {
      console.error('Failed to check for updates:', err);
      setErrorMessage('تعذر الاتصال بخادم التحديثات. يرجى التأكد من اتصال الإنترنت.');
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      checkForUpdates();
    } else {
      setApplying(false);
      setErrorMessage(null);
      setSuccessMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleApplyUpdate = async () => {
    if (!updateInfo || !updateInfo.download_url) return;

    setApplying(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const payload = {
        download_url: updateInfo.download_url,
        sha256: updateInfo.sha256,
        version: updateInfo.latest_version,
      };

      const res = await api.post('/system/apply-update/', payload);
      setSuccessMessage(res.data?.message || 'تم تحميل ملف التحديث بنجاح، وجاري بدء التثبيت.');
    } catch (err) {
      console.error('Failed to apply update:', err);
      const detail = err.response?.data?.message || err.response?.data?.error || err.message || 'فشل تحميل أو تثبيت التحديث.';
      setErrorMessage(detail);
      setApplying(false);
    }
  };

  return (
    <div 
      className="modal modal-blur fade show d-block" 
      tabIndex="-1" 
      role="dialog" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)', zIndex: 1060 }}
      dir="rtl"
    >
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content shadow-lg border-0">
          
          {/* Header */}
          <div className="modal-header bg-light py-2 px-3 border-bottom">
            <h5 className="modal-title fw-bold text-dark d-flex align-items-center gap-2 m-0">
              <IconCloudDownload size={20} className="text-primary" />
              تحديثات النظام (VentaPOS Auto-Updater)
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              disabled={applying} 
              onClick={onClose} 
              aria-label="Close" 
            />
          </div>

          {/* Body */}
          <div className="modal-body p-3">
            {errorMessage && (
              <div className="alert alert-danger py-2 px-3 small d-flex align-items-center gap-2 mb-3">
                <IconAlertCircle size={18} className="flex-shrink-0" />
                <div>{errorMessage}</div>
              </div>
            )}

            {successMessage && (
              <div className="alert alert-success py-2 px-3 small d-flex align-items-center gap-2 mb-3">
                <IconCheck size={18} className="flex-shrink-0 text-success" />
                <div>{successMessage}</div>
              </div>
            )}

            {checking ? (
              <div className="text-center py-4">
                <IconLoader size={36} className="text-primary icon-spin mb-2" />
                <div className="fw-bold text-dark">جاري فحص الإصدارات الجديدة من خادم التحديثات...</div>
                <div className="text-muted small">يتم فحص مستودع التحديثات الرسمي VentaPOS Releases</div>
              </div>
            ) : updateInfo ? (
              <div>
                {/* Version Status Box */}
                <div className="p-3 bg-light rounded border mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="text-muted small fw-bold">الإصدار المثبت حالياً:</span>
                    <span className="badge bg-secondary-lt text-dark fw-bold px-2 py-1 fs-5">
                      v{updateInfo.current_version}
                    </span>
                  </div>

                  <div className="d-flex justify-content-between align-items-center">
                    <span className="text-muted small fw-bold">أحدث إصدار متوفر:</span>
                    <span className={`badge ${updateInfo.has_update ? 'bg-success text-white' : 'bg-primary-lt text-primary'} fw-bold px-2 py-1 fs-5`}>
                      v{updateInfo.latest_version}
                    </span>
                  </div>
                </div>

                {/* State: Has Update */}
                {updateInfo.has_update ? (
                  <div>
                    <div className="alert alert-success py-2 px-3 small mb-3 border-success">
                      <div className="d-flex align-items-center gap-2 fw-bold text-success mb-1">
                        <IconSparkles size={18} />
                        يتوفر تحديث جديد للنظام (v{updateInfo.latest_version})!
                      </div>
                      <div className="text-dark small">
                        {updateInfo.release_notes || 'يتضمن هذا التحديث تحسينات في الأداء وإصلاحات استقرار للنظام.'}
                      </div>
                    </div>

                    <div className="d-flex align-items-center gap-1 text-muted small mb-2">
                      <IconShieldCheck size={16} className="text-success" />
                      <span>يتم فحص التحديث رقمياً وتأكيد بصمة SHA-256 قبل بدء التثبيت تلقائياً.</span>
                    </div>
                  </div>
                ) : updateInfo.offline ? (
                  <div className="alert alert-warning py-2 px-3 small mb-3">
                    <strong>وضع عدم الاتصال:</strong> تعذر الوصول لمستودع التحديثات حالياً. تأكد من اتصال الإنترنت ثم أعد المحاولة.
                  </div>
                ) : (
                  <div className="alert alert-info py-2 px-3 small mb-3">
                    <div className="d-flex align-items-center gap-2 fw-bold mb-1">
                      <IconCheck size={18} className="text-primary" />
                      أنت تستخدم أحدث إصدار متوفر بالفعل!
                    </div>
                    <div className="text-muted small">
                      لا توجد تحديثات جديدة في الوقت الحالي. النظام محدث بآخر الميزات والإصلاحات.
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            {applying && (
              <div className="my-3 p-3 bg-light rounded border text-center">
                <IconLoader size={28} className="text-success icon-spin mb-2" />
                <div className="fw-bold text-success mb-1">جاري تحميل ملف التحديث وتأكيد بصمة الأمان...</div>
                <div className="text-muted small">سيتم إطلاق برنامج التثبيت تلقائياً فور اكتمال التحميل.</div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="modal-footer bg-light py-2 px-3 border-top d-flex justify-content-between align-items-center">
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm px-3"
              onClick={onClose}
              disabled={applying}
            >
              إغلاق
            </button>

            <div className="d-flex gap-2">
              <button
                type="button"
                className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1 px-3 fw-bold"
                onClick={checkForUpdates}
                disabled={checking || applying}
                title="إعادة فحص التحديثات"
              >
                <IconRefresh size={16} />
                <span>إعادة الفحص</span>
              </button>

              {updateInfo?.has_update && (
                <button
                  type="button"
                  className="btn btn-success btn-sm d-flex align-items-center gap-1 px-3 fw-bold text-white"
                  onClick={handleApplyUpdate}
                  disabled={applying}
                  style={{ backgroundColor: '#1DA368', borderColor: '#1DA368' }}
                >
                  {applying ? (
                    <>
                      <IconLoader size={16} className="icon-spin" />
                      <span>جاري التثبيت...</span>
                    </>
                  ) : (
                    <>
                      <IconCloudDownload size={16} />
                      <span>تثبيت التحديث الآن</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
