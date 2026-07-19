import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// استيراد الشاشات الأساسية
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Setup from './pages/Setup';
import AppShell from './components/AppShell';
import ActivationModal from './components/ActivationModal';
import DemoBanner from './components/DemoBanner';

import SystemInit from './pages/SystemInit';
import BranchSelection from './pages/BranchSelection';
import PurchaseEntry from './pages/PurchaseEntry';
import SearchPurchases from './pages/SearchPurchases';
import Expenses from './pages/Expenses';
import SearchReceipts from './pages/SearchReceipts';
import Inventory from './pages/Inventory';
import ProductLedger from './pages/ProductLedger';

// استيراد شاشات التقارير الجديدة
import DashboardReport from './pages/reports/DashboardReport';
import SalespersonPerformanceReport from './pages/reports/SalespersonPerformanceReport';
import InventoryMovementReport from './pages/reports/InventoryMovementReport';
import ProfitAndLossReport from './pages/reports/ProfitAndLossReport';
import CashDrawerReport from './pages/reports/CashDrawerReport';
import ReportsIndex from './pages/reports/ReportsIndex';
import InstallmentsReport from './pages/reports/InstallmentsReport';
import ToolsDashboard from './pages/tools/ToolsDashboard';
import ReportsLayout from './pages/reports/ReportsLayout';
import ReceiptsReport from './pages/reports/ReceiptsReport';
import ExpensesReport from './pages/reports/ExpensesReport';
import SettingsIndex from './pages/settings/SettingsIndex';

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
  const [showActivationModal, setShowActivationModal] = useState(false);

  useEffect(() => {
    const handleSubscriptionExpired = () => {
      setShowActivationModal(true);
    };
    
    window.addEventListener('subscription_expired', handleSubscriptionExpired);
    return () => window.removeEventListener('subscription_expired', handleSubscriptionExpired);
  }, []);

  return (
    <>
      <ActivationModal isOpen={showActivationModal} onClose={() => setShowActivationModal(false)} />
      <Router>
        <DemoBanner />
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
          <Route path="inventory" element={<Inventory />} />
          <Route path="product-ledger/:id" element={<ProductLedger />} />
          <Route path="search-purchases" element={<SearchPurchases />} />
          <Route path="purchases/new" element={<PurchaseEntry />} />
          <Route path="purchases/edit/:id" element={<PurchaseEntry />} />
          <Route path="expenses" element={<Expenses />} />
          
          {/* مسارات التقارير */}
          <Route path="reports" element={<ReportsLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<DashboardReport />} />
            <Route path="receipts" element={<ReceiptsReport />} />
            <Route path="expenses" element={<ExpensesReport />} />
            <Route path="salesperson" element={<SalespersonPerformanceReport />} />
            <Route path="inventory" element={<InventoryMovementReport />} />
            <Route path="profit-and-loss" element={<ProfitAndLossReport />} />
            <Route path="cash-drawer" element={<CashDrawerReport />} />
            <Route path="installments" element={<InstallmentsReport />} />
          </Route>
          
          {/* مسارات الأدوات */}
          <Route path="tools/*" element={<ToolsDashboard />} />
          
          {/* مسارات الإعدادات */}
          <Route path="settings" element={<SettingsIndex />} />
        </Route>
      </Routes>
    </Router>
    </>
  );
}

export default App;
