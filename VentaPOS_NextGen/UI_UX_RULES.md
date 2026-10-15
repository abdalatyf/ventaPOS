# VentaPOS NextGen — Frontend & UI/UX Architecture Bible

> **Scope**: Complete Frontend Visual Identity, Interaction Rules, Table Scroll Architecture, and Audited Report Specifications  
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
7. **Universal Western Digits (`0-9`)**:
   - Western ASCII digits (`0-9`) are required universally across all labels, table cells, summary cards, and API payloads. Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) are banned.
8. **Thousands-Comma Sanitization**:
   - Before dispatching numeric inputs to the API, the frontend must strip thousands-separators (`.replace(/,/g, '')`) to prevent DRF DecimalField parsing errors.

---

## 4. Unified Table Scroll Architecture (Native Window Scroll)

Data tables must utilize a single native window scrollbar with hierarchical sticky positioning. Internal scroll divs (`overflow-auto`, `overflow-y: scroll`) inside tables are banned.

```
┌────────────────────────────────────────────────────────┐
│ 1. Fixed Navbar (top: 0, z-index: 1030)                │
├────────────────────────────────────────────────────────┤
│ 2. Sticky Toolbar (top: --navbar-height, z-index: 1020)│
├────────────────────────────────────────────────────────┤
│ 3. Sticky Table Headers (top: offset, z-index: 1010)   │
├────────────────────────────────────────────────────────┤
│ 4. Table Body Rows (Normal Window Document Flow)       │
└────────────────────────────────────────────────────────┘
```

### 4.1 CSS Rules (`src/index.css`)
```css
:root {
  --navbar-height: 64px;
  --toolbar-height: 46px;
}

/* Page wrapper must allow document-level scrolling */
.native-page-scroll {
  height: auto !important;
  min-height: 100vh;
  overflow: visible !important;
}

/* Sticky Toolbar */
.sticky-toolbar {
  position: sticky;
  top: var(--navbar-height);
  z-index: 1020;
  background-color: #f8f9fa;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Sticky Table Header */
.table-sticky-header th {
  position: sticky !important;
  top: calc(var(--navbar-height) + var(--toolbar-height)) !important;
  z-index: 1010;
  background-color: #f8f9fa !important;
  box-shadow: inset 0 -1px 0 var(--tblr-border-color);
}
```

### 4.2 Infinite Scrolling Protocol
Because tables expand naturally into the document, use `IntersectionObserver` attached to the final row of the dataset to trigger pagination, rather than element scroll listeners.

---

## 5. Audited Report Specifications (8 Reports)

The following specifications are verified against the active source implementations in `VentaPOS_NextGen/frontend/src/pages/reports/*.jsx`. All Arabic headers, keys, subfilters, and KPIs are exact.

---

### 5.1 لوحة التحكم / الملخص (`DashboardReport.jsx`)
Features a 2-card financial breakdown with drill-down links to detailed reports.

#### Card 1: تفاصيل المكسب (P&L Breakdown)
- **إجمالي المبيعات** (`kpis.total_revenue`) $\rightarrow$ Click navigates to `/reports/receipts`
- **تكلفة البضاعة (سعر الشراء) (-)** (`kpis.total_cogs`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي المندبة (-)** (`kpis.total_sales_commissions`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي عمولة التحصيل (-)** (`kpis.total_collection_commissions`) $\rightarrow$ Click navigates to `/reports/profit-and-loss`
- **إجمالي المصروفات (-)** (`cashSummary.operating_expenses`) $\rightarrow$ Click navigates to `/reports/expenses`
- **صافي المكسب** (`kpis.estimated_net_profit`)

#### Card 2: تفاصيل السيولة (Cash Drawer Breakdown)
- **(+) مبيعات كاش** (`cashSummary.cash_sales_inflow`)
- **(+) المقدمات** (`cashSummary.down_payment_inflow`)
- **(+) التحصيل** (`cashSummary.collection_inflow`)
- **(=) إجمالي الوارد** (`cashSummary.total_cash_inflow`)
- **(-) إجمالي المشتريات** (`cashSummary.total_purchases`) $\rightarrow$ Click navigates to `/search-purchases`
- **(-) إجمالي المرتبات** (`cashSummary.auto_salaries`) $\rightarrow$ Click navigates to `/reports/salesperson`
- **(-) إجمالي المصروفات** (`cashSummary.operating_expenses`) $\rightarrow$ Click navigates to `/reports/expenses`
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
- **المندوب**: Autocomplete searchable dropdown.
- **من تاريخ بيع**: Dual numeric inputs (`month`, `year`).
- **إلى تاريخ بيع**: Dual numeric inputs (`month`, `year`).
- **اسم العميل**: Text input.
- **رقم الموبايل**: Numeric text input.
- **المنطقة**: Text input.

#### Summary KPIs (3 Cards)
- **تاريخ الدفع**: Active payment month/year.
- **عدد الأقساط**: Total installment count for selected month.
- **إجمالي التحصيل**: Total sum of installment cash due.

---

### 5.3 المصروفات (`ExpensesReport.jsx`)

#### Columns (4 Columns)
1. **رقم المصروف** (`id`): Sequential expense identifier.
2. **البيان** (`description`): Expense descriptive text.
3. **المبلغ** (`amount`): Monetary expenditure value.
4. **التاريخ** (`date`): Business period in `YYYY/MM` format.

#### Subfilters
- **البيان**: Live debounced text search.
- **من مبلغ**: Minimum amount numeric filter.
- **إلى مبلغ**: Maximum amount numeric filter.

#### Summary KPIs (2 Cards)
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

#### Summary KPIs (6 Cards)
- **المبيعات**: Gross revenue sum.
- **التكلفة (-)**: Cumulative COGS.
- **المندبة (-)**: Cumulative sales commissions.
- **عمولة التحصيل (-)**: Cumulative collection commissions.
- **المصروفات (-)**: Operating branch expenses for the month.
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
- **المنطقة**: Area text filter.

#### Summary KPIs (5 Cards)
1. **التاريخ**: Active month/year in `YYYY/MM` format.
2. **عدد الفواتير**: Total invoice count matching filters.
3. **إجمالي الكاش**: Total revenue from cash sales.
4. **إجمالي المقدمات**: Total cash collected from installment down payments.
5. **إجمالي المبيعات**: Grand total sales revenue.
