# Target Database Schema — VentaPOS NextGen Rebuild
**Subsystem**: Database Schema Design (PostgreSQL Transition)  
**Status**: SINGLE SOURCE OF TRUTH (MANDATORY GATEWAY)

This document establishes the absolute Single Source of Truth for the PostgreSQL database schema of the VentaPOS NextGen Rebuild. It incorporates all requirements from the requirements specification (`requirements.md`) and the project scope (`PROJECT.md`).

---

## 1. Architectural Policies & Core Guidelines

### 1.1 Multi-Tenant Isolation
The rebuild transitions VentaPOS from a single-user SQLite setup to a unified, multi-tenant PostgreSQL system.
* **Tenant Root**: The `tenant` (الشركة) table serves as the base entity.
* **Foreign Keys**: Every tenant-owned table contains a `tenant_id UUID REFERENCES tenant(id)` column.
* **Query Constraints**: Every select, update, or delete query must filter by `tenant_id`. For example, composite unique constraints include `tenant_id` (e.g., username is unique per tenant: `UNIQUE (tenant_id, username)`).
* **Row-Level Security (RLS)**: PostgreSQL Row-Level Security must be enabled in production to isolate data:
  ```sql
  ALTER TABLE receipt ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_receipt_isolation ON receipt
      USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
  ```

### 1.2 Soft Deletes Policy
To preserve transactional history and auditability, permanent record deletion via SQL `DELETE` is prohibited.
* **Column Standard**: Every transactional table must support a soft delete flag: `is_deleted BOOLEAN NOT NULL DEFAULT FALSE`.
* **Execution**: Soft deletes update `is_deleted = TRUE`. Default queries and lookups must always filter `WHERE is_deleted = FALSE`.
* **Index Optimization**: All indexes are built as partial indexes omitting deleted records to maximize query performance:
  ```sql
  CREATE INDEX idx_receipt_active ON receipt(tenant_id, branch_id) WHERE is_deleted = FALSE;
  ```

### 1.3 Concurrency Control & Pessimistic Locks
To prevent race conditions during concurrent stock deductions or adjustments:
* **Rule**: Stock adjustments must run inside an atomic transaction utilizing pessimistic lock controls via PostgreSQL's `SELECT FOR UPDATE`.
* **Implementation Note (Python Django)**:
  ```python
  from django.db import transaction
  
  with transaction.atomic():
      # Acquire row-level pessimistic lock
      item = InventoryItem.objects.select_for_update().get(id=item_uuid, tenant_id=tenant_uuid)
      if item.quantity >= requested_qty:
          item.quantity -= requested_qty
          item.save()
      else:
          raise ValidationError("رصيد المخزن غير كافي")
  ```

### 1.4 Idempotency Policy (Duplicate Prevention)
* **Rule**: Synchronization payloads from mobile/viewer clients may be retried. The database prevents duplicate receipt creation by mapping a client-generated UUID token: `client_uuid UUID NOT NULL`.
* **Constraint**: A composite unique constraint on `(tenant_id, client_uuid)` ensures duplicates are rejected cleanly without throwing database collision exceptions.

### 1.5 Database Row Signatures & Tamper Checking
* **ClientLicense Row Integrity (`license_code_hash`)**:
  To prevent manual manipulation of licensing dates and balances (e.g., via direct database access or SQL updates), the `client_license` table contains a cryptographic signature column `license_code_hash`.
  * **Signature Formula**:
    $$\text{license\_code\_hash} = \text{HMAC-SHA256}(\text{expiry\_date} + \text{invoices\_balance} + \text{machine\_id} + \text{product\_id} + \text{is\_active}, \text{SecretKey})$$
  * **Validation**: Request validation middleware recalculates this signature for all active licenses. If a mismatch is detected, it triggers a direct SQL override command to disable the row:
    ```sql
    UPDATE client_license SET is_active = FALSE WHERE id = :id;
    ```
* **Receipt Unique Hash (`receipt_hash`)**:
  To prevent transaction collisions and manipulation of invoice values during cloud pushes, the `receipt` table must store a cryptographic hash `receipt_hash VARCHAR(255) UNIQUE NOT NULL`. This unique token is derived from receipt fields and validated via HMAC-SHA256.

---

## 2. Egyptian Market Terminology Mapping

Per the team guidelines, the schema annotations and UI terminology must adopt Egyptian retail and wholesale merchant terms ("لغة سوق مبسطة ومهنية"):

| DDL Table Name | Technical Entity | Classical Arabic | Egyptian Market Term (UI / Code Reference) |
| :--- | :--- | :--- | :--- |
| `tenant` | Tenant / Company | الشركة / المؤسسة | **الشركة** or **المؤسسة** |
| `cloud_user` | User Account | مستخدم النظام | **مستخدم السحابة** |
| `branch` | Branch / Warehouse | الفرع / المستودع | **المخزن** or **الفرع** |
| `salesperson` | Sales Representative | مندوب المبيعات | **المندوب** |
| `inventory_item` | Catalog Item | السلعة / المنتج | **البضاعة** or **الصنف** |
| `commission_history` | Agent Fee Rate | سجل المندبات | **سجل المندبات** or **العمولات** |
| `inventory_adjustment` | Adjustment Log | تسويات الجرد | **دفتر الجرد والتسويات** |
| `supplier` | Procurement Vendor | المورد | **المورد** or **الموردين** |
| `purchase_invoice` | Vendor Purchase | فاتورة توريد | **شراء بضاعة** or **مرتجع للمورد** |
| `receipt` | Sales Transaction | إيصال البيع / الفاتورة | **الفاتورة** or **الوصل** |
| `sale_item` | Sold Line Item | صنف المبيعات | **الأصناف المباعة** |
| `installment_payment` | Installment Due | دفعة مجدولة | **القسط** or **الأقساط** |
| `expense` | Operational Overhead | المصروفات العامة | **المصاريف** or **الخزنة** |
| `client_license` | Active Activation Profile| ترخيص التشغيل | **الترخيص** or **الكود** |

---

## 3. Data Type Standardization Rules

* **UUID**: Standardized for all primary keys, foreign keys, receipt identifiers, and licensing tokens to prevent local sequence collisions when merging data.
* **DECIMAL(12, 2)**: Used for all financial columns (currency, prices, totals, commissions, expenses) to ensure fixed-point arithmetic accuracy and prevent float rounding errors.
* **INTEGER**: Used for quantities, calendar months, calendar years, and sequential numbering offsets.
* **VARCHAR / TEXT**: Standardized string fields with appropriate size limits (e.g. `VARCHAR(255)`, `VARCHAR(64)` for hashes).
* **TIMESTAMP WITH TIME ZONE**: Standardized timezone-aware representation for timestamps, keeping storage globally aligned to UTC.

---

## 4. PostgreSQL DDL SQL Definition (Single Source of Truth)

```sql
-- PostgreSQL Target Database Schema for VentaPOS NextGen Rebuild
-- Absolute Single Source of Truth

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. Table: tenant (الشركة)
-- =============================================================================
CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tenant IS 'Root tenant organization representation (الشركة)';

-- =============================================================================
-- 2. Table: cloud_user (مستخدمي السحابة)
-- =============================================================================
CREATE TABLE cloud_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    username VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'CASHIER', 'VIEWER', 'BRANCH_MANAGER')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_username UNIQUE (tenant_id, username)
);

-- =============================================================================
-- 3. Table: branch (المخزن / الفرع)
-- =============================================================================
CREATE TABLE branch (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    local_id INTEGER NOT NULL CHECK (local_id >= 0),
    name VARCHAR(150) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_branch_local_id UNIQUE (tenant_id, local_id),
    CONSTRAINT uq_tenant_branch_name UNIQUE (tenant_id, name)
);

-- =============================================================================
-- 4. Table: salesperson (المندوب)
-- =============================================================================
CREATE TABLE salesperson (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    local_id INTEGER NOT NULL CHECK (local_id >= 0),
    name VARCHAR(100) NOT NULL,
    device_token UUID NOT NULL DEFAULT gen_random_uuid(),
    is_device_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_salesperson_local_id UNIQUE (tenant_id, local_id)
);

-- =============================================================================
-- 5. Table: inventory_item (البضاعة / الصنف)
-- =============================================================================
CREATE TABLE inventory_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    local_id INTEGER NOT NULL CHECK (local_id >= 0),
    name VARCHAR(200) NOT NULL,
    initial_quantity INTEGER NOT NULL DEFAULT 0 CHECK (initial_quantity >= 0),
    initial_purchase_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (initial_purchase_price >= 0.00),
    initial_commission_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (initial_commission_amount >= 0.00),
    initial_month INTEGER NOT NULL CHECK (initial_month BETWEEN 1 AND 12),
    initial_year INTEGER NOT NULL CHECK (initial_year >= 2025),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_item_local_id UNIQUE (tenant_id, local_id)
);

-- =============================================================================
-- 6. Table: commission_history (تاريخ عمولات المندوبين)
-- =============================================================================
CREATE TABLE commission_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES inventory_item(id) ON DELETE CASCADE,
    commission_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (commission_amount >= 0.00),
    activation_month INTEGER NOT NULL CHECK (activation_month BETWEEN 1 AND 12),
    activation_year INTEGER NOT NULL CHECK (activation_year >= 2025),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 7. Table: inventory_adjustment (جرد وتسويات البضاعة)
-- =============================================================================
CREATE TABLE inventory_adjustment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES inventory_item(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(20) NOT NULL CHECK (adjustment_type IN ('DEFICIT', 'SURPLUS')),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    reason VARCHAR(255),
    adjustment_month INTEGER NOT NULL CHECK (adjustment_month BETWEEN 1 AND 12),
    adjustment_year INTEGER NOT NULL CHECK (adjustment_year >= 2025),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 8. Table: supplier (الموردين)
-- =============================================================================
CREATE TABLE supplier (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_supplier_name UNIQUE (tenant_id, name)
);

-- =============================================================================
-- 9. Table: purchase_invoice (فاتورة الشراء / المرتجع)
-- =============================================================================
CREATE TABLE purchase_invoice (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES supplier(id) ON DELETE CASCADE,
    invoice_number INTEGER NOT NULL CHECK (invoice_number >= 0),
    invoice_type VARCHAR(20) NOT NULL CHECK (invoice_type IN ('PURCHASE', 'RETURN')),
    invoice_month INTEGER NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_year INTEGER NOT NULL CHECK (invoice_year >= 2025),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_branch_invoice_num_type UNIQUE (tenant_id, branch_id, invoice_number, invoice_type)
);

-- =============================================================================
-- 10. Table: purchase_invoice_item (أصناف فاتورة الشراء)
-- =============================================================================
CREATE TABLE purchase_invoice_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    purchase_invoice_id UUID NOT NULL REFERENCES purchase_invoice(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES inventory_item(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    purchase_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (purchase_price >= 0.00),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 11. Table: receipt (الفاتورة / الوصل)
-- =============================================================================
CREATE TABLE receipt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    salesperson_id UUID REFERENCES salesperson(id) ON DELETE SET NULL,
    local_id INTEGER NOT NULL CHECK (local_id >= 0),
    receipt_number INTEGER NOT NULL CHECK (receipt_number >= 0),
    client_uuid UUID NOT NULL,
    receipt_hash VARCHAR(255) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    phone_number VARCHAR(50),
    address VARCHAR(255),
    area VARCHAR(150),
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0.00),
    down_payment DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (down_payment >= 0.00),
    installment_system VARCHAR(255),
    sale_year INTEGER NOT NULL CHECK (sale_year >= 2025),
    sale_month INTEGER NOT NULL CHECK (sale_month BETWEEN 1 AND 12),
    is_cash_sale BOOLEAN NOT NULL DEFAULT FALSE,
    products_text TEXT,
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at_local TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_receipt_client_uuid UNIQUE (tenant_id, client_uuid)
);

-- =============================================================================
-- 12. Table: sale_item (أصناف الفاتورة المباعة)
-- =============================================================================
CREATE TABLE sale_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    receipt_id UUID NOT NULL REFERENCES receipt(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES inventory_item(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (unit_price >= 0.00),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 13. Table: installment_payment (دفعة القسط المجدول)
-- =============================================================================
CREATE TABLE installment_payment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    receipt_id UUID NOT NULL REFERENCES receipt(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (amount >= 0.00),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 14. Table: expense (دفتر المصاريف / الخزنة)
-- =============================================================================
CREATE TABLE expense (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 CHECK (amount >= 0.00),
    description VARCHAR(255) NOT NULL,
    expense_year INTEGER NOT NULL CHECK (expense_year >= 2025),
    expense_month INTEGER NOT NULL CHECK (expense_month BETWEEN 1 AND 12),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at_local TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 15. Table: company_setting (إعدادات الشركة / Singleton)
-- =============================================================================
CREATE TABLE company_setting (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    phone1 VARCHAR(20) NOT NULL,
    phone2 VARCHAR(20),
    footer_text VARCHAR(250),
    is_cloud_viewer BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_company_setting UNIQUE (tenant_id)
);

-- =============================================================================
-- 16. Table: client_license (ترخيص العميل وتأمين السجل)
-- =============================================================================
CREATE TABLE client_license (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL CHECK (product_id BETWEEN 1 AND 16),
    start_date DATE NOT NULL,
    expiry_date DATE,
    invoices_balance INTEGER NOT NULL DEFAULT 0 CHECK (invoices_balance >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    machine_id VARCHAR(255) NOT NULL,
    company_code VARCHAR(10) NOT NULL,
    license_code_hash VARCHAR(64) NOT NULL,
    is_online_active BOOLEAN NOT NULL DEFAULT FALSE,
    online_start_date DATE,
    online_expiry_date DATE,
    last_checkin TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 17. Table: used_license (منع تكرار تفعيل الأكواد)
-- =============================================================================
CREATE TABLE used_license (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    code_hash VARCHAR(64) UNIQUE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- 18. Table: license_history (أرشيف سجل التراخيص)
-- =============================================================================
CREATE TABLE license_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    machine_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    added_balance INTEGER NOT NULL DEFAULT 0,
    archived_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- 19. Table: pending_external_receipt (الوصلات الخارجية المستوردة المؤقتة)
-- =============================================================================
CREATE TABLE pending_external_receipt (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branch(id) ON DELETE CASCADE,
    batch_id VARCHAR(100) NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('CLOUD', 'USB', 'FILE')),
    payload JSONB NOT NULL,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Indexes for Tenant Isolation & Query Optimization (Partial Indexes)
-- =============================================================================

-- Tenant indexing & soft-delete optimization
CREATE INDEX idx_tenant_active ON tenant(id) WHERE is_deleted = FALSE;

-- Branch & User indexes
CREATE INDEX idx_cloud_user_tenant ON cloud_user(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_branch_tenant ON branch(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_salesperson_tenant ON salesperson(tenant_id) WHERE is_deleted = FALSE;

-- Inventory & Ledgers indexes
CREATE INDEX idx_inventory_item_tenant_branch ON inventory_item(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_commission_history_item ON commission_history(inventory_item_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_inventory_adjustment_item ON inventory_adjustment(inventory_item_id) WHERE is_deleted = FALSE;

-- Supplier & Procurements indexes
CREATE INDEX idx_supplier_tenant ON supplier(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_purchase_invoice_tenant_branch ON purchase_invoice(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_purchase_invoice_item_invoice ON purchase_invoice_item(purchase_invoice_id) WHERE is_deleted = FALSE;

-- Receipts & Installments indexes
CREATE INDEX idx_receipt_tenant_branch ON receipt(tenant_id, branch_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_receipt_hash ON receipt(receipt_hash) WHERE is_deleted = FALSE;
CREATE INDEX idx_sale_item_receipt ON sale_item(receipt_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_installment_payment_receipt ON installment_payment(receipt_id) WHERE is_deleted = FALSE;

-- Expense indexes
CREATE INDEX idx_expense_tenant_branch ON expense(tenant_id, branch_id) WHERE is_deleted = FALSE;

-- Licensing indexes
CREATE INDEX idx_client_license_tenant ON client_license(tenant_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_client_license_hash ON client_license(license_code_hash) WHERE is_deleted = FALSE;
CREATE INDEX idx_used_license_hash ON used_license(code_hash) WHERE is_deleted = FALSE;
