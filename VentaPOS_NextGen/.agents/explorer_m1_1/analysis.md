# Backend Codebase Exploration Analysis Report — VentaPOS NextGen POS Entry Testing

**Author:** Backend Codebase Explorer (`explorer_m1_1`)  
**Date:** 2026-07-04  
**Target Codebase:** `d:\Projects\VentaPOS\VentaPOS_NextGen\backend` and `main.py`  
**Working Directory:** `d:\Projects\VentaPOS\VentaPOS_NextGen\.agents\explorer_m1_1`

---

## 1. Executive Summary

This investigation analyzes the Django backend architecture, models, API contracts, financial math, signature hash algorithms, tenant isolation mechanisms, and SQLite database storage for the VentaPOS NextGen application. The backend is designed as a local-first, multi-tenant POS application with DRF (Django REST Framework) APIs supporting both Cash and Installment sales workflows.

---

## 2. Django Models Documentation

Located at: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\models.py`

### 2.1 `Receipt` (الفاتورة / الوصل)
- **Table Name:** `receipt`
- **Primary Key:** `id` (`UUIDField` default `uuid.uuid4`)
- **Key Fields:**
  - `tenant`: `ForeignKey` to `Tenant` (ON DELETE CASCADE)
  - `branch`: `ForeignKey` to `Branch` (ON DELETE CASCADE)
  - `salesperson`: `ForeignKey` to `Salesperson` (ON DELETE SET_NULL, nullable)
  - `local_id`: `IntegerField` (sequential local device ID, `>= 0`)
  - `receipt_number`: `IntegerField` (sequential invoice number, `>= 0`)
  - `client_uuid`: `UUIDField` (idempotency key per device/tenant)
  - `receipt_hash`: `CharField(max_length=255, unique=True)` (HMAC-SHA256 signature)
  - `customer_name`: `CharField(max_length=200)`
  - `phone_number`: `CharField(max_length=50, blank=True, null=True)`
  - `address`: `CharField(max_length=255, blank=True, null=True)`
  - `area`: `CharField(max_length=150, blank=True, null=True)`
  - `total_amount`: `DecimalField(max_digits=12, decimal_places=2, default="0.00")`
  - `down_payment`: `DecimalField(max_digits=12, decimal_places=2, default="0.00")`
  - `installment_system`: `CharField(max_length=255, blank=True, null=True)`
  - `sale_year`: `IntegerField` (validators `>= 2025`)
  - `sale_month`: `IntegerField` (validators `1..12`)
  - `is_cash_sale`: `BooleanField(default=False)`
  - `products_text`: `TextField(blank=True, null=True)`
  - `is_confirmed`: `BooleanField(default=False)`
  - `is_deleted`: `BooleanField(default=False)` (soft-delete flag)
  - `created_at_local`: `DateTimeField` (device time timestamp)
  - `created_at`: `DateTimeField(auto_now_add=True)` (ingestion timestamp)
- **Constraints & Indexes:**
  - `UniqueConstraint`: `(tenant, client_uuid)` — ensures idempotency per tenant.
  - Check constraints for non-negative values and valid month/year.
  - Partial manager filtering out soft-deleted records (`ActiveManager`).

### 2.2 `SaleItem` (أصناف الفاتورة المباعة)
- **Table Name:** `sale_item`
- **Primary Key:** `id` (`UUIDField`)
- **Key Fields:**
  - `tenant`: `ForeignKey` to `Tenant`
  - `receipt`: `ForeignKey` to `Receipt` (`related_name="sale_items"`)
  - `inventory_item`: `ForeignKey` to `InventoryItem` (`related_name="sale_items"`)
  - `quantity`: `IntegerField` (validators `>= 0`)
  - `unit_price`: `DecimalField(max_digits=12, decimal_places=2)`
  - `is_deleted`: `BooleanField`
  - `created_at`: `DateTimeField`

### 2.3 `InstallmentPayment` (القسط المجدول)
- **Table Name:** `installment_payment`
- **Primary Key:** `id` (`UUIDField`)
- **Key Fields:**
  - `tenant`: `ForeignKey` to `Tenant`
  - `receipt`: `ForeignKey` to `Receipt` (`related_name="installment_payments"`)
  - `payment_date`: `DateField` (25th of month rule enforced via business logic)
  - `amount`: `DecimalField(max_digits=12, decimal_places=2)`
  - `is_deleted`: `BooleanField`
  - `created_at`: `DateTimeField`

### 2.4 `InventoryItem` (Product / البضاعة / الصنف)
- **Table Name:** `inventory_item`
- **Primary Key:** `id` (`UUIDField`)
- **Key Fields:**
  - `tenant`: `ForeignKey` to `Tenant`
  - `branch`: `ForeignKey` to `Branch`
  - `local_id`: `IntegerField`
  - `name`: `CharField(max_length=200)`
  - `initial_quantity`: `IntegerField` (`>= 0`)
  - `initial_purchase_price`: `DecimalField(12, 2)`
  - `initial_commission_amount`: `DecimalField(12, 2)`
  - `initial_month`: `IntegerField(1..12)`
  - `initial_year`: `IntegerField(>= 2025)`
  - `is_deleted`: `BooleanField`
- **Stock Calculator Methods:**
  - `get_stock_at_date(month, year)`: Aggregates initial quantity + purchases + surplus adjustments - sales - returns - deficit adjustments up to specified month/year.

### 2.5 `Customer` Representation
- There is no separate `Customer` database table. Customer details (`customer_name`, `phone_number`, `address`, `area`) are stored directly on each `Receipt`.
- In cash sales (`is_cash_sale=True`), if `customer_name` is empty or omitted, `ReceiptSerializer` automatically defaults `customer_name` to `"عميل نقدي"`.
- Autocomplete searches historical `Receipt` records to suggest customer names, phones, addresses, and areas.

### 2.6 Tenant Models & Multi-tenancy
- `Tenant` (`tenant` table): `id` (UUID), `company_code` (unique string max 10), `name`, `is_active`, `is_deleted`.
- `CloudUser`: User accounts linked to `Tenant`.
- `Branch`: Branch entity (`tenant`, `local_id`, `name`).
- `Salesperson`: Sales representative (`tenant`, `branch`, `local_id`, `name`, `device_token`).
- `ClientLicense`: License status (`tenant`, `machine_id`, `invoices_balance`, `expiry_date`, `license_code_hash`).

---

## 3. API Endpoints Map

All endpoints are mounted under URL prefix `/api/v1/` (configured in `backend/urls.py`).

| Endpoint | Method | View / Class | Description & Payload Rules |
|---|---|---|---|
| `/api/v1/product-suggestions/` | `GET` | `ProductSuggestionsView` | Query params: `term`, `branch_id`, `month`, `year`. Filters products by name/branch, checks subscription dates, computes retroactive safe stock limit. Returns `[{ "id", "value", "max" }]`. |
| `/api/v1/customer-suggestions/` | `GET` | `CustomerSuggestionsView` | Query params: `term`, `field` (`name`, `phone`, `address`, `area`), `salesperson_id`, `current_area`, `current_name`. Converts Arabic numerals, scores relevance, returns `[{ "value" }]` in Arabic numerals. |
| `/api/v1/receipts/` | `GET`, `POST` | `ReceiptViewSet` | Handles receipt creation. Accepts nested `sale_items` (or alias `items`) and `installment_payments` (or alias `installments`). Validates license balance, safe stock limits, auto-generates receipt hash and deducts license balance. |
| `/api/v1/installment-payments/` | `GET`, `POST` | `InstallmentPaymentViewSet` | Manages individual installment payments. |
| `/api/v1/sale-items/` | `GET`, `POST` | `SaleItemViewSet` | Manages individual sale items. |
| `/api/v1/inventory-items/` | `GET`, `POST` | `InventoryItemViewSet` | CRUD for products; includes custom action `/api/v1/inventory/{pk}/stock/` for available quantity. |
| `/api/v1/license/status/` | `GET` | `LicenseStatusView` | Checks active invoice balance and license expiry date for tenant. |
| `/api/v1/license/activate/` | `POST` | `LicenseActivateView` | Activates license code using machine ID signature validation. |

---

## 4. Financial Math, Business Logic & Security Algorithms

### 4.1 Cash Sale vs. Installment Sale Workflow Rules
1. **Cash Sale (`is_cash_sale = True`)**:
   - `customer_name` defaults to `"عميل نقدي"` if not specified.
   - `down_payment` equals `total_amount`.
   - `installment_payments` list is empty.
2. **Installment Sale (`is_cash_sale = False`)**:
   - Requires full customer info (`customer_name`, `phone_number`, `address`, `area`, `installment_system`).
   - `down_payment` paid upfront; remaining balance (`total_amount - down_payment`) is scheduled across `installment_payments`.

### 4.2 Installment Date Calculation (25th-of-Month Rule)
- Installment payments follow the strict 25th day of the month convention.
- In `InstallmentPaymentSerializer.to_internal_value` and `ReceiptSerializer.create`, virtual input fields `payment_month` and `payment_year` automatically map to `payment_date = YYYY-MM-25`.

### 4.3 Retroactive Sale Safe Stock Limit Protection
- Function `calculate_safe_stock_limit(item, default_year, default_month, target_year, target_month)` in `api/views.py`:
  - When posting a retroactive sale (e.g. sale date earlier than latest system date), it iterates through every consecutive month between target sale date and latest date.
  - Calculates stock at each month using `item.get_stock_at_date(m, y)`.
  - Takes the **minimum** stock level across all months in that interval as the `safe_limit`.
  - If requested sale quantity > `safe_limit`, `ReceiptSerializer` raises a `ValidationError` ("عفواً، لا يمكن البيع! أقصى كمية يمكن بيعها بأثر رجعي...").

### 4.4 Cryptographic Signature Hash Algorithms
Located in `api/utils/security_utils.py`:
1. **Receipt Signature (`receipt_hash`)**:
   ```python
   data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}-ITEMS[{items_str}]"
   receipt_hash = hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
   ```
   - Prevents manual database tampering or invoice payload modification.
2. **License Record Signature (`license_code_hash`)**:
   ```python
   data_to_sign = f"{expiry_date}-{balance}-{machine_id}-{product_id}-{is_active}"
   license_code_hash = hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
   ```
   - Every receipt submission deducts 1 from `invoices_balance` and re-signs `license_code_hash` to enforce license integrity.

### 4.5 Multi-tenant Isolation Architecture
- Header `X-Company-Code` identifies the tenant per HTTP request.
- `TenantFromRequestMixin`:
  - Resolves active `Tenant` by company code.
  - Automatically filters viewset querysets (`qs.filter(tenant=tenant)`).
  - Injects `tenant` into serializer context (`context["tenant"]`).
- Database constraints: `UniqueConstraint` on `(tenant, client_uuid)`, `(tenant, branch, local_id)` ensure database-level multi-tenant boundaries.

---

## 5. Database Architecture & Seed Data Management

### 5.1 Dual-Database Router Architecture (`SystemDBRouter`)
Configured in `backend/settings.py` and `api/db_router.py`:
1. **`default` Database (`backend/db/business_data.sqlite3`)**:
   - Operational business tables: `tenant`, `branch`, `salesperson`, `inventory_item`, `commission_history`, `inventory_adjustment`, `supplier`, `purchase_invoice`, `purchase_invoice_item`, `receipt`, `sale_item`, `installment_payment`, `expense`, `company_setting`, `pending_external_receipt`.
2. **`system` Database (`%APPDATA%/VentaPOS/system.sqlite3`)**:
   - Licensing and system tables: `client_license`, `used_license`, `license_history`, `action_log`, `auth_user`, `authtoken_token`.

### 5.2 Desktop App Encrypted Runtime Database
In `main.py`:
- Master encrypted file: `%APPDATA%/VentaPOS/business_data.enc`
- On app launch, `initialize_database_security()` decrypts `business_data.enc` using Fernet cipher key into runtime temporary file `%TEMP%/~sys_runtime_cache_v1.tmp`.
- Auto-save worker background thread re-encrypts runtime DB every 5 minutes and on exit.

### 5.3 Migrations & Seed Data Management
- Database migrations: Run via `python manage.py migrate --database=system` and `python manage.py migrate`.
- Auto-migration on startup in `main.py` via `ensure_databases_are_ready()`.
- Tenant setup helper script: `backend/create_tenant.py` creates default tenant `1234` and main branch.
- Historical data migration script: `migrate_legacy_data.py` transfers legacy SQLite data to new schema models.

---

## 6. Verification & Test Evidence

- Unit tests in `backend/api/tests/test_suggestions_and_parity.py` verify:
  1. `test_customer_suggestions_area_field` — Autocomplete area filtering and relevance ranking.
  2. `test_customer_suggestions_arabic_numerals` — Bidirectional Arabic/English numeral translation in autocomplete queries.
  3. `test_product_suggestions_stock_validation` — Stock availability calculation and retroactive limit calculations.
  4. `test_serializer_day_25_installment_payment` — Enforcing 25th day of the month for installment schedules.

---

## 7. Conclusions & Testing Guidance for M2/M3

1. **POS Entry Submission (`POST /api/v1/receipts/`)**:
   - Always supply `X-Company-Code` header (e.g. `X-Company-Code: 1234` or tenant code).
   - Ensure `ClientLicense` row exists in `system` database with `invoices_balance > 0` and valid signature.
2. **Cash Sale Test Flow**:
   - `is_cash_sale: true` -> backend automatically handles missing `customer_name` by assigning `"عميل نقدي"`.
3. **Installment Sale Test Flow**:
   - `is_cash_sale: false` -> supply `sale_items`, `down_payment`, and `installment_payments` (`payment_month`, `payment_year`). Verify created dates map to `YYYY-MM-25`.
4. **Data Integrity Checks**:
   - Verify `Receipt.receipt_hash` is populated with valid HMAC-SHA256 string.
   - Verify `ClientLicense.invoices_balance` decremented by 1 per receipt.
