# VentaPOS NextGen Rebuild - Target Requirements Specification (PRD)

This document establishes the absolute functional and non-functional requirements for the NextGen Rebuild of the VentaPOS ecosystem, migrating the legacy system from its desktop container (Waitress/Python-Webview/SQLite) to a modern, scalable web-based React/Django architecture with 100% feature parity.

---

## 1. Executive Mission & System Architecture

The NextGen rebuild must transition VentaPOS from a single-user offline desktop app to a modern, multi-tenant web application.
*   **Backend**: Django (Python 3.11+) with Django REST Framework (DRF), utilizing a unified PostgreSQL database (replacing the dual-database SQLite architecture).
*   **Frontend**: React (RTL-first, Tailwind CSS/Bootstrap) delivering a responsive web interface.
*   **Security & Database Isolation**: The architecture must maintain database level segregation between tenant settings while offering centralized license verification.
*   **Parity Principle**: Every business constraint, financial calculation, and sync mechanism must match the legacy desktop application exactly, resolving known discrepancies.

---

## 2. Arabic-First & Right-to-Left (RTL) UI Standards

Per the system rules defined in `AGENTS.md`, the user interface must be fully localized to Arabic and adopt a Right-to-Left (RTL) layout. The terminology and tone must balance professional clarity with simple, everyday market terms in Egypt ("لغة سوق مهنية ومبسطة").

### 2.1 Terminology Mapping Table
The rebuild MUST enforce the following terminology across all views, forms, spreadsheets, and database labels:

| Legacy Technical Term | Classical Arabic | Egyptian Market Term (Required in UI) | Purpose |
| :--- | :--- | :--- | :--- |
| **Customer** | المشتري / العميل | **العميل** | Customer identity |
| **Product / Item** | المنتج / السلعة | **البضاعة** or **الصنف** | Catalog items |
| **Cash Registry / Vault** | الصندوق / الحساب النقدي | **الخزنة** | Cash drawer / cash flow |
| **Invoice / Receipt** | إيصال البيع / سند الصرف | **الفاتورة** or **الوصل** | Transaction slip |
| **Ledger / Book** | دفتر الأستاذ / الحسابات العامة | **الدفتر** | Historical logs & journals |
| **Cash Payment** | الدفع الفوري | **النقدية** or **الكاش** | Immediate settlement |
| **Installments** | دفعات مجدولة | **القسط** or **الأقساط** | Credit schedule |
| **Salesperson** | مندوب المبيعات | **المندوب** | Agent or representative |
| **Branch / Warehouse** | الفرع / المخزن | **المخزن** or **الفرع** | Local warehouse |
| **Down Payment** | الدفعة المقدمة | **المقدم** or **الدفعة المقدمة** | Installment initial cash |
| **Supplier** | المورد | **المورد** or **الموردين** | Vendor for restock |
| **Expense** | المصروفات | **المصاريف** | Overhead costs |
| **License / Code** | الترخيص / كود التفعيل | **الترخيص** or **الكود** | Verification code |

### 2.2 Tone and Language Rules
*   **Do not use** overly strict corporate/legalistic Arabic (e.g., standard Modern Standard Arabic that is cold and unfamiliar to retail merchants).
*   **Do not use** excessive street slang or informal terminology (e.g., avoid terms like "يا معلم", "يا باشا").
*   Use terms that Egypt's retail and wholesale merchants interact with daily to maintain high accessibility.

---

## 3. Safe Data Migration Path

A robust Python migration script must be provided to migrate legacy offline installations to the new Django ORM schema.

### 3.1 Migration Source Input
Legacy clients utilize a split SQLite database configuration:
1.  **Default DB (`~sys_runtime_cache_v1.tmp`)**: Hosts transactional data (Receipts, SaleItems, InventoryItems, etc.).
2.  **System DB (`~sys_lic_runtime.tmp`)**: Hosts Django credentials, session data, and licensing records.

The migration script must accept paths to both files:
`python migrate_legacy_data.py --default-db <path_to_default_db> --system-db <path_to_system_db>`

### 3.2 Migration Rules & Data Mapping
The script must perform the following extractions and maps into the new unified Django ORM:
*   **Auth System**: Extract `auth_user` rows from the legacy system database and load them as tenant-linked users.
*   **Reference Data**: Map `Branch`, `Salesperson`, and `Supplier` records. Restructure all relationships using Django standard primary key mapping.
*   **Inventory Opening Balances**: Migrated `InventoryItem` records must carry over initial values: `initial_quantity`, `initial_purchase_price`, `initial_commission_amount`, `initial_month`, and `initial_year`.
*   **Ledgers & Adjustments**: Populate historical `InventoryAdjustment` records (`DEFICIT` and `SURPLUS`) and `CommissionHistory` logs.
*   **Invoices & Receipts**: Migrate `Receipt` records. The legacy receipt hash `receipt_hash` MUST be imported as is to preserve historical auditability. Line items (`SaleItem`) and installment schedules (`InstallmentPayment`) must be merged into their relative child tables.
*   **Licensing Logs**: Migrate `ClientLicense`, `UsedLicense`, and `LicenseHistory` to maintain activation audit logs.

### 3.3 Verification & Attestation Criteria
*   The script must count records for core entities before and after migration. The counts for **Receipts**, **Customers**, **InventoryItems**, **Salespersons**, and **Suppliers** must match exactly.
*   The script must calculate the sum of `total_amount` for all receipts and verify that the sum matches exactly between the legacy SQLite databases and the new target database.
*   Verify that any active license balance (`invoices_balance`) is carried over without modification.

---

## 4. Time-Machine Inventory Ledger Engine

The NextGen rebuild must implement the exact retrospective "Time-Machine" inventory stock, cost, and commission tracking algorithms from the legacy system. This allows retrieving the system state at any arbitrary month and year.

### 4.1 Stock Calculation Algorithm: `get_stock_at_date(month, year)`
To calculate the stock balance of an item at a specific month and year:
1.  **Date Verification**: If `year < initial_year` or `(year == initial_year and month < initial_month)`, return `0`.
2.  **Total Purchased (Inward)**: Sum the `quantity` of all `PurchaseInvoiceItem` rows where:
    *   `invoice__invoice_type = 'PURCHASE'`
    *   `invoice__invoice_year < year` OR `(invoice__invoice_year == year and invoice__invoice_month <= month)`
3.  **Total Returned (Outward Factory)**: Sum the `quantity` of all `PurchaseInvoiceItem` rows where:
    *   `invoice__invoice_type = 'RETURN'`
    *   `invoice__invoice_year < year` OR `(invoice__invoice_year == year and invoice__invoice_month <= month)`
4.  **Total Sold (Outward Sales)**: Sum the `quantity` of all `SaleItem` rows linked to a `Receipt` where:
    *   `receipt__sale_year < year` OR `(receipt__sale_year == year and receipt__sale_month <= month)`
5.  **Total Adjustments (Deficits/Surplus)**: Filter `InventoryAdjustment` logs where `year < year` OR `(year == year and month <= month)`.
    *   `total_deficit`: Sum of quantity where `adjustment_type = 'DEFICIT'`.
    *   `total_surplus`: Sum of quantity where `adjustment_type = 'SURPLUS'`.
6.  **Mathematical Balance Formula**:
    $$\text{final\_stock} = (\text{initial\_quantity} + \text{total\_purchased} + \text{total\_surplus}) - (\text{total\_sold} + \text{total\_returned} + \text{total\_deficit})$$
    Return $\max(0, \text{final\_stock})$.

### 4.2 Unit Cost Search Engine: `get_price_at_date(month, year)`
To calculate the retrospective purchase unit cost:
*   Query `PurchaseInvoiceItem` where:
    *   `invoice__invoice_type = 'PURCHASE'`
    *   `invoice__invoice_year <= year`
    *   `invoice__invoice_year < year` OR `invoice__invoice_month <= month`
*   Order items by `-invoice__invoice_year`, `-invoice__invoice_month`, and `-id` (getting the latest entry).
*   If an invoice item exists, return its `purchase_price`. Otherwise, fall back and return `initial_purchase_price`.

### 4.3 Sales Commission Lookup: `get_commission_at_date(month, year)`
To calculate the retrospective salesperson commission:
*   Query `CommissionHistory` where:
    *   `activation_year <= year`
    *   `activation_year < year` OR `activation_month <= month`
*   Order records by `-activation_year`, `-activation_month`, and `-id`.
*   If a record exists, return its `commission_amount`. Otherwise, fall back and return `initial_commission_amount`.

---

## 5. Cryptographic Licensing & Validation Protocol

The licensing system relies on an 80-bit dense cryptographic key model. The validation logic must be built using the exact algorithm parameters of the legacy validator to ensure backward compatibility with issued keys.

### 5.1 The Obfuscated Secret Key
*   **ASCII Code Representation**:
    `[74, 113, 120, 81, 81, 65, 75, 111, 48, 66, 98, 73, 55, 54, 116, 107, 110, 97, 75, 108, 104, 100, 48, 114, 67, 57, 104, 68, 99, 97, 109, 95, 98, 113, 74, 121, 119, 88, 109, 97, 88, 72, 113, 65, 75, 107, 86, 80, 82, 90, 104, 122, 103, 82, 106, 72, 88, 45, 122, 77, 69, 49, 49, 101, 110, 120, 50, 111, 66, 56, 111, 95, 105, 118, 74, 67, 110, 50, 112, 88, 66, 88, 45, 80, 111, 119]`
*   **Plaintext Equivalent**:
    `b"JqxQQAKo0BbI76tknaKlhd0rC9hDcam_bqJywXmaXHqAKkVPRZhzgRjHX-zME11enx2oB8o_ivJCn2pXBX-Pow"`

### 5.2 Key Alphabet & Bitwise Layout
*   **Alphabet**: `CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` (Base32 format, excluding `0`, `1`, `I`, `O`).
*   **Format**: Keys are presented to users formatted as `XXXX-XXXX-XXXX-XXXX`.

```
                    80-Bit Integrated Bitwise Layout
      ┌──────────────────────────┬──────────────────────────┐
      │   HMAC-SHA256 Signature  │        Masked Data       │
      │        (36 Bits)         │         (44 Bits)        │
      └─────────────┬────────────┴─────────────┬────────────┘
                    │                          │
                    └─► Mask Generation ───────┼─► XOR Masking
                        (final_sig Shift/OR)   │
                                               ▼
                                     ┌───────────────────┐
                                     │ Machine ID Hash   │ (32 Bits)
                                     ├───────────────────┤
                                     │ Date Code Offset  │ (8 Bits)
                                     ├───────────────────┤
                                     │ Product ID        │ (4 Bits)
                                     └───────────────────┘
```

### 5.3 Decrypting and Validation Pipeline
1.  **Custom Base32 to Integer**: Convert the 16-character string key back to an 80-bit integer (`full_int`).
2.  **Bitwise Separation**:
    *   `final_sig = full_int >> 44` (Extract the top 36 bits).
    *   `masked_data = full_int & ((1 << 44) - 1)` (Extract the bottom 44 bits).
3.  **XOR Mask Resolution**:
    *   Calculate the symmetric mask using signature bit-shifting:
        $$\text{mask} = (\text{final\_sig} \ll 8) \mid (\text{final\_sig} \gg 28) \pmod{2^{44}}$$
4.  **Payload Extraction**:
    *   Restore cleartext data block: `data_block = masked_data ^ mask`.
    *   Extract:
        *   `prod_int = data_block & 0xF` (4 bits) -> Target `product_id` matches `prod_int + 1`.
        *   `date_code = (data_block >> 4) & 0xFF` (8 bits).
        *   `machine_hash = (data_block >> 12) & 0xFFFFFFFF` (32 bits).
5.  **Signature Verification (HMAC-SHA256)**:
    *   Pack the extracted variables in big-endian format into a 6-byte buffer:
        `struct.pack('>IBB', machine_hash, prod_int, date_code)`
    *   Compute the HMAC-SHA256 signature using the Obfuscated Secret Key.
    *   Extract the lower 36 bits of the resulting signature and compare it with the parsed `final_sig`. If they do not match, the code is invalid.
6.  **Hardware & Expiry Checks**:
    *   Calculate the hash of the local client's machine identifier: `machine_hash_expected = SHA256(machine_id)[:4]` (Unpacked as big-endian 32-bit unsigned integer).
    *   Assert `machine_hash == machine_hash_expected`.
    *   Convert `date_code` (months since January 2025) to a subscription start date:
        $$\text{start\_year} = 2025 + \lfloor\text{date\_code} / 12\rfloor$$
        $$\text{start\_month} = 1 + (\text{date\_code} \bmod 12)$$
    *   Look up duration based on `product_id` (Trial is exactly 60 days, Basic plans are 365 days, Lifetime is 36,135 days) and assert current date is within range.

---

## 6. Row-Level Database Tampering Protection

To prevent local merchants or administrators from manually editing SQLite files or database tables (e.g., adding arbitrary balances or dates via direct SQL entry), the application must implement row-level signatures for sensitive license configurations.

### 6.1 Record Signature Algorithm
For each row in `ClientLicense`, the system must calculate a cryptographic hash `license_code_hash` using:
$$\text{license\_code\_hash} = \text{HMAC-SHA256}(\text{expiry\_date}, \text{invoices\_balance}, \text{machine\_id}, \text{product\_id}, \text{is\_active})$$
*   The HMAC must be computed using the system's secret key.

### 6.2 Forensic Verification Check
*   The system's request validation middleware must query all active licenses (`is_active=True`) on every non-static request.
*   For each row, it must recalculate the record signature.
*   If the database `license_code_hash` does not match the newly calculated signature, tampering is detected.
*   **Reaction Policy**: The middleware must immediately execute a direct SQL/ORM update command:
    `ClientLicense.objects.filter(pk=lic.pk).update(is_active=False)`
    *(Bypassing the standard Django `save()` method ensures that custom override hooks do not silently recalculate the hash during the emergency deactivate).*

---

## 7. Two-Way Sync Architecture & Key Resolution

The sync architecture must support two-way data sharing, allowing viewer/mobile clients to push invoices and download the product catalog while resolving legacy sync bugs.

### 7.1 Unified JSON Contract & Key Normalization
To prevent the legacy silent data loss bug during receipt approval (where installment due date schedules were stripped due to key discrepancies), the sync engine must standardize the receipt and installment payload structure:
*   **Key Names**: Serializations must use the key `"installments"` (not `"payments"`) containing arrays of payment schedules.
*   **Due Date Key**: Each payment entry must use `"payment_date"` (not `"date"`).
*   **Example Structured Payload**:
    ```json
    {
      "receipt_hash": "string",
      "customer_name": "العميل التجريبي",
      "total_amount": 3000.0,
      "down_payment": 1000.0,
      "installment_system": "1000 * 2",
      "is_cash_sale": false,
      "installments": [
        {"payment_date": "2026-07-25", "amount": 1000.0},
        {"payment_date": "2026-08-25", "amount": 1000.0}
      ]
    }
    ```

### 7.2 Mobile Sync Translation Layer
The synchronization system must translate field differences between the web server's Django fields and the offline mobile client's SQLite schemas. The mobile worker client must translate field namespaces as follows:

1.  **Inventory/Product Field Mappings**:
    *   `id` $\leftarrow$ `local_id`
    *   `initial_quantity` $\leftarrow$ `quantity`
    *   `initial_purchase_price` $\leftarrow$ `purchase_price`
    *   `initial_commission_amount` $\leftarrow$ `salesperson_commission_amount`
2.  **Receipt Field Mappings**:
    *   `id` $\leftarrow$ `local_id`
    *   `branch_id` $\leftarrow$ `local_branch_id`
    *   `salesperson_id` $\leftarrow$ `local_salesperson_id`
    *   `created_at` $\leftarrow$ `created_at_local`

### 7.3 Sync Ingestion Enhancements
*   **No Data Loss Ingestion**: Refactor `MobilePushIngestView` to parse and import the detailed list of sold items, down payments, and installment due date plans from the mobile client's payload. It must not drop details or hardcode values to "Cloud Item" cash sales.
*   **Complete Pull Loop**: The mobile client's `pullUpdates()` worker must pull and save all sub-tables: `"sale_items"` (into local table `receipt_items`) and `"installments"` (into local table `installment_payments`) to prevent downloading empty shells of invoices.
*   **Collision Prevention**: Do not enforce uniqueness constraints on `(source_machine_id, local_id)` for receipts. Use the cryptographic `receipt_hash` as the unique key across all systems.

---

## 8. Screen Mappings & UI Interaction Flows

The application must support the following core views and workflows, localized to Arabic (RTL) using Egyptian market terminology.

### 1. Login Flow (شاشة تسجيل الدخول)
*   Provides text input fields for Username (`اسم المستخدم`) and Password (`كلمة المرور`).
*   In Viewer mode, if credentials do not match local database configurations, checks credentials remotely via `/api/v1/auth/viewer/` to confirm.

### 2. Company Setup Wizard (مساعد إعداد الشركة)
*   A multi-step setup wizard presented on empty system initializations:
    *   **Step 1: Company Profile**: Enter Company Name (`اسم الشركة`), Phone 1 (`رقم التليفون الأساسي`), Phone 2 (`رقم التليفون البديل`), and Receipt Footer text (`رسالة نهاية الفاتورة`).
    *   **Step 2: Admin Account**: Setup the system supervisor/administrator credentials.
    *   **Step 3: Branch/Warehouse**: Enter the name of the first warehouse/branch.
*   Restricts system access until the onboarding setup is complete.

### 3. Dashboard (شاشة التحكم / الصفحة الرئيسية)
*   Displays KPI badges: Total Sales (`إجمالي المبيعات`), Cash Registry (`الخزنة`), Active Sync Devices (`الأجهزة النشطة`), and Pending Approvals Queue (`قائمة الانتظار للوصلات`).
*   **Pending Queue Badge**: Circular badge. If pending sync items count $> 0$, the color shifts to Orange/Red; if pending count $== 0$, it turns Green/Teal.
*   Shows installment summaries, upcoming dues, and delinquent accounts lists.

### 4. Products List (دفتر الأصناف والبضاعة)
*   Displays the product inventory.
*   Supports details popup showing current stock, cost price, and historical movement ledger.
*   Provides actions to update item commission rules (`تحديث المندبة`) or log manual stock adjustments (`DEFICIT` / `SURPLUS`).

### 5. Sales Receipts View (فاتورة البيع / الوصل)
*   Checkout screen offering product selection, customer data input, and down payment recording.
*   **Credit Installment Due Date Rule**:
    *   If a sale is a credit/installment sale, the payment schedule MUST generate monthly installments due on the **25th of each month**, starting with the month following the sale month.
    *   *Calculation*: `due_date = date(sale_year, sale_month, 25) + relativedelta(months = i + 1)`.
    *   Manual modification of installment dates is prohibited.
*   On receipt save, compute and write the cryptographic signature hash `receipt_hash`.

### 6. Suppliers & Purchase Invoices (الموردين وفواتير الشراء)
*   CRUD interface for Suppliers (`الموردين`).
*   Form to record Restock (`شراء بضاعة`) or Return (`مرتجع بضاعة`) purchase invoices.
*   Correctly adjusts stock levels in the ledger on save.

### 7. Expenses View (دفتر المصاريف)
*   Log overhead payments (rent, electricity, salaries) by Branch and Month/Year.

### 8. License Activation Page (شاشة التنشيط)
*   Displays the Hardware Signature Hash (`رقم الجهاز`).
*   Includes text field to submit the activation key code (`كود التنشيط`).
*   Shows active plans, remaining invoice limits (`رصيد الفواتير`), and cloud synchronization limits.
