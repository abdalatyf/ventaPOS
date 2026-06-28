import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Inventory from './pages/Inventory';
import POS from './pages/POS';
import PosEntry from './pages/PosEntry';
import ProductLedger from './pages/ProductLedger';
import Settings from './pages/Settings';
import Purchases from './pages/Purchases';
import ActivationModal from './components/ActivationModal';

function App() {
  const [isActivationModalOpen, setActivationModalOpen] = useState(false);

  useEffect(() => {
    const handleShowModal = () => setActivationModalOpen(true);
    window.addEventListener('show-activation-modal', handleShowModal);
    
    return () => {
      window.removeEventListener('show-activation-modal', handleShowModal);
    };
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/inventory/:id" element={<ProductLedger />} />
        <Route path="/pos" element={<POS />} />
        <Route path="/receipt-entry" element={<PosEntry />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/purchases" element={<Purchases />} />
      </Routes>
      <ActivationModal 
        isOpen={isActivationModalOpen} 
        onClose={() => setActivationModalOpen(false)} 
      />
    </BrowserRouter>
  );
}

export default App;
