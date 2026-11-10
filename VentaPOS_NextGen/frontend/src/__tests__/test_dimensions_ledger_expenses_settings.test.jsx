import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import Dimensions from '../pages/Dimensions';
import ProductLedger from '../pages/ProductLedger';
import Expenses from '../pages/Expenses';
import SettingsIndex from '../pages/settings/SettingsIndex';

vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('/branches/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'الفرع الرئيسي', code: 'MAIN' }]
        });
      }
      if (url.includes('/salespersons/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'محمد علي', phone: '01000000000', is_active: true }]
        });
      }
      if (url.includes('/suppliers/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'شركة الأمل', phone: '01222222222' }]
        });
      }
      if (url.includes('/ledger/')) {
        return Promise.resolve({
          data: {
            item: { id: 1, name: 'ثلاجة شارب', current_stock: 8, initial_quantity: 10 },
            timeline: [
              {
                id: 1,
                event_type: 'INITIAL',
                date: '2026-01-01',
                year: 2026,
                month: 1,
                change_qty: 10,
                running_stock: 10,
                notes: 'رصيد أول المدة'
              }
            ],
            metrics: { purchases: 0, sales: 2, returns: 0, deficit: 0 }
          }
        });
      }
      if (url.includes('/inventory-items/') || url.includes('/inventory/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'ثلاجة شارب', stock: 8, initial_quantity: 10, initial_commission_amount: 100 }]
        });
      }
      if (url.includes('/expenses/categories/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'كهرباء وإنارة' }, { id: 2, name: 'إيجار' }]
        });
      }
      if (url.includes('/expenses/')) {
        return Promise.resolve({
          data: {
            count: 1,
            total_amount: 1500,
            results: [
              {
                id: 1,
                description: 'إيجار شهر أغسطس',
                category: 'إيجار',
                amount: 1500,
                expense_month: 8,
                expense_year: 2026
              }
            ]
          }
        });
      }
      if (url.includes('/default-date/')) {
        return Promise.resolve({ data: { month: 8, year: 2026 } });
      }
      if (url.includes('/company-settings/')) {
        return Promise.resolve({
          data: {
            name: 'مؤسسة التجارة الحديثة',
            phone: '01000000000',
            collection_commission_rate: 0.1
          }
        });
      }
      if (url.includes('/license/status/')) {
        return Promise.resolve({
          data: {
            status: 'active',
            total_invoices_balance: 4000,
            expiry_date: '2027-01-01',
            is_print_only: false
          }
        });
      }
      return Promise.resolve({ data: {} });
    }),
    post: vi.fn((url) => {
      if (url.includes('/expenses/')) {
        return Promise.resolve({ data: { id: 2, amount: 200 } });
      }
      if (url.includes('/adjustments/')) {
        return Promise.resolve({ data: { id: 3, quantity: 1 } });
      }
      return Promise.resolve({ data: {} });
    }),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  getLicenseStatus: vi.fn(() => Promise.resolve({ is_print_only: false, is_expired: false, status: 'active' })),
  clearLicenseCache: vi.fn(),
}));

describe('Dimensions, Ledger, Expenses & Settings Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('branchId', '1');
    vi.clearAllMocks();
  });

  it('renders Dimensions tabs and switches between them', async () => {
    render(
      <BrowserRouter>
        <Dimensions />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/تأسيس الأصناف/i)).toBeInTheDocument();
      expect(screen.getByText(/تأسيس المناديب/i)).toBeInTheDocument();
      expect(screen.getByText(/تأسيس الموردين/i)).toBeInTheDocument();
    });

    // Click on Suppliers tab
    fireEvent.click(screen.getByText(/تأسيس الموردين/i));
    await waitFor(() => {
      expect(screen.getByText(/شركة الأمل/i)).toBeInTheDocument();
    });
  });

  it('renders ProductLedger with metrics and timeline', async () => {
    render(
      <MemoryRouter initialEntries={['/product-ledger/1']}>
        <Routes>
          <Route path="/product-ledger/:id" element={<ProductLedger />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue(/ثلاجة شارب/i)).toBeInTheDocument();
      expect(screen.getByText(/رصيد البداية/i)).toBeInTheDocument();
    });
  });

  it('renders Expenses page with sticky toolbar and expense records', async () => {
    render(
      <BrowserRouter>
        <Expenses />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/إيجار شهر أغسطس/i)).toBeInTheDocument();
    });

    expect(document.querySelector('.sticky-toolbar')).toBeInTheDocument();
  });

  it('renders SettingsIndex and switches between Company, Security, and Subscription tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <SettingsIndex />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/بيانات الشركة/i)).toBeInTheDocument();
      expect(screen.getByText(/الأمان وكلمة المرور/i)).toBeInTheDocument();
      expect(screen.getByText(/تفاصيل الاشتراك/i)).toBeInTheDocument();
    });

    // Switch to Security tab
    fireEvent.click(screen.getByText(/الأمان وكلمة المرور/i));
    await waitFor(() => {
      expect(screen.getByText(/تغيير كلمة المرور/i)).toBeInTheDocument();
    });
  });
});
