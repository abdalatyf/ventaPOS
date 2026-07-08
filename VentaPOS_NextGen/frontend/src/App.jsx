import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// استيراد الشاشات الأساسية
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Setup from './pages/Setup';
import AppShell from './components/AppShell';

import SystemInit from './pages/SystemInit';
import BranchSelection from './pages/BranchSelection';
import Purchases from './pages/Purchases';
import Expenses from './pages/Expenses';
import SearchReceipts from './pages/SearchReceipts';

// استيراد شاشات التقارير الجديدة
import DashboardReport from './pages/reports/DashboardReport';
import SalespersonPerformanceReport from './pages/reports/SalespersonPerformanceReport';
import InventoryMovementReport from './pages/reports/InventoryMovementReport';
import ProfitAndLossReport from './pages/reports/ProfitAndLossReport';
import CashDrawerReport from './pages/reports/CashDrawerReport';

// مكون حماية المسارات (Gatekeeper)
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const branchId = localStorage.getItem('branchId');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  if (!branchId) {
    return <Navigate to="/select-branch" replace />;
  }
  
  return children;
};

const TokenRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Placeholder page for un-implemented routes
const PlaceholderPage = ({ title }) => (
  <div className="card">
    <div className="card-body text-center py-5">
      <h2 className="text-muted">صفحة: {title}</h2>
      <p className="text-secondary">جاري العمل على هذه الصفحة...</p>
    </div>
  </div>
);

function App() {
  useEffect(() => {
    const handleSubscriptionExpired = () => {
      alert('تنبيه الدفتر: انتهت صلاحية الاشتراك السحابي للشركة. يرجى تفعيل الرخصة.');
    };
    
    window.addEventListener('subscription_expired', handleSubscriptionExpired);
    return () => window.removeEventListener('subscription_expired', handleSubscriptionExpired);
  }, []);

  return (
    <Router>
      <Routes>
        {/* المسارات العامة خارج الـ Shell */}
        <Route path="/init" element={<SystemInit />} />
        <Route path="/login" element={<Login />} />
        
        {/* Gateway لاختيار الفرع - يحتاج توكن لكن لا يحتاج فرع */}
        <Route path="/select-branch" element={
          <TokenRoute><BranchSelection /></TokenRoute>
        } />
        
        {/* المسارات المحمية داخل الـ AppShell */}
        <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route index element={<Navigate to="/receipts" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="pos" element={<POS />} />
          
          {/* التأسيس والإعدادات */}
          <Route path="setup" element={<Setup />} />
          
          {/* مسارات المبيعات */}
          <Route path="receipts" element={<SearchReceipts />} />
          
          {/* مسارات المخزون */}
          <Route path="inventory" element={<PlaceholderPage title="الأصناف" />} />
          <Route path="product-ledger/:id" element={<PlaceholderPage title="حركة صنف" />} />
          <Route path="purchases" element={<Purchases />} />
          <Route path="expenses" element={<Expenses />} />
          
          {/* مسارات التقارير */}
          <Route path="reports/sales" element={<PlaceholderPage title="الجرد والمبيعات" />} />
          <Route path="collections" element={<PlaceholderPage title="التحصيلات" />} />
          
          <Route path="reports/dashboard" element={<DashboardReport />} />
          <Route path="reports/salesperson" element={<SalespersonPerformanceReport />} />
          <Route path="reports/inventory" element={<InventoryMovementReport />} />
          <Route path="reports/profit-and-loss" element={<ProfitAndLossReport />} />
          <Route path="reports/cash-drawer" element={<CashDrawerReport />} />
          
          {/* مسارات الأدوات */}
          <Route path="tools/cloud" element={<PlaceholderPage title="الربط أونلاين" />} />
          <Route path="tools/backup" element={<PlaceholderPage title="النسخ الاحتياطي" />} />
          
          {/* مسارات الإعدادات الأخرى */}
          <Route path="settings/company" element={<PlaceholderPage title="بيانات الشركة" />} />
          <Route path="settings/license" element={<PlaceholderPage title="الاشتراك" />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
