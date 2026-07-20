from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanySettingViewSet, BranchViewSet, SalespersonViewSet, InventoryItemViewSet,
    CommissionHistoryViewSet, InventoryAdjustmentViewSet, SupplierViewSet,
    PurchaseInvoiceViewSet, PurchaseInvoiceItemViewSet, ReceiptViewSet,
    SaleItemViewSet, InstallmentPaymentViewSet, PendingExternalReceiptViewSet,
    ClientLicenseViewSet, UsedLicenseViewSet, LicenseHistoryViewSet,
    LicenseStatusView, LicenseActivateView, CustomAuthToken,
    DemoAuthToken, PasswordRecoveryView, ChangePasswordView, HasPasswordView,
    CustomerSuggestionsView, ProductSuggestionsView,
    DashboardReportView, SalespersonPerformanceReportView, InventoryMovementReportView,
    ProfitAndLossReportView, CashDrawerReportView, DefaultDateView, InstallmentsReportView
)
from .views import ExpenseViewSet
from .tools_views import (
    BackupDownloadView, BackupUploadView, OfflineExportItemsView,
    OfflineImportReceiptsView, ApprovePendingReceiptView, SmartImportWizardView
)

router = DefaultRouter()
router.register(r'company-settings', CompanySettingViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'salespersons', SalespersonViewSet)
router.register(r'inventory-items', InventoryItemViewSet)
router.register(r'commission-histories', CommissionHistoryViewSet, basename='commission-histories')
router.register(r'inventory-adjustments', InventoryAdjustmentViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'purchase-invoices', PurchaseInvoiceViewSet)
router.register(r'purchase-invoice-items', PurchaseInvoiceItemViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'receipts', ReceiptViewSet)
router.register(r'sale-items', SaleItemViewSet)
router.register(r'installment-payments', InstallmentPaymentViewSet)
router.register(r'pending-external-receipts', PendingExternalReceiptViewSet)
router.register(r'client-licenses', ClientLicenseViewSet)
router.register(r'used-licenses', UsedLicenseViewSet)
router.register(r'license-history', LicenseHistoryViewSet)

urlpatterns = [
    # Removed system_init as per new flow
    path('auth/local/', CustomAuthToken.as_view(), name='auth_local'),
    path('auth/demo/', DemoAuthToken.as_view(), name='auth_demo'),
    path('auth/recover/', PasswordRecoveryView.as_view(), name='auth_recover'),
    path('auth/has-password/', HasPasswordView.as_view(), name='auth_has_password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('license/status/', LicenseStatusView.as_view(), name='license-status'),
    path('license/activate/', LicenseActivateView.as_view(), name='license-activate'),
    path('customer-suggestions/', CustomerSuggestionsView.as_view(), name='customer-suggestions'),
    path('product-suggestions/', ProductSuggestionsView.as_view(), name='product-suggestions'),
    path('default-date/', DefaultDateView.as_view(), name='default-date'),
    path('reports/dashboard/summary/', DashboardReportView.as_view(), name='report-dashboard-summary'),
    path('reports/dashboard/', DashboardReportView.as_view(), name='report-dashboard-alias'),
    path('reports/salespersons/', SalespersonPerformanceReportView.as_view(), name='report-salespersons'),
    path('reports/salesperson-performance/', SalespersonPerformanceReportView.as_view(), name='report-salesperson-performance-alias'),
    path('reports/inventory-movement/', InventoryMovementReportView.as_view(), name='report-inventory-movement'),
    path('reports/sales-pl/', ProfitAndLossReportView.as_view(), name='report-sales-pl'),
    path('reports/profit-and-loss/', ProfitAndLossReportView.as_view(), name='report-profit-and-loss-alias'),
    path('reports/cash-drawer-details/', CashDrawerReportView.as_view(), name='report-cash-drawer-details'),
    path('reports/cash-drawer/', CashDrawerReportView.as_view(), name='report-cash-drawer-alias'),
    path('reports/installments/', InstallmentsReportView.as_view(), name='report-installments'),
    
    # Tools APIs
    path('tools/backup/download/', BackupDownloadView.as_view(), name='backup-download'),
    path('tools/backup/upload/', BackupUploadView.as_view(), name='backup-upload'),
    path('tools/sync/export-items/', OfflineExportItemsView.as_view(), name='sync-export-items'),
    path('tools/sync/import-receipts/', OfflineImportReceiptsView.as_view(), name='sync-import-receipts'),
    path('tools/sync/approve-pending/<int:pk>/', ApprovePendingReceiptView.as_view(), name='sync-approve-pending'),
    path('tools/smart-import/', SmartImportWizardView.as_view(), name='smart-import'),

    path('', include(router.urls)),
]

