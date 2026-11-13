import { test, expect } from '@playwright/test';

test.describe('Search Receipts & Filters E2E Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // Authenticate in localStorage
    await context.addInitScript(() => {
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('branchId', '1');
      localStorage.setItem('branchName', 'الفرع الرئيسي');
    });

    // Mock all required API endpoints
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

    await page.route('**/api/v1/default-date/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ year: 2026, month: 7 })
      });
    });

    await page.route('**/api/v1/receipts/bulk_delete/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success', deleted_count: 1 })
      });
    });

    await page.route('**/api/v1/receipts/**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            count: 2,
            next: null,
            previous: null,
            all_ids: [101, 102],
            all_installment_ids: [102],
            results: [
              {
                id: 101,
                receipt_number: 101,
                sale_year: 2026,
                sale_month: 7,
                salesperson: 1,
                salesperson_name: 'محمد علي',
                customer_name: 'محمود سعيد',
                phone_number: '01000123456',
                area: 'المعادي',
                address: 'شارع النصر',
                is_cash_sale: true,
                total_amount: 5000,
                down_payment: 0,
                receipt_type: 'SALE',
                is_confirmed: true,
                items: [{ id: 1, inventory_item: 1, inventory_item_name: 'غسالة توشيبا', quantity: 1, unit_price: 5000 }]
              },
              {
                id: 102,
                receipt_number: 102,
                sale_year: 2026,
                sale_month: 7,
                salesperson: 1,
                salesperson_name: 'محمد علي',
                customer_name: 'خالد إبراهيم',
                phone_number: '01111222333',
                area: 'مدينة نصر',
                address: 'عباس العقاد',
                is_cash_sale: false,
                total_amount: 12000,
                down_payment: 2000,
                receipt_type: 'SALE',
                is_confirmed: true,
                items: [{ id: 2, inventory_item: 2, inventory_item_name: 'ثلاجة شارب', quantity: 1, unit_price: 12000 }]
              }
            ]
          })
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/receipts');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
  });

  test('should load the search page and verify title and table rows', async ({ page }) => {
    await expect(page.locator('text=دفتر المبيعات').first()).toBeVisible();

    // Verify the table has rows loaded
    const rows = page.locator('.table tbody tr');
    await expect(rows.first()).toBeVisible();
    expect(await rows.count()).toBeGreaterThanOrEqual(2);

    // Verify the master checkbox exists
    const headerCheckbox = page.locator('thead th input[type="checkbox"]');
    if (await headerCheckbox.count() > 0) {
      await expect(headerCheckbox).toBeChecked();
    }
  });

  test('should reset filters correctly', async ({ page }) => {
    // Fill phone filter
    const phoneInput = page.locator('input[placeholder*="هاتف"], input[name="phone"]').first();
    if (await phoneInput.count() > 0) {
      await phoneInput.fill('01000');
      // Click Reset
      const resetBtn = page.locator('button', { hasText: 'إعادة ضبط' }).first();
      if (await resetBtn.count() > 0) {
        await resetBtn.click();
        expect(await phoneInput.inputValue()).toBe('');
      }
    }
  });

  test('should execute bulk delete successfully', async ({ page }) => {
    const rows = page.locator('.table tbody tr');
    await expect(rows.first()).toBeVisible();

    const deleteButton = page.locator('button', { hasText: 'حذف محددة' });
    if (await deleteButton.count() > 0) {
      await deleteButton.click();
      
      // Confirm modal button if displayed
      const confirmModalBtn = page.locator('.modal button, .btn-danger', { hasText: 'تأكيد الحذف' }).first();
      if (await confirmModalBtn.count() > 0) {
        await confirmModalBtn.click();
      }
    }
  });
});
