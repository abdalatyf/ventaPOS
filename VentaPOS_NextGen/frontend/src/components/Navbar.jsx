import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import toast from 'react-hot-toast';
import api, { getLicenseStatus } from '../api';
import { useActiveBranch } from '../hooks/useActiveBranch';
import logo from '../assets/venta.png';
import QuickRestoreModal from './common/QuickRestoreModal';
import UpdateModal from './common/UpdateModal';
import UserManualModal from './common/UserManualModal';
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
  IconCash,
  IconDatabase,
  IconCloudDownload,
  IconBook
} from '@tabler/icons-react';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { branchId, branchName: activeBranchName, setActiveBranch } = useActiveBranch();
  const branchName = activeBranchName || 'الفرع الرئيسي';
  const [branches, setBranches] = useState([]);
  
  // Tabler mobile menu toggle state
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  // React state for dropdowns instead of Bootstrap JS
  const [openDropdown, setOpenDropdown] = useState(null);
  
  const [zoomLevel, setZoomLevel] = useState(parseFloat(localStorage.getItem('appZoomLevel')) || 1.0);
  const [companySettingId, setCompanySettingId] = useState(null);
  const companySettingIdRef = useRef(null);
  const headerRef = useRef(null);
  const [isPrintOnly, setIsPrintOnly] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showManualModal, setShowManualModal] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const checkLicense = (forceRefresh = false) => {
      getLicenseStatus(forceRefresh).then(data => {
        if (isMounted) {
          setIsPrintOnly(Boolean(data?.is_print_only));
        }
      }).catch(err => console.error(err));
    };
    checkLicense();
    const handleUpdate = () => checkLicense(true);
    window.addEventListener('license_updated', handleUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener('license_updated', handleUpdate);
    };
  }, []);

  useEffect(() => {
    const syncNavbarHeight = () => {
      if (headerRef.current) {
        const h = headerRef.current.offsetHeight;
        if (h > 0) {
          document.documentElement.style.setProperty('--navbar-height', `${h}px`);
        }
      }
    };

    syncNavbarHeight();
    let navbarObserver = null;
    if (typeof ResizeObserver !== 'undefined' && headerRef.current) {
      navbarObserver = new ResizeObserver(syncNavbarHeight);
      navbarObserver.observe(headerRef.current);
    }

    // Fetch initial zoom from DB
    const fetchZoom = async () => {
      try {
        const res = await api.get('/company-settings/');
        if (res.data && res.data.results && res.data.results.length > 0) {
          const setting = res.data.results[0];
          companySettingIdRef.current = setting.id;
          setCompanySettingId(setting.id);
          if (setting.zoom_level) {
            const level = Math.max(0.70, Math.min(1.50, Math.round(parseFloat(setting.zoom_level) * 100) / 100));
            document.body.style.zoom = level;
            document.documentElement.style.setProperty('--app-zoom', level);
            localStorage.setItem('appZoomLevel', level);
            setZoomLevel(level);
            syncNavbarHeight();
            window.dispatchEvent(new CustomEvent('app-zoom-changed', { detail: { zoom: level } }));
            window.dispatchEvent(new Event('resize'));
          }
        }
      } catch (err) {
        console.error('Failed to fetch zoom level', err);
      }
    };
    fetchZoom();

    window.applyZoom = async (level) => {
      const roundedLevel = Math.max(0.70, Math.min(1.50, Math.round(level * 100) / 100));
      document.body.style.zoom = roundedLevel;
      document.documentElement.style.setProperty('--app-zoom', roundedLevel);
      localStorage.setItem('appZoomLevel', roundedLevel);
      setZoomLevel(roundedLevel);
      syncNavbarHeight();

      window.dispatchEvent(new CustomEvent('app-zoom-changed', { detail: { zoom: roundedLevel } }));
      window.dispatchEvent(new Event('resize'));

      // Save to DB
      try {
        let id = companySettingIdRef.current;
        if (!id) {
          const res = await api.get('/company-settings/');
          if (res.data?.results?.length > 0) {
            id = res.data.results[0].id;
            companySettingIdRef.current = id;
            setCompanySettingId(id);
          }
        }
        if (id) {
          await api.patch(`/company-settings/${id}/`, { zoom_level: roundedLevel });
        }
      } catch (err) {
        console.error('Failed to save zoom level', err);
      }
    };
    window.zoomIn = () => {
      const currentZoom = parseFloat(localStorage.getItem('appZoomLevel')) || 1.0;
      if (currentZoom < 1.50) window.applyZoom(Math.round((currentZoom + 0.05) * 100) / 100);
    };
    window.zoomOut = () => {
      const currentZoom = parseFloat(localStorage.getItem('appZoomLevel')) || 1.0;
      if (currentZoom > 0.70) window.applyZoom(Math.round((currentZoom - 0.05) * 100) / 100);
    };
    window.resetZoom = () => {
      window.applyZoom(1.0);
    };

    // Apply initial zoom from local storage immediately to prevent flicker
    const initialZoom = Math.max(0.70, Math.min(1.50, Math.round((parseFloat(localStorage.getItem('appZoomLevel')) || 1.0) * 100) / 100));
    document.body.style.zoom = initialZoom;
    document.documentElement.style.setProperty('--app-zoom', initialZoom);
    setZoomLevel(initialZoom);
    syncNavbarHeight();

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
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (navbarObserver) navbarObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const loadBranches = async () => {
      try {
        const res = await api.get('/branches/');
        const data = res?.data;
        const list = Array.isArray(data) ? data : (data?.results || []);
        if (mounted && Array.isArray(list)) {
          setBranches(list);
        }
      } catch {
        // Safely ignore in isolated unit tests or before authentication
      }
    };
    loadBranches();
    return () => {
      mounted = false;
    };
  }, [branchId]);

  const handleQuickSwitchBranch = (b) => {
    setActiveBranch(b.id, b.name);
    setOpenDropdown(null);
    setIsMenuOpen(false);
    toast.success(`تم التبديل إلى: ${b.name}`);
  };

  // Close dropdowns when navigating
  useEffect(() => {
    setOpenDropdown(null);
    setIsMenuOpen(false);
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setActiveBranch(null, '');
    localStorage.removeItem('company_name');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path ? 'active' : '';

  const toggleDropdown = (name, e) => {
    e.preventDefault();
    setOpenDropdown(openDropdown === name ? null : name);
  };

  return (
    <header ref={headerRef} className="navbar navbar-expand-md navbar-light sticky-top d-print-none" style={{ zIndex: 1030 }}>
      <div className="container-fluid">
        <button 
          className="navbar-toggler" 
          type="button" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <h1 className="navbar-brand navbar-brand-autodark d-none-navbar-horizontal pe-0 pe-md-2 me-1">
          <Link to="/">
            <img src={logo} alt="VentaPOS" className="navbar-brand-image" style={{ height: '2.5rem' }} />
          </Link>
        </h1>
        
        <div className="navbar-nav flex-row order-md-last align-items-center flex-shrink-0">
          <button 
            type="button" 
            className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1 me-1 px-2"
            onClick={() => setShowManualModal(true)}
            title="دليل تشغيل البرنامج (دليل التاجر والمدير)"
          >
            <IconBook size={16} />
            <span className="d-none d-sm-inline fw-bold">دليل المستخدم</span>
          </button>

          <div className="btn-group btn-group-sm me-2 bg-light rounded border align-items-center" role="group" aria-label="Zoom Controls">
            <button 
              type="button"
              className="btn btn-sm btn-link text-dark text-decoration-none px-1 py-1" 
              onClick={() => window.zoomOut()} 
              title="تصغير (Ctrl + -)"
              disabled={zoomLevel <= 0.70}
            >
              <IconMinus size={16} />
            </button>
            <span 
              role="button"
              className="badge bg-white text-dark border px-1 py-1 mx-1 fw-bold cursor-pointer"
              onClick={() => window.resetZoom()}
              title="إعادة التعيين إلى 100% (Ctrl + 0)"
              style={{ minWidth: '42px', textAlign: 'center', userSelect: 'none' }}
            >
              {Math.round(zoomLevel * 100)}%
            </span>
            <button 
              type="button"
              className="btn btn-sm btn-link text-dark text-decoration-none px-1 py-1" 
              onClick={() => window.zoomIn()} 
              title="تكبير (Ctrl + +)"
              disabled={zoomLevel >= 1.50}
            >
              <IconPlus size={16} />
            </button>
          </div>
          
          <div className={`nav-item dropdown ${openDropdown === 'user' ? 'show' : ''}`}>
            <a href="#" className="nav-link d-flex lh-1 text-reset px-2 py-1" onClick={(e) => toggleDropdown('user', e)}>
              <span className="avatar avatar-sm bg-primary-lt"><IconBuildingStore size={18} /></span>
              <div className="d-none d-xl-block ps-2">
                <div className="text-truncate" style={{ maxWidth: '95px' }}>{branchName}</div>
              </div>
            </a>
            <div className={`dropdown-menu dropdown-menu-end dropdown-menu-arrow ${openDropdown === 'user' ? 'show' : ''}`} data-bs-popper={openDropdown === 'user' ? 'static' : undefined}>
              {branches.length > 0 && (
                <>
                  <div className="dropdown-header small">تبديل سريع للفرع</div>
                  {branches.map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      className={`dropdown-item d-flex align-items-center justify-content-between ${String(b.id) === String(branchId) ? 'active fw-bold' : ''}`}
                      onClick={() => handleQuickSwitchBranch(b)}
                    >
                      <span>{b.name}</span>
                      {String(b.id) === String(branchId) && <span className="badge bg-success-lt text-success ms-2">نشط</span>}
                    </button>
                  ))}
                  <div className="dropdown-divider" />
                </>
              )}
              <Link to="/select-branch" className="dropdown-item">
                <IconBuildingStore className="icon me-2 text-primary" stroke={1.5} />
                تغيير الفرع
              </Link>
              <a href="#" className="dropdown-item text-primary" onClick={(e) => { e.preventDefault(); setOpenDropdown(null); setShowRestoreModal(true); }}>
                <IconDatabase className="icon me-2 text-primary" stroke={1.5} />
                استعادة نسخة احتياطية
              </a>
              <a href="#" className="dropdown-item text-primary fw-bold" onClick={(e) => { e.preventDefault(); setOpenDropdown(null); setShowManualModal(true); }}>
                <IconBook className="icon me-2 text-primary" stroke={1.5} />
                دليل المستخدم
              </a>
              <a href="#" className="dropdown-item text-success fw-bold" onClick={(e) => { e.preventDefault(); setOpenDropdown(null); setShowUpdateModal(true); }}>
                <IconCloudDownload className="icon me-2 text-success" stroke={1.5} />
                تحديث البرنامج
              </a>
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
                <Link className="nav-link" to="/receipts" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconReceipt size={17} stroke={1.5} />
                  </span>
                  <span className="nav-link-title">دفتر المبيعات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/dimensions') ? 'active' : ''}`}>
                <Link className="nav-link" to="/dimensions" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconBuildingStore size={17} stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الإدارة</span>
                </Link>
              </li>

              {!isPrintOnly && (
                <li className={`nav-item ${location.pathname.startsWith('/search-purchases') || location.pathname.startsWith('/purchases') ? 'active' : ''}`}>
                  <Link className="nav-link" to="/search-purchases" onClick={() => setOpenDropdown(null)}>
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconPackage size={17} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">المشتريات</span>
                  </Link>
                </li>
              )}

              {!isPrintOnly && (
                <li className={`nav-item ${location.pathname.startsWith('/expenses') ? 'active' : ''}`}>
                  <Link className="nav-link" to="/expenses" onClick={() => setOpenDropdown(null)}>
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconCash size={17} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">المصروفات</span>
                  </Link>
                </li>
              )}

              {!isPrintOnly && (
                <li className={`nav-item ${location.pathname.startsWith('/reports') ? 'active' : ''}`}>
                  <Link className="nav-link" to="/reports/dashboard" onClick={() => setOpenDropdown(null)}>
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconChartBar size={17} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">التقارير</span>
                  </Link>
                </li>
              )}

              <li className={`nav-item ${location.pathname.startsWith('/tools') ? 'active' : ''}`}>
                <Link className="nav-link" to="/tools" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconTool size={17} stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الأدوات</span>
                </Link>
              </li>

              <li className={`nav-item ${location.pathname.startsWith('/settings') ? 'active' : ''}`}>
                <Link className="nav-link" to="/settings" onClick={() => setOpenDropdown(null)}>
                  <span className="nav-link-icon d-md-none d-lg-inline-block">
                    <IconSettings size={17} stroke={1.5} />
                  </span>
                  <span className="nav-link-title">الإعدادات</span>
                </Link>
              </li>

            </ul>
          </div>
        </div>
      </div>
      <QuickRestoreModal isOpen={showRestoreModal} onClose={() => setShowRestoreModal(false)} />
      <UpdateModal isOpen={showUpdateModal} onClose={() => setShowUpdateModal(false)} />
      <UserManualModal isOpen={showManualModal} onClose={() => setShowManualModal(false)} />
    </header>
  );
}
