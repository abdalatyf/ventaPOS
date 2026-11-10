import { test, expect } from '@playwright/test';

test.describe('Reports Module E2E Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // Pre-populate localStorage so every page load is already authenticated
    await context.addInitScript(() => {
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('branchId', '1');
      localStorage.setItem('branchName', 'الفرع الرئيسي');
    });

    // Intercept all API calls strictly under /api/v1/ to avoid intercepting Vite source files
    await page.route('**/api/v1/frontend-logs/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.route('**/api/v1/license/status/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'active',
          is_demo: false,
          is_print_only: false,
          is_expired: false,
          total_invoices_balance: 5000,
          expiry_date: '2027-01-01',
          start_date: '2026-01-01',
        })
      });
    });

    await page.route('**/api/v1/branches/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'الفرع الرئيسي' }])
      });
    });

    await page.route('**/api/v1/company-settings/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ name: 'مؤسسة التجارة الحديثة' })
      });
    });

    await page.route('**/api/v1/salespersons/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'محمد علي' }])
      });
    });

    await page.route('**/api/v1/suppliers/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, name: 'شركة النور' }])
      });
    });

    await page.route('**/api/v1/default-date/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ year: 2026, month: 7 })
      });
    });

    await page.route('**/api/v1/reports/dashboard/summary/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sales: { gross: 100000, net: 95000, cash: 40000, installment: 60000, down_payments: 15000, returns: 5000 },
          collections: { expected: 20000, actual: 18000, percentage: 90 },
          purchases: { total: 50000, returns: 2000, net: 48000 },
          expenses: { total: 7000 },
          profit: { gross: 30000, net: 23000 }
        })
      });
    });

    await page.route('**/api/v1/reports/dashboard/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          period: { year: 2026, month: 7 },
          kpis: {
            safe_balance: 1000,
            total_revenue: 5000,
            total_cogs: 2000,
            total_sales_commissions: 100,
            total_collection_commissions: 50,
            estimated_net_profit: 2000,
            current_inventory_value: 10000,
            low_stock_count: 0,
            avg_basket_size: 150
          },
          cash_drawer_summary: {
            cash_sales_inflow: 3000,
            down_payment_inflow: 500,
            collection_inflow: 500,
            total_cash_inflow: 4000,
            total_purchases: 1000,
            operating_expenses: 500,
            auto_salaries: 150,
            net_cash_in_hand: 2350
          },
          top_products: [],
          top_areas: []
        })
      });
    });

    await page.route('**/api/v1/receipts/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          count: 1,
          results: [{ id: 1, receipt_number: 101, customer_name: 'أحمد', total_amount: 100 }]
        })
      });
    });

    await page.route('**/api/v1/expenses/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          count: 1,
          results: [{ id: 1, description: 'إيجار', amount: 50 }]
        })
      });
    });

    await page.route('**/api/v1/reports/salesperson-performance/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totals: { grand_total_sales: 0, grand_total_collected: 0, grand_total_due: 0, grand_total_cash: 0 },
          salespersons: [
            {
              id: 1,
              name: 'محمد علي',
              receipts_count: 5,
              cash_sales: 1000,
              credit_sales: 4000,
              down_payments: 500,
              total_sales_val: 5000,
              collected: 1000,
              comm_sales: 250,
              comm_coll: 100,
              due_salary: 350
            }
          ]
        })
      });
    });

    await page.route('**/api/v1/reports/profit-and-loss/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          summary: { 
            grand_revenue: 100, 
            grand_cost: 50, 
            grand_commission: 10, 
            expenses_total: 20, 
            net_profit_final: 20 
          },
          details: []
        })
      });
    });

    await page.route('**/api/v1/reports/inventory-movement/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_inventory_value: 0,
          total_adjustments_count: 0,
          items: [
            {
              id: 1,
              name: 'منتج',
              initial_qty: 10,
              purchases_qty: 5,
              sales_qty: 2,
              returns_qty: 0,
              current_stock: 13
            }
          ]
        })
      });
    });

    await page.route('**/api/v1/reports/installments/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_installments_amount: 100,
          installments_count: 1,
          installments: [{ id: 1, receipt_number: 101, customer_name: 'علي حسن', monthly_amount: 500, total_amount: 3000 }]
        })
      });
    });

    await page.route('**/api/v1/reports/areas/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          areas: [
            {
              area: 'الدقي',
              gross_sales: 10000,
              cash_sales: 4000,
              installment_sales: 6000,
              down_payments: 1000,
              due_installments_month: 2000,
              returns_amount: 0,
              net_sales: 10000,
              invoices_count: 5,
              salespersons_display: 'محمد علي'
            }
          ],
          summary: { total_sales: 10000, net_sales: 10000, areas_count: 1 }
        })
      });
    });

    await page.route('**/api/v1/reports/purchases/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          invoices: [],
          summary: { total_purchases: 0, total_returns: 0, net_purchases: 0 }
        })
      });
    });

    await page.route('**/api/v1/reports/averages/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          products: [],
          summary: { total_sales: 0, total_units: 0 }
        })
      });
    });
  });

  test('Dashboard Report loads successfully', async ({ page }) => {
    await page.goto('/reports/dashboard');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.getByText('تفاصيل السيولة')).toBeVisible();
    await expect(page.getByText('تفاصيل المكسب')).toBeVisible();
  });

  test('Receipts Report tab loads as read-only', async ({ page }) => {
    await page.goto('/reports/receipts');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('button', { hasText: 'إضافة فاتورة' })).toHaveCount(0);
  });

  test('Installments Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/installments');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('Expenses Report tab loads as read-only', async ({ page }) => {
    await page.goto('/reports/expenses');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('button', { hasText: 'إضافة' })).toHaveCount(0);
  });

  test('Profit & Loss Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/profit-and-loss');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('Inventory Movement Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/inventory');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table th')).toHaveCount(10);
  });

  test('Salesperson Performance Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/salesperson');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table th')).toHaveCount(12);
  });

  test('Areas Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/areas');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('Purchases Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/purchases');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('Averages Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/averages');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });
});
