import { chromium } from 'playwright';

(async () => {
  console.log("Launching browser...");
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  console.log("Navigating to http://localhost:5173...");
  await page.goto('http://localhost:5173/');
  
  console.log("Waiting for network to be idle...");
  await page.waitForLoadState('networkidle');
  
  console.log("Waiting an additional 5 seconds for React/Charts to render...");
  await page.waitForTimeout(5000);
  
  console.log("Taking screenshot...");
  await page.screenshot({ path: 'dashboard.png', fullPage: true });
  
  console.log("Screenshot saved as dashboard.png.");
  await browser.close();
})();
