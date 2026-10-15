# VentaPOS Codebase Interface Map

> **This is a compressed, interface-only representation of the VentaPOS codebase (~10KB).**
> Agents must read this file instead of navigating the raw 200KB+ source code to prevent context bloat.

## 1. Backend Models (`backend/api/models.py`)

### Branch
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `name` (CharField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### Salesperson
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `name` (CharField)
- `branch` (ForeignKey)
- `device_token` (UUIDField)
- `is_device_active` (BooleanField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### InventoryItem
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `name` (CharField)
- `branch` (ForeignKey)
- `initial_quantity` (PositiveIntegerField)
- `initial_purchase_price` (DecimalField)
- `initial_commission_amount` (DecimalField)
- `initial_month` (PositiveIntegerField)
- `initial_year` (PositiveIntegerField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### CommissionHistory
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `item` (ForeignKey)
- `commission_amount` (DecimalField)
- `activation_month` (PositiveIntegerField)
- `activation_year` (PositiveIntegerField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### InventoryAdjustment
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `ADJUSTMENT_TYPES` (Field)
- `item` (ForeignKey)
- `adjustment_type` (CharField)
- `quantity` (PositiveIntegerField)
- `reason` (CharField)
- `month` (PositiveIntegerField)
- `year` (PositiveIntegerField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### Supplier
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `name` (CharField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### PurchaseInvoice
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `INVOICE_TYPES` (Field)
- `branch` (ForeignKey)
- `supplier` (ForeignKey)
- `invoice_number` (PositiveIntegerField)
- `invoice_type` (CharField)
- `invoice_month` (PositiveIntegerField)
- `invoice_year` (PositiveIntegerField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### PurchaseInvoiceItem
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `invoice` (ForeignKey)
- `inventory_item` (ForeignKey)
- `quantity` (PositiveIntegerField)
- `purchase_price` (DecimalField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### Receipt
- `parent_receipt` (ForeignKey)
- `receipt_type` (CharField)
- `branch` (ForeignKey)
- `salesperson` (ForeignKey)
- `receipt_number` (PositiveIntegerField)
- `client_uuid` (UUIDField)
- `receipt_hash` (CharField)
- `customer_name` (CharField)
- `phone_number` (CharField)
- `address` (CharField)
- `area` (CharField)
- `total_amount` (DecimalField)
- `down_payment` (DecimalField)
- `installment_system` (CharField)
- `sale_year` (PositiveIntegerField)
- `sale_month` (PositiveIntegerField)
- `is_cash_sale` (BooleanField)
- `products_text` (TextField)
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### SaleItem
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `receipt` (ForeignKey)
- `inventory_item` (ForeignKey)
- `quantity` (PositiveIntegerField)
- `unit_price` (DecimalField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### InstallmentPayment
- `receipt` (ForeignKey)
- `payment_date` (DateField)
- `amount` (DecimalField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### Expense
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `branch` (ForeignKey)
- `amount` (DecimalField)
- `description` (CharField)
- `expense_year` (IntegerField)
- `expense_month` (IntegerField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### CompanySetting
- `source` (CharField)
- `sync_action` (CharField)
- `is_confirmed` (BooleanField)
- `is_synced` (BooleanField)
- `name` (CharField)
- `description` (CharField)
- `phone1` (CharField)
- `phone2` (CharField)
- `footer_text` (CharField)
- `is_cloud_viewer` (BooleanField)
- `collection_commission_rate` (DecimalField)
- `zoom_level` (DecimalField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### ClientLicense
- `product_id` (IntegerField)
- `start_date` (DateField)
- `expiry_date` (DateField)
- `invoices_balance` (PositiveIntegerField)
- `is_active` (BooleanField)
- `machine_id` (CharField)
- `company_code` (IntegerField)
- `license_code_hash` (CharField)
- `is_online_active` (BooleanField)
- `online_start_date` (DateField)
- `online_expiry_date` (DateField)
- `last_checkin` (DateTimeField)
- `is_deleted` (BooleanField)
- `created_at` (DateTimeField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### UsedLicense
- `code_hash` (CharField)
- `used_at` (DateTimeField)
- `is_deleted` (BooleanField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### LicenseHistory
- `machine_id` (CharField)
- `product_name` (CharField)
- `operation_type` (CharField)
- `start_date` (DateField)
- `end_date` (DateField)
- `added_balance` (IntegerField)
- `archived_at` (DateTimeField)
- `status` (CharField)
- `is_deleted` (BooleanField)
- `objects` (ActiveManager)
- `all_objects` (AllObjectsManager)

### MonthlyInventorySnapshot
- `item` (ForeignKey)
- `year` (PositiveIntegerField)
- `month` (PositiveIntegerField)
- `closing_stock` (IntegerField)
- `closing_value` (DecimalField)
- `created_at` (DateTimeField)

## 3. Backend API Endpoints (`backend/api/urls.py`)

- `/auth/local/` -> `CustomAuthToken.as_view(`
- `/auth/demo/` -> `DemoAuthToken.as_view(`
- `/auth/recover/` -> `PasswordRecoveryView.as_view(`
- `/auth/has-password/` -> `HasPasswordView.as_view(`
- `/auth/change-password/` -> `ChangePasswordView.as_view(`
- `/license/status/` -> `LicenseStatusView.as_view(`
- `/license/activate/` -> `LicenseActivateView.as_view(`
- `/customer-suggestions/` -> `CustomerSuggestionsView.as_view(`
- `/product-suggestions/` -> `ProductSuggestionsView.as_view(`
- `/default-date/` -> `DefaultDateView.as_view(`
- `/reports/dashboard/summary/` -> `DashboardReportView.as_view(`
- `/reports/dashboard/` -> `DashboardReportView.as_view(`
- `/reports/salespersons/` -> `SalespersonPerformanceReportView.as_view(`
- `/reports/salesperson-performance/` -> `SalespersonPerformanceReportView.as_view(`
- `/reports/inventory-movement/` -> `InventoryMovementReportView.as_view(`
- `/reports/sales-pl/` -> `ProfitAndLossReportView.as_view(`
- `/reports/profit-and-loss/` -> `ProfitAndLossReportView.as_view(`
- `/reports/cash-drawer-details/` -> `CashDrawerReportView.as_view(`
- `/reports/cash-drawer/` -> `CashDrawerReportView.as_view(`
- `/reports/installments/` -> `InstallmentsReportView.as_view(`
- `/tools/backup/download/` -> `BackupDownloadView.as_view(`
- `/tools/backup/upload/` -> `BackupUploadView.as_view(`
- `/tools/sync/export-items/` -> `OfflineExportItemsView.as_view(`
- `/receipts-history-cursor/` -> `ReceiptHistoryCursorView.as_view(`
- `/receipts-next-number/` -> `ReceiptNextNumberView.as_view(`
- `/tools/sync/import-receipts/` -> `OfflineImportReceiptsView.as_view(`
- `/tools/sync/approve-pending/<int:pk>/` -> `ApprovePendingReceiptView.as_view(`
- `/` -> `include(router.urls`

## 2. Backend Views (`backend/api/views.py`)

### SoftDeleteModelViewSet
- `def destroy(self, request)`
- `def create(self, request)`
- `def perform_create(self, serializer)`

### CustomAuthToken
- `def post(self, request)`

### DemoAuthToken
- `def post(self, request)`

### PasswordRecoveryView
- `def post(self, request)`

### HasPasswordView
- `def get(self, request)`

### ChangePasswordView
- `def post(self, request)`

### BranchViewSet
- `def destroy(self, request)`

### SalespersonViewSet
- `def get_queryset(self)`
- `def destroy(self, request)`

### InventoryItemViewSet
- `def destroy(self, request)`
- `def get_queryset(self)`
- `def safe_available_qty(self, request, pk)`
- `def get_safe_available_qty(self, request, pk)`
- `def pos_search(self, request)`
- `def ledger(self, request, pk)`

### CommissionHistoryViewSet
- `def get_queryset(self)`

### InventoryAdjustmentViewSet

### SupplierViewSet
- `def destroy(self, request)`

### PurchaseInvoicePagination
- `def get_paginated_response(self, data)`

### PurchaseInvoiceViewSet
- `def get_queryset(self)`
- `def _prepare_pdf_context(self, invoice)`
- `def desktop_print(self, request)`

### PurchaseInvoiceItemViewSet

### ReceiptPagination
- `def get_paginated_response(self, data)`

### ReceiptViewSet
- `def perform_create(self, serializer)`
- `def bulk_delete(self, request)`
- `def return_receipt(self, request, pk)`
- `def printers(self, request)`
- `def desktop_print(self, request)`
- `def _prepare_pdf_context(self, receipt, inst, inst_index, total_inst)`
- `def get_queryset(self)`
- `def list(self, request)`

### SaleItemViewSet

### InstallmentPaymentViewSet

### ExpenseViewSet
- `def get_queryset(self)`

### CompanySettingViewSet

### ClientLicenseViewSet

### UsedLicenseViewSet

### LicenseHistoryViewSet

### LicenseStatusView
- `def get(self, request)`

### LicenseActivateView
- `def post(self, request)`

### CustomerSuggestionsView
- `def get(self, request)`

### ProductSuggestionsView
- `def get(self, request)`

### DefaultDateView
- `def get(self, request)`

### DashboardReportView
- `def get(self, request)`

### SalespersonPerformanceReportView
- `def get(self, request)`

### InventoryMovementReportView
- `def get(self, request)`

### ProfitAndLossReportView
- `def get(self, request)`

### CashDrawerReportView
- `def get(self, request)`

### InstallmentsReportView
- `def get(self, request)`

### ReceiptNextNumberView
- `def get(self, request)`

### ReceiptHistoryCursorView
- `def get(self, request)`

## 4. Frontend Note
- Use `find_by_name` to locate React components in `frontend/src/`.
- **Anchor Page:** `frontend/src/pages/POS.jsx`
- **Reports:** `frontend/src/pages/reports/*.jsx`
- **Utils:** `frontend/src/utils/formatUtils.js`, `frontend/src/api.js`
