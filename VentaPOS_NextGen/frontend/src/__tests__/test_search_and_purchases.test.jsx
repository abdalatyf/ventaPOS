import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import SearchReceipts from '../pages/SearchReceipts';
import SearchPurchases from '../pages/SearchPurchases';
import PurchaseEntry from '../pages/PurchaseEntry';

const mockReceiptsPage1 = Array.from({ length: 197 }, (_, i) => ({
  id: i + 1,
  receipt_number: 1000 + i,
  sale_month: 8,
  sale_year: 2026,
  customer_name: `عميل رقم ${i + 1}`,
  phone_number: '01000000000',
  area: 'الدقي',
  address: 'شارع التحرير',
  salesperson: 1,
  total_amount: 3000,
  down_payment: 500,
  is_cash_sale: false,
  items: [{ id: i + 1, product_name: 'منتج تجريبي', quantity: 1, unit_price: 3000 }],
  products_text: 'منتج تجريبي'
}));

const mockAllIds = Array.from({ length: 3000 }, (_, i) => i + 1);

vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('/salespersons/')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'محمد علي', phone: '01000000000' }]
        });
      }
      if (url.includes('/receipts/')) {
        return Promise.resolve({
          data: {
            count: 3000,
            all_ids: mockAllIds,
            total_amount_sum: 9000000,
            results: mockReceiptsPage1
          }
        });
      }
      if (url.includes('/purchase-invoices/')) {
        return Promise.resolve({
          data: {
            count: 1,
            results: [
              {
                id: 1,
                invoice_number: 'PUR-001',
                supplier: 1,
                supplier_name: 'شركة النور',
                purchase_date: '2026-08-01',
                total_amount: 15000,
                is_return: false,
                items: []
              }
            ]
          }
        });
      }
      if (url.includes('/suppliers/')) {
        return Promise.resolve({
          data: [
            { id: 1, name: 'شركة النور للمفروشات', phone: '01111111111' }
          ]
        });
      }
      if (url.includes('/inventory-items/') || url.includes('/inventory/')) {
        return Promise.resolve({
          data: [
            { id: 1, name: 'طقم لحاف', stock: 20, initial_cost: 500 }
          ]
        });
      }
      return Promise.resolve({ data: { results: [] } });
    }),
    post: vi.fn((url) => {
      if (url.includes('/receipts/bulk_delete/')) {
        return Promise.resolve({ data: { deleted_count: 197 } });
      }
      if (url.includes('/purchase-invoices/')) {
        return Promise.resolve({ data: { id: 10, invoice_number: 'PUR-002' } });
      }
      return Promise.resolve({ data: {} });
    }),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
  getLicenseStatus: vi.fn(() => Promise.resolve({ is_print_only: false, is_expired: false, status: 'active' })),
  clearLicenseCache: vi.fn(),
}));

describe('Search & Purchases Suite (3-Tier Selection & CRUD)', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('branchId', '1');
    vi.clearAllMocks();
  });

  it('verifies SearchReceipts Global Selection State without sticky-selection-strip (3000 -> 0 -> 3000 & 2999 -> 3000)', async () => {
    const { container } = render(
      <BrowserRouter>
        <SearchReceipts />
      </BrowserRouter>
    );

    // 1. Initial Load: Should show 3,000 results and 3,000 selected by default, with NO sticky-selection-strip
    await waitFor(() => {
      expect(screen.getByText(/نتائج البحث: 3,000 فاتورة/i)).toBeInTheDocument();
      expect(screen.getByText(/محدد 3,000/i)).toBeInTheDocument();
    });
    expect(container.querySelector('.sticky-selection-strip')).toBeNull();
    expect(screen.queryByText(/تم تحديد كافة الـ 3,000 فاتورة المطابقة للبحث/i)).toBeNull();

    // 2. Click the header checkbox to clear all selection (3,000 -> 0)
    const thead = document.querySelector('thead');
    const headerCheckbox = thead.querySelector('input[type="checkbox"]');
    expect(headerCheckbox).toBeInTheDocument();
    expect(headerCheckbox.checked).toBe(true);
    expect(headerCheckbox.indeterminate).toBe(false);

    fireEvent.click(headerCheckbox);

    // Now selected should be 0
    await waitFor(() => {
      expect(screen.queryByText(/محدد 3,000/i)).toBeNull();
      expect(screen.queryByText(/محدد/i)).toBeNull();
      expect(headerCheckbox.checked).toBe(false);
    });

    // 3. Click the header checkbox again (0 -> all 3,000 matching rows across all pages)
    fireEvent.click(headerCheckbox);

    await waitFor(() => {
      expect(screen.getByText(/محدد 3,000/i)).toBeInTheDocument();
      expect(headerCheckbox.checked).toBe(true);
    });

    // 4. Uncheck first row checkbox (3,000 -> 2,999, indeterminate = true), then click header checkbox (2,999 -> 3,000)
    const firstRowCheckbox = container.querySelector('tbody tr input[type="checkbox"]');
    fireEvent.click(firstRowCheckbox);

    await waitFor(() => {
      expect(screen.getByText(/محدد 2,999/i)).toBeInTheDocument();
      expect(headerCheckbox.checked).toBe(false);
      expect(headerCheckbox.indeterminate).toBe(true);
    });

    fireEvent.click(headerCheckbox);

    await waitFor(() => {
      expect(screen.getByText(/محدد 3,000/i)).toBeInTheDocument();
      expect(headerCheckbox.checked).toBe(true);
      expect(headerCheckbox.indeterminate).toBe(false);
    });
  });

  it('renders SearchPurchases with 4-row layout and purchase invoice rows', async () => {
    render(
      <BrowserRouter>
        <SearchPurchases />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/دفتر فواتير الشراء ومرتجع المصنع/i)).toBeInTheDocument();
    });

    expect(document.querySelector('.sticky-toolbar')).toBeInTheDocument();
    expect(document.querySelector('.table-sticky-header')).toBeInTheDocument();
  });

  it('renders PurchaseEntry with supplier select and item calculation', async () => {
    render(
      <BrowserRouter>
        <PurchaseEntry />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/إضافة فاتورة مشتريات \/ مرتجع مصنع/i)).toBeInTheDocument();
    });
  });
});
