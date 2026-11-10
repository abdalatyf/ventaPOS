import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Login from '../pages/Login';
import ActivationSetup from '../pages/ActivationSetup';
import BranchSelection from '../pages/BranchSelection';

// Mock api
vi.mock('../api', () => ({
  default: {
    get: vi.fn((url) => {
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
      return Promise.resolve({ data: {} });
    }),
    post: vi.fn((url, payload) => {
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
    }),
  },
  getLicenseStatus: vi.fn(() => Promise.resolve({ is_print_only: false, is_expired: false, status: 'active' })),
  clearLicenseCache: vi.fn(),
}));

describe('Auth & Lifecycle Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
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
});
