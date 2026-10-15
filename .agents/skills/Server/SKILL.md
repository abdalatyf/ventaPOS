---
name: ventapos-server
description: Complete technical documentation of the VentaPOS Server subsystem, including database schema, API contracts, routing, configuration, and business rules, fully verified against the source code.
---

# VentaPOS Server Subsystem - Comprehensive Technical Documentation

This document serves as the absolute, verified technical reference for the VentaPOS Server subsystem. Every detail within this document has been audited and verified against the actual Django implementation in the source codebase.

---

## 1. Database Schema

All database models for the VentaPOS Server subsystem are defined in `sync_api/models.py` (absolute path: `d:\Projects\VentaPOS\Server\sync_api\models.py`).

### 1.1 ServerLicense (Lines 7 - 18)
*   **machine_id** (`CharField`, `max_length=255`, `unique=True`): Hardware unique signature identifier for the master machine.
*   **company_code** (`CharField`, `max_length=4`, `unique=True`, `null=True`, `blank=True`): The **4-digit Company Code system** used to bind desktop/mobile/viewer clients to the master machine.
*   **client_name** (`CharField`, `max_length=150`, `blank=True`): Name of the client entity.
*   **is_active** (`BooleanField`, `default=True`): Status of the general client license.
*   **is_online_active** (`BooleanField`, `default=False`): Controls whether online syncing functionality is enabled.
*   **online_expiry_date** (`DateField`, `null=True`, `blank=True`): Expiration date for the online sync module subscription.
*   **created_at** (`DateTimeField`, `auto_now_add=True`): Record creation timestamp.
*   **last_sync_at** (`DateTimeField`, `null=True`, `blank=True`): Timestamp tracking when the client last synchronized data.

### 1.2 ServerCompanySetting (Lines 25 - 42)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Machine ID of origin.
*   **local_id** (`IntegerField`, `default=1`): Local company settings row ID.
*   **name** (`CharField`, `max_length=100`): Corporate/Branch name.
*   **description** (`CharField`, `max_length=200`, `blank=True`, `null=True`): Description/Slogan.
*   **phone1** (`CharField`, `max_length=20`): Main contact number.
*   **phone2** (`CharField`, `max_length=20`, `blank=True`, `null=True`): Alternative contact number.
*   **footer_text** (`CharField`, `max_length=250`, `blank=True`, `null=True`): Receipt footer note.
*   **synced_at** (`DateTimeField`, `auto_now=True`): Time of synchronization.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 41).

### 1.3 ServerBranch (Lines 44 - 52)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local branch ID.
*   **name** (`CharField`, `max_length=150`): Branch name.
*   **synced_at** (`DateTimeField`, `auto_now=True`): Time of synchronization.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 51).

### 1.4 ServerSalesperson (Lines 54 - 64)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local salesperson ID.
*   **local_branch_id** (`IntegerField`): Local branch ID reference.
*   **name** (`CharField`, `max_length=100`): Employee name.
*   **synced_at** (`DateTimeField`, `auto_now=True`): Time of synchronization.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 63).

### 1.5 ServerInventoryItem (Lines 66 - 83)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local product ID.
*   **local_branch_id** (`IntegerField`): Local branch ID reference.
*   **name** (`CharField`, `max_length=200`): Product name.
*   **quantity** (`PositiveIntegerField`, `default=0`): Product count/stock.
*   **purchase_price** (`DecimalField`, `max_digits=12`, `decimal_places=2`, `default=0`): Product unit cost price.
*   **salesperson_commission_amount** (`DecimalField`, `max_digits=12`, `decimal_places=2`, `default=0`): Commission amount awarded to salesperson.
*   **created_at_local** (`DateTimeField`, `null=True`, `blank=True`): Originating client-side timestamp.
*   **synced_at** (`DateTimeField`, `auto_now=True`): Time of synchronization.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 82).

### 1.6 ServerReceipt (Lines 87 - 117)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local transaction ID.
*   **receipt_hash** (`CharField`, `max_length=255`, `unique=True`, `null=True`, `blank=True`): Unique security hash of the receipt. Used as the sole ecosystem-wide key to prevent ID collisions.
*   **receipt_number** (`PositiveIntegerField`): Sequential printed receipt number.
*   **local_branch_id** (`IntegerField`): Local branch ID reference.
*   **local_salesperson_id** (`IntegerField`, `null=True`, `blank=True`): Local salesperson ID.
*   **customer_name** (`CharField`, `max_length=200`, `blank=True`): Client name.
*   **phone_number** (`CharField`, `max_length=50`, `blank=True`): Client phone.
*   **address** (`CharField`, `max_length=255`, `blank=True`): Client address.
*   **area** (`CharField`, `max_length=150`, `blank=True`): Regional area.
*   **total_amount** (`DecimalField`, `max_digits=12`, `decimal_places=2`, `default=0`): Full sales amount.
*   **down_payment** (`DecimalField`, `max_digits=12`, `decimal_places=2`, `default=0`): Cash down payment.
*   **installment_system** (`CharField`, `max_length=255`, `blank=True`): Installment details description.
*   **sale_year** (`IntegerField`): Year of sale.
*   **sale_month** (`IntegerField`): Month of sale.
*   **is_cash_sale** (`BooleanField`, `default=False`): Cash-only transaction marker.
*   **products_text** (`TextField`, `blank=True`, `null=True`): Serialized raw list of purchased items.
*   **is_confirmed** (`BooleanField`, `default=False`): True if reviewed/pulled by Master machine.
*   **synced_at** (`DateTimeField`, `auto_now_add=True`): Receipt synchronization time.
*   **created_at_local** (`DateTimeField`, `null=True`, `blank=True`): Transaction timestamp on the client POS.
*   **Constraints**: The legacy `unique_together = ('source_machine_id', 'local_id')` constraint has been completely **removed** to prevent mobile device ID collisions. Uniqueness is enforced solely via `receipt_hash`.
*   **Ordering**: `ordering = ['-created_at_local']` (Line 116).

### 1.7 ServerSaleItem (Lines 121 - 128)
*   **receipt** (`ForeignKey` to `ServerReceipt`, `related_name='items'`, `on_delete=models.CASCADE`): Link to parent receipt.
*   **local_product_id** (`IntegerField`): ID of product on local machine.
*   **product_name_snapshot** (`CharField`, `max_length=255`): Name of product at time of sale.
*   **quantity** (`PositiveIntegerField`): Quantity sold.
*   **unit_price** (`DecimalField`, `max_digits=12`, `decimal_places=2`): Sold price per item.

### 1.8 ServerInstallmentPayment (Lines 132 - 136)
*   **receipt** (`ForeignKey` to `ServerReceipt`, `related_name='payments'`, `on_delete=models.CASCADE`): Link to parent receipt.
*   **payment_date** (`DateField`): Date of payment.
*   **amount** (`DecimalField`, `max_digits=12`, `decimal_places=2`): Payoff amount.

### 1.9 ServerExpense (Lines 140 - 155)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local expense ID.
*   **local_branch_id** (`IntegerField`): Local branch reference.
*   **amount** (`DecimalField`, `max_digits=12`, `decimal_places=2`): Total expense value.
*   **description** (`CharField`, `max_length=255`): Description details.
*   **expense_year** (`IntegerField`): Financial logging year.
*   **expense_month** (`IntegerField`): Financial logging month.
*   **created_at_local** (`DateTimeField`, `null=True`, `blank=True`): Local logging time.
*   **synced_at** (`DateTimeField`, `auto_now_add=True`): Synchronized timestamp.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 154).

### 1.10 ServerStockTransaction (Lines 159 - 174)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Originating machine identifier.
*   **local_id** (`IntegerField`): Local transaction item ID.
*   **local_product_id** (`IntegerField`): Local product reference.
*   **product_name_snapshot** (`CharField`, `max_length=255`, `blank=True`): Snapshot of name.
*   **transaction_type** (`CharField`, `max_length=50`): Type (e.g., RESTOCK, ADJUSTMENT, SALE).
*   **quantity** (`IntegerField`): Count quantity change.
*   **created_at_local** (`DateTimeField`, `null=True`, `blank=True`): Local transaction time.
*   **synced_at** (`DateTimeField`, `auto_now_add=True`): Server synchronization time.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 173).

### 1.11 MobileProvisionToken (Lines 178 - 185)
*   **token** (`CharField`, `max_length=255`, `unique=True`, `default=uuid.uuid4`): Secure random token string.
*   **payload** (`JSONField`): Provision settings snapshot (includes database configurations).
*   **created_at** (`DateTimeField`, `auto_now_add=True`): Creation timestamp.

### 1.12 ServerCloudUser (Lines 189 - 203)
*   **source_machine_id** (`CharField`, `max_length=255`, `db_index=True`): Binded company/master machine identifier.
*   **local_id** (`IntegerField`): Local employee database index.
*   **username** (`CharField`, `max_length=150`): Login username.
*   **password_hash** (`CharField`, `max_length=255`): Password crypt hash.
*   **role** (`CharField`, `max_length=50`, `default='VIEWER'`): Permissions boundary ('VIEWER', 'CASHIER').
*   **is_active** (`BooleanField`, `default=True`): Active account status flag.
*   **synced_at** (`DateTimeField`, `auto_now=True`): Synced timestamp.
*   **Constraints**: `unique_together = ('source_machine_id', 'local_id')` (Line 201).

---

## 2. Routing & Endpoints

Server routes map to standard view classes in `sync_api/views.py` (absolute path: `d:\Projects\VentaPOS\Server\sync_api\views.py`).

### 2.1 URL Routing Configuration
*   **Root Router (`server_backend/urls.py`)**:
    *   `admin/` -> `admin.site.urls` (Standard Django Admin) — Line 5.
    *   `/` -> Includes sub-router `sync_api.urls` — Line 7.
*   **Sub-Router (`sync_api/urls.py`)**:
    *   `api/v1/sync/push/` -> `SyncIngestView.as_view()` — Line 6.
    *   `api/v1/sync/mobile-push/` -> `MobilePushIngestView.as_view()` — Line 7.
    *   `api/v1/sync/pending-receipts/` -> `PendingReceiptsView.as_view()` — Line 8.
    *   `api/v1/sync/confirm-receipts/` -> `ConfirmReceiptsView.as_view()` — Line 9.
    *   `api/v1/sync/upload-setup/` -> `UploadSetupView.as_view()` — Line 12.
    *   `api/v1/sync/download-setup/` -> `DownloadSetupView.as_view()` — Line 13.
    *   `api/v1/auth/viewer/` -> `ViewerAuthView.as_view()` — Line 16.
    *   `api/v1/sync/viewer/download/` -> `ViewerDownloadSyncView.as_view()` — Line 17.
    *   `api/v1/dashboard/manager/` -> `ManagerDashboardView.as_view()` — (Manager Dashboard endpoints).

---

## 3. API Contract (JSON Payload Specifications)

*Note: All Mobile Sync APIs have been refactored according to the new `api_contract.md` specifications.*

### 3.1 `SyncIngestView` (Primary Sync Push)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/sync/push/`
*   **Request Payload**:
    ```json
    {
      "machine_id": "string",
      "payload": {
        "company_settings": {
          "name": "string",
          "description": "string",
          "phone1": "string",
          "phone2": "string",
          "footer_text": "string"
        },
        "branches": [{"id": 1, "name": "string"}],
        "salespeople": [{"id": 1, "branch_id": 1, "name": "string"}],
        "inventory": [{
          "id": 1,
          "branch_id": 1,
          "name": "string",
          "quantity": 10,
          "purchase_price": "50.00",
          "commission": "5.00",
          "created_at": "YYYY-MM-DDTHH:MM:SSZ"
        }],
        "cloud_users": [{
          "id": 1,
          "username": "string",
          "password_hash": "string",
          "role": "VIEWER",
          "is_active": true
        }],
        "receipts": [{
          "receipt_hash": "string",
          "id": 1,
          "receipt_number": 1001,
          "branch_id": 1,
          "salesperson_id": 1,
          "customer_name": "string",
          "phone_number": "string",
          "address": "string",
          "area": "string",
          "total_amount": "150.00",
          "down_payment": "50.00",
          "installment_system": "string",
          "sale_year": 2026,
          "sale_month": 6,
          "is_cash_sale": false,
          "created_at": "YYYY-MM-DDTHH:MM:SSZ",
          "items": [{
            "product_id": 1,
            "product_name": "string",
            "quantity": 2,
            "price": "50.00"
          }],
          "payments": [{
            "payment_date": "YYYY-MM-DD",
            "amount": "50.00"
          }]
        }],
        "expenses": [{
          "id": 1,
          "branch_id": 1,
          "amount": "20.00",
          "description": "string",
          "expense_year": 2026,
          "expense_month": 6,
          "created_at": "YYYY-MM-DDTHH:MM:SSZ"
        }],
        "stock_transactions": [{
          "id": 1,
          "product_id": 1,
          "product_name": "string",
          "transaction_type": "RESTOCK",
          "quantity": 10,
          "created_at": "YYYY-MM-DDTHH:MM:SSZ"
        }]
      }
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "message": "Data synced successfully. Receipts processed: 1",
      "global_price_updates": [],
      "config_changes": {}
    }
    ```

### 3.2 `MobilePushIngestView` (Mobile Device Push Ingestion)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/sync/mobile-push/`
*   **Request Payload**:
    ```json
    {
      "machine_id": "string",
      "payload": {
        "receipts": [{
          "receipt_hash": "string",
          "local_id": 1,
          "receipt_number": 5001,
          "branch_id": 1,
          "total_amount": 250.00,
          "sale_year": 2026,
          "sale_month": 6,
          "items": [{
            "product_id": 1,
            "quantity": 1,
            "price": 250.00
          }]
        }]
      }
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "message": "Cloud Viewer push data received and staged."
    }
    ```

### 3.3 `PendingReceiptsView` (Read Unconfirmed Receipts)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/sync/pending-receipts/?machine_id=string`
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "receipts": [{
        "receipt_hash": "string",
        "local_id": 1,
        "receipt_number": 5001,
        "local_branch_id": 1,
        "total_amount": "250.00",
        "items": [{
          "product_id": 1,
          "quantity": 1,
          "unit_price": "250.00"
        }]
      }]
    }
    ```

### 3.4 `ConfirmReceiptsView` (Confirm Receipt Ingestion)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/sync/confirm-receipts/`
*   **Request Payload**:
    ```json
    {
      "machine_id": "string",
      "receipt_hashes": ["string"]
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "message": "Receipts confirmed successfully."
    }
    ```

### 3.5 `UploadSetupView` (Generate Remote Setup Token)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/sync/upload-setup/`
*   **Request Payload**:
    ```json
    {
      "machine_id": "string",
      "payload": {
        "database_settings": "JSON formatted settings payload..."
      }
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "token": "UUID-token-string"
    }
    ```

### 3.6 `DownloadSetupView` (One-Time Remote Configuration Download)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/sync/download-setup/?token=UUID-token-string`
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "payload": {
        "database_settings": "JSON formatted settings payload..."
      }
    }
    ```

### 3.7 `ViewerAuthView` (Cloud Viewer Authentication)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/auth/viewer/`
*   **Request Payload**:
    ```json
    {
      "company_code": "string",
      "username": "string",
      "password_hash": "string"
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "master_machine_id": "string",
      "user": {
        "username": "string",
        "role": "VIEWER",
        "local_id": 1
      }
    }
    ```

### 3.8 `ViewerDownloadSyncView` (Viewer Core Sync Download)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/sync/viewer/download/`
*   **Request Payload**:
    ```json
    {
      "company_code": "string"
    }
    ```
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "products": [{
        "name": "string",
        "initial_quantity": 10,
        "initial_purchase_price": 50,
        "initial_commission_amount": 5,
        "initial_month": 6,
        "initial_year": 2026
      }],
      "branches": [{"local_id": 1, "name": "string"}],
      "salespersons": [{"local_id": 1, "name": "string"}]
    }
    ```

### 3.9 `ManagerDashboardView` (Manager Analytics & Summaries)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/dashboard/manager/?company_code=1234`
*   **Response Payload (Success - 200 OK)**:
    ```json
    {
      "status": "success",
      "data": {
        "total_sales": "15000.00",
        "active_devices": 3,
        "pending_syncs": 5,
        "recent_receipts": []
      }
    }
    ```

---

## 4. Core Business Logic & Security Workflows

### 4.1 Sync Ingestion Flow (Atomicity & Overwrite Strategies)
*   **Atomicity**: Ingestion inside `SyncIngestView` uses a Django transaction block: `with transaction.atomic():` (`sync_api/views.py:42`).
*   **Reference Data Upsert Mode**: Company settings, branches, salespeople, inventory items, and cloud users are synchronized via Django's `update_or_create` (`sync_api/views.py:51-95` & `182-192`), mapping on `source_machine_id` and `local_id`.
*   **Child Entity Overwrite Strategy**: For each ingested receipt, existing lines and payments are completely removed before the new ones are saved:
    *   `receipt_obj.items.all().delete()` (Line 131).
    *   `receipt_obj.payments.all().delete()` (Line 132).

### 4.2 Security Gatekeeper Pattern (Zero-Trust)
*   **Zero-Trust Authorization**: Endpoints (`SyncIngestView`, `MobilePushIngestView`, `PendingReceiptsView`, `ConfirmReceiptsView`, `UploadSetupView`, and `ViewerAuthView`) validate the client's `machine_id` against a valid, active license row in `ServerLicense`:
    1.  Is license active? (`is_active=True`)
    2.  Is online synchronization allowed? (`is_online_active=True`)
    3.  Has the subscription expired? (`online_expiry_date >= current_date`)
*   **Mobile Push Enforcement**: The mobile ingestion endpoint `/api/v1/sync/mobile-push/` (`MobilePushIngestView`) implements these exact checks to prevent unauthorized pushes (`sync_api/views.py:210-221`).

### 4.3 Temporary Remote Provisioning
*   **One-Time Configuration Setup**: `DownloadSetupView` enables initial branch desktop installation setup without manual database copy. A 10-minute validity window is backed by immediate database token deletion upon request to prevent token hijacking:
    *   `provision.delete()` (Line 391).

---

## 5. Configuration Settings & DevOps

### 5.1 Settings File Citations (`server_backend/settings.py`)
*   **Entry Points**: `manage.py`, `server_backend/wsgi.py` (Line 75), and `server_backend/asgi.py`.
*   **Debug Mode**: `DEBUG = True` (Line 26).
*   **Allowed Hosts**: `ALLOWED_HOSTS = ['*']` (Line 29). Allows tunneling tools like Ngrok.
*   **CSRF Trust Origins**: `CSRF_TRUSTED_ORIGINS = ['https://jargonal-colourationally-buddy.ngrok-free.dev']` (Lines 32 - 34). Allows requests from secure tunnels.
*   **Database Engine**: SQLite database engine `db.sqlite3` (`BASE_DIR / 'db.sqlite3'`) (Lines 81 - 86).
*   **Timezone**: `TIME_ZONE = 'UTC'` and `USE_TZ = True` (Lines 113 & 117).
*   **Static Files**: `STATIC_URL = 'static/'` (Line 123).

### 5.2 Build Script (`build.sh`)
*   Provides automated script pipelines for cloud deploy (e.g. Render/Heroku):
    1.  `pip install -r requirements.txt` (Line 5).
    2.  `python manage.py collectstatic --no-input` (Line 6).
    3.  `python manage.py migrate` (Line 7).

---

## 6. Django Admin & UI Architecture

### 6.1 Admin Model Registrations (`sync_api/admin.py`)
*   The admin dashboard is configured to prevent tampering with records:
    *   **ServerLicense**: `machine_id` is marked `readonly_fields` (Line 14).
    *   **ServerReceipt**: Historical financial fields (`source_machine_id`, `local_id`, `receipt_number`, `total_amount`, `created_at_local`) are read-only (Line 65).
    *   **ServerSaleItem** & **ServerInstallmentPayment**: Inlines with completely read-only fields to preserve historic ledger integrity (Lines 49 & 55).
*   **Unregistered Utility Models**:
    *   `MobileProvisionToken` (provisioning token utility, `models.py:178`) is omitted from `admin.py`.
    *   `ServerCloudUser` (system cloud user credentials, `models.py:189`) is unregistered in `admin.py` to keep user credentials secure from standard administrative modifications, although listed in the Jazzmin search configuration (`settings.py:131`).

---

## 7. Quality Audit & Architectural Resolutions

A total of four core discrepancies were resolved in collaboration with the Product Manager:

### 7.1 Product Schema Convergence
*   **Audit Observation**: The viewer sync download endpoint (`ViewerDownloadSyncView`) attempted to import a non-existent `ServerProduct` model and query invalid fields (`barcode`, `selling_price`, `cost_price`, `minimum_stock`).
*   **Impact**: Querying the endpoint crashed with an `ImportError` and `AttributeError`.
*   **Resolution**: The `ServerProduct` model was confirmed as a legacy hallucination. The view was refactored to query `ServerInventoryItem` (the correct model). Non-existent fields were stripped. The serialized JSON payload is populated with exactly `name`, `initial_quantity`, `initial_purchase_price`, `initial_commission_amount`, `initial_month`, and `initial_year`.

### 7.2 Desktop Client Schema Mismatch
*   **Audit Observation**: The desktop client's sync view (`initial_sync_views.py`) attempted to write non-existent fields (`barcode`, `current_purchase_price`, `current_quantity`) on the local `InventoryItem` model, and omitted the mandatory `branch` ForeignKey reference during creation.
*   **Impact**: Initial desktop sync failed with database `IntegrityError` (NOT NULL constraint failed).
*   **Resolution**: The client-side logic was refactored to populate only genuine fields (`name`, `initial_quantity`, `initial_purchase_price`, `initial_commission_amount`, `initial_month`, `initial_year`). It queries the first downloaded branch (Main Branch) and assigns it to all `InventoryItem` and `Salesperson` records.

### 7.3 Mobile Receipt ID Collision
*   **Audit Observation**: The `ServerReceipt` table had a unique constraint on `('source_machine_id', 'local_id')`.
*   **Impact**: When multiple mobile cashiers generated sequential receipt numbers under the same master `machine_id`, pushing transactions triggered database integrity collision crashes.
*   **Resolution**: The `unique_together` constraint on `('source_machine_id', 'local_id')` was completely removed from the `ServerReceipt` model's Meta options. Receipt uniqueness is now enforced solely via `receipt_hash` across the entire system.

### 7.4 Mobile Push License Verification
*   **Audit Observation**: The `/api/v1/sync/mobile-push/` endpoint (`MobilePushIngestView`) lacked security license validations.
*   **Impact**: Unlicensed devices could push arbitrary transactional data directly to the server.
*   **Resolution**: Strict Zero-Trust license status checks (verifying `is_active`, `is_online_active`, and expiration date) were integrated into `MobilePushIngestView` to ensure uniformity and high security across all sync entry points.
