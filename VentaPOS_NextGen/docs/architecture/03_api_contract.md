# Chapter 3: API Contract

# VentaPOS NextGen — API Contract & Endpoints

> **Status:** Living document · Last updated: 2026-07-19

This document defines the REST API contract between the React frontend and Django backend for the offline-first desktop POS.

## Global Rules
- **Format:** `application/json` for all requests and responses
- **Auth:** `Authorization: Token <token>` header required for all endpoints except `/auth/`
- **Headers:** `X-Branch-ID` required on branch-specific endpoints. (NO `X-Company-Code` needed for single-tenant).
- **RTL/Arabic Policy:** All error messages returned by the API must be in professional Egyptian Arabic suitable for the UI (e.g., `"رصيد الفواتير لا يكفي"`).

---

## 1. Authentication & System Init

| Endpoint | Method | Description |
|---|---|---|
| `/api/init/` | POST | Initialize the system (first run). Sets admin password and generates recovery license code. |
| `/api/auth/local/` | POST | Admin login. Returns DRF Token. Payload: `password`. |
| `/api/auth/demo/` | POST | Enter demo mode. Creates temporary session with sample data. |
| `/api/auth/recover/` | POST | Password recovery. Payload: `recovery_code` (which is validated as a special license) and `new_password`. |

---

## 2. Licensing

| Endpoint | Method | Description |
|---|---|---|
| `/api/license/status/` | GET | Returns current license tier, expiry date, and remaining invoice balance. |
| `/api/license/activate/` | POST | Activate a new 80-bit license code to renew or add invoice balance. |

---

## 3. Reports & Analytics

All reports support query parameters for filtering (e.g., `?month=7&year=2026&branch_id=1`).

| Endpoint | Method | Description |
|---|---|---|
| `/api/reports/dashboard/` | GET | KPI summary (sales, expenses, profit). |
| `/api/reports/salesperson-performance/` | GET | Salesperson metrics. Calculates salary = (مندبة) + (عمولة تحصيل). |
| `/api/reports/inventory-movement/` | GET | Stock in/out movements. |
| `/api/reports/profit-and-loss/` | GET | Per-product profitability and net profit. |
| `/api/reports/cash-drawer/` | GET | Daily/monthly cash flow details. |
| `/api/reports/installments/` | GET | Installment schedule tracking (upcoming/overdue). |
| `/api/reports/receipts/` | GET | Sales ledger with advanced filters. |
| `/api/reports/expenses/` | GET | Branch expenses report. |

---

## 4. Tools & Maintanence

| Endpoint | Method | Description |
|---|---|---|
| `/api/tools/backup/download/` | GET | Download a hot-backup of the SQLite database file. |
| `/api/tools/backup/upload/` | POST | Upload and restore a SQLite database (with integrity check). |
| `/api/tools/sync/export-items/` | GET | Export inventory JSON to USB for offline mobile device. |
| `/api/tools/sync/import-receipts/` | POST | Import receipts JSON from USB into `PendingExternalReceipt`. |
| `/api/tools/sync/approve-pending/{id}/` | POST | Approve a pending imported receipt to create a real sale. |
| `/api/tools/smart-import/` | POST | Excel upload. Expects columns for Name and Quantity only. |

---

## 5. Core CRUD Operations

All entities follow the `SoftDeleteModelViewSet` pattern with standard REST routing:
- `GET /api/{entity}/` (List)
- `POST /api/{entity}/` (Create)
- `GET /api/{entity}/{id}/` (Retrieve)
- `PUT / PATCH /api/{entity}/{id}/` (Update)
- `DELETE /api/{entity}/{id}/` (Soft Delete -> sets `is_deleted=True`)

**Available Entities:**
- `/api/company-settings/`
- `/api/branches/`
- `/api/salespersons/`
- `/api/inventory-items/`
- `/api/inventory-adjustments/`
- `/api/suppliers/`
- `/api/purchase-invoices/`
- `/api/purchase-invoice-items/`
- `/api/receipts/`
- `/api/sale-items/`
- `/api/installment-payments/`
- `/api/expenses/`

### 5.1 Special Rules for Receipts & Installments
- **25th Billing Rule:** When generating installment schedules, the backend enforces that the `payment_date` is the 25th of the month.
- **Payload Schema:** Installments array must use the key `"installments"` and inside each object, the date key must be `"payment_date"`.
- **Deduction:** `POST /api/receipts/` automatically deducts 1 from the license invoice balance.

---

## 6. Helpers

| Endpoint | Method | Description |
|---|---|---|
| `/api/default-date/` | GET | Returns the logical business month/year (not daily). |
| `/api/customer-suggestions/` | GET | Auto-complete list of unique customer names extracted from receipts. |
| `/api/product-suggestions/` | GET | Auto-complete list of product names. |
| `/api/purchase-invoices/desktop_print/` | POST | Triggers `os.startfile()` backend printing for an invoice. |
| `/api/receipts/desktop_print/` | POST | Triggers `os.startfile()` backend printing for a receipt. |
