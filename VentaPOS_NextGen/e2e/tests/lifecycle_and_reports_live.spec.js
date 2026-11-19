const { test, expect } = require('@playwright/test');
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const { spawn, execFileSync, spawnSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const BACKEND_DIR = path.join(REPO_ROOT, 'backend');
const VENV_PYTHON = path.join(REPO_ROOT, 'venv', 'Scripts', 'python.exe');
const BACKEND_BASE = 'http://127.0.0.1:8000';

let tempDir = null;
let serverProc = null;
let sharedContext = null;
let sharedPage = null;
let monitors = null;
let mintedLicenses = null;
const liveIds = {};

function checkPortFree(port, host = '127.0.0.1') {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once('error', (err) => reject(new Error(`Port ${host}:${port} is already in use: ${err.message}`)));
    srv.once('listening', () => srv.close(() => resolve()));
    srv.listen(port, host);
  });
}

async function waitForServerReady(url, proc, stderrChunks, timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (proc.exitCode !== null) {
      throw new Error(
        `Django test server exited early with code ${proc.exitCode}.\nStderr:\n${stderrChunks.join('')}`
      );
    }
    try {
      const res = await fetch(url);
      if (res.status === 200) return;
    } catch {
      // keep polling
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`Timed out waiting for Django test server at ${url}`);
}

async function stopProcessTree(proc) {
  if (!proc || proc.exitCode !== null) return;
  if (process.platform === 'win32') {
    spawnSync('taskkill', ['/PID', String(proc.pid), '/T', '/F'], {
      stdio: 'ignore',
      windowsHide: true,
    });
  } else {
    try {
      proc.kill('SIGTERM');
    } catch {
      // ignore
    }
  }
  const waitStart = Date.now();
  while (proc.exitCode === null && Date.now() - waitStart < 5000) {
    await new Promise((r) => setTimeout(r, 100));
  }
}

async function removeTempDirSafe(dirPath) {
  if (!dirPath || !fs.existsSync(dirPath)) return;
  for (let attempt = 0; attempt < 20; attempt++) {
    try {
      fs.rmSync(dirPath, { recursive: true, force: true });
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 250));
    }
  }
}

function attachRuntimeMonitors(page) {
  const state = { pageErrors: [], consoleErrors: [], serverErrors: [] };
  page.on('pageerror', (err) => state.pageErrors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      state.consoleErrors.push(msg.text());
    }
  });
  page.on('response', (res) => {
    if (res.status() >= 500 || res.status() === 403) {
      state.serverErrors.push(`${res.status()} ${res.url()}`);
    }
  });
  return state;
}

function resetMonitors() {
  if (!monitors) return;
  monitors.pageErrors.length = 0;
  monitors.consoleErrors.length = 0;
  monitors.serverErrors.length = 0;
}

function assertCleanRuntime() {
  expect(monitors.serverErrors).toEqual([]);
  expect(monitors.pageErrors).toEqual([]);
  expect(monitors.consoleErrors).toEqual([]);
}

async function fillLicenseKeySegments(page, licenseCode) {
  const parts = licenseCode.split('-');
  expect(parts).toHaveLength(4);
  const inputs = page.locator('input[placeholder="XXXX"]');
  await expect(inputs).toHaveCount(4);
  for (let i = 0; i < 4; i++) {
    await inputs.nth(i).fill(parts[i]);
  }
}

test.describe.serial('Wave 4 Zero-Mock Full Lifecycle, Print-Only, Backup & Report Print Live E2E', () => {
  test.setTimeout(120000);

  test.beforeAll(async ({ browser }) => {
    await checkPortFree(8000, '127.0.0.1');
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ventapos-w4-live-'));

    try {
      const e2eSettingsContent = `
import os
from pathlib import Path
from backend.settings import *

TEMP_DB_DIR = Path(os.environ['VENTAPOS_E2E_TEMP_DIR'])
DB_DIR = TEMP_DB_DIR
MEDIA_ROOT = str(TEMP_DB_DIR / 'media')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(TEMP_DB_DIR / 'e2e_db.sqlite3'),
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    }
}
if 'LOGGING' in globals() and 'handlers' in LOGGING and 'file' in LOGGING['handlers']:
    LOGGING['handlers']['file']['filename'] = str(TEMP_DB_DIR / 'e2e_system.log')
`;
      fs.writeFileSync(path.join(tempDir, 'e2e_settings.py'), e2eSettingsContent, 'utf-8');

      const childEnv = {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
        VENTAPOS_E2E_TEMP_DIR: tempDir,
        DJANGO_SETTINGS_MODULE: 'e2e_settings',
        PYTHONPATH: `${BACKEND_DIR}${path.delimiter}${tempDir}`,
      };

      execFileSync(VENV_PYTHON, ['manage.py', 'migrate', '--noinput'], {
        cwd: BACKEND_DIR,
        env: childEnv,
        stdio: 'pipe',
      });

      execFileSync(VENV_PYTHON, ['manage.py', 'init_demo_db'], {
        cwd: BACKEND_DIR,
        env: childEnv,
        stdio: 'pipe',
      });

      const mintScript = `
import json, django
django.setup()
from api.utils.security_utils import get_machine_id
from api.tests.test_licensing_and_security import mint_test_license_code

mach = get_machine_id()
print(json.dumps({
    'machineId': mach,
    'stdYear1': mint_test_license_code(mach, 4, 2026, 1),
    'renewYear2': mint_test_license_code(mach, 4, 2027, 1),
    'printOnlyYear': mint_test_license_code(mach, 2, 2028, 1),
    'recoveryCode': mint_test_license_code(mach, 16, 2026, 1),
}))
`;
      const mintOut = execFileSync(VENV_PYTHON, ['-c', mintScript], {
        cwd: BACKEND_DIR,
        env: childEnv,
        encoding: 'utf-8',
      });
      const lines = mintOut.trim().split(/\r?\n/);
      mintedLicenses = JSON.parse(lines[lines.length - 1]);

      const stderrChunks = [];
      serverProc = spawn(
        VENV_PYTHON,
        ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'],
        {
          cwd: BACKEND_DIR,
          env: childEnv,
          stdio: ['ignore', 'pipe', 'pipe'],
          windowsHide: true,
        }
      );
      serverProc.stderr.on('data', (chunk) => stderrChunks.push(chunk.toString()));

      await waitForServerReady(`${BACKEND_BASE}/api/v1/license/status/`, serverProc, stderrChunks);

      sharedContext = await browser.newContext();
      sharedPage = await sharedContext.newPage();
      monitors = attachRuntimeMonitors(sharedPage);
    } catch (err) {
      if (sharedContext) await sharedContext.close().catch(() => {});
      await stopProcessTree(serverProc);
      await removeTempDirSafe(tempDir);
      throw err;
    }
  });

  test.afterAll(async () => {
    if (sharedContext) await sharedContext.close().catch(() => {});
    await stopProcessTree(serverProc);
    await new Promise((r) => setTimeout(r, 300));
    await removeTempDirSafe(tempDir);
  });

  test('1. Demo Mode boot -> DemoBanner -> Activate Standard License wipes demo DB cleanly', async () => {
    resetMonitors();
    const page = sharedPage;

    await page.goto('/');
    // Demo auto-login lands on /select-branch or directly /receipts
    await expect(page).toHaveURL(/\/(select-branch|receipts)/, { timeout: 15000 });
    if (page.url().includes('/select-branch')) {
      // SelectBranch may auto-redirect to /receipts when only 1 branch exists
      await Promise.race([
        page.waitForURL(/\/receipts/, { timeout: 15000 }),
        page.locator('.card.cursor-pointer').first().click({ timeout: 15000 }).catch(() => {}),
      ]);
      await expect(page).toHaveURL(/\/receipts/, { timeout: 15000 });
    }

    // DemoBanner should be visible with Activate button
    const activateBannerBtn = page.getByRole('button', { name: 'تفعيل البرنامج' });
    await expect(activateBannerBtn).toBeVisible();
    await expect(page.getByRole('button', { name: 'استعادة نسخة احتياطية' })).toBeVisible();

    // Navigate to subscription activation tab via DemoBanner
    await activateBannerBtn.click();
    await expect(page).toHaveURL(/\/settings\?tab=subscription/);

    // Activate genuine Standard 1-Year license (product_id=4, 2026/01)
    await fillLicenseKeySegments(page, mintedLicenses.stdYear1);
    const activatePromise = page.waitForResponse(
      (res) => res.url().includes('/api/v1/license/activate/') && res.request().method() === 'POST'
    );
    await page.getByRole('button', { name: 'تنفيذ العملية' }).click();
    const activateRes = await activatePromise;
    expect([200, 201]).toContain(activateRes.status());
    const activateJson = await activateRes.json();
    expect(activateJson.wiped_demo).toBe(true);

    // Confirm /api/v1/license/status/ is now production and demo branches are wiped
    const statusRes = await fetch(`${BACKEND_BASE}/api/v1/license/status/`);
    expect(statusRes.status).toBe(200);
    const statusJson = await statusRes.json();
    expect(statusJson.is_demo).toBe(false);
    expect(statusJson.has_password).toBe(false);
    expect(statusJson.total_invoices_balance).toBe(4800);

    // Redirects cleanly to /activation-setup
    await expect(page).toHaveURL(/\/activation-setup/, { timeout: 15000 });
    await expect(page.getByText('تهانينا! تم تفعيل VentaPOS بنجاح 🎉')).toBeVisible({ timeout: 10000 });
    assertCleanRuntime();
  });

  test('2. Setup Wizard (/activation-setup) -> Set Company & Password -> Create Branch -> Create Receipt & Purchase', async () => {
    resetMonitors();
    const page = sharedPage;

    await expect(page).toHaveURL(/\/activation-setup/);
    await page.locator('input[name="name"]').fill('مؤسسة الوفاء للتجارة');
    await page.locator('input[name="phone1"]').fill('01099988877');
    await page.locator('input[name="admin_password"]').fill('SecretPass#2026');

    const saveCompanyPromise = page.waitForResponse(
      (res) => res.url().includes('/api/v1/company-settings/') && res.status() < 400
    );
    await page.getByRole('button', { name: 'حفظ البيانات وبدء العمل' }).click();
    await saveCompanyPromise;

    // May transition via /select-branch or /login if password triggers auth prompt
    await expect(page).toHaveURL(/\/(select-branch|login)/, { timeout: 15000 });
    if (page.url().includes('/login')) {
      await page.getByPlaceholder('أدخل كلمة سر النظام').fill('SecretPass#2026');
      await page.getByRole('button', { name: 'تسجيل الدخول' }).click();
      await expect(page).toHaveURL(/\/select-branch/, { timeout: 15000 });
    }

    // 0 branches after wipe -> Add branch modal opens automatically
    await expect(page.getByText('إضافة فرع جديد').first()).toBeVisible();
    await page.locator('.modal input[type="text"]').fill('الفرع الرئيسي');
    await page.getByRole('button', { name: 'حفظ' }).click();

    // Auto-selects the single newly created branch -> lands on /receipts
    await expect(page).toHaveURL(/\/receipts/, { timeout: 15000 });
    await expect(page.locator('header.navbar')).toContainText('الفرع الرئيسي');

    // DemoBanner must be hidden in Production
    await expect(page.getByRole('button', { name: 'تفعيل البرنامج' })).toHaveCount(0);

    // Capture live auth token and branchId created via UI
    const sessionInfo = await page.evaluate(() => ({
      token: localStorage.getItem('token'),
      branchId: Number(localStorage.getItem('branchId')),
    }));
    expect(sessionInfo.token).toBeTruthy();
    expect(sessionInfo.branchId).toBeGreaterThan(0);
    liveIds.token = sessionInfo.token;
    liveIds.branchId = sessionInfo.branchId;

    const authHeaders = {
      'Content-Type': 'application/json',
      Authorization: `Token ${liveIds.token}`,
    };

    // Seed real Salesperson, Supplier, InventoryItem, PurchaseInvoice, Cash & Installment Receipts in live DB
    const spRes = await fetch(`${BACKEND_BASE}/api/v1/salespersons/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ branch: liveIds.branchId, name: 'مندوب الوفاء' }),
    });
    expect(spRes.status).toBe(201);
    const sp = await spRes.json();

    const supRes = await fetch(`${BACKEND_BASE}/api/v1/suppliers/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ branch: liveIds.branchId, name: 'شركة الموردين الحديثة' }),
    });
    expect(supRes.status).toBe(201);
    const sup = await supRes.json();

    const itemRes = await fetch(`${BACKEND_BASE}/api/v1/inventory-items/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        branch: liveIds.branchId,
        name: 'ثلاجة نوفروست 16 قدم',
        initial_quantity: 10,
        initial_purchase_price: 8000,
        initial_commission_amount: 250,
        initial_month: 1,
        initial_year: 2026,
      }),
    });
    expect(itemRes.status).toBe(201);
    const item = await itemRes.json();

    const purRes = await fetch(`${BACKEND_BASE}/api/v1/purchase-invoices/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        branch: liveIds.branchId,
        supplier: sup.id,
        invoice_number: 501,
        invoice_type: 'PURCHASE',
        invoice_year: 2026,
        invoice_month: 2,
        items: [{ inventory_item: item.id, quantity: 2, purchase_price: 8000 }],
      }),
    });
    expect(purRes.status).toBe(201);
    liveIds.purchaseId = (await purRes.json()).id;

    const cashRecRes = await fetch(`${BACKEND_BASE}/api/v1/receipts/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        branch: liveIds.branchId,
        salesperson: sp.id,
        receipt_number: 101,
        customer_name: 'عميل نقدي مباشر',
        area: 'مدينة نصر',
        is_cash_sale: true,
        total_amount: 10000,
        down_payment: 10000,
        sale_year: 2026,
        sale_month: 2,
        items: [{ inventory_item: item.id, quantity: 1, unit_price: 10000 }],
      }),
    });
    expect(cashRecRes.status).toBe(201);
    liveIds.cashReceiptId = (await cashRecRes.json()).id;

    const instRecRes = await fetch(`${BACKEND_BASE}/api/v1/receipts/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        branch: liveIds.branchId,
        salesperson: sp.id,
        receipt_number: 102,
        customer_name: 'أحمد محمود حسن',
        area: 'المعادي',
        is_cash_sale: false,
        total_amount: 12000,
        down_payment: 2000,
        installment_system: '5 شهور',
        sale_year: 2026,
        sale_month: 2,
        items: [{ inventory_item: item.id, quantity: 1, unit_price: 12000 }],
        installments: [
          { amount: 2000, payment_date: '2026-02-25' },
          { amount: 2000, payment_date: '2026-03-25' },
          { amount: 2000, payment_date: '2026-04-25' },
          { amount: 2000, payment_date: '2026-05-25' },
          { amount: 2000, payment_date: '2026-06-25' },
        ],
      }),
    });
    expect(instRecRes.status).toBe(201);
    liveIds.instReceiptId = (await instRecRes.json()).id;

    // Reload /receipts and confirm created customer renders cleanly in UI
    await page.reload();
    await expect(page.getByText('أحمد محمود حسن')).toBeVisible({ timeout: 10000 });
    assertCleanRuntime();
  });

  test('3. Multi-Year Renewal via Settings UI extends balance and preserves all receipts', async () => {
    resetMonitors();
    const page = sharedPage;

    await page.goto('/settings?tab=subscription');
    await expect(page.getByText(/الرصيد المتاح:/)).toBeVisible();

    const beforeStatusRes = await fetch(`${BACKEND_BASE}/api/v1/license/status/`);
    const beforeStatus = await beforeStatusRes.json();
    const balanceBefore = beforeStatus.total_invoices_balance;

    await fillLicenseKeySegments(page, mintedLicenses.renewYear2);
    const renewPromise = page.waitForResponse(
      (res) => res.url().includes('/api/v1/license/activate/') && res.request().method() === 'POST'
    );
    await page.getByRole('button', { name: 'تنفيذ العملية' }).click();
    const renewRes = await renewPromise;
    expect([200, 201]).toContain(renewRes.status());
    const renewJson = await renewRes.json();
    expect(renewJson.wiped_demo).toBeFalsy();

    // Verify quota increased and receipt #102 was preserved
    const afterStatusRes = await fetch(`${BACKEND_BASE}/api/v1/license/status/`);
    const afterStatus = await afterStatusRes.json();
    expect(afterStatus.total_invoices_balance).toBeGreaterThan(balanceBefore);

    const histRows = page.locator('table tbody tr');
    await expect(histRows).toHaveCount(2, { timeout: 10000 });

    await page.goto('/receipts');
    await expect(page.getByText('أحمد محمود حسن')).toBeVisible();
    assertCleanRuntime();
  });

  test('4. Live Backup Download & Authenticated Backup Upload Verification', async () => {
    resetMonitors();

    // 1. Unauthenticated upload rejected cleanly with 401
    const unauthForm = new FormData();
    unauthForm.append('backup_file', new Blob([Buffer.from('fake')], { type: 'application/octet-stream' }), 'bad.sqlite3');
    const unauthRes = await fetch(`${BACKEND_BASE}/api/v1/tools/backup/upload/`, {
      method: 'POST',
      body: unauthForm,
    });
    expect(unauthRes.status).toBe(401);

    // 2. Authenticated download yields valid SQLite3 database bytes
    const dlRes = await fetch(`${BACKEND_BASE}/api/v1/tools/backup/download/`, {
      headers: { Authorization: `Token ${liveIds.token}` },
    });
    expect(dlRes.status).toBe(200);
    const dlBytes = Buffer.from(await dlRes.arrayBuffer());
    expect(dlBytes.subarray(0, 15).toString('utf-8')).toBe('SQLite format 3');

    // 3. Authenticated upload with corrupt payload returns 400
    const badForm = new FormData();
    badForm.append('backup_file', new Blob([Buffer.from('NOT_A_VALID_SQLITE_DB')], { type: 'application/octet-stream' }), 'corrupt.sqlite3');
    const badRes = await fetch(`${BACKEND_BASE}/api/v1/tools/backup/upload/`, {
      method: 'POST',
      headers: { Authorization: `Token ${liveIds.token}` },
      body: badForm,
    });
    expect(badRes.status).toBe(400);

    // 4. Authenticated upload with valid downloaded SQLite3 succeeds cleanly
    const goodForm = new FormData();
    goodForm.append('backup_file', new Blob([dlBytes], { type: 'application/x-sqlite3' }), 'live_valid_backup.sqlite3');
    const goodRes = await fetch(`${BACKEND_BASE}/api/v1/tools/backup/upload/`, {
      method: 'POST',
      headers: { Authorization: `Token ${liveIds.token}` },
      body: goodForm,
    });
    expect(goodRes.status).toBe(200);
    const goodJson = await goodRes.json();
    expect(['success', 'restored', 'pending_restart']).toContain(goodJson.status);
    assertCleanRuntime();
  });

  test('5. Live Financial Reports UI + Real PDF Compilation for Receipt/Purchase/Report desktop_print', async () => {
    resetMonitors();
    const page = sharedPage;

    // Navigate across live report views in Chromium
    await page.goto('/reports/dashboard');
    await expect(page.locator('.card').first()).toBeVisible({ timeout: 10000 });

    await page.goto('/reports/profit-and-loss');
    await expect(page.getByText(/22,000|10,000|12,000/).first()).toBeVisible({ timeout: 10000 });

    await page.goto('/reports/installments');
    await expect(page.getByText('أحمد محمود حسن').first()).toBeVisible({ timeout: 10000 });
    assertCleanRuntime();

    const authHeaders = {
      'Content-Type': 'application/json',
      Authorization: `Token ${liveIds.token}`,
    };

    // Live printers discovery
    const printersRes = await fetch(`${BACKEND_BASE}/api/v1/receipts/printers/`, {
      headers: { Authorization: `Token ${liveIds.token}` },
    });
    expect(printersRes.status).toBe(200);
    const printersJson = await printersRes.json();
    expect(Array.isArray(printersJson.printers)).toBe(true);

    // Cash-only receipt blocked from schedule print cleanly with 400
    const cashPrintRes = await fetch(`${BACKEND_BASE}/api/v1/receipts/desktop_print/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ receipt_ids: [liveIds.cashReceiptId], action: 'print', target_printer: '__E2E_NULL_PRINTER__' }),
    });
    expect(cashPrintRes.status).toBe(400);

    // Real PDF generation via wkhtmltopdf.exe + CREATE_NO_WINDOW Sumatra dispatch for Receipt, Purchase, and Report
    const instPrintRes = await fetch(`${BACKEND_BASE}/api/v1/receipts/desktop_print/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ receipt_ids: [liveIds.instReceiptId], action: 'print', target_printer: '__E2E_NULL_PRINTER__' }),
    });
    expect(instPrintRes.status).toBe(200);

    const purPrintRes = await fetch(`${BACKEND_BASE}/api/v1/purchase-invoices/desktop_print/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ invoice_ids: [liveIds.purchaseId], action: 'print', target_printer: '__E2E_NULL_PRINTER__' }),
    });
    expect(purPrintRes.status).toBe(200);

    const repPrintRes = await fetch(`${BACKEND_BASE}/api/v1/reports/desktop_print/`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        report_type: 'purchases',
        branch_id: liveIds.branchId,
        year: 2026,
        month: 2,
        action: 'print',
        target_printer: '__E2E_NULL_PRINTER__',
      }),
    });
    expect(repPrintRes.status).toBe(200);

    // Verify 3 real PDF files were produced on disk inside tempDir/media/Invoices
    const pdfDir = path.join(tempDir, 'media', 'Invoices');
    expect(fs.existsSync(pdfDir)).toBe(true);
    const pdfFiles = fs.readdirSync(pdfDir).filter((f) => f.endsWith('.pdf'));
    expect(pdfFiles.length).toBeGreaterThanOrEqual(3);
    for (const f of pdfFiles) {
      const hdr = fs.readFileSync(path.join(pdfDir, f)).subarray(0, 5).toString('utf-8');
      expect(hdr).toBe('%PDF-');
    }
    assertCleanRuntime();
  });

  test('6. Emergency Password Recovery (product_id=16) rotates password and revokes prior token', async () => {
    resetMonitors();
    const page = sharedPage;
    const staleToken = liveIds.token;

    await page.evaluate(() => {
      localStorage.removeItem('token');
      localStorage.removeItem('branchId');
      localStorage.removeItem('branchName');
    });
    await page.goto('/login');

    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    await page.getByText('نسيت كلمة المرور؟').click();

    await page.getByPlaceholder('مثال: VNTA-ABCD-1234').fill(mintedLicenses.recoveryCode);
    const recForm = page.locator('form').filter({ hasText: 'تغيير كلمة المرور' });
    await recForm.locator('input[type="password"]').fill('Recovered#2026');
    await page.getByRole('button', { name: 'تغيير كلمة المرور' }).click();

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 10000 });

    // Confirm prior token is immediately revoked (401)
    const staleCheck = await fetch(`${BACKEND_BASE}/api/v1/branches/`, {
      headers: { Authorization: `Token ${staleToken}` },
    });
    expect(staleCheck.status).toBe(401);

    // Return to login form and log in with recovered password
    const cancelBtn = page.getByRole('button', { name: 'إلغاء' });
    if (await cancelBtn.isVisible().catch(() => false)) {
      await cancelBtn.click();
    }
    const passInput = page.getByPlaceholder('أدخل كلمة سر النظام');
    await expect(passInput).toBeVisible({ timeout: 5000 });
    await passInput.fill('Recovered#2026');
    await page.getByRole('button', { name: 'تسجيل الدخول' }).click();
    await expect(page).toHaveURL(/\/(select-branch|receipts)/, { timeout: 15000 });
    if (page.url().includes('/select-branch')) {
      // SelectBranch may auto-redirect to /receipts when only 1 branch exists
      await Promise.race([
        page.waitForURL(/\/receipts/, { timeout: 15000 }),
        page.locator('.card.cursor-pointer').first().click({ timeout: 15000 }).catch(() => {}),
      ]);
      await expect(page).toHaveURL(/\/receipts/, { timeout: 15000 });
    }

    liveIds.token = await page.evaluate(() => localStorage.getItem('token'));
    expect(liveIds.token).toBeTruthy();
    expect(liveIds.token).not.toBe(staleToken);
    assertCleanRuntime();
  });

  test('7. Print-Only Basic Mode (product_id=2) enables PrintOnlyGate redirects across restricted routes', async () => {
    resetMonitors();
    const page = sharedPage;

    await page.goto('/settings?tab=subscription');
    await fillLicenseKeySegments(page, mintedLicenses.printOnlyYear);
    const activatePromise = page.waitForResponse(
      (res) => res.url().includes('/api/v1/license/activate/') && res.request().method() === 'POST'
    );
    await page.getByRole('button', { name: 'تنفيذ العملية' }).click();
    const actRes = await activatePromise;
    expect([200, 201]).toContain(actRes.status());

    // Confirm /api/v1/license/status/ now reports is_print_only=true
    const statusRes = await fetch(`${BACKEND_BASE}/api/v1/license/status/`);
    const statusJson = await statusRes.json();
    expect(statusJson.is_print_only).toBe(true);
    await expect(page.getByText(/باقة طباعة فقط/)).toBeVisible({ timeout: 10000 });

    // Restricted routes must redirect automatically back to /receipts
    for (const blockedPath of ['/reports/dashboard', '/product-ledger', '/purchases/new', '/expenses', `/receipts/return/${liveIds.instReceiptId}`]) {
      await page.goto(blockedPath);
      await expect(page).toHaveURL(/\/receipts$/, { timeout: 10000 });
    }

    assertCleanRuntime();
  });
});
