---
name: ventapos-desktop
description: Complete technical documentation of the VentaPOS Desktop subsystem, including database schema, configuration, views, local license validation, migration logic, automation scripts, and known limitations, fully verified against the source code.
---

# VentaPOS Desktop Subsystem - Comprehensive Technical Documentation

This document serves as the absolute, audited technical reference for the VentaPOS Desktop subsystem. Every detail within this document has been verified against the actual Django implementation and automation scripts in the codebase.

---

## 1. Project Structure & Database Configurations

The VentaPOS Desktop application is built using the Django framework, wrapped locally in a graphical container.

*   **Root Directory**: `d:\Projects\VentaPOS\Desktop\sales\`
*   **Settings File**: `d:\Projects\VentaPOS\Desktop\sales\sales\settings.py`
*   **Main URL Mapping**: `d:\Projects\VentaPOS\Desktop\sales\sales\urls.py`
*   **Primary Application Module**: `d:\Projects\VentaPOS\Desktop\sales\salesapp\`

### 1.1 Database Configuration (`settings.py:106-117`)
The application splits its database operations across two distinct SQLite databases to optimize read/write performance and isolate sensitive security/licensing data:

```python
SYSTEM_DB_PATH = os.path.join(tempfile.gettempdir(), '~sys_lic_runtime.tmp')
RUNTIME_DB_PATH = os.path.join(tempfile.gettempdir(), '~sys_runtime_cache_v1.tmp')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': RUNTIME_DB_PATH,
        'CONN_MAX_AGE': None,
    },
    'system': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SYSTEM_DB_PATH,
        'CONN_MAX_AGE': None,
    }
}
```

*   **Default Database (`default`)**: Stored at `%TEMP%\~sys_runtime_cache_v1.tmp`. It functions as a high-speed runtime cache for business transactional data (receipts, inventory, suppliers, salespersons, expenses).
*   **System Database (`system`)**: Stored at `%TEMP%\~sys_lic_runtime.tmp`. It hosts system configuration, user accounts, sessions, and local licensing records.

### 1.2 Database Router (`salesapp/db_router.py`)
Model-to-database routing is controlled dynamically by the `SystemRouter` class (`salesapp/db_router.py:1-57`):
*   **System DB Routing**: Automatically routes core Django apps (`auth`, `contenttypes`, `sessions`, `admin`) and specific local licensing models (`clientlicense`, `usedlicense`, `licensehistory`) to the `system` database.
*   **Default DB Routing**: Routes all other business transaction and setting models to the `default` database.
*   **Migrations**: Restricts database migration applications (`allow_migrate`) so that system-related tables are generated exclusively in the `system` database, and business-related tables are generated in the `default` database.

---

## 2. Models (`salesapp/models.py`)

All model classes are located in `d:\Projects\VentaPOS\Desktop\sales\salesapp\models.py`.

### 2.1 System & Authentication Models (Routed to `system` Database)

1.  **SyncDeletionLog (Lines 36-49)**
    *   *Purpose*: Tracks deletion events of business objects to synchronize deletions to the cloud server.
    *   *Fields*:
        *   `table_name` (`CharField`, `max_length=50`, choices: `Receipt`, `InventoryItem`, `Salesperson`, `Expense`, `StockTransaction`): Name of the deleted model.
        *   `record_id` (`IntegerField`): Primary key of the deleted record.
        *   `timestamp` (`DateTimeField`, `auto_now_add=True`): Time of deletion log capture.

2.  **ActionLog (Lines 54-75)**
    *   *Purpose*: Logs security and operational actions performed by local users.
    *   *Fields*:
        *   `actor` (`CharField`, `max_length=100`, `null=True`, `blank=True`): Username or user representation.
        *   `action_type` (`CharField`, `max_length=20`, choices: `CREATE`, `UPDATE`, `DELETE`, `SYNC`, `LOGIN`): Performed operation.
        *   `model_name` (`CharField`, `max_length=50`): Target section name.
        *   `details` (`TextField`, `null=True`, `blank=True`): Detailed text description of the operation.
        *   `timestamp` (`DateTimeField`, `auto_now_add=True`): Time of operation logging.

3.  **UsedLicense (Lines 474-479)**
    *   *Purpose*: Caches cryptographic hashes of activated licenses to prevent key reuse.
    *   *Fields*:
        *   `code_hash` (`CharField`, `max_length=64`, `unique=True`): SHA-256 hash of the applied license key.
        *   `used_at` (`DateTimeField`, `auto_now_add=True`): Date of key activation.

4.  **ClientLicense (Lines 482-605)**
    *   *Purpose*: Stores local license profiles, invoice balances, active subscription windows, and machine bindings.
    *   *Fields*:
        *   `product_id` (`IntegerField`, choices for products 1-16): Defines package/license tier (e.g., Trial, Yearly Basic/Pro, Lifetime, Charge Cards, Emergency Code).
        *   `start_date` (`DateField`, `null=True`, `blank=True`): Date subscription started.
        *   `expiry_date` (`DateField`, `null=True`, `blank=True`): Date subscription expires.
        *   `invoices_balance` (`PositiveIntegerField`, `default=0`): Remaining invoice counts allowed.
        *   `is_active` (`BooleanField`, `default=True`): Whether license is active.
        *   `machine_id` (`CharField`, `max_length=255`, `null=True`, `blank=True`): Hardware UUID binding.
        *   `company_code` (`CharField`, `max_length=10`, `null=True`, `blank=True`): Org code for secondary clients.
        *   `license_code_hash` (`CharField`, `max_length=64`, `null=True`, `blank=True`): Cryptographic record signature.
        *   `last_checkin` (`DateTimeField`, `auto_now=True`): Last license active verification timestamp.
        *   `is_online_active` (`BooleanField`, `default=False`): Enable cloud syncing.
        *   `online_start_date` / `online_expiry_date` (`DateField`, `null=True`, `blank=True`): Cloud sync subscription bounds.
    *   *Key Methods*:
        *   `is_expired` property (Lines 516-524): Determines expiration based on product type and dates.
        *   `get_active_license()` classmethod (Lines 526-587): Merges active license profiles into a single aggregated runtime configuration block.
        *   `save()` override (Lines 592-605): Automatically computes `license_code_hash` using `generate_record_signature` to enforce database integrity.

5.  **LicenseHistory (Lines 607-618)**
    *   *Purpose*: Archive of all license activation, renewal, and recharge history.
    *   *Fields*:
        *   `machine_id` (`CharField`, `max_length=100`)
        *   `product_name` (`CharField`, `max_length=100`)
        *   `operation_type` (`CharField`, `max_length=50`)
        *   `start_date` / `end_date` (`DateField`, `null=True`, `blank=True`)
        *   `added_balance` (`IntegerField`, `default=0`)
        *   `archived_at` (`DateTimeField`, `auto_now_add=True`)
        *   `status` (`CharField`, `max_length=50`)

### 2.2 Business Models (Routed to `default` Database)

6.  **Branch (Lines 81-90)**
    *   *Purpose*: Stores local branch/warehouse names.
    *   *Fields*: `name` (`CharField`, `max_length=100`, `unique=True`), `is_synced` (`BooleanField`, `default=False`).
    *   *Save Behavior*: `save()` override resets `is_synced` to `False` to mark the record for synchronization.

7.  **Salesperson (Lines 92-108)**
    *   *Purpose*: Represents local employees/sales agents.
    *   *Fields*: `name` (`CharField`), `branch` (`ForeignKey` to `Branch`), `is_synced` (`BooleanField`), `device_token` (`UUIDField`), `is_device_active` (`BooleanField`).
    *   *Save Behavior*: `save()` override resets `is_synced` to `False`.

8.  **CloudUser (Lines 111-125)**
    *   *Purpose*: Local login accounts for secondary viewer/cashier PCs.
    *   *Fields*: `username` (`CharField`), `password` (`CharField`), `role` (`CharField`, choices: `VIEWER`, `CASHIER`), `is_active` (`BooleanField`), `is_synced` (`BooleanField`).
    *   *Save Behavior*: `save()` override resets `is_synced` to `False`.

9.  **InventoryItem (Lines 131-222)**
    *   *Purpose*: Product catalog and inventory openings.
    *   *Fields*: `name` (`CharField`), `branch` (`ForeignKey`), `initial_quantity` (`PositiveIntegerField`), `initial_purchase_price` (`PositiveIntegerField`), `initial_commission_amount` (`PositiveIntegerField`), `initial_month`/`initial_year` (`PositiveIntegerField`).
    *   *Key Methods*:
        *   `get_stock_at_date(month, year)` (Lines 149-186): Historical stock computation (Initial + Purchases + Surplus - Sales - Returns - Deficits).
        *   `get_price_at_date(month, year)` (Lines 188-199): Retrospective purchase cost lookup.
        *   `get_commission_at_date(month, year)` (Lines 202-212): Retrospective commission lookup.

10. **CommissionHistory (Lines 225-240)**
    *   *Purpose*: Records changes to commissions over time.
    *   *Fields*: `item` (`ForeignKey`), `commission_amount` (`PositiveIntegerField`), `activation_month`/`activation_year` (`PositiveIntegerField`).

11. **InventoryAdjustment (Lines 243-265)**
    *   *Purpose*: Logs manual deficit (`DEFICIT`) or surplus (`SURPLUS`) stock events.
    *   *Fields*: `item` (`ForeignKey`), `adjustment_type` (`CharField`), `quantity` (`PositiveIntegerField`), `reason` (`CharField`), `month`/`year` (`PositiveIntegerField`).

12. **Supplier (Lines 269-278)**
    *   *Purpose*: Factory or vendor records.
    *   *Fields*: `name` (`CharField`, `max_length=200`, `unique=True`), `is_synced` (`BooleanField`, `default=False`).

13. **PurchaseInvoice (Lines 280-307)**
    *   *Purpose*: Procurement orders from suppliers.
    *   *Fields*: `branch` (`ForeignKey`), `invoice_number` (`PositiveIntegerField`), `supplier` (`ForeignKey`), `invoice_type` (`CharField`, choices: `PURCHASE`, `RETURN`), `invoice_month`/`invoice_year` (`PositiveIntegerField`), `is_synced` (`BooleanField`).

14. **PurchaseInvoiceItem (Lines 309-327)**
    *   *Purpose*: Line items for purchase invoices.
    *   *Fields*: `invoice` (`ForeignKey`), `inventory_item` (`ForeignKey`), `quantity` (`PositiveIntegerField`), `purchase_price` (`PositiveIntegerField`), `is_synced` (`BooleanField`).

15. **Receipt (Lines 332-416)**
    *   *Purpose*: Sales receipts.
    *   *Fields*: `source` (`CharField`), `receipt_number` (`PositiveIntegerField`), `branch` (`ForeignKey`), `customer_name` (`CharField`), `products_text` (`TextField`), `phone_number` (`CharField`), `address` (`CharField`), `area` (`CharField`), `total_amount` (`PositiveIntegerField`), `down_payment` (`PositiveIntegerField`), `installment_system` (`CharField`), `salesperson` (`ForeignKey`), `sale_year`/`sale_month` (`PositiveIntegerField`), `is_cash_sale` (`BooleanField`), `receipt_hash` (`CharField`), `is_synced` (`BooleanField`).
    *   *Key Methods*:
        *   `is_authentic` (Lines 364-370): Cryptographic integrity signature check.
        *   `get_next_receipt_number(branch)` (Lines 412-415): Auto-increments local invoices.
        *   *Duplicate save() override*: Documented in detail below.

16. **SaleItem (Lines 417-424)**
    *   *Purpose*: Product line items inside sales receipts.
    *   *Fields*: `receipt` (`ForeignKey`), `inventory_item` (`ForeignKey`), `quantity` (`PositiveIntegerField`), `unit_price` (`PositiveIntegerField`).

17. **InstallmentPayment (Lines 426-433)**
    *   *Purpose*: Individual payment schedule for credit transactions.
    *   *Fields*: `receipt` (`ForeignKey`), `payment_date` (`DateField`), `amount` (`PositiveIntegerField`).

18. **Expense (Lines 438-452)**
    *   *Purpose*: Logged branch overhead costs.
    *   *Fields*: `branch` (`ForeignKey`), `amount` (`DecimalField`), `description` (`CharField`), `expense_year`/`expense_month` (`IntegerField`), `is_synced` (`BooleanField`).

19. **CompanySetting (Lines 454-468)**
    *   *Purpose*: Global metadata parameters. Implements Singleton pattern.
    *   *Fields*: `name` (`CharField`), `description` (`CharField`), `phone1`/`phone2` (`CharField`), `footer_text` (`CharField`), `is_cloud_viewer` (`BooleanField`).

20. **PendingExternalReceipt (Lines 624-643)**
    *   *Purpose*: Staging stage for incoming receipts imported offline or from client sync.
    *   *Fields*: `branch` (`ForeignKey`), `batch_id` (`CharField`), `source` (`CharField`, choices: `CLOUD`, `USB`, `FILE`), `payload` (`JSONField`), `is_processed` (`BooleanField`).

### 2.3 The Duplicate `Receipt.save()` Override
In `salesapp/models.py`, `Receipt.save` is defined twice:
*   **First Definition (Lines 355-357)**:
    ```python
    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)
    ```
    *   *Audit Status*: **Dead Code**. This implementation is entirely overwritten by Python's class parser because of the second declaration below.
*   **Second Definition (Lines 372-403)**:
    *   *Purpose*: Core business enforcement logic:
        1.  Checks if it is a new record (`self.pk is None`).
        2.  Finds the active base license (`product_id < 10`) and decrements `invoices_balance` by 1.
        3.  If no base license balance exists, falls back to active recharge codes (`product_id >= 10`) and decrements by 1.
        4.  Generates the cryptographic signature signature `receipt_hash` using `generate_receipt_signature(...)` to prevent raw database manipulations.
        5.  Sets `is_synced = False`.
        6.  Executes the superclass `save()`.

---

## 3. Views & Routing (`salesapp/views/` & `urls.py`)

All view modules are located under `salesapp/views/` and map to urls in `salesapp/urls.py:28-135`.

### 3.1 Authentication & Configuration Views (`auth_views.py`)
*   `login_view(request)` (Lines 22-95): Authenticates cashier/viewer users. Secondary viewer devices authenticate remotely via `SERVER_URL/api/v1/auth/viewer/` if offline credentials do not match.
*   `logout_view(request)` (Lines 98-101): Clears user session.
*   `emergency_reset_view(request)` (Lines 104-147): Resets master superuser credentials. Bypassed by presenting `DEV_MASTER_KEY` (`"Dev2025#Sales"`) or validating an emergency license (product code 16).
*   `setup_company(request)` (Lines 150-181): Multi-step config wizard (Company, admin, first branch).
*   `general_settings(request)` (Lines 185-263): Settings editing portal. Restricts company setting edits by demanding either product 16 license code or `DEV_MASTER_KEY`.

### 3.2 Branch & Dashboard Views (`branch_views.py`)
*   `select_branch(request)` (Lines 20-26) / `set_branch(request, branch_id)` (Lines 28-35): Manages active branch session parameters.
*   `dashboard(request)` (Lines 37-238): Computes dashboard stats, current month cash flow metrics, salesperson ledger data, installment trackers, and inventory items list.
*   `UnifiedOnlineHub(request)`: Acts as the **Unified Online Hub** for managing real-time data sync across branches, cloud endpoints, and monitoring mobile device activity.

### 3.3 Duplicate Dead-Code views (`settings_views.py`)
*   **Active Functions (Lines 17-126)**:
    *   `manage_branches`, `edit_branch`, `delete_branch`: Branch CRUD actions.
    *   `manage_salespersons`, `edit_salesperson`, `delete_salesperson`: Salesperson CRUD actions.
*   **Dead-Code Duplicates (Lines 127 to end)**:
    *   *Functions*: `manage_products`, `edit_product`, `delete_product`, `update_commission`, `manage_suppliers`, `delete_supplier`, `search_purchase_invoices`, `manage_purchase_invoices`, `edit_purchase_invoice`, `delete_purchase_invoice`.
    *   *Audit Status*: **Dead Code**. These functions duplicate logic defined in `inventory_views.py` and `purchase_views.py`. Since `urls.py` routes are mapped directly to `inventory_views` and `purchase_views`, these settings views are never executed.

### 3.4 Inventory Management Views (`inventory_views.py`)
*   `manage_products(request)` (Lines 24-106) / `edit_product` / `delete_product`: Product catalog operations.
*   `update_commission(request)` (Lines 142-171) / `edit_commission_record` / `delete_commission_record`: Historical commission (agent fee rate adjustments) entries.
*   `add_adjustment(request)` (Lines 206-231): Submits stock deficit or surplus adjustments.
*   `product_ledger(request, pk)` (Lines 233-289): Detailed product ledger with historical movement details.

### 3.5 Purchase Views (`purchase_views.py`)
*   `manage_suppliers(request)` (Lines 23-39) / `delete_supplier`: Vendor CRUD views.
*   `manage_purchase_invoices(request)` (Lines 124-174) / `search_purchase_invoices` / `edit_purchase_invoice` / `delete_purchase_invoice`: Inward restock and vendor return invoices management.

### 3.6 Sales Receipt Views (`receipt_views.py`)
*   `add_receipt(request)` (Lines 155-352): Processes local cash/credit sales receipts. Validates license date bounds, checks current limits, decrements invoice balances, and hashes receipt attributes.
*   `edit_receipt` (Lines 354-535) / `delete_receipt` (Lines 599-616) / `delete_all_receipts`: Receipt modification and deletion views.
*   `search_receipts` (Lines 537-597): Invoices search grid.

### 3.7 Printing Views (`print_views.py`)
*   `print_single_receipt_view(request, receipt_id)` (Lines 172-236) / `print_batch_receipts_view(request)` (Lines 238-333): Renders print invoice outputs to PDF.

### 3.8 Licensing & Subscription Views (`subscription_views.py`)
*   `activate_app_view(request)` (Lines 151-169): Standard app entry activation wall. Decodes and processes license keys.
*   `subscription_dashboard(request)` (Lines 176-209): Displays machine signature ID, remaining license time limit, balance parameters, and license operation histories.

### 3.9 Synchronization Views (`sync_views.py`)
*   `mobile_sync_view(request)` (Lines 18-25) / `mobile_import_preview` / `mobile_import_confirm`: Offline file import and sync tools.
*   `cloud_status_view(request)` (Lines 162-213) / `push_to_cloud_ajax` (Lines 643-662): Active status and manual push AJAX triggers.
*   `local_setup_api(request)` (Lines 231-262) / `local_push_api` (Lines 264-307): Network sync endpoints for Android USB connection bridge.
*   `pending_receipts_view(request)` (Lines 309-391) / `approve_pending_receipts` (Lines 393-529): Validation staging area before merging external invoices.

### 3.10 Utility Views (`utility_views.py`)
*   `exit_app(request)` (Lines 9-12): Standard application kill exit view. Renders "Closing..." and calls `os.kill(os.getpid(), signal.SIGTERM)`.

---

## 4. Local Licensing Validator & Enforcement

### 4.1 Cryptographic License Validator (`salesapp/license_validator.py:1-93`)
Decodes license key strings into integers using a customized Base32 alphabet and verifies their HMAC signature:

1.  **Alphabet Base**: Excludes ambiguous characters `0`, `1`, `I`, and `O` to prevent typing mistakes:
    `CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` (Line 8).
2.  **Base32 Conversion**: `_custom_base32_to_int` (Lines 30-39) converts the key string back to a large integer.
3.  **Data Extraction**:
    *   Signature: `final_sig = full_int >> 44` (Extracts top 36 bits - Line 50)
    *   Masked Data: `masked_data = full_int & ((1 << 44) - 1)` (Extracts bottom 44 bits - Line 51)
4.  **XOR Unmasking**:
    *   Generates a mask: `mask = (final_sig << 8) | (final_sig >> 28)` (Line 54)
    *   Restores cleartext payload: `data_block = masked_data ^ mask` (Line 55)
5.  **Payload Extraction**:
    *   Product ID: `extracted_prod = data_block & 0xF` (4 bits - Line 58)
    *   Date Code Offset: `extracted_date_code = (data_block >> 4) & 0xFF` (8 bits - Line 59)
    *   Machine ID Hash: `extracted_machine_hash = (data_block >> 12) & 0xFFFFFFFF` (32 bits - Line 60)
6.  **HMAC Validation**:
    *   Packs the data elements: `struct.pack('>IBB', extracted_machine_hash, extracted_prod, extracted_date_code)` (Line 63)
    *   Secret Key: Derived from dynamic array of bytes: `[74, 113, 120, 81, 81, ...]` (Line 20)
    *   Calculates HMAC-SHA256 and compares the lower 36 bits of the hash with `final_sig` (Lines 68-72).
7.  **Machine Binding**: Checks if `extracted_machine_hash` matches local hardware signature `_get_machine_hash(machine_id)`.
8.  **Date Decoding**: Decodes start month/year offset relative to `BASE_YEAR = 2025` (Lines 81-83).

### 4.2 Middleware Enforcement (`salesapp/middleware.py:1-106`)
Enforces the licensing constraints on HTTP requests using `LicenseEnforcementMiddleware`:
1.  **Static/Media Bypass**: Automatically allows traffic to static resources and admin panels.
2.  **Activation Bypass**: Excludes activation paths (`activate_app`, `subscription_dashboard`) to prevent redirection loops.
3.  **Performance Caching**: Caches license status in session memory (`request.session['is_licensed'] = True`). If checked within `< 5` minutes and not saving a receipt, bypasses heavy database checks.
4.  **Security Tampering Check**: Re-calculates and validates the signature of each `ClientLicense` database entry on validation triggers using `generate_record_signature`. If any record's database values do not match its cryptographic hash, the code automatically marks the license inactive (`is_active=False`).
5.  **Expirations & Actions**:
    *   Redirects to `activate_app` if the base time license is expired or not present.
    *   Redirects to `subscription_dashboard` with an error message if saving a receipt while `total_invoices_balance <= 0`.
    *   Redirects to `shutdown_app` if the client is a secondary `is_cloud_viewer` and the main online sync subscription has expired.

---

## 5. Migration Logic & Automation Scripts

### 5.1 Startup Migration Sequence (`run_app.py:279-289`)
During application startup, `run_app.py` triggers migrations programmatically:
1.  **System Database**: Migrates the `system` database (which holds user credentials, login sessions, and license states) using:
    `call_command('migrate', database='system', interactive=False)` (Line 283).
2.  **Business Database**: Migrates the `default` database (which holds receipts and inventory cache tables) using:
    `call_command('migrate', interactive=False)` (Line 286).

### 5.2 Desktop Bootloader & Runtime (`run_app.py`)
`run_app.py` boots a secure local runtime environment using Waitress and Python-Webview:
*   **Security Initialization**: Calls `initialize_database_security` to clear temporary caches (`~sys_runtime_cache_v1.tmp`), decrypt the production database (`business_data.enc` using Fernet cipher key), and cache a decrypted SQLite copy in Temp.
*   **Auto-Save Background Worker**: Spawns `auto_save_worker` thread (Lines 211-216) which performs full database checkpoints (`PRAGMA wal_checkpoint(FULL)`) and encrypts database changes back to `business_data.enc` every 5 minutes.
*   **Port Binder**: Searches for a dynamic free port (`get_free_port()`) on loopback address `127.0.0.1`.
*   **Waitress Server**: Boots waitress to serve Django's WSGI application at the allocated port.
*   **Safe Exit Routine**: Binds to webview `closing` and `closed` events. Triggers cleanups on exit, closes Django DB connections, pushes final local synced items, overwrites and removes runtime temp database files, and terminates using `os._exit(0)`.

> ⚠️ **Product Manager Directive**: The file `run_browser.py` is entirely excluded from this documentation scope.

### 5.3 Release Engineering Scripts (`d:\Projects\VentaPOS\Desktop\`)

1.  **`build_release.py`**
    *   *Purpose*: Command-line release engineering interface offering 4 tasks: (1) PyInstaller execution and version archiving; (2) Inno Setup executable package construction (both Full installation and Patch scripts); (3) Auto Git committing and release version tagging; (4) Mock cloud upload script operations.
2.  **`module_builder.py`**
    *   *Purpose*: Updates version configuration strings in `version.txt`. Invokes PyInstaller targeting `VentaPOS.spec`. Copies compiled folders into the release `Archive` dir.
    *   *Differential Analysis*: `analyze_differences(old_dir, new_dir)` computes files added, modified, and deleted between versions to package patch updates.
3.  **`module_installer.py`**
    *   *Purpose*: Compiles setup binaries. Generates temporary `Patch_Setup.iss` scripts on the fly for patch releases. Restricts updates to matching base application registry IDs (`HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\{5E3B8F9A-1234-4B5C-9D8E-7F6A5B4C3D2E}_is1`).
4.  **`module_git.py`**
    *   *Purpose*: Automates local git stages, commits, and logs version release tags (`v{version}`).
5.  **`module_cloud.py`**
    *   *Purpose*: Placeholder script containing instructions and configurations for publishing release binaries to cloud storage (MediaFire).
6.  **`config.py`**
    *   *Purpose*: Configures path parameters: PyInstaller dist directories, workspace paths, releases folders, and path coordinates for Inno Setup's command-line compiler (`ISCC.exe` at `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`).

---

## 6. Quality Audit & Architectural Resolutions

### 6.1 Architectural Resolutions (Product Manager Approved)

#### License Expiry Logic Inconsistency
*   *Issue*: `receipt_views.py:199-201` blocks receipt creation if `invoice_date > (expiry_date - 1 month)`. However, the unit tests inside `test_license.py` check if `invoice_date > expiry_date`, expecting the license to allow receipt additions up until the day of expiration.
*   *Resolution*: **The 1-month early renewal block in the views is intentional.** The desktop views are correct. The unit test suite in `test_license.py` must be updated to align with this policy.

#### Technical Debt: System Database Encryption
*   *Known Limitation*: Unlike the business database (which is decrypted to Temp and re-encrypted on exit), the `system` database (`~sys_lic_runtime.tmp` in the OS Temp folder) is stored **unencrypted**. Since it resides in OS Temp, it can be deleted during standard disk cleanups, requiring re-authentication and re-activation.
*   *Resolution*: **Accepted Technical Debt.** This behavior is documented as a known platform limitation.

#### Technical Debt: Background Sync Trigger in Production
*   *Known Limitation*: Continuous background auto-sync relies on `runserver` being present in CLI arguments (`apps.py:13`). Production waitress environments do not execute with `runserver`, thus disabling continuous background sync.
*   *Resolution*: **Accepted Technical Debt.** Continuous 1-minute background sync is disabled in production. Syncing is explicitly triggered via the Safe Exit routine or UI actions.

---

### 6.2 Grill-Me Protocol: Codebase Warnings & Unresolved Risks

> ⚠️ **CRITICAL WARNINGS & RISK FACTORS**
>
> 1. **Stored License Key File Is Never Restored**
>    * *Observation*: `salesapp/security_utils.py:85` defines `load_stored_license()` to read license credentials from `%LOCALAPPDATA%/VentaPOS/license.key`.
>    * *Risk*: This function is **never imported or called** during application startup. If a user's temporary `system` database (`~sys_lic_runtime.tmp`) is deleted, the application fails to restore the license automatically from the saved key file.
>
> 2. **Staged Cloud Sync False Alarm in Explorer Analysis**
>    * *Observation*: The upstream explorer analysis report claimed that the cloud initial sync view (`initial_sync_views.py:54-63`) crashes due to invalid model fields (`barcode`, `current_purchase_price`) and missing database constraints (`branch`).
>    * *Audited Code Reality*: Code verification shows that `initial_sync_views.py:57-65` correctly supplies `branch=main_branch` and populates only valid fields (`name`, `initial_quantity`, `initial_purchase_price`, etc.). **The crash bug does not exist in the codebase.**
