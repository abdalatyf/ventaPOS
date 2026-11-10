import { test, expect } from '@playwright/test';

test.describe('Return Logic End-to-End Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // Authenticate in localStorage
    await context.addInitScript(() => {
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('branchId', '1');
      localStorage.setItem('branchName', 'الفرع الرئيسي');
    });

    await page.route('**/api/v1/frontend-logs/**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
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

    await page.route('**/api/v1/receipts/101/**', async (route) => {
      if (route.request().url().includes('return_receipt')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'success', return_receipt_id: 102 })
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
          has_returns: false,
          sale_items: [
            {
              id: 1,
              inventory_item: 1,
              product_name: 'غسالة توشيبا 10 كيلو',
              quantity: 2,
              unit_price: 2500
            }
          ]
        })
      });
    });
  });

  test('تحميل صفحة استرجاع الفاتورة وعرض بيانات الأصناف', async ({ page }) => {
    await page.goto('/receipts/return/101');
    await expect(page.locator('.spinner-border')).not.toBeVisible();

    await expect(page.locator('text=غسالة توشيبا 10 كيلو').first()).toBeVisible();
    await expect(page.locator('td', { hasText: '2' }).first()).toBeVisible();
    await expect(page.locator('text=تحديد الأصناف المسترجعة')).toBeVisible();
  });

  test('زيادة ونقصان كمية المرتجع وتحديث إجمالي المرتجع', async ({ page }) => {
    await page.goto('/receipts/return/101');
    await expect(page.locator('.spinner-border')).not.toBeVisible();

    const incBtn = page.locator('button:has-text("+")').first();
    const decBtn = page.locator('button:has-text("-")').first();
    const qtyInput = page.locator('table input[type="text"]').first();

    // Initial return quantity is 0
    await expect(qtyInput).toHaveValue('0');

    // Click increment (+) -> 1
    await incBtn.dispatchEvent('click');
    await expect(qtyInput).toHaveValue('1');
    await expect(page.locator('text=2,500 ج.م').first()).toBeVisible();

    // Click increment (+) -> 2 (sold quantity)
    await incBtn.dispatchEvent('click');
    await expect(qtyInput).toHaveValue('2');
    await expect(page.locator('text=5,000 ج.م').first()).toBeVisible();

    // Click increment (+) again -> should stay at 2 (max clamp)
    await incBtn.dispatchEvent('click');
    await expect(qtyInput).toHaveValue('2');

    // Click decrement (-) -> 1
    await decBtn.dispatchEvent('click');
    await expect(qtyInput).toHaveValue('1');
    await expect(page.locator('text=2,500 ج.م').first()).toBeVisible();
  });

  test('تأكيد المرتجع بنجاح وإعادة التوجيه إلى دفتر المبيعات', async ({ page }) => {
    await page.goto('/receipts/return/101');
    await expect(page.locator('.spinner-border')).not.toBeVisible();

    // Increment return qty to 1
    await page.locator('button:has-text("+")').first().dispatchEvent('click');

    // Click "تأكيد المرتجع"
    const confirmBtn = page.locator('button', { hasText: 'تأكيد المرتجع' });
    await expect(confirmBtn).toBeEnabled();

    await Promise.all([
      page.waitForRequest(req => req.url().includes('/return_receipt/') && req.method() === 'POST'),
      confirmBtn.click()
    ]);

    await expect(page).toHaveURL(/.*\/receipts/);
  });
});
