import React, { useState } from 'react';
import SyncTab from './SyncTab';
import BackupTab from './BackupTab';
import { IconCloudDataConnection, IconShieldLock } from '@tabler/icons-react';

const ToolsDashboard = () => {
  const [activeTab, setActiveTab] = useState('backup');

  return (
    <div className="page-wrapper" dir="rtl">
      <div className="page-body mt-0 pt-0">
        <div className="container-fluid px-3">
          <div className="card shadow-none border-0 rounded-0">
            <div className="card-header bg-white pt-3 pb-0 px-4 position-sticky top-0 border-bottom" style={{ zIndex: 10 }}>
              <ul className="nav nav-tabs card-header-tabs" data-bs-toggle="tabs">
                {/* USB Sync deactivated dormant mode (P2-4.1) */}
                {/* <li className="nav-item">
                  <button 
                    type="button"
                    className={`nav-link fw-bold fs-4 ${activeTab === 'sync' ? 'active text-primary border-primary' : 'text-muted'}`} 
                    onClick={() => setActiveTab('sync')}
                  >
                    <IconCloudDataConnection className="me-2" /> المزامنة والربط
                  </button>
                </li> */}
                <li className="nav-item">
                  <button 
                    type="button"
                    className={`nav-link fw-bold fs-4 ${activeTab === 'backup' ? 'active text-primary border-primary' : 'text-muted'}`} 
                    onClick={() => setActiveTab('backup')}
                  >
                    <IconShieldLock className="me-2" /> النسخ الاحتياطي والاستعادة
                  </button>
                </li>
              </ul>
            </div>
            <div className="card-body p-4 bg-light">
              <div className="tab-content">
                {/* Dormant Sync tab kept for future reactivation */}
                {activeTab === 'sync' && (
                  <div className={`tab-pane fade ${activeTab === 'sync' ? 'active show' : ''}`} id="tabs-sync">
                    <SyncTab />
                  </div>
                )}
                <div className={`tab-pane fade ${activeTab === 'backup' ? 'active show' : ''}`} id="tabs-backup">
                  {activeTab === 'backup' && <BackupTab />}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolsDashboard;
