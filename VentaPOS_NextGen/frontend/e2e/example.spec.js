import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/VentaPOS/i);
});

test('login page loads', async ({ page }) => {
  await page.goto('/login');

  // Verify that there is a login form or heading
  await expect(page.getByRole('heading', { name: /تسجيل الدخول/i })).toBeVisible();
});
