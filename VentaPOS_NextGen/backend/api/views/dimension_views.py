"""
Dimension ViewSets for VentaPOS NextGen:
BranchViewSet, SalespersonViewSet, SupplierViewSet, CompanySettingViewSet.
"""
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import (
    Branch,
    Salesperson,
    Supplier,
    CompanySetting,
    Receipt,
    PurchaseInvoice,
    InventoryItem,
    Expense,
)
from api.serializers import (
    BranchSerializer,
    SalespersonSerializer,
    SupplierSerializer,
    CompanySettingSerializer,
)
from .base import SoftDeleteModelViewSet, get_request_branch_id


class BranchViewSet(SoftDeleteModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            Receipt.all_objects.filter(branch=instance).exists()
            or PurchaseInvoice.all_objects.filter(branch=instance).exists()
            or InventoryItem.all_objects.filter(branch=instance).exists()
            or Expense.all_objects.filter(branch=instance).exists()
        ):
            raise ValidationError({"detail": "لا يمكن حذف هذا الفرع لوجود فواتير أو أصناف مرتبطة به"})

        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalespersonViewSet(SoftDeleteModelViewSet):
    queryset = Salesperson.objects.select_related("branch").all()
    serializer_class = SalespersonSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Receipt.objects.filter(salesperson=instance).exists():
            raise ValidationError({"detail": "لا يمكن حذف مندوب مرتبط بفواتير."})
        return super().destroy(request, *args, **kwargs)


class SupplierViewSet(SoftDeleteModelViewSet):
    queryset = Supplier.objects.select_related("branch").all()
    serializer_class = SupplierSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search.strip())
        return qs

    def perform_create(self, serializer):
        branch_id = get_request_branch_id(self.request)
        if branch_id and not serializer.validated_data.get("branch"):
            serializer.save(branch_id=branch_id)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if PurchaseInvoice.objects.filter(supplier=instance).exists():
            raise ValidationError({"detail": "لا يمكن حذف مورد مرتبط بفواتير شراء."})
        return super().destroy(request, *args, **kwargs)


class CompanySettingViewSet(SoftDeleteModelViewSet):
    queryset = CompanySetting.objects.all()
    serializer_class = CompanySettingSerializer
