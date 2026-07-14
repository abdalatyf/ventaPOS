import React, { createContext, useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { IconDashboard, IconReceipt, IconWallet, IconCoin, IconChartBar, IconBox, IconUser, IconFilter } from '@tabler/icons-react';
import { useDefaultDate } from '../../hooks/useDefaultDate';

export const ReportsContext = createContext();

export default function ReportsLayout() {
  const branchId = localStorage.getItem('branchId');
  const { defaultYear, defaultMonth, loading: dateLoading } = useDefaultDate(branchId);
  const location = useLocation();

  const [year, setYear] = useState('');
  const [month, setMonth] = useState('');
  
  // Update from URL params if present, otherwise from defaults
  useEffect(() => {
    if (!dateLoading) {
      const searchParams = new URLSearchParams(location.search);
      const urlYear = searchParams.get('year');
      const urlMonth = searchParams.get('month');
      
      if (urlYear && urlMonth) {
        setYear(urlYear);
        setMonth(urlMonth);
      } else if (!year || !month) {
        setYear(defaultYear);
        setMonth(defaultMonth);
      }
    }
  }, [dateLoading, defaultYear, defaultMonth, location.search]);

  // Generate years (5 years back from current)
  const currentYear = new Date().getFullYear();
  const years = Array.from(new Array(6), (val, index) => currentYear - index);
  
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const monthNames = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
  ];

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
    <ReportsContext.Provider value={{ year, month, setYear, setMonth, branchId }}>
      <div className="page-wrapper native-page-scroll flex-fill d-flex flex-column">
        
        {/* Global Filter Bar */}
        <div className="page-header d-print-none flex-shrink-0 m-0 py-2 border-bottom bg-white shadow-sm">
          <div className="container-fluid">
            <div className="row g-2 align-items-center">
              <div className="col">
                <h3 className="page-title text-primary d-flex align-items-center mb-0">
                  <IconFilter size={20} className="me-2" />
                  فترة التقرير
                </h3>
              </div>
              <div className="col-auto ms-auto d-flex gap-2">
                <select
                  className="form-select form-select-sm fw-bold bg-light"
                  value={month}
                  onChange={(e) => setMonth(e.target.value)}
                  style={{ width: '120px' }}
                >
                  {months.map((m) => (
                    <option key={m} value={m}>
                      {monthNames[m - 1]} ({m})
                    </option>
                  ))}
                </select>
                <select
                  className="form-select form-select-sm fw-bold bg-light"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  style={{ width: '90px' }}
                >
                  {years.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="page-body m-0 p-3 pt-2">
          <div className="container-fluid p-0">
            
            <div className="card shadow-sm border-0 rounded-3">
              <div className="card-header bg-white border-bottom p-0">
                <ul className="nav nav-tabs card-header-tabs nav-fill m-0 w-100" data-bs-toggle="tabs" role="tablist">
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/dashboard?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconDashboard size={18} className="me-2" />
                      الملخص
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/receipts?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconReceipt size={18} className="me-2" />
                      فواتير المبيعات
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/installments?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconWallet size={18} className="me-2" />
                      التحصيل
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/expenses?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconCoin size={18} className="me-2" />
                      المصروفات
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/profit-and-loss?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconChartBar size={18} className="me-2" />
                      الأرباح والخسائر
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/inventory?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconBox size={18} className="me-2" />
                      جرد المخزن
                    </NavLink>
                  </li>
                  <li className="nav-item" role="presentation">
                    <NavLink to={`/reports/salesperson?year=${year}&month=${month}`} className={({ isActive }) => `nav-link py-3 fw-bold ${isActive ? 'active' : 'text-muted'}`}>
                      <IconUser size={18} className="me-2" />
                      أداء المناديب
                    </NavLink>
                  </li>
                </ul>
              </div>
              
              <div className="card-body p-0 bg-light-lt">
                <Outlet />
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </ReportsContext.Provider>
  );
}
