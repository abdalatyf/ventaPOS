# Mobile App Core Business Logic

## 1. Setup & Identity Workflow (`setup_screen.dart`)
*   **Initialization Sequence:** On startup, `main.dart` checks local SQLite for `salesperson_id`. If `0` (or empty), routes to `SetupScreen`.
*   **Data Import (JSON):** The user imports a `setup.json` file via `FilePicker`.
*   **Validation & Extraction:** The app expects JSON containing keys `branch_id` and `products`. Optionally `salesperson_id`.
*   **State Mutation:** Calls `setIdentity` to lock the device to a branch/salesperson, and `importProducts` to fully overwrite the local `inventory` table with the new product catalog.

## 2. Point of Sale & Receipt Calculation (`pos_screen.dart`)
This screen manages the creation and modification of offline receipts.

### Cart Management & Pricing
*   Products are added by searching the local `inventory` table.
*   The cart stores `id`, `name`, `code`, `qty`, and `price`.
*   **Crucial Rule:** Prices are NOT fetched from the inventory. They are manually inputted by the salesperson per item via a dedicated `TextEditingController`.

### Mathematical Steps: Totals & Balance
*   `_totalItemsPrice` = $\sum (\text{qty} \times \text{price})$ for all items in `_cart`.
*   `_totalPaid` = 
    *   If `_isCash` is true: `_totalItemsPrice`.
    *   If `_isCash` is false: `down_payment` + $\sum_{sys=1}^{3} (\text{months}_{sys} \times \text{amount}_{sys})$.
*   **Validation Rule (isBalanced):** The receipt can only be saved if `abs(_totalItemsPrice - _totalPaid) <= 1.0` and `_totalItemsPrice > 0`. This enforces strict financial balancing before allowing a save.

### Installment Generation
If a sale is not cash, the system generates a schedule:
*   **Start Date:** Defaults to the 15th of the currently selected month/year (`DateTime(_selectedYear, _selectedMonth, 15)`).
*   **Schedule Builder:** Iterates sequentially through system 1, then system 2, then system 3. For each month $i$, it adds 1 to the month offset, generating a payment date and assigning the corresponding amount.
*   **String Formatter:** Compiles an `installment_system` string in the format `"amount*months + amount*months"`.

### Serialization
*   Constructs a deep JSON payload containing metadata, the calculated `total_amount`, the `products_text` (a summarized string of items), the full `items` array, and the `payments` array (if installments exist).
*   Generates a `composite_key`: `"SP{salesperson_id}_{timestamp}"` to ensure global uniqueness when eventually synced.

## 3. Archive, Filtering, and Export (`receipts_archive_screen.dart`)

### Filtering Engine
Filters operate directly on the deserialized JSON strings in memory (`jsonDecode(receipt['json_payload'])`).
*   **Text Search:** Matches query against `customer_name`, `phone_number`, `area`, `address`.
*   **Date Search:** Matches `sale_month` and `sale_year`.
*   **ID Range Search:** Matches local SQLite auto-incremented `id`.

### Export Workflow (The Sync Mechanism)
Since the app is entirely offline, "syncing" is done via file sharing:
1.  **Collection:** Gathers all receipts where the checkbox is selected (defaults to `is_exported == 0`).
2.  **Aggregation:** Wraps the array of receipt JSON payloads in a master envelope containing `meta` (branch_id, salesperson_id, export_timestamp).
3.  **File Generation:** Writes this envelope to a physical JSON file `Sales_B{branch_id}_SP{sp_id}_{timestamp}.json`.
4.  **Sharing:** Uses `share_plus` to invoke the native OS share dialog (e.g., sending via WhatsApp or Email to the backend admin).
5.  **State Update:** On successful share dialog return, marks the selected receipts as `is_exported = 1` in the database.

### Data Retention
*   Exported receipts remain in the database (marked with a gray indicator in the UI).
*   They can be permanently deleted via the "delete_exported" popup menu option which invokes `deleteAllExportedReceipts()`.
