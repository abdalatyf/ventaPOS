# Backend Models Documentation — VentaPOS NextGen

**Subsystem**: Django Backend API  
**Version**: 1.0.0  
**Date**: 2026-06-28  
**Schema Source**: `d:/Projects/VentaPOS/database_schema.md`  
**API Contract**: `d:/Projects/VentaPOS/api_contract.md`  
**Status**: ✅ SYNCHRONIZED WITH SCHEMA SINGLE SOURCE OF TRUTH

---

## 1. Overview

This document describes every Django model, serializer, and viewset in the VentaPOS NextGen backend (`backend/api/`). All models have been rebuilt to exactly match the approved PostgreSQL DDL schema.

### Key Architectural Policies Enforced

| Policy | Implementation |
|--------|---------------|
| **Multi-Tenant Isolation** | Every table has a `tenant` ForeignKey. `TenantFromRequestMixin` injects the active tenant from `X-Company-Code` header or JWT claim into every queryset. |
| **Soft Deletes** | `is_deleted = BooleanField(default=False)` on every table. `ActiveManager` auto-filters `is_deleted=False`. `SoftDeleteModelViewSet.destroy()` sets `is_deleted=True` instead of `DELETE`. |
| **UUID Primary Keys** | All models use `UUIDField(primary_key=True, default=uuid.uuid4)`. |
| **Financial Precision** | All monetary columns use `DecimalField(max_digits=12, decimal_places=2)` — no floats. |
| **Timezone-Aware Timestamps** | All datetime fields are `DateTimeField` (maps to `TIMESTAMP WITH TIME ZONE`). Requires `USE_TZ=True` in Django settings. |
| **Receipt Tamper-Proofing** | `receipt_hash VARCHAR(255) UNIQUE NOT NULL` — HMAC-SHA256 hash generated at creation and re-generated on update. |
| **License Row Integrity** | `license_code_hash VARCHAR(64)` — HMAC-SHA256 of `(expiry_date + invoices_balance + machine_id + product_id + is_active)`. Recalculated on every balance deduction. |
| **Idempotency (Push sync)** | `UNIQUE (tenant_id, client_uuid)` constraint on `receipt` prevents duplicate receipt creation from retried payloads. |
| **Pessimistic Locking** | `SELECT FOR UPDATE` used when deducting license balance and when auto-assigning receipt numbers. |

---

## 2. Model Reference

### 2.1 Tenant (`tenant`)

**Table**: `tenant`  
**Description**: Root organizational entity. All other tenant-owned tables reference this.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | `gen_random_uuid()` | |
| `company_code` | VARCHAR(10) | UNIQUE NOT NULL | Short company identifier |
| `name` | VARCHAR(100) | NOT NULL | Company display name |
| `is_active` | BOOLEAN | NOT NULL DEFAULT TRUE | Global on/off switch |
| `is_deleted` | BOOLEAN | NOT NULL DEFAULT FALSE | Soft-delete flag |
| `created_at` | TIMESTAMPTZ | NOT NULL auto | Server ingestion time |

**Indexes**: `idx_tenant_active` on `id WHERE is_deleted=FALSE`

---

### 2.2 CloudUser (`cloud_user`)

**Table**: `cloud_user`  
**Description**: User accounts for web/cloud access with role-based authorization.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `username` | VARCHAR(150) | NOT NULL | Unique per tenant |
| `password_hash` | VARCHAR(255) | NOT NULL | Pre-hashed, write-only in API |
| `role` | VARCHAR(50) | CHECK IN (`ADMIN`, `CASHIER`, `VIEWER`, `BRANCH_MANAGER`) | |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id, username) WHERE is_deleted=FALSE`  
**Indexes**: `idx_cloud_user_tenant`

---

### 2.3 Branch (`branch`)

**Table**: `branch`  
**Description**: Physical branch or warehouse within a tenant.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `local_id` | INTEGER | NOT NULL, `>= 0` | SQLite sequential ID from device |
| `name` | VARCHAR(150) | NOT NULL | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**:
- `UNIQUE (tenant_id, local_id)` — `uq_tenant_branch_local_id`
- `UNIQUE (tenant_id, name) WHERE is_deleted=FALSE` — `uq_tenant_branch_name`

---

### 2.4 Salesperson (`salesperson`)

**Table**: `salesperson`  
**Description**: Sales representative, assigned to a branch.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `local_id` | INTEGER | NOT NULL, `>= 0` | |
| `name` | VARCHAR(100) | NOT NULL | |
| `device_token` | UUID | DEFAULT uuid4 | Mobile device auth token |
| `is_device_active` | BOOLEAN | DEFAULT TRUE | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id, local_id)` — `uq_tenant_salesperson_local_id`

---

### 2.5 InventoryItem (`inventory_item`)

**Table**: `inventory_item`  
**Description**: Product/SKU catalog entry, scoped to a branch.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `local_id` | INTEGER | `>= 0` | SQLite row id |
| `name` | VARCHAR(200) | NOT NULL | |
| `initial_quantity` | INTEGER | `>= 0` DEFAULT 0 | Opening stock |
| `initial_purchase_price` | DECIMAL(12,2) | `>= 0.00` DEFAULT 0.00 | Cost price |
| `initial_commission_amount` | DECIMAL(12,2) | `>= 0.00` DEFAULT 0.00 | Salesperson commission |
| `initial_month` | INTEGER | BETWEEN 1 AND 12 | |
| `initial_year` | INTEGER | `>= 2025` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id, local_id)` — `uq_tenant_item_local_id`  
**Indexes**: `idx_inventory_item_tenant_branch`

**Business Methods**:
- `get_stock_at_date(month, year)` → Computes net stock by aggregating initial qty + purchases − returns − sales ± adjustments up to the given period.
- `get_commission_at_date(month, year)` → Returns the effective commission rate for the period (latest `CommissionHistory` entry or `initial_commission_amount`).

---

### 2.6 CommissionHistory (`commission_history`)

**Table**: `commission_history`  
**Description**: Tracks commission rate changes over time for a product.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `inventory_item` | UUID FK → inventory_item | ON DELETE CASCADE | |
| `commission_amount` | DECIMAL(12,2) | `>= 0.00` | |
| `activation_month` | INTEGER | BETWEEN 1 AND 12 | |
| `activation_year` | INTEGER | `>= 2025` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

---

### 2.7 InventoryAdjustment (`inventory_adjustment`)

**Table**: `inventory_adjustment`  
**Description**: Stock correction entries (deficit or surplus).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `inventory_item` | UUID FK → inventory_item | ON DELETE CASCADE | |
| `adjustment_type` | VARCHAR(20) | CHECK IN (`DEFICIT`, `SURPLUS`) | |
| `quantity` | INTEGER | `>= 0` | |
| `reason` | VARCHAR(255) | nullable | Optional explanation |
| `adjustment_month` | INTEGER | BETWEEN 1 AND 12 | |
| `adjustment_year` | INTEGER | `>= 2025` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

---

### 2.8 Supplier (`supplier`)

**Table**: `supplier`  
**Description**: Procurement vendor entity.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `name` | VARCHAR(200) | NOT NULL | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id, name) WHERE is_deleted=FALSE`

---

### 2.9 PurchaseInvoice (`purchase_invoice`)

**Table**: `purchase_invoice`  
**Description**: Vendor purchase or return invoice header.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `supplier` | UUID FK → supplier | ON DELETE CASCADE | |
| `invoice_number` | INTEGER | `>= 0` | |
| `invoice_type` | VARCHAR(20) | CHECK IN (`PURCHASE`, `RETURN`) | |
| `invoice_month` | INTEGER | BETWEEN 1 AND 12 | |
| `invoice_year` | INTEGER | `>= 2025` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id, branch_id, invoice_number, invoice_type)`

---

### 2.10 PurchaseInvoiceItem (`purchase_invoice_item`)

**Table**: `purchase_invoice_item`  
**Description**: Line item within a purchase or return invoice.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `purchase_invoice` | UUID FK → purchase_invoice | ON DELETE CASCADE | |
| `inventory_item` | UUID FK → inventory_item | ON DELETE CASCADE | |
| `quantity` | INTEGER | `>= 0` | |
| `purchase_price` | DECIMAL(12,2) | `>= 0.00` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

---

### 2.11 Receipt (`receipt`)

**Table**: `receipt`  
**Description**: Sales transaction / invoice record. Central financial entity.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `salesperson` | UUID FK → salesperson | ON DELETE SET NULL, nullable | |
| `local_id` | INTEGER | `>= 0` | SQLite sequential ID |
| `receipt_number` | INTEGER | `>= 0` | Human-readable invoice number |
| `client_uuid` | UUID | NOT NULL | Idempotency key from device |
| `receipt_hash` | VARCHAR(255) | UNIQUE NOT NULL | HMAC-SHA256 tamper-proof hash |
| `customer_name` | VARCHAR(200) | NOT NULL | |
| `phone_number` | VARCHAR(50) | nullable | Maps to `customer_phone` in SQLite |
| `address` | VARCHAR(255) | nullable | Maps to `customer_address` in SQLite |
| `area` | VARCHAR(150) | nullable | Maps to `customer_area` in SQLite |
| `total_amount` | DECIMAL(12,2) | `>= 0.00` | |
| `down_payment` | DECIMAL(12,2) | `>= 0.00` | |
| `installment_system` | VARCHAR(255) | nullable | Installment plan description |
| `sale_year` | INTEGER | `>= 2025` | |
| `sale_month` | INTEGER | BETWEEN 1 AND 12 | |
| `is_cash_sale` | BOOLEAN | DEFAULT FALSE | |
| `products_text` | TEXT | nullable | Denormalized products summary |
| `is_confirmed` | BOOLEAN | DEFAULT FALSE | Set by master POS |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at_local` | TIMESTAMPTZ | NOT NULL | Device local timestamp |
| `created_at` | TIMESTAMPTZ | auto | Server ingestion time |

**Constraints**: `UNIQUE (tenant_id, client_uuid)` — idempotency guard  
**Indexes**: `idx_receipt_tenant_branch`, `idx_receipt_hash`

> [!IMPORTANT]
> The `receipt_hash` is **always generated server-side** using HMAC-SHA256 of `(receipt_number + total_amount + sale_month + sale_year + items)`. Clients must send the hash they computed — the server validates and stores it. A mismatch causes a 400 rejection.

---

### 2.12 SaleItem (`sale_item`)

**Table**: `sale_item`  
**Description**: Individual sold product line within a receipt.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `receipt` | UUID FK → receipt | ON DELETE CASCADE | |
| `inventory_item` | UUID FK → inventory_item | ON DELETE CASCADE | |
| `quantity` | INTEGER | `>= 0` | |
| `unit_price` | DECIMAL(12,2) | `>= 0.00` | Selling price per unit |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

---

### 2.13 InstallmentPayment (`installment_payment`)

**Table**: `installment_payment`  
**Description**: Scheduled installment payment tied to a receipt.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `receipt` | UUID FK → receipt | ON DELETE CASCADE | |
| `payment_date` | DATE | NOT NULL | Due date (25th-of-month rule) |
| `amount` | DECIMAL(12,2) | `>= 0.00` | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

> [!NOTE]
> The **25th-of-month rule**: installment due dates are automatically generated starting from the 25th of the month following the sale date. Manual modification via the API is prohibited by the contract.

---

### 2.14 Expense (`expense`)

**Table**: `expense`  
**Description**: Operational overhead expense logged against a branch.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `amount` | DECIMAL(12,2) | `>= 0.00` | |
| `description` | VARCHAR(255) | NOT NULL | |
| `expense_year` | INTEGER | `>= 2025` | |
| `expense_month` | INTEGER | BETWEEN 1 AND 12 | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at_local` | TIMESTAMPTZ | NOT NULL | Device local time |
| `created_at` | TIMESTAMPTZ | auto | Server ingestion time |

---

### 2.15 CompanySetting (`company_setting`)

**Table**: `company_setting`  
**Description**: Per-tenant company profile settings. Singleton (one row per tenant).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID OneToOne → tenant | ON DELETE CASCADE | |
| `name` | VARCHAR(100) | NOT NULL | |
| `description` | VARCHAR(200) | nullable | |
| `phone1` | VARCHAR(20) | NOT NULL | |
| `phone2` | VARCHAR(20) | nullable | |
| `footer_text` | VARCHAR(250) | nullable | |
| `is_cloud_viewer` | BOOLEAN | DEFAULT FALSE | Cloud viewer mode enabled |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Constraints**: `UNIQUE (tenant_id)` — enforced via `OneToOneField` + DB constraint

---

### 2.16 ClientLicense (`client_license`)

**Table**: `client_license`  
**Description**: Active POS device activation profile with cryptographic row integrity.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `product_id` | INTEGER | BETWEEN 1 AND 16 | |
| `start_date` | DATE | NOT NULL | |
| `expiry_date` | DATE | nullable | Time-based license |
| `invoices_balance` | INTEGER | `>= 0` DEFAULT 0 | Remaining invoice quota |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `machine_id` | VARCHAR(255) | NOT NULL | Hardware UUID |
| `company_code` | VARCHAR(10) | NOT NULL | Redundant for fast lookup |
| `license_code_hash` | VARCHAR(64) | NOT NULL | HMAC-SHA256 row signature |
| `is_online_active` | BOOLEAN | DEFAULT FALSE | Cloud subscription status |
| `online_start_date` | DATE | nullable | |
| `online_expiry_date` | DATE | nullable | |
| `last_checkin` | TIMESTAMPTZ | auto_now | Updated on every device ping |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

**Signature Formula**:
```
license_code_hash = HMAC-SHA256(
    expiry_date + invoices_balance + machine_id + product_id + is_active,
    SecretKey
)
```

> [!CAUTION]
> Any direct SQL UPDATE to `invoices_balance`, `expiry_date`, or `is_active` without recalculating `license_code_hash` will be detected by the validation middleware and will trigger `SET is_active = FALSE`.

---

### 2.17 UsedLicense (`used_license`)

**Table**: `used_license`  
**Description**: Registry of consumed activation codes — prevents replay attacks.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `code_hash` | VARCHAR(64) | UNIQUE NOT NULL | SHA-256 of raw license code |
| `used_at` | TIMESTAMPTZ | auto | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |

---

### 2.18 LicenseHistory (`license_history`)

**Table**: `license_history`  
**Description**: Append-only audit log of all licensing operations.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `machine_id` | VARCHAR(255) | NOT NULL | |
| `product_name` | VARCHAR(100) | NOT NULL | |
| `operation_type` | VARCHAR(50) | NOT NULL | e.g., `ACTIVATE`, `RENEW`, `REVOKE` |
| `start_date` | DATE | nullable | |
| `end_date` | DATE | nullable | |
| `added_balance` | INTEGER | DEFAULT 0 | Invoices added in this operation |
| `archived_at` | TIMESTAMPTZ | auto | |
| `status` | VARCHAR(50) | NOT NULL | `SUCCESS`, `FAILED`, etc. |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |

---

### 2.19 PendingExternalReceipt (`pending_external_receipt`)

**Table**: `pending_external_receipt`  
**Description**: Temporary staging table for external receipts awaiting desktop processing.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID PK | | |
| `tenant` | UUID FK → tenant | ON DELETE CASCADE | |
| `branch` | UUID FK → branch | ON DELETE CASCADE | |
| `batch_id` | VARCHAR(100) | NOT NULL | Groups related external receipts |
| `source` | VARCHAR(20) | CHECK IN (`CLOUD`, `USB`, `FILE`) | Origin of data |
| `payload` | JSONB | NOT NULL | Raw receipt data |
| `is_processed` | BOOLEAN | DEFAULT FALSE | |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | auto | |

---

## 3. Serializer Reference

| Serializer | Model | Nested Fields | Notes |
|-----------|-------|---------------|-------|
| `TenantSerializer` | Tenant | — | |
| `CloudUserSerializer` | CloudUser | — | `password_hash` write-only |
| `BranchSerializer` | Branch | — | |
| `SalespersonSerializer` | Salesperson | — | |
| `InventoryItemSerializer` | InventoryItem | — | Adds `current_stock` computed field |
| `CommissionHistorySerializer` | CommissionHistory | — | |
| `InventoryAdjustmentSerializer` | InventoryAdjustment | — | |
| `SupplierSerializer` | Supplier | — | |
| `PurchaseInvoiceSerializer` | PurchaseInvoice | `items` (write) | Creates nested `PurchaseInvoiceItem` on POST |
| `PurchaseInvoiceItemSerializer` | PurchaseInvoiceItem | — | |
| `ReceiptSerializer` | Receipt | `sale_items`, `installment_payments` | Generates hash, deducts license balance atomically |
| `SaleItemSerializer` | SaleItem | — | Accepts alias `inventory_item_id` |
| `InstallmentPaymentSerializer` | InstallmentPayment | — | |
| `ExpenseSerializer` | Expense | — | |
| `CompanySettingSerializer` | CompanySetting | — | |
| `ClientLicenseSerializer` | ClientLicense | — | `license_code_hash` read-only |
| `UsedLicenseSerializer` | UsedLicense | — | |
| `LicenseHistorySerializer` | LicenseHistory | — | |
| `PendingExternalReceiptSerializer` | PendingExternalReceipt | — | |

### Tenant Injection Pattern

Every serializer exposes `tenant_id` as a **read-only** computed field. The actual `tenant` object is injected by the view through serializer context:

```python
# In views.py
def get_serializer_context(self):
    context = super().get_serializer_context()
    context["tenant"] = self._get_tenant()  # resolved from header/JWT
    return context

# In SoftDeleteModelViewSet
def perform_create(self, serializer):
    serializer.save(tenant=context["tenant"])
```

---

## 4. ViewSet & Endpoint Reference

### 4.1 Standard CRUD ViewSets

All standard viewsets inherit from `TenantFromRequestMixin + SoftDeleteModelViewSet`:
- Querysets are **automatically scoped** to the active tenant.
- `destroy()` performs **soft-delete** (`is_deleted=True`) instead of `DELETE`.

| ViewSet | Base URL | Filters |
|---------|----------|---------|
| `TenantViewSet` | `/api/v1/tenants/` | — (admin only) |
| `CloudUserViewSet` | `/api/v1/cloud-users/` | — |
| `BranchViewSet` | `/api/v1/branches/` | — |
| `SalespersonViewSet` | `/api/v1/salespeople/` | — |
| `InventoryItemViewSet` | `/api/v1/inventory/` | `?branch_id=` `?month=` `?year=` |
| `CommissionHistoryViewSet` | `/api/v1/commission-history/` | `?item_id=` |
| `InventoryAdjustmentViewSet` | `/api/v1/inventory-adjustments/` | — |
| `SupplierViewSet` | `/api/v1/suppliers/` | — |
| `PurchaseInvoiceViewSet` | `/api/v1/purchase-invoices/` | — |
| `PurchaseInvoiceItemViewSet` | `/api/v1/purchase-invoice-items/` | — |
| `ReceiptViewSet` | `/api/v1/receipts/` | `?branch_id=` `?salesperson_id=` `?is_cash_sale=` |
| `SaleItemViewSet` | `/api/v1/sale-items/` | — |
| `InstallmentPaymentViewSet` | `/api/v1/installment-payments/` | — |
| `ExpenseViewSet` | `/api/v1/expenses/` | `?branch_id=` `?year=` `?month=` |
| `CompanySettingViewSet` | `/api/v1/company-settings/` | — |
| `ClientLicenseViewSet` | `/api/v1/client-licenses/` | — |
| `UsedLicenseViewSet` | `/api/v1/used-licenses/` | — |
| `LicenseHistoryViewSet` | `/api/v1/license-history/` | — |
| `PendingExternalReceiptViewSet` | `/api/v1/pending-external-receipts/` | — |

### 4.2 Custom Actions on InventoryItemViewSet

| Action | Method | URL | Description |
|--------|--------|-----|-------------|
| `safe_available_qty` | GET | `/api/v1/inventory/{pk}/stock/` | Pessimistic minimum stock projection |
| `ledger` | GET | `/api/v1/inventory/{pk}/ledger/` | Full stock timeline + monthly summary + profit metrics |

### 4.3 Special API Views

| View | Method | URL | Description |
|------|--------|-----|-------------|
| `ViewerAuthView` | POST | `/api/v1/auth/viewer/` | Authenticate cloud user; returns machine_id and role |
| `SyncPushView` | POST | `/api/v1/sync/push/` | Atomic ingestion of local device payload |
| `SyncPullView` | GET/POST | `/api/v1/sync/pull/` | Fetch updates since `last_sync` with SQLite field translation |
| `ConfirmReceiptsView` | POST | `/api/v1/sync/confirm-receipts/` | Master POS marks salesperson receipts as confirmed |
| `LicenseStatusView` | GET | `/api/v1/license/status/` | Current balance and expiry |
| `LicenseActivateView` | POST | `/api/v1/license/activate/` | Validate and activate a license code |

---

## 5. SQLite ↔ PostgreSQL Field Translation Layer

Per `api_contract.md §3`, the sync endpoints translate field names automatically:

### Inventory Items

| Django/PostgreSQL Field | SQLite Field | Direction |
|------------------------|--------------|-----------|
| `local_id` | `id` | push: client sends `id` → stored as `local_id` |
| `initial_quantity` | `quantity` | |
| `initial_purchase_price` | `purchase_price` | |
| `initial_commission_amount` | `commission` | |
| `created_at_local` | `created_at` | |

### Receipts

| Django/PostgreSQL Field | SQLite Field | Direction |
|------------------------|--------------|-----------|
| `local_id` | `id` | |
| `phone_number` | `phone_number` | stored identically |
| `address` | `address` | stored identically |
| `area` | `area` | stored identically |
| `created_at_local` | `created_at` | |

---

## 6. Managers

| Manager | Class | Description |
|---------|-------|-------------|
| `objects` | `ActiveManager` | Default — filters `is_deleted=False` automatically |
| `all_objects` | `AllObjectsManager` | Unfiltered — use only for admin/migration purposes |

> [!WARNING]
> Always use `Model.all_objects` when checking for soft-deleted records (e.g., idempotency checks in sync push). Using `Model.objects` will silently miss deleted records and may create unintended duplicates.

---

## 7. Database Indexes Created

All indexes are **partial indexes** omitting deleted records per schema §1.2:

```sql
-- Tenant
CREATE INDEX idx_tenant_active ON tenant(id) WHERE is_deleted = FALSE;

-- Users & Branches
CREATE INDEX idx_cloud_user_tenant ON cloud_user(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_branch_tenant ON branch(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_salesperson_tenant ON salesperson(tenant_id) WHERE is_deleted = FALSE;

-- Inventory
CREATE INDEX idx_inventory_item_tenant_branch ON inventory_item(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_commission_history_item ON commission_history(inventory_item_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_inventory_adjustment_item ON inventory_adjustment(inventory_item_id) WHERE is_deleted = FALSE;

-- Procurement
CREATE INDEX idx_supplier_tenant ON supplier(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_purchase_invoice_tenant_branch ON purchase_invoice(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_purchase_invoice_item_invoice ON purchase_invoice_item(purchase_invoice_id) WHERE is_deleted = FALSE;

-- Sales
CREATE INDEX idx_receipt_tenant_branch ON receipt(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_receipt_hash ON receipt(receipt_hash) WHERE is_deleted = FALSE;
CREATE INDEX idx_sale_item_receipt ON sale_item(receipt_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_installment_payment_receipt ON installment_payment(receipt_id) WHERE is_deleted = FALSE;

-- Expenses
CREATE INDEX idx_expense_tenant_branch ON expense(tenant_id, branch_id) WHERE is_deleted = FALSE;

-- Licensing
CREATE INDEX idx_client_license_tenant ON client_license(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_client_license_hash ON client_license(license_code_hash) WHERE is_deleted = FALSE;
CREATE INDEX idx_used_license_hash ON used_license(code_hash) WHERE is_deleted = FALSE;
```

> [!TIP]
> Partial indexes must be created via `RunSQL` in Django migrations since `Meta.indexes` does not support `WHERE` clauses natively. Add them to the initial migration's `operations` list.

---

## 8. Migration Notes

After applying these model changes, the following steps are required:

1. **Generate migrations**:
   ```powershell
   python manage.py makemigrations api
   ```

2. **Apply migrations**:
   ```powershell
   python manage.py migrate
   ```

3. **Add partial indexes** (via RunSQL in migration):
   ```python
   from django.db import migrations

   class Migration(migrations.Migration):
       operations = [
           migrations.RunSQL(
               "CREATE INDEX idx_receipt_tenant_branch ON receipt(tenant_id, branch_id) WHERE is_deleted = FALSE;",
               "DROP INDEX IF EXISTS idx_receipt_tenant_branch;"
           ),
           # ... repeat for all partial indexes listed in §7
       ]
   ```

4. **Enable PostgreSQL RLS** (production only, per schema §1.1):
   ```sql
   ALTER TABLE receipt ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_receipt_isolation ON receipt
       USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
   ```

---

## 9. Legacy Items

| Item | Status | Notes |
|------|--------|-------|
| `ActionLog` model | ⚠️ Legacy — not in approved schema | Kept to avoid breaking existing migrations. Will be removed in a future sprint. |
| `ActionLogSerializer` | ⚠️ Legacy | Read-only serializer maintained alongside the model. |
| `ActionLogViewSet` | ⚠️ Legacy | HTTP GET only. |

---

## 10. Changes vs Previous Version

| Category | Previous State | New State |
|----------|---------------|-----------|
| Primary Keys | Auto-integer | UUID everywhere |
| Tenant isolation | None | `tenant` FK on every model + mixin enforcement |
| Soft deletes | Not present | `is_deleted` + `ActiveManager` on every model |
| Financial fields | `PositiveIntegerField` | `DecimalField(12,2)` |
| `InstallmentPayment` | `payment_month/year` fields | `payment_date` (DATE field, stores 25th rule) |
| `Receipt` | Missing `local_id`, `client_uuid`, `products_text`, `is_confirmed`, `created_at_local` | All added per schema |
| `Expense` | Not present | Full model added |
| `CompanySetting` | Single-tenant, no UUID PK | Multi-tenant with UUID PK and `is_cloud_viewer` |
| `ClientLicense` | Missing `tenant`, `company_code`, `is_online_active`, `online_start/expiry_date`, `last_checkin` | All added per schema |
| `UsedLicense` | Missing `tenant`, `is_deleted` | Both added |
| `LicenseHistory` | Missing `tenant`, `machine_id`, `start_date`, `end_date`, `status`, `is_deleted` | All added per schema |
| `PendingExternalReceipt` | Missing `tenant`, `branch`, `source`, `is_deleted` | All added per schema |
| New models | — | `Tenant`, `CloudUser` added |
| Serializers | Flat, no tenant injection | Tenant-aware, nested writable |
| Views | No tenant filtering | Full tenant isolation via mixin |
| Soft-delete in views | Hard `DELETE` | `is_deleted=True` override |
