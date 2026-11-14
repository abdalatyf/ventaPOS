import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route, Outlet, useLocation } from 'react-router-dom';
import { vi } from 'vitest';
import Login from '../pages/Login';
import ActivationSetup from '../pages/ActivationSetup';
import BranchSelection from '../pages/BranchSelection';
import App from '../App';
import DemoBanner from '../components/DemoBanner';
import QuickRestoreModal from '../components/common/QuickRestoreModal';
import PrintModal from '../components/common/PrintModal';
import UpdateModal from '../components/common/UpdateModal';
import UserManualModal from '../components/common/UserManualModal';
import SubscriptionTab from '../pages/settings/tabs/SubscriptionTab';
import SecurityTab from '../pages/settings/tabs/SecurityTab';
import api, { getLicenseStatus, clearLicenseCache } from '../api';

vi.mock('../components/AppShell', async () => {
  const { Outlet: RouterOutlet } = await import('react-router-dom');
  return {
    default: () => (
      <div data-testid="mock-appshell">
        <RouterOutlet />
      </div>
    ),
  };
});

vi.mock('../pages/ReturnReceipt', () => ({
  default: () => <div data-testid="return-receipt-page">RETURN_RECEIPT_PAGE</div>,
}));

vi.mock('../pages/SearchReceipts', () => ({
  default: () => <div data-testid="search-receipts-page">SEARCH_RECEIPTS_PAGE</div>,
}));

const defaultGetImpl = (url) => {
  if (url.includes('/branches/')) {
    return Promise.resolve({
      data: [
        { id: 1, name: 'الفرع الرئيسي', code: 'MAIN' },
        { id: 2, name: 'فرع الجيزة', code: 'GIZA' }
      ]
    });
  }
  if (url.includes('/license/status/')) {
    return Promise.resolve({
      data: {
        status: 'active',
        is_demo: false,
        has_password: true,
        total_invoices_balance: 5000,
        expiry_date: '2027-01-01',
      }
    });
  }
  if (url.includes('/company-settings/')) {
    return Promise.resolve({
      data: { name: 'مؤسسة التجارة الحديثة' }
    });
  }
  if (url.includes('/license-history/')) {
    return Promise.resolve({ data: [] });
  }
  if (url.includes('/auth/has-password/')) {
    return Promise.resolve({ data: { has_password: true } });
  }
  if (url.includes('/receipts/printers/')) {
    return Promise.resolve({
      data: {
        printers: [
          { name: 'HP LaserJet Ready', status: 'ready', is_default: true },
          { name: 'Canon Offline', status: 'offline', is_default: false },
        ],
      },
    });
  }
  if (url.includes('/system/check-update/')) {
    return Promise.resolve({
      data: { current_version: '1.0.0', has_update: false, offline: false },
    });
  }
  return Promise.resolve({ data: {} });
};

const defaultPostImpl = (url, payload) => {
  if (url === '/auth/demo/') {
    return Promise.reject(new Error('Not demo mode'));
  }
  if (url === '/auth/local/') {
    if (payload?.password === 'correct_pass') {
      return Promise.resolve({
        data: { token: 'mock-jwt-token', company_name: 'مؤسسة التجارة الحديثة' }
      });
    }
    return Promise.reject({
      response: { data: { error: 'كلمة المرور غير صحيحة' } }
    });
  }
  if (url === '/auth/recover-password/') {
    return Promise.resolve({ data: { message: 'تم تعيين كلمة المرور بنجاح' } });
  }
  return Promise.resolve({ data: {} });
};

// Mock api
vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  getLicenseStatus: vi.fn(),
  clearLicenseCache: vi.fn(),
}));

function LocationEcho() {
  const loc = useLocation();
  return <div data-testid="location-echo">{`${loc.pathname}${loc.search}`}</div>;
}

describe('Auth & Lifecycle Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    api.get.mockImplementation(defaultGetImpl);
    api.post.mockImplementation(defaultPostImpl);
    getLicenseStatus.mockImplementation(() =>
      Promise.resolve({ is_print_only: false, is_expired: false, status: 'active' })
    );
    window.history.pushState({}, '', '/');
  });

  it('renders Login page and handles failed and successful password authentication', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Login />
      </MemoryRouter>
    );

    // Verify password input is present
    const passwordInput = await screen.findByPlaceholderText(/أدخل كلمة سر النظام/i);
    expect(passwordInput).toBeInTheDocument();

    // Try wrong password
    fireEvent.change(passwordInput, { target: { value: 'wrong_pass' } });
    fireEvent.submit(passwordInput.closest('form'));

    await waitFor(() => {
      expect(screen.getByText(/كلمة المرور غير صحيحة/i)).toBeInTheDocument();
    });

    // Enter correct password
    fireEvent.change(passwordInput, { target: { value: 'correct_pass' } });
    fireEvent.submit(passwordInput.closest('form'));

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('mock-jwt-token');
      expect(localStorage.getItem('company_name')).toBe('مؤسسة التجارة الحديثة');
    });
  });

  it('renders ActivationSetup wizard with setup greeting and backup restore button', async () => {
    render(
      <MemoryRouter initialEntries={['/activation-setup']}>
        <ActivationSetup />
      </MemoryRouter>
    );

    expect(screen.getByText(/تهانينا! تم تفعيل VentaPOS بنجاح/i)).toBeInTheDocument();
    expect(screen.getByText(/استعادة نسخة احتياطية/i)).toBeInTheDocument();
  });

  it('renders BranchSelection with branches and allows selecting an active branch', async () => {
    render(
      <MemoryRouter initialEntries={['/select-branch']}>
        <BranchSelection />
      </MemoryRouter>
    );

    // Wait for branch names to appear
    await waitFor(() => {
      expect(screen.getByText(/الفرع الرئيسي/i)).toBeInTheDocument();
      expect(screen.getByText(/فرع الجيزة/i)).toBeInTheDocument();
    });

    // Click on Branch 1
    const branchBtn = screen.getByText(/الفرع الرئيسي/i);
    fireEvent.click(branchBtn);

    expect(localStorage.getItem('branchId')).toBe('1');
    expect(localStorage.getItem('branchName')).toBe('الفرع الرئيسي');
  });

  it('SubscriptionTab displays license balance, print-only badge, and activation history', async () => {
    api.get.mockImplementation((url) => {
      if (url.includes('/license/status/')) {
        return Promise.resolve({
          data: {
            status: 'active',
            total_invoices_balance: 7500,
            is_print_only: true,
            is_expired: false,
            is_demo: false,
            start_date: '2026/01',
            expiry_date: '2027-01-01',
          },
        });
      }
      if (url.includes('/license-history/')) {
        return Promise.resolve({
          data: {
            results: [
              {
                id: 11,
                product_name: 'طباعة فقط - سنة واحدة',
                operation_type: 'تفعيل أولي',
                added_balance: 5000,
                start_date: '2026/01',
                end_date: '2027/01',
                archived_at: '2026-01-01T10:00:00Z',
                status: 'SUCCESS',
              },
            ],
          },
        });
      }
      return defaultGetImpl(url);
    });

    render(
      <MemoryRouter>
        <SubscriptionTab />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/license/status/');
      expect(api.get).toHaveBeenCalledWith('/license-history/');
      expect(screen.getByText(/الرصيد المتاح: 7,500 فاتورة/)).toBeInTheDocument();
      expect(screen.getByText(/باقة طباعة فقط/)).toBeInTheDocument();
      expect(screen.getByText('طباعة فقط - سنة واحدة')).toBeInTheDocument();
      expect(screen.getByText('تفعيل أولي')).toBeInTheDocument();
      expect(screen.getByText('ناجح')).toBeInTheDocument();
    });
  });

  it('PrintOnlyGate redirects /receipts/return/1 to /receipts when is_print_only is true, and allows access when false', async () => {
    localStorage.setItem('token', 'live-token');
    localStorage.setItem('branchId', '1');

    getLicenseStatus.mockResolvedValue({ is_print_only: true, is_expired: false, status: 'active' });
    window.history.pushState({}, '', '/receipts/return/1');
    const { unmount } = render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('search-receipts-page')).toBeInTheDocument();
      expect(screen.queryByTestId('return-receipt-page')).not.toBeInTheDocument();
      expect(window.location.pathname).toBe('/receipts');
    });
    unmount();

    getLicenseStatus.mockResolvedValue({ is_print_only: false, is_expired: false, status: 'active' });
    window.history.pushState({}, '', '/receipts/return/1');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('return-receipt-page')).toBeInTheDocument();
      expect(screen.queryByTestId('search-receipts-page')).not.toBeInTheDocument();
    });
  });

  it('QuickRestoreModal shows pending_restart notice without scheduling /login redirect, and schedules 2s /login redirect for immediate swap', async () => {
    const originalLocation = window.location;
    delete window.location;
    window.location = { ...originalLocation, href: 'http://localhost/' };

    try {
      // Case 1: pending_restart
      api.post.mockImplementationOnce((url) => {
        if (url === '/tools/backup/upload/') {
          return Promise.resolve({ data: { status: 'pending_restart', pending_restart: true } });
        }
        return Promise.resolve({ data: {} });
      });

      const timeoutSpy = vi.spyOn(globalThis, 'setTimeout');
      const { container, unmount } = render(<QuickRestoreModal isOpen={true} onClose={vi.fn()} />);

      const fileInput1 = container.querySelector('input[type="file"]');
      fireEvent.change(fileInput1, {
        target: { files: [new File(['sqlite'], 'backup.sqlite3')] },
      });
      fireEvent.click(screen.getByRole('button', { name: /بدء الاستعادة الآن/ }));

      await waitFor(() => {
        expect(
          screen.getByText(/تم تجهيز النسخة الاحتياطية بنجاح! يرجى إعادة تشغيل البرنامج لتطبيق التغييرات\./)
        ).toBeInTheDocument();
      });
      expect(timeoutSpy.mock.calls.some((c) => c[1] === 2000)).toBe(false);
      timeoutSpy.mockRestore();
      unmount();

      // Case 2: immediate restore (non-pending_restart) schedules 2000ms redirect to /login
      api.post.mockImplementationOnce((url) => {
        if (url === '/tools/backup/upload/') {
          return Promise.resolve({ data: { status: 'restored', pending_restart: false } });
        }
        return Promise.resolve({ data: {} });
      });

      const redirectSpy = vi.spyOn(globalThis, 'setTimeout');
      const { container: c2 } = render(<QuickRestoreModal isOpen={true} onClose={vi.fn()} />);

      const fileInput2 = c2.querySelector('input[type="file"]');
      fireEvent.change(fileInput2, {
        target: { files: [new File(['sqlite'], 'backup.sqlite3')] },
      });
      fireEvent.click(screen.getByRole('button', { name: /بدء الاستعادة الآن/ }));

      await waitFor(() => {
        expect(redirectSpy.mock.calls.some((c) => c[1] === 2000)).toBe(true);
      });
      const scheduledCall = redirectSpy.mock.calls.find((c) => c[1] === 2000);
      redirectSpy.mockRestore();
      scheduledCall[0]();
      expect(window.location.href).toBe('/login');
    } finally {
      window.location = originalLocation;
    }
  });

  it('DemoBanner hides on /login and /activation-setup, opens QuickRestoreModal, and navigates to /settings?tab=subscription', async () => {
    getLicenseStatus.mockResolvedValue({ is_demo: true, is_expired: false, status: 'demo' });

    const { container: cLogin, unmount: u1 } = render(
      <MemoryRouter initialEntries={['/login']}>
        <DemoBanner />
      </MemoryRouter>
    );
    await waitFor(() => expect(cLogin.textContent).toBe(''));
    u1();

    const { container: cSetup, unmount: u2 } = render(
      <MemoryRouter initialEntries={['/activation-setup']}>
        <DemoBanner />
      </MemoryRouter>
    );
    await waitFor(() => expect(cSetup.textContent).toBe(''));
    u2();

    render(
      <MemoryRouter initialEntries={['/']}>
        <DemoBanner />
        <Routes>
          <Route path="*" element={<LocationEcho />} />
        </Routes>
      </MemoryRouter>
    );

    const activateBtn = await screen.findByRole('button', { name: /تفعيل البرنامج/ });
    const restoreBtn = screen.getByRole('button', { name: /استعادة نسخة احتياطية/ });

    fireEvent.click(restoreBtn);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /بدء الاستعادة الآن/ })).toBeInTheDocument();
    });

    fireEvent.click(activateBtn);
    await waitFor(() => {
      expect(screen.getByTestId('location-echo')).toHaveTextContent('/settings?tab=subscription');
    });
  });

  it('SecurityTab changes password and rotates token in localStorage', async () => {
    localStorage.setItem('token', 'old-token');
    api.post.mockImplementationOnce((url, payload) => {
      if (url === '/auth/change-password/') {
        expect(payload.old_password).toBe('old123');
        expect(payload.new_password).toBe('newpass456');
        return Promise.resolve({ data: { token: 'rotated-fresh-token' } });
      }
      return Promise.resolve({ data: {} });
    });

    const { container } = render(
      <MemoryRouter>
        <SecurityTab />
      </MemoryRouter>
    );

    const oldInput = await waitFor(() => {
      const el = container.querySelector('input[name="oldPassword"]');
      expect(el).not.toBeNull();
      return el;
    });
    const newInput = container.querySelector('input[name="newPassword"]');
    const confirmInput = container.querySelector('input[name="confirmPassword"]');

    fireEvent.change(oldInput, { target: { value: 'old123' } });
    fireEvent.change(newInput, { target: { value: 'newpass456' } });
    fireEvent.change(confirmInput, { target: { value: 'newpass456' } });
    fireEvent.click(screen.getByRole('button', { name: /حفظ/ }));

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('rotated-fresh-token');
      expect(screen.getByText(/تم تحديث كلمة المرور بنجاح\./)).toBeInTheDocument();
    });
  });

  it('PrintModal shows offline warning/override, chunks 45 items by 20 with progress, and supports retry & cancel recovery', async () => {
    const items45 = Array.from({ length: 45 }, (_, i) => i + 1);
    let rejectChunk2;
    const chunk2Promise = new Promise((_, rej) => {
      rejectChunk2 = rej;
    });

    // Sub-scenario A: offline warning -> cancel -> override -> 45-item chunking -> chunk 2 fails -> retry succeeds
    let callIdx = 0;
    const executeChunk = vi.fn((chunk, meta) => {
      callIdx += 1;
      if (callIdx === 1) return Promise.resolve();
      if (callIdx === 2) return chunk2Promise;
      return Promise.resolve();
    });
    const onClose = vi.fn();

    const { container, unmount } = render(
      <PrintModal
        isOpen={true}
        onClose={onClose}
        title="طباعة الإيصالات"
        itemCount={45}
        itemLabel="إيصال"
        items={items45}
        executeChunk={executeChunk}
      />
    );

    const selectEl = await waitFor(() => {
      const s = container.querySelector('select');
      expect(s).not.toBeNull();
      expect(s.options.length).toBeGreaterThanOrEqual(2);
      return s;
    });

    // Switch to offline printer -> shows offline badge and warning modal on print click
    fireEvent.change(selectEl, { target: { value: 'Canon Offline' } });
    await waitFor(() => {
      expect(screen.getByText(/غير متصل \(Offline\)/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /طباعة فورية/ }));
    await waitFor(() => {
      expect(screen.getByText(/تنبيه: الطابعة المحددة.*غير متصلة حالياً \(Offline\)\./)).toBeInTheDocument();
    });

    // Cancel warning, then re-open and override
    fireEvent.click(screen.getByRole('button', { name: /إلغاء \/ تغيير الطابعة/ }));
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /متابعة الطباعة على أي حال/ })).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /طباعة فورية/ }));
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /متابعة الطباعة على أي حال/ })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /متابعة الطباعة على أي حال/ }));

    // Chunk 1 finishes -> sets progress -> chunk 2 hangs in-flight -> check progress indicator
    await waitFor(() => {
      expect(screen.getByText(/جاري معالجة الدفعة 1 من 3/)).toBeInTheDocument();
    });
    expect(executeChunk).toHaveBeenCalledTimes(2);
    expect(executeChunk.mock.calls[0][0]).toHaveLength(20);
    expect(executeChunk.mock.calls[1][0]).toHaveLength(20);

    // Reject chunk 2 -> pauses on chunk 2 error
    rejectChunk2(new Error('Printer offline mid-job'));
    await waitFor(() => {
      expect(screen.getByText(/تعذر إرسال الدفعة رقم 2 إلى الطابعة!/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /إعادة محاولة الدفعة/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /إلغاء باقي الدفعات/ })).toBeInTheDocument();
    });

    // Retry chunk 2 -> succeeds, then chunk 3 (length 5) succeeds -> closes modal
    fireEvent.click(screen.getByRole('button', { name: /إعادة محاولة الدفعة/ }));
    await waitFor(() => {
      expect(executeChunk).toHaveBeenCalledTimes(4);
      expect(onClose).toHaveBeenCalled();
    });
    expect(executeChunk.mock.calls[2][0]).toHaveLength(20);
    expect(executeChunk.mock.calls[3][0]).toHaveLength(5);
    unmount();

    // Sub-scenario B: error recovery cancel skips chunk 3
    localStorage.clear();
    let cancelCallIdx = 0;
    const executeChunkCancel = vi.fn(() => {
      cancelCallIdx += 1;
      if (cancelCallIdx === 2) return Promise.reject(new Error('Paper out'));
      return Promise.resolve();
    });
    const onCloseCancel = vi.fn();

    const { container: cCancel } = render(
      <PrintModal
        isOpen={true}
        onClose={onCloseCancel}
        title="طباعة الإيصالات"
        itemCount={45}
        itemLabel="إيصال"
        items={items45}
        executeChunk={executeChunkCancel}
      />
    );

    await waitFor(() => {
      const sel = cCancel.querySelector('select');
      expect(sel && sel.options.length >= 2).toBe(true);
    });
    fireEvent.click(screen.getByRole('button', { name: /طباعة فورية/ }));

    await waitFor(() => {
      expect(screen.getByText(/تعذر إرسال الدفعة رقم 2 إلى الطابعة!/)).toBeInTheDocument();
    });
    expect(executeChunkCancel).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByRole('button', { name: /إلغاء باقي الدفعات/ }));
    await waitFor(() => {
      expect(onCloseCancel).toHaveBeenCalled();
    });
    expect(executeChunkCancel).toHaveBeenCalledTimes(2);
  });

  it('UpdateModal displays available update, posts signed update payload, and renders offline status', async () => {
    api.get.mockImplementation((url) => {
      if (url.includes('/system/check-update/')) {
        return Promise.resolve({
          data: {
            current_version: '1.0.0',
            latest_version: '1.1.0',
            has_update: true,
            offline: false,
            download_url: 'https://github.com/org/repo/releases/download/v1.1.0/setup.exe',
            sha256: 'deadbeef1234',
            release_notes: 'إصلاحات شاملة',
          },
        });
      }
      return defaultGetImpl(url);
    });
    api.post.mockImplementation((url, payload) => {
      if (url === '/system/apply-update/') {
        return Promise.resolve({ data: { status: 'downloading' } });
      }
      return defaultPostImpl(url, payload);
    });

    const { unmount } = render(<UpdateModal isOpen={true} onClose={vi.fn()} />);

    const applyBtn = await screen.findByRole('button', { name: /تثبيت التحديث الآن/ });
    expect(screen.getByText(/يتوفر تحديث جديد للنظام \(v1\.1\.0\)!/)).toBeInTheDocument();
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/system/apply-update/', {
        download_url: 'https://github.com/org/repo/releases/download/v1.1.0/setup.exe',
        sha256: 'deadbeef1234',
        version: '1.1.0',
      });
    });
    unmount();

    api.get.mockImplementation((url) => {
      if (url.includes('/system/check-update/')) {
        return Promise.resolve({
          data: { current_version: '1.0.0', has_update: false, offline: true },
        });
      }
      return defaultGetImpl(url);
    });

    render(<UpdateModal isOpen={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText(/وضع عدم الاتصال:/)).toBeInTheDocument();
    });
  });

  it('UserManualModal filters chapters by query, shows empty state, and switches chapters', async () => {
    render(<UserManualModal isOpen={true} onClose={vi.fn()} />);

    const searchInput = screen.getByPlaceholderText('ابحث في فصول وموضوعات دليل الاستخدام...');
    expect(searchInput).toBeInTheDocument();

    const chapterButtons = screen.getAllByRole('button').filter((b) => /\d+/.test(b.textContent || ''));
    expect(chapterButtons.length).toBeGreaterThanOrEqual(2);
    fireEvent.click(chapterButtons[1]);

    fireEvent.change(searchInput, { target: { value: 'zzzz_unmatched_query_999' } });
    await waitFor(() => {
      expect(screen.getByText(/لا توجد فصول مطابقة للبحث/)).toBeInTheDocument();
    });

    fireEvent.change(searchInput, { target: { value: '1' } });
    await waitFor(() => {
      expect(screen.queryByText(/لا توجد فصول مطابقة للبحث/)).not.toBeInTheDocument();
    });
  });
});

