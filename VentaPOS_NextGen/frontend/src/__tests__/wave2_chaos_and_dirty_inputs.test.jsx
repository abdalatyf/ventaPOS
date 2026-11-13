import React from 'react';
import { render, screen, fireEvent, waitFor, act, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import {
  normalizeArabicDigits,
  parseStrictInt,
  parseWholeMoney,
  parseValidMonthYear,
} from '../utils/formatUtils';
import { setActiveBranch, useActiveBranch } from '../hooks/useActiveBranch';
import Navbar from '../components/Navbar';
import BranchSelection from '../pages/BranchSelection';
import POS from '../pages/POS';
import PurchaseEntry from '../pages/PurchaseEntry';
import ReturnReceipt from '../pages/ReturnReceipt';
import Expenses from '../pages/Expenses';
import ProductLedger from '../pages/ProductLedger';
import SearchReceipts from '../pages/SearchReceipts';
import SearchPurchases from '../pages/SearchPurchases';
import InventoryTab from '../components/InventoryTab';
import SalespersonsTab from '../components/SalespersonsTab';
import SuppliersTab from '../components/SuppliersTab';
import Login from '../pages/Login';

vi.mock('react-hot-toast', () => {
  const fn = vi.fn();
  fn.success = vi.fn();
  fn.error = vi.fn();
  return { default: fn };
});

vi.mock('sweetalert2', () => ({
  default: {
    fire: vi.fn(() => Promise.resolve({ isConfirmed: true })),
  },
}));

vi.mock('../utils/dialogUtils', () => ({
  confirmDialog: vi.fn(() => Promise.resolve(true)),
  confirmAction: vi.fn(() => Promise.resolve(true)),
  alertDialog: vi.fn(() => Promise.resolve({ isConfirmed: true })),
  showAlert: vi.fn(() => Promise.resolve({ isConfirmed: true })),
  default: {
    confirmDialog: vi.fn(() => Promise.resolve(true)),
    confirmAction: vi.fn(() => Promise.resolve(true)),
    alertDialog: vi.fn(() => Promise.resolve({ isConfirmed: true })),
    showAlert: vi.fn(() => Promise.resolve({ isConfirmed: true })),
  },
}));

vi.mock('../components/common/QuickRestoreModal', () => ({
  default: () => null,
}));

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

const clearLicenseCacheMock = vi.hoisted(() => vi.fn());
const getLicenseStatusMock = vi.hoisted(() =>
  vi.fn(() =>
    Promise.resolve({
      status: 'active',
      is_demo: false,
      is_print_only: false,
      is_expired: false,
      start_date: '2026-01-01',
      total_invoices_balance: 5000,
    })
  )
);

vi.mock('../api', () => ({
  default: apiMock,
  clearLicenseCache: clearLicenseCacheMock,
  getLicenseStatus: getLicenseStatusMock,
}));

function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function defaultGetRouter(url) {
  const branchId = String(localStorage.getItem('branchId') || '1');
  if (url.includes('/branches/')) {
    return Promise.resolve({
      data: [
        { id: 1, name: 'الفرع الرئيسي' },
        { id: 2, name: 'فرع الجيزة' },
      ],
    });
  }
  if (url.includes('/company-settings/')) {
    return Promise.resolve({
      data: { name: 'مؤسسة الاختبار', collection_commission_rate: 0.1 },
    });
  }
  if (url.includes('/license/status/')) {
    return Promise.resolve({
      data: {
        status: 'active',
        is_demo: false,
        is_print_only: false,
        is_expired: false,
        start_date: '2026-01-01',
        total_invoices_balance: 5000,
      },
    });
  }
  if (url.includes('/default-date/')) {
    return Promise.resolve({ data: { month: 8, year: 2026 } });
  }
  if (url.includes('/receipts/next-number/')) {
    return Promise.resolve({
      data: { next_number: branchId === '2' ? 2001 : 1001 },
    });
  }
  if (url.includes('/product-suggestions/')) {
    if (branchId === '2') {
      return Promise.resolve({
        data: [{ id: 201, value: 'غسالة فرع 2', label: 'غسالة فرع 2', safe_qty: 5 }],
      });
    }
    return Promise.resolve({
      data: [{ id: 101, value: 'ثلاجة فرع 1', label: 'ثلاجة فرع 1', safe_qty: 10 }],
    });
  }
  if (url.includes('/salespersons/')) {
    if (branchId === '2') {
      return Promise.resolve({ data: [{ id: 20, name: 'مندوب فرع 2', branch: 2 }] });
    }
    return Promise.resolve({ data: [{ id: 10, name: 'مندوب فرع 1', branch: 1 }] });
  }
  if (url.includes('/suppliers/')) {
    if (branchId === '2') {
      return Promise.resolve({ data: [{ id: 200, name: 'مورد فرع 2', branch: 2 }] });
    }
    return Promise.resolve({ data: [{ id: 100, name: 'مورد فرع 1', branch: 1 }] });
  }
  if (url.includes('/ledger/')) {
    return Promise.resolve({
      data: {
        item: {
          id: 101,
          branch: 1,
          name: 'ثلاجة فرع 1',
          current_stock: 10,
          initial_quantity: 10,
          initial_commission_amount: 100,
        },
        timeline: [],
        metrics: { purchases: 0, sales: 0, returns: 0, deficit: 0 },
      },
    });
  }
  if (url.includes('/stock/') || url.includes('/inventory/safe_available_qty/')) {
    return Promise.resolve({
      data: { safe_available_qty: 10, available_qty: 10, bottleneck_month: 8, bottleneck_year: 2026 },
    });
  }
  if (url.includes('/inventory/') || url.includes('/inventory-items/')) {
    if (branchId === '2') {
      return Promise.resolve({
        data: [
          {
            id: 201,
            name: 'غسالة فرع 2',
            branch: 2,
            stock: 5,
            current_stock: 5,
            initial_quantity: 5,
            initial_purchase_price: 4000,
            initial_commission_amount: 80,
          },
        ],
      });
    }
    return Promise.resolve({
      data: [
        {
          id: 101,
          name: 'ثلاجة فرع 1',
          branch: 1,
          stock: 10,
          current_stock: 10,
          initial_quantity: 10,
          initial_purchase_price: 5000,
          initial_commission_amount: 100,
        },
      ],
    });
  }
  if (url.includes('/receipts/55/')) {
    return Promise.resolve({
      data: {
        id: 55,
        receipt_number: 1055,
        branch: 1,
        sale_month: 11,
        sale_year: 2026,
        customer_name: 'عميل قديم',
        phone_number: '01000000001',
        area: 'مدينة نصر',
        address: 'شارع عباس',
        salesperson: 10,
        is_cash_sale: false,
        down_payment: 0,
        total_amount: 3000,
        installment_payments: [],
        sale_items: [
          {
            id: 1,
            inventory_item: 101,
            inventory_item_name: 'ثلاجة فرع 1',
            quantity: 2,
            unit_price: 1500,
          },
        ],
      },
    });
  }
  if (url.includes('/receipts/')) {
    return Promise.resolve({
      data: {
        count: 1,
        all_ids: [branchId === '2' ? 202 : 102],
        total_amount_sum: branchId === '2' ? 2000 : 1000,
        results: [
          {
            id: branchId === '2' ? 202 : 102,
            receipt_number: branchId === '2' ? 2002 : 1002,
            branch: Number(branchId),
            sale_month: 8,
            sale_year: 2026,
            customer_name: branchId === '2' ? 'عميل فرع 2' : 'عميل فرع 1',
            phone_number: '01000000000',
            area: 'الدقي',
            address: 'شارع النيل',
            salesperson: branchId === '2' ? 20 : 10,
            salesperson_name: branchId === '2' ? 'مندوب فرع 2' : 'مندوب فرع 1',
            is_cash_sale: true,
            down_payment: 0,
            total_amount: branchId === '2' ? 2000 : 1000,
            receipt_type: 'SALE',
            products_text: branchId === '2' ? 'غسالة فرع 2 × 1' : 'ثلاجة فرع 1 × 1',
            items: [],
          },
        ],
      },
    });
  }
  if (url.includes('/purchase-invoices/10/')) {
    return Promise.resolve({
      data: {
        id: 10,
        invoice_number: 'PUR-10',
        branch: 1,
        supplier: 100,
        invoice_month: 8,
        invoice_year: 2026,
        is_return: false,
        total_amount: 5000,
        items: [
          {
            inventory_item: 101,
            inventory_item_name: 'ثلاجة فرع 1',
            quantity: 1,
            unit_cost: 5000,
          },
        ],
      },
    });
  }
  if (url.includes('/purchase-invoices/')) {
    return Promise.resolve({
      data: {
        count: 1,
        results: [
          {
            id: branchId === '2' ? 210 : 110,
            invoice_number: branchId === '2' ? 'PUR-B2' : 'PUR-B1',
            branch: Number(branchId),
            supplier: branchId === '2' ? 200 : 100,
            supplier_name: branchId === '2' ? 'مورد فرع 2' : 'مورد فرع 1',
            invoice_month: 8,
            invoice_year: 2026,
            total_amount: branchId === '2' ? 4000 : 5000,
            is_return: false,
            items: [],
          },
        ],
      },
    });
  }
  if (url.includes('/expenses/categories/')) {
    return Promise.resolve({ data: [{ id: 1, name: 'إيجار' }] });
  }
  if (url.includes('/expenses/')) {
    return Promise.resolve({
      data: {
        count: 1,
        total_amount: branchId === '2' ? 800 : 500,
        results: [
          {
            id: branchId === '2' ? 2 : 1,
            branch: Number(branchId),
            description: branchId === '2' ? 'مصروف فرع 2' : 'مصروف فرع 1',
            category: 'إيجار',
            amount: branchId === '2' ? 800 : 500,
            expense_month: 8,
            expense_year: 2026,
          },
        ],
      },
    });
  }
  if (url.includes('/customers/search/') || url.includes('/areas/search/')) {
    return Promise.resolve({ data: [] });
  }
  return Promise.resolve({ data: {} });
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem('token', 'test-token');
  localStorage.setItem('branchId', '1');
  localStorage.setItem('branchName', 'الفرع الرئيسي');
  vi.clearAllMocks();
  apiMock.get.mockImplementation(defaultGetRouter);
  apiMock.post.mockImplementation(() => Promise.resolve({ data: { id: 999 } }));
  apiMock.patch.mockImplementation(() => Promise.resolve({ data: { id: 1 } }));
  apiMock.put.mockImplementation(() => Promise.resolve({ data: { id: 1 } }));
  apiMock.delete.mockImplementation(() => Promise.resolve({ data: {} }));
});

describe('Wave 2 Chaos QA — Utilities & Reactive Branch Sync', () => {
  it('validates Arabic-Indic normalization and strict parsing helpers', () => {
    expect(normalizeArabicDigits('١٢٬٣٤٥')).toBe('12345');
    expect(normalizeArabicDigits('٠')).toBe('0');

    expect(parseStrictInt('٤٢')).toBe(42);
    expect(parseStrictInt('12abc')).toBeNull();
    expect(parseStrictInt('12.5')).toBeNull();
    expect(parseStrictInt('0', { min: 1 })).toBeNull();
    expect(parseStrictInt('')).toBeNull();

    expect(parseWholeMoney('٥٬٠٠٠')).toBe(5000);
    expect(parseWholeMoney('0', { min: 0 })).toBe(0);
    expect(parseWholeMoney('-10', { min: 0 })).toBeNull();
    expect(parseWholeMoney('99.5')).toBe(100);
    expect(parseWholeMoney('abc')).toBeNull();

    expect(parseValidMonthYear('٨', '٢٠٢٦')).toEqual({ month: 8, year: 2026 });
    expect(parseValidMonthYear('13', '2026')).toBeNull();
    expect(parseValidMonthYear('0', '2026')).toBeNull();
    expect(parseValidMonthYear('5', '2024', { minYear: 2025 })).toBeNull();
  });

  it('syncs active branch reactively via branch_changed and storage events', () => {
    function BranchProbe() {
      const { branchId, branchName } = useActiveBranch();
      return (
        <div>
          <span data-testid="probe-id">{String(branchId || '')}</span>
          <span data-testid="probe-name">{branchName}</span>
        </div>
      );
    }

    render(<BranchProbe />);
    expect(screen.getByTestId('probe-id')).toHaveTextContent('1');
    expect(screen.getByTestId('probe-name')).toHaveTextContent('الفرع الرئيسي');

    act(() => {
      setActiveBranch(2, 'فرع الجيزة');
    });
    expect(screen.getByTestId('probe-id')).toHaveTextContent('2');
    expect(screen.getByTestId('probe-name')).toHaveTextContent('فرع الجيزة');

    act(() => {
      localStorage.setItem('branchId', '3');
      localStorage.setItem('branchName', 'فرع أكتوبر');
      window.dispatchEvent(new StorageEvent('storage', { key: 'branchId', newValue: '3' }));
    });
    expect(screen.getByTestId('probe-id')).toHaveTextContent('3');
    expect(screen.getByTestId('probe-name')).toHaveTextContent('فرع أكتوبر');
  });
});

describe('Wave 2 Chaos QA — BranchSelection & Navbar Quick Switch', () => {
  it('enforces single branch submission on rapid double-click and blocks whitespace-only branch name', async () => {
    const postDef = deferred();
    apiMock.post.mockReturnValueOnce(postDef.promise);

    render(
      <MemoryRouter>
        <BranchSelection />
      </MemoryRouter>
    );

    await screen.findByText('الفرع الرئيسي');
    fireEvent.click(screen.getByText('إضافة فرع جديد'));

    const input = await waitFor(() => document.querySelector('.modal input[type="text"]'));
    expect(input).toBeInTheDocument();
    const form = input.closest('form');

    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.submit(form);
    expect(apiMock.post).not.toHaveBeenCalled();

    fireEvent.change(input, { target: { value: 'فرع المعادي' } });
    fireEvent.submit(form);
    fireEvent.submit(form);

    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post).toHaveBeenCalledWith('/branches/', { name: 'فرع المعادي' });

    await act(async () => {
      postDef.resolve({ data: { id: 3, name: 'فرع المعادي' } });
    });
  });

  it('allows quick-switching branch from Navbar dropdown and emits branch_changed', async () => {
    const listener = vi.fn();
    window.addEventListener('branch_changed', listener);

    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('فرع الجيزة')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('فرع الجيزة'));
    });

    expect(localStorage.getItem('branchId')).toBe('2');
    expect(localStorage.getItem('branchName')).toBe('فرع الجيزة');
    expect(listener).toHaveBeenCalled();
    window.removeEventListener('branch_changed', listener);
  });
});

describe('Wave 2 Chaos QA — POS, PurchaseEntry & ReturnReceipt Locks and Isolation', () => {
  it('prevents duplicate POST /receipts/ on rapid double-click and blocks dirty month/down-payment', async () => {
    const postDef = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url === '/receipts/') return postDef.promise;
      return Promise.resolve({ data: {} });
    });

    const { container } = render(
      <MemoryRouter initialEntries={['/pos']}>
        <Routes>
          <Route path="/pos" element={<POS />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('مندوب فرع 1')).toBeInTheDocument();
    });

    // Select salesperson from SuggestionList (onMouseDown)
    fireEvent.focus(screen.getByPlaceholderText('ابحث عن مندوب...'));
    fireEvent.mouseDown(screen.getByText('مندوب فرع 1'));

    // Customer name
    fireEvent.change(container.querySelector('#input_name'), {
      target: { value: 'عميل اختبار' },
    });

    // Trigger product suggestions and select via onMouseDown
    const autoInputs = container.querySelectorAll('input[autocomplete="off"]');
    const productInput = autoInputs[2];
    fireEvent.focus(productInput);
    fireEvent.change(productInput, { target: { value: 'ثلاجة فرع 1' } });
    const suggestionItem = await screen.findByText('ثلاجة فرع 1');
    fireEvent.mouseDown(suggestionItem);

    const numInputs = container.querySelectorAll('input[inputmode="numeric"]');
    const monthInput = numInputs[0];
    const qtyInput = numInputs[2];
    const priceInput = numInputs[3];

    fireEvent.change(qtyInput, { target: { value: '١' } });
    fireEvent.change(priceInput, { target: { value: '١٥٠٠' } });

    fireEvent.click(screen.getByRole('button', { name: '+' }));

    const table = container.querySelector('table');
    await waitFor(() => {
      expect(within(table).getByText('ثلاجة فرع 1')).toBeInTheDocument();
    });

    // Switch to cash sale
    fireEvent.click(screen.getByRole('button', { name: 'كاش' }));

    // Dirty month = 13 must block save
    fireEvent.change(monthInput, { target: { value: '13' } });
    const confirmBtn = screen.getByRole('button', { name: /تأكيد البيع/ });
    fireEvent.click(confirmBtn);
    expect(apiMock.post).not.toHaveBeenCalled();

    // Fix month with Arabic-Indic '٨', rapid double-click confirm while pending
    fireEvent.change(monthInput, { target: { value: '٨' } });
    fireEvent.click(confirmBtn);
    fireEvent.click(confirmBtn);

    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][0]).toBe('/receipts/');
    expect(apiMock.post.mock.calls[0][1].branch).toBe(1);
    expect(apiMock.post.mock.calls[0][1].sale_month).toBe(8);
    expect(apiMock.post.mock.calls[0][1].total_amount).toBe(1500);

    await act(async () => {
      postDef.resolve({ data: { id: 500, receipt_number: 1001 } });
    });
  });

  it('wipes POS form and exits edit mode on mid-form branch switch', async () => {
    render(
      <MemoryRouter initialEntries={['/pos?edit=55']}>
        <Routes>
          <Route path="/pos" element={<POS />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('عميل قديم')).toBeInTheDocument();
    });

    await act(async () => {
      setActiveBranch(2, 'فرع الجيزة');
    });

    await waitFor(() => {
      expect(screen.queryByDisplayValue('عميل قديم')).not.toBeInTheDocument();
      expect(screen.getByText('مندوب فرع 2')).toBeInTheDocument();
      expect(screen.queryByText('مندوب فرع 1')).not.toBeInTheDocument();
    });
  });

  it('locks PurchaseEntry double-submit, validates bad year/month, and resets on branch switch', async () => {
    const postDef = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url === '/purchase-invoices/') return postDef.promise;
      return Promise.resolve({ data: {} });
    });

    const { container } = render(
      <MemoryRouter initialEntries={['/purchases/edit/10']}>
        <Routes>
          <Route path="/purchases/new" element={<PurchaseEntry />} />
          <Route path="/purchases/edit/:id" element={<PurchaseEntry />} />
          <Route path="/search-purchases" element={<div>SEARCH_PURCHASES_PAGE</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('مورد فرع 1')).toBeInTheDocument();
    });

    // Switch branch mid-edit -> resets & navigates off edit route, loading Branch 2 supplier
    await act(async () => {
      setActiveBranch(2, 'فرع الجيزة');
    });

    await waitFor(() => {
      expect(screen.queryByDisplayValue('مورد فرع 1')).not.toBeInTheDocument();
      expect(screen.getByText('مورد فرع 2')).toBeInTheDocument();
    });

    // Select supplier, select product via SuggestionList onMouseDown, add item
    fireEvent.focus(screen.getByPlaceholderText('ابحث عن مورد...'));
    fireEvent.mouseDown(screen.getByText('مورد فرع 2'));

    const prodInput = screen.getByPlaceholderText('ابحث عن صنف...');
    fireEvent.focus(prodInput);
    fireEvent.change(prodInput, { target: { value: 'غسالة فرع 2' } });
    fireEvent.mouseDown(await screen.findByText('غسالة فرع 2'));

    const ltrInputs = container.querySelectorAll('input[dir="ltr"]');
    const yearInput = ltrInputs[1];
    const itemQtyInput = ltrInputs[ltrInputs.length - 2];
    const itemCostInput = ltrInputs[ltrInputs.length - 1];

    fireEvent.change(itemQtyInput, { target: { value: '٢' } });
    fireEvent.change(itemCostInput, { target: { value: '٣٠٠٠' } });
    fireEvent.click(screen.getByRole('button', { name: /إضافة/ }));

    const table = container.querySelector('table');
    await waitFor(() => {
      expect(within(table).getByText('غسالة فرع 2')).toBeInTheDocument();
    });

    fireEvent.change(yearInput, { target: { value: '2024' } });

    const saveBtn = screen.getByRole('button', { name: /حفظ الفاتورة/ });
    fireEvent.click(saveBtn);
    expect(apiMock.post).not.toHaveBeenCalled();

    fireEvent.change(yearInput, { target: { value: '٢٠٢٦' } });
    fireEvent.click(saveBtn);
    fireEvent.click(saveBtn);

    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][0]).toBe('/purchase-invoices/');
    expect(apiMock.post.mock.calls[0][1].branch).toBe(2);
    expect(apiMock.post.mock.calls[0][1].invoice_year).toBe(2026);

    await act(async () => {
      postDef.resolve({ data: { id: 99 } });
    });
  });

  it('fixes ReturnReceipt month "12" rollover, locks double-submit, and calculates next-year installment', async () => {
    const postDef = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url.includes('/return_receipt/')) return postDef.promise;
      return Promise.resolve({ data: {} });
    });

    const { container } = render(
      <MemoryRouter initialEntries={['/receipts/return/55']}>
        <Routes>
          <Route path="/receipts/return/:id" element={<ReturnReceipt />} />
          <Route path="/receipts" element={<div>SEARCH_RECEIPTS_PAGE</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/عميل قديم/)).toBeInTheDocument();
    });

    // Return 1 unit (+ button) -> totalReturnValue = 1500, newDebt = 1500
    fireEvent.click(screen.getByRole('button', { name: '+' }));

    const numInputs = container.querySelectorAll('input[inputmode="numeric"]');
    const monthBox = numInputs[0];
    fireEvent.change(monthBox, { target: { value: '12' } });

    // Enter new installment schedule: 1500 x 1 month -> must roll over from 12/2026 to 1/2027
    const instAmtInput = screen.getByPlaceholderText('قسط 1');
    const instCntInput = screen.getAllByPlaceholderText('عدد الشهور')[0];
    fireEvent.change(instAmtInput, { target: { value: '1500' } });
    fireEvent.change(instCntInput, { target: { value: '1' } });

    const confirmBtn = screen.getByRole('button', { name: /تأكيد المرتجع/ });
    fireEvent.click(confirmBtn);
    fireEvent.click(confirmBtn);

    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][0]).toBe('/receipts/55/return_receipt/');
    const payload = apiMock.post.mock.calls[0][1];
    expect(payload.return_month).toBe(12);
    expect(payload.return_year).toBe(2026);
    expect(payload.new_installments).toEqual([
      { payment_month: 1, payment_year: 2027, amount: 1500 },
    ]);

    await act(async () => {
      postDef.resolve({ data: { id: 56 } });
    });
  });
});

describe('Wave 2 Chaos QA — Expenses, ProductLedger, Search & Dimensions', () => {
  it('blocks dirty Expense inputs, locks double-submit, and drops stale branch responses', async () => {
    const b1Slow = deferred();
    let b1Requested = false;

    apiMock.get.mockImplementation((url) => {
      if (url.includes('/expenses/') && !url.includes('categories')) {
        if (String(localStorage.getItem('branchId') || '1') === '1') {
          b1Requested = true;
          return b1Slow.promise;
        }
        return Promise.resolve({
          data: {
            count: 1,
            total_amount: 800,
            results: [
              {
                id: 2,
                branch: 2,
                description: 'مصروف فرع 2 النهائي',
                category: 'إيجار',
                amount: 800,
                expense_month: 8,
                expense_year: 2026,
              },
            ],
          },
        });
      }
      return defaultGetRouter(url);
    });

    const postDef = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url === '/expenses/') return postDef.promise;
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter>
        <Expenses />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(b1Requested).toBe(true);
    });

    // Switch to Branch 2 while Branch 1 fetch is still pending
    await act(async () => {
      setActiveBranch(2, 'فرع الجيزة');
    });

    await waitFor(() => {
      expect(screen.getByText('مصروف فرع 2 النهائي')).toBeInTheDocument();
    });

    // Resolve stale Branch 1 response late — must NOT overwrite Branch 2 table
    await act(async () => {
      b1Slow.resolve({
        data: {
          count: 1,
          total_amount: 999,
          results: [
            {
              id: 1,
              branch: 1,
              description: 'مصروف فرع 1 المتأخر',
              category: 'إيجار',
              amount: 999,
              expense_month: 8,
              expense_year: 2026,
            },
          ],
        },
      });
    });
    expect(screen.queryByText('مصروف فرع 1 المتأخر')).not.toBeInTheDocument();
    expect(screen.getByText('مصروف فرع 2 النهائي')).toBeInTheDocument();

    // Whitespace description rejected
    const descInput = screen.getByPlaceholderText('البيان (اسم المصروف) *');
    const amountInput = screen.getByPlaceholderText('المبلغ *');
    fireEvent.change(descInput, { target: { value: '   ' } });
    fireEvent.change(amountInput, { target: { value: '250' } });
    fireEvent.submit(descInput.closest('form'));
    expect(apiMock.post).not.toHaveBeenCalled();

    // Zero amount rejected
    fireEvent.change(descInput, { target: { value: 'كهرباء فرع 2' } });
    fireEvent.change(amountInput, { target: { value: '0' } });
    fireEvent.submit(descInput.closest('form'));
    expect(apiMock.post).not.toHaveBeenCalled();

    // Valid Arabic-Indic amount + rapid double-submit
    fireEvent.change(amountInput, { target: { value: '٥٠٠' } });
    fireEvent.submit(descInput.closest('form'));
    fireEvent.submit(descInput.closest('form'));

    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][0]).toBe('/expenses/');
    expect(apiMock.post.mock.calls[0][1]).toMatchObject({
      description: 'كهرباء فرع 2',
      amount: 500,
      expense_month: 8,
      expense_year: 2026,
    });

    await act(async () => {
      postDef.resolve({ data: { id: 88 } });
    });
  });

  it('allows 0 commission in ProductLedger, blocks dirty deficit/dates, and redirects on branch switch', async () => {
    const defPost = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url === '/inventory-adjustments/') return defPost.promise;
      return Promise.resolve({ data: { id: 1 } });
    });

    render(
      <MemoryRouter initialEntries={['/product-ledger/101']}>
        <Routes>
          <Route path="/product-ledger/:id" element={<ProductLedger />} />
          <Route path="/product-ledger" element={<div>LEDGER_INDEX</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /تعديل المندبة/ })).toBeInTheDocument();
    });

    // Open commission modal & verify 0 is allowed
    fireEvent.click(screen.getByRole('button', { name: /تعديل المندبة/ }));
    const commAmount = screen.getByPlaceholderText('مثال: 50');
    fireEvent.change(commAmount, { target: { value: '٠' } });
    fireEvent.submit(commAmount.closest('form'));

    await waitFor(() => {
      expect(apiMock.post).toHaveBeenCalledWith(
        '/commission-histories/',
        expect.objectContaining({ item: '101', commission_amount: 0, activation_month: 8, activation_year: 2026 })
      );
    });

    // Open deficit form, reject 0 qty, lock double-click on valid qty
    apiMock.post.mockClear();
    fireEvent.click(screen.getByRole('button', { name: /تسجيل عجز/ }));
    const defQty = screen.getByPlaceholderText('مثال: 2');
    fireEvent.change(defQty, { target: { value: '0' } });
    fireEvent.submit(defQty.closest('form'));
    expect(apiMock.post).not.toHaveBeenCalled();

    fireEvent.change(defQty, { target: { value: '٢' } });
    fireEvent.submit(defQty.closest('form'));
    fireEvent.submit(defQty.closest('form'));
    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][1]).toMatchObject({ item: '101', quantity: 2 });

    await act(async () => {
      defPost.resolve({ data: { id: 12 } });
    });

    // Switching branch redirects off branch 1 product ledger
    await act(async () => {
      setActiveBranch(2, 'فرع الجيزة');
    });
    await waitFor(() => {
      expect(screen.getByText('LEDGER_INDEX')).toBeInTheDocument();
    });
  });

  it('clears SearchReceipts and SearchPurchases state on branch switch and locks bulk delete', async () => {
    const bulkDef = deferred();
    apiMock.post.mockImplementation((url) => {
      if (url.includes('/receipts/bulk_delete/')) return bulkDef.promise;
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter>
        <SearchReceipts />
        <SearchPurchases />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('عميل فرع 1')).toBeInTheDocument();
      expect(screen.getByText('PUR-B1')).toBeInTheDocument();
    });

    // Initial load selects all_ids automatically — locate SearchReceipts 'حذف محددة' button & double-click
    const bulkBtns = await screen.findAllByRole('button', { name: /حذف محددة/ });
    fireEvent.click(bulkBtns[0]);
    fireEvent.click(bulkBtns[0]);

    await waitFor(() => {
      expect(apiMock.post).toHaveBeenCalledTimes(1);
      expect(apiMock.post.mock.calls[0][0]).toContain('/receipts/bulk_delete/');
    });

    await act(async () => {
      bulkDef.resolve({ data: { deleted_count: 1 } });
    });

    // Switch branch -> both SearchReceipts and SearchPurchases switch cleanly to Branch 2 records
    await act(async () => {
      setActiveBranch(2, 'فرع الجيزة');
    });

    await waitFor(() => {
      expect(screen.getByText('عميل فرع 2')).toBeInTheDocument();
      expect(screen.getByText('PUR-B2')).toBeInTheDocument();
      expect(screen.queryByText('عميل فرع 1')).not.toBeInTheDocument();
      expect(screen.queryByText('PUR-B1')).not.toBeInTheDocument();
    });
  });

  it('enforces validation and rapid double-submit locks across InventoryTab, SalespersonsTab, and SuppliersTab', async () => {
    const postDef = deferred();
    apiMock.post.mockReturnValue(postDef.promise);

    const { container } = render(
      <MemoryRouter>
        <InventoryTab />
        <SalespersonsTab />
        <SuppliersTab />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ثلاجة فرع 1')).toBeInTheDocument();
      expect(screen.getByText('مندوب فرع 1')).toBeInTheDocument();
      expect(screen.getByText('مورد فرع 1')).toBeInTheDocument();
    });

    // InventoryTab inline form: bad year 2024 rejected, then valid Arabic-Indic double submit locked
    const invName = container.querySelector('input[name="name"]');
    const invQty = container.querySelector('input[name="qty"]');
    const invYear = container.querySelector('input[name="startYear"]');
    const invForm = invName.closest('form');

    fireEvent.change(invName, { target: { value: 'مروحة جديدة' } });
    fireEvent.change(invQty, { target: { value: '٣' } });
    fireEvent.change(invYear, { target: { value: '2024' } });
    fireEvent.submit(invForm);
    expect(apiMock.post).not.toHaveBeenCalled();

    fireEvent.change(invYear, { target: { value: '2026' } });
    fireEvent.submit(invForm);
    fireEvent.submit(invForm);
    expect(apiMock.post).toHaveBeenCalledTimes(1);
    expect(apiMock.post.mock.calls[0][0]).toBe('/inventory-items/');
    expect(apiMock.post.mock.calls[0][1]).toMatchObject({
      branch: 1,
      name: 'مروحة جديدة',
      initial_quantity: 3,
    });

    await act(async () => {
      postDef.resolve({ data: { id: 102, name: 'مروحة جديدة' } });
    });

    // SalespersonsTab: whitespace-only rejected
    apiMock.post.mockClear();
    const spInput = screen.getByPlaceholderText('اسم المندوب الجديد... *');
    fireEvent.change(spInput, { target: { value: '   ' } });
    fireEvent.submit(spInput.closest('form'));
    expect(apiMock.post).not.toHaveBeenCalled();

    // SuppliersTab: whitespace-only rejected
    const supInput = screen.getByPlaceholderText('اسم المورد / المصنع الجديد... *');
    fireEvent.change(supInput, { target: { value: '   ' } });
    fireEvent.submit(supInput.closest('form'));
    expect(apiMock.post).not.toHaveBeenCalled();
  });

  it('prevents POS focus stealing after initial load and prevents /login 401 infinite reload loops', async () => {
    const { container } = render(
      <MemoryRouter>
        <POS />
      </MemoryRouter>
    );

    const custInput = await waitFor(() => {
      const el = container.querySelector('#input_name');
      expect(el).toBeInTheDocument();
      return el;
    });
    custInput.focus();
    expect(document.activeElement).toBe(custInput);

    // Wait longer than usePOSDataLoader's 150ms auto-focus timer -> focus must remain on customer input
    await act(async () => {
      await new Promise((r) => setTimeout(r, 220));
    });
    expect(document.activeElement).toBe(custInput);

    // Login mounted unauthenticated must NOT call protected /company-settings/
    localStorage.clear();
    apiMock.get.mockClear();
    apiMock.post.mockImplementationOnce(() => Promise.reject({ response: { status: 403 } }));
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/license/status/')) {
        return Promise.resolve({ data: { status: 'active', is_demo: false, has_password: true } });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Login />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('أدخل كلمة سر النظام')).toBeInTheDocument();
    });
    const companyCalls = apiMock.get.mock.calls.filter(([u]) => String(u).includes('/company-settings/'));
    expect(companyCalls).toHaveLength(0);

    // Verify real api.js 401 interceptor ignores 401 on /login or /auth/local/, but redirects on protected pages
    const { default: realApi } = await vi.importActual('../api');
    const respHandlers = realApi.interceptors.response.handlers || [];
    const errorHandler = respHandlers.find((h) => typeof h?.rejected === 'function')?.rejected;
    expect(typeof errorHandler).toBe('function');

    const origLocation = window.location;
    let assignedHref = '';
    const fakeLocation = {
      pathname: '/login',
      get href() { return assignedHref || 'http://localhost/login'; },
      set href(v) { assignedHref = v; },
    };
    Object.defineProperty(window, 'location', { configurable: true, value: fakeLocation });

    try {
      localStorage.setItem('token', 'valid-token');
      await expect(
        errorHandler({ response: { status: 401 }, config: { url: '/company-settings/' } })
      ).rejects.toBeDefined();
      expect(assignedHref).toBe('');
      expect(localStorage.getItem('token')).toBe('valid-token');

      fakeLocation.pathname = '/receipts';
      await expect(
        errorHandler({ response: { status: 401 }, config: { url: '/auth/local/' } })
      ).rejects.toBeDefined();
      expect(assignedHref).toBe('');

      await expect(
        errorHandler({ response: { status: 401 }, config: { url: '/receipts/' } })
      ).rejects.toBeDefined();
      expect(assignedHref).toBe('/login');
      expect(localStorage.getItem('token')).toBeNull();
    } finally {
      Object.defineProperty(window, 'location', { configurable: true, value: origLocation });
    }
  });
});
