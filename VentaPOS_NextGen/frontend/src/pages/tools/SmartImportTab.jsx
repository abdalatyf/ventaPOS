import React, { useState } from 'react';
import { IconDatabaseImport, IconFileSpreadsheet, IconCheck } from '@tabler/icons-react';
import axios from 'axios';

const SmartImportTab = () => {
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setProgress(0);
  };

  const handleImport = async () => {
    if (!file) {
      alert("يرجى اختيار ملف الإكسيل أولاً");
      return;
    }
    
    setImporting(true);
    setProgress(30);
    
    const formData = new FormData();
    formData.append('excel_file', file);
    
    try {
      const token = localStorage.getItem('token');
      // Simulated progress for better UX
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 10, 90));
      }, 500);

      const res = await axios.post('http://127.0.0.1:8000/api/v1/tools/smart-import/', formData, {
        headers: { Authorization: `Token ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      
      clearInterval(progressInterval);
      setProgress(100);
      setResult({ type: 'success', message: res.data.message });
      setFile(null);
    } catch (err) {
      setProgress(0);
      setResult({ type: 'error', message: err.response?.data?.error || 'حدث خطأ أثناء الاستيراد' });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="card border-0 shadow-sm rounded-4 max-w-3xl mx-auto">
      <div className="card-body p-5 text-center">
        <div className="mb-4">
          <span className="avatar avatar-xl bg-primary-lt rounded-circle mb-3">
            <IconDatabaseImport size={32} className="text-primary" />
          </span>
          <h2 className="fw-bold text-dark">الاستيراد الذكي للبيانات</h2>
          <p className="text-muted">قم برفع ملف إكسيل (.xlsx) يحتوي على الأصناف والعملاء والديون ليتم استيرادها دفعة واحدة للنظام.</p>
        </div>

        <div className="border border-dashed border-2 rounded-3 p-5 mb-4 position-relative hover-bg-light transition-all">
          <input 
            type="file" 
            accept=".xlsx, .xls" 
            className="position-absolute top-0 start-0 w-100 h-100 opacity-0 cursor-pointer"
            onChange={handleFileChange}
            disabled={importing}
          />
          <IconFileSpreadsheet size={48} className="text-muted mb-2" />
          <h4 className="text-dark fw-bold mb-1">
            {file ? file.name : 'اضغط هنا أو اسحب ملف الإكسيل للإفلات'}
          </h4>
          <p className="text-muted small mb-0">الامتدادات المدعومة: .xlsx, .xls</p>
        </div>

        {importing && (
          <div className="mb-4 text-start">
            <div className="d-flex justify-content-between mb-1">
              <span className="small text-muted fw-bold">جاري معالجة البيانات...</span>
              <span className="small text-primary fw-bold">{progress}%</span>
            </div>
            <div className="progress progress-sm">
              <div className="progress-bar progress-bar-indeterminate bg-primary" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        {result && (
          <div className={`alert alert-${result.type === 'success' ? 'success' : 'danger'} d-flex align-items-center justify-content-center border-0 rounded-3`}>
            {result.type === 'success' && <IconCheck className="me-2" />}
            {result.message}
          </div>
        )}

        <button 
          className="btn btn-primary btn-lg rounded-pill px-5 fw-bold" 
          onClick={handleImport}
          disabled={!file || importing}
        >
          {importing ? 'جاري الاستيراد...' : 'بدء الاستيراد الآن'}
        </button>
      </div>
    </div>
  );
};

export default SmartImportTab;
