import { test, expect } from '@playwright/test';

test.describe('POS Page - Core Features & Cart E2E Tests', () => {
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

    await page.route('**/api/v1/receipts-next-number/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ next_receipt_number: 105 })
      });
    });

    await page.route('**/api/v1/inventory-items/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'باركية خشب فاخر', safe_available_qty: 20, initial_purchase_price: 500 }
        ])
      });
    });

    await page.route('**/api/v1/customer-suggestions/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { name: 'محمود سعيد', phone: '01000123456', area: 'المعادي', address: 'شارع النصر' }
        ])
      });
    });

    await page.route('**/api/v1/product-suggestions/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, value: 'باركية خشب فاخر', safe_available_qty: 20, current_price: 500 }
        ])
      });
    });

    await page.route('**/api/v1/receipts/**', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ id: 105, receipt_number: 105 })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ count: 0, results: [] })
        });
      }
    });

    await page.goto('/pos');
    await expect(page.locator('.spinner-border')).not.toBeVisible();
  });

  test('يجب أن تحتوي الصفحة على الحقول الأساسية المحملة', async ({ page }) => {
    await expect(page.locator('label', { hasText: 'الشهر' })).toBeVisible();
    await expect(page.locator('label', { hasText: 'السنة' })).toBeVisible();
    await expect(page.locator('label', { hasText: 'المندوب' })).toBeVisible();
    await expect(page.locator('#input_name')).toBeVisible();
    await expect(page.locator('#input_phone')).toBeVisible();
  });

  test('تفعيل تبديل "كاش" يخفي بيانات العميل ونظام التقسيط ويعيد إظهارها عند اختيار "قسط"', async ({ page }) => {
    const cashBtn = page.locator('button', { hasText: 'كاش' });
    const installmentBtn = page.locator('button', { hasText: 'قسط' });

    // Switch to Cash
    await cashBtn.click();
    await expect(page.locator('#input_name')).toBeHidden();
    await expect(page.locator('text=كاش — لا توجد أقساط ومقدم')).toBeVisible();

    // Switch back to Installments
    await installmentBtn.click();
    await expect(page.locator('#input_name')).toBeVisible();
    await expect(page.locator('text=كاش — لا توجد أقساط ومقدم')).toBeHidden();
  });

  test('إضافة صنف للسلة والتأكد من نزوله في الجدول وتحديث الإجمالي', async ({ page }) => {
    const prodInput = page.locator('.row.mb-4 input[type="text"]').first();
    await prodInput.fill('باركية خشب فاخر');

    const qtyInput = page.locator('.row.mb-4 input[inputmode="numeric"]').first();
    await qtyInput.fill('2');

    const priceInput = page.locator('.row.mb-4 input[inputmode="numeric"]').nth(1);
    await priceInput.fill('500');

    const addBtn = page.locator('.row.mb-4 button', { hasText: '+' });
    await addBtn.click();

    const tableRow = page.locator('table tbody tr').first();
    await expect(tableRow).toBeVisible();
    await expect(tableRow).toContainText('2');
    await expect(tableRow).toContainText('500');

    await expect(page.locator('.text-success.fs-3', { hasText: '1,000' })).toBeVisible();
  });

  test('حفظ الفاتورة الكاش بنجاح وإعادة تعيين السلة', async ({ page }) => {
    // Select salesperson
    const spInput = page.locator('input[placeholder="ابحث عن مندوب..."]').first();
    await spInput.fill('محمد علي');
    const spSuggestion = page.locator('.list-group button, .list-group-item', { hasText: 'محمد علي' }).first();
    if (await spSuggestion.count() > 0) {
      await spSuggestion.click();
    }

    // Switch to Cash mode
    await page.locator('button', { hasText: 'كاش' }).click();

    const prodInput = page.locator('.row.mb-4 input[type="text"]').first();
    await prodInput.fill('باركية خشب فاخر');

    const qtyInput = page.locator('.row.mb-4 input[inputmode="numeric"]').first();
    await qtyInput.fill('1');

    const priceInput = page.locator('.row.mb-4 input[inputmode="numeric"]').nth(1);
    await priceInput.fill('1500');

    await page.locator('.row.mb-4 button', { hasText: '+' }).click();
    await expect(page.locator('table tbody tr').first()).toBeVisible();

    const confirmBtn = page.locator('button', { hasText: 'تأكيد البيع' });
    await expect(confirmBtn).toBeEnabled();

    // Click confirm and wait for successful POST
    await Promise.all([
      page.waitForRequest(req => req.url().includes('/api/v1/receipts/') && req.method() === 'POST'),
      confirmBtn.click()
    ]);

    // Cart is reset
    await expect(page.locator('text=لا توجد أصناف مضافة')).toBeVisible();
  });
});
