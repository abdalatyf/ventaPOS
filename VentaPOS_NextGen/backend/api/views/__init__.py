"""
Views package for VentaPOS NextGen Backend.
Re-exports all ViewSets, APIViews, pagination classes, and helper functions
for complete backwards compatibility across URLs, serializers, and tests.
"""
from .base import (
    SoftDeleteModelViewSet,
    to_english_numerals,
    to_arabic_numerals,
    get_default_date,
    is_date_within_subscription,
    resolve_salesperson_id,
    get_collection_commission_rate,
)
from .auth_views import (
    CustomAuthToken,
    DemoAuthToken,
    PasswordRecoveryView,
    HasPasswordView,
    ChangePasswordView,
)
from .dimension_views import (
    BranchViewSet,
    SalespersonViewSet,
    SupplierViewSet,
    CompanySettingViewSet,
)
from .inventory_views import (
    InventoryItemViewSet,
    CommissionHistoryViewSet,
    InventoryAdjustmentViewSet,
)
from .purchase_views import (
    PurchaseInvoicePagination,
    PurchaseInvoiceViewSet,
    PurchaseInvoiceItemViewSet,
)
from .receipt_views import (
    ReceiptPagination,
    ReceiptViewSet,
    SaleItemViewSet,
    InstallmentPaymentViewSet,
    ReceiptNextNumberView,
    ReceiptHistoryCursorView,
)
from .expense_views import (
    ExpenseViewSet,
)
from .license_views import (
    LicenseHistoryViewSet,
    LicenseStatusView,
    LicenseActivateView,
)
from .suggestion_views import (
    CustomerSuggestionsView,
    ProductSuggestionsView,
)
from .report_views import (
    DefaultDateView,
    DashboardReportView,
    SalespersonPerformanceReportView,
    InventoryMovementReportView,
    ProfitAndLossReportView,
    CashDrawerReportView,
    InstallmentsReportView,
    PurchasesReportView,
    ReportDesktopPrintView,
)
from .system_views import (
    SystemCheckUpdateView,
    SystemApplyUpdateView,
)

__all__ = [
    # Base & helpers
    "SoftDeleteModelViewSet",
    "to_english_numerals",
    "to_arabic_numerals",
    "get_default_date",
    "is_date_within_subscription",
    "resolve_salesperson_id",
    "get_collection_commission_rate",
    # Auth
    "CustomAuthToken",
    "DemoAuthToken",
    "PasswordRecoveryView",
    "HasPasswordView",
    "ChangePasswordView",
    # Dimensions
    "BranchViewSet",
    "SalespersonViewSet",
    "SupplierViewSet",
    "CompanySettingViewSet",
    # Inventory
    "InventoryItemViewSet",
    "CommissionHistoryViewSet",
    "InventoryAdjustmentViewSet",
    # Purchases
    "PurchaseInvoicePagination",
    "PurchaseInvoiceViewSet",
    "PurchaseInvoiceItemViewSet",
    # Receipts
    "ReceiptPagination",
    "ReceiptViewSet",
    "SaleItemViewSet",
    "InstallmentPaymentViewSet",
    "ReceiptNextNumberView",
    "ReceiptHistoryCursorView",
    # Expenses
    "ExpenseViewSet",
    # Licenses
    "LicenseHistoryViewSet",
    "LicenseStatusView",
    "LicenseActivateView",
    # Suggestions
    "CustomerSuggestionsView",
    "ProductSuggestionsView",
    # Reports
    "DefaultDateView",
    "DashboardReportView",
    "SalespersonPerformanceReportView",
    "InventoryMovementReportView",
    "ProfitAndLossReportView",
    "CashDrawerReportView",
    "InstallmentsReportView",
    "PurchasesReportView",
    "ReportDesktopPrintView",
    # System & Auto-updater
    "SystemCheckUpdateView",
    "SystemApplyUpdateView",
]
