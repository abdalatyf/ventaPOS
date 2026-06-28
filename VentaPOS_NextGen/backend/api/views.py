"""
views.py — VentaPOS NextGen Backend
=====================================
ViewSets and API Views for the VentaPOS NextGen backend.

Architecture:
  - Every ModelViewSet injects `tenant` into serializer context so serializers
    can enforce tenant isolation without relying on the client to supply a
    tenant_id in the request body.
  - Default querysets filter `is_deleted=False` via the `ActiveManager`.
  - Soft-delete is performed via a custom `destroy()` override that sets
    `is_deleted=True` instead of running `DELETE`.
  - The `TenantFromRequestMixin` resolves the tenant from the request headers
    (X-Company-Code) or JWT payload, providing the single source of truth for
    multi-tenancy at the view level.

Endpoints implemented:
  Standard CRUD ViewSets (one per model):
    /api/v1/tenants/
    /api/v1/cloud-users/
    /api/v1/branches/
    /api/v1/salespeople/
    /api/v1/inventory/
    /api/v1/commission-history/
    /api/v1/inventory-adjustments/
    /api/v1/suppliers/
    /api/v1/purchase-invoices/
    /api/v1/purchase-invoice-items/
    /api/v1/receipts/
    /api/v1/sale-items/
    /api/v1/installment-payments/
    /api/v1/expenses/
    /api/v1/company-settings/
    /api/v1/client-licenses/
    /api/v1/used-licenses/
    /api/v1/license-history/
    /api/v1/pending-external-receipts/

  Special API Views (per api_contract.md):
    POST /api/v1/auth/viewer/          → ViewerAuthView
    POST /api/v1/sync/push/            → SyncPushView
    GET|POST /api/v1/sync/pull/        → SyncPullView
    POST /api/v1/sync/confirm-receipts/→ ConfirmReceiptsView
    GET  /api/v1/license/status/       → LicenseStatusView
    POST /api/v1/license/activate/     → LicenseActivateView
    GET  /api/v1/inventory/{pk}/stock/ → safe_available_qty action
    GET  /api/v1/inventory/{pk}/ledger/→ ledger action
"""

import hashlib
import uuid
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets, views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import (
    ActionLog,
    Branch,
    ClientLicense,
    CloudUser,
    CommissionHistory,
    CompanySetting,
    Expense,
    InstallmentPayment,
    InventoryAdjustment,
    InventoryItem,
    LicenseHistory,
    PendingExternalReceipt,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    Salesperson,
    Supplier,
    Tenant,
    UsedLicense,
)
from .serializers import (
    ActionLogSerializer,
    BranchSerializer,
    ClientLicenseSerializer,
    CloudUserSerializer,
    CommissionHistorySerializer,
    CompanySettingSerializer,
    ExpenseSerializer,
    InstallmentPaymentSerializer,
    InventoryAdjustmentSerializer,
    InventoryItemSerializer,
    LicenseHistorySerializer,
    PendingExternalReceiptSerializer,
    PurchaseInvoiceItemSerializer,
    PurchaseInvoiceSerializer,
    ReceiptSerializer,
    SaleItemSerializer,
    SalespersonSerializer,
    SupplierSerializer,
    TenantSerializer,
    UsedLicenseSerializer,
)
from .utils.license_validator import LicenseValidator
from .utils.security_utils import (
    generate_record_signature,
    generate_receipt_signature,
    get_machine_id,
)


# ===========================================================================
# Tenant resolution mixin
# ===========================================================================

class TenantFromRequestMixin:
    """
    Resolves the active tenant from:
      1. JWT payload's `tenant_id` claim (cloud viewer sessions).
      2. `X-Company-Code` header (local device sync sessions).

    Raises HTTP 404 if the company code is unknown or HTTP 403 if the
    tenant is inactive.
    """

    def _get_tenant(self):
        # Try X-Company-Code header first (device sync flow)
        company_code = self.request.headers.get("X-Company-Code")
        if company_code:
            try:
                tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
            except Tenant.DoesNotExist:
                raise ValidationError({
                    "company_code": (
                        "رمز الشركة المكتوب غير مسجل في الدفتر، يرجى التحقق من الرقم."
                    )
                })
            if not tenant.is_active:
                raise ValidationError({
                    "company_code": (
                        "الاشتراك السحابي للشركة انتهى أو معطل، يرجى التجديد لتتمكن من الدخول."
                    )
                })
            return tenant

        # Fall back to JWT claim
        tenant_id = getattr(getattr(self.request, "auth", None), "tenant_id", None)
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_deleted=False)
            except Tenant.DoesNotExist:
                raise ValidationError({"tenant": "Tenant not found."})

        raise ValidationError({
            "auth": (
                "بيانات الدخول ناقصة، يرجى كتابة رمز الشركة واسم المستخدم كاملاً."
            )
        })

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tenant"] = self._get_tenant()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = self._get_tenant()
        return qs.filter(tenant=tenant)


# ===========================================================================
# Base soft-delete ViewSet
# ===========================================================================

class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    """
    Override destroy() to perform a soft-delete (is_deleted=True) instead
    of a permanent SQL DELETE, per schema §1.2.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """Inject tenant from context into every create call."""
        context = self.get_serializer_context()
        tenant = context.get("tenant")
        if tenant:
            serializer.save(tenant=tenant)
        else:
            serializer.save()


# ===========================================================================
# Standard CRUD ViewSets
# ===========================================================================

class TenantViewSet(SoftDeleteModelViewSet):
    """
    Tenant management — typically admin-only.
    Does NOT use TenantFromRequestMixin (tenant IS the root entity).
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def perform_create(self, serializer):
        serializer.save()


class CloudUserViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = CloudUser.objects.select_related("tenant").all()
    serializer_class = CloudUserSerializer


class BranchViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = Branch.objects.select_related("tenant").all()
    serializer_class = BranchSerializer


class SalespersonViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = Salesperson.objects.select_related("tenant", "branch").all()
    serializer_class = SalespersonSerializer


class InventoryItemViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = InventoryItem.objects.select_related("tenant", "branch").all()
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch_local_id = self.request.query_params.get("branch_id")
        if branch_local_id:
            qs = qs.filter(branch__local_id=branch_local_id)
        return qs

    # ------------------------------------------------------------------
    # Custom action: safe available quantity (pessimistic time projection)
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="stock")
    def safe_available_qty(self, request, pk=None):
        item = self.get_object()

        try:
            req_month = int(request.query_params.get("month", timezone.now().month))
            req_year = int(request.query_params.get("year", timezone.now().year))
        except ValueError:
            return Response(
                {"error": "قيم الشهر أو السنة غير صحيحة، يرجى إدخال أرقام صحيحة."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build month-by-month change map
        changes = {}
        changes[(item.initial_year, item.initial_month)] = item.initial_quantity

        for sale in SaleItem.objects.filter(inventory_item=item, is_deleted=False).select_related("receipt"):
            key = (sale.receipt.sale_year, sale.receipt.sale_month)
            changes[key] = changes.get(key, 0) - sale.quantity

        for purchase in PurchaseInvoiceItem.objects.filter(
            inventory_item=item, is_deleted=False
        ).select_related("purchase_invoice"):
            key = (
                purchase.purchase_invoice.invoice_year,
                purchase.purchase_invoice.invoice_month,
            )
            if purchase.purchase_invoice.invoice_type == "RETURN":
                changes[key] = changes.get(key, 0) - purchase.quantity
            else:
                changes[key] = changes.get(key, 0) + purchase.quantity

        for adj in InventoryAdjustment.objects.filter(inventory_item=item, is_deleted=False):
            key = (adj.adjustment_year, adj.adjustment_month)
            if adj.adjustment_type == "SURPLUS":
                changes[key] = changes.get(key, 0) + adj.quantity
            else:
                changes[key] = changes.get(key, 0) - adj.quantity

        if not changes:
            return Response({"safe_available_qty": 0})

        min_key = min(changes.keys())
        max_key = max(max(changes.keys()), (req_year, req_month))

        cy, cm = min_key
        ey, em = max_key

        running = 0
        balances = {}
        while (cy, cm) <= (ey, em):
            key = (cy, cm)
            running += changes.get(key, 0)
            balances[key] = running
            cm += 1
            if cm > 12:
                cm = 1
                cy += 1

        future = [
            b for k, b in balances.items()
            if k[0] > req_year or (k[0] == req_year and k[1] >= req_month)
        ]
        safe_qty = min(future) if future else running

        return Response({"safe_available_qty": safe_qty})

    # ------------------------------------------------------------------
    # Custom action: full stock ledger with monthly summary
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="ledger")
    def ledger(self, request, pk=None):
        item = self.get_object()
        timeline = []

        timeline.append({
            "type": "INITIAL",
            "year": item.initial_year,
            "month": item.initial_month,
            "quantity": item.initial_quantity,
            "price": str(item.initial_purchase_price),
            "description": "رصيد افتتاحي",
            "sort_key": (item.initial_year, item.initial_month, 0, 0),
        })

        for p in PurchaseInvoiceItem.objects.filter(
            inventory_item=item, is_deleted=False
        ).select_related("purchase_invoice", "purchase_invoice__supplier"):
            timeline.append({
                "type": p.purchase_invoice.invoice_type,
                "year": p.purchase_invoice.invoice_year,
                "month": p.purchase_invoice.invoice_month,
                "quantity": p.quantity,
                "price": str(p.purchase_price),
                "invoice_number": p.purchase_invoice.invoice_number,
                "supplier": p.purchase_invoice.supplier.name,
                "sort_key": (
                    p.purchase_invoice.invoice_year,
                    p.purchase_invoice.invoice_month,
                    1,
                    p.purchase_invoice.invoice_number,
                ),
            })

        for s in SaleItem.objects.filter(
            inventory_item=item, is_deleted=False
        ).select_related("receipt"):
            timeline.append({
                "type": "SALE",
                "year": s.receipt.sale_year,
                "month": s.receipt.sale_month,
                "quantity": s.quantity,
                "price": str(s.unit_price),
                "receipt_number": s.receipt.receipt_number,
                "is_cash_sale": s.receipt.is_cash_sale,
                "receipt_total": str(s.receipt.total_amount),
                "receipt_down_payment": str(s.receipt.down_payment),
                "sort_key": (
                    s.receipt.sale_year,
                    s.receipt.sale_month,
                    2,
                    s.receipt.receipt_number,
                ),
            })

        for adj in InventoryAdjustment.objects.filter(inventory_item=item, is_deleted=False):
            timeline.append({
                "type": f"ADJUSTMENT_{adj.adjustment_type}",
                "year": adj.adjustment_year,
                "month": adj.adjustment_month,
                "quantity": adj.quantity,
                "reason": adj.reason,
                "sort_key": (adj.adjustment_year, adj.adjustment_month, 3, 0),
            })

        timeline.sort(key=lambda x: x["sort_key"])
        for m in timeline:
            del m["sort_key"]

        monthly_summary_dict = {}
        dashboard_metrics = {
            "cash_profit": 0.0,
            "installment_profit": 0.0,
            "total_profit": 0.0,
        }

        avg_cost = 0.0
        current_qty = 0

        for m in timeline:
            ym = f"{m['year']}-{m['month']:02d}"
            if ym not in monthly_summary_dict:
                monthly_summary_dict[ym] = {
                    "year": m["year"],
                    "month": m["month"],
                    "incoming": 0,
                    "outgoing": 0,
                }

            price = float(m.get("price", 0))

            if m["type"] == "INITIAL":
                current_qty += m["quantity"]
                avg_cost = price
                monthly_summary_dict[ym]["incoming"] += m["quantity"]

            elif m["type"] == "PURCHASE":
                total_val = (current_qty * avg_cost) + (m["quantity"] * price)
                current_qty += m["quantity"]
                avg_cost = total_val / current_qty if current_qty > 0 else 0.0
                monthly_summary_dict[ym]["incoming"] += m["quantity"]

            elif m["type"] == "RETURN":
                total_val = (current_qty * avg_cost) - (m["quantity"] * price)
                current_qty -= m["quantity"]
                avg_cost = total_val / current_qty if current_qty > 0 else 0.0
                monthly_summary_dict[ym]["outgoing"] += m["quantity"]

            elif m["type"] == "ADJUSTMENT_SURPLUS":
                current_qty += m["quantity"]
                monthly_summary_dict[ym]["incoming"] += m["quantity"]

            elif m["type"] == "ADJUSTMENT_DEFICIT":
                current_qty -= m["quantity"]
                monthly_summary_dict[ym]["outgoing"] += m["quantity"]

            elif m["type"] == "SALE":
                cogs = m["quantity"] * avg_cost
                revenue = m["quantity"] * price
                gross = revenue - cogs
                commission = float(item.get_commission_at_date(m["month"], m["year"]))
                total_commission = m["quantity"] * commission
                monthly_summary_dict[ym]["outgoing"] += m["quantity"]

                if m.get("is_cash_sale"):
                    net = gross - total_commission
                    dashboard_metrics["cash_profit"] += net
                else:
                    receipt_total = float(m.get("receipt_total", 0))
                    receipt_dp = float(m.get("receipt_down_payment", 0))
                    coll_comm = (
                        revenue * (receipt_total - receipt_dp) * 0.10 / receipt_total
                        if receipt_total > 0
                        else 0.0
                    )
                    net = gross - total_commission - coll_comm
                    dashboard_metrics["installment_profit"] += net

                current_qty -= m["quantity"]

        dashboard_metrics["total_profit"] = (
            dashboard_metrics["cash_profit"] + dashboard_metrics["installment_profit"]
        )
        monthly_summary = [v for _, v in sorted(monthly_summary_dict.items())]

        return Response({
            "timeline": timeline,
            "monthly_summary": monthly_summary,
            "dashboard_metrics": dashboard_metrics,
        })


class CommissionHistoryViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = CommissionHistory.objects.select_related("tenant", "inventory_item").all()
    serializer_class = CommissionHistorySerializer

    def get_queryset(self):
        qs = super().get_queryset().order_by("-activation_year", "-activation_month")
        item_id = self.request.query_params.get("item_id")
        if item_id:
            qs = qs.filter(inventory_item__local_id=item_id)
        return qs


class InventoryAdjustmentViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = InventoryAdjustment.objects.select_related("tenant", "inventory_item").all()
    serializer_class = InventoryAdjustmentSerializer


class SupplierViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = Supplier.objects.select_related("tenant").all()
    serializer_class = SupplierSerializer


class PurchaseInvoiceViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = PurchaseInvoice.objects.select_related(
        "tenant", "branch", "supplier"
    ).prefetch_related("items").all()
    serializer_class = PurchaseInvoiceSerializer


class PurchaseInvoiceItemViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = PurchaseInvoiceItem.objects.select_related(
        "tenant", "purchase_invoice", "inventory_item"
    ).all()
    serializer_class = PurchaseInvoiceItemSerializer


class ReceiptViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = Receipt.objects.select_related(
        "tenant", "branch", "salesperson"
    ).prefetch_related("sale_items", "installment_payments").all()
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if branch_id := params.get("branch_id"):
            qs = qs.filter(branch__local_id=branch_id)
        if salesperson_id := params.get("salesperson_id"):
            qs = qs.filter(salesperson__local_id=salesperson_id)
        if (is_cash := params.get("is_cash_sale")) is not None:
            qs = qs.filter(is_cash_sale=is_cash.lower() == "true")
        return qs


class SaleItemViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = SaleItem.objects.select_related(
        "tenant", "receipt", "inventory_item"
    ).all()
    serializer_class = SaleItemSerializer


class InstallmentPaymentViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = InstallmentPayment.objects.select_related("tenant", "receipt").all()
    serializer_class = InstallmentPaymentSerializer


class ExpenseViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = Expense.objects.select_related("tenant", "branch").all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if branch_id := params.get("branch_id"):
            qs = qs.filter(branch__local_id=branch_id)
        if year := params.get("year"):
            qs = qs.filter(expense_year=year)
        if month := params.get("month"):
            qs = qs.filter(expense_month=month)
        return qs


class CompanySettingViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = CompanySetting.objects.select_related("tenant").all()
    serializer_class = CompanySettingSerializer


class ClientLicenseViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = ClientLicense.objects.select_related("tenant").all()
    serializer_class = ClientLicenseSerializer


class UsedLicenseViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = UsedLicense.objects.select_related("tenant").all()
    serializer_class = UsedLicenseSerializer


class LicenseHistoryViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = LicenseHistory.objects.select_related("tenant").all()
    serializer_class = LicenseHistorySerializer


class PendingExternalReceiptViewSet(TenantFromRequestMixin, SoftDeleteModelViewSet):
    queryset = PendingExternalReceipt.objects.select_related("tenant", "branch").all()
    serializer_class = PendingExternalReceiptSerializer


class ActionLogViewSet(viewsets.ModelViewSet):
    """Legacy — read-only view of the action log."""
    queryset = ActionLog.objects.all().order_by("-created_at")
    serializer_class = ActionLogSerializer
    http_method_names = ["get", "head", "options"]


# ===========================================================================
# Special API Views
# ===========================================================================

class ViewerAuthView(views.APIView):
    """
    POST /api/v1/auth/viewer/
    Authenticate a cloud user (viewer/manager) by company_code + credentials.
    Returns master machine_id and user metadata.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        company_code = request.data.get("company_code", "").strip()
        username = request.data.get("username", "").strip()
        password_hash = request.data.get("password_hash", "").strip()

        if not all([company_code, username, password_hash]):
            return Response(
                {
                    "status": "error",
                    "message": (
                        "بيانات الدخول ناقصة، يرجى كتابة رمز الشركة "
                        "واسم المستخدم كاملاً."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "رمز الشركة المكتوب غير مسجل في الدفتر، يرجى التحقق من الرقم.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not tenant.is_active:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "الاشتراك السحابي للشركة انتهى أو معطل، "
                        "يرجى التجديد لتتمكن من الدخول."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate online license
        active_lic = ClientLicense.objects.filter(
            tenant=tenant,
            is_active=True,
            is_online_active=True,
            is_deleted=False,
        ).order_by("-online_expiry_date").first()

        if not active_lic or (
            active_lic.online_expiry_date and active_lic.online_expiry_date < date.today()
        ):
            return Response(
                {
                    "status": "error",
                    "message": (
                        "الاشتراك السحابي للشركة انتهى أو معطل، "
                        "يرجى التجديد لتتمكن من الدخول."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user = CloudUser.objects.get(
                tenant=tenant,
                username=username,
                password_hash=password_hash,
                is_deleted=False,
            )
        except CloudUser.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "غير مصرح بالدخول، يرجى التحقق من اسم المستخدم "
                        "أو كلمة المرور الخاصة بالخزنة."
                    ),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {
                    "status": "error",
                    "message": "حساب المستخدم معطل، يرجى التواصل مع مدير الشركة.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            "status": "success",
            "master_machine_id": active_lic.machine_id,
            "user": {
                "username": f"{company_code}-{username}",
                "role": user.role,
            },
        })


class SyncPushView(views.APIView):
    """
    POST /api/v1/sync/push/
    Atomic ingestion of local device data payload.
    Processes: company_settings, branches, salespeople, inventory,
               receipts (with items & installments), expenses.
    """

    def post(self, request):
        company_code = request.headers.get("X-Company-Code", "").strip()
        machine_id_header = request.headers.get("X-Machine-ID", "").strip()

        if not company_code:
            return Response(
                {
                    "status": "error",
                    "message": "بيانات الدخول ناقصة، يرجى إرسال رمز الشركة في الترويسة.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "رمز الشركة المكتوب غير مسجل في الدفتر.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify device license
        active_lic = ClientLicense.objects.filter(
            tenant=tenant,
            machine_id=machine_id_header,
            is_active=True,
            is_deleted=False,
        ).first()

        if not active_lic:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "الاشتراك السحابي انتهى، يرجى التجديد "
                        "لتتمكن من مزامنة الفواتير."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if active_lic.expiry_date and active_lic.expiry_date < date.today():
            return Response(
                {
                    "status": "error",
                    "message": (
                        "الاشتراك السحابي انتهى، يرجى التجديد "
                        "لتتمكن من مزامنة الفواتير."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        payload = request.data.get("payload", {})
        receipts_processed = 0

        try:
            with transaction.atomic():
                # --- Company settings ---
                cs_data = payload.get("company_settings")
                if cs_data:
                    CompanySetting.objects.update_or_create(
                        tenant=tenant,
                        defaults={
                            "name": cs_data.get("name", ""),
                            "description": cs_data.get("description", ""),
                            "phone1": cs_data.get("phone1", ""),
                            "phone2": cs_data.get("phone2", ""),
                            "footer_text": cs_data.get("footer_text", ""),
                        },
                    )

                # --- Branches ---
                for b in payload.get("branches", []):
                    Branch.objects.update_or_create(
                        tenant=tenant,
                        local_id=b["id"],
                        defaults={"name": b["name"]},
                    )

                # --- Salespeople ---
                for s in payload.get("salespeople", []):
                    try:
                        branch = Branch.objects.get(
                            tenant=tenant, local_id=s["branch_id"], is_deleted=False
                        )
                    except Branch.DoesNotExist:
                        continue
                    Salesperson.objects.update_or_create(
                        tenant=tenant,
                        local_id=s["id"],
                        defaults={"name": s["name"], "branch": branch},
                    )

                # --- Inventory ---
                for inv in payload.get("inventory", []):
                    try:
                        branch = Branch.objects.get(
                            tenant=tenant, local_id=inv["branch_id"], is_deleted=False
                        )
                    except Branch.DoesNotExist:
                        continue
                    InventoryItem.objects.update_or_create(
                        tenant=tenant,
                        local_id=inv["id"],
                        defaults={
                            "branch": branch,
                            "name": inv.get("name", ""),
                            "initial_quantity": inv.get("quantity", 0),
                            "initial_purchase_price": inv.get("purchase_price", "0.00"),
                            "initial_commission_amount": inv.get("commission", "0.00"),
                            "initial_month": inv.get("initial_month", timezone.now().month),
                            "initial_year": inv.get("initial_year", timezone.now().year),
                        },
                    )

                # --- Receipts ---
                for r in payload.get("receipts", []):
                    receipt_hash = r.get("receipt_hash", "")
                    if not receipt_hash:
                        continue

                    # Idempotency: skip if already processed
                    client_uuid_str = r.get("client_uuid") or str(uuid.uuid4())
                    if Receipt.all_objects.filter(
                        tenant=tenant, receipt_hash=receipt_hash
                    ).exists():
                        receipts_processed += 1
                        continue

                    try:
                        branch = Branch.objects.get(
                            tenant=tenant, local_id=r["branch_id"], is_deleted=False
                        )
                    except Branch.DoesNotExist:
                        continue

                    salesperson = None
                    if r.get("salesperson_id"):
                        salesperson = Salesperson.objects.filter(
                            tenant=tenant, local_id=r["salesperson_id"], is_deleted=False
                        ).first()

                    receipt = Receipt.objects.create(
                        tenant=tenant,
                        branch=branch,
                        salesperson=salesperson,
                        local_id=r.get("id", 0),
                        receipt_number=r.get("receipt_number", 0),
                        client_uuid=client_uuid_str,
                        receipt_hash=receipt_hash,
                        customer_name=r.get("customer_name", ""),
                        phone_number=r.get("phone_number", ""),
                        address=r.get("address", ""),
                        area=r.get("area", ""),
                        total_amount=r.get("total_amount", "0.00"),
                        down_payment=r.get("down_payment", "0.00"),
                        installment_system=r.get("installment_system", ""),
                        sale_year=r.get("sale_year", timezone.now().year),
                        sale_month=r.get("sale_month", timezone.now().month),
                        is_cash_sale=r.get("is_cash_sale", False),
                        is_confirmed=False,
                        created_at_local=r.get("created_at", timezone.now()),
                    )

                    for item_data in r.get("items", []):
                        inv_item = InventoryItem.objects.filter(
                            tenant=tenant,
                            local_id=item_data["product_id"],
                            is_deleted=False,
                        ).first()
                        if inv_item:
                            SaleItem.objects.create(
                                tenant=tenant,
                                receipt=receipt,
                                inventory_item=inv_item,
                                quantity=item_data.get("quantity", 0),
                                unit_price=item_data.get("price", "0.00"),
                            )

                    for inst in r.get("installments", []):
                        InstallmentPayment.objects.create(
                            tenant=tenant,
                            receipt=receipt,
                            payment_date=inst["payment_date"],
                            amount=inst.get("amount", "0.00"),
                        )

                    receipts_processed += 1

                # --- Expenses ---
                for exp in payload.get("expenses", []):
                    try:
                        branch = Branch.objects.get(
                            tenant=tenant, local_id=exp["branch_id"], is_deleted=False
                        )
                    except Branch.DoesNotExist:
                        continue
                    Expense.objects.create(
                        tenant=tenant,
                        branch=branch,
                        amount=exp.get("amount", "0.00"),
                        description=exp.get("description", ""),
                        expense_year=exp.get("expense_year", timezone.now().year),
                        expense_month=exp.get("expense_month", timezone.now().month),
                        created_at_local=exp.get("created_at", timezone.now()),
                    )

        except Exception as exc:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "بيانات الفاتورة غير مطابقة أو ناقصة، يرجى مراجعة الدفتر "
                        "والتأكد من حقول الأقساط وتواريخها."
                    ),
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "success",
                "message": "تم مزامنة البيانات وحفظ الفواتير بالدفتر بنجاح.",
                "receipts_processed": receipts_processed,
            },
            status=status.HTTP_201_CREATED,
        )


class SyncPullView(views.APIView):
    """
    GET|POST /api/v1/sync/pull/
    Returns entity updates since `last_sync`.
    Applies the SQLite↔PostgreSQL field translation layer (api_contract.md §3).
    """

    def _handle(self, request, data):
        machine_id = data.get("machine_id", "").strip()
        last_sync_str = data.get("last_sync")
        company_code = data.get(
            "company_code",
            request.headers.get("X-Company-Code", ""),
        ).strip()

        if not machine_id or not last_sync_str:
            return Response(
                {
                    "status": "error",
                    "message": "يجب إرسال machine_id وlast_sync في الطلب.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response(
                {"status": "error", "message": "رمز الشركة غير موجود."},
                status=status.HTTP_404_NOT_FOUND,
            )

        active_lic = ClientLicense.objects.filter(
            tenant=tenant,
            machine_id=machine_id,
            is_active=True,
            is_deleted=False,
        ).first()

        if not active_lic:
            return Response(
                {
                    "status": "error",
                    "message": (
                        "الاشتراك السحابي غير فعال، يرجى مراجعة إدارة الترخيص بالشركة."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.utils.dateparse import parse_datetime
        last_sync = parse_datetime(last_sync_str)
        if not last_sync:
            return Response(
                {"status": "error", "message": "صيغة last_sync غير صحيحة."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Products (translated to SQLite field names)
        products = []
        for item in InventoryItem.objects.filter(
            tenant=tenant, is_deleted=False, created_at__gte=last_sync
        ):
            products.append({
                "id": item.local_id,
                "name": item.name,
                "branch_id": item.branch.local_id,
                "initial_quantity": item.initial_quantity,
                "initial_purchase_price": str(item.initial_purchase_price),
                "initial_commission_amount": str(item.initial_commission_amount),
                "initial_month": item.initial_month,
                "initial_year": item.initial_year,
            })

        # Receipts (translated to SQLite field names)
        receipts = []
        salesperson_filter = data.get("salesperson_id")
        receipt_qs = Receipt.objects.filter(
            tenant=tenant, is_deleted=False, created_at__gte=last_sync
        )
        if salesperson_filter:
            receipt_qs = receipt_qs.filter(salesperson__local_id=salesperson_filter)

        for rec in receipt_qs.select_related("branch", "salesperson"):
            receipts.append({
                "id": rec.local_id,
                "receipt_hash": rec.receipt_hash,
                "receipt_number": rec.receipt_number,
                "branch_id": rec.branch.local_id,
                "salesperson_id": rec.salesperson.local_id if rec.salesperson else None,
                "customer_name": rec.customer_name,
                "phone_number": rec.phone_number,
                "address": rec.address,
                "area": rec.area,
                "total_amount": str(rec.total_amount),
                "down_payment": str(rec.down_payment),
                "is_cash_sale": rec.is_cash_sale,
                "sale_month": rec.sale_month,
                "sale_year": rec.sale_year,
                "created_at": rec.created_at_local.isoformat() if rec.created_at_local else None,
            })

        # Branches
        branches = []
        for br in Branch.objects.filter(
            tenant=tenant, is_deleted=False, created_at__gte=last_sync
        ):
            branches.append({"id": br.local_id, "name": br.name})

        # Salespeople
        users = []
        for sp in Salesperson.objects.filter(
            tenant=tenant, is_deleted=False, created_at__gte=last_sync
        ).select_related("branch"):
            users.append({
                "id": sp.local_id,
                "name": sp.name,
                "branch_id": sp.branch.local_id,
            })

        # Expenses
        expenses = []
        for exp in Expense.objects.filter(
            tenant=tenant, is_deleted=False, created_at__gte=last_sync
        ).select_related("branch"):
            expenses.append({
                "id": str(exp.id),
                "branch_id": exp.branch.local_id,
                "amount": str(exp.amount),
                "description": exp.description,
                "expense_year": exp.expense_year,
                "expense_month": exp.expense_month,
                "created_at": exp.created_at_local.isoformat() if exp.created_at_local else None,
            })

        # Installments
        installments = []
        for inst in InstallmentPayment.objects.filter(
            tenant=tenant,
            is_deleted=False,
            created_at__gte=last_sync,
        ).select_related("receipt"):
            installments.append({
                "id": str(inst.id),
                "receipt_id": inst.receipt.local_id,
                "payment_date": inst.payment_date.isoformat(),
                "amount": str(inst.amount),
            })

        return Response({
            "status": "success",
            "products": products,
            "receipts": receipts,
            "expenses": expenses,
            "installments": installments,
            "branches": branches,
            "users": users,
        })

    def get(self, request):
        return self._handle(request, request.query_params)

    def post(self, request):
        return self._handle(request, request.data)


class ConfirmReceiptsView(views.APIView):
    """
    POST /api/v1/sync/confirm-receipts/
    Master POS marks mobile-submitted receipts as confirmed.
    """

    def post(self, request):
        machine_id = request.headers.get("X-Machine-ID", "").strip()
        company_code = request.headers.get("X-Company-Code", "").strip()
        receipt_hashes = request.data.get("receipt_hashes", [])

        if not machine_id:
            return Response(
                {
                    "status": "error",
                    "message": "غير مصرح للجهاز بتأكيد الحساب المالي، يرجى مراجعة إدارة الخزنة.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response(
                {"status": "error", "message": "رمز الشركة غير موجود."},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated = Receipt.objects.filter(
            tenant=tenant,
            receipt_hash__in=receipt_hashes,
            is_deleted=False,
        ).update(is_confirmed=True)

        return Response({"status": "success", "updated_count": updated})


class LicenseStatusView(views.APIView):
    """
    GET /api/v1/license/status/
    Returns current license balance and expiry for a tenant.
    """

    def get(self, request):
        company_code = request.headers.get("X-Company-Code", "").strip()
        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response({"status": "inactive", "message": "رمز الشركة غير موجود."})

        active_lics = ClientLicense.objects.filter(
            tenant=tenant, is_active=True, is_deleted=False
        )
        if not active_lics.exists():
            return Response({"status": "inactive", "message": "لا توجد تراخيص نشطة."})

        total_balance = sum(lic.invoices_balance for lic in active_lics)
        latest = active_lics.order_by("-expiry_date").first()

        return Response({
            "status": "active",
            "total_invoices_balance": total_balance,
            "expiry_date": latest.expiry_date if latest else None,
        })


class LicenseActivateView(views.APIView):
    """
    POST /api/v1/license/activate/
    Validate and activate a license code for a device.
    """

    def post(self, request):
        license_code = request.data.get("license_code", "").strip()
        company_code = request.headers.get("X-Company-Code", "").strip()
        machine_id = request.headers.get("X-Machine-ID", "").strip()

        if not license_code:
            return Response(
                {"error": "license_code مطلوب."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(company_code=company_code, is_deleted=False)
        except Tenant.DoesNotExist:
            return Response(
                {"error": "رمز الشركة غير موجود."},
                status=status.HTTP_404_NOT_FOUND,
            )

        code_hash = hashlib.sha256(license_code.encode()).hexdigest()
        if UsedLicense.objects.filter(code_hash=code_hash, is_deleted=False).exists():
            return Response(
                {"error": "هذا الكود مستخدم من قبل، يرجى إدخال كود جديد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = LicenseValidator.validate(license_code, machine_id)
        if not result.get("valid"):
            return Response(
                {"error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date = date(result["start_year"], result["start_month"], 1)
        expiry_date = date(result["start_year"] + 1, result["start_month"], 1)
        invoices_balance = result.get("invoices_balance", 5000)
        is_active = True

        new_sig = generate_record_signature(
            expiry_date,
            invoices_balance,
            machine_id,
            result["product_id"],
            is_active,
        )

        with transaction.atomic():
            ClientLicense.objects.create(
                tenant=tenant,
                product_id=result["product_id"],
                start_date=start_date,
                expiry_date=expiry_date,
                invoices_balance=invoices_balance,
                is_active=is_active,
                machine_id=machine_id,
                company_code=company_code,
                license_code_hash=new_sig,
            )
            UsedLicense.objects.create(tenant=tenant, code_hash=code_hash)

            LicenseHistory.objects.create(
                tenant=tenant,
                machine_id=machine_id,
                product_name=f"Product {result['product_id']}",
                operation_type="ACTIVATE",
                start_date=start_date,
                end_date=expiry_date,
                added_balance=invoices_balance,
                status="SUCCESS",
            )

        return Response(
            {"status": "success", "message": "تم تفعيل الترخيص بنجاح."},
            status=status.HTTP_201_CREATED,
        )
