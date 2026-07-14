import React, { useState, useEffect } from 'react';
import { IconHistory, IconRefresh } from '@tabler/icons-react';
import axios from 'axios';

const LogsTab = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get('http://127.0.0.1:8000/api/v1/action-logs/', {
        headers: { Authorization: `Token ${token}` }
      });
      // Assuming DRF paginated response
      setLogs(Array.isArray(res.data) ? res.data : (res.data?.results || []));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="card border-0 shadow-sm rounded-4">
      <div className="card-header bg-white border-bottom-0 pt-4 pb-2 px-4 d-flex justify-content-between align-items-center">
        <h3 className="card-title fw-bold text-dark d-flex align-items-center">
          <IconHistory className="me-2 text-primary" /> سجل عمليات النظام
        </h3>
        <button className="btn btn-sm btn-outline-primary rounded-pill" onClick={fetchLogs}>
          <IconRefresh size={16} className="me-1" /> تحديث السجل
        </button>
      </div>
      <div className="card-body p-0">
        {loading ? (
          <div className="text-center p-5"><div className="spinner-border text-primary" /></div>
        ) : logs?.length === 0 ? (
          <div className="text-center p-5 text-muted">لا توجد عمليات مسجلة حتى الآن.</div>
        ) : (
          <div className="table-responsive">
            <table className="table table-vcenter table-hover card-table table-striped mb-0">
              <thead className="bg-light">
                <tr>
                  <th className="text-muted fw-bold">التاريخ والوقت</th>
                  <th className="text-muted fw-bold">نوع العملية</th>
                  <th className="text-muted fw-bold">التفاصيل</th>
                  <th className="text-muted fw-bold">المستخدم</th>
                </tr>
              </thead>
              <tbody>
                {(logs || []).map((log) => (
                  <tr key={log.id}>
                    <td>
                      <span className="text-muted small">
                        {new Date(log.timestamp).toLocaleString('ar-EG')}
                      </span>
                    </td>
                    <td>
                      <span className="badge bg-secondary-lt fw-bold">{log.action_type}</span>
                    </td>
                    <td className="text-dark fw-semibold">{log.details}</td>
                    <td className="text-muted">{log.user_name || 'مدير النظام'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsTab;
