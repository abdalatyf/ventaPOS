# VentaPOS NextGen Reporting Subsystem — Comprehensive Specification Analysis

**Generated:** 2026-09-01  
**Scope:** Reporting Subsystem Survey & Full Specification Extraction (R1, R2, R3, UI/UX Guidelines, Backend Contracts)  
**SSoT Sources:** `requirements.md`, `REPORTS_AGREEMENT.md`, `AGENTS.md`, `UI_UX_RULES.md`, `TABLE_UX_GUIDELINES.md`, `Desktop/sales/salesapp/views/` (Legacy Reference).

---

## 1. Executive Summary & Architecture Overview

VentaPOS NextGen Reporting is a back-office analytical suite designed for a single business owner (المدير / صاحب المحل) managing multiple branch locations. Sales in the field are performed by salespeople (مناديب) via paper notebooks and recorded from the desktop.

### Core Architectural Rules
1. **Date Engine**: Strict **Monthly Business Accounting** (`month` 1-12, `year` YYYY). No daily date pickers in report headers. Display format is strictly `MM/YYYY` (e.g. `٨/٢٠٢٦` - month first, no leading zero on display).
2. **Numeric Localization**: User-facing numbers use Arabic-Indic digits (`٠١٢٣٤٥٦٧٨٩`). Thousand separators use `,` (or `،`). Storage and API parameters use standard Western ASCII digits (`0-9`).
3. **Currency Display**: Egyptian market convention uses integer rounding (`Math.round`) for monetary summary cards and table rows without `.00` clutter unless explicitly decimal.
4. **UI Framework**: Tabler / Bootstrap 5 + custom glassmorphism card styling (`.card`, `.table-sticky-header`, `.sticky-toolbar`). Cairo font. Strictly RTL layout.
5. **No `<select>` for Dynamic Entities**: All dynamic entities (Salespersons, Inventory Items, Customers, Areas) MUST use searchable autocompletes (`ReportAutocomplete`), NOT raw HTML `<select>` elements. Fixed enums (e.g., Sale Type: All / Cash / Installment) may use `<select>`.
6. **No Footers for Totals (`<tfoot>`)**: All report totals and aggregate KPIs are displayed as Top Summary Cards via `<ReportTable summaryCards={...} />`.
7. **Drill-Down Navigation**: Aggregated figures and table identifiers (receipt numbers, salesperson sales, items) provide direct clickable drill-down links to relevant detail reports with pre-filled query parameters (`?year=YYYY&month=MM&salesperson_id=...`).

---

## 2. Features Discovered & Inventory Table

| # | Category | Feature / Page | Description | Inputs / Query Params | Outputs / Payload | Error Behavior | SSoT / Discovered Via |
|---|----------|----------------|-------------|-----------------------|-------------------|----------------|----------------|
| 1 | R1: Utilities | `fmtNum` | Formats numeric/monetary values with thousand separators as integer | Numeric string or number | Formatted string (e.g., `"1,500"`) | `0` on `null`/`undefined`/`NaN` | `formatUtils.js`, `REPORTS_AGREEMENT.md` |
| 2 | R1: Utilities | `toArabic` | Converts Western digits `0-9` to Arabic-Indic `٠-٩` | String or number | Arabic-Indic string (`"١٥٠٠"`) | `""` on `null`/`undefined` | `UI_UX_RULES.md` §6.3 |
| 3 | R1: Utilities | `ReportAutocomplete` | Searchable dropdown input for salespersons, items, and text fields with debounce & clear | `items`, `value`, `onChange`, `onSelect`, `displayKey`, `idKey`, `searchKeys`, `placeholder` | Selected item object or string | Graceful empty list fallback | `UI_UX_RULES.md` §6.1, `REPORTS_AGREEMENT.md` |
| 4 | R2: Backend | `ReceiptViewSet` Filtering | Filter receipts by number range, date, salesperson, customer, area | `receipt_from`, `receipt_to`, `year`, `month`, `salesperson_id`, `customer_name`, `phone`, `area`, `is_cash_sale`, `has_down_payment` | Paginated JSON with `results`, `count`, `aggregate` (total_sales, total_cash, total_down_payments) | 400 on invalid param format | `backend/api/views.py:1119-1130` |
| 5 | R2: Backend | `DashboardReportView` | Financial summary KPIs, cash drawer summary, top products, top areas | `branch_id`, `year`, `month` | `{ period, kpis, cash_drawer_summary, top_products, top_areas }` | 400 if `branch_id` missing/invalid | `views.py:1651`, legacy `branch_views.py` |
| 6 | R2: Backend | `SalespersonPerformanceReportView` | Per-salesperson breakdown of cash/credit sales, collections, and salaries | `branch_id`, `year`, `month` | `{ totals: {...}, salespersons: [...] }` | 400 if `branch_id` missing | `views.py:1900`, legacy `dashboard.html` |
| 7 | R2: Backend | `InventoryMovementReportView` | Time-machine stock movement per product (opening, purchases, returns, sales, adjustments, final stock, valuation) | `branch_id`, `year`, `month` | `{ total_inventory_value, total_adjustments_count, items: [...] }` | 400 if `branch_id` missing | `views.py:2020`, legacy `report_views.py` |
| 8 | R2: Backend | `ProfitAndLossReportView` | P&L per product split into Cash Sales & Installment Sales | `branch_id`, `year`, `month`, `salesperson_id` | `{ summary: {...}, cash_sales_profitability: [...], installment_sales_profitability: [...] }` | 400 if `branch_id` missing | `views.py:2150`, legacy `report_views.py` |
| 9 | R2: Backend | `InstallmentsReportView` | Installment collection schedules & ledger with multi-column filtering | `branch_id`, `year`, `month`, `salesperson_id`, `sale_from_year`, `sale_from_month`, `sale_to_year`, `sale_to_month`, `customer_name`, `phone`, `area` | `{ total_installments_amount, installments_count, installments: [...] }` | 400 if `branch_id` missing | `views.py:2427`, legacy `collections_views.py` |
| 10 | R2: Backend | `CashDrawerReportView` | Detailed atomic cash inflows: cash sales receipts, installment down payments, collected installments | `branch_id`, `year`, `month` | `{ cash_sales: [...], down_payments: [...], collections: [...] }` | 400 if `branch_id` missing | `views.py:2334` |
| 11 | R3: Frontend | Dashboard Report (`/reports/dashboard`) | High-level 2-card financial breakdown: "تفاصيل المكسب" (P&L breakdown) and "تفاصيل السيولة" (Cash Flow breakdown) with full drill-down | Context `year`, `month`, `branchId` | Rendered summary tables with drill-down routes | Alert banner on API error | `DashboardReport.jsx`, `REPORTS_AGREEMENT.md` |
| 12 | R3: Frontend | Salesperson Performance Report (`/reports/salesperson`) | Comprehensive performance table with grouped headers (Sales Performance, Collections, Salary Details) and summary cards | Context `year`, `month`, `branchId`, filter by salesperson name/number | Grouped table with 10 columns, 7 KPI cards, sorting | Empty state icon when no data | `SalespersonPerformanceReport.jsx`, `REPORTS_AGREEMENT.md` §7 |
| 13 | R3: Frontend | Inventory Movement Report (`/reports/inventory`) | 10-column inventory movement ledger (Opening, Purchases, Sales Returns, Sales, Purchase Returns, Deficit, Final Stock, Unit Cost, Total Value) | Context `year`, `month`, `branchId`, search product name/number, filter salesperson | 10 columns, 8 KPI summary cards, sorting | Empty state message | `InventoryMovementReport.jsx`, `REPORTS_AGREEMENT.md` §6 |
| 14 | R3: Frontend | Profit & Loss Report - Totals (`/reports/profit-and-loss`) | Product profitability with total revenue, total cost, sales comm, collection comm, total profit | Context `year`, `month`, `branchId`, filter product, salesperson, sale type | 7 columns, 6 KPI cards, sorting | Empty state message | `ProfitAndLossReport.jsx`, `REPORTS_AGREEMENT.md` §4 |
| 15 | R3: Frontend | Profit & Loss Report - Averages (`/reports/averages`) | Per-unit product averages: avg sell price, unit cost, avg sales comm, avg coll comm, avg profit | Context `year`, `month`, `branchId`, filter product, salesperson, sale type | 7 columns (per unit), 0 KPI cards (per spec), sorting | Empty state message | `AveragesReport.jsx`, `REPORTS_AGREEMENT.md` §5 |
| 16 | R3: Frontend | Installments Report (`/reports/installments`) | Installment collection schedule report with batch selection & printing | Context `year`, `month`, `branchId`, salesperson autocomplete, sale period range, customer, phone, area | 9 columns, 2 KPI cards, multi-level sorting, checkbox selection | Empty state message | `InstallmentsReport.jsx`, `REPORTS_AGREEMENT.md` §2 |
| 17 | R3: Frontend | Expenses Report (`/reports/expenses`) | Monthly branch operating expenses listing | Context `year`, `month`, `branchId`, search description, amount range | 4 columns, 2 KPI cards, sorting | Empty state message | `ExpensesReport.jsx`, `REPORTS_AGREEMENT.md` §3 |
| 18 | R3: Frontend | Sales Invoices / Receipts Report (`/reports/receipts`) | Full sales receipts listing with infinite scroll, salesperson autocomplete, number range, and payment breakdown | Context `year`, `month`, `branchId`, sale type select, salesperson autocomplete, receipt range, customer, phone, area | 8 columns, 4 KPI cards, drill-down to POS edit | Empty state message | `ReceiptsReport.jsx`, `invoices_report.html` |

---

## 3. Detailed Specification for R1: Shared Utilities & Autocomplete

### 3.1 `ReportAutocomplete.jsx` Specification
- **Purpose**: A lightweight, unified, searchable autocomplete component tailored for table filter toolbars in reports.
- **Props Interface**:
  - `items`: `Array<Object | String>` (Pre-fetched list of options, e.g. salespersons or areas).
  - `fetchSuggestions`: `Function(query: string) => Promise<Array>` (Optional async search function).
  - `value`: `String` (The currently displayed input text).
  - `onChange`: `Function(value: string)` (Handler called when text is typed).
  - `onSelect`: `Function(item: Object | String | null)` (Handler called when an option is selected or cleared).
  - `placeholder`: `String` (Placeholder text in Arabic, e.g. `"ابحث عن مندوب..."`).
  - `displayKey`: `String` (Object key to display, default `"name"`).
  - `idKey`: `String` (Object key representing ID, default `"id"`).
  - `searchKeys`: `Array<String>` (Object keys to match against when filtering client-side, e.g. `['name', 'local_id']`).
  - `className`: `String` (Custom CSS class, default `"form-control form-control-sm"`).
  - `allowClear`: `Boolean` (Whether to render a clear `×` button when value is non-empty, default `true`).
  - `style`: `Object` (Wrapper inline styling).
- **Behaviors**:
  - **Debounce**: 200–300ms debounce on keystrokes when querying async suggestions. Instant client-side filtering for static `items`.
  - **Keyboard Navigation**:
    - `ArrowDown`: Moves selection down the dropdown list.
    - `ArrowUp`: Moves selection up the dropdown list.
    - `Enter`: Selects the currently highlighted item and closes dropdown without submitting the enclosing form.
    - `Escape`: Closes the dropdown list.
  - **Clear Behavior**:
    - Clicking the clear `×` button triggers `onChange('')` and `onSelect(null)`, clearing the filter instantly.
    - Blurring the input with empty text clears any previously selected ID.
  - **RTL & Popup Styling**:
    - Popup positioned absolutely directly below input (`top: 100%`, `right: 0`, `left: 0`, `z-index: 1060`).
    - Max height: `220px` with vertical scroll (`overflowY: 'auto'`).
    - High-contrast hover/active state (`bg-light`, `text-primary fw-bold`).

### 3.2 `fmtNum` Specification
- **Input**: Any number, numeric string, `null`, or `undefined`.
- **Logic**:
  1. Handle edge cases: if `val === null || val === undefined || isNaN(val)`, return `"0"`.
  2. Parse to float/integer: `const n = Math.round(Number(val))`.
  3. Format with thousand separators: `n.toLocaleString('en-US')`.
- **Output**: Clean integer string with comma separators (e.g. `0` -> `"0"`, `1500` -> `"1,500"`, `2500000.75` -> `"2,500,001"`).

### 3.3 `toArabic` Specification
- **Input**: Any string, number, `null`, or `undefined`.
- **Logic**:
  1. If `val === null || val === undefined`, return `""`.
  2. Convert to string: `String(val)`.
  3. Replace ASCII digits `0-9` with Arabic-Indic glyphs `٠١٢٣٤٥٦٧٨٩` using regex `/\d/g`.
  4. Date formatting helper: if a date object/ISO string is passed for monthly dates, format as `M/YYYY` (e.g. `8/2026`) and convert to `٨/٢٠٢٦`.
- **Output**: Pure Arabic-Indic text string.

---

## 4. Detailed Specification for R2: Backend Fixes & API Contracts

### 4.1 `receipt_from` and `receipt_to` Query Parameter Handling
- **Location**: `backend/api/views.py` inside `ReceiptViewSet.get_queryset()`.
- **Root Cause of Bug**: Current code does `qs.filter(receipt_number__gte=clean_rf)` where `clean_rf` is a string. In SQLite, comparing integer column `receipt_number` against string `"10"` vs `"2"` causes string collation bugs.
- **Fixed Specification**:
  ```python
  if receipt_from := params.get("receipt_from"):
      clean_rf = to_english_numerals(str(receipt_from).strip())
      if clean_rf.isdigit():
          qs = qs.filter(receipt_number__gte=int(clean_rf))

  if receipt_to := params.get("receipt_to"):
      clean_rt = to_english_numerals(str(receipt_to).strip())
      if clean_rt.isdigit():
          qs = qs.filter(receipt_number__lte=int(clean_rt))
  ```

### 4.2 `إجمالي المقدمات` (Total Down Payments) KPI Logic
- **Requirements**:
  1. **Dashboard Endpoint (`/api/v1/reports/dashboard/summary/`)**:
     - `down_payment_inflow = Receipt.objects.filter(branch_id=branch_id, sale_month=month, sale_year=year, is_cash_sale=False, is_deleted=False).aggregate(s=Sum('down_payment'))['s'] or 0`
     - Must be returned in `cash_drawer_summary.down_payment_inflow`.
  2. **Receipts Endpoint (`/api/v1/receipts/`)**:
     - When paginated, the response metadata must include overall query aggregate totals (not just current page slice):
       - `total_sales`: Sum of `total_amount` for all matching receipts.
       - `total_cash`: Sum of `total_amount` for matching receipts where `is_cash_sale=True`.
       - `total_down_payments`: Sum of `down_payment` for matching receipts where `is_cash_sale=False`.
     - Key structure in response:
       ```json
       {
         "count": 120,
         "next": "...",
         "previous": null,
         "total_amount_sum": 450000,
         "aggregate": {
           "total_sales": 450000,
           "total_cash": 180000,
           "total_down_payments": 75000
         },
         "results": [...]
       }
       ```

### 4.3 Array Extraction Contracts Across All Endpoints
| Endpoint | Method | Backend JSON Response Key | Frontend Component | Required Extraction Key |
|---|---|---|---|---|
| `/api/v1/reports/dashboard/` | GET | `kpis`, `cash_drawer_summary`, `top_products`, `top_areas` | `DashboardReport.jsx` | `data.kpis`, `data.cash_drawer_summary` |
| `/api/v1/reports/salesperson-performance/` | GET | `salespersons`, `totals` | `SalespersonPerformanceReport.jsx` | `data.salespersons` (Array), `data.totals` (Object) |
| `/api/v1/reports/inventory-movement/` | GET | `items`, `total_inventory_value`, `total_adjustments_count` | `InventoryMovementReport.jsx` | `data.items` (Array), `data.total_inventory_value` |
| `/api/v1/reports/profit-and-loss/` | GET | `cash_sales_profitability`, `installment_sales_profitability`, `summary` | `ProfitAndLossReport.jsx`, `AveragesReport.jsx` | `data.cash_sales_profitability`, `data.installment_sales_profitability`, `data.summary` |
| `/api/v1/reports/installments/` | GET | `installments`, `total_installments_amount`, `installments_count` | `InstallmentsReport.jsx` | `data.installments` (Array), `data.total_installments_amount`, `data.installments_count` |
| `/api/v1/reports/cash-drawer/` | GET | `cash_sales`, `down_payments`, `collections` | `CashDrawerReportView` | `data.cash_sales`, `data.down_payments`, `data.collections` |
| `/api/v1/expenses/` | GET | `results` (or array) | `ExpensesReport.jsx` | `Array.isArray(res.data.results) ? res.data.results : res.data` |
| `/api/v1/receipts/` | GET | `results`, `count`, `aggregate` | `ReceiptsReport.jsx` | `data.results` (Array), `data.count`, `data.aggregate` |

---

## 5. Detailed Specification for R3: 7 Report Pages Breakdown

### Page 1: Dashboard Report (`/reports/dashboard`)
- **Route**: `/reports/dashboard`
- **Layout**: 2 side-by-side high-density cards:
  1. **تفاصيل المكسب (P&L Breakdown)**:
     - Rows:
       - إجمالي المبيعات (`data.kpis.total_revenue`) -> Drill-down to `/reports/receipts?year=Y&month=M`
       - تكلفة البضاعة (سعر الشراء) (`- data.kpis.total_cogs`) -> Drill-down to `/reports/profit-and-loss?year=Y&month=M`
       - إجمالي المندبة (`- data.kpis.total_sales_commissions`) -> Drill-down to `/reports/profit-and-loss?year=Y&month=M`
       - إجمالي عمولة التحصيل (`- data.kpis.total_collection_commissions`) -> Drill-down to `/reports/profit-and-loss?year=Y&month=M`
       - إجمالي المصروفات (`- data.cash_drawer_summary.operating_expenses`) -> Drill-down to `/reports/expenses?year=Y&month=M`
     - Footer / Highlight: صافي المكسب (`data.kpis.estimated_net_profit`)
  2. **تفاصيل السيولة (Cash Flow / Drawer Breakdown)**:
     - Rows:
       - (+) مبيعات كاش (`data.cash_drawer_summary.cash_sales_inflow`) -> Drill-down to `/reports/receipts?year=Y&month=M&is_cash_sale=true`
       - (+) المقدمات (`data.cash_drawer_summary.down_payment_inflow`) -> Drill-down to `/reports/receipts?year=Y&month=M&has_down_payment=true`
       - (+) التحصيل (`data.cash_drawer_summary.collection_inflow`) -> Drill-down to `/reports/installments?year=Y&month=M`
       - (=) إجمالي الوارد (`data.cash_drawer_summary.total_cash_inflow`)
       - (-) إجمالي المشتريات (`- data.cash_drawer_summary.total_purchases`) -> Drill-down to `/search-purchases?year=Y&month=M`
       - (-) إجمالي المرتبات (`- data.cash_drawer_summary.auto_salaries`) -> Drill-down to `/reports/salesperson?year=Y&month=M`
       - (-) إجمالي المصروفات (`- data.cash_drawer_summary.operating_expenses`) -> Drill-down to `/reports/expenses?year=Y&month=M`
       - (=) إجمالي الصادر (`- (total_purchases + auto_salaries + operating_expenses)`)
     - Footer / Highlight: صافي السيولة (`data.cash_drawer_summary.net_cash_in_hand`)

---

### Page 2: Salesperson Performance Report (`/reports/salesperson`)
- **Route**: `/reports/salesperson`
- **Columns (Grouped Header Architecture)**:
  1. `salesperson`: اسم المندوب (Text, Align Right)
  2. `receipts_count`: عدد الفواتير (Badge link to `/reports/receipts?year=Y&month=M&salesperson_id=ID`)
  3. **أداء المبيعات (Sales Performance Group)**:
     - `cash_sales`: كاش (Currency link to `/reports/receipts?year=Y&month=M&salesperson_id=ID&is_cash_sale=true`)
     - `credit_sales`: قسط (Currency link to `/reports/receipts?year=Y&month=M&salesperson_id=ID&is_cash_sale=false`)
     - `total_sales_val`: إجمالي المبيعات (Currency link to `/reports/receipts?year=Y&month=M&salesperson_id=ID`)
  4. **تحصيل الشهر (Collections Group)**:
     - `collected`: تحصيل (Currency link to `/reports/installments?year=Y&month=M&salesperson_id=ID`)
  5. **تفاصيل المرتب (Salary Details Group)**:
     - `comm_sales`: المندبة (Currency)
     - `comm_coll`: عمولة تحصيل (Currency)
     - `due_salary`: المرتب المستحق (Currency, Dark/Bold Highlight)
- **Subfilters**:
  - `ReportAutocomplete` for salesperson search (by name or ID) with clear button.
- **KPI Summary Cards**:
  1. إجمالي الفواتير (`data.totals.grand_total_receipts` or calculated sum of counts)
  2. إجمالي المبيعات كاش (`data.totals.grand_total_cash`)
  3. إجمالي المبيعات قسط (`data.totals.grand_total_credit`)
  4. إجمالي المبيعات (`data.totals.grand_total_sales`)
  5. إجمالي التحصيل (`data.totals.grand_total_collected`)
  6. إجمالي المندبة (`data.totals.grand_total_comm_sales`)
  7. إجمالي المرتبات المستحقة (`data.totals.grand_total_due`)

---

### Page 3: Inventory Movement Report (`/reports/inventory`)
- **Route**: `/reports/inventory`
- **Columns (10 Columns Exact)**:
  1. `product_name`: الصنف (Text, Align Right)
  2. `opening_stock`: رصيد أول / الكمية قبل (Integer)
  3. `purchases`: المشتريات (+) (Integer, Green text `+X`)
  4. `returns`: مرتجع مبيعات (+) / مرتجع مشتريات (-) (Integer per sign)
  5. `sales`: المبيعات (-) (Integer, `-X`)
  6. `surplus`: الزيادة (+) (Integer, Green text `+X`)
  7. `deficit`: العجز (-) (Integer, Red text `-X`)
  8. `final_stock`: رصيد آخر / الكمية بعد (Badge Info highlight)
  9. `unit_cost`: تكلفة الوحدة / سعر الشراء الحالي (Currency)
  10. `total_value`: إجمالي القيمة (Currency, Bold Green)
- **Subfilters**:
  - Search input / `ReportAutocomplete` for Product Name.
- **KPI Summary Cards (8 Cards Exact)**:
  1. رصيد أول (Sum of Opening Stock)
  2. المشتريات (+) (Sum of Purchases)
  3. مرتجع مبيعات (+) (Sum of Sales Returns)
  4. المبيعات (-) (Sum of Sales)
  5. مرتجع مشتريات (-) (Sum of Purchase Returns)
  6. العجز (-) (Sum of Deficits)
  7. رصيد آخر (Sum of Final Stock)
  8. إجمالي القيمة (Total Inventory Valuation)

---

### Page 4: Profit & Loss Report - Totals (`/reports/profit-and-loss`)
- **Route**: `/reports/profit-and-loss`
- **Columns (7 Columns Exact)**:
  1. `name`: الصنف (Text, Align Right)
  2. `qty`: الكمية المباعة (Integer)
  3. `total_rev`: إجمالي الإيراد / المبيعات (Currency)
  4. `total_cost`: إجمالي التكلفة (Currency, Red text)
  5. `total_sales_comm`: إجمالي المندبة (Currency, Red text)
  6. `total_coll_comm`: إجمالي عمولة التحصيل (Currency, Red text; displays `'-'` for cash sales)
  7. `total_profit`: إجمالي المكسب / الربح (Currency, Bold Green)
- **Subfilters**:
  - Product `ReportAutocomplete`.
  - Salesperson `ReportAutocomplete`.
  - Sale Type `<select>` (`الكل`, `كاش فقط`, `قسط فقط`).
- **KPI Summary Cards (6 Cards Exact)**:
  1. المبيعات (`totals.revenue`)
  2. التكلفة (-) (`totals.cost`)
  3. المندبة (-) (`totals.salesCommission`)
  4. عمولة التحصيل (-) (`totals.collCommission`)
  5. المصروفات (-) (`totals.expenses`)
  6. صافي الربح (`totals.profit`)

---

### Page 5: Profit & Loss Report - Averages (`/reports/averages`)
- **Route**: `/reports/averages`
- **Columns (7 Columns Per Unit Exact)**:
  1. `name`: الصنف (Text, Align Right)
  2. `qty`: الكمية (Integer)
  3. `avg_sell`: متوسط سعر البيع (Currency)
  4. `cost_per_unit`: تكلفة الوحدة (Currency, Red text)
  5. `sales_comm_per_unit`: متوسط المندبة (Currency, Red text)
  6. `coll_comm_per_unit`: متوسط عمولة التحصيل (Currency, Red text; displays `'-'` for cash sales)
  7. `avg_profit`: متوسط المكسب للقطعة (Currency, Bold Green)
- **Subfilters**:
  - Product `ReportAutocomplete`.
  - Salesperson `ReportAutocomplete`.
  - Sale Type `<select>` (`الكل`, `كاش فقط`, `قسط فقط`).
- **KPI Summary Cards**:
  - **None (لا يوجد)** per `REPORTS_AGREEMENT.md` §5.

---

### Page 6: Installments Report (`/reports/installments`)
- **Route**: `/reports/installments`
- **Columns (9 Columns Exact)**:
  1. `receipt_num`: رقم الفاتورة (Clickable link to `/pos?edit=ID`)
  2. `area`: المنطقة (Text)
  3. `customer_name`: اسم العميل (Text, Bold Primary)
  4. `phone`: رقم الموبايل (Text)
  5. `amount`: مبلغ القسط (Currency, Bold Success)
  6. `salesperson_name`: المندوب (Text)
  7. `date`: تاريخ استحقاق القسط (`MM/YYYY`)
  8. `sale_date`: تاريخ البيع (`MM/YYYY`)
  9. `installment_system`: نظام التقسيط (Text)
- **Subfilters**:
  - `sale_from_month` & `sale_from_year` (Numeric inputs for sale start date).
  - `sale_to_month` & `sale_to_year` (Numeric inputs for sale end date).
  - Salesperson `ReportAutocomplete`.
  - Area `ReportAutocomplete` / Input.
  - Customer Name `ReportAutocomplete` / Input.
  - Phone `ReportAutocomplete` / Input.
- **KPI Summary Cards (2 Cards Exact)**:
  1. عدد الأقساط (Total Count of Installments)
  2. إجمالي التحصيل (Total Sum of Installment Amounts)

---

### Page 7: Expenses Report (`/reports/expenses`)
- **Route**: `/reports/expenses`
- **Columns (4 Columns Exact)**:
  1. `id` / `index`: رقم المصروف / # (Integer)
  2. `description`: البيان (Text, Align Right)
  3. `amount`: المبلغ (Currency, Bold Red)
  4. `date`: التاريخ (`MM/YYYY`)
- **Subfilters**:
  - Search input for Description (بحث في البيان).
  - Min amount input (من مبلغ).
  - Max amount input (إلى مبلغ).
- **KPI Summary Cards (2 Cards Exact)**:
  1. عدد المصروفات (Count of Expenses)
  2. إجمالي المصروفات (Total Sum of Expenses)

---

## 6. Edge Cases & Observed Behaviors Table

| # | Feature / Component | Input / Scenario | Expected / Observed Behavior | Source / Verification |
|---|---|---|---|---|
| 1 | `fmtNum` | `null`, `undefined`, `NaN`, `""` | Returns `"0"` without throwing runtime exception | `formatUtils.js` |
| 2 | `fmtNum` | `0` or `"0"` | Returns `"0"` | `formatUtils.js` |
| 3 | `fmtNum` | Decimal float `15420.85` | Rounds to integer `15421` and returns `"15,421"` | Market rules & `REPORTS_AGREEMENT.md` |
| 4 | `toArabic` | ASCII string `"Invoice #1002 - 07/2026"` | Returns `"Invoice #١٠٠٢ - ٠٧/٢٠٢٦"` | `UI_UX_RULES.md` §6.3 |
| 5 | `toArabic` | `null` or `undefined` | Returns `""` | `formatUtils.js` |
| 6 | `ReportAutocomplete` | User selects an option, then clears text input | Emits `onSelect(null)` and `onChange('')` to clear filter | `UI_UX_RULES.md` §9.2 |
| 7 | `ReportAutocomplete` | User presses Enter on focused item in dropdown | Selects item, closes popup, prevents premature form submit | `UI_UX_RULES.md` §5.4 |
| 8 | `ReceiptViewSet` Filter | `receipt_from="2"&receipt_to="10"` | Numeric query comparison `receipt_number >= 2 AND receipt_number <= 10` returns receipts 2 through 10 (not string order where 10 < 2) | `views.py:1119-1130` fix |
| 9 | `ReceiptViewSet` Filter | Arabic digits `receipt_from="٢"` | Sanitized via `to_english_numerals("٢")` -> `2` and filtered as integer | `views.py` |
| 10 | `InventoryMovement` | Product created in current month | Opening stock includes `initial_quantity`; opening stock before creation month shows 0 | `views.py:2079`, legacy `report_views.py` |
| 11 | `InventoryMovement` | Product with 0 movements in period | Displays opening stock = final stock, 0 sales/purchases, total value = `stock * price` | `views.py:2074-2141` |
| 12 | `SalespersonPerformance` | Salesperson with 0 sales and 0 collections | Row displays with 0 counts/amounts, salary = 0 | `views.py:1940-2005` |
| 13 | `ProfitAndLoss` Cash vs Credit | Cash sale item | Collection commission column is `0` / `'-'`, does not deduct collection reserve | `views.py:2239`, legacy `report_views.py` |
| 14 | `ProfitAndLoss` Proportional Coll Comm | Installment sale with down payment | Collection commission calculated as `(item_rev * (total_amount - down_payment) * 10%) / total_amount` | `views.py:2284`, legacy `report_views.py:47` |
| 15 | `InstallmentsReport` | Installment with null/empty customer name | Displays fallback `"بدون اسم"` without crashing | `views.py:2510` |
| 16 | `ReportsLayout` Master Bar | Month input change (e.g. `8` -> `9`) | URL query string immediately updates to `?year=2026&month=9` and child report automatically re-fetches | `ReportsLayout.jsx:35-46` |

---

## 7. Acceptance Criteria & Verification Checklist

- [ ] **R1 Utilities**:
  - `ReportAutocomplete` is implemented as a reusable component in `frontend/src/components/ReportAutocomplete.jsx` supporting both static `items` array and dynamic search, with debounce, keyboard navigation, clear button, and RTL styling.
  - `fmtNum` in `frontend/src/utils/formatUtils.js` formats numbers as integers with thousand separators and handles null/undefined/0/NaN safely.
  - `toArabic` in `frontend/src/utils/formatUtils.js` converts digits `0-9` to `٠-٩` and formats `MM/YYYY` dates properly.
- [ ] **R2 Backend**:
  - `receipt_from` and `receipt_to` in `ReceiptViewSet` sanitize Arabic digits, convert to integer, and filter `receipt_number__gte` and `receipt_number__lte` correctly.
  - `DashboardReportView` accurately computes `down_payment_inflow` for non-cash sales with down payments.
  - `ReceiptViewSet` returns overall aggregate totals (`total_sales`, `total_cash`, `total_down_payments`) in paginated responses.
  - `SalespersonPerformanceReportView` and `InventoryMovementReportView` arrays are extracted by the exact matching keys (`salespersons`, `items`) on the frontend.
- [ ] **R3 Frontend 7 Report Pages**:
  - `DashboardReport.jsx` renders financial breakdown cards with working drill-down navigation.
  - `SalespersonPerformanceReport.jsx` renders grouped table columns (Sales Performance, Collections, Salary Details), 7 KPI summary cards, and salesperson autocomplete.
  - `InventoryMovementReport.jsx` renders 10 columns, 8 KPI summary cards, and product search.
  - `ProfitAndLossReport.jsx` renders 7 columns, 6 KPI summary cards, product & salesperson autocompletes, and sale type select.
  - `AveragesReport.jsx` renders 7 per-unit columns and 0 KPI cards per spec.
  - `InstallmentsReport.jsx` renders 9 columns, 2 KPI summary cards, sale period range filters, and salesperson autocomplete.
  - `ExpensesReport.jsx` renders 4 columns, 2 KPI summary cards, description search, and amount range filters.
- [ ] **Verification**:
  - Backend tests pass (`python manage.py test api.tests`).
  - Frontend builds with zero errors (`npm run build`).
