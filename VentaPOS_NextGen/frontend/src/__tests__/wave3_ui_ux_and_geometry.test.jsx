import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import Swal from 'sweetalert2';

import SuggestionList from '../components/purchases/SuggestionList';
import ReportTable from '../components/ReportTable';
import SearchReceipts from '../pages/SearchReceipts';
import PurchasesReport from '../pages/reports/PurchasesReport';
import ReportsLayout, { ReportsContext } from '../pages/reports/ReportsLayout';
import Expenses from '../pages/Expenses';
import LedgerDeficitForm from '../components/ledger/LedgerDeficitForm';
import LedgerCommissionForm from '../components/ledger/LedgerCommissionForm';
import POS from '../pages/POS';
import AppAutocomplete from '../components/common/AppAutocomplete';
import QuickRestoreModal from '../components/common/QuickRestoreModal';
import CompanyTab from '../pages/settings/tabs/CompanyTab';
import InstallmentsReport from '../pages/reports/InstallmentsReport';
import PrintModal from '../components/common/PrintModal';
import StandardTablePageLayout from '../components/common/StandardTablePageLayout';
import { Routes, Route } from 'react-router-dom';

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

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

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
  clearLicenseCache: vi.fn(),
  getLicenseStatus: getLicenseStatusMock,
}));

function installDomPolyfills() {
  if (!window.ResizeObserver) {
    window.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
  if (!window.IntersectionObserver) {
    window.IntersectionObserver = class IntersectionObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = vi.fn();
  }
  if (!window.scrollTo) {
    window.scrollTo = vi.fn();
  }
}

describe('Wave 3 UI/UX & Interaction Regressions', () => {
  beforeEach(() => {
    installDomPolyfills();
    localStorage.clear();
    localStorage.setItem('branchId', '1');
    localStorage.setItem('branchName', 'الفرع الرئيسي');
    vi.clearAllMocks();

    apiMock.post.mockResolvedValue({ data: { id: 999 } });
    apiMock.patch.mockResolvedValue({ data: { id: 1 } });
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/printers/')) {
        return Promise.resolve({ data: [{ name: 'DefaultPrinter', status: 'ready', is_default: true }] });
      }
      if (url.includes('/default-date/')) {
        return Promise.resolve({ data: { month: 8, year: 2026 } });
      }
      if (url.includes('/salespersons/')) {
        return Promise.resolve({ data: [{ id: 10, name: 'مندوب اختبار' }] });
      }
      if (url.includes('/suppliers/')) {
        return Promise.resolve({
          data: [
            { id: 101, name: 'مورد الأمل' },
            { id: 102, name: 'مورد السلام' },
          ],
        });
      }
      if (url.includes('/inventory-items/')) {
        return Promise.resolve({
          data: [
            { id: 201, name: 'ثلاجة ٣٠٠ لتر', safe_qty: 8, bottleneck_month: 8, bottleneck_year: 2026 },
          ],
        });
      }
      if (url.includes('/receipts/next-number/')) {
        return Promise.resolve({ data: { next_number: 505 } });
      }
      if (url.includes('/expenses/')) {
        return Promise.resolve({
          data: [
            {
              id: 1,
              description: 'حملة إعلانية',
              category: 'تسويق مخصص',
              amount: '450.00',
              expense_month: 8,
              expense_year: 2026,
            },
          ],
        });
      }
      if (url.includes('/reports/purchases/')) {
        return Promise.resolve({
          data: {
            items: [],
            summary: { total_purchases_amount: 0, gross_purchases_amount: 0 },
          },
        });
      }
      if (url.includes('/company-settings/')) {
        return Promise.resolve({
          data: { results: [{ id: 1, name: 'شركة الاختبار', phone1: '01000000000', collection_commission_rate: 0.1 }] },
        });
      }
      return Promise.resolve({ data: { results: [], count: 0 } });
    });
  });

  afterEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('SuggestionList keeps hook order stable when toggling from closed empty state to open', () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <SuggestionList open={false} suggestions={[]} activeIndex={-1} onSelect={onSelect} />
    );

    expect(screen.queryByRole('list')).toBeNull();

    rerender(
      <SuggestionList
        open={true}
        suggestions={[{ id: 1, name: 'غسالة ١٠ كيلو' }]}
        activeIndex={0}
        onSelect={onSelect}
      />
    );

    const itemText = screen.getByText('غسالة ١٠ كيلو');
    expect(itemText).toBeInTheDocument();
    fireEvent.mouseDown(itemText.closest('li'));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('ReportTable rounds currency & number columns to whole integers and resolves route titleMap cleanly', async () => {
    window.history.pushState({}, '', '/reports/inventory');
    const columns = [
      { key: 'name', label: 'الصنف' },
      { key: 'amount', label: 'الإجمالي', format: 'currency' },
      { key: 'qty', label: 'الكمية', format: 'number' },
    ];
    const data = [{ id: 1, name: 'تلاجة', amount: 1234.67, qty: 15.8 }];

    render(
      <MemoryRouter>
        <ReportsContext.Provider value={{ year: 2026, month: 8, branchId: 1, registerPrintHandler: () => {} }}>
          <ReportTable columns={columns} data={data} loading={false} />
        </ReportsContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByText('1,235')).toBeInTheDocument();
    expect(screen.getByText('16')).toBeInTheDocument();
    expect(screen.queryByText(/\.67|\.8/)).toBeNull();

    // Open PrintModal and trigger Preview to verify print payload title & rounded rows
    fireEvent.click(screen.getByTitle('طباعة التقرير'));
    const previewBtn = await screen.findByText('معاينة ملف PDF');
    await waitFor(() => expect(previewBtn.closest('button')).not.toBeDisabled());
    fireEvent.click(previewBtn.closest('button'));

    await waitFor(() => {
      const call = apiMock.post.mock.calls.find(([u]) => u === '/reports/desktop_print/');
      expect(call).toBeTruthy();
      const [, payload] = call;
      expect(payload.title).toBe('تقرير حركة المخزون');
      expect(payload.rows[0].amount).toBe('1,235');
      expect(payload.rows[0].qty).toBe('16');
    });
  });

  it('SearchReceipts blocks cash-only bulk print across paginated all_ids and filters out cash in mixed selection', async () => {
    // 1. Cash-only across multi-page all_ids
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/salespersons/')) return Promise.resolve({ data: [] });
      if (url.includes('/receipts/')) {
        return Promise.resolve({
          data: {
            count: 3,
            results: [{ id: 10, receipt_number: 101, is_cash_sale: true, receipt_type: 'SALE', total_amount: 500 }],
            all_ids: [10, 11, 12],
            all_installment_ids: [],
            aggregate: { total_sales: 1500 },
          },
        });
      }
      return Promise.resolve({ data: [] });
    });

    const { unmount } = render(
      <MemoryRouter>
        <SearchReceipts />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText('نتائج البحث: 3 فاتورة')).toBeInTheDocument());
    fireEvent.click(screen.getByText('طباعة محددة').closest('button'));

    await waitFor(() => {
      expect(Swal.fire).toHaveBeenCalledWith(
        expect.objectContaining({
          text: 'الطباعة مخصصة فقط لجداول الأقساط (الفواتير الكاش ليس لها جدول طباعة).',
        })
      );
    });
    expect(apiMock.post).not.toHaveBeenCalledWith('/receipts/desktop_print/', expect.anything());
    unmount();

    // 2. Mixed all_ids: includes cash [10, 11] and installment [12] -> prints ONLY [12]
    vi.clearAllMocks();
    apiMock.post.mockResolvedValue({ data: { status: 'ok' } });
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/printers/')) return Promise.resolve({ data: [{ name: 'P1', status: 'ready', is_default: true }] });
      if (url.includes('/salespersons/')) return Promise.resolve({ data: [] });
      if (url.includes('/receipts/')) {
        return Promise.resolve({
          data: {
            count: 3,
            results: [{ id: 10, receipt_number: 101, is_cash_sale: true, receipt_type: 'SALE', total_amount: 500 }],
            all_ids: [10, 11, 12],
            all_installment_ids: [12],
            aggregate: { total_sales: 1500 },
          },
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(
      <MemoryRouter>
        <SearchReceipts />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText('نتائج البحث: 3 فاتورة')).toBeInTheDocument());
    fireEvent.click(screen.getByText('طباعة محددة').closest('button'));
    const previewBtn = await screen.findByText('معاينة ملف PDF');
    await waitFor(() => expect(previewBtn.closest('button')).not.toBeDisabled());
    fireEvent.click(previewBtn.closest('button'));

    await waitFor(() => {
      const printCall = apiMock.post.mock.calls.find(([u]) => u === '/receipts/desktop_print/');
      expect(printCall).toBeTruthy();
      expect(printCall[1].receipt_ids).toEqual([12]);
    });
  });

  it('PurchasesReport uses searchable ReportAutocomplete instead of dynamic supplier <select>', async () => {
    const { container } = render(
      <MemoryRouter>
        <ReportsContext.Provider value={{ year: 2026, month: 8, branchId: 1, registerPrintHandler: () => {} }}>
          <PurchasesReport />
        </ReportsContext.Provider>
      </MemoryRouter>
    );

    const supInput = await screen.findByPlaceholderText('جميع الموردين...');
    expect(supInput).toBeInTheDocument();

    // Ensure no dynamic supplier <option> rendered inside a <select>
    const selects = Array.from(container.querySelectorAll('select'));
    for (const sel of selects) {
      expect(sel.textContent).not.toContain('مورد الأمل');
    }

    fireEvent.change(supInput, { target: { value: 'الأمل' } });
    await waitFor(() => expect(screen.getByText('مورد الأمل')).toBeInTheDocument(), { timeout: 1500 });
    fireEvent.mouseDown(screen.getByText('مورد الأمل'));

    await waitFor(() => {
      const reportCall = apiMock.get.mock.calls.find(
        ([u, cfg]) => u === '/reports/purchases/' && cfg?.params?.supplier_id === '101'
      );
      expect(reportCall).toBeTruthy();
    });
  });

  it('Expenses & Ledger forms support Enter progression, YYYY/MM formatting, and custom categories', async () => {
    render(
      <MemoryRouter>
        <Expenses />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText('2026/08')).toBeInTheDocument());

    const descInput = screen.getByPlaceholderText('البيان (اسم المصروف) *');
    const catInput = screen.getByPlaceholderText('التصنيف (افتراضي: عامة)');
    const amountInput = screen.getByPlaceholderText('المبلغ *');

    descInput.focus();
    fireEvent.keyDown(descInput, { key: 'Enter' });
    expect(document.activeElement).toBe(catInput);

    fireEvent.keyDown(catInput, { key: 'Enter' });
    expect(document.activeElement).toBe(amountInput);

    // Custom category 'تسويق مخصص' from fetched expenses is present in filter <select>
    expect(screen.getByRole('option', { name: 'تسويق مخصص' })).toBeInTheDocument();

    // Ledger Deficit & Commission forms Enter progression
    const { container: ledgerContainer } = render(
      <>
        <LedgerDeficitForm
          showDeficitForm={true}
          setShowDeficitForm={() => {}}
          deficitForm={{ quantity: '', month: '8', year: '2026', reason: '' }}
          setDeficitForm={() => {}}
          handleDeficitSubmit={(e) => e.preventDefault()}
          deficitSubmitting={false}
        />
        <LedgerCommissionForm
          showCommissionForm={true}
          setShowCommissionForm={() => {}}
          commForm={{ amount: '', month: '8', year: '2026' }}
          setCommForm={() => {}}
          handleCommissionSubmit={(e) => e.preventDefault()}
          commSubmitting={false}
        />
      </>
    );

    const qtyInput = ledgerContainer.querySelector('input[placeholder="مثال: 2"]');
    qtyInput.focus();
    fireEvent.keyDown(qtyInput, { key: 'Enter' });
    expect(document.activeElement.value).toBe('8');

    const commAmountInput = ledgerContainer.querySelector('input[placeholder="مثال: 50"]');
    commAmountInput.focus();
    fireEvent.keyDown(commAmountInput, { key: 'Enter' });
    expect(document.activeElement.value).toBe('8');
  });

  it('AppAutocomplete uses typed localValue on ArrowDown & POS F9 triggers save', async () => {
    const fetchSuggestions = vi.fn(async (q) => [{ id: 1, name: `نتيجة ${q}` }]);
    render(
      <AppAutocomplete
        value=""
        onChange={() => {}}
        onSelect={() => {}}
        fetchSuggestions={fetchSuggestions}
        placeholder="اكتب للبحث"
        debounceMs={500}
      />
    );

    const autoInput = screen.getByPlaceholderText('اكتب للبحث');
    fireEvent.change(autoInput, { target: { value: 'ثلاجة' } });
    fireEvent.keyDown(autoInput, { key: 'ArrowDown' });

    await waitFor(() => {
      expect(fetchSuggestions).toHaveBeenCalledWith('ثلاجة');
      expect(screen.getByText('نتيجة ثلاجة')).toBeInTheDocument();
    });

    // POS F9 global shortcut saves receipt
    render(
      <MemoryRouter>
        <POS />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByPlaceholderText('ابحث عن مندوب...')).toBeInTheDocument());
    fireEvent.keyDown(window, { key: 'F9' });
    // Should display validation or save feedback; add item + salesperson -> POST /receipts/
    await waitFor(() => {
      const alertEl = document.querySelector('.alert-danger');
      expect(alertEl).not.toBeNull();
    });
  });

  it('QuickRestoreModal handles status=pending_restart cleanly without decimal MB and CompanyTab blocks setup completion on error', async () => {
    apiMock.post.mockResolvedValueOnce({ data: { status: 'pending_restart' } });
    render(<QuickRestoreModal isOpen={true} onClose={() => {}} />);

    const fileInput = document.querySelector('input[type="file"]');
    const smallFile = new File([new Uint8Array(2048)], 'backup.sqlite3');
    fireEvent.change(fileInput, { target: { files: [smallFile] } });

    expect(screen.getByText(/2 كيلوبايت/)).toBeInTheDocument();
    expect(screen.queryByText(/0\.00/)).toBeNull();

    const restoreBtn = screen.getByRole('button', { name: /بدء الاستعادة الآن/i });
    fireEvent.click(restoreBtn);
    await waitFor(() => {
      expect(screen.getByText(/تم تجهيز النسخة الاحتياطية بنجاح/)).toBeInTheDocument();
    });

    // CompanyTab must not call onSetupComplete if save fails
    const onSetupComplete = vi.fn();
    apiMock.patch.mockRejectedValueOnce({ response: { data: { error: 'كلمة المرور مطلوبة' } } });
    const { container } = render(
      <MemoryRouter>
        <CompanyTab isFirstSetup={true} onSetupComplete={onSetupComplete} />
      </MemoryRouter>
    );

    await waitFor(() => expect(apiMock.get).toHaveBeenCalledWith('/company-settings/'));
    const form = container.querySelector('form');
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText('كلمة المرور مطلوبة')).toBeInTheDocument();
    });
    expect(onSetupComplete).not.toHaveBeenCalled();
  });

  it('InstallmentsReport auto-selects all rows on load, renders print button in sticky toolbar, and dispatches single-month installment_ids with chunkSize=20', async () => {
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/printers/')) {
        return Promise.resolve({ data: { printers: [{ name: 'HP_LaserJet', status: 'ready', is_default: true }] } });
      }
      if (url.includes('/salespersons/')) {
        return Promise.resolve({ data: [{ id: 1, name: 'مندوب ١' }] });
      }
      if (url.includes('/reports/installments/')) {
        return Promise.resolve({
          data: {
            total_installments_amount: 1500,
            installments_count: 3,
            installments: [
              { payment_id: 501, receipt_id: 9001, receipt_num: 101, customer_name: 'عميل أ', amount: 500, area: 'الدقي', phone: '0101' },
              { payment_id: 502, receipt_id: 9001, receipt_num: 101, customer_name: 'عميل أ', amount: 500, area: 'الدقي', phone: '0101' },
              { payment_id: 503, receipt_id: 9002, receipt_num: 102, customer_name: 'عميل ب', amount: 500, area: 'المعادي', phone: '0102' },
            ],
          },
        });
      }
      return Promise.resolve({ data: [] });
    });

    const { container } = render(
      <MemoryRouter>
        <ReportsContext.Provider value={{ year: 2026, month: 8, branchId: 1, registerPrintHandler: () => {} }}>
          <StandardTablePageLayout title="التقارير">
            <InstallmentsReport />
          </StandardTablePageLayout>
        </ReportsContext.Provider>
      </MemoryRouter>
    );

    // Auto-selects all 3 rows on load and renders print button inside .sticky-toolbar
    const printSelectedBtn = await screen.findByRole('button', { name: /طباعة جداول المحدد \(3\)/ });
    expect(printSelectedBtn.closest('.sticky-toolbar')).not.toBeNull();
    expect(screen.getByText('تم تحديد 3')).toBeInTheDocument();

    // Unselect all via header checkbox -> 0 selected, then re-select all -> 3 selected
    const headerCheckbox = container.querySelector('thead input[type="checkbox"]');
    expect(headerCheckbox.checked).toBe(true);
    fireEvent.click(headerCheckbox);
    await waitFor(() => expect(headerCheckbox.checked).toBe(false));
    expect(screen.queryByText('تم تحديد 3')).toBeNull();

    fireEvent.click(headerCheckbox);
    await waitFor(() => expect(headerCheckbox.checked).toBe(true));
    expect(screen.getByText('تم تحديد 3')).toBeInTheDocument();

    // Click print selected -> opens PrintModal with 3 items (no batch split alert since 3 <= 20)
    fireEvent.click(screen.getByRole('button', { name: /طباعة جداول المحدد \(3\)/ }));
    const previewBtn = await screen.findByText('معاينة ملف PDF');
    expect(screen.queryByText(/تقسيم الدفعات التلقائي/)).toBeNull();
    fireEvent.click(previewBtn.closest('button'));

    await waitFor(() => {
      const printCall = apiMock.post.mock.calls.find(([u]) => u === '/receipts/desktop_print/');
      expect(printCall).toBeTruthy();
      expect(printCall[1]).toMatchObject({
        receipt_ids: [9001, 9002],
        installment_ids: [501, 502, 503],
        month: 8,
        year: 2026,
        action: 'view',
      });
    });
  });

  it('PrintModal supports chunkSize=2 for SearchReceipts, hides batch banner on A4 ReportTable (>20 rows), and shows retry alert on printer fetch error', async () => {
    // 1. Printer fetch error -> renders retry warning alert; clicking retry loads printers
    let printerAttempt = 0;
    apiMock.get.mockImplementation((url) => {
      if (url.includes('/printers/')) {
        printerAttempt++;
        if (printerAttempt === 1) return Promise.reject(new Error('Spooler unavailable'));
        return Promise.resolve({ data: { printers: [{ name: 'Offline_USB_Printer', status: 'offline', is_default: true }] } });
      }
      return Promise.resolve({ data: [] });
    });

    const executeChunkMock = vi.fn(() => Promise.resolve());
    const { unmount } = render(
      <PrintModal
        isOpen={true}
        onClose={() => {}}
        title="طباعة جداول الأقساط"
        items={[1, 2, 3, 4, 5]}
        itemLabel="جدول أقساط"
        chunkSize={2}
        executeChunk={executeChunkMock}
      />
    );

    // Verify dynamic chunkSize=2 batch banner
    expect(await screen.findByText(/إلى دفعات متتابعة من 2 عنصراً/)).toBeInTheDocument();

    // Verify printer error alert & retry button
    expect(await screen.findByText('تعذر فحص حالة الطابعات من النظام')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /إعادة المحاولة/ }));
    await waitFor(() => {
      expect(screen.getByText('غير متصل (Offline)')).toBeInTheDocument();
    });

    // Click direct print on offline printer -> shows pre-print offline warning -> confirm -> runs 3 chunks of size 2 ([1,2], [3,4], [5])
    fireEvent.click(screen.getByRole('button', { name: /طباعة فورية/ }));
    expect(await screen.findByText(/غير متصلة حالياً \(Offline\)/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /متابعة الطباعة على أي حال/ }));

    await waitFor(() => {
      expect(executeChunkMock).toHaveBeenCalledTimes(3);
      expect(executeChunkMock.mock.calls[0][0]).toEqual([1, 2]);
      expect(executeChunkMock.mock.calls[1][0]).toEqual([3, 4]);
      expect(executeChunkMock.mock.calls[2][0]).toEqual([5]);
    });
    unmount();

    // 2. Single-PDF A4 Report (items=null, itemCount=35) must NOT show batch-split banner
    render(
      <PrintModal
        isOpen={true}
        onClose={() => {}}
        title="طباعة تقرير تحليلي"
        itemCount={35}
        itemLabel="سجل"
        onExecute={vi.fn(() => Promise.resolve())}
      />
    );
    expect(screen.queryByText(/تقسيم الدفعات التلقائي/)).toBeNull();
  });

  it('AppAutocomplete clear X button has pointerEvents: auto, clears without null crash, and filter toolbar number inputs clamp bounds cleanly', async () => {
    const onSelectMock = vi.fn();
    const onChangeMock = vi.fn();
    const { unmount } = render(
      <AppAutocomplete
        value="الهرم"
        onChange={onChangeMock}
        onSelect={onSelectMock}
        items={[{ id: 1, name: 'الهرم' }]}
        placeholder="المنطقة..."
      />
    );

    const clearBtn = screen.getByTitle('مسح الحقل');
    expect(clearBtn).toBeInTheDocument();
    expect(clearBtn.style.pointerEvents).toBe('auto');
    fireEvent.click(clearBtn);
    expect(onChangeMock).toHaveBeenCalledWith('');
    expect(onSelectMock).toHaveBeenCalledWith(null);
    unmount();

    // SearchReceipts filter toolbar numeric limits & From <= To clamping on blur
    const { container } = render(
      <MemoryRouter>
        <SearchReceipts />
      </MemoryRouter>
    );

    const monthInput = container.querySelector('input[name="month"]');
    const yearInput = container.querySelector('input[name="year"]');
    const fromInput = container.querySelector('input[name="receipt_from"]');
    const toInput = container.querySelector('input[name="receipt_to"]');

    expect(monthInput.getAttribute('type')).toBe('number');
    expect(yearInput.getAttribute('type')).toBe('number');
    expect(fromInput.getAttribute('type')).toBe('number');
    expect(toInput.getAttribute('type')).toBe('number');

    fireEvent.change(monthInput, { target: { name: 'month', value: '15' } });
    fireEvent.blur(monthInput);
    expect(monthInput.value).toBe('12');

    fireEvent.change(yearInput, { target: { name: 'year', value: '2015' } });
    fireEvent.blur(yearInput);
    expect(yearInput.value).toBe('2020');

    fireEvent.change(toInput, { target: { name: 'receipt_to', value: '50' } });
    fireEvent.change(fromInput, { target: { name: 'receipt_from', value: '100' } });
    fireEvent.blur(fromInput);
    expect(fromInput.value).toBe('50');

    // ReportsLayout must not unmount filter inputs when month is temporarily cleared while typing
    render(
      <MemoryRouter initialEntries={['/reports/purchases?year=2026&month=8']}>
        <Routes>
          <Route path="/reports" element={<ReportsLayout />}>
            <Route path="purchases" element={<PurchasesReport />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    const repMonthInput = await screen.findByPlaceholderText('شهر');
    fireEvent.change(repMonthInput, { target: { value: '' } });
    expect(screen.getByPlaceholderText('شهر')).toBeInTheDocument();
    fireEvent.blur(repMonthInput);
    expect(repMonthInput.value).toBe('8');
  });
});
