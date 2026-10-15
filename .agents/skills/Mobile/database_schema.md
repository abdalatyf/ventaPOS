# Mobile App Database Schema & State Models

## SQLite Database (`mobile_sales_v1.db`)
File: `D:\Projects\VentaPOS\Mobile\sales_app_offline\lib\db\database_helper.dart`

### Table: `config`
Used to store key-value configuration pairs, primarily identity details.
*   **Fields:**
    *   `key`: `TEXT PRIMARY KEY` - The configuration key (e.g., 'branch_id', 'salesperson_id').
    *   `value`: `TEXT` - The corresponding value.
*   **Operations/Behaviors:**
    *   Upserts (replace on conflict) used in `setIdentity(branchId, salespersonId)`.

### Table: `inventory`
Stores the local copy of the product catalog.
*   **Fields:**
    *   `id`: `INTEGER PRIMARY KEY` - The unique ID of the product.
    *   `name`: `TEXT` - The name of the product.
    *   `code`: `TEXT` - The barcode or product code.
*   **Operations/Behaviors:**
    *   Populated via `importProducts(List<dynamic> products)`, which deletes all existing records before inserting the new batch (full refresh) inside a transaction.
    *   Queried via `searchProducts(String query)` using `name LIKE ? OR code LIKE ?`.

### Table: `receipts`
Stores offline receipts to be exported later.
*   **Fields:**
    *   `id`: `INTEGER PRIMARY KEY AUTOINCREMENT` - Internal local auto-incremented receipt ID.
    *   `composite_key`: `TEXT UNIQUE` - A unique identifier used to prevent duplication, combining identity and local time/ID.
    *   `customer_name`: `TEXT` - The name of the customer.
    *   `total_amount`: `REAL` - The total amount of the sale.
    *   `sale_date`: `TEXT` - ISO8601 string of the creation datetime.
    *   `is_exported`: `INTEGER DEFAULT 0` - Flag indicating if the receipt has been synced with the server (0 = pending, 1 = exported).
    *   `json_payload`: `TEXT` - A stringified JSON representation of the full receipt payload, capturing all line items and metadata needed for export.
*   **Operations/Behaviors:**
    *   `saveReceipt`: Inserts a new receipt with `is_exported` defaulting to 0 and auto-generated `sale_date`.
    *   `getPendingReceipts`: Queries where `is_exported = 0`.
    *   `markAsExported(List<int> ids)`: Updates `is_exported = 1` for matching IDs.
    *   `getNextReceiptId`: Aggregates `MAX(id)` for display purposes.
    *   `deleteReceipt(int id)`: Deletes receipt by ID.
    *   `updateReceipt(...)`: Updates existing pending receipt attributes and re-serializes payload.
    *   `getAllReceipts()`: Queries all ordered by ID descending.
    *   `deleteAllExportedReceipts()`: Cleans up database by removing records where `is_exported = 1`.

## Local State Variables (UI State)
*(Note: These will be further detailed in Business Logic and Routing steps as they reside in widget states. Primary persistent state is localized within the SQLite tables above).*
