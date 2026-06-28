import React from 'react';
import { IconDashboard, IconPackage, IconCashBanknote, IconSettings } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  return (
    <div className="page">
      {/* Sidebar */}
      <aside className="navbar navbar-vertical navbar-expand-lg navbar-dark bg-dark">
        <div className="container-fluid">
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#sidebar-menu">
            <span className="navbar-toggler-icon"></span>
          </button>
          <h1 className="navbar-brand navbar-brand-autodark px-3 py-4 text-start w-100">
            <span className="fw-bolder fs-2 tracking-tight">Venta<span className="text-primary">POS</span></span>
          </h1>
          <div className="collapse navbar-collapse" id="sidebar-menu">
            <ul className="navbar-nav pt-lg-3">
              <h6 className="navbar-heading text-muted mt-2 fw-bold">1. المبيعات</h6>
              <li className="nav-item">
                <Link className="nav-link" to="/pos">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconCashBanknote size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إضافة فاتورة</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconCashBanknote size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">بحث وتعديل الفواتير</span>
                </Link>
              </li>

              <h6 className="navbar-heading text-muted mt-4 fw-bold">2. المشتريات والمصروفات</h6>
              <li className="nav-item">
                <Link className="nav-link" to="/purchases">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إضافة فاتورة شراء</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">بحث فواتير الشراء</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconCashBanknote size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">المصروفات</span>
                </Link>
              </li>

              <h6 className="navbar-heading text-muted mt-4 fw-bold">3. التأسيس والإدارة</h6>
              <li className="nav-item">
                <Link className="nav-link" to="/settings">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إدارة الفروع</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/settings">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إدارة المناديب</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/inventory">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">الأصناف والتسعير</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إدارة الموردين</span>
                </Link>
              </li>

              <h6 className="navbar-heading text-muted mt-4 fw-bold">4. التقارير والتحليلات</h6>
              <li className="nav-item">
                <Link className="nav-link" to="/">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconDashboard size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">ملخصات الداشبورد</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconDashboard size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">صفحة الجرد</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconCashBanknote size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إدارة التحصيلات والديون</span>
                </Link>
              </li>

              <h6 className="navbar-heading text-muted mt-4 fw-bold">5. الأدوات</h6>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">الربط أونلاين</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">الاستيراد الذكي</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">النسخ الاحتياطي</span>
                </Link>
              </li>

              <h6 className="navbar-heading text-muted mt-4 fw-bold">6. الإعدادات والأمان</h6>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">الشركة والاشتراكات</span>
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="#">
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={20} />
                  </span>
                  <span className="nav-link-title fw-medium">إغلاق البرنامج</span>
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="page-wrapper bg-light">
        {/* Header */}
        <header className="navbar navbar-expand-md navbar-light d-none d-lg-flex d-print-none shadow-sm bg-white">
          <div className="container-xl">
            <div className="navbar-nav flex-row order-md-last ms-auto">
              <div className="nav-item dropdown">
                <a href="#" className="nav-link d-flex lh-1 text-reset p-0" data-bs-toggle="dropdown">
                  <span className="avatar avatar-sm bg-blue-lt">م</span>
                  <div className="d-none d-xl-block ps-2">
                    <div className="fw-bold">المدير</div>
                    <div className="mt-1 small text-muted">مدير النظام</div>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <div className="page-body">
          <div className="container-xl">
            <div className="row g-4">
              <div className="col-12">
                <div className="card shadow-sm border-0 rounded-3">
                  <div className="card-body py-5 text-center">
                    <h2 className="display-6 fw-bold mb-3">أهلاً بك في VentaPOS</h2>
                    <p className="text-muted fs-4 mb-4">النظام الأمثل لإدارة البضاعة والنقدية.</p>
                    <div className="d-flex justify-content-center gap-3">
                      <Link to="/pos" className="btn btn-primary btn-lg rounded-pill px-5 shadow-sm">
                        <IconCashBanknote className="me-2" /> فتح الخزنة
                      </Link>
                      <Link to="/receipt-entry" className="btn btn-warning btn-lg rounded-pill px-5 shadow-sm">
                        <IconCashBanknote className="me-2" /> إصدار فاتورة
                      </Link>
                      <Link to="/inventory" className="btn btn-outline-secondary btn-lg rounded-pill px-5">
                        <IconPackage className="me-2" /> إدارة البضاعة
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Quick Stats Placeholders */}
              <div className="col-md-6 col-xl-3">
                <div className="card shadow-sm border-0 rounded-3">
                  <div className="card-body">
                    <div className="d-flex align-items-center">
                      <div className="subheader">مبيعات اليوم</div>
                    </div>
                    <div className="h1 mb-3">١٢٥٠ جنيه</div>
                    <div className="d-flex mb-2">
                      <div>زيادة ٥٪ عن امبارح</div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Add more stats as needed */}
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="footer footer-transparent d-print-none">
          <div className="container-xl">
            <div className="row text-center align-items-center flex-row-reverse">
              <div className="col-12 col-lg-auto mt-3 mt-lg-0">
                <ul className="list-inline list-inline-dots mb-0">
                  <li className="list-inline-item">
                    جميع الحقوق محفوظة &copy; 2026 VentaPOS
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Dashboard;
