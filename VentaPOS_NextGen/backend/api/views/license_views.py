"""
License Views for VentaPOS NextGen:
ClientLicenseViewSet, UsedLicenseViewSet, LicenseHistoryViewSet,
LicenseStatusView, LicenseActivateView.
"""
import datetime
import hashlib
from django.db import transaction
from rest_framework import status, views, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.models import (
    ClientLicense,
    UsedLicense,
    LicenseHistory,
    Branch,
    Salesperson,
    InventoryItem,
    Receipt,
    SaleItem,
    InstallmentPayment,
    Supplier,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    CommissionHistory,
    CompanySetting,
    Expense,
    InventoryAdjustment,
)
from api.serializers import (
    LicenseHistorySerializer,
)
from api.utils.license_validator import LicenseValidator
from api.utils.security_utils import (
    generate_record_signature,
    get_machine_id,
)
from .base import SoftDeleteModelViewSet


class LicenseHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LicenseHistory.objects.all()
    serializer_class = LicenseHistorySerializer


class LicenseStatusView(views.APIView):
    """
    GET /api/v1/license/status/
    Returns current license balance and expiry for a tenant.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(is_superuser=True).first()
        has_password = bool(admin_user and admin_user.has_usable_password() and not admin_user.check_password(""))

        machine_id = get_machine_id()
        active_lics = ClientLicense.objects.filter(is_active=True, is_deleted=False)
        is_demo = not active_lics.exclude(machine_id="DEMO_MACHINE").exists()

        if not active_lics.exists():
            return Response({
                "status": "inactive",
                "message": "لا توجد تراخيص نشطة.",
                "machine_id": machine_id,
                "is_demo": is_demo,
                "has_password": has_password,
            })

        total_balance = sum(lic.invoices_balance for lic in active_lics)
        valid_time_lics = active_lics.exclude(machine_id="DEMO_MACHINE")
        if not valid_time_lics.exists():
            valid_time_lics = active_lics
        latest = valid_time_lics.order_by("-expiry_date").first()

        is_last_month = False
        if latest and latest.expiry_date:
            from api.services.receipt_service import get_license_date_bounds
            from django.utils import timezone
            start_date, last_allowed_month, grace_end = get_license_date_bounds(latest)
            today = timezone.localdate()
            if last_allowed_month:
                if (today.year == last_allowed_month.year and today.month == last_allowed_month.month) or (grace_end and last_allowed_month < today <= grace_end):
                    is_last_month = True

        needs_support = (total_balance <= 100)

        return Response({
            "status": "active",
            "total_invoices_balance": total_balance,
            "expiry_date": latest.expiry_date if latest else None,
            "machine_id": machine_id,
            "is_last_month": is_last_month,
            "needs_support": needs_support,
            "is_demo": is_demo,
            "has_password": has_password,
            "product_id": latest.product_id if latest else None,
            "is_print_only": bool(latest and latest.product_id in (2, 3)),
            "start_date": latest.start_date.isoformat() if (latest and latest.start_date) else None,
            "lic_start_date": latest.start_date.isoformat() if (latest and latest.start_date) else None,
        })


class LicenseActivateView(views.APIView):
    """
    POST /api/v1/license/activate/
    Validate and activate a license code for a device.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        license_code = request.data.get("license_code", "").strip()
        machine_id = get_machine_id()

        if not license_code:
            return Response(
                {"error": "license_code مطلوب."},
                status=status.HTTP_400_BAD_REQUEST,
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

        if result.get("product_id") in (15, 16) or result.get("is_recovery"):
            return Response(
                {"error": "هذا كود استرداد وليس كود تفعيل. الرجاء استخدامه في شاشة استعادة كلمة المرور."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pid = result["product_id"]
        TOPUP_MAP = {
            10: 100,
            11: 300,
            12: 500,
            13: 1000,
            14: 3000,
        }

        # Check for top-up codes
        if pid in TOPUP_MAP:
            topup_qty = TOPUP_MAP[pid]
            active_lic = (
                ClientLicense.objects.filter(is_active=True, is_deleted=False)
                .exclude(machine_id="DEMO_MACHINE")
                .order_by("-expiry_date")
                .first()
            )
            if not active_lic:
                return Response(
                    {"error": "لا يوجد ترخيص نشط لإضافة باقة الفواتير إليه. يرجى تفعيل اشتراك أساسي أولاً."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                active_lic.invoices_balance += topup_qty
                new_sig = generate_record_signature(
                    active_lic.expiry_date,
                    active_lic.invoices_balance,
                    machine_id,
                    active_lic.product_id,
                    active_lic.is_active,
                )
                active_lic.license_code_hash = new_sig
                active_lic.save(update_fields=["invoices_balance", "license_code_hash"])

                UsedLicense.objects.create(code_hash=code_hash)
                LicenseHistory.objects.create(
                    machine_id=machine_id,
                    product_name=f"Top-up +{topup_qty} (Product {pid})",
                    operation_type="TOPUP",
                    start_date=active_lic.start_date,
                    end_date=active_lic.expiry_date,
                    added_balance=topup_qty,
                    status="SUCCESS",
                )

            return Response(
                {
                    "status": "success",
                    "message": f"تمت إضافة {topup_qty} فاتورة إلى الرصيد بنجاح.",
                    "added_balance": topup_qty,
                    "total_invoices_balance": active_lic.invoices_balance,
                    "wiped_demo": False,
                },
                status=status.HTTP_200_OK,
            )

        start_year = result.get("start_year") or result.get("year")
        start_month = result.get("start_month") or result.get("month")
        start_date = datetime.date(start_year, start_month, 1)

        if pid == 1:
            # 1: Trial 60 Days (2 months, 800 balance)
            m = start_month + 2
            exp_y = start_year + (m - 1) // 12
            exp_m = ((m - 1) % 12) + 1
            expiry_date = datetime.date(exp_y, exp_m, 1)
            invoices_balance = 800
        elif pid == 2:
            # 2: Print-Only 1 Year (12 months, 4800 balance)
            expiry_date = datetime.date(start_year + 1, start_month, 1)
            invoices_balance = 4800
        elif pid == 3:
            # 3: Print-Only Lifetime (99 years, 999999 balance)
            expiry_date = datetime.date(start_year + 99, start_month, 1)
            invoices_balance = 999999
        elif pid == 4:
            # 4: Full Management 1 Year (12 months, 4800 balance)
            expiry_date = datetime.date(start_year + 1, start_month, 1)
            invoices_balance = 4800
        elif pid == 5:
            # 5: Full 3 Years (36 months, 14400 balance)
            expiry_date = datetime.date(start_year + 3, start_month, 1)
            invoices_balance = 14400
        elif pid == 6:
            # 6: Full 5 Years (60 months, 24000 balance)
            expiry_date = datetime.date(start_year + 5, start_month, 1)
            invoices_balance = 24000
        elif pid == 7:
            # 7: Full Lifetime (99 years, 999999 balance)
            expiry_date = datetime.date(start_year + 99, start_month, 1)
            invoices_balance = 999999
        else:
            expiry_date = datetime.date(start_year + 1, start_month, 1)
            invoices_balance = result.get("invoices_balance", 4800)

        is_active = True

        new_sig = generate_record_signature(
            expiry_date,
            invoices_balance,
            machine_id,
            pid,
            is_active,
        )

        is_demo = not ClientLicense.all_objects.exclude(machine_id="DEMO_MACHINE").exists()

        with transaction.atomic():
            if is_demo:
                Expense.all_objects.all().delete()
                InventoryAdjustment.all_objects.all().delete()
                LicenseHistory.all_objects.all().delete()
                InstallmentPayment.all_objects.all().delete()
                SaleItem.all_objects.all().delete()
                Receipt.all_objects.all().delete()
                PurchaseInvoiceItem.all_objects.all().delete()
                PurchaseInvoice.all_objects.all().delete()
                CommissionHistory.all_objects.all().delete()
                InventoryItem.all_objects.all().delete()
                Supplier.all_objects.all().delete()
                Salesperson.all_objects.all().delete()
                Branch.all_objects.all().delete()
                CompanySetting.all_objects.all().delete()
                ClientLicense.objects.all().delete()
                UsedLicense.objects.all().delete()

            ClientLicense.objects.create(
                product_id=pid,
                start_date=start_date,
                expiry_date=expiry_date,
                invoices_balance=invoices_balance,
                is_active=is_active,
                machine_id=machine_id,
                company_code=None,
                license_code_hash=new_sig,
            )
            UsedLicense.objects.create(code_hash=code_hash)

            LicenseHistory.objects.create(
                machine_id=machine_id,
                product_name=f"Product {pid}",
                operation_type="ACTIVATE",
                start_date=start_date,
                end_date=expiry_date,
                added_balance=invoices_balance,
                status="SUCCESS",
            )

        return Response(
            {
                "status": "success",
                "message": "تم تفعيل الترخيص بنجاح.",
                "wiped_demo": is_demo,
            },
            status=status.HTTP_201_CREATED,
        )
