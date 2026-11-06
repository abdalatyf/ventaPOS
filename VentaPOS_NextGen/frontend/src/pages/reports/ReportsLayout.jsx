import React, { createContext, useState, useEffect, useCallback, useMemo } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { IconFilter, IconReport, IconPrinter } from '@tabler/icons-react';
import { useDefaultDate } from '../../hooks/useDefaultDate';
import StandardTablePageLayout from '../../components/common/StandardTablePageLayout';
import { getLicenseStatus } from '../../api';

export const ReportsContext = createContext();

export default function ReportsLayout() {
  const branchId = localStorage.getItem('branchId');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  const location = useLocation();
  const navigate = useNavigate();

  const [year, setYear] = useState('');
  const [month, setMonth] = useState('');
  const [activePrintHandler, setActivePrintHandler] = useState(null);
  const [licenseWarning, setLicenseWarning] = useState(null);

  const registerPrintHandler = useCallback((handler) => {
    setActivePrintHandler(() => handler);
  }, []);

  // Verify license: block print-only plan and show expired warnings
  useEffect(() => {
    let isMounted = true;
    const verifyLicense = async (forceRefresh = false) => {
      try {
        const data = await getLicenseStatus(forceRefresh);
        if (!isMounted || !data) return;

        // Print-Only license (product_id 2 or 3) blocks analytical reports
        if (data.is_print_only) {
          navigate('/pos', { replace: true });
          return;
        }

        // Expired subscription warning
        if (data.is_expired || data.status === 'expired') {
          setLicenseWarning('الاشتراك منتهي. التقارير متاحة للاطلاع والمراجعة فقط.');
        } else if (data.is_last_month) {
          setLicenseWarning('تنبيه: الاشتراك ينتهي هذا الشهر. يرجى تجديد الترخيص.');
        } else {
          setLicenseWarning(null);
        }
      } catch (err) {
        console.error('Failed to verify license in ReportsLayout', err);
      }
    };

    verifyLicense();
    const handleUpdate = () => verifyLicense(true);
    window.addEventListener('license_updated', handleUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener('license_updated', handleUpdate);
    };
  }, [navigate]);
  
  // Extract report type from current path
  const currentPath = location.pathname.split('/').filter(Boolean).pop();
  const reportPath = (!currentPath || currentPath === 'reports') ? 'dashboard' : currentPath;

  // Immediately redirect /reports or /reports/ to /reports/dashboard
  useEffect(() => {
    if (location.pathname === '/reports' || location.pathname === '/reports/') {
      navigate(`/reports/dashboard${location.search}`, { replace: true });
    }
  }, [location.pathname, location.search, navigate]);

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

  const contextValue = useMemo(() => ({
    year,
    month,
    branchId,
    registerPrintHandler,
    handlePrint: () => {
      if (activePrintHandler) activePrintHandler();
    }
  }), [year, month, branchId, registerPrintHandler, activePrintHandler]);

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
    <ReportsContext.Provider value={contextValue}>
      <StandardTablePageLayout
        title="التقارير الإدارية والتحليلية"
        icon={IconReport}
        headerContent={
          <div className="d-flex align-items-center gap-2 flex-shrink-0" style={{ overflow: 'visible' }}>
            {/* Report Selector with explicit label "نوع التقرير" */}
            <div className="input-group input-group-sm" style={{ width: '290px' }}>
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle px-2">نوع التقرير</span>
              <select 
                className="form-select form-select-sm fw-bold border-secondary-subtle text-primary"
                value={reportPath}
                onChange={(e) => navigate(`/reports/${e.target.value}${location.search}`)}
                style={{ cursor: 'pointer' }}
              >
                <option value="dashboard">الملخص الشامل (لوحة القيادة)</option>
                <option value="receipts">فواتير المبيعات</option>
                <option value="purchases">المشتريات والموردين</option>
                <option value="areas">المناطق والتحصيل</option>
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
        headerActions={
          <button
            type="button"
            className="btn btn-sm btn-outline-primary fw-bold px-3 py-1 d-flex align-items-center gap-1 border-secondary-subtle"
            onClick={() => {
              if (activePrintHandler) activePrintHandler();
            }}
            title="طباعة التقرير"
          >
            <IconPrinter size={15} />
            <span>طباعة التقرير</span>
          </button>
        }
      >
        <div className="p-0">
          {licenseWarning && (
            <div className="alert alert-warning py-2 px-3 mb-2 mx-3 small fw-bold d-flex align-items-center gap-2 border-warning-subtle" role="alert">
              <span>⚠️</span>
              <span>{licenseWarning}</span>
            </div>
          )}
          <Outlet />
        </div>
      </StandardTablePageLayout>
    </ReportsContext.Provider>
  );
}
