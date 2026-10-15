# Original User Request

## Initial Request — 2026-06-20T14:29:51Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Upgrade the Central Server's Django Admin interface with `django-jazzmin`, create explicit `.bat` scripts for manual console execution, and conduct a final suite of E2E Ngrok tests for Viewer PC authentication and syncing.

Working directory: `D:\Projects\VentaPOS\Server`
Integrity mode: development

## Requirements

### R1. Organize Admin Interface (Jazzmin)
Install `django-jazzmin` via pip. Update `settings.py` to include it in `INSTALLED_APPS` and configure `JAZZMIN_SETTINGS`. The admin panel should have a cohesive side navigation menu grouping models like Licenses, Receipts, and Branches. Use the default VentaPOS branding (no custom logo file needed).

### R2. Manual Execution Scripts
Create two explicit batch scripts in the Server root directory:
- `start_server.bat`: Launches the Django server (`manage.py runserver 0.0.0.0:8000`) in a visible CMD window.
- `stop_server.bat`: Gracefully terminates the Python server process running on port 8000.

### R3. QA E2E Testing (Ngrok)
Run the remote API tests via Ngrok to validate:
- `POST /api/v1/auth/viewer/`
- `GET /api/v1/sync/viewer/download/`
- `POST /api/v1/sync/mobile-push/`

## Acceptance Criteria

### Verification
- [ ] `django-jazzmin` is successfully installed and `runserver` starts without any syntax or configuration errors.
- [ ] `start_server.bat` and `stop_server.bat` are created and correctly start/stop the server.
- [ ] A test script (e.g., `qa_e2e_test.py`) or manual curl commands can successfully hit the endpoints over Ngrok and receive expected responses (e.g., 200 OK for valid push, 403/404 for invalid credentials).

## Follow-up — 2026-06-20T19:06:16Z

## RESUME — Pick up where the previous team stopped

Working directory: d:/Projects/VentaPOS
Integrity mode: benchmark

## CRITICAL CONTEXT — What was already completed

A previous agent team already completed TWO phases:

### Phase 1: Full Codebase Analysis (COMPLETED — DO NOT REDO)
Detailed analysis reports saved at:
1. `d:/Projects/VentaPOS/.agents/explorer_server/analysis_server.md` (15KB) — Full Server analysis
2. `d:/Projects/VentaPOS/.agents/explorer_mobile/analysis_mobile.md` (16KB) — Full Mobile analysis
3. `d:/Projects/VentaPOS/.agents/explorer_desktop/analysis_desktop.md` (22KB) — Full Desktop analysis
4. `d:/Projects/VentaPOS/.agents/explorer_license/analysis_license.md` (11KB) — Full License analysis

### Phase 2: Initial SKILL.md Documentation (PARTIALLY COMPLETED)
The following documentation files were already written to `.agents/skills/`:

**Global files** (in `.agents/skills/`):
- `global_architecture.md` (2.4KB)
- `api_contract.md` (3.2KB)
- `audit_code.md` (1KB)
- `deploy_app.md` (1.2KB)
- `global_roadmap.md` (1.6KB)

**Server** (in `.agents/skills/Server/`):
- `database_schema.md` (6.4KB), `business_logic.md` (4KB), `api_and_security.md` (2.7KB), `configuration.md` (2.3KB), `routing_and_templates.md` (2.5KB)

**Mobile** (in `.agents/skills/Mobile/`):
- `database_schema.md` (2.7KB), `business_logic.md` (3.8KB), `api_and_security.md` (3KB), `configuration.md` (2.6KB), `routing_and_templates.md` (3.5KB)

**Desktop** (in `.agents/skills/Desktop/`):
- `database_schema.md` (21KB), `business_logic.md` (4.5KB), `api_and_security.md` (4KB), `configuration.md` (5.4KB), `routing_and_templates.md` (10.9KB)

**LicenseManager** (in `.agents/skills/LicenseManager/`):
- `database_schema.md` (5.1KB), `business_logic.md` (5.6KB), `api_and_security.md` (4.9KB), `configuration.md` (3.3KB), `routing_and_templates.md` (4.7KB)

## YOUR MISSION — Phase 3: Quality Audit & SKILL.md Conversion

The raw documentation exists. Your job is:

1. **AUDIT**: Read each existing `.md` file in `.agents/skills/` and cross-verify claims against the ACTUAL source code. Fix any inaccuracies. Ensure every claim has file path + line number citations.

2. **CONVERT TO SKILL FORMAT**: Each subsystem directory needs a proper `SKILL.md` file with YAML frontmatter:
```yaml
---
name: ventapos-server
description: Complete technical documentation of the VentaPOS Server subsystem...
---
```
The SKILL.md should either contain or reference all the documentation for that subsystem.

3. **GRILL-ME PROTOCOL**: If you find ambiguous business logic that cannot be understood from the code alone, STOP and ask the user. Do NOT guess.

4. **CHECKPOINT-SAFE**: Save each file fully before starting the next. Update progress.md after each completed file.

### Existing architecture docs to cross-reference:
- `d:/Projects/VentaPOS/database_schema.md`
- `d:/Projects/VentaPOS/requirements.md`

## Acceptance Criteria
- [ ] Each subsystem (Server, Mobile, Desktop, LicenseManager) has a proper `SKILL.md` with YAML frontmatter
- [ ] Every technical claim verified against actual source code with file:line citations
- [ ] QA audit completed independently
- [ ] Grill-Me protocol invoked for any ambiguous business logic
- [ ] All files checkpoint-saved incrementally

## 2026-06-24T19:31:33Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Execute the multi-agent teamwork project

Complete the VentaPOS Mobile App overhaul (Flutter/SQLite) to match the Django Desktop application 100% in logic, UI (FlareLine), and features, excluding the local license invoice deduction.

Working directory: D:\Projects\VentaPOS\Mobile\sales_app_offline
Integrity mode: development

## Requirements

### R1. Complete All Remaining Screens
Migrate all remaining mobile screens (`manage_products_screen.dart`, `expenses_screen.dart`, `manage_branches_screen.dart`, `manage_users_screen.dart`, `manage_suppliers_screen.dart`, `manage_purchase_invoices_screen.dart`, `sync_hub_screen.dart`, `product_ledger_screen.dart`, `sales_reports_screen.dart`) to use the FlareLine UIKit components (`CommonCard`, `OutBorderTextFormField`, etc.).

### R2. Replicate Desktop Business Logic (All Screens)
Implement exact Desktop logic for EVERY screen (not just Receipts). This includes inventory constraints, cryptographic hashing, parsing, and advanced filtering across the entire app, excluding only the `invoices_balance` deduction. You must read the corresponding Django views in `D:\Projects\VentaPOS\Desktop\sales\salesapp\views\` to understand the exact logic for each screen.

### R3. Dedicated Agent Per Screen
The teamwork orchestrator must spawn a dedicated subagent for each individual screen. Each agent is responsible for perfectly translating both the FlareLine UI and the underlying Django business logic for their assigned screen.

### R4. Offline Sync Architecture
Ensure the SQLite `database_helper.dart` handles the `receipt_hash` correctly and stages data for the `SyncHub` to push to the Cloud/Desktop.

## Acceptance Criteria

### Automated Verification
- [ ] A Python script (`test_mobile_logic.py`) is written to query the local SQLite DB and verify that `receipt_hash` is generated identically to the Django logic.
- [ ] A Python script verifies that adding a receipt in the mobile app correctly updates stock and respects the `get_safe_available_qty` algorithm.

### Agent-as-Judge Verification
- [ ] All specified screens are fully translated to Flareline UIKit components.
- [ ] No screen uses plain Flutter TextFields or Cards where Flareline components exist.

## Follow-up — 2026-06-28T13:02:13Z

Rebuild the VentaPOS desktop application as a modern web app (React/Django) achieving 100% feature parity with the original system, including exact business logic, UI flows, and comprehensive technical documentation. Includes a safe data migration path for old clients.

Working directory: d:/Projects/VentaPOS/VentaPOS_NextGen
Integrity mode: demo

## Requirements

### R1. 100% Parity Reconstruction
Reconstruct the legacy desktop application's complete logic into the new React/Django stack. You MUST read the old code to understand expected behaviors (like the time-machine inventory logic, invoice hashing, and strict Company Setup Wizard) and replicate them exactly without inventing new constraints or dropping existing ones.

### R2. Data Migration Script
Write a robust Python script that cleanly migrates client data from the old `.sqlite3` database schema to the new Django ORM schema without data loss.

### R3. Continuous Documentation
Generate comprehensive technical documentation (Markdown/OpenAPI) for the system architecture immediately after completing each subsystem.

### R4. Zero Hallucination Policy
If you encounter any ambiguity, missing information in the old codebase, or are unsure about how a specific business rule was implemented, you MUST stop and ask the user for clarification. Do not invent, guess, or assume any logic.

## Acceptance Criteria

### Migration Integrity
- [ ] A test run of the migration script on the user-provided legacy `.sqlite3` database completes without errors.
- [ ] Record counts for core entities (Invoices, Customers, Items, Salespersons) match exactly between the old and new databases.

### Feature Parity
- [ ] A programmatic test script validates that generating an invoice in the new system with identical inputs to the old system produces the exact same cryptographic hash and stock deductions.

### Documentation completeness
- [ ] A verified OpenAPI 3.1 contract exists for all endpoints.
- [ ] Markdown architecture files exist documenting the UI flow mappings from the old desktop views.

## Follow-up — 2026-07-01T02:14:10Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

An automated team of AI agents will analyze the legacy VentaPOS desktop codebase and the new VentaPOS_NextGen codebase to produce a comprehensive feature parity report. The report will identify missing pages, missing features, unhandled edge cases, and actionable steps to implement them in the new architecture.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen

## Requirements

### R1. Deep Codebase Comparison
Use Static Code Analysis to thoroughly compare the old desktop system (`D:\Projects\VentaPOS\Desktop\sales`) against the new React/Django system (`D:\Projects\VentaPOS\VentaPOS_NextGen`).

### R2. Exhaustive Gap Analysis Report
Generate a highly detailed, exhaustive Markdown report documenting *every single missing page, feature, logic discrepancy, or UI difference*. **DO NOT Summarize.** You must list the full details about every single page and component that is missing from the new system. 

### R3. Actionable AI Tasks and Prompts
Provide a Master Markdown Checklist artifact containing copy-pasteable AI prompts for each missing page/feature so they can be assigned to other AI agents seamlessly.

## Acceptance Criteria

### Verification
- [ ] The report accurately identifies missing features by statically analyzing and referencing specific files in both codebases.
- [ ] The report does not skip or summarize details—it must be extensive and granular.
- [ ] The report provides actionable, copy-pasteable implementation prompts mapped to the new Django/React architecture.

## Follow-up — 2026-07-01T16:26:58+03:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Rebuild the VentaPOS NextGen POS Entry (Add Receipt) screen and its supporting backend APIs to achieve 100% feature parity with the legacy Django Desktop version, specifically restoring the dynamic Smart Autocomplete engine, Installment schedule shifting, and payload integrity.

Working directory: `D:\Projects\VentaPOS\VentaPOS_NextGen`
Integrity mode: development

## Requirements

### R1. Backend Autocomplete APIs
Implement two endpoints in the Django backend (`api/views.py`):
1. `GET /api/v1/product-suggestions/`: Accepts `term`, `month`, and `year`. Must return `{id, value, max}` where `max` is the safe available quantity calculated for that future date.
2. `GET /api/v1/customer-suggestions/`: Accepts `term`, `field` (name/phone/address/area), `salesperson_id`, `current_area`, and `current_name`. Must return relevance-sorted suggestions matching the legacy logic.

### R2. Frontend Smart Autocomplete
Modify `PosEntry.jsx` to remove the upfront fetching of all inventory items. Replace the standard inputs for Product Search, Customer Name, Phone, Address, and Area with debounced Async Autocomplete dropdowns that query the new APIs from R1. The Customer autocomplete must pass context (e.g., passing `salesperson_id` when searching for a name).

### R3. POS Business Logic Parity
1. **Cash Sale Toggle**: Replicate the "Cash Sale?" checkbox logic. When checked, the UI must hide the Customer and Installment sections, remove their validation requirements, and set `is_cash_sale=true` in the payload.
2. **Installment Shift**: The generated installment schedule must start on `sale_month + 1` (handling year rollover).
3. **Stock Validation**: The product autocomplete must cache the returned `max` value. When clicking "Add to Cart", the UI must strictly block the addition if `requested_qty + cart_qty > max`.
4. **Payload Mapping**: The final POST payload to `/api/v1/receipts/` must use the keys `phone_number`, `address`, and `area` instead of `customer_phone`, etc., to prevent data loss. The Address field must remain a standard `<input type="text">`, not a textarea.

## Acceptance Criteria

### API Integrity
- [ ] `GET /api/v1/product-suggestions/?term=X&month=7&year=2026` returns a valid JSON array of objects with `id`, `value`, and `max`.
- [ ] `GET /api/v1/customer-suggestions/?field=phone&term=010` returns a valid JSON array of `value` strings.

### Frontend Logic
- [ ] Typing in the product search box triggers a network request rather than filtering a static array.
- [ ] Selecting a sale month of "12" and adding a 1-month installment generates a schedule for month "1" of the next year.
- [ ] The submitted POST payload contains `phone_number` and `address` fields, and the backend successfully saves them to the database.

## Follow-up — 2026-07-04T05:06:09+03:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Implement the "Search Receipts" (دفتر المبيعات) as the primary hub for the Sales department, replacing the sales dropdown in the sidebar and setting it as the main landing page of the app.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen
Integrity mode: development

## Requirements

### R1. Frontend Restructuring & Routing
- Modify `App.jsx` to make the new `/receipts` page the default landing page (main page) when the application is opened/authenticated, bypassing or replacing the old dashboard.
- Modify `Navbar.jsx` to remove the "Sales" dropdown and instead provide a direct link to `/receipts`.

### R2. Search Receipts Page UI
- Create `SearchReceipts.jsx` using Tabler UI components and Arabic RTL styling.
- Include a prominent "➕ إضافة فاتورة جديدة" button that links to the existing `/pos` page.
- Implement a comprehensive search filter section matching the legacy desktop app:
  - Dropdowns: Salesperson, Year, Month.
  - Number Inputs: Receipt From, Receipt To.
  - Text Inputs: Customer Name, Phone, Address, Area.
- Display a data table for results showing: Receipt ID, Date, Customer Name, Total Amount, Sale Type (Cash/Installment), and an Actions column.

### R3. Backend Filtering & API
- Modify `ReceiptViewSet` in `api/views.py` (and serializers if needed) to accept and process all the aforementioned search filters via query parameters.
- Ensure the filtering logic correctly applies `icontains` for text fields and exact/range matches for numbers and dates.

## Acceptance Criteria

### Testing & Verification
- [ ] Programmatic: A GET request to `/api/v1/receipts/?customer_name=X&year=2026` returns a 200 OK and only returns receipts matching those exact filters.
- [ ] UI Verification: Navigating to the root `/` URL correctly redirects or renders the Search Receipts page.
- [ ] UI Verification: The Sales nav link is a direct clickable link, not a dropdown.
- [ ] UI Verification: Clicking "إضافة فاتورة جديدة" successfully navigates to `/pos`.

## Follow-up — 2026-07-07T04:42:55Z

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Implement the Reporting and Dashboard subsystem for VentaPOS_NextGen using a "Drill-down" architecture. The UI must follow a new functional division (Dashboard, Salesperson Performance, Inventory Movement, P&L, and Cash Drawer) while **strictly reusing the exact mathematical and accounting logic** from the legacy VentaPOS Desktop application without any deviation or "creative" additions.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen
Integrity mode: development

## Reference Material

The legacy application source code is at `D:\Projects\VentaPOS\Desktop\sales\salesapp\`. Key files the research agent MUST read before any implementation begins:

**Backend (Logic & Calculations):**
- **`views/report_views.py`** — Contains `sales_reports()` and `invoices_report()` with ALL calculation formulas (COGS, commissions, P&L, inventory movement, time-machine pricing).
- **`views/branch_views.py`** — Contains `dashboard()` with cash flow, salesperson stats, KPI calculations.
- **`views/collections_views.py`** — Contains collections/installment filtering, grouping by salesperson, and A4 report generation.
- **`views/expense_views.py`** — Contains expense management and aggregation logic.
- **`models.py`** — Contains `InventoryItem.get_price_at_date()`, `get_commission_at_date()`, `get_stock_at_date()` — the "time-machine" methods.

**Frontend (Table Shapes & UI Structure):**
- **`templates/salesapp/dashboard.html`** — Dashboard layout, KPI cards, salesperson stats table, top products/areas.
- **`templates/salesapp/sales_reports.html`** — Tabbed report (Inventory tab, P&L tab, Detailed Ledger tab) with table column definitions.
- **`templates/salesapp/invoices_report.html`** — Invoice listing table with summary cards.
- **`templates/salesapp/manage_collections.html`** — Collections table grouped by salesperson, with filtering UI.
- **`templates/salesapp/salaries_report.html`** — Salesperson salary/commission breakdown table.

> **⚠️ General Rule:** When anything is unclear or ambiguous during implementation, the legacy application at `D:\Projects\VentaPOS\Desktop\sales\salesapp\` is the single source of truth. Always consult it — read the relevant view, template, or model — before making assumptions.

## Requirements

### R1. Add Missing `get_price_at_date()` Method to NextGen Models
The NextGen `InventoryItem` model (in `backend/api/models.py`) already has `get_stock_at_date()` and `get_commission_at_date()`, but is **missing** the critical `get_price_at_date()` method. This method MUST be added with the exact same logic as the legacy app: it queries `PurchaseInvoiceItem` records to find the most recent purchase price at or before the given month/year, falling back to `initial_purchase_price`.

### R2. Backend Report API Endpoints
Create new Django REST Framework API views that expose reporting data as JSON. All calculation logic must strictly mirror the legacy Python code — specifically the "time-machine" pricing (`get_price_at_date`), the fixed 10% collection commission rule (applied to `total_amount - down_payment` for installment sales only), and the proportional per-item collection commission distribution formula from `report_views.py`.

Required endpoints:
- `GET /api/v1/reports/dashboard/` — High-level financial KPIs (cash inflow, revenue, COGS, profit, inventory value, low stock count, avg basket, top products, top areas).
- `GET /api/v1/reports/salesperson-performance/` — Per-salesperson breakdown (cash sales, credit sales, collections, sales commission, collection commission, total due).
- `GET /api/v1/reports/inventory-movement/` — Per-item movement (opening stock, purchases, returns, sales, surplus, deficit, final stock, price, total value).
- `GET /api/v1/reports/profit-and-loss/` — Per-item profitability split by cash vs. installment (unit cost, sell price, sales commission, collection commission, net profit).
- `GET /api/v1/reports/cash-drawer/` — Detailed breakdown of all cash inflows (cash sale receipts, installment down-payments, collected installment payments).

All endpoints must accept `year` and `month` query parameters for filtering.

### R3. Frontend Reporting UI (5 New Pages)
Create 5 new React pages under `frontend/src/pages/reports/`. Each page must use the existing RTL + Tabler + Bootstrap design system already in use in the application. No new CSS frameworks or chart libraries unless absolutely necessary.

- **Dashboard** (`/reports/dashboard`): Summary cards showing key financial numbers. Each card's number is a clickable link that navigates to the relevant detail page (e.g., clicking "السيولة" goes to Cash Drawer, clicking "الأرباح" goes to P&L).
- **Salesperson Performance** (`/reports/salesperson`): Full table with all reps — cash sales, credit sales, collections, commissions, total due. Clicking any number navigates to the relevant detail page with filters applied.
- **Inventory Movement** (`/reports/inventory`): Per-item stock tracking table (opening, purchases, returns, sales, adjustments, final, price, total value).
- **Profit & Loss** (`/reports/profit-and-loss`): Per-item profitability table separated into Cash Sales and Installment Sales sections.
- **Cash Drawer** (`/reports/cash-drawer`): Detailed table listing individual cash-sale receipts, down-payments from installment sales, and collection payments — the atomic transactions behind the "السيولة" number.

### R4. Drill-down Navigation Between Report Pages Only
All aggregated numbers in the report UI must be clickable. Clicking navigates to another report page with appropriate filters pre-applied via URL query parameters (e.g., `?year=2026&month=7&salesperson=X`). The drill-down operates ONLY between the 5 new report pages. Existing pages (like SearchReceipts, POS, Expenses) must NOT be modified.

### R5. Navigation Menu Integration
Add a "التقارير" (Reports) section to the existing sidebar/navbar with links to the 5 new report pages. Add the corresponding React Router routes in `App.jsx`.

## Acceptance Criteria

### Backend Verification
- [ ] Programmatic: A `get_price_at_date(month, year)` method exists on `InventoryItem` and returns the correct historical purchase price matching the legacy logic.
- [ ] Programmatic: `GET /api/v1/reports/dashboard/?year=YYYY&month=MM` returns a 200 OK with JSON containing at minimum: `cash_inflow`, `revenue`, `cogs`, `net_profit`, `inventory_value`.
- [ ] Programmatic: `GET /api/v1/reports/salesperson-performance/?year=YYYY&month=MM` returns a 200 OK with a list of salesperson stats matching the legacy dashboard's `salespersons_stats` structure.
- [ ] Programmatic: `GET /api/v1/reports/profit-and-loss/?year=YYYY&month=MM` returns 200 OK with items split into `cash_sales_list` and `installment_sales_list`, each item having `total_cost`, `total_sales_comm`, `total_coll_comm`, and `total_profit`.

### Frontend Verification
- [ ] UI: All 5 report pages render without JavaScript errors and display data from the API.
- [ ] UI: The navigation sidebar contains a "التقارير" section with links to all 5 pages.
- [ ] UI: Clicking an aggregated number on the Dashboard (e.g., السيولة) successfully navigates to the Cash Drawer page with the correct year/month in the URL.
- [ ] UI: All pages use RTL layout and Arabic labels consistent with the existing application design.


## 2026-07-17T18:13:57Z

# Teamwork Project Prompt — Draft

Organize and restructure the VentaPOS NextGen master documentation hub to make development easy. Update `index.md` with links and descriptive summaries, and discover undocumented features by deeply comparing the docs against the codebase.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen
Integrity mode: development

## Requirements

### R1. Analyze & Restructure Existing Documentation
Scan `docs/` and its subdirectories (`/business`, `/architecture`, `/technical`, `/features`). Read the actual contents and headers of ALL markdown files. Restructure and organize these files if necessary to make development easier and more intuitive.

### R2. Comprehensive Codebase Scan
Perform a deep, comprehensive scan of the application's actual codebase. Go beyond just `frontend/src/pages/` and `backend/api/urls.py`—trace into components, views, and logic to ensure absolutely no hidden features are missed.

### R3. Identify Undocumented Features
Compare the comprehensive codebase scan against the existing documentation to identify any pages, components, or API endpoints that are truly NOT yet documented anywhere. 
**Note:** The user has already documented the items currently listed in the "Missing Documentation (TODO)" section of `index.md`. You must find *new* undocumented features.

### R4. Update Master Index
Update the `docs/index.md` file to include relative links to all existing documentation files, grouped cleanly under their respective (and potentially restructured) directory headings. Add a brief, one-line descriptive summary next to each link based on the file contents.

### R5. Update Missing Documentation List
Clear the outdated items from the 'Missing Documentation (TODO)' section at the bottom of `index.md` and populate it with the *newly* discovered undocumented features identified in step R3.

## Acceptance Criteria

### Scripted Verification
- [ ] A verification script (e.g. Python) is created to programmatically check that every backend endpoint and frontend route discovered in the codebase is mentioned in either the markdown documentation or the newly updated Missing Documentation TODO list.

### Structural Organization
- [ ] The `index.md` provides a seamless navigation experience, where every documentation link is accompanied by a clear, one-line summary.
- [ ] The documentation folder hierarchy logically groups related documents without clutter.

### Completeness
- [ ] The 'Missing Documentation (TODO)' section at the bottom of `index.md` has been cleared of the previously completed items.
- [ ] The TODO section accurately covers the new gap between the codebase and the existing documentation without hallucinations.

## 2026-09-01T02:37:31Z

# Teamwork Project Prompt — Draft

> Status: Launched.
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full Team

Implement the unified reporting UI and backend fixes for VentaPOS NextGen based strictly on the `REPORTS_AGREEMENT.md` and `implementation_plan.md` artifacts.

Working directory: D:\Projects\VentaPOS\VentaPOS_NextGen
Integrity mode: demo

## Requirements

### R1. Shared Utilities & Autocomplete
Implement the `ReportAutocomplete` component and ensure `fmtNum` and `toArabic` strictly format integers with thousand separators and dates as MM/YYYY.

### R2. Backend Fixes
Fix the `receipt_from`/`receipt_to` filter bug, the `إجمالي المقدمات` KPI logic in `api/views.py`, and the array extraction bugs for Inventory and Salesperson reports.

### R3. Refactor 7 Report Pages
Refactor all 7 `.jsx` report files to match the exact Columns, Subfilters, and KPIs specified in `REPORTS_AGREEMENT.md`.

## Acceptance Criteria

### Automated Verification
- [ ] Backend tests pass (`python manage.py test api.tests`)
- [ ] Frontend builds successfully (`npm run build`)

### Functional Verification
- [ ] Navigating to each report renders the correct columns and KPIs without crashing.
- [ ] Inventory and Salesperson reports successfully display data (array extraction bug fixed).

