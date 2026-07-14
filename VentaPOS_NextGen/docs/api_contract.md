# VentaPOS NextGen - OpenAPI Contract
*This document defines the RESTful endpoints that the React frontend will consume.*

## 🔒 1. Authentication & Licensing
All API endpoints (except `/auth/local/`, `/auth/demo/`, `/auth/recover/`, `/init/`, and `/license/activate/`) require an authenticated session and a valid active license.

### `POST /api/v1/auth/local/`
Authenticates the user using the single master password.
*   **Request**: `{"password": "..."}`
*   **Response**: `200 OK`, `{"token": "...", "company_name": "..."}`

### `POST /api/v1/auth/demo/`
Silently logs the frontend into a volatile Demo Mode if no active license exists.
*   **Response**: `200 OK`, `{"token": "...", "company_name": "شركة تجريبية (Demo)"}`

### `POST /api/v1/auth/recover/`
Recovers the master password using the Recovery Code generated during initialization.
*   **Request**: `{"recovery_code": "VNTA-...", "new_password": "..."}`
*   **Response**: `200 OK` or `400 Bad Request`

### `POST /api/v1/init/`
Initializes the system upon receiving a valid license code. Returns a Recovery Code.
*   **Request**: `{"company_name": "...", "branch_name": "...", "password": "...", "license_code": "..."}`
*   **Response**: `201 Created`, `{"message": "...", "recovery_code": "VNTA-ABCD-1234"}`

### `GET /api/v1/license/status/`
Returns the current status of the machine's license.
*   **Response**: `{"is_active": true, "invoices_balance": 150, "expiry_date": "2026-12-31", "product_name": "Yearly Pro"}`

### `POST /api/v1/license/activate/`
Activates a new code or recharges invoices.
*   **Request**: `{"license_code": "A1B2-C3D4-..."}`
*   **Response**: `200 OK` or `400 Bad Request`

> [!WARNING]
> **402 Payment Required - Read-Only Mode**: If a user attempts to call ANY mutating endpoint (`POST`, `PUT`, `DELETE`) and their license is expired, the API will return a `402 Payment Required` with `{"error": "license_expired", "message": "انتهى الاشتراك"}`. The React app must catch this globally and show a read-only warning.
> **403 Forbidden - License Tamper / Exhausted**: If invoices balance is exhausted or tampering is detected.

---

## 🏬 2. Core Entities

### `GET /api/v1/branches/`
Returns all branches.

### `GET /api/v1/settings/company/`
Returns the singleton company configuration.

---

## 📦 3. Inventory Management

### `GET /api/v1/inventory/`
Returns the product catalog, including the dynamically computed current stock.
*   **Query Params**: `?month=6&year=2026` (For time-machine calculations)

### `GET /api/v1/inventory-items/{id}/ledger/`
Returns the complete history of a product (Purchases, Sales, Returns, Adjustments) and its monthly Financial Analysis (profits and commissions).

### `GET /api/v1/commission-histories/?item_id={id}`
Returns or manages the commission time machine for a specific product. Used to override commissions for a given month/year.

### `POST /api/v1/inventory/adjustments/`
Submit a manual surplus or deficit.

---

## 🛒 4. Point of Sale & Receipts

### `GET /api/v1/receipts/`
Search and filter sales receipts.

### `POST /api/v1/receipts/`
Create a new sale. **Triggers License Invoice Decrement.**
*   **Request Body**:
```json
{
  "customer_name": "Ahmed",
  "branch_id": 1,
  "is_cash_sale": true,
  "total_amount": 500,
  "items": [
     {"inventory_item_id": 4, "quantity": 2, "unit_price": 250}
  ]
}
```
*   **Response**: `201 Created` with `{"receipt_number": 1001}`

---

## 🔌 5. USB & Offline Sync

### `POST /api/v1/sync/usb/`
Accepts a JSON payload from an external USB connection to insert pending receipts.
*   **Request Body**: `{"batch_id": "SYNC-99", "payload": [...]}`
*   **Response**: `202 Accepted`
