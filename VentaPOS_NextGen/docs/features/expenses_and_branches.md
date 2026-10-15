# Expenses and Branch Context

This document explains the branch-specific features and expense tracking in the VentaPOS NextGen application, detailing the strict Branch Context rule and how daily expenses are recorded against a specific branch.

## 1. Branch Selection Context

VentaPOS is designed as an offline-first multi-branch system where every operational transaction and expense must be strictly tied to a specific branch.

### Frontend Flow
1. **Branch Selection (`BranchSelection.jsx`)**: 
   When the application starts, users must select a branch from the grid of available branches. This selection persists the active branch ID in the browser's `localStorage` as `branchId`.
2. **API Interceptor (`api.js`)**:
   An Axios interceptor reads the `branchId` from `localStorage` and automatically injects it into every outgoing HTTP request via the `X-Branch-ID` header.

### Branch Commission Rules
The Branch model includes a `collection_commission_rate` (DecimalField). This is the percentage used to calculate the collection commission (عمولة تحصيل).
- This percentage rate applies globally to **ALL** salespersons working within that branch.
- A salesperson's total monthly collection commission is calculated as: `collection_commission_rate × total_monthly_collections`.

### Backend Context Resolution
On the backend (Django API), the `TenantFromRequestMixin` (combined with `SoftDeleteModelViewSet`) automatically resolves and enforces the branch context:
- For `POST` (create) requests, the `_fill_local_data()` method intercepts the creation payload. It reads the `X-Branch-ID` HTTP header and automatically populates the `branch_id` field in the database.
- This ensures that frontend forms do not need to explicitly include the `branch_id` in their JSON payloads, preventing manual manipulation and enforcing strict data context.

## 2. Expense Tracking

Expenses are recorded on a monthly basis, strictly linked to a specific `expense_month` and `expense_year`, and bound to the active branch.

### Frontend Expense Management (`Expenses.jsx`)
- **Default Date Resolution**: The page uses a custom hook `useDefaultDate(branchId)` to default the month and year filters based on the selected branch's local time zone or last active date.
- **Fetching Expenses**: The UI sends a `GET` request to `/api/expenses/?month={month}&year={year}`. The request inherently carries the `X-Branch-ID` header.
- **Adding Expenses**: When submitting a new expense, the payload only contains `description`, `amount`, `expense_month`, and `expense_year`. The frontend relies completely on the Axios interceptor to transmit the branch context.

### Backend Processing (`ExpenseViewSet`)
- **Filtering (`GET`)**: `ExpenseViewSet.get_queryset()` retrieves the `branch_id` query parameter if provided, or otherwise securely filters by the authenticated tenant. (In the frontend, only expenses matching the selected month and year are queried).
- **Creation (`POST`)**: The overridden `create()` method in `SoftDeleteModelViewSet` automatically binds the newly created `Expense` to the branch identified by the `X-Branch-ID` header, adhering to the strict branch context rule.

## 3. Strict Branch Context Rule

To prevent data cross-contamination between branches, VentaPOS strictly enforces the following:
- **No Orphaned Expenses**: Every expense must belong to a branch. The `_fill_local_data` method guarantees that if the `X-Branch-ID` header is present, the branch relation is auto-assigned. If the header is missing, it attempts to fall back to a default branch for the local device.
- **Data Isolation**: This design ensures that a cashier logged into Branch A cannot accidentally record expenses for Branch B. The active `branchId` acts as a global application state that implicitly secures and scopes all subsequent API calls.
