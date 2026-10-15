# Environment & Integration Analysis Report: VentaPOS NextGen POS Entry Testing

**Date**: 2026-07-04  
**Author**: Environment & Integration Explorer (`explorer_m1_3`)  
**Target Repository**: `d:\Projects\VentaPOS\VentaPOS_NextGen`

---

## 1. Executive Summary

This report presents a comprehensive investigation of the runtime environment, server startup procedures, active SQLite database state, seed data scripts, and available test runners for the **VentaPOS NextGen POS Entry Screen (`http://localhost:5173/pos`)**.

---

## 2. Server Execution Setup & Ports

| Subsystem | Launch Method | Default / Active Port | Environment Details |
|---|---|---|---|
| **Backend API (Development)** | `python backend/manage.py runserver 8000` (or `python manage.py runserver 8000` from `backend/`) | **8000** (`http://127.0.0.1:8000`) | Django 6.0.6 development server; handles REST API calls at `/api/` |
| **Backend Desktop Bundle** | `python main.py` | **Dynamic** (Selected via `get_free_port()`) | Waitress WSGI server (`threads=6`) + PyWebView desktop GUI window; decrypts `%APPDATA%\VentaPOS\business_data.enc` into a temporary runtime SQLite DB (`~sys_runtime_cache_v1.tmp`) |
| **Frontend Dev Server** | `npm run dev` (executes `vite`) from `frontend/` | **5173** (`http://localhost:5173/pos`) | Vite 8.1.0 SPA server; configured with proxy in `vite.config.js` forwarding `/api` -> `http://127.0.0.1:8000` |

### Key Observation on Port Integration:
- In development/testing mode for the Web POS UI (`http://localhost:5173/pos`), Vite forwards all `/api` requests to `http://127.0.0.1:8000`. Therefore, the backend **MUST** be launched using `python backend/manage.py runserver 8000` so that product search (`/api/v1/products/search/`), customer search (`/api/v1/customers/search/`), and receipt submission (`/api/v1/receipts/`) respond on port 8000.

---

## 3. Database Architecture & Current State

The system uses a multi-database router architecture defined in `backend/backend/settings.py` (`DATABASE_ROUTERS = ['api.db_router.SystemDBRouter']`).

### 3.1 Active Database Files

1. **Business Database (`default` alias)**:
   - **Path**: `d:\Projects\VentaPOS\VentaPOS_NextGen\backend\db\business_data.sqlite3`
   - **File Size**: ~405.5 KB
   - **Engine**: SQLite 3 (`django.db.backends.sqlite3`)
   - **Table Count**: 18 transactional tables (`tenant`, `branch`, `salesperson`, `inventory_item`, `receipt`, `sale_item`, `installment_payment`, `expense`, `company_setting`, `commission_history`, `inventory_adjustment`, `supplier`, `purchase_invoice`, `purchase_invoice_item`, `pending_external_receipt`, `cloud_user`, `authtoken_token`, `django_migrations`).

2. **System / License Database (`system` alias)**:
   - **Path**: `%APPDATA%\VentaPOS\system.sqlite3` (`C:\Users\Abdo\AppData\Roaming\VentaPOS\system.sqlite3`)
   - **Engine**: SQLite 3
   - **Table Count**: 19 tables (`client_license`, `used_license`, `license_history`, `api_clientlicense`, `authtoken_token`, `auth_user`, `auth_permission`, etc.).

### 3.2 Database Inspection Summary

| Model / Table | Table Name | Existing Row Count | Key Data Inspected |
|---|---|---|---|
| **Tenant** | `tenant` | 1 | ID: `703e4534-ae85-4820-a7ce-4346ef1bd0b6`, `company_code`: `"1234"`, `name`: `"Local Dev Company"`, `is_active`: `True` |
| **Branch** | `branch` | 1 | ID: `a89b7905-7621-4fc4-ac5c-3aef75ff0840`, `local_id`: `1`, `name`: `"الفرع الرئيسي"` |
| **Salesperson** | `salesperson` | 1 | ID: `7db091e1-c130-4fe3-9fa0-6fd59d2895bd`, `local_id`: `1`, `name`: `"Test Salesperson"` |
| **InventoryItem** | `inventory_item` | 11 (8 active) | e.g. Local ID `1` `"test2"`, Local ID `11` `"كبة"` (Initial Qty: 150, Purchase Price: 150.00, Commission: 150.00) |
| **Receipt** | `receipt` | 4 | Receipt #1 Cash (1000.00), #2 Cash (1000.00), #3 Cash (150.00), #4 Installment (150.00, Down Payment: 50.00) |
| **SaleItem** | `sale_item` | 4 | 4 items linked to Receipts 1–4 |
| **InstallmentPayment** | `installment_payment` | 2 | Linked to Receipt #4: Due `2026-08-25` (50.00 EGP), Due `2026-09-25` (50.00 EGP) |
| **ClientLicense** | `client_license` | 1 | Active license row in `system.sqlite3` |

### 3.3 Migration & Seed Scripts

- **`migrate_legacy_data.py`** (Repository Root):
  - Purpose: Migrates legacy VentaPOS v1.0 SQLite data (`salesapp_*` tables from `Backup_SalesApp_2026-05-24.sqlite3`) into NextGen tables (`Tenant`, `Branch`, `Salesperson`, `InventoryItem`).
  - Automatically creates/uses tenant `company_code="LGCY"` ("Legacy Migrated Tenant").
- **`backend/create_tenant.py`**:
  - Seed script to ensure company `1234` ("Local Dev Company") and Branch local_id `1` ("الفرع الرئيسي") exist.
- **`backend/inspect_db.py`**:
  - Custom utility created during this exploration to inspect row counts, schema attributes, and records across both `default` and `system` SQLite databases.

---

## 4. Test Runner Setup & E2E Testing Verification

### 4.1 Backend Test Framework
- **Framework**: Django Test Suite (`django.test.TestCase`).
- **Location**: `backend/api/tests/`
- **Key Test Files**:
  - `test_parity.py`: 56 test cases covering:
    1. **Time-Machine Stock Calculations**: `InventoryItem.get_stock_at_date()`
    2. **Invoice Cryptographic Hashes**: `generate_receipt_signature()` (HMAC-SHA256)
    3. **Installment Billing Rules**: 25th-of-month schedule calculation
    4. **License Balance Deduction**: Deducts 1 unit from `invoices_balance` per saved receipt
    5. **Record Signatures**: DB tamper detection via HMAC signature
    6. **POS Entry Parity**: Autocomplete endpoints & submission behavior
  - `test_suggestions_and_parity.py`: 4 test cases for customer & product suggestion endpoints.
- **Execution Command**:
  ```powershell
  .\venv\Scripts\python.exe backend\manage.py test api.tests.test_parity api.tests.test_suggestions_and_parity --keepdb
  ```

### 4.2 Frontend / E2E Testing Framework
- Currently, `frontend/package.json` contains `oxlint` for linting, but no browser automation framework (such as Cypress, Playwright, or Vitest) is pre-configured in `package.json`.
- E2E testing of the Web POS UI (`http://localhost:5173/pos`) can be performed using browser automation tools or Python HTTP request automation against `/api/v1/receipts/` and `/api/v1/products/search/`.

---

## 5. Summary Matrix for NextGen POS Testing

| Area | Current Status | Verification Command | Notes |
|---|---|---|---|
| **Backend API** | Ready | `.\venv\Scripts\python.exe backend\manage.py runserver 8000` | Port 8000 required for Vite proxy |
| **Frontend UI** | Ready | `npm run dev` (in `frontend/`) | Port 5173 (`http://localhost:5173/pos`) |
| **Database** | Populated & Ready | `.\venv\Scripts\python.exe backend\inspect_db.py` | DB has tenant `1234`, branch `1`, products ("كبة", "test2"), and existing receipts |
| **Backend Unit/Integration Tests** | Operational | `.\venv\Scripts\python.exe backend\manage.py test api.tests.test_suggestions_and_parity --keepdb` | 4/4 passing |

