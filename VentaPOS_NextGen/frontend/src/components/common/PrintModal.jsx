import React, { useState, useEffect, useRef } from 'react';
import { 
  IconPrinter, 
  IconEye, 
  IconX, 
  IconAlertCircle, 
  IconAlertTriangle, 
  IconLoader,
  IconCheck,
  IconRefresh
} from '@tabler/icons-react';
import api from '../../api';

/**
 * PrintModal — Unified Printing Dialog with:
 * - Live Windows Printer Status (Ready / Offline)
 * - Pre-Print Offline Warning
 * - Sequential Chunking (CHUNK_SIZE = 20) with Pause, Retry & Cancel on failure
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - title: string
 * - itemCount: number (total count of receipts/invoices/pages)
 * - itemLabel: string (optional label for item type)
 * - items: Array (optional array of item IDs for native chunk management)
 * - executeChunk: async (chunk, { action, targetPrinter, chunkIndex, totalChunks }) => Promise<void>
 * - onExecute: async ({ action, targetPrinter, onProgress, isCancelledRef }) => Promise<void> (fallback)
 */
export default function PrintModal({
  isOpen,
  onClose,
  title = 'خيارات الطباعة',
  itemCount = 1,
  itemLabel = 'بند',
  items = null,
  executeChunk = null,
  onExecute = null,
}) {
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState('');
  const [loadingPrinters, setLoadingPrinters] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Pre-print offline warning state
  const [showOfflineWarning, setShowOfflineWarning] = useState(false);

  // Chunk failure pause/retry states
  const [isPaused, setIsPaused] = useState(false);
  const [pausedChunkIndex, setPausedChunkIndex] = useState(null);
  const [chunkErrorMsg, setChunkErrorMsg] = useState(null);
  const [activeAction, setActiveAction] = useState(null);
  const [processedCount, setProcessedCount] = useState(0);

  const isCancelledRef = useRef(false);

  // Normalize printer list items
  const normalizePrinters = (rawPrinters) => {
    return (rawPrinters || []).map((p) => {
      if (typeof p === 'string') {
        return { name: p, status: 'ready', is_default: false };
      }
      return {
        name: p.name || '',
        status: p.status === 'offline' ? 'offline' : 'ready',
        is_default: Boolean(p.is_default),
      };
    }).filter((p) => Boolean(p.name));
  };

  useEffect(() => {
    if (!isOpen) {
      setIsProcessing(false);
      setProgress(null);
      setErrorMessage(null);
      setShowOfflineWarning(false);
      setIsPaused(false);
      setPausedChunkIndex(null);
      setChunkErrorMsg(null);
      setActiveAction(null);
      setProcessedCount(0);
      isCancelledRef.current = false;
      return;
    }

    const fetchPrinters = async () => {
      setLoadingPrinters(true);
      try {
        const res = await api.get('/receipts/printers/');
        const normalized = normalizePrinters(res.data?.printers);
        setPrinters(normalized);

        const savedPrinter = localStorage.getItem('preferred_printer');
        const foundSaved = normalized.find((p) => p.name === savedPrinter);
        const defaultPrinter = normalized.find((p) => p.is_default);

        if (foundSaved) {
          setSelectedPrinter(foundSaved.name);
        } else if (defaultPrinter) {
          setSelectedPrinter(defaultPrinter.name);
        } else if (normalized.length > 0) {
          setSelectedPrinter(normalized[0].name);
        } else {
          setSelectedPrinter('');
        }
      } catch (err) {
        console.error('Failed to load printers:', err);
        setPrinters([]);
      } finally {
        setLoadingPrinters(false);
      }
    };

    fetchPrinters();
  }, [isOpen]);

  if (!isOpen) return null;

  const currentPrinterObj = printers.find((p) => p.name === selectedPrinter);
  const effectiveCount = items && Array.isArray(items) ? items.length : itemCount;
  const isBatch = effectiveCount > 20;

  const handlePrinterChange = (e) => {
    const val = e.target.value;
    setSelectedPrinter(val);
    setShowOfflineWarning(false);
    if (val) {
      localStorage.setItem('preferred_printer', val);
    }
  };

  // Helper to split array into chunks of 20
  const buildChunks = (arr, size = 20) => {
    const chunks = [];
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size));
    }
    return chunks;
  };

  // Run chunk-based execution with pause/retry support
  const runChunkedExecution = async (actionType, startChunkIdx = 0) => {
    const CHUNK_SIZE = 20;
    const allChunks = buildChunks(items, CHUNK_SIZE);
    const totalChunks = allChunks.length;
    // For view action with multiple chunks, preview only first chunk
    const targetChunks = (actionType === 'view' && totalChunks > 1) ? [allChunks[0]] : allChunks;
    const effectiveTotalChunks = targetChunks.length;
    const effectiveTotalItems = (actionType === 'view' && totalChunks > 1) ? targetChunks[0].length : items.length;

    setIsProcessing(true);
    setIsPaused(false);
    setChunkErrorMsg(null);
    setErrorMessage(null);
    setActiveAction(actionType);
    isCancelledRef.current = false;

    let currentProcessed = startChunkIdx > 0 ? processedCount : 0;

    for (let i = startChunkIdx; i < effectiveTotalChunks; i++) {
      if (isCancelledRef.current) {
        setIsProcessing(false);
        return;
      }

      const chunk = targetChunks[i];
      setPausedChunkIndex(i);

      try {
        await executeChunk(chunk, {
          action: actionType,
          targetPrinter: selectedPrinter || null,
          chunkIndex: i + 1,
          totalChunks: effectiveTotalChunks,
        });

        currentProcessed += chunk.length;
        setProcessedCount(currentProcessed);

        const pct = Math.round((currentProcessed / effectiveTotalItems) * 100);
        setProgress({
          current: currentProcessed,
          total: effectiveTotalItems,
          currentChunk: i + 1,
          totalChunks: effectiveTotalChunks,
          pct: Math.min(pct, 100),
        });
      } catch (err) {
        console.error(`Error in chunk ${i + 1}:`, err);
        const detail = err.response?.data?.error || err.response?.data?.detail || err.response?.data?.message || err.message || 'فشل إرسال الدفعة إلى الطابعة';
        setIsPaused(true);
        setPausedChunkIndex(i);
        setChunkErrorMsg(detail);
        setIsProcessing(false);
        return; // Pause execution loop at failed chunk
      }
    }

    // All chunks succeeded
    setIsProcessing(false);
    setProgress(null);
    if (!isCancelledRef.current) {
      onClose();
    }
  };

  // Entry point when clicking Print / Preview
  const handleStart = async (actionType, bypassOfflineWarning = false) => {
    setErrorMessage(null);

    // Pre-print offline warning check
    if (actionType === 'print' && !bypassOfflineWarning) {
      if (currentPrinterObj && currentPrinterObj.status === 'offline') {
        setShowOfflineWarning(true);
        return;
      }
    }
    setShowOfflineWarning(false);

    // If native chunk execution is supported via items & executeChunk
    if (items && Array.isArray(items) && items.length > 0 && executeChunk) {
      setProcessedCount(0);
      setPausedChunkIndex(0);
      await runChunkedExecution(actionType, 0);
      return;
    }

    // Fallback to onExecute callback
    setIsProcessing(true);
    isCancelledRef.current = false;

    try {
      if (onExecute) {
        await onExecute({
          action: actionType,
          targetPrinter: selectedPrinter || null,
          onProgress: (p) => setProgress(p),
          isCancelledRef,
        });
      }
      if (!isCancelledRef.current) {
        onClose();
      }
    } catch (err) {
      console.error('Print execution error:', err);
      const detail = err.response?.data?.error || err.response?.data?.detail || err.response?.data?.message || err.message || 'حدث خطأ أثناء تنفيذ الطباعة.';
      setErrorMessage(detail);
    } finally {
      setIsProcessing(false);
      setProgress(null);
    }
  };

  // Retry failed batch
  const handleRetryBatch = async () => {
    if (pausedChunkIndex !== null && activeAction) {
      await runChunkedExecution(activeAction, pausedChunkIndex);
    }
  };

  // Cancel remaining batches
  const handleCancelRemainingBatches = () => {
    isCancelledRef.current = true;
    setIsProcessing(false);
    setIsPaused(false);
    setProgress(null);
    onClose();
  };

  const handleCancelProcess = () => {
    isCancelledRef.current = true;
    setIsProcessing(false);
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
              <IconPrinter size={20} className="text-primary" />
              {title}
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              disabled={isProcessing} 
              onClick={onClose} 
              aria-label="Close" 
            />
          </div>

          {/* Body */}
          <div className="modal-body p-3">
            {/* General Error Message */}
            {errorMessage && (
              <div className="alert alert-danger py-2 px-3 small d-flex align-items-center gap-2 mb-3">
                <IconAlertCircle size={18} className="flex-shrink-0" />
                <div>{errorMessage}</div>
              </div>
            )}

            {/* Pre-Print Offline Warning Alert */}
            {showOfflineWarning && (
              <div className="alert alert-warning py-2 px-3 small mb-3 border-warning shadow-sm">
                <div className="d-flex align-items-center gap-2 mb-1">
                  <IconAlertTriangle size={20} className="text-warning flex-shrink-0" />
                  <strong className="text-dark">تنبيه: الطابعة المحددة ({selectedPrinter}) غير متصلة حالياً (Offline).</strong>
                </div>
                <p className="text-muted small mb-2">
                  قد لا تستجيب الطابعة لأمر الطباعة الفورية أو قد تظل المستندات عالقة في قائمة الانتظار حتى توصيل الطابعة.
                </p>
                <div className="d-flex justify-content-end gap-2">
                  <button 
                    type="button" 
                    className="btn btn-sm btn-outline-secondary" 
                    onClick={() => setShowOfflineWarning(false)}
                  >
                    إلغاء / تغيير الطابعة
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-sm btn-warning text-dark fw-bold" 
                    onClick={() => handleStart('print', true)}
                  >
                    متابعة الطباعة على أي حال
                  </button>
                </div>
              </div>
            )}

            {/* Chunk Failure Pause Alert */}
            {isPaused && (
              <div className="alert alert-danger py-2 px-3 small mb-3 border-danger shadow-sm">
                <div className="d-flex align-items-center gap-2 mb-1">
                  <IconAlertCircle size={20} className="text-danger flex-shrink-0" />
                  <strong className="text-danger">
                    تعذر إرسال الدفعة رقم {(pausedChunkIndex ?? 0) + 1} إلى الطابعة!
                  </strong>
                </div>
                <div className="text-dark small mb-2">
                  {chunkErrorMsg || 'حدث خطأ في الاتصال بالطابعة أو انقطاع في خادم الطباعة.'}
                </div>
                <div className="text-muted small mb-2">
                  تم إيقاف المعالجة مؤقتاً عند هذا البند. تم إنجاز {processedCount} من أصل {effectiveCount}.
                </div>
                <div className="d-flex justify-content-end gap-2">
                  <button 
                    type="button" 
                    className="btn btn-sm btn-outline-danger" 
                    onClick={handleCancelRemainingBatches}
                  >
                    إلغاء باقي الدفعات
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-sm btn-danger fw-bold d-flex align-items-center gap-1" 
                    onClick={handleRetryBatch}
                  >
                    <IconRefresh size={16} />
                    <span>إعادة محاولة الدفعة</span>
                  </button>
                </div>
              </div>
            )}

            {/* Item Summary Banner */}
            <div className="d-flex justify-content-between align-items-center bg-light p-2 rounded border mb-3">
              <span className="fw-bold text-secondary small">عدد البنود المحددة:</span>
              <span className="badge bg-primary fs-5 px-3 py-1 fw-bold rounded-pill">
                {effectiveCount} {effectiveCount === 1 ? itemLabel : `${itemLabel}ات`}
              </span>
            </div>

            {/* Printer Selector with Status Badge */}
            <div className="mb-3">
              <div className="d-flex justify-content-between align-items-center mb-1">
                <label className="form-label fw-bold text-dark m-0 small">
                  الطابعة المحددة للطباعة الفورية:
                </label>
                {/* Status Badge */}
                {currentPrinterObj && (
                  currentPrinterObj.status === 'ready' ? (
                    <span className="badge bg-success text-white px-2 py-1 small d-flex align-items-center gap-1">
                      <span className="status-dot status-dot-animated bg-white"></span>
                      <span>جاهز (متصل)</span>
                    </span>
                  ) : (
                    <span className="badge bg-danger text-white px-2 py-1 small d-flex align-items-center gap-1">
                      <span className="status-dot bg-white"></span>
                      <span>غير متصل (Offline)</span>
                    </span>
                  )
                )}
              </div>

              {loadingPrinters ? (
                <div className="d-flex align-items-center gap-2 text-muted small py-1">
                  <IconLoader size={16} className="icon-spin" />
                  جاري جلب الطابعات المتصلة بالويندوز...
                </div>
              ) : (
                <select
                  className="form-select border-secondary-subtle fw-semibold"
                  value={selectedPrinter}
                  onChange={handlePrinterChange}
                  disabled={isProcessing || isPaused}
                >
                  <option value="">الطابعة الافتراضية للويندوز</option>
                  {printers.map((p, idx) => (
                    <option key={idx} value={p.name}>
                      {p.name} {p.status === 'ready' ? '(جاهز)' : '(غير متصل)'}
                    </option>
                  ))}
                </select>
              )}
              <div className="form-text small text-muted">
                يتم تذكر الطابعة المختارة تلقائياً للعمليات اللاحقة.
              </div>
            </div>

            {/* Batch Notice */}
            {isBatch && !isProcessing && !isPaused && (
              <div className="alert alert-info py-2 px-3 small mb-3">
                <strong>تقسيم الدفعات التلقائي:</strong> سيتم تجزئة هذا الطلب ({effectiveCount} عنصر) إلى دفعات متتابعة من 20 عنصراً لضمان سرعة واستقرار الطابعة.
              </div>
            )}

            {/* Live Progress Bar */}
            {isProcessing && progress && (
              <div className="my-3 p-3 bg-light rounded border">
                <div className="d-flex justify-content-between align-items-center small fw-bold mb-1">
                  <span>
                    جاري معالجة الدفعة {progress.currentChunk} من {progress.totalChunks}
                  </span>
                  <span>{progress.pct}%</span>
                </div>
                <div className="progress progress-sm mb-2" style={{ height: '8px' }}>
                  <div 
                    className="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                    role="progressbar" 
                    style={{ width: `${progress.pct}%` }} 
                  />
                </div>
                <div className="d-flex justify-content-between align-items-center text-muted small">
                  <span>تم إنجاز {progress.current} من أصل {progress.total}</span>
                  <button 
                    type="button" 
                    className="btn btn-sm btn-outline-danger py-0 px-2 fw-bold"
                    onClick={handleCancelProcess}
                  >
                    إيقاف مؤقت
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="modal-footer bg-light py-2 px-3 border-top d-flex justify-content-between align-items-center">
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm px-3"
              onClick={onClose}
              disabled={isProcessing}
            >
              إغلاق
            </button>

            <div className="d-flex gap-2">
              {/* Preview Button */}
              <button
                type="button"
                className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1 px-3 fw-bold"
                onClick={() => handleStart('view')}
                disabled={isProcessing || isPaused || effectiveCount === 0}
                title="معاينة المستند وحفظه كملف PDF"
              >
                <IconEye size={18} />
                <span>معاينة ملف PDF</span>
              </button>

              {/* Direct Print Button */}
              <button
                type="button"
                className="btn btn-success btn-sm d-flex align-items-center gap-1 px-3 fw-bold text-white"
                onClick={() => handleStart('print')}
                disabled={isProcessing || isPaused || effectiveCount === 0}
                style={{ backgroundColor: '#1DA368', borderColor: '#1DA368' }}
                title="طباعة فورية على الطابعة المحددة"
              >
                {isProcessing ? (
                  <>
                    <IconLoader size={18} className="icon-spin" />
                    <span>جاري الإرسال...</span>
                  </>
                ) : (
                  <>
                    <IconPrinter size={18} />
                    <span>طباعة فورية</span>
                  </>
                )}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
