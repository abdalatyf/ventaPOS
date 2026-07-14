# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: reports.spec.js >> Reports Module E2E Tests >> Installments Report tab loads successfully
- Location: e2e\reports.spec.js:136:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('إجمالي التحصيلات')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('إجمالي التحصيلات')

```

# Test source

```ts
  39  |             net_cash_in_hand: 2350
  40  |           },
  41  |           top_products: [],
  42  |           top_areas: []
  43  |         })
  44  |       });
  45  |     });
  46  | 
  47  |     await page.route('**/receipts/**', async (route) => {
  48  |       await route.fulfill({
  49  |         status: 200,
  50  |         contentType: 'application/json',
  51  |         body: JSON.stringify([{ id: 1, total_amount: 100 }])
  52  |       });
  53  |     });
  54  | 
  55  |     await page.route('**/expenses/**', async (route) => {
  56  |       await route.fulfill({
  57  |         status: 200,
  58  |         contentType: 'application/json',
  59  |         body: JSON.stringify([{ id: 1, amount: 50 }])
  60  |       });
  61  |     });
  62  | 
  63  |     await page.route('**/reports/salesperson-performance/**', async (route) => {
  64  |       await route.fulfill({
  65  |         status: 200,
  66  |         contentType: 'application/json',
  67  |         body: JSON.stringify({
  68  |           totals: { grand_total_sales: 0, grand_total_collected: 0, grand_total_due: 0, grand_total_cash: 0 },
  69  |           salespersons: []
  70  |         })
  71  |       });
  72  |     });
  73  | 
  74  |     await page.route('**/reports/profit-and-loss/**', async (route) => {
  75  |       await route.fulfill({
  76  |         status: 200,
  77  |         contentType: 'application/json',
  78  |         body: JSON.stringify({
  79  |           summary: { 
  80  |             grand_revenue: 100, 
  81  |             grand_cost: 50, 
  82  |             grand_commission: 10, 
  83  |             expenses_total: 20, 
  84  |             net_profit_final: 20 
  85  |           },
  86  |           details: []
  87  |         })
  88  |       });
  89  |     });
  90  | 
  91  |     await page.route('**/reports/inventory-movement/**', async (route) => {
  92  |       await route.fulfill({
  93  |         status: 200,
  94  |         contentType: 'application/json',
  95  |         body: JSON.stringify({
  96  |           total_inventory_value: 0,
  97  |           total_adjustments_count: 0,
  98  |           items: []
  99  |         })
  100 |       });
  101 |     });
  102 | 
  103 |     await page.route('**/reports/installments/**', async (route) => {
  104 |       await route.fulfill({
  105 |         status: 200,
  106 |         contentType: 'application/json',
  107 |         body: JSON.stringify({
  108 |           total_collected: 0,
  109 |           salesperson_breakdown: [{ salesperson_id: 1, salesperson_name: 'Test', total_collected: 100 }]
  110 |         })
  111 |       });
  112 |     });
  113 | 
  114 |     // Bypass login by setting localStorage
  115 |     await page.goto('/');
  116 |     await page.evaluate(() => {
  117 |       localStorage.setItem('token', 'mock-token');
  118 |       localStorage.setItem('branchId', '1');
  119 |     });
  120 |   });
  121 | 
  122 |   test('Dashboard Report loads successfully', async ({ page }) => {
  123 |     await page.goto('/reports/dashboard');
  124 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  125 |     await expect(page.getByText('تفاصيل السيولة')).toBeVisible();
  126 |     await expect(page.getByText('تفاصيل المكسب')).toBeVisible();
  127 |   });
  128 | 
  129 |   test('Receipts Report tab loads as read-only', async ({ page }) => {
  130 |     await page.goto('/reports/receipts');
  131 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  132 |     await expect(page.locator('table')).toBeVisible();
  133 |     await expect(page.locator('button', { hasText: 'إضافة فاتورة' })).toHaveCount(0);
  134 |   });
  135 | 
  136 |   test('Installments Report tab loads successfully', async ({ page }) => {
  137 |     await page.goto('/reports/installments');
  138 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
> 139 |     await expect(page.getByText('إجمالي التحصيلات')).toBeVisible();
      |                                                      ^ Error: expect(locator).toBeVisible() failed
  140 |   });
  141 | 
  142 |   test('Expenses Report tab loads as read-only', async ({ page }) => {
  143 |     await page.goto('/reports/expenses');
  144 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  145 |     await expect(page.locator('table')).toBeVisible();
  146 |     await expect(page.locator('button', { hasText: 'إضافة' })).toHaveCount(0);
  147 |   });
  148 | 
  149 |   test('Profit & Loss Report tab loads successfully', async ({ page }) => {
  150 |     await page.goto('/reports/profit-and-loss');
  151 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  152 |     await expect(page.locator('.card-body .fw-bold').first()).toBeVisible();
  153 |   });
  154 | 
  155 |   test('Inventory Movement Report tab loads successfully', async ({ page }) => {
  156 |     await page.goto('/reports/inventory');
  157 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  158 |     await expect(page.locator('table th')).toHaveCount(10);
  159 |   });
  160 | 
  161 |   test('Salesperson Performance Report tab loads successfully', async ({ page }) => {
  162 |     await page.goto('/reports/salesperson');
  163 |     await expect(page.locator('.spinner-border')).not.toBeVisible();
  164 |     await expect(page.locator('.card-body .fw-bold.fs-3')).toHaveCount(4);
  165 |     await expect(page.locator('table th')).toHaveCount(9);
  166 |   });
  167 | });
  168 | 
```