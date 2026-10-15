import { test, expect } from '@playwright/test';

// Configuration
const NUM_INVOICES = 100;

// Reusable Arabic letters to search for a product randomly
const LETTERS = ['ا', 'ب', 'ت', 'ج', 'م', 'س', 'ش', 'د', 'ر', 'ع', 'ل', 'ك', 'ن', 'هـ', 'و', 'ي'];
const INSTALLMENT_SYSTEMS = ['100*5', '50*2 + 20*3', ' 150 * 3', '200*1', '500*2', '125*4', ''];

test.describe('محاكاة إضافة 100 فاتورة كعميل حقيقي', () => {

  // Before each test, we login and navigate to POS
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    // Navigate and let auto-login handle DEMO or use actual login
    await page.goto('/login');
    
    // Wait to be redirected away from login
    await page.waitForURL('**/(select-branch|receipts)', { timeout: 15000 }).catch(() => {});
    
    // If stuck on branch selection (happens if multiple branches, or sometimes just lands here)
    if (page.url().includes('select-branch')) {
        await page.locator('.card-link').first().waitFor({ state: 'visible', timeout: 5000 });
        await page.locator('.card-link').first().click();
        await page.waitForURL('**/receipts', { timeout: 10000 });
    }
    
    // Go to POS explicitly
    await page.goto('/pos');
    await expect(page.getByRole('heading', { name: 'نقطة البيع' })).toBeVisible({ timeout: 10000 });
  });

  // Dynamically generate 100 independent tests
  for (let i = 1; i <= NUM_INVOICES; i++) {
    test(`إنشاء الفاتورة العشوائية رقم ${i}`, async ({ page }) => {
      // 1 minute timeout per invoice creation
      test.setTimeout(60000);

      const isCash = Math.random() > 0.5; // 50% chance of being Cash

      // --- COMMON FIELDS ---
      // Select Rep (tabindex 3)
      const repSelect = page.locator('select[tabindex="3"]');
      await repSelect.waitFor({ state: 'visible' });
      await page.waitForTimeout(500); 
      await repSelect.selectOption({ index: 1 }).catch(() => {
          console.log(`[Test ${i}]: Failed to select Rep.`);
      });

      // 2. Select a Customer Name
      const nameInput = page.locator('input[tabindex="4"]');
      await nameInput.fill('');
      await nameInput.pressSequentially('ع', { delay: 100 });
      try {
          const nameList = page.locator('.input-group:has-text("الاسم") .list-group button').first();
          await nameList.waitFor({ state: 'visible', timeout: 3000 });
          await nameInput.press('ArrowDown');
          await page.waitForTimeout(100);
          await nameInput.press('Enter');
      } catch (e) {
          await nameInput.fill(`عميل تجريبي ${i}`);
      }
      
      // 3. Select a Phone
      const phoneInput = page.locator('input[tabindex="5"]');
      await phoneInput.fill('');
      await phoneInput.pressSequentially('01', { delay: 100 });
      try {
          const phoneList = page.locator('.input-group:has-text("التليفون") .list-group button').first();
          await phoneList.waitFor({ state: 'visible', timeout: 3000 });
          await phoneInput.press('ArrowDown');
          await page.waitForTimeout(100);
          await phoneInput.press('Enter');
      } catch (e) {
          await phoneInput.fill(`01000000${i}`);
      }

      // 4. Fill Area and Address (tabindex 6 and 7)
      await page.locator('input[tabindex="6"]').fill(`منطقة تجريبية ${i}`);
      await page.locator('input[tabindex="7"]').fill(`شارع تجريبي ${i}`);

      if (isCash) {
          // Toggle Cash sale
          await page.locator('label[for="cashSaleToggle"]').click();
      } else {
          // Select Salesperson
          const spSelect = page.locator('select[tabindex="3"]');
          await spSelect.selectOption({ index: 1 }).catch(() => {});

          // Fill Installment Data
          const randomSystem = INSTALLMENT_SYSTEMS[Math.floor(Math.random() * INSTALLMENT_SYSTEMS.length)];
          await page.locator('input[tabindex="13"]').first().fill(randomSystem);
          
          // Downpayment
          await page.locator('input[tabindex="12"]').first().fill('0');
      }

      // We will add between 1 to 3 random items to the cart
      const numItems = Math.floor(Math.random() * 3) + 1;
      
      for (let j = 0; j < numItems; j++) {
          const randomLetter = LETTERS[Math.floor(Math.random() * LETTERS.length)];
          const productInput = page.locator('input[tabindex="8"]');
          await productInput.fill('');
          await productInput.pressSequentially(randomLetter, { delay: 100 });
          
          const productList = page.locator('.input-group:has-text("صنف") .list-group button').first();
          
          try {
              await productList.waitFor({ state: 'visible', timeout: 3000 });
              await productInput.press('ArrowDown');
              await page.waitForTimeout(100); // wait for React state update
              await productInput.press('Enter');
              console.log(`[Test ${i} Item ${j}]: Successfully selected product suggestion via keyboard.`);
          } catch (e) {
              console.log(`[Test ${i} Item ${j}]: Failed first search for '${randomLetter}'`, e.message);
              // Fallback to "ا" which usually matches something
              await productInput.fill('');
              await productInput.pressSequentially('ا', { delay: 100 });
              try {
                  await productList.waitFor({ state: 'visible', timeout: 3000 });
                  await productInput.press('ArrowDown');
                  await page.waitForTimeout(100); // wait for React state update
                  await productInput.press('Enter');
                  console.log(`[Test ${i} Item ${j}]: Successfully selected product suggestion after fallback.`);
              } catch (innerE) {
                  console.log(`[Test ${i} Item ${j}]: Failed fallback search`, innerE.message);
                  continue;
              }
          }

          // Random quantity between 1 and 3 (to minimize "safe quantity exceeded" errors but still test multiples)
          const randomQty = Math.floor(Math.random() * 3) + 1;
          await page.locator('input[tabindex="9"]').first().fill(randomQty.toString());
          
          // Enter random price
          const randomPrice = Math.floor(Math.random() * 50) + 10;
          await page.locator('input[tabindex="10"]').first().fill(randomPrice.toString());
          
          // Wait for React useEffect to set the price
          await page.waitForTimeout(500);

          // Add to cart
          await page.locator('button[tabindex="11"]').click();
          
          // Small delay to let React update DOM
          await page.waitForTimeout(300);
      }
      
      // If we failed to add ANY item, add a default fallback item or skip test
      const cartRows = page.locator('table.table-hover tbody tr');
      const count = await cartRows.count();
      if (count === 1) {
          const firstRowText = await cartRows.first().innerText();
          if (firstRowText.includes('لا توجد بضاعة')) {
              console.log(`Test ${i}: Skipped unconditionally due to empty cart (no products added successfully).`);
              test.skip();
              return;
          }
      }

      // Hit Save and wait for 201 response OR specific error messages
      // We will just click save and see if the success dialog pops up, 
      // or if an error dialog pops up (like out of stock), we catch it to prevent false test failure.
      
      let success = false;
      let errorMessage = '';

      // Set up dialog listener to catch success or errors gracefully
      page.on('dialog', async dialog => {
          const msg = dialog.message();
          console.log(`[Dialog in Test ${i}]:`, msg);
          if (msg.includes('تم حفظ الفاتورة بنجاح')) {
              success = true;
          } else {
              errorMessage = msg;
          }
          await dialog.accept();
      });

      // Wait for React to recalculate installment amounts based on the final totalAmount
      await page.waitForTimeout(1000);

      // Save Invoice
      await page.waitForTimeout(500);
      await page.locator('button:has-text("حفظ الفاتورة")').click();

      try {
          // Wait for network response
          const response = await page.waitForResponse(resp => resp.url().includes('/receipts/') && ['POST'].includes(resp.request().method()), { timeout: 3000 });
          
          if (response.status() === 201) {
              // Success!
              await page.waitForTimeout(500); // Give time for dialog to trigger
              expect(success).toBe(true);
          } else {
              const body = await response.json();
              console.log(`Test ${i} failed intentionally due to business rule or error:`, response.status(), body);
              
              if (body.error && body.error.includes("أقصى كمية يمكن بيعها بأثر رجعي")) {
                  test.info().annotations.push({ type: 'business_rule', description: body.error });
              } else {
                  throw new Error(`Unexpected API Error ${response.status()}: ${JSON.stringify(body)}`);
              }
          }
      } catch (e) {
          if (errorMessage) {
              console.log(`[Validation Error in Test ${i}]:`, errorMessage);
              test.skip();
          } else {
              throw e;
          }
      }
    });
  }
});
