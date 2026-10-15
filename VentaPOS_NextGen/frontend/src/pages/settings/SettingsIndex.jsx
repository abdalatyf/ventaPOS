import React, { useState } from 'react';
import CompanyTab from './tabs/CompanyTab';
import SecurityTab from './tabs/SecurityTab';
import SubscriptionTab from './tabs/SubscriptionTab';
import { IconBuildingStore, IconShieldLock, IconKey } from '@tabler/icons-react';

import { useLocation } from 'react-router-dom';

export default function SettingsIndex() {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const initialTab = searchParams.get('tab') || 'company';
  
  const [activeTab, setActiveTab] = useState(initialTab);

  // If the URL changes (e.g. from DemoBanner), update the tab
  React.useEffect(() => {
    const tab = new URLSearchParams(location.search).get('tab');
    if (tab) setActiveTab(tab);
  }, [location.search]);

  return (
    <div className="container-fluid px-0">
      {/* Removed page header to stick tabs to navbar */}

      <div className="card shadow-none border-0 animate__animated animate__fadeIn rounded-0" style={{ marginTop: '-1rem' }}>
        <div className="card-header border-bottom-0 p-0 bg-white sticky-top" style={{ top: '60px', zIndex: 1020, borderBottom: '1px solid #dee2e6' }}>
          <ul className="nav nav-tabs nav-fill w-100" data-bs-toggle="tabs">
            <li className="nav-item">
              <button 
                className={`nav-link fw-bold py-3 ${activeTab === 'company' ? 'active' : ''}`}
                onClick={() => setActiveTab('company')}
              >
                <IconBuildingStore className="me-2" />
                بيانات الشركة
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link fw-bold py-3 ${activeTab === 'security' ? 'active' : ''}`}
                onClick={() => setActiveTab('security')}
              >
                <IconShieldLock className="me-2" />
                الأمان وكلمة المرور
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link fw-bold py-3 ${activeTab === 'subscription' ? 'active' : ''}`}
                onClick={() => setActiveTab('subscription')}
              >
                <IconKey className="me-2" />
                تفاصيل الاشتراك
              </button>
            </li>
          </ul>
        </div>
        <div className="card-body p-4 bg-light" style={{ minHeight: '60vh' }}>
          <div className="tab-content">
            <div className={`tab-pane ${activeTab === 'company' ? 'active show' : ''}`}>
              {activeTab === 'company' && <CompanyTab />}
            </div>
            <div className={`tab-pane ${activeTab === 'security' ? 'active show' : ''}`}>
              {activeTab === 'security' && <SecurityTab />}
            </div>
            <div className={`tab-pane ${activeTab === 'subscription' ? 'active show' : ''}`}>
              {activeTab === 'subscription' && <SubscriptionTab />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
