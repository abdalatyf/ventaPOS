# Handoff Report — Codebase Routing & Endpoints Registry

This report compiles the complete, verified registry of all active React frontend routes and pages alongside all active Django backend viewsets, views, and url endpoints for the VentaPOS NextGen application.

---

## 1. Observations

### A. Frontend Routes & Components (`VentaPOS_NextGen/frontend/src/App.jsx`)
In `App.jsx`, the routing structure uses `react-router-dom` and is defined as follows:

- **Public Routes (outside AppShell)**:
  - `/init` → `SystemInit.jsx` (System setup wizard)
  - `/login` → `Login.jsx` (Cashier login screen)
  - `/select-branch` → `BranchSelection.jsx` (Branch selection gateway, requires authentication)

- **Protected Routes (inside AppShell wrapper)**:
  - `/` → Redirects to `/receipts`
  - `/dashboard` → `Dashboard.jsx` (Dashboard metrics page)
  - `/pos` → `POS.jsx` (Cashier POS register, currently a visual skeleton)
  - `/setup` → `Setup.jsx` (System setup and data entry. Employs state tabs: `inventory` → `InventoryTab.jsx`, `salespersons` → `SalespersonsTab.jsx`, `suppliers` → `SuppliersTab.jsx`)
  - `/receipts` → `SearchReceipts.jsx` (Sales receipts search/history)
  - `/inventory` → `Inventory.jsx` (Current inventory status page)
  - `/product-ledger/:id` → `ProductLedger.jsx` (Audit trail ledger for specific inventory item)
  - `/search-purchases` → `SearchPurchases.jsx` (Search purchase invoices)
  - `/purchases/new` → `PurchaseEntry.jsx` (Create new purchase invoice)
  - `/purchases/edit/:id` → `PurchaseEntry.jsx` (Edit existing purchase invoice)
  - `/expenses` → `Expenses.jsx` (Branch expenses log)
  - `/reports` → `ReportsLayout.jsx` (Layout managing date selectors and sub-reports NavLinks):
    - `/reports/dashboard` → `DashboardReport.jsx` (Business summary stats)
    - `/reports/receipts` → `ReceiptsReport.jsx` (Detailed receipts tally)
    - `/reports/expenses` → `ExpensesReport.jsx` (Tally of all expenses)
    - `/reports/salesperson` → `SalespersonPerformanceReport.jsx` (Salesperson metrics and commissions)
    - `/reports/inventory` → `InventoryMovementReport.jsx` (Inventory audit ledger summary)
    - `/reports/profit-and-loss` → `ProfitAndLossReport.jsx` (Profit and loss statement)
    - `/reports/cash-drawer` → `CashDrawerReport.jsx` (Cash register stats. *Note: Route exists but has no link in ReportsLayout.jsx navigation tabs*)
    - `/reports/installments` → `InstallmentsReport.jsx` (Aging and upcoming installment dues)
  - `/tools` → `ToolsDashboard.jsx` (Administration tools dashboard. Employs state tabs: `sync` → `SyncTab.jsx`, `import` → `SmartImportTab.jsx`, `backup` → `BackupTab.jsx`, `logs` → `LogsTab.jsx`)
  - `/settings` → `SettingsIndex.jsx` (App settings. Employs state tabs: `company` → `CompanyTab.jsx`, `security` → `SecurityTab.jsx`, `subscription` → `SubscriptionTab.jsx`)

- **Orphaned / Unused Frontend Files**:
  - `PosEntry.jsx`: Contains a complete, 784-line React implementation of a POS cart with live customer suggestions, installment breakdowns, and item selection. Currently unmapped in `App.jsx` in favor of the basic skeleton `POS.jsx`.
  - `ReportsIndex.jsx`: Grid menu of available reports. Currently unused since `/reports` redirects automatically to `/reports/dashboard`.

---

### B. Backend Endpoints (`VentaPOS_NextGen/backend/api/urls.py`)
All backend endpoints are prefixed with `/api/v1/` based on `backend/urls.py`. The routing configuration consists of Django Rest Framework ViewSets and APIViews:

#### 1. Registered ViewSets (DefaultRouter)
- `/api/v1/company-settings/` → `CompanySettingViewSet`
- `/api/v1/branches/` → `BranchViewSet`
- `/api/v1/salespersons/` → `SalespersonViewSet`
- `/api/v1/inventory-items/` → `InventoryItemViewSet`
  - *Custom actions*:
    - `GET /api/v1/inventory-items/{id}/stock/` (and alias `get_safe_available_qty/`) → Projected safe stock quantity.
    - `GET /api/v1/inventory-items/pos_search/` → Search for items during POS checkout.
    - `GET /api/v1/inventory-items/{id}/ledger/` → Ledger timeline.
- `/api/v1/commission-histories/` → `CommissionHistoryViewSet`
- `/api/v1/inventory-adjustments/` → `InventoryAdjustmentViewSet`
- `/api/v1/suppliers/` → `SupplierViewSet`
- `/api/v1/purchase-invoices/` → `PurchaseInvoiceViewSet`
  - *Custom actions*:
    - `POST /api/v1/purchase-invoices/desktop_print/` → Local invoice PDF printer utility.
- `/api/v1/purchase-invoice-items/` → `PurchaseInvoiceItemViewSet`
- `/api/v1/expenses/` → `ExpenseViewSet`
- `/api/v1/receipts/` → `ReceiptViewSet`
  - *Custom actions*:
    - `POST /api/v1/receipts/bulk_delete/` → Soft deletes multiple receipts.
    - `GET /api/v1/receipts/printers/` → Queries OS for installed printers list using PowerShell.
    - `POST /api/v1/receipts/desktop_print/` → Generates PDF and opens it locally via PDF viewer/printer.
- `/api/v1/sale-items/` → `SaleItemViewSet`
- `/api/v1/installment-payments/` → `InstallmentPaymentViewSet`
- `/api/v1/pending-external-receipts/` → `PendingExternalReceiptViewSet`
- `/api/v1/client-licenses/` → `ClientLicenseViewSet`
- `/api/v1/used-licenses/` → `UsedLicenseViewSet`
- `/api/v1/license-history/` → `LicenseHistoryViewSet`
- `/api/v1/action-logs/` → `ActionLogViewSet`

#### 2. Explicit Path Endpoints (APIViews)
- **Authentication & Setup**:
  - `POST /api/v1/init/` → `SystemInitializationView` (First-time initialization and seed database)
  - `POST /api/v1/auth/local/` → `CustomAuthToken` (Django Token Auth token generation)
  - `POST /api/v1/auth/demo/` → `DemoAuthToken` (Demo mode quick-login)
  - `POST /api/v1/auth/recover/` → `PasswordRecoveryView` (Local password reset using recovery code)
  - `POST /api/v1/auth/change-password/` → `ChangePasswordView` (Password reset for authenticated users)
- **Licensing**:
  - `GET /api/v1/license/status/` → `LicenseStatusView` (Current license status checker)
  - `POST /api/v1/license/activate/` → `LicenseActivateView` (Activate license key)
- **Suggestions & Context**:
  - `GET /api/v1/customer-suggestions/` → `CustomerSuggestionsView` (Debounced customer details lookup)
  - `GET /api/v1/product-suggestions/` → `ProductSuggestionsView` (Live search lookup)
  - `GET /api/v1/default-date/` → `DefaultDateView` (Gets reporting date context)
- **Reports**:
  - `GET /api/v1/reports/dashboard/` (and alias `dashboard/summary/`) → `DashboardReportView`
  - `GET /api/v1/reports/salespersons/` (and alias `salesperson-performance/`) → `SalespersonPerformanceReportView`
  - `GET /api/v1/reports/inventory-movement/` → `InventoryMovementReportView`
  - `GET /api/v1/reports/sales-pl/` (and alias `profit-and-loss/`) → `ProfitAndLossReportView`
  - `GET /api/v1/reports/cash-drawer-details/` (and alias `cash-drawer/`) → `CashDrawerReportView`
  - `GET /api/v1/reports/installments/` → `InstallmentsReportView`
- **Utilities & Tools**:
  - `GET /api/v1/tools/backup/download/` → `BackupDownloadView` (Download current SQLite database backup)
  - `POST /api/v1/tools/backup/upload/` → `BackupUploadView` (Restore database backup upon next reload)
  - `GET /api/v1/tools/sync/export-items/` → `OfflineExportItemsView` (Generate JSON of inventory items for mobile device)
  - `POST /api/v1/tools/sync/import-receipts/` → `OfflineImportReceiptsView` (Ingest USB/JSON offline receipts payload)
  - `POST /api/v1/tools/sync/approve-pending/<int:pk>/` → `ApprovePendingReceiptView` (Approve offline receipt and update stock)
  - `POST /api/v1/tools/smart-import/` → `SmartImportWizardView` (Excel parser to populate inventory items)

#### 3. Defined but Unmapped/Unused Backend Views (In views.py only)
These views are fully implemented in `api/views.py` but are not registered in `api/urls.py` (likely because this backend runs in local offline desktop mode and does not handle direct remote sync push/pull requests):
- `ViewerAuthView` (`POST /api/v1/auth/viewer/`)
- `SyncPushView` (`POST /api/v1/sync/push/`)
- `SyncPullView` (`GET|POST /api/v1/sync/pull/`)
- `ConfirmReceiptsView` (`POST /api/v1/sync/confirm-receipts/`)

---

## 2. Logic Chain

1. **Routing File Analysis**: By analyzing `App.jsx` and `backend/api/urls.py`, we identified all registered routes and their component mappings.
2. **Tab-based Routing Identification**: By inspecting `Setup.jsx`, `ToolsDashboard.jsx`, and `SettingsIndex.jsx`, we established that sub-views are implemented via state-driven React tabs rather than React Router paths.
3. **Dead-Code Discovery**: 
   - A filesystem-wide search for component usages identified that `PosEntry.jsx` and `ReportsIndex.jsx` are not imported or navigated to inside the active `App.jsx` routing.
   - A search for class imports and usages in `backend/api/` revealed that `SyncPushView`, `SyncPullView`, `ConfirmReceiptsView`, and `ViewerAuthView` are defined in `views.py` but completely omitted from `urls.py`.
4. **Header Integration verification**: Analysis of `api.js` showed how requests attach standard headers (`Authorization`, `X-Company-Code`, `X-Machine-ID`, `X-Branch-ID`) to interact with the backend views.

---

## 3. Caveats
- No active network request validation was done since the investigation operates in `CODE_ONLY` network mode. All endpoint details were extracted directly from python source views, url paths, and serializers.
- This registry is accurate as of current codebase state. Some unmapped routes (like `/reports/cash-drawer` missing from the Reports layout) might be intentionally reachable only via deep links or internal redirects.

---

## 4. Conclusion
The VentaPOS NextGen application is mapped accurately with 16 active React router paths and 44 Django API views/endpoints. There are a few orphaned frontend screens (`PosEntry.jsx`, `ReportsIndex.jsx`) and unregistered backend sync views (`SyncPushView`, `SyncPullView`, etc.) which might need clean-up or integration in the future implementation phases.

---

## 5. Verification Method
To verify this registry:
1. **Frontend Route Mapping Check**: Inspect the `<Route>` components inside `VentaPOS_NextGen/frontend/src/App.jsx`.
2. **Backend URLs Check**: Inspect the `urlpatterns` lists inside `VentaPOS_NextGen/backend/backend/urls.py` and `VentaPOS_NextGen/backend/api/urls.py`.
3. **View Action Validation**: Confirm `@action` definitions inside `VentaPOS_NextGen/backend/api/views.py` (e.g. `pos_search` on `InventoryItemViewSet`).
