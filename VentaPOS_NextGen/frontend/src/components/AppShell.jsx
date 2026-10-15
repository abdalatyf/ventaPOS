import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function AppShell() {
  return (
    <div className="page" dir="rtl">
      <Navbar />
      <div className="page-wrapper">
        <div className="page-body m-0 p-0">
          <div className="container-fluid p-0">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
