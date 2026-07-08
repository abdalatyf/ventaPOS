import React, { useState } from 'react';
import { 
  IconUsers, 
  IconTruck, 
  IconPackage 
} from '@tabler/icons-react';
import SalespersonsTab from '../components/SalespersonsTab';
import SuppliersTab from '../components/SuppliersTab';
import InventoryTab from '../components/InventoryTab';

export default function Setup() {
  // الافتراضي هو الأصناف لأنها الأهم
  const [activeTab, setActiveTab] = useState('inventory');

  return (
    <>
      {/* Secondary Navbar for Tabs */}
      <div className="navbar-expand-md">
        <div className="collapse navbar-collapse">
          <div className="navbar navbar-light bg-white border-bottom shadow-sm">
            <div className="container-xl">
              <ul className="navbar-nav">
                <li className={`nav-item ${activeTab === 'inventory' ? 'active' : ''}`}>
                  <a 
                    href="#tabs-inventory" 
                    className="nav-link fw-bold" 
                    onClick={(e) => { e.preventDefault(); setActiveTab('inventory'); }}
                  >
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconPackage size={20} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">تأسيس الأصناف</span>
                  </a>
                </li>
                <li className={`nav-item ${activeTab === 'salespersons' ? 'active' : ''}`}>
                  <a 
                    href="#tabs-salespersons" 
                    className="nav-link fw-bold" 
                    onClick={(e) => { e.preventDefault(); setActiveTab('salespersons'); }}
                  >
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconUsers size={20} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">تأسيس المناديب</span>
                  </a>
                </li>
                <li className={`nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}>
                  <a 
                    href="#tabs-suppliers" 
                    className="nav-link fw-bold" 
                    onClick={(e) => { e.preventDefault(); setActiveTab('suppliers'); }}
                  >
                    <span className="nav-link-icon d-md-none d-lg-inline-block">
                      <IconTruck size={20} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">تأسيس الموردين</span>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="container-xl py-4">
        <div className="tab-content">
          <div className={`tab-pane ${activeTab === 'inventory' ? 'active show' : ''}`}>
            <InventoryTab />
          </div>
          <div className={`tab-pane ${activeTab === 'salespersons' ? 'active show' : ''}`}>
            <SalespersonsTab />
          </div>
          <div className={`tab-pane ${activeTab === 'suppliers' ? 'active show' : ''}`}>
            <SuppliersTab />
          </div>
        </div>
      </div>
    </>
  );
}
