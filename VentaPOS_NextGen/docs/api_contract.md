# VentaPOS NextGen - OpenAPI Contract
*This document defines the RESTful endpoints that the React frontend will consume.*

## 🔒 1. Authentication & Licensing
All API endpoints (except `/auth/login/` and `/license/activate/`) require an authenticated session and a valid active license.

### `POST /api/v1/auth/login/`
Authenticates the user and returns an HttpOnly session cookie or Token.
*   **Request**: `{"username": "...", "password": "..."}`
*   **Response**: `200 OK`, `{"role": "CASHIER", "user_id": 1}`

### `GET /api/v1/license/status/`
Returns the current status of the machine's license.
*   **Response**: `{"is_active": true, "invoices_balance": 150, "expiry_date": "2026-12-31", "product_name": "Yearly Pro"}`

### `POST /api/v1/license/activate/`
Activates a new code or recharges invoices.
*   **Request**: `{"license_code": "A1B2-C3D4-..."}`
*   **Response**: `200 OK` or `400 Bad Request`

> [!WARNING]
> **403 Forbidden - License Tamper / Expired**: If a user attempts to call ANY endpoint (especially `POST /api/v1/receipts/`) and their license is expired or has been tampered with, the API will return a `403 Forbidden` with `{"error": "license_expired"}`. The React app must catch this globally.

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
