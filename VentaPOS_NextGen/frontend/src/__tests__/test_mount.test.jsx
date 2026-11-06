import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import POS from '../pages/POS';
import SearchReceipts from '../pages/SearchReceipts';
import SearchPurchases from '../pages/SearchPurchases';
import Expenses from '../pages/Expenses';
import Dimensions from '../pages/Dimensions';
import ReportsLayout from '../pages/reports/ReportsLayout';
import ReceiptsReport from '../pages/reports/ReceiptsReport';
import PurchasesReport from '../pages/reports/PurchasesReport';
import { vi } from 'vitest';

// Mock the api module to return empty arrays/objects immediately
vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('/default-date/')) {
        return Promise.resolve({ data: { month: 8, year: 2026 } });
      }
      if (url.includes('/reports/purchases/')) {
        return Promise.resolve({ data: { invoices: [], summary: {} } });
      }
      return Promise.resolve({ data: { results: [], count: 0 } });
    }),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  }
}));

describe('POS & Standardized Table Pages Mount Tests', () => {
  it('should mount and render POS without crashing', async () => {
    const { container } = render(
      <BrowserRouter>
        <POS />
      </BrowserRouter>
    );
    await waitFor(() => {
      const spinner = container.querySelector('.spinner-border');
      if (spinner) throw new Error('Spinner still here');
    }, { timeout: 3000 });
  });

  it('should mount all 5 standardized table pages with identical Title + 2-Row top structure and sticky table headers', async () => {
    const pages = [
      <BrowserRouter key="receipts"><SearchReceipts /></BrowserRouter>,
      <BrowserRouter key="purchases"><SearchPurchases /></BrowserRouter>,
      <BrowserRouter key="expenses"><Expenses /></BrowserRouter>,
      <BrowserRouter key="dimensions"><Dimensions /></BrowserRouter>,
      <MemoryRouter key="reports-receipts" initialEntries={['/reports/receipts?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="receipts" element={<ReceiptsReport />} />
          </Route>
        </Routes>
      </MemoryRouter>,
      <MemoryRouter key="reports-purchases" initialEntries={['/reports/purchases?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="purchases" element={<PurchasesReport />} />
          </Route>
        </Routes>
      </MemoryRouter>,
    ];

    for (const page of pages) {
      const { container, unmount } = render(page);
      await waitFor(() => {
        expect(container.querySelector('.standard-page-top-section')).not.toBeNull();
        expect(container.querySelector('.standard-page-header')).not.toBeNull();
        expect(container.querySelector('.standard-top-card')).not.toBeNull();
        expect(container.querySelector('.standard-top-row-1')).not.toBeNull();
        expect(container.querySelector('.standard-top-row-2')).not.toBeNull();
        expect(container.querySelector('.standard-page-table-area')).not.toBeNull();
        expect(container.querySelector('.table-sticky-header, .report-sticky-header')).not.toBeNull();
        const tableContainer = container.querySelector('.report-table-container');
        expect(tableContainer).not.toBeNull();
        expect(tableContainer.style.overflow).not.toBe('visible');
      }, { timeout: 3000 });
      unmount();
    }
  });
});

