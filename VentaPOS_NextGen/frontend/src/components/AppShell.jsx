import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function AppShell() {
  return (
    <div className="page" dir="rtl">
      <Navbar />
      <div className="page-wrapper d-flex flex-column flex-grow-1">
        <div className="page-body d-flex flex-column flex-grow-1 m-0 p-0" style={{ minHeight: 0 }}>
          <div className="container-fluid d-flex flex-column flex-grow-1 p-0" style={{ minHeight: 0 }}>
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
