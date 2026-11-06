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
      row1={
        <div className="d-flex align-items-center gap-2 flex-shrink-0">
          {!isPrintOnly && (
            <button 
              type="button" 
              className={`btn btn-sm fw-bold d-flex align-items-center gap-1 px-3 py-1 ${activeTab === 'inventory' ? 'btn-primary' : 'btn-outline-secondary border-secondary-subtle'}`}
              onClick={() => setActiveTab('inventory')}
            >
              <IconPackage size={16} />
              <span>تأسيس الأصناف</span>
            </button>
          )}
          <button 
            type="button" 
            className={`btn btn-sm fw-bold d-flex align-items-center gap-1 px-3 py-1 ${activeTab === 'salespersons' ? 'btn-primary' : 'btn-outline-secondary border-secondary-subtle'}`}
            onClick={() => setActiveTab('salespersons')}
          >
            <IconUsers size={16} />
            <span>تأسيس المناديب</span>
          </button>
          {!isPrintOnly && (
            <button 
              type="button" 
              className={`btn btn-sm fw-bold d-flex align-items-center gap-1 px-3 py-1 ${activeTab === 'suppliers' ? 'btn-primary' : 'btn-outline-secondary border-secondary-subtle'}`}
              onClick={() => setActiveTab('suppliers')}
            >
              <IconTruck size={16} />
              <span>تأسيس الموردين</span>
            </button>
          )}
        </div>
      }
    >
      {activeTab === 'inventory' && !isPrintOnly && <InventoryTab />}
      {activeTab === 'salespersons' && <SalespersonsTab />}
      {activeTab === 'suppliers' && !isPrintOnly && <SuppliersTab />}
    </StandardTablePageLayout>
  );
}
