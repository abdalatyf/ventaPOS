import React, { useState, useEffect } from 'react';
import { 
  IconUsers, 
  IconTruck, 
  IconPackage 
} from '@tabler/icons-react';
import api from '../api';
import SalespersonsTab from '../components/SalespersonsTab';
import SuppliersTab from '../components/SuppliersTab';
import InventoryTab from '../components/InventoryTab';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';

export default function Dimensions() {
  const [activeTab, setActiveTab] = useState('inventory');
  const [isPrintOnly, setIsPrintOnly] = useState(false);

  useEffect(() => {
    api.get('/license/status/').then(res => {
      if (res.data?.is_print_only) {
        setIsPrintOnly(true);
        setActiveTab('salespersons');
      }
    }).catch(err => console.error(err));
  }, []);

  return (
    <StandardTablePageLayout
      title="البيانات الأساسية والتأسيس"
      icon={IconPackage}
      toolbar={
        <div className="navbar-expand-md shadow-sm border rounded bg-white">
          <div className="navbar navbar-light bg-white border-0 py-1">
            <div className="container-fluid p-0">
              <ul className="navbar-nav flex-row gap-2">
                {!isPrintOnly && (
                  <li className={`nav-item ${activeTab === 'inventory' ? 'active' : ''}`}>
                    <a 
                      href="#tabs-inventory" 
                      className={`nav-link fw-bold px-3 py-2 rounded ${activeTab === 'inventory' ? 'bg-primary-lt text-primary' : 'text-dark'}`}
                      onClick={(e) => { e.preventDefault(); setActiveTab('inventory'); }}
                    >
                      <span className="nav-link-icon me-1">
                        <IconPackage size={20} stroke={1.5} />
                      </span>
                      <span className="nav-link-title">تأسيس الأصناف</span>
                    </a>
                  </li>
                )}
                <li className={`nav-item ${activeTab === 'salespersons' ? 'active' : ''}`}>
                  <a 
                    href="#tabs-salespersons" 
                    className={`nav-link fw-bold px-3 py-2 rounded ${activeTab === 'salespersons' ? 'bg-primary-lt text-primary' : 'text-dark'}`}
                    onClick={(e) => { e.preventDefault(); setActiveTab('salespersons'); }}
                  >
                    <span className="nav-link-icon me-1">
                      <IconUsers size={20} stroke={1.5} />
                    </span>
                    <span className="nav-link-title">تأسيس المناديب</span>
                  </a>
                </li>
                {!isPrintOnly && (
                  <li className={`nav-item ${activeTab === 'suppliers' ? 'active' : ''}`}>
                    <a 
                      href="#tabs-suppliers" 
                      className={`nav-link fw-bold px-3 py-2 rounded ${activeTab === 'suppliers' ? 'bg-primary-lt text-primary' : 'text-dark'}`}
                      onClick={(e) => { e.preventDefault(); setActiveTab('suppliers'); }}
                    >
                      <span className="nav-link-icon me-1">
                        <IconTruck size={20} stroke={1.5} />
                      </span>
                      <span className="nav-link-title">تأسيس الموردين</span>
                    </a>
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      }
    >
      <div className="tab-content py-2">
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
    </StandardTablePageLayout>
  );
}
