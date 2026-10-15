import React, { useState } from 'react';
import SyncTab from './SyncTab';
import SmartImportTab from './SmartImportTab';
import BackupTab from './BackupTab';
import LogsTab from './LogsTab';
import { IconCloudDataConnection, IconDatabaseImport, IconShieldLock, IconHistory } from '@tabler/icons-react';

const ToolsDashboard = () => {
  const [activeTab, setActiveTab] = useState('sync');

  return (
    <div className="page-wrapper">
      <div className="page-body mt-0 pt-0">
        <div className="container-xl px-0">
          <div className="card shadow-none border-0 rounded-0">
            <div className="card-header bg-white pt-3 pb-0 px-4 position-sticky top-0 border-bottom" style={{ zIndex: 10 }}>
              <ul className="nav nav-tabs nav-fill card-header-tabs" data-bs-toggle="tabs">
                <li className="nav-item">
                  <a href="#tabs-sync" className={`nav-link fw-bold fs-4 ${activeTab === 'sync' ? 'active text-primary border-primary' : 'text-muted'}`} onClick={() => setActiveTab('sync')}>
                    <IconCloudDataConnection className="me-2" /> المزامنة والربط
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-import" className={`nav-link fw-bold fs-4 ${activeTab === 'import' ? 'active text-primary border-primary' : 'text-muted'}`} onClick={() => setActiveTab('import')}>
                    <IconDatabaseImport className="me-2" /> الاستيراد الذكي
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-backup" className={`nav-link fw-bold fs-4 ${activeTab === 'backup' ? 'active text-primary border-primary' : 'text-muted'}`} onClick={() => setActiveTab('backup')}>
                    <IconShieldLock className="me-2" /> النسخ الاحتياطي
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-logs" className={`nav-link fw-bold fs-4 ${activeTab === 'logs' ? 'active text-primary border-primary' : 'text-muted'}`} onClick={() => setActiveTab('logs')}>
                    <IconHistory className="me-2" /> سجل العمليات
                  </a>
                </li>
              </ul>
            </div>
            <div className="card-body p-4 bg-light">
              <div className="tab-content">
                <div className={`tab-pane fade ${activeTab === 'sync' ? 'active show' : ''}`} id="tabs-sync">
                  {activeTab === 'sync' && <SyncTab />}
                </div>
                <div className={`tab-pane fade ${activeTab === 'import' ? 'active show' : ''}`} id="tabs-import">
                  {activeTab === 'import' && <SmartImportTab />}
                </div>
                <div className={`tab-pane fade ${activeTab === 'backup' ? 'active show' : ''}`} id="tabs-backup">
                  {activeTab === 'backup' && <BackupTab />}
                </div>
                <div className={`tab-pane fade ${activeTab === 'logs' ? 'active show' : ''}`} id="tabs-logs">
                  {activeTab === 'logs' && <LogsTab />}
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
