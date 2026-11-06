"""
Base ViewSet and shared utility functions for VentaPOS NextGen views.
"""
import datetime
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.services.financial_service import get_collection_commission_rate


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


def get_request_branch_id(request):
    """
    Extracts branch_id from request query params ('branch_id' or 'branch')
    or from HTTP header 'X-Branch-ID'. Normalizes Arabic numerals to ASCII digits.
    Returns integer branch_id or None.
    """
    if not request:
        return None
    val = None
    if hasattr(request, 'query_params'):
        val = request.query_params.get('branch_id') or request.query_params.get('branch')
    if not val and hasattr(request, 'headers'):
        val = request.headers.get('X-Branch-ID')
    if not val and hasattr(request, 'data') and isinstance(request.data, dict):
        val = request.data.get('branch_id') or request.data.get('branch')
    if not val and hasattr(request, 'GET'):
        val = request.GET.get('branch_id') or request.GET.get('branch')

    if not val:
        return None
    val_clean = to_english_numerals(str(val)).strip()
    try:
        return int(val_clean)
    except (ValueError, TypeError):
        return None


def get_default_date(branch_id=None):
    from api.models import Receipt, ClientLicense
    qs = Receipt.objects.filter(is_deleted=False, is_confirmed=True)
    if branch_id is not None:
        qs = qs.filter(branch_id=branch_id)
    latest_receipt = qs.order_by('-sale_year', '-sale_month', '-id').first()
    if latest_receipt:
        return latest_receipt.sale_year, latest_receipt.sale_month

    active_license = ClientLicense.objects.filter(is_active=True, is_deleted=False).order_by('-start_date').first()
    if active_license and active_license.start_date:
        return active_license.start_date.year, active_license.start_date.month

    now = timezone.now()
    return now.year, now.month


def is_date_within_subscription(year, month):
    from api.models import ClientLicense
    from dateutil.relativedelta import relativedelta
    target_date = datetime.date(year, month, 1)
    
    # Query active production license first, fallback to demo
    active_lic = ClientLicense.objects.filter(is_active=True, is_deleted=False).exclude(machine_id="DEMO_MACHINE").order_by('-expiry_date').first()
    if not active_lic:
        active_lic = ClientLicense.objects.filter(is_active=True, is_deleted=False).order_by('-expiry_date').first()

    if active_lic:
        start = active_lic.start_date
        expiry = active_lic.expiry_date

        if start:
            start_norm = datetime.date(start.year, start.month, 1)
            if target_date < start_norm:
                return False
        if expiry:
            if expiry.day == 1 and (not start or start < expiry):
                last_allowed_month = (expiry - relativedelta(months=1)).replace(day=1)
            else:
                last_allowed_month = expiry.replace(day=1)

            if target_date > last_allowed_month:
                return False
        return True
    return True


def resolve_salesperson_id(salesperson_id):
    if not salesperson_id:
        return None
    try:
        return int(str(salesperson_id))
    except ValueError:
        pass
    try:
        from api.models import Salesperson
        local_id = int(salesperson_id)
        sp = Salesperson.objects.filter(id=local_id, is_deleted=False).first()
        if sp:
            return sp.id
    except (ValueError, TypeError):
        pass
    return None


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
                    try:
                        branch = Branch.objects.get(id=int(request.headers.get("X-Branch-ID")), is_deleted=False)
                    except (Branch.DoesNotExist, ValueError):
                        pass
                if not branch:
                    branch = Branch.objects.first()
                if branch:
                    data['branch'] = branch.id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return super().create(request, *args, **kwargs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["tenant"] = getattr(self.request, "tenant", None)
        return ctx
