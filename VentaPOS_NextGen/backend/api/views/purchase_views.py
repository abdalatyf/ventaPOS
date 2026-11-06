"""
Purchase Views for VentaPOS NextGen:
PurchaseInvoicePagination, PurchaseInvoiceViewSet, PurchaseInvoiceItemViewSet.
"""
from collections import defaultdict
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django.template.loader import render_to_string
from api.print_utils import generate_and_open_pdf, to_arabic_numerals
from api.models import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    CompanySetting,
)
from api.serializers import (
    PurchaseInvoiceSerializer,
    PurchaseInvoiceItemSerializer,
)
from .base import SoftDeleteModelViewSet, get_default_date, get_request_branch_id


class PurchaseInvoicePagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
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

        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            if instance.invoice_type == "PURCHASE":
                curr_year, curr_month = get_default_date()

                item_quantities = defaultdict(int)
                item_objects = {}
                for p_item in instance.items.filter(is_deleted=False).select_related("inventory_item"):
                    item_quantities[p_item.inventory_item_id] += p_item.quantity
                    item_objects[p_item.inventory_item_id] = p_item.inventory_item

                for item_id, total_qty in item_quantities.items():
                    inv_item = item_objects[item_id]
                    safe_qty, b_m, b_y = inv_item.get_safe_available_qty(
                        instance.invoice_month,
                        instance.invoice_year,
                        curr_month,
                        curr_year,
                        return_bottleneck=True,
                    )
                    if total_qty > safe_qty:
                        raise ValidationError({
                            "detail": f"لا يمكن حذف فاتورة الشراء! حذف الكمية ({total_qty}) من الصنف '{inv_item.name}' سيؤدي إلى عجز في رصيد المخزن في شهر {b_m}/{b_y} (الرصيد المتاح للحذف: {safe_qty})."
                        })

            instance.items.filter(is_deleted=False).update(is_deleted=True)
            instance.is_deleted = True
            instance.save(update_fields=["is_deleted"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def desktop_print(self, request):
        invoice_ids = request.data.get("invoice_ids", [])
        action_type = request.data.get("action", "print")
        target_printer = request.data.get("target_printer", None)

        if not isinstance(invoice_ids, list) or not invoice_ids:
            return Response({"error": "invoice_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        invoices = self.get_queryset().filter(id__in=invoice_ids).select_related('supplier', 'branch').prefetch_related('items__inventory_item')
        if not invoices.exists():
            return Response({"error": "No valid purchase invoices found"}, status=status.HTTP_404_NOT_FOUND)

        company_settings = CompanySetting.objects.first()
        pages_html = []

        for inv in invoices:
            inv_items = list(inv.items.filter(is_deleted=False).select_related('inventory_item'))
            total_amount = sum(it.quantity * it.purchase_price for it in inv_items)

            formatted_items = []
            for it in inv_items:
                formatted_items.append({
                    'inventory_item': it.inventory_item,
                    'quantity': it.quantity,
                    'purchase_price': it.purchase_price,
                    'total_price': it.quantity * it.purchase_price,
                    'quantity_ar': to_arabic_numerals(it.quantity),
                    'purchase_price_ar': to_arabic_numerals(it.purchase_price),
                    'total_price_ar': to_arabic_numerals(it.quantity * it.purchase_price),
                })

            invoice_date_str = inv.created_at.strftime("%Y/%m/%d") if inv.created_at else f"{inv.invoice_year}/{str(inv.invoice_month).zfill(2)}"

            ctx = {
                'invoice': inv,
                'invoice_date': invoice_date_str,
                'invoice_number_ar': to_arabic_numerals(inv.invoice_number),
                'invoice_date_ar': to_arabic_numerals(invoice_date_str),
                'supplier_name': inv.supplier.name if inv.supplier else 'غير محدد',
                'items': formatted_items,
                'total_amount': total_amount,
                'total_amount_ar': to_arabic_numerals(total_amount),
                'company_settings': company_settings,
                'phone1_ar': to_arabic_numerals(company_settings.phone1) if company_settings and company_settings.phone1 else '',
                'phone2_ar': to_arabic_numerals(company_settings.phone2) if company_settings and company_settings.phone2 else '',
            }
            part = render_to_string('api/pdf_purchase_content.html', ctx)
            pages_html.append(part)

        full_content_body = '<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>'.join(pages_html)
        final_html = render_to_string('api/pdf_base.html', {'content': full_content_body})

        if action_type == "view":
            success, result_msg = generate_and_open_pdf(
                final_html, "View_Purchase_Invoices",
                target_printer=None, action="view", paper_size="DL"
            )
            if success:
                return Response({"status": "success", "message": result_msg}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": result_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            success, msg = generate_and_open_pdf(
                final_html, "Batch_Purchase_Invoices",
                target_printer=target_printer, action="print", paper_size="DL"
            )
            if success:
                return Response({"status": "success", "message": msg}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseInvoiceItemViewSet(SoftDeleteModelViewSet):
    queryset = PurchaseInvoiceItem.objects.select_related(
        "invoice", "inventory_item"
    ).all()
    serializer_class = PurchaseInvoiceItemSerializer
