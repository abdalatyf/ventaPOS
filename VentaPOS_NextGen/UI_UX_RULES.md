# VentaPOS NextGen — Frontend & UI/UX Architecture Bible

> **Supreme SSoT**: [`../APP_BIBLE.md`](../APP_BIBLE.md) · **Governance Rules**: [`../.agents/rules/rules.md`](../.agents/rules/rules.md)  
> **Scope**: Complete Frontend Visual Identity, Interaction Rules, 2-Scroll Table Architecture, and Audited Report Specifications  
> **Typography**: 'Cairo' Font · **Layout**: Fluid RTL · **Theme**: High-Contrast Light Mode  

---

## 1. Visual Identity & Brand Palette

The user interface reflects a clean, high-contrast desktop aesthetic designed for busy retail offices and warehouse environments.

### 1.1 Color System (Derived from Corporate Identity)
- **Primary Brand Color**: Deep Navy Blue (`#123F68`) — Used for primary headers, navigation active states, branding elements, and table titles.
- **Secondary / Accent Color**: Emerald Green (`#1DA368`) — Used for confirmation actions ("حفظ", "دفع", "تأكيد"), cash inflows, positive totals, and badges.
- **Danger Color**: Crimson (`#D63939`) — Used for cost deductions, purchase returns, expense figures, and delete actions.
- **Warning Color**: Amber (`#F59F00`) — Used for installment sales and pending states.
- **Info Color**: Cyan / Blue (`#206BC4`) — Used for down payments and closing stock quantities.
- **Surface & Backgrounds**: Crisp white (`#FFFFFF`) card surfaces on soft background (`#F8F9FA`).
- **Framework**: Tabler UI & Bootstrap v5 utilities with custom CSS. **No Tailwind CSS.**

### 1.2 Language & Tone of Voice
- **Strictly RTL & Arabic**: The entire application is rendered Right-to-Left in Arabic.
- **Commercial Egyptian Tone (لغة سوق مهنية ومبسطة)**:
  - Clear, authentic Egyptian trade vocabulary: (العميل, البضاعة, الخزنة, الفاتورة, الدفتر, النقدية, المندبة, المرتجع, كاش, قسط).
  - Avoid overly rigid academic translations and avoid excessive casual slang.

---

## 2. Layout & Data Density Principles

### 2.1 Fluid Width Containers
- All views, pages, and dialogs must use **fluid containers** (`container-fluid`) to leverage modern widescreen desktop monitors.
- Avoid fixed maximum widths (`container`) that cause wasted horizontal margins.

### 2.2 High Data Density
- Use compact padding (`p-2`, `py-1`, `table-sm`) and dense typography in data tables so the manager can inspect maximum rows at a single glance without scrolling.

### 2.3 Application Zoom Controls (`70%`–`150%` in `5%` Steps)
- **Bounds & Step**: `Navbar.jsx` enforces zoom clamping between `0.70` (`70%`) and `1.50` (`150%`), stepping by **`0.05` (`5%`)** increments via `window.zoomIn()`, `window.zoomOut()`, `window.resetZoom()` (`100%`), and keyboard shortcuts (`Ctrl + +`, `Ctrl + -`, `Ctrl + 0`).
- **Persistence & Layout Sync**: Zoom changes update `document.body.style.zoom` and CSS variable `--app-zoom`, persist to `localStorage` (`appZoomLevel`) and backend `CompanySetting.zoom_level`, and dispatch `app-zoom-changed` so `useSmartScroll.js` recalculates `.report-table-container` height accurately.

---

## 3. Keyboard-First Data Entry Rules

Because the manager transcribes transactions from physical paper notebooks, data entry speed is critical.

1. **Auto-Focus**: Every page or modal form must automatically focus its primary input on initial render.
2. **Enter Key Progression**: Pressing `Enter` in form inputs must move focus to the next logical input field. It must **never** trigger premature form submission.
3. **Tab-Indexing**: Logical `tabIndex` sequences must guide the operator through fields in natural reading order.
4. **Banned Input Types**:
   - **No `<select>` for Dynamic Entities**: Standard HTML `<select>` dropdowns are strictly prohibited for database entities (Products, Salespersons, Suppliers, Customers). You must use `ReportAutocomplete` or `Autocomplete`.
   - *Exception*: Standard `<select>` is only permissible for fixed, static enums (e.g. `Payment Type: CASH | INSTALLMENT` or `Status: ALL | ACTIVE`).
5. **Date Entry via Dual Numeric Fields**:
   - Native `<input type="date">` and `<input type="month">` are prohibited.
   - All date inputs must use **two separate numeric inputs** placed side-by-side: Month (`1-12`) and Year (4 digits).
6. **Date Display Format**:
   - Displayed dates must strictly follow `YYYY/MM` format (e.g. `2026/08` — year first with leading zero for single-digit months).
7. **Number & Digits Formatting Convention (UI vs Print)**:
   - **In App UI**: Western ASCII whole integers (`0-9`, `int` only, **NO `.00` decimals**) are required universally across all labels, table cells, summary cards, inputs, and API payloads.
   - **In Printing / PDFs**: All numbers on printed installment schedules, purchase invoices, and printed reports must use **Arabic-Indic numerals (`٠١٢٣٤٥٦٧٨٩`)** as whole integers via `ed2ad` / `to_arabic_numerals`.
8. **Thousands-Comma Sanitization**:
   - Before dispatching numeric inputs to the API, the frontend must strip thousands-separators (`.replace(/,/g, '')`) to prevent DRF DecimalField parsing errors.

---

## 4. Standardized Table Architecture (`StandardTablePageLayout.jsx` & 2-Scroll Architecture)

> [!NOTE]
> **Reconciliation Flag (Window-Level Sticky $\rightarrow$ 2-Scroll Architecture)**: Earlier versions of this spec (and the legacy docstring inside `StandardTablePageLayout.jsx`) described `2 × 48px` top rows (`Y = 231px`) and pure window-level sticky `<thead>` with `overflow: visible !important` on `.report-table-container`. The live codebase (`index.css`, `ReportTable.css`, `useSmartScroll.js`) implements the **2-Scroll Architecture** below with `52px` `.standard-top-row` height and a bounded `.report-table-container` height.

All 5 table/listing pages (`SearchReceipts.jsx`, `SearchPurchases.jsx`, `Expenses.jsx`, `Dimensions.jsx`, and `ReportsLayout.jsx` / `ReportTable.jsx`) share a single parent layout template (`StandardTablePageLayout.jsx`) that enforces a uniform top-section structure and the **2-Scroll Architecture**:

```
Unified 2-Scroll Table Architecture (StandardTablePageLayout.jsx + useSmartScroll.js)
┌────────────────────────────────────────────────────────┐
│ 1. Fixed Navbar (sticky-top, height: 56px, z: 1030)    │
├────────────────────────────────────────────────────────┤
│ 2. Top Section (.standard-page-top-section, scrolls):  │
│    - Header Banner (.standard-page-header: 48px)       │
│    - 2-Row Controls Card (.standard-top-card: 2×52px)  │
├────────────────────────────────────────────────────────┤
│ 3. Card Chrome (.sticky-toolbar: 48px, top: 56px)      │
│    - KPI summaryCards / bulk actions / Print / Sort    │
├────────────────────────────────────────────────────────┤
│ 4. Bounded Table Container (.report-table-container)   │
│    - Sticky <thead> th (top: 0 inside container, z1010)│
│    - Internal Y & X scroll (6px thin scrollbars)       │
└────────────────────────────────────────────────────────┘
```

### 4.1 Locked Top Section Height ("Title + 2 Rows")
- **Unified Top Section**: Every table page renders `.standard-page-top-section` containing:
  1. **Header Banner (`.standard-page-header`, fixed `48px` height)**: Page Icon + Title on the right, and `headerActions` on the left (`margin-bottom: 8px; padding-bottom: 6px`).
  2. **Unified 2-Row Controls Card (`.standard-top-card`, `2 × 52px` `.standard-top-row` rows in `index.css`)**:
     - **Row 1 (`.standard-top-row-1`, `52px`)**: Primary filters, tabs, and live search controls.
     - **Row 2 (`.standard-top-row-2`, `52px`)**: Inline add forms (`Expenses`, `Dimensions`), secondary filters, and status/reset controls.
- **React Portal Slots (`useStandardTableSlots`)**: Composite child components (`InventoryTab.jsx`, `SalespersonsTab.jsx`, `SuppliersTab.jsx`, and `ReportTable.jsx`) portal their `row1Extra` and `row2` controls directly into `.standard-top-card` without rendering extra accordions, filter cards, or `.card-header` bars above the table card.
- **No Footer Wrapper**: Table pages use a top wrapper only and never render a sticky bottom footer wrapper.
- **Scope Boundary**: Data-entry and specialized screens (`POS.jsx`, `PurchaseEntry.jsx`, `ReturnReceipt.jsx`, `ProductLedger.jsx`) retain their dedicated custom layouts (standalone sticky tables outside `.report-table-container`, e.g., `ProductLedger.jsx` and `SubscriptionTab.jsx`, use `:not(.report-table-container) > .table-sticky-header th` at `top: var(--navbar-height, 56px)`).

### 4.2 2-Scroll Architecture & Sticky Headers (`useSmartScroll.js`)
- **Scroll #1 (Window Scroll)**: As the user scrolls down, `.standard-page-top-section` (Header + 2-row `.standard-top-card`) scrolls out of view naturally until `.sticky-toolbar` (`48px` height, `position: sticky !important; top: var(--navbar-height, 56px) !important; z-index: 1020;`) meets the bottom edge of the fixed `Navbar`.
- **Scroll #2 (Bounded `.report-table-container` Internal Scroll)**:
  - `useSmartScroll.js` observes `header.navbar`, `.card`, `.sticky-toolbar`, `.sticky-selection-strip`, `.report-table-container`, and `<table>` via `ResizeObserver` (plus `resize`, `app-zoom-changed`, and `scroll` events) to dynamically set:
    `maxHeight = max(200px, calc((100vh / currentZoom) - offset))` (CSS fallback `calc((100vh / var(--app-zoom, 1)) - 114px)`).
  - Horizontal scroll (`overflow-x: auto`) is **always enabled** for wide matrices. Vertical scroll (`overflow-y`) toggles cleanly between `hidden` and `auto` when `.sticky-toolbar` touches the Navbar (`triggerTop <= navbarBottom + 4`) or the window reaches bottom.
- **Container-Relative Sticky `<thead>`**: Inside `.report-table-container`, `thead th` / `.report-sticky-header th` stick at `top: 0 !important` (`z-index: 1010`). For 2-level grouped headers (`SalespersonPerformanceReport.jsx`), `.report-sticky-header.level-2 th` sticks at `top: var(--header-row-1-height, 37px) !important` (`z-index: 1009`) measured dynamically via `ResizeObserver`.
- **6px Thin Scrollbars**: `index.css` and `ReportTable.css` enforce `scrollbar-width: thin` and `6px` (`width: 6px; height: 6px;`) custom WebKit scrollbars (`#c1c1c1` thumb on `#f1f1f1` track, `#94a3b8` hover) across `.report-table-container`, `.table-responsive`, `.hide-vertical-scroll`, and modals.

### 4.3 Sorting, Column Summaries & Keyboard Interaction Rules
1. **Direct Header Click-to-Sort**: Clicking any sortable column header (`<th>`) immediately toggles primary sorting (`asc` $\rightarrow$ `desc` $\rightarrow$ default) with visible directional indicator arrows (`↑` / `↓`). The multi-rule `"ترتيب حسب"` dropdown is retained for composite multi-column sorting and must dismiss automatically upon outside click or `Escape`.
2. **Report Totals in Top KPI `summaryCards` Only (No `<tfoot>`)**: All report and table totals live exclusively in the top KPI summary cards (`summaryCards`). Bottom summary rows (`<tfoot>`) are prohibited to maintain clean vertical scanability, eliminate double-scroll obstruction, and ensure consistent layout density.
3. **Tabular Numerals (`tabular-nums`)**: All numeric cells, monetary amounts, and KPI badges must enforce CSS `font-variant-numeric: tabular-nums` to ensure exact vertical digit alignment down columns.
4. **Table Keyboard Navigation**: When the table is focused, operators can navigate rows using `ArrowUp` (`↑`) and `ArrowDown` (`↓`), press `Space` to toggle checkbox selection (when multi-select is enabled), and press `Enter` to activate the row's primary drilldown link or action.
5. **Infinite Scrolling Protocol**: For paginated datasets (`ReceiptsReport`), `IntersectionObserver` attached to the final row of the dataset triggers asynchronous batch loading.

### 4.4 Standard Tabler Cards Only (No Glassmorphism / No `.premium-card`)
- All cards, panels, and modals across the application must use clean, standard Tabler/Bootstrap `.card` classes (`card`, `card-body`, `card-header`, `shadow-sm`).
- Glassmorphism, backdrop filters, custom decorative gradients, and `.premium-card` styles are strictly prohibited across all screens.

---

## 5. Audited Report Specifications (10 Reports)

The following specifications are verified against the active source implementations in `VentaPOS_NextGen/frontend/src/pages/reports/*.jsx` (10 reports hosted inside `ReportsLayout.jsx`, plus the standalone `ProductLedger.jsx` lifecycle view documented in §5.9). All Arabic headers, keys, subfilters, and KPIs are exact.

> [!NOTE]
> **Report Printing Behavior (`ReportsLayout` Top Bar vs `ReportTable` Toolbar)**:
> - **Standard `ReportTable` Reports**: `ReportTable.jsx` renders a `"طباعة"` button inside `.sticky-toolbar` and registers a default handler with `ReportsLayout.jsx` (`registerPrintHandler`) so both the top-bar `"طباعة التقرير"` button and toolbar `"طباعة"` button open `PrintModal.jsx` (printer selection, immediate print, or PDF preview via `POST /api/v1/reports/desktop_print/`).
> - **Direct PDF Preview Exception (`PurchasesReport.jsx` & `AreasReport.jsx`)**: Both register a custom `registerPrintHandler` that calls `POST /api/v1/reports/desktop_print/` directly with `action: 'view'` on the top-bar `"طباعة التقرير"` click (opening instant PDF preview without `PrintModal`), while their `.sticky-toolbar` `"طباعة"` button inside `ReportTable` still opens `PrintModal.jsx` for printer selection or PDF preview.

---

### 5.1 لوحة التحكم / الملخص (`DashboardReport.jsx`)
Features a 2-card financial breakdown with drill-down links to detailed reports and live branch filters.

#### Subfilters
- **المندوب**: `ReportAutocomplete` searchable dropdown.
- **المنطقة**: `ReportAutocomplete` backed by `/customer-suggestions/?field=area`.
- **إلغاء الفلاتر**: Quick reset button (visible when salesperson or area filter is active).

#### Card 1: تفاصيل المكسب (P&L Breakdown)
- **إجمالي المبيعات** (`kpis.total_revenue`) $\rightarrow$ Click navigates to `/reports/receipts`
- **تكلفة البضاعة (سعر الشراء) (-)** (`kpis.total_cogs`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي المندبة (-)** (`kpis.total_sales_commissions`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي عمولة التحصيل (-)** (`kpis.total_collection_commissions`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي المصروفات (-)** (`cashSummary.operating_expenses`) $\rightarrow$ Click navigates to `/reports/expenses`
- **خسائر العجز (-)** (`kpis.total_deficit_loss`) $\rightarrow$ Click navigates to `/reports/inventory`
- **صافي المكسب** (`kpis.estimated_net_profit`)

#### Card 2: تفاصيل السيولة (Cash Drawer Breakdown)
- **(+) مبيعات كاش** (`cashSummary.cash_sales_inflow`) $\rightarrow$ Click navigates to `/reports/receipts?${dateParams}&is_cash_sale=true`
- **(+) المقدمات** (`cashSummary.down_payment_inflow`) $\rightarrow$ Click navigates to `/reports/receipts?${dateParams}&has_down_payment=true`
- **(+) التحصيل** (`cashSummary.collection_inflow`) $\rightarrow$ Click navigates to `/reports/installments?${dateParams}`
- **(+) مرتجع مشتريات** (`cashSummary.purchase_returns_total`) $\rightarrow$ Click navigates to `/reports/purchases?${dateParams}&invoice_type=RETURN`
- **(=) إجمالي الوارد** (`cashSummary.total_cash_inflow`)
- **(-) إجمالي المشتريات** (`cashSummary.total_purchases`) $\rightarrow$ Click navigates to `/reports/purchases?${dateParams}&invoice_type=PURCHASE`
- **(-) مرتجع مبيعات** (`cashSummary.sales_returns_cash`) $\rightarrow$ Click navigates to `/reports/receipts?${dateParams}&receipt_type=RETURN`
- **(-) إجمالي المرتبات** (`cashSummary.auto_salaries`) $\rightarrow$ Click navigates to `/reports/salesperson?${dateParams}`
- **(-) إجمالي المصروفات** (`cashSummary.operating_expenses`) $\rightarrow$ Click navigates to `/reports/expenses?${dateParams}`
- **(=) إجمالي الصادر** (`totalOutgoing`)
- **صافي السيولة** (`cashSummary.net_cash_in_hand`)

---

### 5.2 تحصيل الأقساط (`InstallmentsReport.jsx`)

#### Columns (7 Columns)
1. **رقم الفاتورة** (`receipt_num`): Sequential receipt ID with drilldown link to POS edit.
2. **المنطقة** (`area`): Customer geographic zone.
3. **اسم العميل** (`customer_name`): Customer full name.
4. **رقم الموبايل** (`phone`): Customer phone number.
5. **مبلغ القسط** (`amount`): Monthly installment amount due.
6. **المندوب** (`salesperson_name`): Assigned salesperson name.
7. **تاريخ البيع** (`sale_date`): Original sale date in `YYYY/MM` format.

#### Subfilters
- **Row 1**: **المندوب** (`ReportAutocomplete`), **العميل** (`DebouncedInput`), **المنطقة** (`ReportAutocomplete` backed by `/customer-suggestions/?field=area`).
- **Row 2**: **الموبايل** (`DebouncedInput`), **إعادة ضبط** button. *(Reconciliation Note: Earlier spec listed `من تاريخ بيع` / `إلى تاريخ بيع` and plain-text `المنطقة`; current `InstallmentsReport.jsx` filters the selected payment month/year from `ReportsLayout` and uses `ReportAutocomplete` for `المنطقة`.)*

#### Summary KPIs (3 Cards)
- **تاريخ الدفع**: Active payment month/year.
- **عدد الأقساط**: Total installment count for selected month.
- **إجمالي التحصيل**: Total sum of installment cash due.

---

### 5.3 المصروفات (`ExpensesReport.jsx`)

#### Columns (5 Columns)
1. **رقم المصروف** (`id`): Sequential expense identifier.
2. **التصنيف** (`category`): Expense category badge (e.g., `إيجار`, `كهرباء ومياه`, `نقل ومشال`, `صيانة`, `نثريات`, `مصروفات عامة`).
3. **البيان** (`description`): Expense descriptive text.
4. **المبلغ** (`amount`): Monetary expenditure value.
5. **التاريخ** (`date`): Business period in `YYYY/MM` format.

#### Subfilters
- **التصنيف**: Autocomplete / category filter.
- **البيان**: Live debounced text search.
- **من مبلغ**: Minimum amount numeric filter.
- **إلى مبلغ**: Maximum amount numeric filter.

#### Summary KPIs
- **عدد المصروفات**: Total count of expense entries.
- **إجمالي المصروفات**: Cumulative monetary sum.

---

### 5.4 الأرباح والخسائر - إجماليات (`ProfitAndLossReport.jsx`)

#### Columns (7 Columns)
1. **الصنف** (`name`): Product trade name.
2. **الكمية المباعة** (`qty`): Total units sold.
3. **إجمالي الإيراد** (`total_rev`): Gross revenue generated.
4. **إجمالي التكلفة** (`total_cost`): Cumulative cost of goods sold.
5. **إجمالي المندبة** (`total_sales_comm`): Cumulative sales commission.
6. **إجمالي عمولة التحصيل** (`total_coll_comm`): Cumulative collection commission (shows "كاش" for cash sales).
7. **إجمالي المكسب** (`total_profit`): Net gross profit.

#### Subfilters
- **الصنف**: Product autocomplete dropdown.
- **نوع البيع**: Select (`الكل`, `كاش فقط`, `قسط فقط`).
- **المندوب**: Salesperson autocomplete dropdown.
- **المنطقة**: Area `ReportAutocomplete` (`/customer-suggestions/?field=area`).

#### Summary KPIs (7 Cards)
- **المبيعات**: Gross revenue sum.
- **التكلفة (-)**: Cumulative COGS.
- **المندبة (-)**: Cumulative sales commissions.
- **عمولة التحصيل (-)**: Cumulative collection commissions.
- **المصروفات (-)**: Operating branch expenses for the month.
- **خسائر العجز (-)**: Physical deficit financial losses for the month.
- **صافي الربح**: Final net profit after all deductions.

---

### 5.5 الأرباح والخسائر - متوسطات القطعة (`AveragesReport.jsx`)

#### Columns (7 Columns)
1. **الصنف** (`name`): Product trade name.
2. **الكمية** (`qty`): Total units sold.
3. **متوسط سعر البيع** (`avg_sell`): Average revenue per single unit.
4. **تكلفة الوحدة** (`cost_per_unit`): Purchase cost per unit.
5. **متوسط المندبة** (`sales_comm_per_unit`): Sales commission per unit.
6. **متوسط عمولة التحصيل** (`coll_comm_per_unit`): Collection commission per unit.
7. **متوسط المكسب للقطعة** (`avg_profit`): Average net profit per single unit.

#### Subfilters
- **الصنف**: Product autocomplete dropdown.
- **نوع البيع**: Select (`الكل`, `كاش فقط`, `قسط فقط`).
- **المندوب**: Salesperson autocomplete dropdown.
- **المنطقة**: Area `ReportAutocomplete` (`/customer-suggestions/?field=area`).

#### Summary KPIs
- **None**: Strictly 0 summary cards by design.

---

### 5.6 حركة المخزون (`InventoryMovementReport.jsx`)

#### Columns (10 Columns)
1. **الصنف** (`product_name`): Product trade name.
2. **رصيد أول** (`opening_stock`): Stock balance at beginning of month.
3. **المشتريات (+)** (`purchases`): Inbound supplier purchases.
4. **مرتجع مبيعات (+)** (`sales_returns`): Customer returns added back to stock.
5. **المبيعات (-)** (`sales`): Outbound customer sales.
6. **مرتجع مشتريات (-)** (`purchase_returns`): Returns to suppliers deducted from stock.
7. **العجز (-)** (`deficit`): Physical deficit adjustments.
8. **رصيد آخر** (`final_stock`): Closing stock at end of month.
9. **تكلفة الوحدة** (`unit_cost`): Purchase price per unit.
10. **إجمالي القيمة** (`total_value`): Closing inventory valuation (`final_stock * unit_cost`).

#### Subfilters
- **الصنف**: Product autocomplete dropdown.
- **المندوب**: Salesperson autocomplete dropdown.
- **المنطقة**: Area `ReportAutocomplete` (`/customer-suggestions/?field=area`).

#### Summary KPIs (8 Cards)
- **رصيد أول**: Total opening units across branch.
- **المشتريات (+)**: Total inbound purchase units.
- **مرتجع مبيعات (+)**: Total sales return units.
- **المبيعات (-)**: Total sold units.
- **مرتجع مشتريات (-)**: Total supplier return units.
- **العجز (-)**: Total deficit units.
- **رصيد آخر**: Total closing inventory units.
- **إجمالي القيمة**: Grand total inventory monetary value.

---

### 5.7 أداء المناديب (`SalespersonPerformanceReport.jsx`)

#### Grouped Header Hierarchy
```
┌─────────────────┬──────────────┬───────────────────────────────────────────┬──────────────┬─────────────────────────────────────────┐
│                 │              │                أداء المبيعات              │  تحصيل MM/YY │               تفاصيل المرتب             │
│   اسم المندوب   │ عدد الفواتير ├──────┬──────┬──────────┬──────────────────┤              ├──────────┬──────────────┬───────────────┤
│                 │              │ كاش  │ قسط  │ المقدمات │ إجمالي المبيعات  │              │  المندبة │ عمولة تحصيل  │ المرتب المستحق│
└─────────────────┴──────────────┴──────┴──────┴──────────┴──────────────────┴──────────────┴──────────┴──────────────┴───────────────┘
```

#### Subfilters
- **المندوب**: Autocomplete searchable dropdown.
- **المنطقة**: Area `ReportAutocomplete` (`/customer-suggestions/?field=area`).

#### Summary KPIs (7 Cards)
1. **إجمالي الفواتير**: Total receipts generated by sales force.
2. **مبيعات كاش**: Total volume of cash sales.
3. **مبيعات قسط**: Total volume of installment sales.
4. **إجمالي المقدمات**: Total down payment cash collected.
5. **إجمالي المبيعات**: Grand total sales volume.
6. **إجمالي التحصيل**: Total installment cash collected.
7. **إجمالي المرتبات المستحقة**: Total salaries earned by all salespersons.

---

### 5.8 فواتير المبيعات (`ReceiptsReport.jsx`)

#### Columns (7 Columns)
1. **رقم الفاتورة** (`receipt_number`): Sequential receipt ID with drilldown link to `/pos?edit={id}`.
2. **المندوب** (`salesperson`): Salesperson name.
3. **العميل** (`customer_name`): Customer full name.
4. **رقم الموبايل** (`phone`): Customer phone number.
5. **المنطقة** (`area`): Geographic zone.
6. **المقدم** (`down_payment`): Down payment amount (or `-` for cash sales).
7. **الإجمالي** (`total_amount`): Grand total invoice value.

#### Subfilters
- **النوع**: Select (`الكل`, `كاش فقط`, `قسط فقط`, `بمقدم فقط`).
- **المندوب**: Autocomplete dropdown.
- **من فاتورة**: Starting receipt number.
- **إلى**: Ending receipt number.
- **الموبايل**: Customer phone search.
- **العميل**: Customer name search.
- **المنطقة**: Area `ReportAutocomplete` (`/customer-suggestions/?field=area`).

#### Summary KPIs (5 Cards)
1. **التاريخ**: Active month/year in `YYYY/MM` format.
2. **عدد الفواتير**: Total invoice count matching filters.
3. **إجمالي الكاش**: Total revenue from cash sales.
4. **إجمالي المقدمات**: Total cash collected from installment down payments.
5. **إجمالي المبيعات**: Grand total sales revenue.

---

### 5.9 كارت الصنف وسجل حياة المنتج (`ProductLedger.jsx`)

Features complete chronological lifecycle tracking from product creation (`INITIAL`) to its last operation, with top KPI cards, integrated commission management, and monthly movement summaries.

#### Top KPI Cards (6 Cards)
1. **رصيد البداية**: Initial quantity and opening date (`YYYY/MM`).
2. **الرصيد الحالي بالمخزن**: Real-time computed physical stock $\ge 0$.
3. **سعر الشراء الحالي**: Active buying price based on date ranges (`item.get_price_at_date`).
4. **المندبة الحالية**: Active sales commission rate (`item.get_commission_at_date`).
5. **إجمالي خسائر العجز (-)**: Cumulative financial deficit losses (`sum(deficit_qty * unit_cost)`).
6. **صافي المكسب بعد العجز**: Net gross profit from all cash and installment sales minus total deficit losses.

#### Exclusive Management Panels in Product Ledger (Removed from InventoryTab)
1. **Commission Management (`تعديل المندبة`)**:
   - Lives exclusively inside `ProductLedger.jsx` via a collapsible accordion / action panel. Removed completely from `InventoryTab.jsx`.
   - Inputs: `commission_amount` (numeric, Western digits `0-9`) + dual numeric inputs `activation_month` (1-12) and `activation_year`.
   - Backend Flow: Upserts `CommissionHistory` without UniqueConstraint conflicts, immediately refreshing the ledger timeline.
2. **Deficit Registration (`تسجيل عجز في البضاعة`)**:
   - Lives exclusively inside `ProductLedger.jsx` via a collapsible accordion / action panel alongside commission management. Removed completely from `InventoryTab.jsx`.
   - Inputs: `quantity` (integer > 0) + dual numeric inputs `month` (1-12) and `year` (pre-filled with current business date via `useDefaultDate`) + `reason` (text).
   - Backend Flow: Submits `POST /api/v1/inventory-adjustments/` with `adjustment_type: "DEFICIT"`, immediately refreshing running stock and deficit losses.

#### Lifecycle Timeline Columns (8 Columns)
1. **التاريخ**: Event date in `YYYY/MM`.
2. **العملية / الحركة**: Badge (`رصيد افتتاحي`, `فاتورة شراء`, `مرتجع مشتريات للمورد`, `فاتورة بيع`, `مرتجع مبيعات من عميل`, `تسوية عجز مخزن`, `تعديل المندبة`).
3. **التفاصيل / البيان**: Supplier, customer, salesperson, or deficit reason.
4. **الوارد (+)**: Inbound units.
5. **المنصرف (-)**: Outbound units.
6. **الرصيد بعد العملية**: Running stock badge after the event.
7. **سعر الوحدة / التكلفة / المندبة**: Unit price, COGS unit cost, or commission rate with purchase price change indicators.
8. **الأثر المالي**: Net profit or deficit loss value.

---

### 5.10 تقرير المشتريات والموردين (`PurchasesReport.jsx`, `/reports/purchases`)

> [!NOTE]
> **Reconciliation Flag**: Earlier spec versions documented a 7-column invoice-level layout. The live implementation in `PurchasesReport.jsx` renders an **11-column `(Product, Supplier)` aggregated matrix** from `res.data.items` (`GET /api/v1/reports/purchases/`).

#### Columns (11 Columns — `(Product, Supplier)` Matrix)
1. **#** (`index`): Sequential row index.
2. **اسم الصنف** (`item_name`): Product trade name.
3. **اسم المورد** (`supplier_name`): Supplier name (`مورد عام` fallback).
4. **الفواتير** (`invoices_count`): Distinct purchase/return invoice count for the `(Product, Supplier)` pair.
5. **كمية الشراء** (`purchased_qty`): Purchased units (`PURCHASE`).
6. **كمية المرتجع** (`returned_qty`): Returned units (`RETURN`).
7. **صافي الكمية** (`net_qty`): Net purchased units (`purchased_qty - returned_qty`).
8. **متوسط السعر (ج.م)** (`avg_unit_cost`): Weighted average unit purchase cost.
9. **إجمالي الشراء (ج.م)** (`gross_purchases`): Gross purchase monetary amount.
10. **إجمالي المرتجع (ج.م)** (`returns_amount`): Gross purchase return monetary amount.
11. **صافي المشتريات (ج.م)** (`net_purchases`): Net purchase monetary amount (`gross_purchases - returns_amount`).

#### Subfilters
- **Row 1**: **المورد** (`ReportAutocomplete`), **الصنف** (`ReportAutocomplete`), **النوع** (`Select`: `الكل`, `شراء فقط`, `مرتجع فقط`).
- **Row 2**: Quick client-side search (`بحث سريع باسم الصنف أو المورد...` via `DebouncedInput`), **تحديث** button, **إعادة ضبط** button.

#### Summary KPIs (6 Cards)
1. **صافي المشتريات**: Net purchases (`summary.total_purchases_amount`, `PURCHASE - RETURN`).
2. **إجمالي الشراء**: Gross purchase amount (`summary.gross_purchases_amount`).
3. **إجمالي المرتجع**: Total purchase return amount (`summary.total_returns_amount`).
4. **صافي القطع المشتراة**: Total net purchased units (`summary.total_items_quantity`).
5. **عدد الأصناف**: Distinct purchased products count (`summary.distinct_products_count`).
6. **عدد الموردين**: Distinct suppliers count (`summary.suppliers_count`).

#### Printing
- Top-bar `"طباعة التقرير"` button invokes `registerPrintHandler` $\rightarrow$ `POST /api/v1/reports/desktop_print/` directly with `action: 'view'` (instant PDF preview); `ReportTable` toolbar `"طباعة"` button opens `PrintModal.jsx`.

---

### 5.11 تقرير المناطق والتحصيل الجغرافي (`AreasReport.jsx`, `/reports/areas`)

#### Columns (11 Columns)
1. **#** (`index`): Sequential row index.
2. **المنطقة** (`area`): Customer geographic zone (`غير محدد` fallback).
3. **الفواتير** (`invoices_count`): Total sales invoice count.
4. **مبيعات نقدي (ج.م)** (`cash_sales`): Cash sales volume.
5. **مبيعات تقسيط (ج.م)** (`installment_sales`): Installment sales volume.
6. **إجمالي المبيعات (ج.م)** (`gross_sales`): Gross sales volume.
7. **المقدمات (ج.م)** (`down_payments`): Total down payments collected.
8. **الأقساط المستحقة (ج.م)** (`due_installments_month`): Monthly installment dues in the active period.
9. **المرتجعات (ج.م)** (`returns_amount`): Total sales returns amount.
10. **صافي المبيعات (ج.م)** (`net_sales`): Net sales (`gross_sales - returns_amount`).
11. **المناديب النشطين** (`salespersons_display`): Active salespersons operating in the area.

#### Subfilters
- **Row 1**: **المندوب** (`ReportAutocomplete`), **المنطقة** (`ReportAutocomplete` backed by `/customer-suggestions/?field=area`).
- **Row 2**: Quick client-side search (`بحث سريع باسم المنطقة أو المندوب...` via `DebouncedInput`), **تحديث** button, **إعادة ضبط** button.

#### Summary KPIs (6 Cards)
1. **إجمالي المبيعات** (`summary.total_sales`)
2. **صافي المبيعات** (`summary.net_sales`)
3. **إجمالي المقدمات** (`summary.total_down_payments`)
4. **الأقساط المستحقة بالشهر** (`summary.total_due_installments`)
5. **إجمالي المرتجعات** (`summary.total_returns_amount`)
6. **عدد المناطق النشطة** (`summary.areas_count`)

#### Printing
- Top-bar `"طباعة التقرير"` button invokes `registerPrintHandler` $\rightarrow$ `POST /api/v1/reports/desktop_print/` directly with `action: 'view'` (instant PDF preview); `ReportTable` toolbar `"طباعة"` button opens `PrintModal.jsx`.
