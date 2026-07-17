# Inventory Management & Time-Machine Ledger

## 1. Adding and Editing Items (Initial Balance)
In VentaPOS NextGen, adding an inventory item is not just about registering a product's name; it establishes the baseline for the system's "Time-Machine" retrospective engine. 

When a user adds or edits an item via the `Inventory.jsx` interface, they are required to input initial state parameters:
*   **Initial Quantity (`initial_quantity`)**: The exact stock balance of the item at the moment it was registered in the system (opening balance).
*   **Initial Purchase Price (`initial_purchase_price`)**: The base unit cost at that starting point.
*   **Initial Commission (`initial_commission_amount`)**: The baseline salesperson commission (مندبة) for selling this item.
*   **Start Date (`initial_month` & `initial_year`)**: The exact month and year this opening balance was recorded. 

The time-machine engine uses these fields as $t_0$. Any stock calculations for a specific month will start with this initial quantity and iteratively apply all inward (purchases/returns) and outward (sales/adjustments) movements that occurred after this start date.

## 2. The Product Ledger (كارت الصنف)
The Product Ledger (`ProductLedger.jsx`) provides a comprehensive audit trail and profitability breakdown for a specific item. It is divided into four main tabs:

1.  **Dashboard (لوحة المعلومات)**: Displays high-level Key Performance Indicators (KPIs). It calculates total profit by dynamically subtracting the time-machine average cost from the sales revenue, separating **Cash Profit** and **Installment Profit**, and accounting for the financial impact of manual stock adjustments.
2.  **Financial / Monthly Summary (تحليل مالي)**: Aggregates movements on a monthly basis. It shows the total incoming vs. outgoing stock for each month, calculating the net profit and the total sales commissions paid out during that period based on the specific historical cost.
3.  **Movement / Timeline (السجل التفصيلي)**: A strict chronological ledger of every single transaction that affected the item's quantity. This includes initial balances, purchase invoices (IN), sales receipts (OUT), factory returns (OUT), and manual deficit/surplus adjustments.
4.  **Salespersons Commissions (سجل المندبات)**: A time-machine tracking tab specifically for salesperson commissions. Since commission rates fluctuate over time, this tab logs the changes (by month/year) so that historical sales are always calculated using the commission rate active at the time of the sale, not the current rate.

## 3. Missing Requirements & Code Discrepancies
While reviewing the current implementation in `frontend/src/pages/Inventory.jsx`, `frontend/src/pages/ProductLedger.jsx`, and `backend/api/views.py`, several discrepancies were found between the intended architecture and the actual code:

### 3.1. API Contract Mismatch in Ledger Data
*   The backend `InventoryItemViewSet.ledger` endpoint returns a JSON payload containing `timeline`, `monthly_summary`, and `dashboard_metrics`.
*   However, the frontend `ProductLedger.jsx` expects the data under different keys: `data.movements` (instead of timeline), `data.financials` (instead of monthly_summary), and it expects a `data.commissions` array.
*   Because of this mismatch, the frontend fails to parse the real backend data and falls back to rendering `MOCK_LEDGER`.

### 3.2. Missing Commission Data in Ledger Endpoint
*   The frontend expects `data.commissions` to populate the "سجل المندبات" tab. 
*   The backend's `ledger` endpoint calculates commissions internally for the dashboard metrics but **does not** return the historical list of commission changes in its response. A separate fetch to `CommissionHistoryViewSet` is needed, or the backend `ledger` endpoint must be updated to include it.

### 3.3. Inventory List Shows Stale Initial Balances
*   In `Inventory.jsx`, the frontend maps the fetched items and sets `quantity: item.initial_quantity` to display in the data table.
*   **Critical Flaw**: This means the main Inventory list only ever displays the *opening balance* of the items, not the actual, real-time live stock. It completely bypasses the time-machine calculation endpoint (`/api/v1/inventory-items/<id>/stock/` or `safe_available_qty`) which is required to determine how many items are currently in the warehouse.

### 3.4. Create/Update Payload Formatting
*   The `Inventory.jsx` modal captures standard field names (`quantity`, `purchase_price`) but maps them to `initial_quantity` and `initial_purchase_price` before sending the POST/PUT payload. While correct for creation, applying this on a PUT (edit) request will silently overwrite the historical opening balance of the item rather than creating a stock adjustment, which violates the immutable ledger principles.
