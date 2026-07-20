import { chromium } from 'playwright';
import fs from 'fs';

const routes = [
  '/',
  '/pos',
  '/receipts',
  '/inventory',
  '/search-purchases',
  '/purchases/new',
  '/expenses',
  '/reports/dashboard',
  '/reports/receipts',
  '/reports/expenses',
  '/reports/salesperson',
  '/reports/inventory',
  '/reports/profit-and-loss',
  '/reports/cash-drawer',
  '/reports/installments',
  '/settings'
];

(async () => {
  console.log("Launching browser for full site test...");
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Array to collect console errors
  const errors = [];
  page.on('pageerror', err => {
    errors.push(`Page Error: ${err.message}`);
  });
  page.on('console', msg => {
    if (msg.type() === 'error' && !msg.text().includes('favicon')) {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });

  try {
    console.log("Navigating to root for auto-login...");
    await page.goto('http://localhost:5173/');
    
    console.log("Waiting for /select-branch redirect...");
    await page.waitForURL('**/select-branch', { timeout: 15000 });
    
    console.log("Clicking 'الفرع الرئيسي'...");
    await page.click('text="الفرع الرئيسي"');
    
    console.log("Waiting for dashboard...");
    await page.waitForURL('**/', { timeout: 15000 });
    
    console.log("Login successful! Starting page traversal...");
    
    let results = "Test Results:\n===================\n";
    
    for (const route of routes) {
      console.log(`Testing ${route}...`);
      errors.length = 0; // Clear previous errors
      
      try {
        await page.goto(`http://localhost:5173${route}`);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1500); // Wait for React to render
        
        // Check for common error texts on screen
        const bodyText = await page.innerText('body');
        if (bodyText.includes('Internal Server Error') || bodyText.includes('TypeError') || bodyText.includes('Something went wrong')) {
          results += `[FAIL] ${route} -> Rendered Error Text on screen.\n`;
        } else if (errors.length > 0) {
          results += `[FAIL] ${route} -> Console/Page Errors: ${errors[0]}\n`;
        } else {
          results += `[PASS] ${route}\n`;
        }
      } catch (err) {
        results += `[FAIL] ${route} -> Exception: ${err.message}\n`;
      }
    }
    
    fs.writeFileSync('test_results.txt', results);
    console.log("Testing complete! Results saved to test_results.txt.");
    console.log(results);
    
  } catch (err) {
    console.error("Test suite failed:", err);
  } finally {
    await browser.close();
  }
})();
