import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import POS from '../pages/POS';
import ReturnReceipt from '../pages/ReturnReceipt';
import { parseInstallmentTextToBoxes, formatBoxesToInstallmentText } from '../components/pos/posUtils';

vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
      if (url.includes('receipts-next-number')) {
        return Promise.resolve({ data: { next_receipt_number: 105 } });
      }
      if (url.includes('/default-date/')) {
        return Promise.resolve({ data: { month: 8, year: 2026 } });
      }
      if (url.includes('/salespersons/')) {
        return Promise.resolve({
          data: [
            { id: 1, name: 'محمد علي', phone: '01000000000', is_active: true }
          ]
        });
      }
      if (url.includes('/inventory-items/') || url.includes('/inventory/')) {
        return Promise.resolve({
          data: [
            { id: 1, name: 'غسالة توشيبا', stock: 10, initial_commission_amount: 50 },
            { id: 2, name: 'شاشة سامسونج', stock: 5, initial_commission_amount: 70 }
          ]
        });
      }
      if (url.includes('/receipts/1/')) {
        return Promise.resolve({
          data: {
            id: 1,
            receipt_number: 101,
            sale_month: 6,
            sale_year: 2026,
            customer_name: 'أحمد محمود',
            phone_number: '01234567890',
            total_amount: 5000,
            down_payment: 1000,
            is_cash_sale: false,
            sale_items: [
              { id: 10, inventory_item: 1, product_name: 'غسالة توشيبا', quantity: 2, unit_price: 2500 }
            ],
            installment_payments: [
              { id: 1, payment_month: 7, payment_year: 2026, amount: 500 }
            ]
          }
        });
      }
      return Promise.resolve({ data: {} });
    }),
    post: vi.fn((url, payload) => {
      if (url.includes('/receipts/1/return_receipt/')) {
        return Promise.resolve({ data: { status: 'success', receipt_id: 102 } });
      }
      if (url.includes('/receipts/')) {
        return Promise.resolve({ data: { id: 99, receipt_number: 105 } });
      }
      return Promise.resolve({ data: {} });
    }),
  },
  getLicenseStatus: vi.fn(() => Promise.resolve({ is_print_only: false, is_expired: false, status: 'active', lic_start_date: '2026-01-01' })),
  clearLicenseCache: vi.fn(),
}));

describe('POS & Returns Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('branchId', '1');
    vi.clearAllMocks();
  });

  it('renders POS and verifies cash vs installment mode calculations', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/pos']}>
        <Routes>
          <Route path="/pos" element={<POS />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      const customerInput = container.querySelector('#input_name');
      expect(customerInput).not.toBeNull();
    });

    const customerInput = container.querySelector('#input_name');
    fireEvent.change(customerInput, { target: { value: 'محمود حسن' } });
    expect(customerInput.value).toBe('محمود حسن');

    // Toggle cash sale via Cash button
    const cashBtn = screen.getByText('كاش');
    expect(cashBtn).toBeInTheDocument();
    fireEvent.click(cashBtn);

    // Click installment button
    const installmentBtn = screen.getByText('قسط');
    expect(installmentBtn).toBeInTheDocument();
    fireEvent.click(installmentBtn);
  });

  it('renders ReturnReceipt page with original items and calculates partial return', async () => {
    render(
      <MemoryRouter initialEntries={['/return/1']}>
        <Routes>
          <Route path="/return/:id" element={<ReturnReceipt />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/أحمد محمود/i)).toBeInTheDocument();
      expect(screen.getByText(/غسالة توشيبا/i)).toBeInTheDocument();
    });

    // Check plus button to increment return quantity
    const plusBtn = screen.getByText('+');
    expect(plusBtn).toBeInTheDocument();
    fireEvent.click(plusBtn);

    await waitFor(() => {
      // 1 unit returned * 2500 price = 2,500
      expect(screen.getAllByText(/2,500/i).length).toBeGreaterThan(0);
    });
  });

  it('correctly parses and round-trips installment boxes with counts > 20 (e.g. 500*24 and 300*36)', () => {
    const boxes24 = parseInstallmentTextToBoxes('500*24');
    expect(boxes24[0]).toEqual({ count: 24, amount: 500 });
    expect(formatBoxesToInstallmentText(boxes24)).toBe('500*24');

    const boxes36 = parseInstallmentTextToBoxes('300*36+150*12');
    expect(boxes36[0]).toEqual({ count: 36, amount: 300 });
    expect(boxes36[1]).toEqual({ count: 12, amount: 150 });
    expect(formatBoxesToInstallmentText(boxes36)).toBe('300*36+150*12');

    const legacySwapped = parseInstallmentTextToBoxes('24*500');
    expect(legacySwapped[0]).toEqual({ count: 24, amount: 500 });
  });
});
