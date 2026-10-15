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

---

## 4. Commission History (`CommissionHistoryViewSet`)

### How Commission Histories Track Changes Over Time
In a POS environment, commission rates for salespeople or items are not static; they change over time. If a commission rate is updated, historical reports (e.g., last month's ledger) must still reflect the rate that was active *at that time*, not the newly updated rate.

To solve this, the backend uses an append-only time-machine approach:
- The `CommissionHistory` table records any changes to a sales commission rate (مندبة) along with an effective date (month/year).
- When the ledger or a report needs to calculate commissions for a specific period, it calls an internal method like `get_commission_at_date(month, year)`.
- The system queries the most recent `CommissionHistory` entry that is **at or before** the requested date.
- If no history record exists for the requested timeframe, it falls back to the `initial_commission_amount` defined on the core item.

This ensures financial data integrity and prevents retroactive corruption of past sales reports when commission rates are updated.

---

## 5. Manual Stock-Taking (`InventoryAdjustmentViewSet`)

### How Manual Stock-Taking Works
Physical inventory often deviates from the calculated system inventory due to theft, damage, or data entry errors. The `InventoryAdjustmentViewSet` provides a secure way to reconcile the system without destructively altering past sales or purchase records.

- **Adjustment Types**: Managers can submit adjustments categorized as either `DEFICIT` (stock lost/missing) or `SURPLUS` (extra stock found).
- **Ledger Impact**: Instead of overwriting the "current stock" integer on a product, the backend creates an immutable `InventoryAdjustment` log. 
- When the system calculates current inventory (e.g., via the ledger endpoint), it dynamically aggregates: `Initial Stock + Total Purchases - Total Sales + Total Adjustments (Surplus - Deficit)`.
- This ensures that every manual change to the inventory is fully audited, timestamped, and attributable to a specific stock-taking event.

---

## 6. Default Date Synchronization (`DefaultDateView`)

### Why Use a Unified Backend Date?
VentaPOS is an offline-first desktop application, meaning the backend (Django) and frontend (React) run locally on the cashier's machine. Normally, a frontend might rely on `new Date()` from the local OS clock. However, VentaPOS relies on `/api/default-date/` for a critical business reason: **The Logical Business Day**.

- **Shift Overlaps**: A store's operating shift may continue past midnight (e.g., 2:00 AM). If the frontend relied on the local client time, transactions would split across two different calendar days, breaking daily closing reports and cash drawer reconciliations.
- **Centralized Control**: The backend dictates the "active" business date. Until a manager explicitly runs the "End of Day" or "Close Shift" process, the `/api/default-date/` will continue to return the logical business date, regardless of the local OS clock passing midnight.
- **Data Integrity**: This prevents data fragmentation and stops cashiers from accidentally manipulating dates by changing their local Windows system clock.
