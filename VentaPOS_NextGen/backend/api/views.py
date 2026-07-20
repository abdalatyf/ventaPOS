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
from datetime import date, timedelta

from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import status, viewsets, views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination

from .models import (
    Branch,
    ClientLicense,
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
    UsedLicense,
)
from .serializers import (
    BranchSerializer,
    ClientLicenseSerializer,
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

    def create(self, request, *args, **kwargs):
        """Auto-fill branch if missing."""
        from api.models import Branch
        if isinstance(request.data, dict) or hasattr(request.data, 'copy'):
            data = request.data.copy()
            if 'branch' not in data:
                branch = None
                if request.headers.get("X-Branch-ID"):
                    branch = Branch.objects.filter(id=request.headers.get("X-Branch-ID"), is_deleted=False).first()
                if not branch:
                    branch = Branch.objects.filter(is_deleted=False).first()
                if branch:
                    data['branch'] = branch.id
        else:
            data = request.data
            
        from rest_framework.response import Response
        from rest_framework import status
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        try:
            serializer.save()
        except IntegrityError as e:
            print(f"IntegrityError in perform_create: {e}")
            if "UNIQUE constraint failed" in str(e):
                raise ValidationError({"name": ["الاسم ده متسجل قبل كده، أو موجود في سلة المهملات."]})
            raise ValidationError({"error": [f"حدث خطأ في قاعدة البيانات: {e}"]})
        except IntegrityError as e:
            print(f"IntegrityError in perform_create: {e}")
            if "UNIQUE constraint failed" in str(e):
                raise ValidationError({"name": ["الاسم ده متسجل قبل كده، أو موجود في سلة المهملات."]})
            raise ValidationError({"error": [f"حدث خطأ في قاعدة البيانات: {e}"]})


from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # We only need password for the local master PC
        password = request.data.get('password')
        if not password:
            return Response({"error": "يرجى إدخال كلمة المرور"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the first admin user
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            return Response({"error": "النظام غير مهيأ بعد. يرجى إعداد النظام."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user.check_password(password):
            return Response({"error": "كلمة المرور غير صحيحة"}, status=status.HTTP_401_UNAUTHORIZED)
            
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'company_name': tenant.name if tenant else "VentaPOS",
            'is_cloud': False
        })

class DemoAuthToken(views.APIView):
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        from api.models import ClientLicense
        if ClientLicense.objects.filter(is_active=True).exclude(machine_id="DEMO_MACHINE").exists():
            return Response({"error": "النظام مفعل مسبقاً، الرجاء تسجيل الدخول العادي."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # Fallback if somehow missing
            user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True})
            
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'company_name': 'نسخة تجريبية VentaPOS',
            'is_cloud': False
        })

class PasswordRecoveryView(views.APIView):
    permission_classes = []
    
    def post(self, request):
        recovery_code = request.data.get('recovery_code')
        new_password = request.data.get('new_password')
        if not recovery_code or not new_password:
            return Response({"error": "الرجاء إدخال كود الاسترداد وكلمة المرور الجديدة"}, status=400)
            
        from django.contrib.auth.hashers import check_password
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user or not admin_user.last_name:
            return Response({"error": "لا يوجد كود استرداد مسجل في النظام."}, status=400)
            
        if check_password(recovery_code, admin_user.last_name):
            admin_user.set_password(new_password)
            admin_user.save()
            return Response({"message": "تم تغيير كلمة المرور بنجاح."})
        else:
            return Response({"error": "كود الاسترداد غير صحيح."}, status=400)
class HasPasswordView(views.APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "غير مصرح لك"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"has_password": user.has_usable_password() and user.check_password("") is False})

class ChangePasswordView(views.APIView):
    def post(self, request):
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        
        if old_password is None or new_password is None:
            return Response({"error": "بيانات غير صالحة"}, status=400)
        
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "غير مصرح لك"}, status=status.HTTP_401_UNAUTHORIZED)

        has_password = user.has_usable_password() and user.check_password("") is False
        
        if has_password and not user.check_password(old_password):
            return Response({"error": "كلمة المرور الحالية غير صحيحة"}, status=400)
            
        user.set_password(new_password)
        user.save()
        msg = "تم تغيير كلمة المرور بنجاح." if new_password else "تم إلغاء كلمة المرور، ستتمكن من الدخول مباشرة."
        return Response({"message": msg})

# ===========================================================================
# Standard ViewSets
# ===========================================================================

class BranchViewSet(SoftDeleteModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        from django.db import transaction
        with transaction.atomic():
            from api.models import SaleItem, InstallmentPayment, PurchaseInvoiceItem, CommissionHistory, InventoryAdjustment, Receipt, PurchaseInvoice, InventoryItem, Expense, TemporaryReceipt, Salesperson
            
            # 1. SaleItems & Payments
            SaleItem.all_objects.filter(receipt__branch=instance).delete()
            InstallmentPayment.all_objects.filter(receipt__branch=instance).delete()
            # 2. Receipts
            Receipt.all_objects.filter(branch=instance).delete()
            
            # 3. PurchaseInvoiceItems
            PurchaseInvoiceItem.all_objects.filter(invoice__branch=instance).delete()
            # 4. PurchaseInvoices
            PurchaseInvoice.all_objects.filter(branch=instance).delete()
            
            # 5. CommissionHistory & Adjustments
            CommissionHistory.all_objects.filter(item__branch=instance).delete()
            InventoryAdjustment.all_objects.filter(item__branch=instance).delete()
            
            # 6. InventoryItems & Expenses & Temp
            InventoryItem.all_objects.filter(branch=instance).delete()
            Expense.all_objects.filter(branch=instance).delete()
            TemporaryReceipt.all_objects.filter(branch=instance).delete()
            
            # 7. Salespersons
            Salesperson.all_objects.filter(branch=instance).delete()
            
            # Finally, delete the branch itself permanently (Hard delete overrides the SoftDeleteViewSet)
            instance.delete()
            
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalespersonViewSet(SoftDeleteModelViewSet):
    queryset = Salesperson.objects.select_related("branch").all()
    serializer_class = SalespersonSerializer


class InventoryItemViewSet(SoftDeleteModelViewSet):
    queryset = InventoryItem.objects.select_related("branch").all()
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id_param = self.request.query_params.get("branch_id")
        if branch_id_param:
            try:
                # If it's a UUID (NextGen React frontend)
                uuid_val = int(branch_id_param)
                qs = qs.filter(branch__id=uuid_val)
            except ValueError:
                # If it's an integer (Legacy Sync script)
                qs = qs.filter(branch__id=branch_id_param)
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

        default_year, default_month = get_default_date_for_tenant(item.tenant)
        safe_qty = item.get_safe_available_qty(req_month, req_year, default_month, default_year)

        return Response({"safe_available_qty": safe_qty})

    @action(detail=True, methods=["get"], url_path="get_safe_available_qty")
    def get_safe_available_qty(self, request, pk=None):
        return self.safe_available_qty(request, pk)

    @action(detail=False, methods=["get"], url_path="pos_search")
    def pos_search(self, request):
        term = request.query_params.get("term", "").strip()
        if not term:
            return Response([])

        try:
            req_month = int(request.query_params.get("month", timezone.now().month))
            req_year = int(request.query_params.get("year", timezone.now().year))
        except ValueError:
            return Response(
                {"error": "قيم الشهر أو السنة غير صحيحة، يرجى إدخال أرقام صحيحة."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(name__icontains=term)[:20]
        default_year, default_month = get_default_date_for_tenant(tenant)
        
        results = []
        for item in qs:
            safe_stock = item.get_safe_available_qty(req_month, req_year, default_month, default_year)
            results.append({
                "id": item.id,
                "name": item.name,
                "max": safe_stock,
            })
            
        return Response(results)

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
        ).select_related("invoice", "invoice__supplier"):
            timeline.append({
                "type": p.invoice.invoice_type,
                "year": p.invoice.invoice_year,
                "month": p.invoice.invoice_month,
                "quantity": p.quantity,
                "price": str(p.purchase_price),
                "invoice_number": p.invoice.invoice_number,
                "supplier": p.invoice.supplier.name,
                "sort_key": (
                    p.invoice.invoice_year,
                    p.invoice.invoice_month,
                    1,
                    p.invoice.invoice_number,
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
                "year": adj.year,
                "month": adj.month,
                "quantity": adj.quantity,
                "reason": adj.reason,
                "sort_key": (adj.year, adj.month, 3, 0),
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
                avg_cost = total_val // current_qty if current_qty > 0 else 0
                monthly_summary_dict[ym]["incoming"] += m["quantity"]

            elif m["type"] == "RETURN":
                total_val = (current_qty * avg_cost) - (m["quantity"] * price)
                current_qty -= m["quantity"]
                avg_cost = total_val // current_qty if current_qty > 0 else 0
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
                        revenue * (receipt_total - receipt_dp) // (100 * receipt_total)
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


class CommissionHistoryViewSet(SoftDeleteModelViewSet):
    queryset = CommissionHistory.objects.select_related("inventory_item").all()
    serializer_class = CommissionHistorySerializer

    def get_queryset(self):
        qs = super().get_queryset().order_by("-activation_year", "-activation_month")
        item_id = self.request.query_params.get("item_id")
        if item_id:
            qs = qs.filter(inventory_item__id=item_id)
        return qs


class InventoryAdjustmentViewSet(SoftDeleteModelViewSet):
    queryset = InventoryAdjustment.objects.select_related("inventory_item").all()
    serializer_class = InventoryAdjustmentSerializer


class SupplierViewSet(SoftDeleteModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseInvoicePagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        from django.db.models import Sum, F
        # Calculate total cost by multiplying quantity by purchase_price for all items in these invoices
        total_purchases = PurchaseInvoiceItem.objects.filter(
            invoice__in=self.page.paginator.object_list
        ).aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )["total"] or 0
        all_ids = list(self.page.paginator.object_list.values_list('id', flat=True))
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "aggregate": {"total_purchases": total_purchases},
            "all_ids": all_ids,
            "results": data
        })

class PurchaseInvoiceViewSet(SoftDeleteModelViewSet):
    queryset = PurchaseInvoice.objects.select_related(
        "branch", "supplier"
    ).prefetch_related("items").all()
    serializer_class = PurchaseInvoiceSerializer
    pagination_class = PurchaseInvoicePagination

    def get_queryset(self):
        qs = super().get_queryset().order_by("-created_at")
        supplier_id = self.request.query_params.get("supplier")
        invoice_number = self.request.query_params.get("invoice_number")
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        invoice_type = self.request.query_params.get("invoice_type")

        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if invoice_number:
            qs = qs.filter(invoice_number=invoice_number)
        if month:
            qs = qs.filter(invoice_month=month)
        if year:
            qs = qs.filter(invoice_year=year)
        if invoice_type and invoice_type != "ALL":
            qs = qs.filter(invoice_type=invoice_type)
        return qs

    def _prepare_pdf_context(self, invoice):
        from api.models import CompanySetting
        from api.utils.format_utils import to_arabic_numerals, ed2ad
        
        company_settings = CompanySetting.objects.filter().first()
        items = list(invoice.items.all())
        
        total_amount = sum((item.quantity * item.purchase_price) for item in items)
        
        context = {
            "invoice": invoice,
            "company_settings": company_settings,
            "items": items,
            "total_amount": ed2ad(str(int(total_amount))),
            "invoice_date": invoice.created_at.strftime("%Y-%m-%d %I:%M %p") if invoice.created_at else f"{invoice.invoice_year}-{invoice.invoice_month:02d}",
        }
        return context

    @action(detail=False, methods=["post"])
    def desktop_print(self, request):
        invoice_ids = request.data.get("invoice_ids", [])
        action_type = request.data.get("action", "print") # 'print' or 'view'
        target_printer = request.data.get("target_printer", None)
        
        if not isinstance(invoice_ids, list) or not invoice_ids:
            return Response({"error": "invoice_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        invoices = self.get_queryset().filter(id__in=invoice_ids)
        if not invoices.exists():
            return Response({"error": "No valid invoices found"}, status=status.HTTP_404_NOT_FOUND)

        from django.template.loader import render_to_string
        from .print_utils import generate_and_open_pdf

        pages_html = []
        for invoice in invoices:
            ctx = self._prepare_pdf_context(invoice)
            part = render_to_string('api/pdf_purchase_content.html', ctx)
            pages_html.append(part)

        full_content_body = '<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>'.join(pages_html)
        final_html = render_to_string('api/pdf_base.html', {'content': full_content_body})

        if action_type == 'view':
            success, result_msg = generate_and_open_pdf(
                html_content=final_html,
                target_printer=None,
                open_pdf=True
            )
            if success:
                return Response({"status": "success", "message": "تم فتح الـ PDF لمعاينته"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": f"فشل في إنشاء أو فتح الـ PDF: {result_msg}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            success, msg = generate_and_open_pdf(
                html_content=final_html,
                target_printer=target_printer,
                open_pdf=False
            )
            if success:
                return Response({"status": "success", "message": "تم إرسال الفواتير للطباعة"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": f"فشل في الطباعة: {msg}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PurchaseInvoiceItemViewSet(SoftDeleteModelViewSet):
    queryset = PurchaseInvoiceItem.objects.select_related(
        "invoice", "inventory_item"
    ).all()
    serializer_class = PurchaseInvoiceItemSerializer


class ReceiptPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        from django.db.models import Sum
        total_sales = self.page.paginator.object_list.aggregate(total=Sum("total_amount"))["total"] or 0
        all_ids = list(self.page.paginator.object_list.values_list('id', flat=True))
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "aggregate": {"total_sales": total_sales},
            "all_ids": all_ids,
            "results": data
        })


class ReceiptViewSet(SoftDeleteModelViewSet):
    queryset = Receipt.objects.select_related(
        "branch", "salesperson"
    ).prefetch_related("sale_items", "payments").all()
    serializer_class = ReceiptSerializer
    pagination_class = ReceiptPagination

    def perform_create(self, serializer):
        from django.db import transaction
        from api.models import ClientLicense
        from api.utils.security_utils import generate_record_signature, get_machine_id
        from rest_framework.exceptions import PermissionDenied

        with transaction.atomic():
            # Decrement license balance securely
            machine_id = get_machine_id()
            
            # Lock the active licenses for update to prevent race conditions
            active_lics = ClientLicense.objects.select_for_update().filter(
                is_active=True, is_deleted=False
            ).order_by('expiry_date')

            deducted = False
            for lic in active_lics:
                if lic.invoices_balance > 0:
                    lic.invoices_balance -= 1
                    # Recalculate signature to prevent tampering middleware from flagging it
                    lic.license_code_hash = generate_record_signature(
                        lic.expiry_date,
                        lic.invoices_balance,
                        lic.machine_id,
                        lic.product_id,
                        lic.is_active,
                    )
                    lic.save()
                    deducted = True
                    break
            
            if not deducted:
                raise PermissionDenied("Invoice balance exhausted. Please renew your license.")

            serializer.save(tenant=tenant)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        receipt_ids = request.data.get("receipt_ids", [])
        if not isinstance(receipt_ids, list):
            return Response({"error": "receipt_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete
        Receipt.objects.filter(id__in=receipt_ids).update(is_deleted=True)
        return Response({"status": "success", "deleted_count": len(receipt_ids)}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def printers(self, request):
        import subprocess
        try:
            # استخدام PowerShell لاسترجاع أسماء الطابعات لضمان عدم حدوث مشاكل مع pywin32
            result = subprocess.run(["powershell", "Get-Printer | Select-Object -ExpandProperty Name"], capture_output=True, text=True, check=True)
            printers = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return Response({"printers": printers}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"فشل في جلب الطابعات: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def desktop_print(self, request):
        receipt_ids = request.data.get("receipt_ids", [])
        action_type = request.data.get("action", "print") # 'print' or 'view'
        target_printer = request.data.get("target_printer", None)
        
        if not isinstance(receipt_ids, list) or not receipt_ids:
            return Response({"error": "receipt_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        receipts = self.get_queryset().filter(id__in=receipt_ids).prefetch_related('payments')
        if not receipts.exists():
            return Response({"error": "No valid receipts found"}, status=status.HTTP_404_NOT_FOUND)

        from django.template.loader import render_to_string
        from .print_utils import generate_and_open_pdf, ed2ad

        company_settings = CompanySetting.objects.filter().first()
        pages_html = []

        for receipt in receipts:
            installments_from_db = list(receipt.payments.filter(is_deleted=False).order_by('payment_date'))
            total_installments = len(installments_from_db)
            paid_so_far = receipt.down_payment

            if receipt.is_cash_sale:
                ctx = self._prepare_pdf_context(receipt)
                ctx['company_settings'] = company_settings
                part = render_to_string('api/pdf_invoice_content.html', ctx)
                pages_html.append(part)
            else:
                if not installments_from_db:
                    # Fallback if no installments
                    ctx = self._prepare_pdf_context(receipt)
                    ctx['company_settings'] = company_settings
                    part = render_to_string('api/pdf_invoice_content.html', ctx)
                    pages_html.append(part)
                else:
                    for i, inst in enumerate(installments_from_db):
                        total = int(receipt.total_amount)
                        if str(total)[-1] in ("1", "6"): total -= 1
                        elif str(total)[-1] in ("9", "4"): total += 1

                        paid_so_far += inst.amount
                        rem = total - paid_so_far
                        rem_text = ed2ad(str(rem)) if rem > 0 else "خالص"

                        ctx = self._prepare_pdf_context(receipt, inst, i + 1, total_installments)
                        ctx['remaining_amount'] = rem_text
                        ctx['company_settings'] = company_settings

                        part = render_to_string('api/pdf_invoice_content.html', ctx)
                        pages_html.append(part)

        full_content_body = '<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>'.join(pages_html)
        final_html = render_to_string('api/pdf_base.html', {'content': full_content_body})

        if action_type == "view":
            success, result_msg = generate_and_open_pdf(
                final_html, "View_Receipts", 
                target_printer=None, action="view", paper_size="DL"
            )
            if success:
                return Response({"status": "success", "message": result_msg}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": result_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            # Batch Printing Logic is now handled by the Frontend chunking
            success, msg = generate_and_open_pdf(
                final_html, "Batch_Receipts", 
                target_printer=target_printer, action="print", paper_size="DL"
            )
            
            if success:
                return Response({"status": "success", "message": msg}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_pdf_context(self, receipt, inst=None, inst_index=1, total_inst=1):
        from .print_utils import ed2ad, to_arabic_numerals, get_num_to_words_ar
        from django.utils import timezone

        total = receipt.total_amount
        rem_amount = total - receipt.down_payment if not receipt.is_cash_sale else 0
        
        return {
            'receipt_number': ed2ad(str(receipt.receipt_number)),
            'current_installment_index': ed2ad(str(inst_index)) if inst_index else '',
            'company_settings': {
                'name': receipt.branch.name if receipt.branch else '',
                'description': '',
                'phone1': '',
                'phone2': '',
                'footer_text': ''
            },
            'total_amount': ed2ad(str(total)),
            'area': receipt.area or '',
            'total_installments_count': ed2ad(str(total_inst)) if not receipt.is_cash_sale else '',
            'down_payment': ed2ad(str(receipt.down_payment)),
            'customer_name': receipt.customer_name,
            'remaining_amount': ed2ad(str(rem_amount)),
            'address': receipt.address or '',
            'phone_number': ed2ad(str(receipt.phone_number)) if receipt.phone_number else '',
            'amount_to_pay': ed2ad(str(inst.amount)) if inst else ed2ad(str(total)),
            'amount_in_words': get_num_to_words_ar(int(inst.amount if inst else total)),
            'payment_date': ed2ad(inst.payment_date.strftime("%Y/%m/%d")) if inst and inst.payment_date else ed2ad(receipt.created_at.strftime("%Y/%m/%d")),
            'products_text': receipt.products_text or '',
            'sale_date': ed2ad(receipt.created_at.strftime("%Y/%m/%d")),
            'installment_system': receipt.installment_system or ('كاش' if receipt.is_cash_sale else ''),
            'salesperson_name': receipt.salesperson.name if receipt.salesperson else '',
        }


    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # branch_id: filter branch__id=branch_id or branch_id=branch_id
        if branch_id_param := params.get("branch_id"):
            if str(branch_id_param).strip():
                clean_branch_id = to_english_numerals(str(branch_id_param).strip())
                try:
                    uuid_val = int(clean_branch_id)
                    qs = qs.filter(branch_id=uuid_val)
                except ValueError:
                    qs = qs.filter(branch__id=clean_branch_id)

        # salesperson_id / salesperson: filter salesperson__id=salesperson_id or salesperson_id=salesperson_id
        if sp_param := (params.get("salesperson_id") or params.get("salesperson")):
            if str(sp_param).strip():
                clean_sp_id = to_english_numerals(str(sp_param).strip())
                try:
                    uuid_val = int(clean_sp_id)
                    qs = qs.filter(salesperson_id=uuid_val)
                except ValueError:
                    qs = qs.filter(salesperson__id=clean_sp_id)

        # year: filter sale_year=to_english_numerals(year)
        if year := params.get("year"):
            if str(year).strip():
                clean_year = to_english_numerals(str(year).strip())
                qs = qs.filter(sale_year=clean_year)

        # month: filter sale_month=to_english_numerals(month)
        if month := params.get("month"):
            if str(month).strip():
                clean_month = to_english_numerals(str(month).strip())
                qs = qs.filter(sale_month=clean_month)

        # receipt_from: filter receipt_number__gte=to_english_numerals(receipt_from)
        if receipt_from := params.get("receipt_from"):
            if str(receipt_from).strip():
                clean_rf = to_english_numerals(str(receipt_from).strip())
                qs = qs.filter(receipt_number__gte=clean_rf)

        # receipt_to: filter receipt_number__lte=to_english_numerals(receipt_to)
        if receipt_to := params.get("receipt_to"):
            if str(receipt_to).strip():
                clean_rt = to_english_numerals(str(receipt_to).strip())
                qs = qs.filter(receipt_number__lte=clean_rt)

        # customer_name: filter customer_name__icontains=customer_name
        if customer_name := params.get("customer_name"):
            if str(customer_name).strip():
                qs = qs.filter(customer_name__icontains=str(customer_name).strip())

        # phone / phone_number: filter phone_number__icontains=to_english_numerals(phone)
        if phone_param := (params.get("phone") or params.get("phone_number")):
            if str(phone_param).strip():
                clean_phone = to_english_numerals(str(phone_param).strip())
                qs = qs.filter(phone_number__icontains=clean_phone)

        # address: filter address__icontains=address
        if address := params.get("address"):
            if str(address).strip():
                qs = qs.filter(address__icontains=str(address).strip())

        # area: filter area__icontains=area
        if area := params.get("area"):
            if str(area).strip():
                qs = qs.filter(area__icontains=str(area).strip())

        # is_cash_sale: filter is_cash_sale=(is_cash_sale.lower() == 'true') if provided and non-empty
        if (is_cash := params.get("is_cash_sale")) is not None:
            is_cash_str = str(is_cash).strip()
            if is_cash_str != "":
                qs = qs.filter(is_cash_sale=(is_cash_str.lower() == "true"))

        # has_down_payment: filter down_payment__gt=0
        if (has_down_payment := params.get("has_down_payment")) is not None:
            if str(has_down_payment).strip().lower() == "true":
                qs = qs.filter(is_cash_sale=False, down_payment__gt=0)

        return qs.order_by("-created_at", "-id")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        from django.db.models import Sum
        total_sum = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['total_amount_sum'] = float(total_sum)
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'total_amount_sum': float(total_sum)
        })


class SaleItemViewSet(SoftDeleteModelViewSet):
    queryset = SaleItem.objects.select_related(
        "receipt", "inventory_item"
    ).all()
    serializer_class = SaleItemSerializer


class InstallmentPaymentViewSet(SoftDeleteModelViewSet):
    queryset = InstallmentPayment.objects.select_related("receipt").all()
    serializer_class = InstallmentPaymentSerializer


class ExpenseViewSet(SoftDeleteModelViewSet):
    queryset = Expense.objects.select_related("branch").all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if branch_id := params.get("branch_id"):
            qs = qs.filter(branch__id=branch_id)
        if year := params.get("year"):
            qs = qs.filter(expense_year=year)
        if month := params.get("month"):
            qs = qs.filter(expense_month=month)
        return qs


class CompanySettingViewSet(SoftDeleteModelViewSet):
    queryset = CompanySetting.objects.all()
    serializer_class = CompanySettingSerializer


class ClientLicenseViewSet(SoftDeleteModelViewSet):
    queryset = ClientLicense.objects.all()
    serializer_class = ClientLicenseSerializer


class UsedLicenseViewSet(SoftDeleteModelViewSet):
    queryset = UsedLicense.objects.all()
    serializer_class = UsedLicenseSerializer


class LicenseHistoryViewSet(SoftDeleteModelViewSet):
    queryset = LicenseHistory.objects.all()
    serializer_class = LicenseHistorySerializer


class PendingExternalReceiptViewSet(SoftDeleteModelViewSet):
    queryset = PendingExternalReceipt.objects.select_related("branch").all()
    serializer_class = PendingExternalReceiptSerializer


class LicenseStatusView(views.APIView):
    """
    GET /api/v1/license/status/
    Returns current license balance and expiry for a tenant.
    """

    def get(self, request):
        from api.utils.security_utils import get_machine_id
        import datetime
        
        machine_id = get_machine_id()
        active_lics = ClientLicense.objects.filter(is_active=True, is_deleted=False)

        if not active_lics.exists():
            return Response({"status": "inactive", "message": "لا توجد تراخيص نشطة.", "machine_id": machine_id})

        total_balance = sum(lic.invoices_balance for lic in active_lics)
        latest = active_lics.order_by("-expiry_date").first()
        
        is_last_month = False
        if latest and latest.expiry_date:
            today = datetime.date.today()
            if today.year == latest.expiry_date.year and today.month == latest.expiry_date.month:
                is_last_month = True
                
        needs_support = (total_balance <= 100)

        return Response({
            "status": "active",
            "total_invoices_balance": total_balance,
            "expiry_date": latest.expiry_date if latest else None,
            "machine_id": machine_id,
            "is_last_month": is_last_month,
            "needs_support": needs_support
        })


class LicenseActivateView(views.APIView):
    """
    POST /api/v1/license/activate/
    Validate and activate a license code for a device.
    """

    def post(self, request):
        license_code = request.data.get("license_code", "").strip()
        from api.utils.security_utils import get_machine_id
        machine_id = get_machine_id()

        if not license_code:
            return Response(
                {"error": "license_code مطلوب."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Removed tenant check since company_code is no longer used

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
                product_id=result["product_id"],
                start_date=start_date,
                expiry_date=expiry_date,
                invoices_balance=invoices_balance,
                is_active=is_active,
                machine_id=machine_id,
                company_code=company_code,
                license_code_hash=new_sig,
            )
            UsedLicense.objects.create(code_hash=code_hash)

            LicenseHistory.objects.create(
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


# ===========================================================================
# Suggestions Autocomplete Views
# ===========================================================================

def to_english_numerals(text):
    if not text:
        return ""
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    english_digits = '0123456789'
    translation_table = str.maketrans(arabic_digits, english_digits)
    return text.translate(translation_table)

def to_arabic_numerals(text):
    if not text:
        return ""
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    english_digits = '0123456789'
    translation_table = str.maketrans(english_digits, arabic_digits)
    return text.translate(translation_table)

def get_default_date_for_tenant():
    latest_receipt = Receipt.objects.filter(is_deleted=False).order_by('-created_at').first()
    if latest_receipt:
        return latest_receipt.sale_year, latest_receipt.sale_month
    
    active_license = ClientLicense.objects.filter(is_active=True, is_deleted=False).order_by('-start_date').first()
    if active_license and active_license.start_date:
        return active_license.start_date.year, active_license.start_date.month
        
    now = timezone.now()
    return now.year, now.month

def is_date_within_subscription(year, month):
    target_date = date(year, month, 1)
    active_license = ClientLicense.objects.filter(is_active=True, is_deleted=False).order_by('-start_date').first()
    if active_license:
        start = active_license.start_date
        expiry = active_license.expiry_date
        
        if start:
            start_norm = date(start.year, start.month, 1)
            if target_date < start_norm:
                return False
        if expiry:
            expiry_norm = date(expiry.year, expiry.month, 1)
            if target_date > expiry_norm:
                return False
        return True
    else:
        now = timezone.now()
        return now.year == year and now.month == month



def resolve_salesperson_id(tenant, salesperson_id):
    if not salesperson_id:
        return None
    try:
        return int(str(salesperson_id))
    except ValueError:
        pass
    try:
        local_id = int(salesperson_id)
        sp = Salesperson.objects.filter(id=local_id, is_deleted=False).first()
        if sp:
            return sp.id
    except ValueError:
        pass
    return None

class CustomerSuggestionsView(views.APIView):
    def get(self, request):
        term = to_english_numerals(request.query_params.get("term", "").strip())
        field = request.query_params.get("field", "").strip()
        salesperson_id = to_english_numerals(request.query_params.get("salesperson_id", "").strip())
        current_area = to_english_numerals(request.query_params.get("current_area", "").strip())
        current_name = to_english_numerals(request.query_params.get("current_name", "").strip())

        if len(term) < 1:
            return Response([])

        if field not in ['name', 'phone', 'address', 'area']:
            return Response([])

        receipts_qs = Receipt.objects.filter(is_deleted=False)

        if field == 'area':
            receipts_qs = receipts_qs.filter(area__icontains=term).exclude(area='').exclude(area__isnull=True)
        elif field == 'name':
            receipts_qs = receipts_qs.filter(customer_name__icontains=term)
        elif field == 'address':
            receipts_qs = receipts_qs.filter(address__icontains=term).exclude(address='').exclude(address__isnull=True)
        elif field == 'phone':
            receipts_qs = receipts_qs.filter(phone_number__icontains=term).exclude(phone_number='').exclude(phone_number__isnull=True)

        sp_id = resolve_salesperson_id(tenant, salesperson_id)

        suggestions_map = {}
        for r in receipts_qs:
            if field == 'area':
                val = r.area
            elif field == 'name':
                val = r.customer_name
            elif field == 'address':
                val = r.address
            elif field == 'phone':
                val = r.phone_number
            else:
                continue

            if not val:
                continue
            val = val.strip()
            if not val:
                continue

            relevance = 0
            if val.lower().startswith(term.lower()):
                relevance += 50

            if field == 'area':
                if sp_id and r.salesperson_id == sp_id:
                    relevance += 20
            elif field == 'name':
                if sp_id and r.salesperson_id == sp_id:
                    relevance += 20
                if current_area and r.area and r.area.strip().lower() == current_area.lower():
                    relevance += 10
            elif field == 'address':
                if current_area and r.area and r.area.strip().lower() == current_area.lower():
                    relevance += 30
                if sp_id and r.salesperson_id == sp_id:
                    relevance += 10
                if current_name and r.customer_name and r.customer_name.strip().lower() == current_name.lower():
                    relevance += 5
            elif field == 'phone':
                if current_area and r.area and r.area.strip().lower() == current_area.lower():
                    relevance += 30
                if sp_id and r.salesperson_id == sp_id:
                    relevance += 10
                if current_name and r.customer_name and r.customer_name.strip().lower() == current_name.lower():
                    relevance += 5

            if val not in suggestions_map:
                suggestions_map[val] = {
                    "value": val,
                    "relevance": relevance,
                    "use_count": 1
                }
            else:
                suggestions_map[val]["use_count"] += 1
                if relevance > suggestions_map[val]["relevance"]:
                    suggestions_map[val]["relevance"] = relevance

        suggestions_list = list(suggestions_map.values())
        if field == 'area':
            suggestions_list.sort(key=lambda x: (-x["relevance"], -x["use_count"]))
        else:
            suggestions_list.sort(key=lambda x: (-x["relevance"], x["value"].lower()))

        results = []
        for item in suggestions_list[:15]:
            results.append({"value": to_arabic_numerals(item["value"])})

        return Response(results)


class ProductSuggestionsView(views.APIView):
    def get(self, request):
        term = to_english_numerals(request.query_params.get("term", "").strip())
        month_str = to_english_numerals(request.query_params.get("month", "").strip())
        year_str = to_english_numerals(request.query_params.get("year", "").strip())
        branch_id = to_english_numerals(request.query_params.get("branch_id", "").strip())

        # Resolve target date
        default_year, default_month = get_default_date_for_tenant(tenant)
        
        try:
            target_month = int(month_str) if month_str else default_month
            target_year = int(year_str) if year_str else default_year
        except ValueError:
            target_month = default_month
            target_year = default_year

        # If not within subscription dates, return empty array []
        if not is_date_within_subscription( target_year, target_month):
            return Response([])

        # Filter items by tenant and name
        items_qs = InventoryItem.objects.filter(is_deleted=False)
        if term:
            items_qs = items_qs.filter(name__icontains=term)
        
        if branch_id:
            try:
                branch_uuid = int(branch_id)
                items_qs = items_qs.filter(branch_id=branch_uuid)
            except ValueError:
                try:
                    branch_local_id = int(branch_id)
                    items_qs = items_qs.filter(branch__id=branch_local_id)
                except ValueError:
                    pass

        items = items_qs[:50]

        results = []
        for item in items:
            max_stock = calculate_safe_stock_limit(item, default_year, default_month, target_year, target_month)
            results.append({
                "id": str(item.id),
                "value": item.name,
                "max": max_stock
            })

        return Response(results)


# ===========================================================================
# 9. Reports and Dashboard Views
# ===========================================================================

class DefaultDateView(views.APIView):
    def get(self, request):
        branch_id_str = request.query_params.get("branch_id")
        from django.utils import timezone
        
        try:
            qs = Receipt.objects.filter(is_deleted=False)
            if branch_id_str:
                qs = qs.filter(branch_id=branch_id_str)

            last_receipt = qs.order_by('-sale_year', '-sale_month').first()
            if last_receipt:
                return Response({"year": last_receipt.sale_year, "month": last_receipt.sale_month})

            now = timezone.now()
            return Response({"year": now.year, "month": now.month})
        except Exception as e:
            now = timezone.now()
            return Response({"year": now.year, "month": now.month, "error": str(e)})


class DashboardReportView(views.APIView):
    def get(self, request):
        
        from django.db.models import Sum, Count
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})

        # 1. Cash Inflow calculations
        cash_sales_inflow = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_cash_sale=True,
            is_deleted=False
        ).aggregate(s=Sum('total_amount'))['s'] or 0

        down_payment_inflow = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_cash_sale=False,
            is_deleted=False
        ).aggregate(s=Sum('down_payment'))['s'] or 0

        collection_inflow = InstallmentPayment.objects.filter(
            receipt__branch_id=branch_id,
            payment_date__year=year,
            payment_date__month=month,
            is_deleted=False,
            receipt__is_deleted=False
        ).aggregate(s=Sum('amount'))['s'] or 0

        total_cash_inflow = cash_sales_inflow + down_payment_inflow + collection_inflow

        # 2. Revenue
        total_revenue = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_deleted=False
        ).aggregate(s=Sum('total_amount'))['s'] or 0

        # 3. COGS and Sales Commission
        sale_items = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__sale_year=year,
            receipt__sale_month=month,
            receipt__is_deleted=False,
            is_deleted=False
        ).select_related('inventory_item')

        total_cogs = 0
        total_sales_comm_fixed = 0
        for item in sale_items:
            qty = item.quantity
            cost_unit = item.inventory_item.get_price_at_date(month, year)
            comm_unit = item.inventory_item.get_commission_at_date(month, year)
            total_cogs += qty * cost_unit
            total_sales_comm_fixed += qty * comm_unit

        # 4. Reserve Deduction
        credit_receipts = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_cash_sale=False,
            is_deleted=False
        )
        credit_rev_sum = credit_receipts.aggregate(s=Sum('total_amount'))['s'] or 0
        credit_down_payment_sum = credit_receipts.aggregate(s=Sum('down_payment'))['s'] or 0
        reserve_deduction = (credit_rev_sum - credit_down_payment_sum) // 10

        # 5. Operating Expenses
        operating_expenses = Expense.objects.filter(
            branch_id=branch_id,
            expense_year=year,
            expense_month=month,
            is_deleted=False
        ).aggregate(s=Sum('amount'))['s'] or 0

        # 6. Auto Salaries
        salespersons = Salesperson.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )
        auto_salaries = 0
        total_sales_commissions = 0
        total_collection_commissions = 0
        for sp in salespersons:
            sp_sale_items = SaleItem.objects.filter(
                receipt__salesperson=sp,
                receipt__branch_id=branch_id,
                receipt__sale_year=year,
                receipt__sale_month=month,
                receipt__is_deleted=False,
                is_deleted=False
            ).select_related('inventory_item')
            sp_comm_sales = 0
            for item in sp_sale_items:
                qty = item.quantity
                comm_unit = item.inventory_item.get_commission_at_date(month, year)
                sp_comm_sales += qty * comm_unit

            sp_collected = InstallmentPayment.objects.filter(
                receipt__salesperson=sp,
                receipt__branch_id=branch_id,
                payment_date__year=year,
                payment_date__month=month,
                is_deleted=False,
                receipt__is_deleted=False
            ).aggregate(s=Sum('amount'))['s'] or 0
            sp_comm_coll = sp_collected // 10

            total_sales_commissions += sp_comm_sales
            total_collection_commissions += sp_comm_coll
            auto_salaries += sp_comm_sales + sp_comm_coll

        from django.db.models import F

        total_purchases = PurchaseInvoiceItem.objects.filter(
            invoice__branch_id=branch_id,
            invoice__invoice_year=year,
            invoice__invoice_month=month,
            invoice__invoice_type="PURCHASE",
            is_deleted=False,
            invoice__is_deleted=False
        ).aggregate(s=Sum(F('quantity') * F('purchase_price')))['s'] or 0

        # 7. Net Cash in Hand and Safe Balance
        net_cash_in_hand = total_cash_inflow - (operating_expenses + auto_salaries + total_purchases)
        safe_balance = net_cash_in_hand

        # 8. Estimated Net Profit
        estimated_net_profit = total_revenue - (total_cogs + total_sales_commissions + total_collection_commissions + operating_expenses)

        # 9. Current Inventory Value & Low Stock Count
        inventory_items = InventoryItem.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )
        current_inventory_value = 0
        low_stock_count = 0
        for item in inventory_items:
            c_stock = item.get_stock_at_date(month, year)
            c_price = item.get_price_at_date(month, year)
            current_inventory_value += c_stock * c_price
            if c_stock <= 3:
                low_stock_count += 1

        # 10. Avg Basket Size
        receipt_count = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_deleted=False
        ).count()
        avg_basket_size = total_revenue // receipt_count if receipt_count > 0 else 0

        # 11. Top Products
        top_products_qs = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__sale_year=year,
            receipt__sale_month=month,
            receipt__is_deleted=False,
            is_deleted=False
        ).values('inventory_item__name').annotate(
            qty=Sum('quantity')
        ).order_by('-qty')[:5]

        top_products = [
            {
                "product_name": p['inventory_item__name'],
                "quantity_sold": int(p['qty'])
            }
            for p in top_products_qs
        ]

        # 12. Top Areas
        top_areas_qs = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_deleted=False
        ).values('area').annotate(
            val=Sum('total_amount'),
            count=Count('id')
        ).order_by('-val')[:5]

        top_areas = [
            {
                "area": a['area'] if a['area'] else "",
                "sales_value": a['val'],
                "invoice_count": a['count']
            }
            for a in top_areas_qs
        ]

        return Response({
            "period": { "year": year, "month": month },
            "kpis": {
                "safe_balance": safe_balance,
                "total_revenue": total_revenue,
                "total_cogs": total_cogs,
                "total_sales_commissions": total_sales_commissions,
                "total_collection_commissions": total_collection_commissions,
                "estimated_net_profit": estimated_net_profit,
                "current_inventory_value": current_inventory_value,
                "low_stock_count": low_stock_count,
                "avg_basket_size": avg_basket_size
            },
            "cash_drawer_summary": {
                "cash_sales_inflow": cash_sales_inflow,
                "down_payment_inflow": down_payment_inflow,
                "collection_inflow": collection_inflow,
                "total_cash_inflow": total_cash_inflow,
                "total_purchases": total_purchases,
                "operating_expenses": operating_expenses,
                "auto_salaries": auto_salaries,
                "net_cash_in_hand": net_cash_in_hand
            },
            "top_products": top_products,
            "top_areas": top_areas
        })


class SalespersonPerformanceReportView(views.APIView):
    def get(self, request):
        
        from django.db.models import Sum
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})

        salespersons = Salesperson.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )

        list_data = []
        grand_total_cash = 0
        grand_total_credit = 0
        grand_total_collected = 0
        grand_total_comm_sales = 0
        grand_total_comm_coll = 0

        for sp in salespersons:
            receipts_qs = Receipt.objects.filter(
                salesperson=sp,
                branch_id=branch_id,
                sale_year=year,
                sale_month=month,
                is_deleted=False
            )
            
            receipts_count = receipts_qs.count()
            
            cash_sales = receipts_qs.filter(is_cash_sale=True).aggregate(s=Sum('total_amount'))['s'] or 0
            credit_sales = receipts_qs.filter(is_cash_sale=False).aggregate(s=Sum('total_amount'))['s'] or 0
            total_sales_val = cash_sales + credit_sales
            
            collected = InstallmentPayment.objects.filter(
                receipt__salesperson=sp,
                receipt__branch_id=branch_id,
                payment_date__year=year,
                payment_date__month=month,
                is_deleted=False,
                receipt__is_deleted=False
            ).aggregate(s=Sum('amount'))['s'] or 0
            
            sp_sale_items = SaleItem.objects.filter(
                receipt__salesperson=sp,
                receipt__branch_id=branch_id,
                receipt__sale_year=year,
                receipt__sale_month=month,
                receipt__is_deleted=False,
                is_deleted=False
            ).select_related('inventory_item')
            
            comm_sales = 0
            for item in sp_sale_items:
                qty = item.quantity
                comm_unit = item.inventory_item.get_commission_at_date(month, year)
                comm_sales += qty * comm_unit
                
            comm_coll = collected // 10
            due_salary = comm_sales + comm_coll
            
            grand_total_cash += cash_sales
            grand_total_credit += credit_sales
            grand_total_collected += collected
            grand_total_comm_sales += comm_sales
            grand_total_comm_coll += comm_coll
            
            list_data.append({
                "salesperson_id": str(sp.id),
                "id": sp.id,
                "name": sp.name,
                "receipts_count": receipts_count,
                "cash_sales": cash_sales,
                "credit_sales": credit_sales,
                "total_sales_val": total_sales_val,
                "collected": collected,
                "comm_sales": comm_sales,
                "comm_coll": comm_coll,
                "due_salary": due_salary
            })

        return Response({
            "totals": {
                "grand_total_cash": grand_total_cash,
                "grand_total_credit": grand_total_credit,
                "grand_total_sales": (grand_total_cash + grand_total_credit),
                "grand_total_collected": grand_total_collected,
                "grand_total_comm_sales": grand_total_comm_sales,
                "grand_total_comm_coll": grand_total_comm_coll,
                "grand_total_due": (grand_total_comm_sales + grand_total_comm_coll)
            },
            "salespersons": list_data
        })


class InventoryMovementReportView(views.APIView):
    def get(self, request):
        
        from django.db.models import Sum
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})

        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year

        inventory_items = InventoryItem.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )

        items_list = []
        total_inventory_value = 0

        total_adjustments_count = InventoryAdjustment.objects.filter(
            item__branch_id=branch_id,
            year=year,
            month=month,
            is_deleted=False
        ).count()

        for item in inventory_items:
            opening_stock = item.get_stock_at_date(prev_month, prev_year)
            if item.initial_year == year and item.initial_month == month:
                opening_stock += item.initial_quantity
                
            purchases = PurchaseInvoiceItem.objects.filter(
                invoice__branch_id=branch_id,
                invoice__invoice_type="PURCHASE",
                invoice__invoice_year=year,
                invoice__invoice_month=month,
                inventory_item=item,
                is_deleted=False,
                invoice__is_deleted=False
            ).aggregate(s=Sum('quantity'))['s'] or 0
            
            returns = PurchaseInvoiceItem.objects.filter(
                invoice__branch_id=branch_id,
                invoice__invoice_type="RETURN",
                invoice__invoice_year=year,
                invoice__invoice_month=month,
                inventory_item=item,
                is_deleted=False,
                invoice__is_deleted=False
            ).aggregate(s=Sum('quantity'))['s'] or 0
            
            sales = SaleItem.objects.filter(
                receipt__branch_id=branch_id,
                receipt__sale_year=year,
                receipt__sale_month=month,
                inventory_item=item,
                is_deleted=False,
                receipt__is_deleted=False
            ).aggregate(s=Sum('quantity'))['s'] or 0
            
            surplus = InventoryAdjustment.objects.filter(
                item=item,
                adjustment_type="SURPLUS",
                year=year,
                month=month,
                is_deleted=False
            ).aggregate(s=Sum('quantity'))['s'] or 0
            
            deficit = InventoryAdjustment.objects.filter(
                item=item,
                adjustment_type="DEFICIT",
                year=year,
                month=month,
                is_deleted=False
            ).aggregate(s=Sum('quantity'))['s'] or 0
            
            final_stock = item.get_stock_at_date(month, year)
            unit_cost = item.get_price_at_date(month, year)
            total_value = final_stock * unit_cost
            
            total_inventory_value += total_value
            
            items_list.append({
                "product_id": str(item.id),
                "id": item.id,
                "product_name": item.name,
                "opening_stock": opening_stock,
                "purchases": purchases,
                "returns": returns,
                "sales": sales,
                "surplus": surplus,
                "deficit": deficit,
                "final_stock": final_stock,
                "unit_cost": unit_cost,
                "total_value": total_value
            })

        return Response({
            "total_inventory_value": total_inventory_value,
            "total_adjustments_count": total_adjustments_count,
            "items": items_list
        })


class ProfitAndLossReportView(views.APIView):
    def get(self, request):
        
        from django.db.models import Sum
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        salesperson_id_str = request.query_params.get("salesperson_id")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})

        salesperson_id = None
        if salesperson_id_str:
            try:
                salesperson_id = int(salesperson_id_str)
            except ValueError:
                raise ValidationError({"salesperson_id": ["Invalid salesperson_id format."]})

        sale_items_qs = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__sale_year=year,
            receipt__sale_month=month,
            receipt__is_deleted=False,
            is_deleted=False
        )
        if salesperson_id:
            sale_items_qs = sale_items_qs.filter(receipt__salesperson_id=salesperson_id)

        cash_groups = {}
        installment_groups = {}

        for item in sale_items_qs.select_related('inventory_item', 'receipt'):
            item_id = item.inventory_item.id
            is_cash = item.receipt.is_cash_sale
            
            group = cash_groups if is_cash else installment_groups
            
            if item_id not in group:
                group[item_id] = {
                    "item": item.inventory_item,
                    "qty": 0,
                    "total_rev": 0,
                    "sale_items": []
                }
            
            group[item_id]["qty"] += item.quantity
            group[item_id]["total_rev"] += item.quantity * item.unit_price
            group[item_id]["sale_items"].append(item)

        cash_sales_profitability = []
        installment_sales_profitability = []
        
        grand_revenue = 0
        grand_cost = 0
        grand_commission = 0

        # Cash sales calculations
        for item_id, data in cash_groups.items():
            item = data["item"]
            qty = data["qty"]
            total_rev = data["total_rev"]
            
            avg_sell = total_rev // qty if qty > 0 else 0
            cost_per_unit = item.get_price_at_date(month, year)
            total_cost = qty * cost_per_unit
            sales_comm_per_unit = item.get_commission_at_date(month, year)
            total_sales_comm = qty * sales_comm_per_unit
            
            coll_comm_per_unit = 0
            total_coll_comm = 0
            
            total_profit = total_rev - total_cost - total_sales_comm - total_coll_comm
            avg_profit = total_profit // qty if qty > 0 else 0
            
            grand_revenue += total_rev
            grand_cost += total_cost
            grand_commission += (total_sales_comm + total_coll_comm)
            
            cash_sales_profitability.append({
                "id": str(item.id),
                "id": getattr(item, 'id', 0),
                "name": item.name,
                "qty": int(qty),
                "avg_sell": avg_sell,
                "cost_per_unit": cost_per_unit,
                "sales_comm_per_unit": sales_comm_per_unit,
                "total_rev": total_rev,
                "total_cost": total_cost,
                "total_sales_comm": total_sales_comm,
                "coll_comm_per_unit": coll_comm_per_unit,
                "total_coll_comm": total_coll_comm,
                "total_profit": total_profit,
                "avg_profit": avg_profit
            })

        # Installment sales calculations
        for item_id, data in installment_groups.items():
            item = data["item"]
            qty = data["qty"]
            total_rev = data["total_rev"]
            
            avg_sell = total_rev // qty if qty > 0 else 0
            cost_per_unit = item.get_price_at_date(month, year)
            total_cost = qty * cost_per_unit
            sales_comm_per_unit = item.get_commission_at_date(month, year)
            total_sales_comm = qty * sales_comm_per_unit
            
            total_coll_comm = 0
            for sale_item in data["sale_items"]:
                receipt = sale_item.receipt
                if receipt.total_amount > 0:
                    item_rev = sale_item.quantity * sale_item.unit_price
                    payment_diff = receipt.total_amount - receipt.down_payment
                    item_coll_comm = (item_rev * payment_diff // 10) // receipt.total_amount
                    total_coll_comm += item_coll_comm
            
            coll_comm_per_unit = total_coll_comm // qty if qty > 0 else 0
            total_profit = total_rev - total_cost - total_sales_comm - total_coll_comm
            avg_profit = total_profit // qty if qty > 0 else 0
            
            grand_revenue += total_rev
            grand_cost += total_cost
            grand_commission += (total_sales_comm + total_coll_comm)
            
            installment_sales_profitability.append({
                "id": str(item.id),
                "id": getattr(item, 'id', 0),
                "name": item.name,
                "qty": int(qty),
                "avg_sell": avg_sell,
                "cost_per_unit": cost_per_unit,
                "sales_comm_per_unit": sales_comm_per_unit,
                "total_rev": total_rev,
                "total_cost": total_cost,
                "total_sales_comm": total_sales_comm,
                "coll_comm_per_unit": coll_comm_per_unit,
                "total_coll_comm": total_coll_comm,
                "total_profit": total_profit,
                "avg_profit": avg_profit
            })

        # Operating Expenses (branch-level, not filtered by salesperson)
        expenses_total = Expense.objects.filter(
            branch_id=branch_id,
            expense_year=year,
            expense_month=month,
            is_deleted=False
        ).aggregate(s=Sum('amount'))['s'] or 0

        net_profit_final = grand_revenue - grand_cost - grand_commission - expenses_total

        return Response({
            "summary": {
                "grand_revenue": grand_revenue,
                "grand_cost": grand_cost,
                "grand_commission": grand_commission,
                "expenses_total": expenses_total,
                "net_profit_final": net_profit_final
            },
            "cash_sales_profitability": cash_sales_profitability,
            "installment_sales_profitability": installment_sales_profitability
        })


class CashDrawerReportView(views.APIView):
    def get(self, request):
        
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})

        # 1. Cash Sales receipts
        cash_receipts = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_cash_sale=True,
            is_deleted=False
        ).order_by('created_at')
        
        cash_sales_list = [
            {
                "receipt_id": str(receipt.id),
                "receipt_number": receipt.receipt_number,
                "customer_name": receipt.customer_name,
                "amount": receipt.total_amount,
                "sale_date": receipt.created_at.isoformat()
            }
            for receipt in cash_receipts
        ]

        # 2. Down payments (for credit sales where down_payment > 0)
        down_payment_receipts = Receipt.objects.filter(
            branch_id=branch_id,
            sale_year=year,
            sale_month=month,
            is_cash_sale=False,
            down_payment__gt=0,
            is_deleted=False
        ).order_by('created_at')

        down_payments_list = [
            {
                "receipt_id": str(receipt.id),
                "receipt_number": receipt.receipt_number,
                "customer_name": receipt.customer_name,
                "down_payment": receipt.down_payment,
                "total_amount": receipt.total_amount,
                "sale_date": receipt.created_at.isoformat()
            }
            for receipt in down_payment_receipts
        ]

        # 3. Collection payments
        collections_payments = InstallmentPayment.objects.filter(
            receipt__branch_id=branch_id,
            payment_date__year=year,
            payment_date__month=month,
            is_deleted=False,
            receipt__is_deleted=False
        ).order_by('payment_date').select_related('receipt')

        collections_list = [
            {
                "payment_id": str(payment.id),
                "receipt_number": payment.receipt.receipt_number,
                "customer_name": payment.receipt.customer_name,
                "amount": payment.amount,
                "payment_date": payment.payment_date.isoformat()
            }
            for payment in collections_payments
        ]

        return Response({
            "cash_sales": cash_sales_list,
            "down_payments": down_payments_list,
            "collections": collections_list
        })


class InstallmentsReportView(views.APIView):
    def get(self, request):
        from django.db.models import Sum, F, ExpressionWrapper, IntegerField, Q
        from django.utils import timezone
        
        
        branch_id_str = request.query_params.get("branch_id")
        if not branch_id_str:
            raise ValidationError({"branch_id": ["This field is required."]})
        try:
            branch_id = int(branch_id_str)
        except ValueError:
            raise ValidationError({"branch_id": ["Invalid ID format."]})
            
        try:
            Branch.objects.get(id=branch_id, is_deleted=False)
        except Branch.DoesNotExist:
            raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        salesperson_id_str = request.query_params.get("salesperson_id")
        
        # Original Sale period filters
        sale_from_year_str = request.query_params.get("sale_from_year")
        sale_from_month_str = request.query_params.get("sale_from_month")
        sale_to_year_str = request.query_params.get("sale_to_year")
        sale_to_month_str = request.query_params.get("sale_to_month")
        
        now = timezone.now()
        year = int(year_str) if year_str else None
        month = int(month_str) if month_str else None

        filters = Q(receipt__branch_id=branch_id, is_deleted=False, receipt__is_deleted=False)
        
        if year: filters &= Q(payment_date__year=year)
        if month: filters &= Q(payment_date__month=month)
        
        if salesperson_id_str:
            try:
                sp_id = int(salesperson_id_str)
                filters &= Q(receipt__salesperson_id=sp_id)
            except ValueError:
                pass

        customer_name = request.query_params.get("customer_name")
        phone = request.query_params.get("phone")
        area = request.query_params.get("area")

        if customer_name: filters &= Q(receipt__customer_name__icontains=customer_name)
        if phone: filters &= Q(receipt__phone_number__icontains=phone)
        if area: filters &= Q(receipt__area__icontains=area)

        installments = InstallmentPayment.objects.filter(filters)

        # Sale period filtering
        if (sale_from_year_str and sale_from_month_str) or (sale_to_year_str and sale_to_month_str):
            sale_period_expr = ExpressionWrapper(
                F('receipt__sale_year') * 100 + F('receipt__sale_month'),
                output_field=IntegerField()
            )
            installments = installments.annotate(sale_period=sale_period_expr)
            
            if sale_from_year_str and sale_from_month_str:
                from_val = int(sale_from_year_str) * 100 + int(sale_from_month_str)
                installments = installments.filter(sale_period__gte=from_val)
                
            if sale_to_year_str and sale_to_month_str:
                to_val = int(sale_to_year_str) * 100 + int(sale_to_month_str)
                installments = installments.filter(sale_period__lte=to_val)

        installments = installments.select_related('receipt', 'receipt__salesperson').order_by('receipt__salesperson__name', 'payment_date')

        installments_list = []
        total_report_amount = 0

        for payment in installments:
            sp_name = payment.receipt.salesperson.name if payment.receipt.salesperson else "بدون مندوب"
            
            installments_list.append({
                'payment_id': str(payment.id),
                'receipt_id': str(payment.receipt.id),
                'receipt_num': payment.receipt.receipt_number,
                'customer_name': payment.receipt.customer_name or "بدون اسم",
                'phone': payment.receipt.phone_number or "-",
                'area': payment.receipt.area or "-",
                'salesperson_name': sp_name,
                'amount': payment.amount,
                'date': payment.payment_date.isoformat(),
                'sale_date': f"{payment.receipt.sale_year}/{payment.receipt.sale_month:02d}",
                'inst_system': payment.receipt.installment_system or ""
            })
            total_report_amount += payment.amount

        return Response({
            "total_installments_amount": total_report_amount,
            "installments_count": len(installments_list),
            "installments": installments_list
        })

