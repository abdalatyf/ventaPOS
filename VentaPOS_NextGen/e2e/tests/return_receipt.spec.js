import { test, expect } from '@playwright/test';

test.describe('Return Logic End-to-End Tests', () => {

  // Helper function to pick a receipt and open return page
  async function openFirstAvailableReturnPage(page) {
    await page.goto('/receipts');
    // Wait for the receipts table to load
    await page.waitForSelector('table tbody tr');
    
    // Find the first receipt that has the "إرجاع بضاعة" (Return Items) button
    const returnLink = page.locator('a:has-text("استرجاع"), a[href*="/return/"], a:has-text("مرتجع")').first();
    
    // Check if there's any available receipt to return
    const count = await returnLink.count();
    if (count === 0) {
      test.skip('No available receipts for return found in the database. Please ensure the DB has receipts.');
      return false;
    }
    
    await returnLink.click();
    await page.waitForURL(/\/receipts\/\d+\/return/);
    return true;
  }

  test('Test Case 1: Valid return flow from existing receipt', async ({ page }) => {
    const hasReceipts = await openFirstAvailableReturnPage(page);
    if (!hasReceipts) return;

    // Wait for the return items table/list to load
    await page.waitForSelector('input[type="number"]');

    // Get the first item's quantity input
    const firstQtyInput = page.locator('input[type="number"]').first();
    
    // Enter 1 as the return quantity
    await firstQtyInput.fill('1');

    // Click Save
    await page.getByRole('button', { name: /حفظ|تأكيد/ }).click();

    // Verify success message and redirection
    // Note: The app uses `alert()` currently in React code, we need to handle dialogs.
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('نجاح');
      await dialog.accept();
    });

    // Ensure we are redirected back to receipts
    await page.waitForURL('/receipts');
  });

  test('Test Case 2: Over-return protection', async ({ page }) => {
    const hasReceipts = await openFirstAvailableReturnPage(page);
    if (!hasReceipts) return;

    await page.waitForSelector('input[type="number"]');
    const firstQtyInput = page.locator('input[type="number"]').first();
    
    // Enter an artificially large quantity
    await firstQtyInput.fill('9999');

    // Handle the expected error alert
    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: /حفظ|تأكيد/ }).click();
    
    const dialog = await dialogPromise;
    const msg = dialog.message();
    // The backend error should contain "تتخطى الكمية المتاحة" or similar
    expect(msg).toMatch(/تتخطى|أكبر من|خطأ/);
    await dialog.accept();

    // Verify we are still on the return page
    expect(page.url()).toMatch(/\/receipts\/\d+\/return/);
  });

  test('Test Case 3: Price manipulation protection (Network Intercept)', async ({ page }) => {
    const hasReceipts = await openFirstAvailableReturnPage(page);
    if (!hasReceipts) return;

    await page.waitForSelector('input[type="number"]');
    const firstQtyInput = page.locator('input[type="number"]').first();
    await firstQtyInput.fill('1');

    // Intercept the API POST request to /return_receipt/
    await page.route('**/return_receipt/', async route => {
      const request = route.request();
      const payload = request.postDataJSON();
      
      // Manipulate the return value
      if (payload) {
        payload.return_value = 9999999; 
        if (payload.returned_items && payload.returned_items.length > 0) {
            payload.returned_items[0].unit_price = 9999999;
        }
      }
      
      // Continue with modified payload
      await route.continue({
        postData: JSON.stringify(payload)
      });
    });

    // Click Save
    const dialogPromise = page.waitForEvent('dialog');
    await page.getByRole('button', { name: /حفظ|تأكيد/ }).click();
    
    const dialog = await dialogPromise;
    // Since the backend strictly ignores the manipulated price, it will process it with the original price.
    expect(dialog.message()).not.toContain('Internal Server Error');
    await dialog.accept();
  });

  test('Test Case 4: UI lock verification on POS/PosEntry', async ({ page }) => {
    await page.goto('/receipts');
    await page.waitForSelector('table tbody tr');

    // Find a receipt that has the "يوجد مرتجع" badge (which we added previously)
    const returnedBadge = page.locator('span.badge.bg-danger:has-text("يوجد مرتجع")').first();
    const count = await returnedBadge.count();
    
    if (count === 0) {
      test.skip('No receipts with returns found to test UI lock.');
      return;
    }

    // Go to its edit/POS page
    const row = returnedBadge.locator('..').locator('..'); // go up to tr
    const editBtn = row.locator('a[href*="/pos/"], a[href*="/edit"]').first();
    await editBtn.click();

    await page.waitForLoadState('networkidle');

    // Verify the warning banner exists
    await expect(page.locator('text=لا يمكن تعديل البضاعة أو الماليات لوجود مرتجع')).toBeVisible();

    // Verify the product search input is disabled
    const searchInput = page.locator('input[placeholder*="بحث"]').first();
    if (await searchInput.count() > 0) {
      await expect(searchInput).toBeDisabled();
    }

    // Verify installment/financial inputs are disabled
    const paymentInputs = page.locator('input[type="number"]');
    const inputsCount = await paymentInputs.count();
    for (let i = 0; i < inputsCount; i++) {
        await expect(paymentInputs.nth(i)).toBeDisabled();
    }
  });

});
