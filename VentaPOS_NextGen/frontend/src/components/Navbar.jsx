import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../api';
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
  IconMinus,
  IconCash
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
  const [companySettingId, setCompanySettingId] = useState(null);

  useEffect(() => {
    // Fetch initial zoom from DB
    const fetchZoom = async () => {
      try {
        const res = await api.get('/company-settings/');
        if (res.data && res.data.results && res.data.results.length > 0) {
          const setting = res.data.results[0];
          setCompanySettingId(setting.id);
          if (setting.zoom_level) {
            const level = parseFloat(setting.zoom_level);
            document.body.style.zoom = level;
            localStorage.setItem('appZoomLevel', level);
            setZoomLevel(level);
          }
        }
      } catch (err) {
        console.error('Failed to fetch zoom level', err);
      }
    };
    fetchZoom();

    window.applyZoom = async (level) => {
      document.body.style.zoom = level;
      localStorage.setItem('appZoomLevel', level);
      setZoomLevel(level);
      
      // Save to DB
      try {
        // If we don't have ID yet, try to fetch it first or rely on the previous fetch
        let id = companySettingId;
        if (!id) {
            const res = await api.get('/company-settings/');
            if (res.data?.results?.length > 0) {
                id = res.data.results[0].id;
                setCompanySettingId(id);
            }
        }
        if (id) {
          await api.patch(`/company-settings/${id}/`, { zoom_level: level });
        }
      } catch (err) {
        console.error('Failed to save zoom level', err);
      }
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

    // Apply initial zoom from local storage immediately to prevent flicker
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
    <header className="navbar navbar-expand-md navbar-light sticky-top d-print-none" style={{ zIndex: 1030 }}>
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

              <li className={`nav-item ${location.pathname.startsWith('/search-purchases') || location.pathname.startsWith('/purchases') ? 'active' : ''}`}>
                <Link className="nav-link text-info" to="/search-purchases" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconPackage stroke={1.5} />
                  </span>
                  <span className="nav-link-title">المشتريات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/expenses') ? 'active' : ''}`}>
                <Link className="nav-link text-danger" to="/expenses" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconCash stroke={1.5} />
                  </span>
                  <span className="nav-link-title">المصروفات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/reports') ? 'active' : ''}`}>
                <Link className="nav-link text-warning" to="/reports" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconChartBar stroke={1.5} />
                  </span>
                  <span className="nav-link-title">التقارير</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/tools') ? 'active' : ''}`}>
                <Link className="nav-link text-secondary" to="/tools" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconTool stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الأدوات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/settings') ? 'active' : ''}`}>
                <Link className="nav-link text-dark" to="/settings" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الإعدادات</span>
                </Link>
              </li>

            </ul>
          </div>
        </div>
      </div>
    </header>
  );
}
