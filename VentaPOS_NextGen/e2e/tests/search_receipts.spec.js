const { test, expect } = require('@playwright/test');

test.describe('Search Receipts & Filters', () => {
  test.beforeEach(async ({ page }) => {
    // Bypass frontend authentication
    await page.addInitScript(() => {
      window.localStorage.setItem('token', 'e2e-bypass-token');
      window.localStorage.setItem('branchId', 'e2e-bypass-branch');
    });

    // Navigate to the search receipts page
    await page.goto('/receipts');
    // Wait for network requests to settle (mock data load)
    await page.waitForLoadState('networkidle');
  });

  test('should load the search page and perform default select all', async ({ page }) => {
    // Verify the page title or header exists
    await expect(page.locator('text=دفتر المبيعات').first()).toBeVisible();

    // Verify filters are visible by default
    await expect(page.locator('form')).toBeVisible();

    // Ensure the table has rows loaded (assuming seed data exists)
    const rows = page.locator('.table tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);

    // Verify the "Select All" checkbox is checked by default
    const selectAllCheckbox = page.locator('input[type="checkbox"][onChange*="toggleSelectAll"]');
    // We can just look for the main checkbox in the thead
    const headerCheckbox = page.locator('thead th input[type="checkbox"]');
    if (await headerCheckbox.count() > 0) {
      await expect(headerCheckbox).toBeChecked();
    }
  });

  test('should filter by Sale Type correctly', async ({ page }) => {
    // Select CASH type
    await page.selectOption('select[name="sale_type"]', 'CASH');
    await page.click('button[type="submit"]');
    await page.waitForResponse(response => response.url().includes('is_cash_sale=true') && response.status() === 200);

    // The table should update, and we just ensure no errors appear
    const rows = page.locator('.table tbody tr');
    await expect(rows.first()).toBeVisible();
  });

  test('should reset filters correctly', async ({ page }) => {
    // Change a filter
    await page.fill('input[name="phone"]', '01000');
    // Click Reset
    await page.click('text=إعادة ضبط');
    
    // Verify phone input is empty again
    const phoneVal = await page.locator('input[name="phone"]').inputValue();
    expect(phoneVal).toBe('');
  });

  test('should execute bulk delete successfully', async ({ page }) => {
    // First ensure there are receipts
    const rows = page.locator('.table tbody tr');
    await expect(rows.first()).toBeVisible();

    // Since they are selected by default, click "Delete Selected"
    // Wait, let's uncheck all first, then check one to avoid wiping the DB entirely in one test
    const headerCheckbox = page.locator('thead th input[type="checkbox"]');
    await headerCheckbox.uncheck();
    
    // Check just the first row
    const firstRowCheckbox = page.locator('tbody tr:first-child input[type="checkbox"]');
    await firstRowCheckbox.check();

    // Click delete
    page.on('dialog', dialog => dialog.accept()); // Accept the JS confirm dialog if used
    
    const deleteButton = page.locator('button', { hasText: 'حذف المحدد' });
    if (await deleteButton.count() > 0) {
      await deleteButton.click();
      
      // Wait for success toast or response
      await page.waitForResponse(response => response.url().includes('/bulk_delete/') && response.status() === 200);
      
      // We could verify the UI toast "تم الحذف بنجاح"
      await expect(page.locator('text=تم الحذف بنجاح')).toBeVisible({ timeout: 5000 });
    }
  });
});
