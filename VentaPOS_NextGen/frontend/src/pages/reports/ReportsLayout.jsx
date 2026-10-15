import React, { createContext, useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { IconFilter, IconReport } from '@tabler/icons-react';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export const ReportsContext = createContext();

export default function ReportsLayout() {
  const branchId = localStorage.getItem('branchId');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  const location = useLocation();
  const navigate = useNavigate();

  const [year, setYear] = useState('');
  const [month, setMonth] = useState('');
  
  // Extract report type from current path
  const currentPath = location.pathname.split('/').pop();
  const reportPath = currentPath === 'reports' ? 'dashboard' : currentPath;

  // Sync with URL params or default
  useEffect(() => {
    if (!dateLoading) {
      const searchParams = new URLSearchParams(location.search);
      const urlYear = searchParams.get('year') || defaultYear;
      const urlMonth = searchParams.get('month') || defaultMonth;
      if (!year || !month) {
        setYear(urlYear);
        setMonth(urlMonth);
      }
    }
  }, [dateLoading, defaultYear, defaultMonth, location.search]);

  // Update URL when date range changes
  useEffect(() => {
    if (year && month) {
      const searchParams = new URLSearchParams(location.search);
      searchParams.set('year', year);
      searchParams.set('month', month);

      const newSearch = searchParams.toString();
      if (location.search !== `?${newSearch}`) {
        navigate(`${location.pathname}?${newSearch}`, { replace: true });
      }
    }
  }, [year, month, navigate, location.pathname, location.search]);

  if (dateLoading || !year || !month) {
    return (
      <div className="page-wrapper flex-fill d-flex align-items-center justify-content-center" style={{ height: '100vh' }}>
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status"></div>
          <div className="text-muted mt-2">جاري تهيئة التقارير...</div>
        </div>
      </div>
    );
  }

  return (
    <ReportsContext.Provider value={{ year, month, branchId }}>
      <div className="page-wrapper native-page-scroll flex-fill d-flex flex-column">
        
        {/* Master Control Bar */}
        <div className="page-header d-print-none flex-shrink-0 m-0 py-3 border-bottom bg-white shadow-sm">
          <div className="container-fluid">
            <div className="row g-3 align-items-center">
              
              {/* Report Selector */}
              <div className="col-auto">
                <div className="d-flex align-items-center gap-2">
                  <div className="avatar avatar-sm bg-primary-lt rounded">
                    <IconReport size={20} className="text-primary" />
                  </div>
                  <select 
                    className="form-select form-select-md fw-bold border-primary text-primary"
                    value={reportPath}
                    onChange={(e) => navigate(`/reports/${e.target.value}${location.search}`)}
                    style={{ minWidth: '220px', cursor: 'pointer' }}
                  >
                    <option value="dashboard">الملخص (Dashboard)</option>
                    <option value="receipts">فواتير المبيعات</option>
                    <option value="installments">التحصيل (الأقساط)</option>
                    <option value="expenses">المصروفات</option>
                    <option value="profit-and-loss">الأرباح والخسائر (المجاميع)</option>
                    <option value="averages">الأرباح والخسائر (المتوسطات)</option>
                    <option value="inventory">حركة المخزون</option>
                    <option value="salesperson">أداء المناديب</option>
                  </select>
                </div>
              </div>

              {/* Date Filter */}
              <div className="col-auto ms-auto d-flex align-items-center gap-3">
                <div className="d-flex align-items-center gap-2 bg-light p-2 rounded border">
                  <span className="text-muted small fw-bold ms-1">شهر:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="1" max="12" placeholder="شهر"
                    value={month} onChange={(e) => setMonth(e.target.value)}
                    style={{ width: '70px' }}
                  />
                  <span className="text-muted small fw-bold ms-1">سنة:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="2000" max="2100" placeholder="سنة"
                    value={year} onChange={(e) => setYear(e.target.value)}
                    style={{ width: '80px' }}
                  />
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Report Body */}
        <div className="page-body m-0 px-3 pt-3 pb-0">
          <div className="container-fluid p-0">
            <Outlet />
          </div>
        </div>
        
      </div>
    </ReportsContext.Provider>
  );
}
