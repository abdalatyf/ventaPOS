import useSmartScroll from '../../hooks/useSmartScroll';
import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import api from '../../api';
import { ReportsContext } from './ReportsLayout';
import { IconPrinter } from '@tabler/icons-react';
const fmtNum = (val) => {
  const num = Number(val) || 0;
  return Math.round(num).toLocaleString('en-US');
};

const toArabic = (str) => {
  if (str === null || str === undefined) return '';
  return String(str).replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[d]);
};

export default function ExpensesReport() {
  const { setTableRef } = useSmartScroll();
  const { year, month, branchId } = useContext(ReportsContext);

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  
  const tableContainerRef = useRef(null);

  // Calculate total
  const safeData = Array.isArray(data) ? data : [];
  const totalAmount = safeData.reduce((acc, item) => acc + (Number(item.amount) || 0), 0);

  const fetchExpenses = async () => {
    if (!year || !month || !branchId) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/expenses/', {
        params: {
          month: month,
          year: year
        }
      });
      setData(response.data.results || response.data || []);
    } catch (err) {
      console.error("Error fetching expenses:", err);
      setError("حدث خطأ أثناء تحميل بيانات المصروفات.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [year, month, branchId]);

  return (
    <div className="p-3 fs-3" dir="rtl" style={{ fontSize: '1.02rem' }}>
      <div className="card shadow-sm border-secondary-subtle">
        <div className="card-header sticky-toolbar bg-light d-flex justify-content-between align-items-center py-2" style={{ borderColor: '#dee2e6 !important' }}>
          <div className="d-flex align-items-center gap-3">
            <h4 className="card-title m-0 fw-bold d-flex align-items-center gap-2">
              نتائج المصروفات
              <span className="badge bg-primary text-white rounded-pill px-2 py-1">{toArabic(safeData.length)} عملية</span>
            </h4>
            
            {selectedIds.length > 0 && (
              <div className="d-flex align-items-center gap-2 slide-in-right">
                <span className="badge bg-secondary px-2 py-1 fs-5 rounded-pill shadow-sm">
                  محدد: {toArabic(selectedIds.length)}
                </span>
                <button className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1 shadow-sm">
                  <IconPrinter size={16} /> طباعة
                </button>
              </div>
            )}
          </div>
          <span className="badge bg-danger text-white px-3 py-2 fs-4 rounded shadow-sm">الإجمالي: {toArabic(fmtNum(totalAmount))}</span>
        </div>
        {loading ? (
          <div className="p-5 text-center">
            <div className="spinner-border text-primary" role="status"></div>
            <div className="text-muted mt-2">جاري تحميل المصروفات...</div>
          </div>
        ) : error ? (
          <div className="p-4 alert alert-danger m-3">{error}</div>
        ) : (
          <div 
            ref={setTableRef}
            className="table-responsive hide-vertical-scroll"
            style={{ overflowY: 'auto', borderBottom: '1px solid #dee2e6' }}
          >
            <table className="table table-vcenter table-hover card-table table-striped table-bordered m-0" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
              <thead>
                <tr className="hybrid-sticky-header">
                  <th className="text-center w-1 border-secondary-subtle" style={{ minWidth: '40px' }}>
                    <input 
                      type="checkbox" 
                      className="form-check-input border-secondary-subtle" 
                      checked={safeData.length > 0 && selectedIds.length === safeData.length}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th className="text-center w-1 border-secondary-subtle" style={{ minWidth: '50px' }}>#</th>
                  <th className="text-start border-secondary-subtle">البيان</th>
                  <th className="text-center border-secondary-subtle">التاريخ</th>
                  <th className="text-end px-2 border-secondary-subtle" style={{ minWidth: '120px' }}>المبلغ</th>
                </tr>
              </thead>
              <tbody>
                {safeData.length > 0 ? (
                  safeData.map((item, index) => (
                    <tr key={item.id}>
                      <td className="text-center align-middle border-secondary-subtle">
                        <input 
                          type="checkbox" 
                          className="form-check-input border-secondary-subtle" 
                          checked={selectedIds.includes(item.id)}
                          onChange={() => toggleSelect(item.id)}
                        />
                      </td>
                      <td className="text-center align-middle border-secondary-subtle fw-bold">{toArabic(index + 1)}</td>
                      <td className="text-start align-middle border-secondary-subtle fw-bold text-primary">{item.description}</td>
                      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(item.expense_year)}/{toArabic(item.expense_month)}</td>
                      <td className="text-end px-2 align-middle border-secondary-subtle fw-bold text-danger">{toArabic(fmtNum(item.amount))}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="text-center py-4 text-muted">لا يوجد مصروفات في هذا الشهر</td>
                  </tr>
                )}
              </tbody>
              {safeData.length > 0 && (
                <tfoot style={{ position: 'sticky', bottom: 0, zIndex: 10 }}>
                  <tr className="fw-bold bg-light">
                    <td colSpan="4" className="text-end border-secondary-subtle fs-4">إجمالي المصروفات:</td>
                    <td className="text-end border-secondary-subtle text-danger fs-3 px-2">{toArabic(fmtNum(totalAmount))}</td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
