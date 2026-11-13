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
  const pageErrors = [];
  const consoleErrors = [];
  const serverErrors = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('response', (res) => {
    if (res.status() >= 500 || res.status() === 403) {
      serverErrors.push(`${res.status()} ${res.url()}`);
    }
  });
  return { pageErrors, consoleErrors, serverErrors };
}

function assertCleanRuntime(monitors) {
  expect(monitors.serverErrors).toEqual([]);
  expect(monitors.pageErrors).toEqual([]);
  expect(monitors.consoleErrors).toEqual([]);
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

async function setZoomViaResetAndSteps(page, targetPct) {
  const resetBadge = page.locator('span[title="إعادة التعيين إلى 100% (Ctrl + 0)"]');
  const zoomInBtn = page.locator('button[title="تكبير (Ctrl + +)"]');
  const zoomOutBtn = page.locator('button[title="تصغير (Ctrl + -)"]');

  await expect(resetBadge).toBeVisible();
  const patchPromise = (expected) =>
    page.waitForResponse(
      (res) => res.url().includes('/api/v1/company-settings/') && res.request().method() === 'PATCH' && res.status() === 200,
      { timeout: 10000 }
    ).catch(() => null);

  if ((await resetBadge.textContent()).trim() !== '100%') {
    const p = patchPromise();
    await resetBadge.click();
    await p;
    await expect(resetBadge).toHaveText('100%');
  }

  const steps = Math.round((targetPct - 100) / 5);
  if (steps > 0) {
    for (let i = 0; i < steps; i++) {
      await zoomInBtn.click();
    }
  } else if (steps < 0) {
    for (let i = 0; i < Math.abs(steps); i++) {
      await zoomOutBtn.click();
    }
  }
  await expect(resetBadge).toHaveText(`${targetPct}%`);
  await page.waitForTimeout(250);
}

async function assertNoHorizontalOverflowAndNavbarFit(page) {
  const geo = await page.evaluate(() => {
    const docEl = document.documentElement;
    const header = document.querySelector('header.navbar');
    const headerRect = header ? header.getBoundingClientRect() : null;
    const cssVarRaw = getComputedStyle(docEl).getPropertyValue('--navbar-height').trim();
    const cssVarNum = parseFloat(cssVarRaw) || 0;
    const zoom = parseFloat(document.body?.style?.zoom) || 1.0;

    const navItems = Array.from(document.querySelectorAll('header.navbar .nav-link, header.navbar button[title]'));
    const clippedItems = navItems
      .filter((el) => el.offsetParent !== null)
      .map((el) => {
        const r = el.getBoundingClientRect();
        return {
          text: (el.textContent || el.getAttribute('title') || '').trim(),
          left: r.left,
          right: r.right,
          top: r.top,
          bottom: r.bottom,
        };
      })
      .filter((r) => r.left < -2 || r.right > window.innerWidth + 2 || r.top < -2);

    const forbiddenClasses = document.querySelectorAll('.premium-card, .glassmorphism').length;
    const wideElements = [];
    if (docEl.scrollWidth > docEl.clientWidth + 2) {
      for (const el of document.querySelectorAll('body, body *')) {
        if (el.closest('table')) continue;
        const r = el.getBoundingClientRect();
        if (r.width > docEl.clientWidth + 2 || r.left < -2 || r.right > window.innerWidth + 2) {
          wideElements.push({
            tag: el.tagName,
            cls: String(el.className || '').slice(0, 80),
            w: Math.round(r.width),
            sw: el.scrollWidth,
            cw: el.clientWidth,
            left: Math.round(r.left),
            right: Math.round(r.right),
            ovx: getComputedStyle(el).overflowX,
          });
        }
      }
    }

    return {
      scrollWidth: docEl.scrollWidth,
      clientWidth: docEl.clientWidth,
      innerWidth: window.innerWidth,
      headerRect: headerRect
        ? { top: headerRect.top, bottom: headerRect.bottom, height: headerRect.height }
        : null,
      cssVarNum,
      zoom,
      clippedItems,
      forbiddenClasses,
      wideElements,
    };
  });

  expect(geo.forbiddenClasses).toBe(0);
  expect(geo.wideElements).toEqual([]);
  expect(geo.scrollWidth).toBeLessThanOrEqual(geo.clientWidth + 2);
  expect(geo.headerRect).not.toBeNull();
  expect(geo.headerRect.top).toBeGreaterThanOrEqual(-1);
  expect(geo.cssVarNum).toBeGreaterThan(30);
  expect(geo.clippedItems).toEqual([]);
  return geo;
}

async function assertStickyTableGeometry(page, { containerSelector = '.report-table-container' } = {}) {
  const geo = await page.evaluate((cSel) => {
    const header = document.querySelector('header.navbar');
    const toolbar = document.querySelector('.sticky-toolbar');
    const strip = document.querySelector('.sticky-selection-strip');
    const container = document.querySelector(cSel);
    const thead = container ? container.querySelector('thead') : document.querySelector('thead');
    const firstTh = thead ? thead.querySelector('th') : null;
    const firstRow = container ? container.querySelector('tbody tr') : document.querySelector('tbody tr');
    const table = container ? container.querySelector('table') : document.querySelector('table');

    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
    };

    const hRect = rect(header);
    const tRect = rect(toolbar);
    const sRect = rect(strip);
    const cRect = rect(container);
    const thRect = rect(firstTh);
    const rowRect = rect(firstRow);
    const firstTd = container ? container.querySelector('tbody tr td') : document.querySelector('tbody tr td');
    const thStyles = firstTh ? getComputedStyle(firstTh) : null;
    const tdStyles = firstTd ? getComputedStyle(firstTd) : null;

    return {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      windowScrollY: window.scrollY || 0,
      docScrollHeight: document.documentElement.scrollHeight,
      bodyScrollHeight: document.body.scrollHeight,
      containerScrollTop: container ? container.scrollTop : 0,
      containerMaxHeight: container ? container.style.maxHeight : null,
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      hRect,
      tRect,
      sRect,
      cRect,
      thRect,
      rowRect,
      thPosition: thStyles ? thStyles.position : null,
      fontVariantNumeric: tdStyles ? tdStyles.fontVariantNumeric : (thStyles ? thStyles.fontVariantNumeric : null),
    };
  }, containerSelector);

  expect(geo.scrollWidth).toBeLessThanOrEqual(geo.clientWidth + 2);
  expect(geo.thRect).not.toBeNull();
  expect(geo.thRect.width).toBeGreaterThan(0);
  expect(geo.thRect.height).toBeGreaterThan(0);
  expect(geo.thPosition).toBe('sticky');
  expect(geo.fontVariantNumeric || '').toContain('tabular-nums');

  if (geo.hRect && geo.tRect) {
    expect(geo.tRect.top).toBeGreaterThanOrEqual(geo.hRect.bottom - 2);
  }
  if (geo.tRect && geo.sRect) {
    expect(geo.sRect.top).toBeGreaterThanOrEqual(geo.tRect.bottom - 2);
  }
  if (geo.tRect) {
    expect(geo.thRect.top).toBeGreaterThanOrEqual(geo.tRect.bottom - 2);
  }
  if (geo.sRect) {
    expect(geo.thRect.top).toBeGreaterThanOrEqual(geo.sRect.bottom - 2);
  }
  // In the 2-Scroll architecture, .report-table-container fills the remaining viewport height once window scrolls top section away
  if (geo.cRect && geo.windowScrollY > 5) {
    expect(geo.cRect.bottom, 'Table scroll container bottom should fit within viewport').toBeLessThanOrEqual(geo.innerHeight + 6);
  }
  if (geo.rowRect && geo.containerScrollTop === 0) {
    expect(geo.rowRect.top).toBeGreaterThanOrEqual(geo.thRect.bottom - 2);
  }
  return geo;
}

async function assertNoArabicIndicOrDecimalsInTable(page) {
  const sampleText = await page.evaluate(() => {
    const cells = Array.from(document.querySelectorAll('table tbody td, .card .fs-3, .card .fs-4')).slice(0, 120);
    return cells.map((c) => c.textContent || '').join(' | ');
  });
  expect(sampleText).not.toMatch(/[\u0660-\u0669]/);
  expect(sampleText).not.toMatch(/\.\d{2}(?:\s|$|\|)/);
}

test.describe.serial('Wave 3 Zero-Mock 3,100-Row Live Backend UI/UX & DOM Geometry QA', () => {
  test.setTimeout(120000);

  test.beforeAll(async () => {
    await checkPortFree(8000, '127.0.0.1');

    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ventapos-w3-3k-'));
    try {
      const e2eSettingsContent = `
import os
from pathlib import Path
from backend.settings import *

TEMP_DB_DIR = Path(os.environ['VENTAPOS_E2E_TEMP_DIR'])
DB_DIR = TEMP_DB_DIR
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
    CommissionHistory,
    InventoryAdjustment,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    InstallmentPayment,
    Expense,
    CompanySetting,
    ClientLicense,
)
from api.utils.security_utils import get_machine_id, generate_record_signature, generate_receipt_signature

admin_user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True, 'is_staff': True})
admin_user.is_superuser = True
admin_user.is_staff = True
admin_user.set_password('admin123')
admin_user.save()

CompanySetting.objects.create(
    name='شركة المقياس الثلاثي للتجارة',
    phone1='01012345678',
    collection_commission_rate=Decimal('0.10'),
    zoom_level=Decimal('1.00'),
)

mach_id = get_machine_id()
start_d = date(2025, 1, 1)
expiry_d = date(2030, 1, 1)
sig = generate_record_signature(expiry_d, 999999, mach_id, 7, True)
ClientLicense.objects.create(
    company_code=3000,
    product_id=7,
    start_date=start_d,
    expiry_date=expiry_d,
    invoices_balance=999999,
    is_active=True,
    machine_id=mach_id,
    license_code_hash=sig,
)

branch_a = Branch.objects.create(name='الفرع الرئيسي 3000')
branch_b = Branch.objects.create(name='فرع الجيزة المعزول')

sps_a = [
    Salesperson.objects.create(branch=branch_a, name=f'مندوب رئيسي {i}')
    for i in range(1, 6)
]
sps_b = [
    Salesperson.objects.create(branch=branch_b, name=f'مندوب جيزة {i}')
    for i in range(1, 3)
]

# 55 suppliers on Branch A, 5 on Branch B
sups_a = Supplier.objects.bulk_create([
    Supplier(branch=branch_a, name=f'مورد جملة {i:02d}')
    for i in range(1, 56)
])
sups_b = Supplier.objects.bulk_create([
    Supplier(branch=branch_b, name=f'مورد جيزة {i:02d}')
    for i in range(1, 6)
])
sups_a = list(Supplier.objects.filter(branch=branch_a).order_by('id'))
sups_b = list(Supplier.objects.filter(branch=branch_b).order_by('id'))

# 310 items on Branch A, 20 on Branch B
InventoryItem.objects.bulk_create([
    InventoryItem(
        branch=branch_a,
        name=f'صنف مخزون {i:03d}',
        initial_quantity=500,
        initial_purchase_price=Decimal('1000.00'),
        initial_commission_amount=Decimal('50.00'),
        initial_month=1,
        initial_year=2026,
    )
    for i in range(1, 311)
])
InventoryItem.objects.bulk_create([
    InventoryItem(
        branch=branch_b,
        name=f'صنف جيزة {i:02d}',
        initial_quantity=200,
        initial_purchase_price=Decimal('800.00'),
        initial_commission_amount=Decimal('40.00'),
        initial_month=1,
        initial_year=2026,
    )
    for i in range(1, 21)
])
items_a = list(InventoryItem.objects.filter(branch=branch_a).order_by('name'))
items_b = list(InventoryItem.objects.filter(branch=branch_b).order_by('name'))
first_item = items_a[0]

CommissionHistory.objects.create(
    item=first_item,
    commission_amount=Decimal('75.00'),
    activation_month=11,
    activation_year=2026,
)
InventoryAdjustment.objects.create(
    item=first_item,
    adjustment_type='DEFICIT',
    quantity=2,
    month=11,
    year=2026,
    reason='تلف مخزن اختباري',
)

# 105 PurchaseInvoices on Branch A + 5 on Branch B = 110 purchases
pur_a_objs = []
for i in range(1, 106):
    inv_type = 'RETURN' if i % 10 == 0 else 'PURCHASE'
    inv_month = 11 if i > 10 else 10
    pur_a_objs.append(
        PurchaseInvoice(
            branch=branch_a,
            supplier=sups_a[i % len(sups_a)],
            invoice_number=i,
            invoice_type=inv_type,
            invoice_month=inv_month,
            invoice_year=2026,
        )
    )
PurchaseInvoice.objects.bulk_create(pur_a_objs)
pur_a_list = list(PurchaseInvoice.objects.filter(branch=branch_a).order_by('invoice_number'))
PurchaseInvoiceItem.objects.bulk_create([
    PurchaseInvoiceItem(
        invoice=inv,
        inventory_item=items_a[idx % len(items_a)],
        quantity=5,
        purchase_price=Decimal('1000.00'),
    )
    for idx, inv in enumerate(pur_a_list)
])

pur_b_objs = [
    PurchaseInvoice(
        branch=branch_b,
        supplier=sups_b[i % len(sups_b)],
        invoice_number=i,
        invoice_type='PURCHASE',
        invoice_month=11,
        invoice_year=2026,
    )
    for i in range(1, 6)
]
PurchaseInvoice.objects.bulk_create(pur_b_objs)
pur_b_list = list(PurchaseInvoice.objects.filter(branch=branch_b).order_by('invoice_number'))
PurchaseInvoiceItem.objects.bulk_create([
    PurchaseInvoiceItem(
        invoice=inv,
        inventory_item=items_b[idx % len(items_b)],
        quantity=4,
        purchase_price=Decimal('800.00'),
    )
    for idx, inv in enumerate(pur_b_list)
])

# 55 distinct areas
areas = [f'منطقة {i:02d}' for i in range(1, 56)]

# 3,050 Receipts on Branch A (first 1,150 for sp_a[0] so receipts_count > 1,000)
receipt_objs_a = []
receipt_meta_a = []
for num in range(1, 3051):
    is_ret = (num % 50 == 0)
    rtype = 'RETURN' if is_ret else 'SALE'
    is_cash = True if is_ret else (num % 3 == 0)
    sale_m = 10 if num <= 1250 else 11
    sp = sps_a[0] if num <= 1150 else sps_a[1 + (num % 4)]
    total = Decimal('2000.00')
    down = Decimal('0.00') if is_cash else Decimal('500.00')
    inst_sys = '' if is_cash else '3 أقساط شهرية × 500'
    area_name = areas[num % len(areas)]
    item = items_a[num % len(items_a)]
    sig_val = generate_receipt_signature(
        num, total, sale_m, 2026,
        [{'inventory_item_id': item.id, 'quantity': 1}],
    )
    receipt_objs_a.append(
        Receipt(
            branch=branch_a,
            salesperson=sp,
            receipt_number=num,
            receipt_type=rtype,
            customer_name=f'عميل رقم {num}',
            phone_number=f'010{num:08d}',
            address=f'شارع الاختبار رقم {num}',
            area=area_name,
            total_amount=total,
            down_payment=down,
            installment_system=inst_sys,
            sale_year=2026,
            sale_month=sale_m,
            is_cash_sale=is_cash,
            products_text=f'{item.name} × 1',
            receipt_hash=sig_val,
        )
    )
    receipt_meta_a.append((num, item, is_cash, rtype, sale_m))

Receipt.objects.bulk_create(receipt_objs_a, batch_size=500)
saved_a = {r.receipt_number: r for r in Receipt.objects.filter(branch=branch_a)}

sale_items_a = []
inst_payments_a = []
sample_sale_id = None
for num, item, is_cash, rtype, sale_m in receipt_meta_a:
    rec = saved_a[num]
    if sample_sale_id is None and rtype == 'SALE' and sale_m == 11:
        sample_sale_id = rec.id
    sale_items_a.append(
        SaleItem(
            receipt=rec,
            inventory_item=item,
            quantity=1,
            unit_price=Decimal('2000.00'),
        )
    )
    if rtype == 'SALE' and not is_cash:
        # Installments falling due in 2026/11 (from 2026/10 sales) and 2026/12 (from 2026/11 sales)
        # Ensure > 1,100 installments due in 2026/11 for InstallmentsReport >= 1,000 assertion!
        due_date = date(2026, 11, 25) if sale_m == 10 or (num % 2 == 0) else date(2026, 12, 25)
        inst_payments_a.append(
            InstallmentPayment(
                receipt=rec,
                payment_date=due_date,
                amount=Decimal('500.00'),
            )
        )

SaleItem.objects.bulk_create(sale_items_a, batch_size=500)
InstallmentPayment.objects.bulk_create(inst_payments_a, batch_size=500)

# 50 Receipts on Branch B -> 3,100 total receipts
receipt_objs_b = []
for num in range(1, 51):
    item = items_b[num % len(items_b)]
    sig_val = generate_receipt_signature(
        num, Decimal('1500.00'), 11, 2026,
        [{'inventory_item_id': item.id, 'quantity': 1}],
    )
    receipt_objs_b.append(
        Receipt(
            branch=branch_b,
            salesperson=sps_b[num % len(sps_b)],
            receipt_number=num,
            receipt_type='SALE',
            customer_name=f'عميل جيزة {num}',
            phone_number=f'011{num:08d}',
            address=f'عنوان جيزة {num}',
            area='الدقي',
            total_amount=Decimal('1500.00'),
            down_payment=Decimal('0.00'),
            installment_system='',
            sale_year=2026,
            sale_month=11,
            is_cash_sale=True,
            products_text=f'{item.name} × 1',
            receipt_hash=sig_val,
        )
    )
Receipt.objects.bulk_create(receipt_objs_b)
saved_b = {r.receipt_number: r for r in Receipt.objects.filter(branch=branch_b)}
SaleItem.objects.bulk_create([
    SaleItem(
        receipt=saved_b[num],
        inventory_item=items_b[num % len(items_b)],
        quantity=1,
        unit_price=Decimal('1500.00'),
    )
    for num in range(1, 51)
])

# Expenses on Branch A and B in 2026/11
cats = ['مصروفات عامة', 'إيجار', 'كهرباء ومياه', 'نقل ومشال', 'صيانة']
Expense.objects.bulk_create([
    Expense(
        branch=branch_a,
        category=cats[i % len(cats)],
        amount=Decimal('350.00'),
        description=f'مصروف تشغيلي {i:02d}',
        expense_year=2026,
        expense_month=11,
    )
    for i in range(1, 26)
])
Expense.objects.create(
    branch=branch_b,
    category='إيجار',
    amount=Decimal('1200.00'),
    description='إيجار فرع الجيزة',
    expense_year=2026,
    expense_month=11,
)

print(json.dumps({
    'branchAId': branch_a.id,
    'branchBId': branch_b.id,
    'branchAName': branch_a.name,
    'branchBName': branch_b.name,
    'firstItemId': first_item.id,
    'firstItemName': first_item.name,
    'sampleSaleReceiptId': sample_sale_id,
    'receiptsA': 3050,
    'receiptsB': 50,
    'purchasesA': 105,
    'itemsA': 310,
    'suppliersA': 55,
}, ensure_ascii=False))
`;
      const seedPath = path.join(tempDir, 'seed_3000.py');
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

  test('1. Desktop Viewports (1280x720 & 1366x768) + Navbar Zoom Persistence (100% / 125% / 85%)', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    await assertNoHorizontalOverflowAndNavbarFit(page);

    // Zoom to 125% at 1280x720 and confirm Navbar keeps fitting without overflow
    await setZoomViaResetAndSteps(page, 125);
    await assertNoHorizontalOverflowAndNavbarFit(page);

    // Reload and verify DB zoom persistence
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.locator('span[title="إعادة التعيين إلى 100% (Ctrl + 0)"]')).toHaveText('125%');
    await assertNoHorizontalOverflowAndNavbarFit(page);

    // Zoom to 85% and check 1366x768
    await page.setViewportSize({ width: 1366, height: 768 });
    await setZoomViaResetAndSteps(page, 85);
    await assertNoHorizontalOverflowAndNavbarFit(page);

    // Reset back to 100% cleanly
    await setZoomViaResetAndSteps(page, 100);
    await assertNoHorizontalOverflowAndNavbarFit(page);
    assertCleanRuntime(monitors);
  });

  test('2. SearchReceipts (/receipts) with 3,050 Real Rows: Sticky Geometry, Infinite Scroll, 3-Tier Selection, Cash-Only Bulk Print Block, & Clamped ContextMenu at 125% Zoom', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    await expect(page.getByText('نتائج البحث: 3,050 فاتورة')).toBeVisible();
    await expect(page.getByText('محدد 3,050')).toBeVisible();
    await expect(page.getByText(/تم تحديد كافة الـ 3,050 فاتورة المطابقة للبحث/)).toBeVisible();

    const initialRowCount = await page.locator('table tbody tr').count();
    expect(initialRowCount).toBe(200);

    // Verify YYYY/MM formatting, Western integers, no .00, tabular-nums & sticky geometry before scroll
    await assertNoArabicIndicOrDecimalsInTable(page);
    const firstDateCell = (await page.locator('table tbody tr').first().locator('td').nth(3).textContent()).trim();
    expect(firstDateCell).toMatch(/^\d{4}\/(0[1-9]|1[0-2])$/);
    await assertStickyTableGeometry(page);

    // Phase 1 Scroll (Window): dock sticky toolbar under navbar & verify container fits viewport
    await page.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }));
    await page.waitForTimeout(100);
    await assertStickyTableGeometry(page);

    // Phase 2 Scroll (Container): trigger real page 2 via IntersectionObserver scroll inside container
    await page.evaluate(() => {
      const c = document.querySelector('.report-table-container');
      if (c && c.scrollHeight > c.clientHeight) {
        c.scrollTop = c.scrollHeight;
      } else {
        window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
      }
    });
    await expect.poll(async () => page.locator('table tbody tr').count(), { timeout: 10000 }).toBeGreaterThan(200);

    // Verify sticky thead remains non-overlapping after scrolling down into page 2
    await assertStickyTableGeometry(page);

    // Scroll back to top before selection checks
    await page.evaluate(() => {
      const c = document.querySelector('.report-table-container');
      if (c) c.scrollTop = 0;
      window.scrollTo({ top: 0, behavior: 'instant' });
    });

    // Test 3-Tier selection: uncheck first row -> 3,049 selected, click re-select banner -> 3,050
    const firstRowCheckbox = page.locator('table tbody tr').first().locator('input[type="checkbox"]');
    await firstRowCheckbox.click();
    await expect(page.getByText('محدد 3,049')).toBeVisible();
    const reselectBannerBtn = page.getByRole('button', { name: /تحديد كافة الـ 3,050 فاتورة المطابقة للبحث/ });
    await expect(reselectBannerBtn).toBeVisible();
    await reselectBannerBtn.click();
    await expect(page.getByText('محدد 3,050')).toBeVisible();

    // Cash-only bulk print block when only cash receipt(s) are selected
    await page.locator('table thead input[type="checkbox"]').click();
    await expect(page.getByRole('button', { name: 'طباعة محددة' })).toBeHidden();
    const firstCashRow = page.locator('table tbody tr', { hasText: 'كاش' }).first();
    await firstCashRow.locator('input[type="checkbox"]').click();
    await expect(page.getByText('محدد 1')).toBeVisible();

    await page.getByRole('button', { name: 'طباعة محددة' }).click();
    const swalPopup = page.locator('.swal2-popup');
    await expect(swalPopup).toBeVisible();
    await expect(swalPopup).toContainText(/كاش/);
    await page.locator('.swal2-confirm').click();
    await expect(swalPopup).toBeHidden();

    // Test ReceiptContextMenu viewport clamping at 125% zoom near bottom of viewport
    await setZoomViaResetAndSteps(page, 125);
    const ellipsisBtns = page.locator('button[aria-label="خيارات الفاتورة"]');
    await expect(ellipsisBtns.first()).toBeVisible();
    // Scroll container so a middle row sits near bottom of viewport
    await ellipsisBtns.nth(8).scrollIntoViewIfNeeded();
    await ellipsisBtns.nth(8).click();

    const menu = page.locator('.dropdown-menu.show').last();
    await expect(menu).toBeVisible();
    const menuGeo = await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('.dropdown-menu.show')).pop();
      const r = el.getBoundingClientRect();
      return {
        left: r.left,
        right: r.right,
        top: r.top,
        bottom: r.bottom,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
      };
    });
    expect(menuGeo.left).toBeGreaterThanOrEqual(0);
    expect(menuGeo.top).toBeGreaterThanOrEqual(0);
    expect(menuGeo.right).toBeLessThanOrEqual(menuGeo.innerWidth + 2);
    expect(menuGeo.bottom).toBeLessThanOrEqual(menuGeo.innerHeight + 2);

    await setZoomViaResetAndSteps(page, 100);
    assertCleanRuntime(monitors);
  });

  test('3. SearchPurchases (/search-purchases) with 105 Real Invoices: Geometry, Dates, & Scroll', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    await page.goto('/search-purchases');
    await expect(page.getByText('105 فاتورة')).toBeVisible();
    await assertNoArabicIndicOrDecimalsInTable(page);
    await assertStickyTableGeometry(page);

    // Verify YYYY/MM date format on first row
    const rowText = await page.locator('table tbody tr').first().textContent();
    expect(rowText).toMatch(/2026\/1[01]/);

    // Phase 1 Scroll (Window) then Phase 2 Scroll (Container) and confirm sticky header remains pinned
    await page.evaluate(() => {
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
      const c = document.querySelector('.report-table-container');
      if (c && c.scrollHeight > c.clientHeight) c.scrollTop = 250;
    });
    await page.waitForTimeout(50);
    await assertStickyTableGeometry(page);
    assertCleanRuntime(monitors);
  });

  test('4. Data Entry (POS, ReturnReceipt, PurchaseEntry): No Printing Allowed & Autocomplete under 310 Items / 55 Areas / 55 Suppliers', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    // POS (/pos): strictly NO print button, real autocomplete on item #305 & area #52
    await page.goto('/pos');
    await assertNoHorizontalOverflowAndNavbarFit(page);
    expect(await page.locator('button:has-text("طباعة"), a:has-text("طباعة")').count()).toBe(0);

    const areaInput = page.locator('#input_area');
    await areaInput.click();
    await areaInput.fill('منطقة 52');
    const areaOption = page.getByText('منطقة 52', { exact: true }).first();
    await expect(areaOption).toBeVisible();
    // Ensure dropdown suggestion fits inside viewport without clipping
    const areaBox = await areaOption.boundingBox();
    expect(areaBox.y + areaBox.height).toBeLessThanOrEqual(720);
    await areaOption.click();

    const prodInput = page.locator('.row.mb-4 input[type="text"]').first();
    await prodInput.click();
    await prodInput.fill('صنف مخزون 305');
    const prodOption = page.getByText('صنف مخزون 305', { exact: false }).first();
    await expect(prodOption).toBeVisible();
    await prodInput.press('ArrowDown');
    await prodInput.press('Enter');

    const numInputs = page.locator('.row.mb-4 input[inputmode="numeric"]');
    await numInputs.first().fill('2');
    await numInputs.first().press('Enter');
    await numInputs.nth(1).fill('1500');
    await numInputs.nth(1).press('Enter');
    await expect(page.locator('table tbody')).toContainText('صنف مخزون 305');

    // ReturnReceipt (/receipts/return/:id)
    await page.goto(`/receipts/return/${seedData.sampleSaleReceiptId}`);
    await assertNoHorizontalOverflowAndNavbarFit(page);
    await expect(page.locator('body')).toContainText(/مرتجع/);

    // PurchaseEntry (/purchases/new): strictly NO print button, real supplier #52 & item #305 autocomplete
    await page.goto('/purchases/new');
    await assertNoHorizontalOverflowAndNavbarFit(page);
    expect(await page.locator('button:has-text("طباعة"), a:has-text("طباعة")').count()).toBe(0);

    const supInput = page.getByPlaceholder('ابحث عن مورد...');
    await supInput.click();
    await supInput.fill('مورد جملة 52');
    await expect(page.getByText('مورد جملة 52', { exact: true }).first()).toBeVisible();

    const purProdInput = page.getByPlaceholder('ابحث عن صنف...');
    await purProdInput.click();
    await purProdInput.fill('صنف مخزون 305');
    await expect(page.getByText('صنف مخزون 305', { exact: true }).first()).toBeVisible();

    assertCleanRuntime(monitors);
  });

  test('5. Dimensions (310 Items & 55 Suppliers), ProductLedger, & Expenses UI/UX & Keyboard Flows', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    // Dimensions (/dimensions) - InventoryTab with 310 items
    await page.goto('/dimensions');
    await expect.poll(async () => page.locator('table tbody tr:not(:has(td[colspan]))').count(), { timeout: 15000 }).toBe(310);
    await assertNoArabicIndicOrDecimalsInTable(page);
    await assertStickyTableGeometry(page);

    // Switch to Suppliers tab -> 55 suppliers
    await page.getByRole('button', { name: /الموردين/ }).click();
    await expect.poll(async () => page.locator('table tbody tr:not(:has(td[colspan]))').count(), { timeout: 10000 }).toBe(55);
    await assertStickyTableGeometry(page);

    // Switch to Salespersons tab -> 5 salespersons
    await page.getByRole('button', { name: /المناديب/ }).click();
    await expect.poll(async () => page.locator('table tbody tr:not(:has(td[colspan]))').count(), { timeout: 10000 }).toBe(5);
    await assertStickyTableGeometry(page);

    // ProductLedger (/product-ledger/:id)
    await page.goto(`/product-ledger/${seedData.firstItemId}`);
    await expect(page.locator('table tbody tr:not(:has(td[colspan]))').first()).toBeVisible({ timeout: 15000 });
    await assertNoHorizontalOverflowAndNavbarFit(page);
    await assertNoArabicIndicOrDecimalsInTable(page);
    const ledgerDates = await page.locator('table tbody tr td.font-monospace').first().textContent();
    expect(ledgerDates.trim()).toMatch(/^\d{4}\/(0[1-9]|1[0-2])$/);

    // Expenses (/expenses)
    await page.goto('/expenses');
    await expect(page.locator('table tbody tr:not(:has(td[colspan]))').first()).toBeVisible({ timeout: 15000 });
    await assertStickyTableGeometry(page);
    await assertNoArabicIndicOrDecimalsInTable(page);
    assertCleanRuntime(monitors);
  });

  test('6. All 10 Reports at Full 3,050-Receipt Scale + Multi-Branch Isolation Check', async ({ page }) => {
    const monitors = attachRuntimeMonitors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    await loginAndSelectBranch(page, seedData.branchAName);

    const tableReports = [
      { path: '/reports/receipts', title: 'تقرير الفواتير والمبيعات' },
      { path: '/reports/purchases', title: 'تقرير المشتريات' },
      { path: '/reports/areas', title: 'تقرير المناطق والتحصيل' },
      { path: '/reports/expenses', title: 'تقرير المصروفات' },
      { path: '/reports/salesperson', title: 'تقرير أداء المناديب' },
      { path: '/reports/inventory', title: 'تقرير حركة المخزون' },
      { path: '/reports/profit-and-loss', title: 'تقرير الأرباح والخسائر' },
      { path: '/reports/averages', title: 'تقرير الأرباح والخسائر (المتوسطات)' },
      { path: '/reports/installments', title: 'تقرير تحصيل الأقساط' },
    ];

    // Dashboard first
    await page.goto('/reports/dashboard');
    await expect(page.getByText('تفاصيل المكسب')).toBeVisible();
    await expect(page.getByText('تفاصيل السيولة')).toBeVisible();
    await assertNoHorizontalOverflowAndNavbarFit(page);
    await assertNoArabicIndicOrDecimalsInTable(page);

    for (const rep of tableReports) {
      await page.goto(rep.path);
      await expect(page.locator('table tbody tr:not(:has(td[colspan]))').first(), `Report ${rep.path} should render at least one data row`).toBeVisible({ timeout: 15000 });
      await assertNoArabicIndicOrDecimalsInTable(page);
      await assertStickyTableGeometry(page);

      // Assert SortDropdown stays inside viewport when opened
      const sortBtn = page.getByRole('button', { name: /ترتيب/ });
      if (await sortBtn.count() > 0) {
        await sortBtn.first().click();
        const menuBox = await page.locator('.dropdown-menu.show').last().boundingBox();
        if (menuBox) {
          expect(menuBox.x).toBeGreaterThanOrEqual(-2);
          expect(menuBox.x + menuBox.width).toBeLessThanOrEqual(1282);
        }
        await sortBtn.first().click();
      }
    }

    // Verify fmtNum comma formatting >= 1,000 on InstallmentsReport & SalespersonPerformanceReport
    await page.goto('/reports/installments');
    await page.getByPlaceholder('شهر').fill('12');
    await expect(page.getByText(/1,\d{3}/).first()).toBeVisible({ timeout: 10000 });

    await page.goto('/reports/salesperson');
    await expect(page.getByText('1,764').first()).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder('شهر').fill('10');
    await expect(page.getByText('1,127').first()).toBeVisible({ timeout: 10000 });

    // Verify PurchasesReport product/supplier autocomplete against 310 items & 55 suppliers
    await page.goto('/reports/purchases');
    await expect(page.locator('table tbody tr:not(:has(td[colspan]))').first()).toBeVisible({ timeout: 15000 });
    const prodFilterInput = page.getByPlaceholder('جميع الأصناف...');
    await prodFilterInput.click();
    await prodFilterInput.fill('صنف مخزون 305');
    await expect(page.getByText('صنف مخزون 305', { exact: true }).first()).toBeVisible();

    // Multi-Branch Isolation via Navbar Switch -> Branch B (50 receipts, 20 items)
    await quickSwitchBranchViaNavbar(page, seedData.branchBName);
    await page.goto('/receipts');
    await expect(page.getByText('نتائج البحث: 50 فاتورة')).toBeVisible();
    await page.goto('/dimensions');
    await expect.poll(async () => page.locator('table tbody tr').count()).toBe(20);

    assertCleanRuntime(monitors);
  });
});
