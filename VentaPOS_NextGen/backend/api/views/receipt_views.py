"""
Receipt Views for VentaPOS NextGen:
ReceiptPagination, ReceiptViewSet, SaleItemViewSet, InstallmentPaymentViewSet,
ReceiptNextNumberView, ReceiptHistoryCursorView.
"""
from collections import defaultdict
from django.db import transaction
from django.db.models import Sum, Q, Exists, OuterRef
from django.utils import timezone
from rest_framework import status, views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.models import (
    Receipt,
    SaleItem,
    InstallmentPayment,
    CompanySetting,
    Branch,
)
from api.serializers import (
    ReceiptSerializer,
    SaleItemSerializer,
    InstallmentPaymentSerializer,
)
from api.services.receipt_service import (
    process_return_receipt,
    ReceiptServiceError,
)
from .base import SoftDeleteModelViewSet, to_english_numerals, get_default_date, get_request_branch_id


class ReceiptPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        qs = self.page.paginator.object_list
        aggregates = qs.aggregate(
            total_sales=Sum("total_amount"),
            total_cash=Sum("total_amount", filter=Q(is_cash_sale=True)),
            total_down_payments=Sum("down_payment", filter=Q(is_cash_sale=False)),
            total_credit=Sum("total_amount", filter=Q(is_cash_sale=False))
        )
        total_sales = aggregates["total_sales"] or 0
        total_cash = aggregates["total_cash"] or 0
        total_down_payments = aggregates["total_down_payments"] or 0
        total_credit = aggregates["total_credit"] or 0
        all_ids = list(qs.values_list('id', flat=True))
        all_installment_ids = list(qs.filter(is_cash_sale=False).values_list('id', flat=True))
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "aggregate": {
                "total_sales": total_sales,
                "total_cash": total_cash,
                "total_down_payments": total_down_payments,
                "total_credit": total_credit,
            },
            "total_amount_sum": total_sales,
            "all_ids": all_ids,
            "all_installment_ids": all_installment_ids,
            "results": data
        })


class ReceiptViewSet(SoftDeleteModelViewSet):
    queryset = Receipt.objects.select_related(
        "branch", "salesperson"
    ).prefetch_related("sale_items__inventory_item", "payments").all()
    serializer_class = ReceiptSerializer
    pagination_class = ReceiptPagination

    def perform_create(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            if instance.receipt_type == "RETURN":
                curr_year, curr_month = get_default_date()

                item_quantities = defaultdict(int)
                item_objects = {}
                for s_item in instance.sale_items.filter(is_deleted=False).select_related("inventory_item"):
                    item_quantities[s_item.inventory_item_id] += s_item.quantity
                    item_objects[s_item.inventory_item_id] = s_item.inventory_item

                for item_id, total_qty in item_quantities.items():
                    inv_item = item_objects[item_id]
                    safe_qty, b_m, b_y = inv_item.get_safe_available_qty(
                        instance.sale_month,
                        instance.sale_year,
                        curr_month,
                        curr_year,
                        return_bottleneck=True,
                    )
                    if total_qty > safe_qty:
                        raise ValidationError({
                            "detail": f"لا يمكن حذف فاتورة المرتجع! حذف المرتجع للصنف '{inv_item.name}' سيؤدي إلى عجز في رصيد المخزن في شهر {b_m}/{b_y} (الرصيد المتاح: {safe_qty})."
                        })

            instance.sale_items.filter(is_deleted=False).update(is_deleted=True)
            instance.payments.filter(is_deleted=False).update(is_deleted=True)
            instance.is_deleted = True
            instance.save(update_fields=["is_deleted"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        receipt_ids = request.data.get("receipt_ids", [])
        if not isinstance(receipt_ids, list):
            return Response({"error": "receipt_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            receipts_to_delete = list(Receipt.objects.filter(id__in=receipt_ids))
            return_receipts = [r for r in receipts_to_delete if r.receipt_type == "RETURN"]

            if return_receipts:
                curr_year, curr_month = get_default_date()

                for r in return_receipts:
                    item_quantities = defaultdict(int)
                    item_objects = {}
                    for s_item in r.sale_items.filter(is_deleted=False).select_related("inventory_item"):
                        item_quantities[s_item.inventory_item_id] += s_item.quantity
                        item_objects[s_item.inventory_item_id] = s_item.inventory_item

                    for item_id, total_qty in item_quantities.items():
                        inv_item = item_objects[item_id]
                        safe_qty, b_m, b_y = inv_item.get_safe_available_qty(
                            r.sale_month,
                            r.sale_year,
                            curr_month,
                            curr_year,
                            return_bottleneck=True,
                        )
                        if total_qty > safe_qty:
                            raise ValidationError({
                                "detail": f"لا يمكن حذف فاتورة المرتجع رقم #{r.receipt_number}! حذف المرتجع للصنف '{inv_item.name}' سيؤدي إلى عجز في رصيد المخزن في شهر {b_m}/{b_y} (الرصيد المتاح: {safe_qty})."
                            })

            actual_ids = [r.id for r in receipts_to_delete]
            SaleItem.objects.filter(receipt_id__in=actual_ids).update(is_deleted=True)
            InstallmentPayment.objects.filter(receipt_id__in=actual_ids).update(is_deleted=True)
            Receipt.objects.filter(id__in=actual_ids).update(is_deleted=True)

        return Response({"status": "success", "deleted_count": len(actual_ids)}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def return_receipt(self, request, pk=None):
        original_receipt = self.get_object()
        try:
            res = process_return_receipt(original_receipt, request.data)
            return Response(res, status=status.HTTP_200_OK)
        except ReceiptServiceError as e:
            return Response({"error": e.message}, status=e.status_code)

    @action(detail=False, methods=["get"])
    def printers(self, request):
        import subprocess
        import json
        try:
            ps_cmd = (
                "Get-Printer | Select-Object Name, PrinterStatus, WorkOffline, "
                "@{Name='IsDefault'; Expression={[bool]$_.Default}} | ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                check=True
            )
            raw_stdout = result.stdout.strip()
            printers_list = []
            if raw_stdout:
                parsed = json.loads(raw_stdout)
                items = [parsed] if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
                for item in items:
                    name = str(item.get("Name", "")).strip()
                    if not name:
                        continue
                    work_offline = bool(item.get("WorkOffline", False))
                    raw_status = str(item.get("PrinterStatus", "")).strip().lower()
                    is_offline = work_offline or (raw_status in ("offline", "7", "error", "3", "4", "5", "paused", "1"))
                    status_str = "offline" if is_offline else "ready"
                    is_default = bool(item.get("IsDefault", False))
                    printers_list.append({
                        "name": name,
                        "status": status_str,
                        "is_default": is_default
                    })
            return Response({"printers": printers_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"فشل في جلب الطابعات: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def desktop_print(self, request):
        receipt_ids = request.data.get("receipt_ids", [])
        action_type = request.data.get("action", "print")
        target_printer = request.data.get("target_printer", None)

        if not isinstance(receipt_ids, list) or not receipt_ids:
            return Response({"error": "receipt_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        receipts = self.get_queryset().filter(id__in=receipt_ids).prefetch_related('payments')
        if not receipts.exists():
            return Response({"error": "No valid receipts found"}, status=status.HTTP_404_NOT_FOUND)

        if receipts.filter(is_cash_sale=True).exists():
            return Response({"error": "الطباعة مخصصة لجداول الأقساط فقط"}, status=status.HTTP_400_BAD_REQUEST)

        from django.template.loader import render_to_string
        from api.print_utils import generate_and_open_pdf, ed2ad

        company_settings = CompanySetting.objects.filter().first()
        pages_html = []

        for receipt in receipts:
            installments_from_db = list(receipt.payments.filter(is_deleted=False).order_by('payment_date'))
            total_installments = len(installments_from_db)
            paid_so_far = receipt.down_payment

            if not installments_from_db:
                ctx = self._prepare_pdf_context(receipt)
                ctx['company_settings'] = company_settings
                part = render_to_string('api/pdf_invoice_content.html', ctx)
                pages_html.append(part)
            else:
                for i, inst in enumerate(installments_from_db):
                    total = int(receipt.total_amount)
                    if str(total)[-1] in ("1", "6"):
                        total -= 1
                    elif str(total)[-1] in ("9", "4"):
                        total += 1

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
            success, msg = generate_and_open_pdf(
                final_html, "Batch_Receipts",
                target_printer=target_printer, action="print", paper_size="DL"
            )
            if success:
                return Response({"status": "success", "message": msg}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_pdf_context(self, receipt, inst=None, inst_index=1, total_inst=1):
        from api.print_utils import ed2ad, get_num_to_words_ar

        total = receipt.total_amount
        rem_amount = total - receipt.down_payment if not receipt.is_cash_sale else 0

        cs = CompanySetting.objects.first()
        branch_name = receipt.branch.name if receipt.branch else ''
        comp_name = (cs.name if cs and cs.name else branch_name) or branch_name

        return {
            'receipt_number': ed2ad(str(receipt.receipt_number)),
            'current_installment_index': ed2ad(str(inst_index)) if inst_index else '',
            'company_settings': {
                'name': comp_name,
                'description': cs.description if cs and cs.description else '',
                'phone1': ed2ad(str(cs.phone1)) if cs and cs.phone1 else '',
                'phone2': ed2ad(str(cs.phone2)) if cs and cs.phone2 else '',
                'footer_text': cs.footer_text if cs and cs.footer_text else 'تطبق الشروط والأحكام'
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

        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        if sp_param := (params.get("salesperson_id") or params.get("salesperson")):
            if str(sp_param).strip():
                clean_sp_id = to_english_numerals(str(sp_param).strip())
                try:
                    uuid_val = int(clean_sp_id)
                    qs = qs.filter(salesperson_id=uuid_val)
                except ValueError:
                    qs = qs.filter(salesperson__id=clean_sp_id)

        if year := params.get("year"):
            if str(year).strip():
                clean_year = to_english_numerals(str(year).strip())
                try:
                    qs = qs.filter(sale_year=int(clean_year))
                except ValueError:
                    pass

        if month := params.get("month"):
            if str(month).strip():
                clean_month = to_english_numerals(str(month).strip())
                try:
                    qs = qs.filter(sale_month=int(clean_month))
                except ValueError:
                    pass

        if receipt_from := params.get("receipt_from"):
            if str(receipt_from).strip():
                clean_rf = to_english_numerals(str(receipt_from).strip())
                try:
                    qs = qs.filter(receipt_number__gte=int(clean_rf))
                except ValueError:
                    pass

        if receipt_to := params.get("receipt_to"):
            if str(receipt_to).strip():
                clean_rt = to_english_numerals(str(receipt_to).strip())
                try:
                    qs = qs.filter(receipt_number__lte=int(clean_rt))
                except ValueError:
                    pass

        if customer_name := params.get("customer_name"):
            if str(customer_name).strip():
                qs = qs.filter(customer_name__icontains=str(customer_name).strip())

        if phone_param := (params.get("phone") or params.get("phone_number")):
            if str(phone_param).strip():
                clean_phone = to_english_numerals(str(phone_param).strip())
                qs = qs.filter(phone_number__icontains=clean_phone)

        if address := params.get("address"):
            if str(address).strip():
                qs = qs.filter(address__icontains=str(address).strip())

        if area := params.get("area"):
            if str(area).strip():
                qs = qs.filter(area__icontains=str(area).strip())

        if (is_cash := params.get("is_cash_sale")) is not None:
            is_cash_str = str(is_cash).strip()
            if is_cash_str != "":
                qs = qs.filter(is_cash_sale=(is_cash_str.lower() == "true"))

        if (has_down_payment := params.get("has_down_payment")) is not None:
            if str(has_down_payment).strip().lower() == "true":
                qs = qs.filter(is_cash_sale=False, down_payment__gt=0)

        qs = qs.annotate(
            _has_returns=Exists(
                Receipt.objects.filter(
                    parent_receipt=OuterRef("pk"),
                    receipt_type="RETURN",
                    is_deleted=False
                )
            )
        )

        return qs.order_by("-created_at", "-id")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

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


class ReceiptNextNumberView(views.APIView):
    def get(self, request):
        branch_id = get_request_branch_id(request)
        branch = None
        if branch_id:
            branch = Branch.all_objects.filter(id=branch_id).first()
        if not branch:
            branch = Branch.objects.first()

        next_num = Receipt.get_next_receipt_number(branch) if branch else 1
        return Response({"next_receipt_number": next_num})


class ReceiptHistoryCursorView(views.APIView):
    def get(self, request):
        current_receipt_number = request.query_params.get("current_receipt_number", "").strip()
        direction = request.query_params.get("direction", "").strip()

        branch_id = get_request_branch_id(request)
        qs = Receipt.objects.filter(is_deleted=False)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        try:
            current_receipt_number = int(current_receipt_number)
        except ValueError:
            current_receipt_number = None

        if direction == 'prev':
            if current_receipt_number is None:
                receipt = qs.order_by('-receipt_number').first()
            else:
                receipt = qs.filter(receipt_number__lt=current_receipt_number).order_by('-receipt_number').first()
        elif direction == 'next':
            if current_receipt_number is None:
                return Response(None)
            receipt = qs.filter(receipt_number__gt=current_receipt_number).order_by('receipt_number').first()
        else:
            return Response(None)

        if not receipt:
            return Response(None)

        return Response({
            "receipt_number": receipt.receipt_number,
            "customer_name": receipt.customer_name,
            "phone_number": receipt.phone_number,
            "area": receipt.area,
            "address": receipt.address,
        })
