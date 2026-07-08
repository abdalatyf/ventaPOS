import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import logo from '../assets/venta.png';
import { 
  IconReceipt, 
  IconPackage, 
  IconChartBar, 
  IconBuildingStore, 
  IconTool, 
  IconSettings,
  IconLogout,
  IconPlus,
  IconMinus
} from '@tabler/icons-react';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [branchName, setBranchName] = useState('');
  
  // Tabler mobile menu toggle state
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  // React state for dropdowns instead of Bootstrap JS
  const [openDropdown, setOpenDropdown] = useState(null);
  
  const [zoomLevel, setZoomLevel] = useState(parseFloat(localStorage.getItem('appZoomLevel')) || 1.0);

  useEffect(() => {
    window.applyZoom = (level) => {
      document.body.style.zoom = level;
      localStorage.setItem('appZoomLevel', level);
      setZoomLevel(level);
    };
    window.zoomIn = () => {
      const currentZoom = parseFloat(localStorage.getItem('appZoomLevel')) || 1.0;
      if (currentZoom < 3.0) window.applyZoom(currentZoom + 0.1);
    };
    window.zoomOut = () => {
      const currentZoom = parseFloat(localStorage.getItem('appZoomLevel')) || 1.0;
      if (currentZoom > 0.5) window.applyZoom(currentZoom - 0.1);
    };
    window.resetZoom = () => {
      window.applyZoom(1.0);
    };

    // Apply initial zoom
    const initialZoom = parseFloat(localStorage.getItem('appZoomLevel')) || 1.0;
    document.body.style.zoom = initialZoom;

    // Keyboard shortcuts
    const handleKeyDown = (e) => {
      if (e.ctrlKey) {
        if (e.key === '=' || e.key === '+') {
          e.preventDefault();
          window.zoomIn();
        } else if (e.key === '-') {
          e.preventDefault();
          window.zoomOut();
        } else if (e.key === '0') {
          e.preventDefault();
          window.resetZoom();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    // Read from localStorage (simulate for now if empty)
    const storedBranch = localStorage.getItem('branchName') || 'الفرع الرئيسي';
    setBranchName(storedBranch);
  }, []);

  // Close dropdowns when navigating
  useEffect(() => {
    setOpenDropdown(null);
    setIsMenuOpen(false);
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('branchId');
    localStorage.removeItem('branchName');
    localStorage.removeItem('company_name');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path ? 'active' : '';

  const toggleDropdown = (name, e) => {
    e.preventDefault();
    setOpenDropdown(openDropdown === name ? null : name);
  };

  return (
    <header className="navbar navbar-expand-md navbar-light d-print-none">
      <div className="container-fluid">
        <button 
          className="navbar-toggler" 
          type="button" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <h1 className="navbar-brand navbar-brand-autodark d-none-navbar-horizontal pe-0 pe-md-3">
          <Link to="/">
            <img src={logo} alt="VentaPOS" className="navbar-brand-image" style={{ height: '2.5rem' }} />
          </Link>
        </h1>
        
        <div className="navbar-nav flex-row order-md-last align-items-center">
          <div className="d-flex align-items-center me-3 bg-light rounded px-2 py-1 border d-none d-md-flex">
            <button className="btn btn-sm btn-link text-dark text-decoration-none px-2" onClick={() => window.zoomOut()} title="تصغير (Ctrl + -)">
              <IconMinus size={18} />
            </button>
            <button className="btn btn-sm btn-link text-primary text-decoration-none px-2 fw-bold" onClick={() => window.resetZoom()} title="افتراضي (Ctrl + 0)">
              {Math.round(zoomLevel * 100)}%
            </button>
            <button className="btn btn-sm btn-link text-dark text-decoration-none px-2" onClick={() => window.zoomIn()} title="تكبير (Ctrl + +)">
              <IconPlus size={18} />
            </button>
          </div>
          
          <div className={`nav-item dropdown ${openDropdown === 'user' ? 'show' : ''}`}>
            <a href="#" className="nav-link d-flex lh-1 text-reset p-0" onClick={(e) => toggleDropdown('user', e)}>
              <span className="avatar avatar-sm bg-primary-lt"><IconBuildingStore size={18} /></span>
              <div className="d-none d-xl-block ps-2">
                <div>{branchName}</div>
              </div>
            </a>
            <div className={`dropdown-menu dropdown-menu-end dropdown-menu-arrow ${openDropdown === 'user' ? 'show' : ''}`} data-bs-popper={openDropdown === 'user' ? 'static' : undefined}>
              <Link to="/select-branch" className="dropdown-item">
                <IconBuildingStore className="icon me-2 text-primary" stroke={1.5} />
                تغيير الفرع
              </Link>
              <div className="dropdown-divider"></div>
              <a href="#" className="dropdown-item text-danger" onClick={(e) => { e.preventDefault(); handleLogout(); }}>
                <IconLogout className="icon me-2 text-danger" stroke={1.5} />
                تسجيل الخروج
              </a>
            </div>
          </div>
        </div>

        <div className={`collapse navbar-collapse ${isMenuOpen ? 'show' : ''}`} id="navbar-menu">
          <div className="d-flex flex-column flex-md-row flex-fill align-items-stretch align-items-md-center">
            <ul className="navbar-nav">
              
              <li className={`nav-item ${location.pathname.startsWith('/receipts') || location.pathname.startsWith('/pos') || location.pathname === '/' ? 'active' : ''}`}>
                <Link className="nav-link text-success" to="/receipts" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconReceipt stroke={1.5} />
                  </span>
                  <span className="nav-link-title">دفتر المبيعات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/setup') ? 'active' : ''}`}>
                <Link className="nav-link text-primary" to="/setup" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconBuildingStore stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الإدارة</span>
                </Link>
              </li>

              <li className={`nav-item dropdown ${location.pathname.startsWith('/purchases') || location.pathname.startsWith('/expenses') ? 'active' : ''} ${openDropdown === 'purchases' ? 'show' : ''}`}>
                <a className="nav-link dropdown-toggle text-info" href="#" onClick={(e) => toggleDropdown('purchases', e)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage stroke={1.5} />
                  </span>
                  <span className="nav-link-title">المشتريات والمصروفات</span>
                </a>
                <div className={`dropdown-menu ${openDropdown === 'purchases' ? 'show' : ''}`} data-bs-popper={openDropdown === 'purchases' ? 'static' : undefined}>
                  <Link className={`dropdown-item ${isActive('/purchases')}`} to="/purchases">إضافة فاتورة مشتريات</Link>
                  <Link className={`dropdown-item ${isActive('/purchases/search')}`} to="/purchases/search">بحث الفواتير</Link>
                  <Link className={`dropdown-item ${isActive('/expenses')}`} to="/expenses">المصروفات اليومية</Link>
                </div>
              </li>

              <li className={`nav-item dropdown ${location.pathname === '/' || location.pathname.startsWith('/reports') || location.pathname.startsWith('/collections') ? 'active' : ''} ${openDropdown === 'reports' ? 'show' : ''}`}>
                <a className="nav-link dropdown-toggle text-warning" href="#" onClick={(e) => toggleDropdown('reports', e)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconChartBar stroke={1.5} />
                  </span>
                  <span className="nav-link-title">التقارير</span>
                </a>
                <div className={`dropdown-menu ${openDropdown === 'reports' ? 'show' : ''}`} data-bs-popper={openDropdown === 'reports' ? 'static' : undefined}>
                  <Link className={`dropdown-item ${isActive('/reports/dashboard')}`} to="/reports/dashboard">لوحة تقارير الأداء</Link>
                  <Link className={`dropdown-item ${isActive('/reports/salesperson')}`} to="/reports/salesperson">عمولات وأداء المناديب</Link>
                  <Link className={`dropdown-item ${isActive('/reports/inventory')}`} to="/reports/inventory">حركة وجرد المخازن</Link>
                  <Link className={`dropdown-item ${isActive('/reports/profit-and-loss')}`} to="/reports/profit-and-loss">الأرباح والخسائر بالتفصيل</Link>
                  <Link className={`dropdown-item ${isActive('/reports/cash-drawer')}`} to="/reports/cash-drawer">حركة درج الخزينة</Link>
                </div>
              </li>

              <li className={`nav-item dropdown ${location.pathname.startsWith('/tools') ? 'active' : ''} ${openDropdown === 'tools' ? 'show' : ''}`}>
                <a className="nav-link dropdown-toggle text-secondary" href="#" onClick={(e) => toggleDropdown('tools', e)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconTool stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الأدوات</span>
                </a>
                <div className={`dropdown-menu ${openDropdown === 'tools' ? 'show' : ''}`} data-bs-popper={openDropdown === 'tools' ? 'static' : undefined}>
                  <Link className={`dropdown-item ${isActive('/tools/cloud')}`} to="/tools/cloud">الربط أونلاين</Link>
                  <Link className={`dropdown-item ${isActive('/tools/backup')}`} to="/tools/backup">النسخ الاحتياطي</Link>
                </div>
              </li>

              <li className={`nav-item dropdown ${location.pathname === '/settings/company' || location.pathname === '/settings/license' ? 'active' : ''} ${openDropdown === 'settings' ? 'show' : ''}`}>
                <a className="nav-link dropdown-toggle text-dark" href="#" onClick={(e) => toggleDropdown('settings', e)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الإعدادات</span>
                </a>
                <div className={`dropdown-menu ${openDropdown === 'settings' ? 'show' : ''}`} data-bs-popper={openDropdown === 'settings' ? 'static' : undefined}>
                  <Link className={`dropdown-item ${isActive('/settings/company')}`} to="/settings/company">بيانات الشركة</Link>
                  <Link className={`dropdown-item ${isActive('/settings/license')}`} to="/settings/license">الاشتراك</Link>
                </div>
              </li>

            </ul>
          </div>
        </div>
      </div>
    </header>
  );
}
