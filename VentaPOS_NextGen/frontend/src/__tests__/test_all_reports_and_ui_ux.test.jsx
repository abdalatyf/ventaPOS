import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi } from 'vitest';

import ReportsLayout from '../pages/reports/ReportsLayout';
import DashboardReport from '../pages/reports/DashboardReport';
import ReceiptsReport from '../pages/reports/ReceiptsReport';
import PurchasesReport from '../pages/reports/PurchasesReport';
import AreasReport from '../pages/reports/AreasReport';
import InstallmentsReport from '../pages/reports/InstallmentsReport';
import ExpensesReport from '../pages/reports/ExpensesReport';
import ProfitAndLossReport from '../pages/reports/ProfitAndLossReport';
import AveragesReport from '../pages/reports/AveragesReport';
import InventoryMovementReport from '../pages/reports/InventoryMovementReport';
import SalespersonPerformanceReport from '../pages/reports/SalespersonPerformanceReport';

vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('/default-date/')) {
        return Promise.resolve({ data: { month: 8, year: 2026 } });
      }
      if (url.includes('/salespersons/')) {
        return Promise.resolve({ data: [{ id: 1, name: 'محمد علي' }] });
      }
      if (url.includes('/suppliers/')) {
        return Promise.resolve({ data: [{ id: 1, name: 'مورد تجريبي' }] });
      }
      if (url.includes('/reports/dashboard/summary/')) {
        return Promise.resolve({
          data: {
            sales: { gross: 100000, net: 95000, cash: 40000, installment: 60000, down_payments: 15000, returns: 5000 },
            collections: { expected: 20000, actual: 18000, percentage: 90 },
            purchases: { total: 50000, returns: 2000, net: 48000 },
            expenses: { total: 7000 },
            profit: { gross: 30000, net: 23000 }
          }
        });
      }
      if (url.includes('/reports/dashboard/')) {
        return Promise.resolve({
          data: {
            kpis: { total_sales: 100000, total_expenses: 7000, net_profit: 23000 }
          }
        });
      }
      if (url.includes('/receipts/printers/')) {
        return Promise.resolve({
          data: {
            printers: [{ name: 'HP LaserJet', status: 'ready', is_default: true }]
          }
        });
      }
      if (url.includes('/reports/purchases/')) {
        return Promise.resolve({
          data: {
            items: [
              {
                item_id: 1,
                item_name: 'طقم لحاف',
                supplier_id: 1,
                supplier_name: 'مورد تجريبي',
                invoices_count: 1,
                purchased_qty: 10,
                returned_qty: 0,
                net_qty: 10,
                avg_unit_cost: 500,
                gross_purchases: 5000,
                returns_amount: 0,
                net_purchases: 5000
              }
            ],
            invoices: [
              {
                id: 1,
                product_name: 'طقم لحاف',
                supplier_name: 'مورد تجريبي',
                total_qty: 10,
                unit_cost: 500,
                total_cost: 5000,
                returns_qty: 0,
                net_qty: 10
              }
            ],
            summary: { total_purchases_amount: 5000, gross_purchases_amount: 5000, total_returns_amount: 0, total_items_quantity: 10, distinct_products_count: 1, suppliers_count: 1 }
          }
        });
      }
      if (url.includes('/reports/areas/')) {
        return Promise.resolve({
          data: {
            areas: [
              {
                area: 'الدقي',
                salesperson_name: 'محمد علي',
                gross_sales: 50000,
                cash_sales: 20000,
                credit_sales: 30000,
                down_payments: 5000,
                due_installments: 25000,
                returns_total: 0,
                net_sales: 50000
              }
            ],
            summary: { total_gross: 50000, total_net: 50000 }
          }
        });
      }
      if (url.includes('/reports/installments/')) {
        return Promise.resolve({
          data: {
            schedules: [
              {
                id: 1,
                receipt_number: 101,
                customer_name: 'علي حسن',
                phone: '01000000000',
                area: 'الدقي',
                salesperson_name: 'محمد علي',
                monthly_amount: 500,
                start_month: 9,
                start_year: 2026,
                total_amount: 3000
              }
            ],
            summary: { total_amount: 3000 }
          }
        });
      }
      if (url.includes('/reports/averages/')) {
        return Promise.resolve({
          data: {
            products: [
              {
                id: 1,
                product_name: 'طقم لحاف',
                sales_count: 5,
                total_units_sold: 10,
                total_revenue: 6000,
                average_unit_price: 600
              }
            ]
          }
        });
      }
      if (url.includes('/reports/inventory-movement/')) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 1,
                product_name: 'طقم لحاف',
                initial_qty: 10,
                purchases_qty: 20,
                sales_qty: 8,
                returns_qty: 1,
                current_stock: 23
              }
            ]
          }
        });
      }
      if (url.includes('/reports/salesperson-performance/')) {
        return Promise.resolve({
          data: {
            performance: [
              {
                salesperson_id: 1,
                salesperson_name: 'محمد علي',
                gross_sales: 50000,
                sales_commission: 2500,
                collection_commission: 1500,
                total_salary: 4000
              }
            ]
          }
        });
      }
      if (url.includes('/reports/profit-and-loss/')) {
        return Promise.resolve({
          data: {
            summary: {
              sales_revenue: 100000,
              cost_of_goods_sold: 70000,
              gross_profit: 30000,
              operating_expenses: 7000,
              net_profit: 23000
            }
          }
        });
      }
      if (url.includes('/reports/expenses/')) {
        return Promise.resolve({
          data: {
            categories: [{ category: 'إيجار', total_amount: 5000 }],
            total: 5000
          }
        });
      }
      return Promise.resolve({ data: { results: [], count: 0 } });
    }),
    post: vi.fn(() => Promise.resolve({ data: {} })),
  },
  getLicenseStatus: vi.fn(() => Promise.resolve({ is_print_only: false, is_expired: false, status: 'active' })),
  clearLicenseCache: vi.fn(),
}));

describe('All 10 Reports & UI/UX Audit Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('branchId', '1');
    vi.clearAllMocks();
  });

  const reportRoutes = [
    { name: 'Dashboard', path: '/reports/dashboard', component: <DashboardReport /> },
    { name: 'Receipts', path: '/reports/receipts', component: <ReceiptsReport /> },
    { name: 'Purchases', path: '/reports/purchases', component: <PurchasesReport /> },
    { name: 'Areas', path: '/reports/areas', component: <AreasReport /> },
    { name: 'Installments', path: '/reports/installments', component: <InstallmentsReport /> },
    { name: 'Expenses', path: '/reports/expenses', component: <ExpensesReport /> },
    { name: 'ProfitAndLoss', path: '/reports/profit-and-loss', component: <ProfitAndLossReport /> },
    { name: 'Averages', path: '/reports/averages', component: <AveragesReport /> },
    { name: 'InventoryMovement', path: '/reports/inventory-movement', component: <InventoryMovementReport /> },
    { name: 'SalespersonPerformance', path: '/reports/salesperson-performance', component: <SalespersonPerformanceReport /> },
  ];

  for (const rep of reportRoutes) {
    it(`renders ${rep.name} report complying with UI/UX rules (no glassmorphism, proper sticky headers)`, async () => {
      const { container, unmount } = render(
        <MemoryRouter initialEntries={[`${rep.path}?year=2026&month=8`]}>
          <Routes>
            <Route path="/reports" element={<ReportsLayout />}>
              <Route path={rep.path.replace('/reports/', '')} element={rep.component} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        // Red line check: strictly NO glassmorphism / .premium-card classes anywhere
        expect(container.querySelector('.premium-card')).toBeNull();
        expect(container.querySelector('.glassmorphism')).toBeNull();

        // 4-Row / Standardized Table top section check
        expect(container.querySelector('.standard-page-top-section')).not.toBeNull();
        expect(container.querySelector('.standard-page-header')).not.toBeNull();
        expect(container.querySelector('.standard-top-card')).not.toBeNull();
        if (rep.name !== 'Dashboard') {
          expect(container.querySelector('.sticky-toolbar')).not.toBeNull();
        }
      }, { timeout: 3000 });

      unmount();
    });
  }

  it('verifies tabular-nums and Western whole integer numbers rendered without decimals', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/reports/areas?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="areas" element={<AreasReport />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      const table = container.querySelector('table');
      expect(table).not.toBeNull();
      expect(table.className).toContain('tabular-nums');

      // Check text in table does not have .00 decimals
      const text = table.textContent;
      expect(text).not.toContain('.00');
    });
  });

  it('opens PrintModal instead of calling desktop_print directly when clicking header print on AreasReport', async () => {
    const { default: api } = await import('../api');
    render(
      <MemoryRouter initialEntries={['/reports/areas?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="areas" element={<AreasReport />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('الدقي')).toBeInTheDocument();
    });

    const headerPrintBtn = screen.getByRole('button', { name: /طباعة التقرير/ });
    fireEvent.click(headerPrintBtn);

    await waitFor(() => {
      expect(screen.getByText('طباعة تقرير المناطق والتحصيل الجغرافي')).toBeInTheDocument();
    });
    expect(api.post).not.toHaveBeenCalled();
  });

  it('opens PrintModal instead of calling desktop_print directly when clicking header print on PurchasesReport', async () => {
    const { default: api } = await import('../api');
    render(
      <MemoryRouter initialEntries={['/reports/purchases?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="purchases" element={<PurchasesReport />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('طقم لحاف')).toBeInTheDocument();
    });

    const headerPrintBtn = screen.getByRole('button', { name: /طباعة التقرير/ });
    fireEvent.click(headerPrintBtn);

    await waitFor(() => {
      expect(screen.getByText('طباعة تقرير المشتريات والموردين')).toBeInTheDocument();
    });
    expect(api.post).not.toHaveBeenCalled();
  });
});
