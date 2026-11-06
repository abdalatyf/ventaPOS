import React, { createContext, useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { IconFilter, IconReport } from '@tabler/icons-react';
import { useDefaultDate } from '../../hooks/useDefaultDate';
import StandardTablePageLayout from '../../components/common/StandardTablePageLayout';

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
      <StandardTablePageLayout
        title="التقارير الإدارية والتحليلية"
        icon={IconReport}
        row1={
          <div className="d-flex align-items-center gap-2 flex-shrink-0" style={{ overflow: 'visible' }}>
            {/* Report Selector */}
            <div style={{ width: '240px' }} className="flex-shrink-0">
              <select 
                className="form-select form-select-sm fw-bold border-secondary-subtle text-primary"
                value={reportPath}
                onChange={(e) => navigate(`/reports/${e.target.value}${location.search}`)}
                style={{ cursor: 'pointer' }}
              >
                <option value="dashboard">الملخص (Dashboard)</option>
                <option value="receipts">فواتير المبيعات</option>
                <option value="purchases">فواتير المشتريات</option>
                <option value="installments">التحصيل (الأقساط)</option>
                <option value="expenses">المصروفات</option>
                <option value="profit-and-loss">الأرباح والخسائر (المجاميع)</option>
                <option value="averages">الأرباح والخسائر (المتوسطات)</option>
                <option value="inventory">حركة المخزون</option>
                <option value="salesperson">أداء المناديب</option>
              </select>
            </div>

            {/* Date Filter: Month */}
            <div style={{ width: '105px' }} className="flex-shrink-0">
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">شهر</span>
                <input
                  type="number"
                  className="form-control form-control-sm fw-bold text-center border-secondary-subtle px-1"
                  min="1" max="12" placeholder="شهر"
                  value={month} onChange={(e) => setMonth(e.target.value)}
                />
              </div>
            </div>

            {/* Date Filter: Year */}
            <div style={{ width: '110px' }} className="flex-shrink-0">
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-1">سنة</span>
                <input
                  type="number"
                  className="form-control form-control-sm fw-bold text-center border-secondary-subtle px-1"
                  min="2000" max="2100" placeholder="سنة"
                  value={year} onChange={(e) => setYear(e.target.value)}
                />
              </div>
            </div>
          </div>
        }
      >
        <div className="p-0">
          <Outlet />
        </div>
      </StandardTablePageLayout>
    </ReportsContext.Provider>
  );
}
