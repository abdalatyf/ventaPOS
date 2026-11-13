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
let seedData = null;

function checkPortFree(port, host = '127.0.0.1') {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once('error', (err) => reject(new Error(`Port ${host}:${port} is already in use: ${err.message}`)));
    srv.once('listening', () => {
      srv.close(() => resolve());
    });
    srv.listen(port, host);
  });
}

async function waitForServerReady(url, proc, stderrChunks, timeoutMs = 25000) {
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
  for (let attempt = 0; attempt < 15; attempt++) {
    try {
      fs.rmSync(dirPath, { recursive: true, force: true });
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 200));
    }
  }
}

async function quickSwitchBranchViaNavbar(page, targetBranchName) {
  const dropdownToggle = page.locator('header.navbar .nav-item.dropdown > a.nav-link');
  await dropdownToggle.click();
  const branchBtn = page.locator('header.navbar .dropdown-menu.show button.dropdown-item', {
    hasText: targetBranchName,
  });
  await expect(branchBtn).toBeVisible();
  await branchBtn.click();
  await expect(dropdownToggle).toContainText(targetBranchName);
}

async function loginAndSelectBranch(page, targetBranchName) {
  await page.goto('/login');
  const pwdInput = page.getByPlaceholder('أدخل كلمة سر النظام');
  await expect(pwdInput).toBeVisible();
  await pwdInput.fill('admin123');
  await page.getByRole('button', { name: 'تسجيل الدخول' }).click();

  await expect(page).toHaveURL(/\/select-branch/);
  await page.getByText(targetBranchName).click();
  await expect(page).toHaveURL(/\/receipts/);
  await expect(page.locator('header.navbar')).toContainText(targetBranchName);
}

test.describe.serial('Live Zero-Mock Chaos & Dirty Inputs E2E', () => {
  test.setTimeout(90000);

  test.beforeAll(async () => {
    await checkPortFree(8000, '127.0.0.1');

    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ventapos-e2e-'));
    try {
      const e2eSettingsContent = `
import os
from pathlib import Path
from backend.settings import *

TEMP_DB_DIR = Path(os.environ['VENTAPOS_E2E_TEMP_DIR'])
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(TEMP_DB_DIR / 'e2e_db.sqlite3'),
    }
}
`;
      fs.writeFileSync(path.join(tempDir, 'e2e_settings.py'), e2eSettingsContent, 'utf-8');

      const seedScriptContent = `
import json
import os
from datetime import date
from decimal import Decimal
import django

django.setup()

from django.contrib.auth.models import User
from api.models import (
    Branch,
    Salesperson,
    Supplier,
    InventoryItem,
    CompanySetting,
    ClientLicense,
)
from api.utils.security_utils import get_machine_id, generate_record_signature

admin_user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True, 'is_staff': True})
admin_user.is_superuser = True
admin_user.is_staff = True
admin_user.set_password('admin123')
admin_user.save()

CompanySetting.objects.create(
    name='مؤسسة فينتا للاختبار المباشر',
    phone1='01000000000',
    collection_commission_rate=Decimal('0.10'),
)

mach_id = get_machine_id()
start_d = date(2026, 1, 1)
expiry_d = date(2027, 12, 31)
sig = generate_record_signature(str(expiry_d), 5000, mach_id, 1, True)
ClientLicense.objects.create(
    company_code=2026,
    product_id=1,
    start_date=start_d,
    expiry_date=expiry_d,
    invoices_balance=5000,
    is_active=True,
    machine_id=mach_id,
    license_code_hash=sig,
)

branch_a = Branch.objects.create(name='فرع المعادي E2E')
branch_b = Branch.objects.create(name='فرع التجمع E2E')

sp_a = Salesperson.objects.create(branch=branch_a, name='مندوب معادي أ')
sp_b = Salesperson.objects.create(branch=branch_b, name='مندوب تجمع ب')

sup_a = Supplier.objects.create(branch=branch_a, name='مورد معادي أ')
sup_b = Supplier.objects.create(branch=branch_b, name='مورد تجمع ب')

item_a = InventoryItem.objects.create(
    branch=branch_a,
    name='ثلاجة معادي أ',
    initial_quantity=10,
    initial_purchase_price=Decimal('5000.00'),
    initial_commission_amount=Decimal('100.00'),
    initial_month=1,
    initial_year=2026,
)
item_b = InventoryItem.objects.create(
    branch=branch_b,
    name='غسالة تجمع ب',
    initial_quantity=5,
    initial_purchase_price=Decimal('4000.00'),
    initial_commission_amount=Decimal('80.00'),
    initial_month=1,
    initial_year=2026,
)

print(json.dumps({
    'branchAId': branch_a.id,
    'branchBId': branch_b.id,
    'spAId': sp_a.id,
    'spBId': sp_b.id,
    'supAId': sup_a.id,
    'supBId': sup_b.id,
    'itemAId': item_a.id,
    'itemBId': item_b.id,
}, ensure_ascii=False))
`;
      const seedPath = path.join(tempDir, 'seed_e2e.py');
      fs.writeFileSync(seedPath, seedScriptContent, 'utf-8');

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

      const seedOut = execFileSync(VENV_PYTHON, [seedPath], {
        cwd: BACKEND_DIR,
        env: childEnv,
        encoding: 'utf-8',
      });
      const lines = seedOut.trim().split(/\r?\n/);
      seedData = JSON.parse(lines[lines.length - 1]);

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
    } catch (err) {
      await stopProcessTree(serverProc);
      await removeTempDirSafe(tempDir);
      throw err;
    }
  });

  test.afterAll(async () => {
    await stopProcessTree(serverProc);
    await removeTempDirSafe(tempDir);
  });

  test('1. Real Login + Branch Selection + Rapid Double-Click POS Submit Creates Exactly 1 Receipt & Deducts Stock Once', async ({ page, request }) => {
    const pageErrors = [];
    const serverErrors = [];
    let receiptPostCount = 0;

    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('response', (res) => {
      if (res.status() >= 500) {
        serverErrors.push(`${res.status()} ${res.url()}`);
      }
    });
    page.on('request', (req) => {
      if (req.method() === 'POST' && req.url().includes('/api/v1/receipts/') && !req.url().includes('bulk')) {
        receiptPostCount += 1;
      }
    });

    await loginAndSelectBranch(page, 'فرع المعادي E2E');
    await page.goto('/pos');

    // Fill POS receipt using Arabic-Indic numerals & literal HTML-like customer name
    const spInput = page.getByPlaceholder('ابحث عن مندوب...');
    await spInput.click();
    await page.getByText('مندوب معادي أ').click();

    const customerName = '<b>عميل أ & "سريع"</b>';
    await page.locator('#input_name').fill(customerName);

    const productInput = page.locator('input[autocomplete="off"]').nth(2);
    await productInput.click();
    await productInput.fill('ثلاجة معادي أ');
    await page.getByText('ثلاجة معادي أ').click();

    const numInputs = page.locator('input[inputmode="numeric"]');
    await numInputs.nth(2).fill('٢');
    await numInputs.nth(3).fill('٦٠٠٠');
    await page.getByRole('button', { name: '+', exact: true }).click();

    await expect(page.locator('table')).toContainText('ثلاجة معادي أ');
    await page.locator('.col-3 input.text-success').fill('٢٠٠٠');
    await page.getByPlaceholder('شهر 1').fill('٥');
    await page.getByPlaceholder('مبلغ 1').fill('٢٠٠٠');

    // Physical double-click on Confirm Sale button — idempotency lock must send strictly 1 POST
    const confirmBtn = page.getByRole('button', { name: /تأكيد البيع/ });
    await confirmBtn.dblclick();

    // Wait for cart reset indicating POST completed and form refreshed
    await expect(page.locator('table')).toContainText('لا توجد أصناف مضافة');
    expect(receiptPostCount).toBe(1);

    // Verify real SQLite persistence & exact stock deduction (10 -> 8) directly via backend API
    const token = await page.evaluate(() => localStorage.getItem('token'));
    const receiptsRes = await request.get(`${BACKEND_BASE}/api/v1/receipts/`, {
      headers: {
        Authorization: `Token ${token}`,
        'X-Branch-ID': String(seedData.branchAId),
      },
    });
    expect(receiptsRes.status()).toBe(200);
    const receiptsBody = await receiptsRes.json();
    expect(receiptsBody.count).toBe(1);
    expect(receiptsBody.results[0].customer_name).toBe(customerName);
    expect(Number(receiptsBody.results[0].total_amount)).toBe(12000);

    const stockRes = await request.get(
      `${BACKEND_BASE}/api/v1/inventory-items/${seedData.itemAId}/stock/?month=11&year=2026`,
      {
        headers: {
          Authorization: `Token ${token}`,
          'X-Branch-ID': String(seedData.branchAId),
        },
      }
    );
    expect(stockRes.status()).toBe(200);
    const stockBody = await stockRes.json();
    expect(stockBody.safe_available_qty).toBe(8);

    expect(pageErrors).toEqual([]);
    expect(serverErrors).toEqual([]);
  });

  test('2. Mid-Form Branch Switch Wipes POS & PurchaseEntry State and Isolates Branch Search Lists', async ({ page }) => {
    const pageErrors = [];
    const serverErrors = [];
    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('response', (res) => {
      if (res.status() >= 500) serverErrors.push(`${res.status()} ${res.url()}`);
    });

    // Authenticate fresh isolated context on Branch A and open /pos
    await loginAndSelectBranch(page, 'فرع المعادي E2E');
    await page.goto('/pos');
    await expect(page.locator('#input_name')).toBeVisible();

    await page.locator('#input_name').fill('عميل مؤقت لا ينتقل');
    const productInput = page.locator('input[autocomplete="off"]').nth(2);
    await productInput.click();
    await productInput.fill('ثلاجة معادي أ');
    await page.getByText('ثلاجة معادي أ').click();
    await page.locator('input[inputmode="numeric"]').nth(3).fill('5000');
    await page.getByRole('button', { name: '+', exact: true }).click();
    await expect(page.locator('table')).toContainText('ثلاجة معادي أ');

    // Switch to Branch B mid-form via Navbar quick-switcher
    await quickSwitchBranchViaNavbar(page, 'فرع التجمع E2E');

    // Verify POS wiped cart & customer, and loads Branch B salesperson list only
    await expect(page.locator('#input_name')).toHaveValue('');
    await expect(page.locator('table')).toContainText('لا توجد أصناف مضافة');
    await page.getByPlaceholder('ابحث عن مندوب...').click();
    await expect(page.getByText('مندوب تجمع ب')).toBeVisible();
    await expect(page.getByText('مندوب معادي أ')).toHaveCount(0);

    // SearchReceipts on Branch B must NOT see Branch A's receipt
    await page.goto('/receipts');
    await expect(page.getByText(/نتائج البحث: 0 فاتورة/)).toBeVisible();

    // Switch back to Branch A -> Branch A's XSS-like customer renders safely escaped as text
    await quickSwitchBranchViaNavbar(page, 'فرع المعادي E2E');
    await expect(page.getByText(/نتائج البحث: 1 فاتورة/)).toBeVisible();
    await expect(page.locator('table')).toContainText('<b>عميل أ & "سريع"</b>');
    const injectedBoldCount = await page.locator('table b', { hasText: 'عميل أ' }).count();
    expect(injectedBoldCount).toBe(0);

    // Switch to Branch B -> PurchaseEntry -> add Branch B item -> switch to Branch A mid-form
    await page.goto('/purchases/new');
    await quickSwitchBranchViaNavbar(page, 'فرع التجمع E2E');
    await page.getByPlaceholder('ابحث عن مورد...').click();
    await expect(page.getByText('مورد تجمع ب')).toBeVisible();
    await page.getByText('مورد تجمع ب').click();

    const purchProd = page.getByPlaceholder('ابحث عن صنف...');
    await purchProd.click();
    await purchProd.fill('غسالة تجمع ب');
    await page.getByText('غسالة تجمع ب').click();

    const ltrInputs = page.locator('input[dir="ltr"]');
    const cnt = await ltrInputs.count();
    await ltrInputs.nth(cnt - 2).fill('١');
    await ltrInputs.nth(cnt - 1).fill('٣٨٠٠');
    await page.getByRole('button', { name: /إضافة/ }).click();
    await expect(page.locator('table')).toContainText('غسالة تجمع ب');

    await quickSwitchBranchViaNavbar(page, 'فرع المعادي E2E');
    await expect(page.locator('table')).not.toContainText('غسالة تجمع ب');
    await page.getByPlaceholder('ابحث عن مورد...').click();
    await expect(page.getByText('مورد معادي أ')).toBeVisible();
    await expect(page.getByText('مورد تجمع ب')).toHaveCount(0);

    expect(pageErrors).toEqual([]);
    expect(serverErrors).toEqual([]);
  });

  test('3. Dirty Inputs Blocked Client-Side & XSS + Arabic-Indic Persisted Safely Across Reload in Real SQLite', async ({ page, request }) => {
    const pageErrors = [];
    const serverErrors = [];
    let expensePostCount = 0;

    page.on('pageerror', (err) => pageErrors.push(err.message));
    page.on('response', (res) => {
      if (res.status() >= 500) serverErrors.push(`${res.status()} ${res.url()}`);
    });
    page.on('request', (req) => {
      if (req.method() === 'POST' && req.url().includes('/api/v1/expenses/')) {
        expensePostCount += 1;
      }
    });

    await loginAndSelectBranch(page, 'فرع المعادي E2E');
    await page.goto('/expenses');
    await expect(page.getByPlaceholder('البيان (اسم المصروف) *')).toBeVisible();

    // Dirty 1: whitespace-only description must not submit
    const descInput = page.getByPlaceholder('البيان (اسم المصروف) *');
    const amtInput = page.getByPlaceholder('المبلغ *');
    await descInput.fill('   ');
    await amtInput.fill('250');
    await page.locator('form button[type="submit"]').click();
    expect(expensePostCount).toBe(0);

    // Dirty 2: zero / negative amount must not submit
    await descInput.fill('كهرباء');
    await amtInput.fill('-50');
    await page.locator('form button[type="submit"]').click();
    expect(expensePostCount).toBe(0);

    // Valid Arabic-Indic amount + XSS payload -> saved literally and escaped after page reload
    const xssExpense = 'كهرباء <script>window.__xssFired=true</script>';
    await descInput.fill(xssExpense);
    await amtInput.fill('٣٥٠');
    await page.locator('form button[type="submit"]').dblclick();

    await expect(page.locator('table')).toContainText(xssExpense);
    expect(expensePostCount).toBe(1);

    await page.reload();
    await expect(page.locator('table')).toContainText(xssExpense);
    const xssFired = await page.evaluate(() => Boolean(window.__xssFired));
    expect(xssFired).toBe(false);

    // Branch isolation check in Expenses: Branch B must have 0 expenses
    await quickSwitchBranchViaNavbar(page, 'فرع التجمع E2E');
    await expect(page.locator('table')).not.toContainText(xssExpense);

    // Verify InventoryTab on Branch A blocks bad year 2024 & saves Arabic-Indic initial stock cleanly
    await quickSwitchBranchViaNavbar(page, 'فرع المعادي E2E');
    await page.goto('/dimensions');
    let invPostCount = 0;
    page.on('request', (req) => {
      if (req.method() === 'POST' && req.url().includes('/api/v1/inventory-items/')) {
        invPostCount += 1;
      }
    });

    await page.locator('input[name="name"]').fill('مروحة اختبار معادي');
    await page.locator('input[name="qty"]').fill('٤');
    await page.locator('input[name="price"]').fill('٩٠٠');
    await page.locator('input[name="commission"]').fill('٣٠');
    await page.locator('input[name="startMonth"]').fill('١١');
    await page.locator('input[name="startYear"]').fill('2024');
    await page.locator('form button[type="submit"]').first().click();
    expect(invPostCount).toBe(0);

    await page.locator('input[name="startYear"]').fill('٢٠٢٦');
    await page.locator('form button[type="submit"]').first().dblclick();
    await expect(page.locator('table').first()).toContainText('مروحة اختبار معادي');
    expect(invPostCount).toBe(1);

    const token = await page.evaluate(() => localStorage.getItem('token'));
    const invA = await request.get(`${BACKEND_BASE}/api/v1/inventory-items/`, {
      headers: { Authorization: `Token ${token}`, 'X-Branch-ID': String(seedData.branchAId) },
    });
    const invAData = await invA.json();
    const listA = Array.isArray(invAData) ? invAData : invAData.results || [];
    expect(listA.some((i) => i.name === 'مروحة اختبار معادي' && i.initial_quantity === 4)).toBe(true);

    const invB = await request.get(`${BACKEND_BASE}/api/v1/inventory-items/`, {
      headers: { Authorization: `Token ${token}`, 'X-Branch-ID': String(seedData.branchBId) },
    });
    const invBData = await invB.json();
    const listB = Array.isArray(invBData) ? invBData : invBData.results || [];
    expect(listB.some((i) => i.name === 'مروحة اختبار معادي')).toBe(false);

    expect(pageErrors).toEqual([]);
    expect(serverErrors).toEqual([]);
  });
});
