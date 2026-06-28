from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanySettingViewSet, BranchViewSet, SalespersonViewSet, InventoryItemViewSet,
    CommissionHistoryViewSet, InventoryAdjustmentViewSet, SupplierViewSet,
    PurchaseInvoiceViewSet, PurchaseInvoiceItemViewSet, ReceiptViewSet,
    SaleItemViewSet, InstallmentPaymentViewSet, PendingExternalReceiptViewSet,
    ClientLicenseViewSet, UsedLicenseViewSet, LicenseHistoryViewSet, ActionLogViewSet,
    LicenseStatusView, LicenseActivateView
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
router.register(r'receipts', ReceiptViewSet)
router.register(r'sale-items', SaleItemViewSet)
router.register(r'installment-payments', InstallmentPaymentViewSet)
router.register(r'pending-external-receipts', PendingExternalReceiptViewSet)
router.register(r'client-licenses', ClientLicenseViewSet)
router.register(r'used-licenses', UsedLicenseViewSet)
router.register(r'license-history', LicenseHistoryViewSet)
router.register(r'action-logs', ActionLogViewSet)

urlpatterns = [
    path('license/status/', LicenseStatusView.as_view(), name='license-status'),
    path('license/activate/', LicenseActivateView.as_view(), name='license-activate'),
    path('', include(router.urls)),
]
