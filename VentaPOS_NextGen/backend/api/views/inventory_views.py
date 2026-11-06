"""
Inventory ViewSets for VentaPOS NextGen:
InventoryItemViewSet, CommissionHistoryViewSet, InventoryAdjustmentViewSet.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import (
    InventoryItem,
    CommissionHistory,
    InventoryAdjustment,
    PurchaseInvoiceItem,
    SaleItem,
)
from api.serializers import (
    InventoryItemSerializer,
    CommissionHistorySerializer,
    InventoryAdjustmentSerializer,
)
from .base import SoftDeleteModelViewSet, get_default_date, get_collection_commission_rate, get_request_branch_id


class InventoryItemViewSet(SoftDeleteModelViewSet):
    queryset = InventoryItem.objects.select_related("branch").all()
    serializer_class = InventoryItemSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if SaleItem.objects.filter(inventory_item=instance).exists() or PurchaseInvoiceItem.objects.filter(inventory_item=instance).exists():
            raise ValidationError({"detail": "لا يمكن حذف صنف مرتبط بفواتير بيع أو شراء."})
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        items_to_process = page if page is not None else list(queryset)

        if items_to_process:
            from api.services.stock_service import calculate_bulk_stock_timeline
            now = timezone.now()
            stock_map = calculate_bulk_stock_timeline(items_to_process, now.month, now.year, now.month, now.year)
            for item in items_to_process:
                item_data = stock_map.get(item.id, {})
                item._precomputed_stock = item_data.get('current_stock', 0)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(items_to_process, many=True)
        return Response(serializer.data)

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

        default_year, default_month = get_default_date(branch_id=item.branch_id)
        safe_qty, b_month, b_year = item.get_safe_available_qty(
            req_month, req_year, default_month, default_year, return_bottleneck=True
        )

        response_data = {"safe_available_qty": safe_qty}
        if b_month != req_month or b_year != req_year:
            response_data["bottleneck_month"] = b_month
            response_data["bottleneck_year"] = b_year

        return Response(response_data)

    @action(detail=True, methods=["get"], url_path="get_safe_available_qty")
    def get_safe_available_qty(self, request, pk=None):
        return self.safe_available_qty(request, pk)

    @action(detail=False, methods=["get"], url_path="pos_search")
    def pos_search(self, request):
        term = request.query_params.get("term", "").strip()
        if not term:
            return Response([])

        qs = self.get_queryset().filter(name__icontains=term)[:20]

        results = []
        for item in qs:
            results.append({
                "id": item.id,
                "name": item.name,
            })

        return Response(results)

    @action(detail=True, methods=["get"], url_path="ledger")
    def ledger(self, request, pk=None):
        item = self.get_object()
        raw_events = []

        # 1. INITIAL (Opening balance)
        raw_events.append({
            "type": "INITIAL",
            "year": item.initial_year,
            "month": item.initial_month,
            "quantity": item.initial_quantity,
            "price": float(item.initial_purchase_price),
            "commission": float(item.initial_commission_amount),
            "description": "إضافة الصنف / رصيد افتتاحي",
            "sort_key": (item.initial_year, item.initial_month, 0, 0, 0),
        })

        # 2. PURCHASES & PURCHASE RETURNS
        for p in PurchaseInvoiceItem.objects.filter(
            inventory_item=item, is_deleted=False, invoice__is_deleted=False
        ).select_related("invoice", "invoice__supplier"):
            is_purchase = (p.invoice.invoice_type == "PURCHASE")
            raw_events.append({
                "type": "PURCHASE" if is_purchase else "RETURN",
                "year": p.invoice.invoice_year,
                "month": p.invoice.invoice_month,
                "quantity": p.quantity,
                "price": float(p.purchase_price),
                "total_amount": float(p.quantity * p.purchase_price),
                "invoice_number": p.invoice.invoice_number,
                "supplier": p.invoice.supplier.name if p.invoice.supplier else "-",
                "description": "فاتورة شراء" if is_purchase else "مرتجع مشتريات للمورد",
                "sort_key": (
                    p.invoice.invoice_year,
                    p.invoice.invoice_month,
                    1 if is_purchase else 2,
                    p.invoice.invoice_number or 0,
                    p.id,
                ),
            })

        from api.services.stock_service import get_bulk_price_resolver, get_bulk_commission_resolver
        resolve_price = get_bulk_price_resolver([item])
        resolve_comm = get_bulk_commission_resolver([item])

        # 3. SALES & SALES RETURNS
        for s in SaleItem.objects.filter(
            inventory_item=item, is_deleted=False, receipt__is_deleted=False, receipt__is_confirmed=True
        ).select_related("receipt", "receipt__salesperson", "receipt__parent_receipt"):
            is_return = (s.receipt.receipt_type == "RETURN")
            if is_return and s.receipt.parent_receipt:
                fin_month = s.receipt.parent_receipt.sale_month
                fin_year = s.receipt.parent_receipt.sale_year
            else:
                fin_month = s.receipt.sale_month
                fin_year = s.receipt.sale_year

            unit_cost = float(resolve_price(item, fin_month, fin_year))
            commission = float(resolve_comm(item, fin_month, fin_year))
            unit_price = float(s.unit_price)
            revenue = float(s.quantity * s.unit_price)
            cogs = float(s.quantity) * unit_cost
            total_comm = float(s.quantity) * commission

            if s.receipt.is_cash_sale:
                coll_comm = 0.0
                net_profit = revenue - cogs - total_comm
            else:
                receipt_total = float(s.receipt.total_amount or 0)
                receipt_dp = float(s.receipt.down_payment or 0)
                coll_rate = get_collection_commission_rate()
                coll_comm = (
                    (revenue * (receipt_total - receipt_dp) * coll_rate) / receipt_total
                    if receipt_total > 0
                    else 0.0
                )
                net_profit = revenue - cogs - total_comm - coll_comm

            if is_return:
                net_profit = -net_profit

            raw_events.append({
                "type": "SALE_RETURN" if is_return else "SALE",
                "year": s.receipt.sale_year,
                "month": s.receipt.sale_month,
                "fin_year": fin_year,
                "fin_month": fin_month,
                "quantity": s.quantity,
                "price": unit_price,
                "unit_cost": unit_cost,
                "commission": commission,
                "net_profit": net_profit,
                "receipt_number": s.receipt.receipt_number,
                "customer_name": s.receipt.customer_name or "-",
                "salesperson": s.receipt.salesperson.name if s.receipt.salesperson else "-",
                "is_cash_sale": s.receipt.is_cash_sale,
                "receipt_total": str(s.receipt.total_amount),
                "receipt_down_payment": str(s.receipt.down_payment),
                "description": "مرتجع مبيعات من عميل" if is_return else "فاتورة بيع",
                "sort_key": (
                    s.receipt.sale_year,
                    s.receipt.sale_month,
                    3 if is_return else 4,
                    s.receipt.receipt_number or 0,
                    s.id,
                ),
            })

        # 4. DEFICITS (Inventory Adjustments)
        for adj in InventoryAdjustment.objects.filter(item=item, is_deleted=False):
            unit_cost = float(resolve_price(item, adj.month, adj.year))
            loss_amount = float(adj.quantity) * unit_cost
            raw_events.append({
                "type": "DEFICIT",
                "year": adj.year,
                "month": adj.month,
                "quantity": adj.quantity,
                "unit_cost": unit_cost,
                "loss_amount": loss_amount,
                "reason": adj.reason or "عجز مخزن",
                "description": "تسوية عجز مخزن",
                "sort_key": (adj.year, adj.month, 5, 0, adj.id),
            })

        # 5. COMMISSION CHANGES (CommissionHistory)
        for comm in CommissionHistory.objects.filter(item=item, is_deleted=False):
            raw_events.append({
                "type": "COMMISSION_CHANGE",
                "year": comm.activation_year,
                "month": comm.activation_month,
                "commission_amount": float(comm.commission_amount),
                "description": f"تعديل المندبة ({float(comm.commission_amount)})",
                "sort_key": (comm.activation_year, comm.activation_month, 0, 1, comm.id),
            })

        raw_events.sort(key=lambda x: x["sort_key"])

        timeline = []
        running_stock = 0
        last_purchase_price = float(item.initial_purchase_price)

        monthly_summary_dict = {}
        total_cash_profit = 0.0
        total_installment_profit = 0.0
        total_deficit_loss = 0.0

        for i, ev in enumerate(raw_events):
            ev_type = ev["type"]
            qty = ev.get("quantity", 0)
            ym = f"{ev['year']}-{ev['month']:02d}"
            fin_ym = f"{ev.get('fin_year', ev['year'])}-{ev.get('fin_month', ev['month']):02d}"

            if ym not in monthly_summary_dict:
                monthly_summary_dict[ym] = {
                    "year": ev["year"],
                    "month": ev["month"],
                    "incoming": 0,
                    "outgoing": 0,
                    "sales_profit": 0.0,
                    "deficit_loss": 0.0,
                    "net_profit": 0.0,
                    "running_stock": 0,
                }
            if fin_ym not in monthly_summary_dict:
                monthly_summary_dict[fin_ym] = {
                    "year": ev.get("fin_year", ev["year"]),
                    "month": ev.get("fin_month", ev["month"]),
                    "incoming": 0,
                    "outgoing": 0,
                    "sales_profit": 0.0,
                    "deficit_loss": 0.0,
                    "net_profit": 0.0,
                    "running_stock": 0,
                }

            is_price_change = False
            if ev_type == "INITIAL":
                running_stock += qty
                monthly_summary_dict[ym]["incoming"] += qty
                last_purchase_price = ev["price"]

            elif ev_type == "PURCHASE":
                running_stock += qty
                monthly_summary_dict[ym]["incoming"] += qty
                if ev["price"] != last_purchase_price:
                    is_price_change = True
                    last_purchase_price = ev["price"]

            elif ev_type == "RETURN":
                running_stock -= qty
                monthly_summary_dict[ym]["outgoing"] += qty

            elif ev_type == "SALE_RETURN":
                running_stock += qty
                monthly_summary_dict[ym]["incoming"] += qty
                np = ev.get("net_profit", 0.0)
                if ev.get("is_cash_sale"):
                    total_cash_profit += np
                else:
                    total_installment_profit += np
                monthly_summary_dict[fin_ym]["sales_profit"] += np

            elif ev_type == "SALE":
                running_stock -= qty
                monthly_summary_dict[ym]["outgoing"] += qty
                np = ev.get("net_profit", 0.0)
                if ev.get("is_cash_sale"):
                    total_cash_profit += np
                else:
                    total_installment_profit += np
                monthly_summary_dict[fin_ym]["sales_profit"] += np

            elif ev_type == "DEFICIT":
                running_stock -= qty
                monthly_summary_dict[ym]["outgoing"] += qty
                loss = ev.get("loss_amount", 0.0)
                total_deficit_loss += loss
                monthly_summary_dict[ym]["deficit_loss"] += loss

            elif ev_type == "COMMISSION_CHANGE":
                pass

            # Check if this is the last event of this month (month boundary)
            is_month_end = (i == len(raw_events) - 1 or 
                            (raw_events[i + 1]["year"], raw_events[i + 1]["month"]) != (ev["year"], ev["month"]))
            if is_month_end:
                running_stock = max(0, running_stock)

            ev["running_stock"] = max(0, running_stock)
            ev["is_price_change"] = is_price_change
            del ev["sort_key"]
            timeline.append(ev)

            monthly_summary_dict[ym]["running_stock"] = max(0, running_stock)

        for m_data in monthly_summary_dict.values():
            m_data["net_profit"] = m_data["sales_profit"] - m_data["deficit_loss"]

        monthly_summary = [v for _, v in sorted(monthly_summary_dict.items())]

        total_profit = (total_cash_profit + total_installment_profit) - total_deficit_loss
        dashboard_metrics = {
            "cash_profit": total_cash_profit,
            "installment_profit": total_installment_profit,
            "deficit_loss": total_deficit_loss,
            "total_profit": total_profit,
        }

        now = timezone.now()
        current_stock = item.get_stock_at_date(now.month, now.year)
        current_purchase_price = float(item.get_price_at_date(now.month, now.year))
        current_commission = float(item.get_commission_at_date(now.month, now.year))

        total_purchased_qty = sum(ev["quantity"] for ev in timeline if ev["type"] == "PURCHASE")
        total_sold_qty = sum(ev["quantity"] for ev in timeline if ev["type"] == "SALE")
        total_deficit_qty = sum(ev["quantity"] for ev in timeline if ev["type"] == "DEFICIT")

        item_info = {
            "id": item.id,
            "name": item.name,
            "initial_quantity": item.initial_quantity,
            "initial_purchase_price": float(item.initial_purchase_price),
            "initial_commission_amount": float(item.initial_commission_amount),
            "initial_month": item.initial_month,
            "initial_year": item.initial_year,
            "current_stock": current_stock,
            "current_purchase_price": current_purchase_price,
            "current_commission": current_commission,
            "total_purchased_qty": total_purchased_qty,
            "total_sold_qty": total_sold_qty,
            "total_deficit_qty": total_deficit_qty,
            "total_deficit_loss": total_deficit_loss,
        }

        return Response({
            "item": item_info,
            "item_info": item_info,
            "timeline": timeline,
            "monthly_summary": monthly_summary,
            "dashboard_metrics": dashboard_metrics,
        })


class CommissionHistoryViewSet(SoftDeleteModelViewSet):
    queryset = CommissionHistory.objects.select_related("item").all()
    serializer_class = CommissionHistorySerializer

    def create(self, request, *args, **kwargs):
        item_id = request.data.get("item")
        activation_month = request.data.get("activation_month")
        activation_year = request.data.get("activation_year")
        commission_amount = request.data.get("commission_amount")

        if item_id and activation_month and activation_year:
            existing = CommissionHistory.all_objects.filter(
                item_id=item_id,
                activation_month=int(activation_month),
                activation_year=int(activation_year)
            ).first()
            if existing:
                existing.commission_amount = commission_amount
                existing.is_deleted = False
                existing.save()
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().order_by("-activation_year", "-activation_month")
        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(item__branch_id=branch_id)
        item_id = self.request.query_params.get("item_id")
        if item_id:
            qs = qs.filter(item__id=item_id)
        return qs


class InventoryAdjustmentViewSet(SoftDeleteModelViewSet):
    queryset = InventoryAdjustment.objects.select_related("item", "item__branch").all()
    serializer_class = InventoryAdjustmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = get_request_branch_id(self.request)
        if branch_id:
            qs = qs.filter(item__branch_id=branch_id)
        item_id = self.request.query_params.get("item_id")
        if item_id:
            qs = qs.filter(item__id=item_id)
        return qs
