# Mobile App API & Security Architecture

## Network & API Landscape (Fully Offline)
The VentaPOS Mobile application is designed as a **100% offline-first, air-gapped system** (`sales_app_offline`). 
*   **No Network Calls:** There are no HTTP clients (no `http`, `dio`, or `fetch` packages used).
*   **No Middleware/Decorators:** Standard API middleware, JWTs, or OAuth decorators do not exist in this context.
*   **No Real-time Sync:** The app does not connect to any endpoint directly.

## Data Exchange Contracts (File-Based Sync)
Data exchange with the backend server is handled entirely via manual JSON file imports and exports.

### 1. Import Contract (`setup.json`)
Used to initialize the application, provide identity, and load the product catalog.
*   **Method:** Read from the device filesystem via `FilePicker`.
*   **Expected Payload:**
    ```json
    {
      "branch_id": 1,
      "salesperson_id": 105,
      "products": [
        {"id": 1, "name": "Product A", "code": "123456"}
      ]
    }
    ```

### 2. Export Contract (Sales Sync File)
Used to send created receipts back to the central server.
*   **Method:** Written to the sandboxed `getApplicationDocumentsDirectory()` and shared externally via `share_plus` (e.g., WhatsApp, Email).
*   **Filename Format:** `Sales_B{branch_id}_SP{salesperson_id}_{timestamp}.json`
*   **Export Payload:**
    ```json
    {
      "meta": {
        "branch_id": 1,
        "salesperson_id": 105,
        "export_timestamp": "2024-05-18T12:00:00.000"
      },
      "payload": {
        "receipts": [
          {
             "local_id": 1,
             "sale_year": 2024,
             "sale_month": 5,
             "customer_name": "John Doe",
             "address": "123 Street",
             "phone_number": "0100000000",
             "area": "Downtown",
             "is_cash_sale": false,
             "total_amount": 5000.0,
             "down_payment": 1000.0,
             "products_text": "1 Product A + 2 Product B",
             "installment_system": "1000*4",
             "items": [
               {"product_id": 1, "product_name": "Product A", "quantity": 1, "price": 2000.0}
             ],
             "payments": [
               {"date": "2024-06-15", "amount": 1000.0}
             ]
          }
        ]
      }
    }
    ```

## Security & Authentication Flow
*   **Authentication:** The app lacks traditional password/token authentication. "Login" is strictly determined by the presence of a non-zero `salesperson_id` in the local SQLite `config` table.
*   **Access Control:** `main.dart` runs `_checkIdentity()` on startup. If `salesperson_id == 0`, the user is forcefully routed to `SetupScreen` and locked out of all operational screens (`Dashboard`, `POS`). Once setup is complete, the user is permanently logged in for that device.
*   **Data Security:** Data is stored unencrypted in local SQLite (`mobile_sales_v1.db`). Security relies entirely on the host OS's application sandboxing (Android/iOS app data isolation). Exported JSON files are plain text.
