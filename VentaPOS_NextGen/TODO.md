# VentaPOS NextGen — Master Task & Roadmap Tracker (v1.0.0 Release Track)

> **Anchors**: `GEMINI.md` · `.agents/AGENTS.md` · `requirements.md` · `UI_UX_RULES.md` · `.agents/CODEBASE_MAP.md`  
> **Status Notation**: `[ ]` = Pending · `[/]` = In Progress · `[x]` = Verified & Done

---

## 0. Completed Architecture Foundations (Passes 1 & 2)

- [x] **Pass 1 (`P0`, `P1`, `P2`) & Pass 2 (`Batch P2-1` to `Batch P2-4`)**:
  - Time-Machine stock formula & bulk bottleneck engine (`stock_service.py`), domain services (`financial_service.py`, `compensation_service.py`, `receipt_service.py`), and modular viewsets (`backend/api/views/*`).
  - Hardware 32-character SHA-256 Machine ID binding, 80-bit cryptographic license validator, monotonic clock-rollback guard, production database wipe protection on renewal/demo auth, and WAL-safe hot backups.
  - USB/Sync placed in dormant mode (`P2-4.1`), First Activation $\rightarrow$ Setup Wizard $\rightarrow$ Branch Creation flow (`P2-4.2`), and Read-Only `403`/`402` interceptor + live banner reactivity (`P2-4.3`).
  - **Baseline Verification**: `148 passed, 1 skipped` backend tests (`manage.py test api.tests`), `0` frontend build errors.

---

## 1. Master v1.0.0 Roadmap (18 Items Grouped into 6 Execution Batches)

### Batch V1-1 — Core Backend, Expense Categorization, Purchases Report & Pre-License Data (Items 1, 4, 5, 6, 10, 11)

- [x] **Item 1 — Fix Collection & Sales Sum = 0 Bugs Across Reports & Search**:
  - `frontend/src/pages/SearchReceipts.jsx:110`: Fix `res.data.aggregate?.total_amount` $\rightarrow$ `res.data.aggregate?.total_sales ?? res.data.total_amount_sum ?? 0` so `إجمالي فواتير البيع` never shows `0`.
  - `backend/api/services/compensation_service.py:134-149`: Ensure installment collections on receipts with `salesperson=None` are included in `grand_total_collected` and `InstallmentsReportView` / `DashboardReportView` / `SalespersonPerformanceReportView` always return accurate collection totals.
  - `frontend/src/pages/reports/InstallmentsReport.jsx:98`: Allow fetching installments even when `month` or `year` filter is cleared, and ensure `total_installments_amount` updates reactively.

- [x] **Item 4 — Implement "Print-Only" Basic Plan Mode (`طباعة فقط`, `product_id in (2, 3)`)**:
  - `backend/api/views/license_views.py` (`LicenseStatusView` & `LicenseActivateView`):
    - Expose `product_id` and `is_print_only: latest.product_id in (2, 3)` in `/api/v1/license/status/`.
    - Map `product_id` quotas in `LicenseActivateView`:
      - `1` (Trial 60 Days): 2 months, `800` invoices.
      - `2` (Print-Only 1 Year): 12 months, `4800` invoices.
      - `3` (Print-Only Lifetime): 99 years, `999999` invoices.
      - `4` (Full Management 1 Year): 12 months, `4800` invoices.
      - `5` (Full 3 Years): 36 months, `14400` invoices; `6` (Full 5 Years): 60 months, `24000` invoices; `7` (Full Lifetime): 99 years, `999999` invoices.
      - `10..15` (Top-up codes): Add `100`, `300`, `500`, `1000`, `3000`, `5000` invoices to active balance.
  - `backend/api/middleware.py` (`LicenseEnforcementMiddleware`): When active license has `product_id in (2, 3)`, block API requests to `/api/v1/inventory-items/`, `/api/v1/purchase-invoices/`, `/api/v1/expenses/`, and `/api/v1/reports/` with `403 Forbidden` (`"هذه الميزة غير متاحة في باقة الطباعة فقط"`).
  - `frontend/src/components/Navbar.jsx` & `App.jsx`: When `is_print_only` is `true`, hide Inventory, Purchases, Product Ledger, Expenses, Suppliers, and Reports from navigation; restrict `/dimensions` to Branches and Salespersons only.
  - `frontend/src/pages/POS.jsx` (`POSItemsTable` / `usePOSSave`): When `is_print_only` is `true`, replace the inventory item autocomplete grid with a single free-text **`الأصناف (وصف البضاعة)`** (`products_text`) input and manual **`إجمالي الفاتورة`** (`total_amount`) input (saving `sale_items: []`).

- [x] **Item 5 — Old External Data Support (Pre-License Receipts: `sale_date < lic_start_month`)**:
  - `backend/api/services/receipt_service.py` (`create_receipt`, `update_receipt`) & `ReceiptSerializer`:
    - When `invoice_date < lic_start_month` (or when editing a receipt with `sale_items.count() == 0` and `invoice_date < lic_start_month`):
      - Allow creation and updates **only** when `items_data` is empty (`len(items_data) == 0`) and `products_text` is provided.
      - Do **not** deduct `ClientLicense.invoices_balance` for pre-license receipts (`invoice_date < lic_start_month`).
      - Do **not** deduct inventory stock.
  - **Report Isolation**:
    - Exclude pre-license legacy receipts (receipts where `sale_items` is empty / `sale_date < lic_start_month`) from `DashboardReportView` Card 1 sales revenue, `ProfitAndLossReportView`, `AveragesReportView`, `InventoryMovementReportView`, and Cash Sales inflows.
    - **Include** their scheduled `InstallmentPayment` rows in `InstallmentsReportView`, `SalespersonPerformanceReportView` (`collected` & `comm_coll`), and Cash Drawer `collection_inflow`.
  - `frontend/src/pages/POS.jsx`: When the entered `(sale_month, sale_year)` is earlier than `lic_start_month` (or when editing a legacy receipt with `sale_items.length === 0`), automatically switch the product entry area to the free-text `products_text` + manual `total_amount` mode.

- [x] **Item 6 — Enable Backup Restore from App Start**:
  - `backend/api/tools_views.py` (`BackupUploadView`): Set `permission_classes = [AllowAny]` (safe on local `127.0.0.1` with strict SQLite `PRAGMA integrity_check` + 8-table schema verification + automatic pre-restore snapshot).
  - Add a reusable **"استعادة نسخة احتياطية (.sqlite3)"** button/trigger in:
    1. `frontend/src/components/DemoBanner.jsx`
    2. `frontend/src/pages/Login.jsx`
    3. `frontend/src/pages/ActivationSetup.jsx`
    4. `frontend/src/components/Navbar.jsx`
  - Upon successful restore, clear `localStorage` (`token`, `branchId`, `branchName`) and prompt restart (if `pending_restart`) or redirect to `/login`.

- [x] **Item 10 — Add Dedicated Purchases Report (`تقرير المشتريات`)**:
  - `backend/api/views/report_views.py` & `urls.py`: Create `PurchasesReportView` at `GET /api/v1/reports/purchases/` supporting filters (`branch_id`, `month`, `year`, `supplier_id`, `item_id`, `invoice_type`, `invoice_from`, `invoice_to`) and returning 6 KPI summary metrics + invoice rows.
  - `frontend/src/pages/reports/PurchasesReport.jsx`, `ReportsLayout.jsx`, `DashboardReport.jsx`, `App.jsx`:
    - Create `PurchasesReport.jsx` using `ReportTable` (Mode B sticky table) with 7 columns (`رقم الفاتورة`, `النوع`, `المورد`, `الأصناف`, `إجمالي القطع`, `التاريخ`, `الإجمالي`) and 6 KPI cards.
    - Add `"فواتير المشتريات"` (`purchases`) to the `ReportsLayout.jsx` selector and link `DashboardReport.jsx` Card 2 purchase rows to `/reports/purchases`.

- [x] **Item 11 — Add Expense Categorization (`تصنيف المصاريف`)**:
  - `backend/api/models.py` (`Expense`): Add `category = models.CharField(max_length=100, blank=True, default="مصروفات عامة", db_index=True)` and generate/run migration.
  - `backend/api/serializers.py` (`ExpenseSerializer`) & `backend/api/views/expense_views.py` / `report_views.py` (`ExpensesReportView`): Expose `category` and support filtering by `category`.
  - `frontend/src/pages/Expenses.jsx` & `frontend/src/pages/reports/ExpensesReport.jsx`:
    - Add `التصنيف` autocomplete input in `Expenses.jsx` with presets (`إيجار`, `كهرباء ومياه`, `نقل ومشال`, `صيانة`, `نثريات`, `مصروفات عامة`) + custom text entry.
    - Add `التصنيف` column and filter to `Expenses.jsx` and `ExpensesReport.jsx`.

---

### Batch V1-2 — UI Standardization, Integer Formatting & Navbar Zoom (Items 7, 9, 12)

- [x] **Item 7 — Unify Table Page Layouts via Shared Parent React Template (`StandardTablePageLayout.jsx`)**:
  - Keep the specialized layouts of `POS.jsx`, `PurchaseEntry.jsx`, `ReturnReceipt.jsx`, and `ProductLedger.jsx` (while ensuring their item tables have `.table-sticky-header`).
  - Create a unified parent React template component `frontend/src/components/common/StandardTablePageLayout.jsx` (`title`, `icon`, `headerActions`, `toolbar`, `children`, `modals`) that standardizes the outer container (`container-fluid py-3 d-flex flex-column`), page header banner, sticky top toolbar slot, and bottom sticky table area.
  - Refactor all table/listing pages (`SearchReceipts.jsx`, `SearchPurchases.jsx`, `Expenses.jsx`, `Dimensions.jsx`, and `ReportsLayout.jsx`) to render inside `<StandardTablePageLayout>`.

- [x] **Item 9 — Enforce English Integers (`0-9`, `int` only) in App UI & Arabic Numerals (`٠-٩`, `int` only) in Print**:
  - `frontend/src/utils/formatUtils.js`, `frontend/src/components/pos/posUtils.js`, `ReturnReceipt.jsx`, `SearchReceipts.jsx`, `SearchPurchases.jsx`:
    - Update all number/currency formatters (`fmtNum`, `formatMoney`, `fmt`, `formatCurrency`) to round to whole integers (`Math.round(Number(val)).toLocaleString('en-US')`) with **zero decimal places** (`maximumFractionDigits: 0`).
  - `backend/api/print_utils.py` (`to_arabic_numerals` / `ed2ad`) & `backend/api/views/receipt_views.py` (`_prepare_pdf_context`):
    - Round all numeric/currency amounts (`total_amount`, `down_payment`, `remaining_amount`, `amount_to_pay`, purchase prices, report numbers) to whole integers (`int(round(float(val)))`) before converting digits to Arabic-Indic numerals (`٠١٢٣٤٥٦٧٨٩`) so printed PDFs never show `.٠٠`.

- [x] **Item 12 — Polish Compact Zoom In (`+`) & Zoom Out (`-`) Buttons in `Navbar.jsx`**:
  - `frontend/src/components/Navbar.jsx`:
    - Make the compact `+` and `-` zoom buttons visible across all desktop window widths (remove `d-none d-md-flex`), display the current zoom percentage badge (e.g. `100%`, click to reset), and fix floating-point rounding (`Math.round((currentZoom + 0.1) * 10) / 10`).
    - Dispatch `window.dispatchEvent(new Event('resize'))` inside `applyZoom` and make `useSmartScroll.js` zoom-aware so sticky report tables scroll smoothly at any zoom level (`80%`–`150%`).

---

### Batch V1-3 — General Print Modal & PDF Print Templates (Items 2, 3)

- [x] **Item 2 — Build General Print Pop-up Modal (`PrintModal.jsx`) with Printer Status, Offline Warning & Chunk Pause/Retry/Cancel**:
  - `backend/api/views/receipt_views.py` (`printers` action):
    - Return structured printer objects `[{"name": str, "status": "ready" | "offline", "is_default": bool}]` by inspecting Windows `WorkOffline` and `PrinterStatus` attributes via PowerShell.
  - `frontend/src/components/common/PrintModal.jsx`:
    - Fetches installed Windows printers from `GET /api/v1/receipts/printers/`, remembers the selected printer in `localStorage.getItem('preferred_printer')`, and displays a live status badge next to the selector: 🟢 **جاهز (Ready)** vs 🔴 **غير متصل (Offline)**.
    - **Pre-Print Offline Warning**: When the selected printer is `offline` and the user clicks **"طباعة فورية" (`action: 'print'`)**, display an inline confirmation warning prompt allowing the user to switch to another printer, cancel, or proceed anyway (`"متابعة الطباعة على أي حال"`).
    - **Chunked Printing (`CHUNK_SIZE = 20`) with Failure Pause / Retry / Cancel**: Automatically splits large batch print jobs (`> 20` items) into sequential batches of `20` with a live progress bar; if any batch fails to reach the printer or returns an error, **automatically pause the queue immediately**, show an error alert explaining that the batch did not reach the printer, and provide **"إلغاء باقي الدفعات" (Cancel Remaining Batches)** and **"إعادة محاولة الدفعة" (Retry This Batch)** buttons.
  - Wire `PrintModal.jsx` exclusively into `SearchReceipts.jsx`, `InstallmentsReport.jsx`, `SearchPurchases.jsx`, and `ReportsLayout.jsx` (**strictly NO printing in `POS.jsx` or `PurchaseEntry.jsx`**).

- [x] **Item 3 — Create Print Templates for Reports & Purchase Receipts (`pdf_purchase_content.html`, `pdf_report_content.html`)**:
  - `backend/api/templates/api/pdf_purchase_content.html` & `backend/api/views/purchase_views.py`:
    - Add `@action(detail=False, methods=['post']) def desktop_print(self, request)` on `PurchaseInvoiceViewSet`.
    - Format all numbers in `pdf_purchase_content.html` as whole Arabic-Indic integers (`٠١٢٣٤٥٦٧٨٩`) via `ed2ad`.
  - `backend/api/templates/api/pdf_report_content.html` & `backend/api/views/report_views.py`:
    - Create `pdf_report_content.html` (A4 layout, Cairo font, company header, active filters bar, KPI summary cards, and multi-page table with repeating `<thead>` and whole Arabic-Indic numerals `٠١٢٣٤٥٦٧٨٩`).
    - Add `ReportDesktopPrintView` at `POST /api/v1/reports/desktop_print/` and wire a **"طباعة التقرير"** button in `ReportsLayout.jsx` that opens `PrintModal.jsx`.

---

### Batch V1-4 — AI Agent Skill for Raw Data $\rightarrow$ `.sqlite3` Backup Generator (Item 8)

- [x] **Item 8 — Create Standalone AI Agent Skill (`ventapos-backup-generator`)**:
  - Create `C:\Users\Abdo\.gemini\config\skills\ventapos-backup-generator\SKILL.md` (and a helper template script in `C:\Users\Abdo\.gemini\config\skills\ventapos-backup-generator\scripts\build_sqlite_backup.py`) outside the app runtime.
  - Document the exact `salesapp_*` SQLite schema, HMAC-SHA256 `receipt_hash` generation (`security_utils.generate_receipt_signature`), `ClientLicense` preservation/demo initialization, and pre-license legacy receipt transformation rules (`sale_date < lic_start_month`, `products_text` only, `InstallmentPayment` schedule generation) so the AI agent can convert any raw client Excel/CSV/JSON/text notebook into a verified `.sqlite3` backup file on demand.

---

### Batch V1-5 — Desktop Packaging, Admin UAC, v1.0.0 Release, Auto-Updater & Release Repo (Items 13, 14, 15, 16)

- [x] **Item 13 — Force `.exe` to Run as Administrator (`uac_admin=True`)**:
  - `VentaPOS_NextGen/VentaPOS.spec:63`: Set `uac_admin=True` inside `EXE(...)`.
  - `VentaPOS_NextGen/build_exe.py:46`: Add `'--uac-admin'` to the PyInstaller arguments list.

- [x] **Item 14 — Prepare Version `1.0.0` Production Release & Git Tag (`https://github.com/abdalatyf/ventaPOS`)**:
  - `backend/backend/settings.py`: Set `APP_VERSION = "1.0.0"` and `WHITENOISE_USE_FINDERS = True` so WhiteNoise serves `frontend/dist` assets cleanly when `DEBUG = False` in frozen builds.
  - `backend/backend/urls.py`: Update the SPA catch-all regex to `re_path(r'^(?!api/|admin/|static/|media/).*$', TemplateView.as_view(template_name='index.html'))`.
  - `frontend/package.json` & `launcher.py`: Set version to `1.0.0` and window title to `VentaPOS NextGen v1.0.0`.
  - Commit all v1.0.0 codebase changes and tag `v1.0.0` in the Git repository (`https://github.com/abdalatyf/ventaPOS`).

- [x] **Items 15 & 16 — Application Update System & Production-Only GitHub Installer Repo (`https://github.com/venta-pos/releases`)**:
  - Backend (`backend/api/views/system_views.py` or `tools_views.py`):
    - Add `GET /api/v1/system/check-update/` that checks `https://raw.githubusercontent.com/venta-pos/releases/main/version.json` (comparing remote `version` against `settings.APP_VERSION = "1.0.0"`) and `POST /api/v1/system/apply-update/` that downloads the new installer/update package into `%TEMP%\VentaPOS_Update\`, verifies its SHA-256 hash, launches the update installer (preserving `%APPDATA%\VentaPOSTest\db.sqlite3`), and exits the running process.
  - Frontend (`Navbar.jsx` / `SettingsIndex.jsx`): Add update notification badge / **"تحديث البرنامج"** action and Update Modal.
  - Release Automation (`scripts/publish_release.py`): Create a release publisher script that packages the compiled build + `version.json` manifest and pushes **only** the binary release artifacts (zero source code) to `https://github.com/venta-pos/releases`.

---

### Batch V1-6 — Marketeer Licensing App (`LicenseManager`) + Supabase & Egyptian Arabic User Manual (Items 17, 18)

- [x] **Item 17 — Connect Marketeer Licensing App (`D:\Projects\VentaPOS\LicenseManager`) to Supabase (`https://tgfhyyfwgcvotxfwbnhd.supabase.co`)**:
  - Require an active internet connection to generate any license key in `LicenseManager` (block offline key generation).
  - Before saving locally or displaying the generated key in `licenses/views.py` (`add_license_view`), insert the license record (`marketeer_id`, `client_name`, `client_phone`, `store_name`, `machine_id`, `product_id`, `product_name`, `license_code`, `price`, `start_date`, `expiry_date`, `created_at`) into Supabase (`https://tgfhyyfwgcvotxfwbnhd.supabase.co/rest/v1/licenses`).
  - Provide `D:\Projects\VentaPOS\LicenseManager\supabase_schema.sql` with strict Row-Level Security (RLS) policies and a PostgreSQL `BEFORE UPDATE OR DELETE` trigger that raises an exception so license rows are strictly append-only (`INSERT` and `SELECT` only — never modified or deleted).
  - Add unit tests in `D:\Projects\VentaPOS\LicenseManager\test_license_manager.py` verifying that key generation succeeds when Supabase returns `201` and aborts without revealing the key when offline or when Supabase rejects the insert.

- [x] **Item 18 — Write User Manual in Easy Egyptian Arabic (`دليل المستخدم`)**:
  - Create `VentaPOS_NextGen/USER_MANUAL_AR.md` (and an in-app Help / User Manual viewer accessible from `Navbar.jsx` / `SettingsIndex.jsx`) written in simple, practical Egyptian commercial Arabic covering:
    1. التشغيل الأول والتفعيل واستعادة النسخة الاحتياطية.
    2. إنشاء الفروع وإضافة المناديب والموردين والأصناف.
    3. تسجيل فواتير المبيعات (كاش وقسط) والبيانات القديمة قبل الاشتراك.
    4. طباعة جداول الأقساط وتقارير النظام وفواتير المشتريات.
    5. كارت الصنف (تعديل المندبة وتسجيل العجز) والمرتجعات.
    6. المصروفات وتصنيفها، والتقارير المالية والسيولة ومرتبات المناديب.
