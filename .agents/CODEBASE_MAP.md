# VentaPOS NextGen — Codebase Interface Map

> **This is a compressed, interface-only representation of the VentaPOS NextGen codebase (~10KB).**
> Agents must read this file instead of navigating raw source files to prevent context bloat.

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
- `category` (CharField)
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

## 2. Backend Views & ViewSets (`backend/api/views/` & `tools_views.py`)

### File: `backend\api\views\auth_views.py`

- **`CustomAuthToken`** (`post`)
- **`DemoAuthToken`** (`post`)
- **`PasswordRecoveryView`** (`post`)
- **`HasPasswordView`** (`get`)
- **`ChangePasswordView`** (`post`)

### File: `backend\api\views\base.py`

- **`SoftDeleteModelViewSet`** (`destroy, create, get_serializer_context`)

### File: `backend\api\views\dimension_views.py`

- **`BranchViewSet`** (`destroy`)
- **`SalespersonViewSet`** (`get_queryset, destroy`)
- **`SupplierViewSet`** (`destroy`)
- **`CompanySettingViewSet`**

### File: `backend\api\views\expense_views.py`

- **`ExpenseViewSet`** (`get_queryset`)

### File: `backend\api\views\inventory_views.py`

- **`InventoryItemViewSet`** (`destroy, get_queryset, list, safe_available_qty, get_safe_available_qty, pos_search, ledger`)
- **`CommissionHistoryViewSet`** (`create, get_queryset`)
- **`InventoryAdjustmentViewSet`** (`get_queryset`)

### File: `backend\api\views\license_views.py`

- **`LicenseHistoryViewSet`**
- **`LicenseStatusView`** (`get`)
- **`LicenseActivateView`** (`post`)

### File: `backend\api\views\purchase_views.py`

- **`PurchaseInvoicePagination`** (`get_paginated_response`)
- **`PurchaseInvoiceViewSet`** (`get_queryset, destroy, desktop_print`)
- **`PurchaseInvoiceItemViewSet`**

### File: `backend\api\views\receipt_views.py`

- **`ReceiptPagination`** (`get_paginated_response`)
- **`ReceiptViewSet`** (`perform_create, destroy, bulk_delete, return_receipt, printers, desktop_print, _prepare_pdf_context, get_queryset, list`)
- **`SaleItemViewSet`**
- **`InstallmentPaymentViewSet`**
- **`ReceiptNextNumberView`** (`get`)
- **`ReceiptHistoryCursorView`** (`get`)

### File: `backend\api\views\report_views.py`

- **`DefaultDateView`** (`get`)
- **`DashboardReportView`** (`get`)
- **`SalespersonPerformanceReportView`** (`get`)
- **`InventoryMovementReportView`** (`get`)
- **`ProfitAndLossReportView`** (`get`)
- **`CashDrawerReportView`** (`get`)
- **`InstallmentsReportView`** (`get`)
- **`PurchasesReportView`** (`get`)
- **`ReportDesktopPrintView`** (`post`)

### File: `backend\api\views\suggestion_views.py`

- **`CustomerSuggestionsView`** (`get`)
- **`ProductSuggestionsView`** (`get`)

### File: `backend\api\views\system_views.py`

- **`SystemCheckUpdateView`** (`get`)
- **`SystemApplyUpdateView`** (`post`)

### File: `backend\api\tools_views.py`

- **`ToolsBaseView`** (`dispatch`)
- **`BackupDownloadView`** (`get`)
- **`BackupUploadView`** (`post`)
- **`OfflineExportItemsView`** (`get`)
- **`OfflineImportReceiptsView`** (`post`)
- **`PendingReceiptsListView`** (`get`)
- **`ApprovePendingReceiptView`** (`post`)

## 3. Backend Domain Services (`backend/api/services/`)

### Service: `backend\api\services\compensation_service.py`

- `def calculate_branch_salespersons_performance(branch_id, month, year, get_cached_comm, coll_rate)`

### Service: `backend\api\services\financial_service.py`

- `def get_collection_commission_rate()`
- `def calculate_upfront_credit_reserve(credit_receipts, credit_returns, coll_rate)`
- `def calculate_cash_drawer_summary(branch_id, month, year, auto_salaries)`
- `def calculate_deficit_loss(branch_id, month, year, price_resolver)`

### Service: `backend\api\services\purchase_service.py`

- `def validate_items_stock_integrity(items, default_year, default_month)`
- `def create_purchase_invoice(validated_data, items_data)`
- `def update_purchase_invoice(instance, validated_data, items_data)`

### Service: `backend\api\services\receipt_service.py`

- `def get_next_receipt_number(branch, select_for_update)`
- `def process_return_receipt(original_receipt, data)`
- `def get_active_license(select_for_update)`
- `def get_license_date_bounds(active_lic)`
- `def create_receipt(validated_data, items_data, installments_data)`
- `def update_receipt(instance, validated_data, items_data, installments_data)`

### Service: `backend\api\services\stock_service.py`

- `def calculate_bulk_stock_timeline(items, target_month, target_year, default_month, default_year)`
- `def get_bulk_price_resolver(item_ids_or_items)`
- `def get_bulk_commission_resolver(item_ids_or_items)`
- `def resolve_price(item, month, year)`
- `def resolve_commission(item, month, year)`
- `def make_stock_getter(i_init_y, i_init_m, i_init_qty, i_deltas, i_timeline)`
- `def get_stock(m, y)`

## 4. Backend API Endpoints (`backend/api/urls.py`)

### REST Router ViewSets:
- `api/v1/company-settings/` -> `CompanySettingViewSet`
- `api/v1/branches/` -> `BranchViewSet`
- `api/v1/salespersons/` -> `SalespersonViewSet`
- `api/v1/inventory-items/` -> `InventoryItemViewSet`
- `api/v1/commission-histories/` -> `CommissionHistoryViewSet`
- `api/v1/commission-history/` -> `CommissionHistoryViewSet`
- `api/v1/inventory-adjustments/` -> `InventoryAdjustmentViewSet`
- `api/v1/suppliers/` -> `SupplierViewSet`
- `api/v1/purchase-invoices/` -> `PurchaseInvoiceViewSet`
- `api/v1/purchase-invoice-items/` -> `PurchaseInvoiceItemViewSet`
- `api/v1/expenses/` -> `ExpenseViewSet`
- `api/v1/receipts/` -> `ReceiptViewSet`
- `api/v1/sale-items/` -> `SaleItemViewSet`
- `api/v1/installment-payments/` -> `InstallmentPaymentViewSet`
- `api/v1/license-history/` -> `LicenseHistoryViewSet`

### Direct API Views:
- `api/v1/auth/local/` -> `CustomAuthToken.as_view(`
- `api/v1/auth/demo/` -> `DemoAuthToken.as_view(`
- `api/v1/auth/recover/` -> `PasswordRecoveryView.as_view(`
- `api/v1/auth/has-password/` -> `HasPasswordView.as_view(`
- `api/v1/auth/change-password/` -> `ChangePasswordView.as_view(`
- `api/v1/license/status/` -> `LicenseStatusView.as_view(`
- `api/v1/license/activate/` -> `LicenseActivateView.as_view(`
- `api/v1/customer-suggestions/` -> `CustomerSuggestionsView.as_view(`
- `api/v1/product-suggestions/` -> `ProductSuggestionsView.as_view(`
- `api/v1/default-date/` -> `DefaultDateView.as_view(`
- `api/v1/reports/dashboard/summary/` -> `DashboardReportView.as_view(`
- `api/v1/reports/dashboard/` -> `DashboardReportView.as_view(`
- `api/v1/reports/salespersons/` -> `SalespersonPerformanceReportView.as_view(`
- `api/v1/reports/salesperson-performance/` -> `SalespersonPerformanceReportView.as_view(`
- `api/v1/reports/inventory-movement/` -> `InventoryMovementReportView.as_view(`
- `api/v1/reports/sales-pl/` -> `ProfitAndLossReportView.as_view(`
- `api/v1/reports/profit-and-loss/` -> `ProfitAndLossReportView.as_view(`
- `api/v1/reports/cash-drawer-details/` -> `CashDrawerReportView.as_view(`
- `api/v1/reports/cash-drawer/` -> `CashDrawerReportView.as_view(`
- `api/v1/reports/installments/` -> `InstallmentsReportView.as_view(`
- `api/v1/reports/purchases/` -> `PurchasesReportView.as_view(`
- `api/v1/reports/desktop_print/` -> `ReportDesktopPrintView.as_view(`
- `api/v1/tools/backup/download/` -> `BackupDownloadView.as_view(`
- `api/v1/tools/backup/upload/` -> `BackupUploadView.as_view(`
- `api/v1/receipts-history-cursor/` -> `ReceiptHistoryCursorView.as_view(`
- `api/v1/receipts-next-number/` -> `ReceiptNextNumberView.as_view(`
- `api/v1/tools/sync/export-items/` -> `OfflineExportItemsView.as_view(`
- `api/v1/tools/sync/import-receipts/` -> `OfflineImportReceiptsView.as_view(`
- `api/v1/tools/sync/pending-receipts/` -> `PendingReceiptsListView.as_view(`
- `api/v1/pending-external-receipts/` -> `PendingReceiptsListView.as_view(`
- `api/v1/tools/sync/approve-pending/<int:pk>/` -> `ApprovePendingReceiptView.as_view(`
- `api/v1/system/check-update/` -> `SystemCheckUpdateView.as_view(`
- `api/v1/system/apply-update/` -> `SystemApplyUpdateView.as_view(`
- `api/v1/frontend-logs/` -> `FrontendLogView.as_view(`
- `api/v1/` -> `include(router.urls`

## 5. Serializers, Middleware & Print Utils

### `backend/api/serializers.py`
- Classes: `BranchSerializer, SalespersonSerializer, InventoryItemSerializer, CommissionHistorySerializer, InventoryAdjustmentSerializer, SupplierSerializer, PurchaseInvoiceItemSerializer, PurchaseInvoiceSerializer, SaleItemSerializer, InstallmentPaymentSerializer, ReceiptSerializer, ExpenseSerializer, CompanySettingSerializer, ClientLicenseSerializer, UsedLicenseSerializer, LicenseHistorySerializer, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta, Meta`
- Functions: `get_current_stock, to_internal_value, validate, create, create, update, to_internal_value, to_internal_value, get_has_returns, to_internal_value, validate, create, update, update, create`

### `backend/api/middleware.py`
- Classes: `LicenseEnforcementMiddleware`

### `backend/api/print_utils.py`
- Functions: `clean_invoices_directory, to_arabic_numerals, to_english_numerals, ed2ad, get_wkhtmltopdf_config, get_save_directory, get_num_to_words_ar, generate_and_open_pdf`

## 6. Frontend Architecture (`frontend/src/`)

### Pages (`frontend/src/pages/`):
- `ActivationSetup.jsx`
- `BranchSelection.jsx`
- `Dimensions.jsx`
- `Expenses.jsx`
- `Login.jsx`
- `POS.jsx`
- `ProductLedger.jsx`
- `PurchaseEntry.jsx`
- `reports\AveragesReport.jsx`
- `reports\DashboardReport.jsx`
- `reports\ExpensesReport.jsx`
- `reports\InstallmentsReport.jsx`
- `reports\InventoryMovementReport.jsx`
- `reports\ProfitAndLossReport.jsx`
- `reports\PurchasesReport.jsx`
- `reports\ReceiptsReport.jsx`
- `reports\ReportsLayout.jsx`
- `reports\SalespersonPerformanceReport.jsx`
- `ReturnReceipt.jsx`
- `SearchPurchases.jsx`
- `SearchReceipts.jsx`
- `settings\SettingsIndex.jsx`
- `settings\tabs\CompanyTab.jsx`
- `settings\tabs\SecurityTab.jsx`
- `settings\tabs\SubscriptionTab.jsx`
- `tools\BackupTab.jsx`
- `tools\SyncTab.jsx`
- `tools\ToolsDashboard.jsx`

### Components (`frontend/src/components/`):
- `AppShell.jsx`
- `Autocomplete.jsx`
- `common\AppAutocomplete.jsx`
- `common\ConfirmModal.jsx`
- `common\MonthYearPicker.jsx`
- `common\PrintModal.jsx`
- `common\QuickRestoreModal.jsx`
- `common\StandardTablePageLayout.jsx`
- `common\UpdateModal.jsx`
- `common\UserManualModal.jsx`
- `DebouncedInput.jsx`
- `DemoBanner.jsx`
- `GlobalErrorBoundary.jsx`
- `InventoryTab.jsx`
- `ledger\LedgerCommissionForm.jsx`
- `ledger\LedgerDeficitForm.jsx`
- `ledger\LedgerHeader.jsx`
- `ledger\LedgerMetricsCards.jsx`
- `ledger\LedgerTimelineTable.jsx`
- `Navbar.jsx`
- `pos\POSCustomerForm.jsx`
- `pos\POSInstallmentBox.jsx`
- `pos\POSItemsTable.jsx`
- `pos\POSTotalsSummary.jsx`
- `purchases\PurchaseContextMenu.jsx`
- `purchases\PurchaseFilterToolbar.jsx`
- `purchases\PurchaseHeader.jsx`
- `purchases\PurchaseInvoiceRow.jsx`
- `purchases\PurchaseItemForm.jsx`
- `purchases\PurchaseItemsTable.jsx`
- `purchases\PurchaseTable.jsx`
- `purchases\SuggestionList.jsx`
- `receipts\ReceiptContextMenu.jsx`
- `receipts\ReceiptRow.jsx`
- `receipts\ReceiptsFilterToolbar.jsx`
- `receipts\ReceiptsTable.jsx`
- `ReportAutocomplete.jsx`
- `ReportTable.jsx`
- `SalespersonsTab.jsx`
- `settings\LicenseKeyInput.jsx`
- `settings\MachineIdDisplay.jsx`
- `SubscriptionWarningBanner.jsx`
- `SuppliersTab.jsx`

### Custom Hooks (`frontend/src/hooks/`):
- `useDefaultDate.js`
- `useSalespersons.js`
- `useSmartScroll.js`

