# Backend Micro-Features & Helper APIs

This document details the specialized backend endpoints and architectural choices that support the frontend in VentaPOS NextGen, specifically focusing on commission tracking, manual inventory adjustments, autocomplete optimizations, and date synchronization.

## 1. Commission History (`CommissionHistoryViewSet`)

**Endpoint**: `/api/commission-histories/` or `/api/v1/commission-history/`

### How Commission Histories Track Changes Over Time
In a POS environment, commission rates for salespeople or items are not static; they change over time. If a commission rate is updated, historical reports (e.g., last month's ledger) must still reflect the rate that was active *at that time*, not the newly updated rate.

To solve this, the backend uses an append-only time-machine approach:
- The `CommissionHistory` table records any changes to a commission rate along with an effective date (month/year).
- When the ledger or a report needs to calculate commissions for a specific period, it calls an internal method like `get_commission_at_date(month, year)`.
- The system queries the most recent `CommissionHistory` entry that is **at or before** the requested date.
- If no history record exists for the requested timeframe, it falls back to the `initial_commission_amount` defined on the core item.

This ensures financial data integrity and prevents retroactive corruption of past sales reports when commission rates are updated.

---

## 2. Manual Stock-Taking (`InventoryAdjustmentViewSet`)

**Endpoint**: `/api/inventory-adjustments/` or `/api/v1/inventory-adjustments/`

### How Manual Stock-Taking Works
Physical inventory often deviates from the calculated system inventory due to theft, damage, or data entry errors. The `InventoryAdjustmentViewSet` provides a secure way to reconcile the system without destructively altering past sales or purchase records.

- **Adjustment Types**: Managers can submit adjustments categorized as either `DEFICIT` (stock lost/missing) or `SURPLUS` (extra stock found).
- **Ledger Impact**: Instead of overwriting the "current stock" integer on a product, the backend creates an immutable `InventoryAdjustment` log. 
- When the system calculates current inventory (e.g., via the ledger endpoint), it dynamically aggregates: `Initial Stock + Total Purchases - Total Sales + Total Adjustments (Surplus - Deficit)`.
- This ensures that every manual change to the inventory is fully audited, timestamped, and attributable to a specific stock-taking event.

---

## 3. Auto-Complete Suggestion APIs

**Endpoints**: 
- `/api/customer-suggestions/`
- `/api/product-suggestions/`

### How Suggestion APIs Optimize Frontend Performance
During peak hours, cashiers need the POS entry screen (`PosEntry.jsx`) to be blazingly fast. Fetching the standard `/api/customers/` or `/api/products/` endpoints for a dropdown search is highly inefficient because those endpoints return heavy, nested JSON payloads containing full transaction histories, related keys, and unneeded metadata.

To solve this, the Suggestion APIs are heavily optimized:
- **Lightweight Payloads**: They return only the bare minimum fields required for a dropdown selection (e.g., `id`, `name`, `code`, and perhaps `price`).
- **Debounced Frontend Integration**: As the cashier types, the frontend debounces the input, firing a request to these specialized endpoints.
- **Database Optimization**: The backend avoids complex joins or aggregations in these views, executing simple `LIKE` or full-text searches. 

This micro-feature prevents the UI from freezing, reduces network payload sizes significantly, and ensures the auto-complete dropdown feels instantaneous.

---

## 4. Default Date Synchronization (`DefaultDateView`)

**Endpoint**: `/api/default-date/`

### Why Use a Unified Backend Date?
VentaPOS is an offline-first desktop application, meaning the backend (Django) and frontend (React) run locally on the cashier's machine. Normally, a frontend might rely on `new Date()` from the local OS clock. However, VentaPOS relies on `/api/default-date/` for a critical business reason: **The Logical Business Day**.

- **Shift Overlaps**: A store's operating shift may continue past midnight (e.g., 2:00 AM). If the frontend relied on the local client time, transactions would split across two different calendar days, breaking daily closing reports and cash drawer reconciliations.
- **Centralized Control**: The backend dictates the "active" business date. Until a manager explicitly runs the "End of Day" or "Close Shift" process, the `/api/default-date/` will continue to return the logical business date, regardless of the local OS clock passing midnight.
- **Data Integrity**: This prevents data fragmentation and stops cashiers from accidentally manipulating dates by changing their local Windows system clock.
