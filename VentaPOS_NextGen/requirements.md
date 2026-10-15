# VentaPOS NextGen - Requirements Specification

## 1. What is this App?

VentaPOS NextGen is a **Back-Office Desk Management Application** designed specifically for the business owner or manager (المدير/صاحب المحل). It is **not** a traditional point-of-sale terminal used by cashiers.

*   **Business Type:** Furniture, household items, and electronics (مفروشات، أدوات منزلية، أجهزة كهربائية).
*   **Workflow:** Salespeople (مناديب) sell products in the field using physical paper notebooks. The manager later enters these receipts into the VentaPOS system.
*   **User Scope:** Single user (one manager/admin). No other user roles.
*   **Deployment:** One app per machine, managing multiple branches from a single interface.
*   **Inventory:** Each branch has completely independent inventory. There are no stock transfers between branches.
*   **Platform:** Desktop application using a Python backend (Django) wrapped in PyWebView. It is tested via a web browser during development.
*   **Localization:** The entire UI is in Arabic (RTL).
*   **Tone:** Professional but simple Egyptian Arabic (لغة سوق مهنية ومبسطة).

## 2. Technical Architecture

*   **Database:** SQLite configured in WAL (Write-Ahead Logging) mode.
*   **Backend:** Django 5.x + Django REST Framework (DRF).
*   **Frontend:** React 19 + Vite.
*   **Desktop Wrapper:** PyWebView.
*   **Primary Keys:** Standard auto-incrementing integers (`AutoField`/`BigAutoField`). **No UUIDs** used for primary keys.
*   **Authentication:** DRF `TokenAuthentication`, designed for a single admin user.
*   **Soft Delete:** Implemented via an `is_deleted` boolean field and a custom `ActiveManager` on all models.
*   **Financial Fields:** `DecimalField(12,2)` for all monetary values.
*   **Quantities:** `PositiveIntegerField` (integers only, no fractions).
*   **Date System:** The system uses a Monthly-based approach (`month`/`year` integer fields) rather than exact daily dates. A `DefaultDate` mechanism returns the current business month.
    *   **Display Format:** `MM/YYYY` (e.g., `8/2026`). Month comes first. No leading zero on the month.
    *   **Digit Convention:** Western digits (0-9) are used universally for both display and storage/API to improve performance and prevent split-brain state bugs. (Arabic-Indic digits ٠١٢٣٤٥٦٧٨٩ were dropped).
*   **Multi-tenancy/Cloud:** Completely removed. No multi-tenancy, no cloud syncing, and no `Tenant` model.

## 3. Data Models

The system is built on 17 core models defined in `models.py`.

| Model Name | Arabic Name | Key Fields / Methods |
| :--- | :--- | :--- |
| **Branch** | المخزن/الفرع | `name`, `is_deleted`, `created_at` |
| **Salesperson** | المندوب | `name`, `branch` (FK), `device_token`, `is_device_active`, `is_deleted` |
| **InventoryItem** | البضاعة/الصنف | `name`, `branch` (FK), `initial_quantity`, `initial_purchase_price`, `initial_commission_amount`, `initial_month`, `initial_year`<br>*Methods:* `get_stock_at_date()`, `get_safe_available_qty()`, `get_commission_at_date()`, `get_price_at_date()` |
| **CommissionHistory** | سجل العمولات | `item` (FK), `commission_amount`, `activation_month`, `activation_year`. Tracks sales commission changes. |
| **InventoryAdjustment** | جرد وتسويات | `item` (FK), `adjustment_type` (DEFICIT/SURPLUS), `quantity`, `reason`, `month`, `year` |
| **Supplier** | الموردين | `name` |
| **PurchaseInvoice** | فاتورة الشراء/المرتجع | `branch` (FK), `supplier` (FK), `invoice_number`, `invoice_type` (PURCHASE/RETURN), `invoice_month`, `invoice_year` |
| **PurchaseInvoiceItem**| | `invoice` (FK), `inventory_item` (FK), `quantity`, `purchase_price` |
| **Receipt** | الفاتورة | `branch`, `salesperson`, `receipt_number`, `client_uuid`, `receipt_hash`, `customer_name`, `phone_number`, `address`, `area`, `total_amount`, `down_payment`, `installment_system`, `sale_year`, `sale_month`, `is_cash_sale`, `receipt_type` (SALE/RETURN), `parent_receipt`, `products_text`, `source`, `sync_action`, `is_confirmed` |
| **SaleItem** | | `receipt` (FK), `inventory_item` (FK), `quantity`, `unit_price` |
| **InstallmentPayment** | القسط | `receipt` (FK), `payment_date`, `amount` |
| **Expense** | المصاريف | `branch` (FK), `amount`, `description`, `expense_year`, `expense_month` |
| **CompanySetting** | إعدادات الشركة | **Singleton**. `name`, `description`, `phone1`, `phone2`, `footer_text`, `is_cloud_viewer`, `collection_commission_rate`, `zoom_level` |
| **ClientLicense** | الترخيص | `product_id`, `start_date`, `expiry_date`, `invoices_balance`, `is_active`, `machine_id`, `company_code`, `license_code_hash`, online fields |
| **UsedLicense** | الأكواد المستخدمة | `code_hash` (unique) |
| **LicenseHistory** | أرشيف التراخيص | `machine_id`, `product_name`, `operation_type`, `dates`, `added_balance`, `status` |
| **PendingExternalReceipt**| | `branch` (FK), `batch_id`, `source`, `payload` (JSON), `is_processed` |

> [!NOTE]
> `collection_commission_rate` is located on the `CompanySetting` model because it is a company-wide percentage, not per-branch.

## 4. Business Rules

### 4.1 Products & Inventory
*   **Branch-Scoped:** Products belong to a specific branch. The same product name can exist in different branches with separate stock levels.
*   **Identification:** No barcodes or SKUs are used. Products are identified purely by their name via text-based search.
*   **Pricing:** There is no fixed selling price on products. The manager enters the price manually per sale.
*   **Stock Calculation (Time-Machine Method):** Stock is calculated dynamically:
    `Stock = initial_quantity + purchases + surplus + sales_returns - sold - purchase_returns - deficit`
*   **Stock Limits:** Stock can never go negative. It is clamped to `max(0, calculated_stock)`.
*   **Sales Commission (مندبة):** A fixed monetary value per product (e.g., 50 EGP per unit sold). Changes over time are tracked in `CommissionHistory`.
*   **Collection Commission (عمولة تحصيل):** A company-wide percentage stored in `CompanySetting.collection_commission_rate`.

### 4.2 Sales (Receipts)
*   **Entry Process:** The manager manually enters receipts copied from the salespeople's paper notebooks.
*   **Data Captured:** Customer information (stored as raw text), items (with quantities and prices), and the payment type.
*   **Payment Types:** Restricted to **Cash (نقدي)** and **Installments (تقسيط)** only. No credit cards or deferred payments.
*   **Receipt Numbering:** Auto-assigned sequentially per branch.
*   **Security:**
    *   `receipt_hash` (HMAC) is used for tamper protection.
    *   `client_uuid` is used to prevent double-submission from the frontend.
*   **Denormalization:** `products_text` stores a summary of the receipt's items for quick display without joins.

### 4.3 Installments (تقسيط)
*   **Scheduling Only:** The system generates an installment schedule but does **not** track actual payments or remaining balances over time.
*   **Printing Date:** The day "25" is often just printed on the schedule; it has no mathematical significance for calculations.
*   **Calculation Focus:** Calculations are based purely on the month and year.
    *   *Example:* 3000 EGP over 6 installments = 500 EGP/month, starting the following month.

### 4.4 Returns (مرتجع)
*   Implemented via `ReturnReceipt.jsx`.
*   A return creates a new receipt record with `receipt_type='RETURN'` and references the original sale via `parent_receipt` FK.
*   Processing a return adds the items' quantities back into the branch's inventory.

### 4.5 Purchases / Procurement (المشتريات)
*   **Scope:** In scope for the initial launch.
*   **Functionality:** Manager records purchase invoices received from suppliers.
*   **Inventory Impact:** Purchases add stock to inventory. Purchase returns reduce stock.
*   **Components:** `PurchaseEntry.jsx` and `SearchPurchases.jsx` exist and require review.

### 4.6 Customers
*   **Implicit Structure:** There is no dedicated `Customer` model or account balances.
*   **Data Storage:** Customer details (`customer_name`, `phone_number`, `address`, `area`) are simply text fields saved directly on the `Receipt`.
*   **UX:** The frontend provides autocomplete suggestions based on historical receipt data to speed up entry.

### 4.7 Salespeople (المناديب)
*   **Compensation:** They work on a commission-only basis (no base salary).
*   **Salary Calculation:**
    `Salary = (Sales Commission [مندبة] × Units Sold) + (Collection Commission Rate × Collections)`
*   This performance is tracked and displayed in reports.

### 4.8 Expenses (المصاريف)
*   **Structure:** Simple free-text description, amount, branch, and month/year.
*   **Categories:** No formal expense categories exist.
*   **Scope:** Branch-scoped.

### 4.9 Printing
*   **Scope:** Printing is supported **only for Installment Schedules**. Standard cash receipts are not printed.
*   **Mechanism:** Uses backend calls to `os.startfile()` or SumatraPDF for silent printing.

## 5. Features In Scope

### 5.1 Core Features
1.  **Login & Auth:** Single admin, token-based authentication.
2.  **Branch Selection:** Switch between branches.
3.  **POS / Sales Entry:** (`POS.jsx`) - The primary, solid foundation of the app. Working well.
4.  **Inventory Management:** Manage items, initial stock, and adjustments.
5.  **Product Ledger:** View the history/time-machine of a product's stock.
6.  **Purchases/Procurement:** Record inbound stock from suppliers.
7.  **Returns (مرتجع):** Process customer returns.
8.  **Search Receipts:** Find historical receipts.
9.  **Search Purchases:** Find historical purchase invoices.
10. **Expenses:** Record monthly branch expenses.
11. **Branches Management:** Add/edit branches.
12. **Salespersons Management:** Add/edit sales personnel.
13. **Settings:** Manage company info and admin password.

### 5.2 Reports (8 Total)
1.  Dashboard Report
2.  CashDrawer Report
3.  Expenses Report
4.  Installments Report
5.  Inventory Movement Report
6.  Profit & Loss Report
7.  Receipts Report
8.  Salesperson Performance Report (Must show sales commission + collection commission).

### 5.3 Tools
1.  **Sync Tools:** Offline USB/file synchronization (infrastructure for future use).
2.  **Backup & Restore:** Critical must-have feature for data safety.

### 5.4 Licensing & Security
1.  80-bit cryptographic licensing.
2.  Machine ID hardware binding.
3.  Receipt HMAC hashing.
4.  Recovery code implemented as a special license type.

### 5.5 Demo Mode Lifecycle
1.  **First Launch:** No license found -> Enters Demo Mode. Generates random sample data.
2.  **Subsequent Demo Starts:** Database is wiped and fresh demo data is generated on every restart.
3.  **Activation:** Once a valid license is entered, demo data is wiped, database is empty, and user is directed to the Setup page.
4.  **Production:** After Setup, the app runs normally with real, persistent data.

## 6. Out of Scope / Removed

*   **Smart Import (Excel):** Removed. Handled by external tools.
*   **Mobile App:** Deferred.
*   **Cloud Sync Server:** Deferred.
*   **Action Logs:** Deleted entirely.
*   **Tenant / CloudUser Models:** Removed entirely.
*   **Legacy Data Migration:** Not needed.
*   **Legacy Code Matching:** NextGen is completely independent; no need to match old code exactly.
*   **Multi-user Roles:** Not planned.
*   **Customer Accounts/Balances:** Not planned.
*   **Barcode/SKU Scanning:** Not planned.
*   **Card/Visa Payments:** Not planned.
*   **Expense Categories:** Not planned.

## 7. Approach & Priorities

*   **Backend First:** Fix Models -> Views -> API -> Frontend.
*   **Quality over Speed:** No strict deadline. Correctness comes first, followed by feature completeness, then polish.
*   **Resource:** Solo developer project.
*   **Documentation:** Skip writing external docs for now. Fix the code first, update documentation later.
*   **Architecture Anchor:** `POS.jsx` is the core foundation. Everything else builds around it.
*   **Cleanup:** `PosEntry.jsx` is deprecated and should be deleted.

## 8. File Status Summary

### 8.1 Frontend Pages
| File | Status | Action Required |
| :--- | :--- | :--- |
| `POS.jsx` (58KB) | ✅ SOLID | Working end-to-end. Do not break. |
| `PosEntry.jsx` (34KB) | ❌ DEPRECATED | Delete. |
| `Inventory.jsx` | Needs Review | Needs review/rebuild. |
| `ProductLedger.jsx` | Needs Review | Currently uses mock data. |
| `PurchaseEntry.jsx` | Needs Review | |
| `SearchPurchases.jsx` | Needs Review | |
| `ReturnReceipt.jsx` | Needs Review | |
| `SearchReceipts.jsx` | Partially Working | Has issues, needs fixing. |
| `Expenses.jsx` | Needs Review | |
| `Dashboard.jsx` | Needs Review | |
| `BranchSelection.jsx` | Needs Review | |
| `Login.jsx` | Needs Implementation | Skipped during initial dev. |
| `Setup.jsx` | Needs Review | |
| `ActivationSetup.jsx` | Needs Review | |
| Settings pages | Unknown State | Needs full review. |
| Report pages (8) | Mostly Complete | 7 have real code, 1 (CashDrawer) might be a stub. |
| Tool pages | Needs Review | |

### 8.2 Backend Files
| File | Status | Action Required |
| :--- | :--- | :--- |
| `models.py` | ✅ CLEAN | 17 models, clean state. Stock `max(0)` logic present. |
| `views.py` (103KB) | Needs Review | Review all endpoints for alignment with new models. |
| `serializers.py` (31KB)| Needs Review | |
| `urls.py` (5KB) | Needs Review | |
| `middleware.py` | Needs Review | |
| `tools_views.py` | Needs Review | |
| `utils/` | Needs Review | Check security and licensing logic. |
