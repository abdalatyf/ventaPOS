import { test, expect } from '@playwright/test';

test.describe('Reports Module E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept all API calls
    await page.route('**/default-date/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ year: 2026, month: 7 })
      });
    });

    await page.route('**/reports/dashboard/**', async (route) => {
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

    await page.route('**/receipts/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, total_amount: 100 }])
      });
    });

    await page.route('**/expenses/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, amount: 50 }])
      });
    });

    await page.route('**/reports/salesperson-performance/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totals: { grand_total_sales: 0, grand_total_collected: 0, grand_total_due: 0, grand_total_cash: 0 },
          salespersons: []
        })
      });
    });

    await page.route('**/reports/profit-and-loss/**', async (route) => {
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

    await page.route('**/reports/inventory-movement/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_inventory_value: 0,
          total_adjustments_count: 0,
          items: []
        })
      });
    });

    await page.route('**/reports/installments/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_collected: 0,
          salesperson_breakdown: [{ salesperson_id: 1, salesperson_name: 'Test', total_collected: 100 }]
        })
      });
    });

    // Bypass login by setting localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('branchId', '1');
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
    await expect(page.locator('.card-body').first()).toBeVisible();
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
    await expect(page.locator('.card-body .fw-bold').first()).toBeVisible();
  });

  test('Inventory Movement Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/inventory');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('table th')).toHaveCount(10);
  });

  test('Salesperson Performance Report tab loads successfully', async ({ page }) => {
    await page.goto('/reports/salesperson');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
    await expect(page.locator('.card-body .fw-bold.fs-3')).toHaveCount(4);
    await expect(page.locator('table th')).toHaveCount(9);
  });
});
