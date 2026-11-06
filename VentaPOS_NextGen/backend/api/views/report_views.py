"""
Report and Dashboard Views for VentaPOS NextGen:
DefaultDateView, DashboardReportView, SalespersonPerformanceReportView,
InventoryMovementReportView, ProfitAndLossReportView, CashDrawerReportView,
InstallmentsReportView.
"""
from collections import defaultdict
from django.db.models import Sum, Count, F, ExpressionWrapper, IntegerField, Q
from django.utils import timezone
from rest_framework import views, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.models import (
    Branch,
    Receipt,
    SaleItem,
    InstallmentPayment,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Expense,
    InventoryItem,
    InventoryAdjustment,
    ClientLicense,
)
from api.services.stock_service import (
    calculate_bulk_stock_timeline,
    get_bulk_price_resolver,
    get_bulk_commission_resolver,
)
from api.services.financial_service import (
    get_collection_commission_rate,
    calculate_upfront_credit_reserve,
    calculate_cash_drawer_summary,
    calculate_deficit_loss,
)
from api.services.compensation_service import (
    calculate_branch_salespersons_performance,
)
from api.print_utils import generate_and_open_pdf, to_arabic_numerals
from django.template.loader import render_to_string
from api.models import CompanySetting
from .base import to_english_numerals, get_default_date, get_request_branch_id


class DefaultDateView(views.APIView):
    def get(self, request):
        branch_id = get_request_branch_id(request)
        try:
            year, month = get_default_date(branch_id=branch_id)
            return Response({"year": year, "month": month})
        except Exception as e:
            now = timezone.now()
            return Response({"year": now.year, "month": now.month, "error": str(e)})


def validate_request_branch(request):
    raw_val = (
        request.query_params.get("branch_id")
        or request.query_params.get("branch")
        or request.headers.get("X-Branch-ID")
    )
    if raw_val is None or str(raw_val).strip() == "":
        raise ValidationError({"branch_id": ["This field is required."]})
    branch_id = get_request_branch_id(request)
    if branch_id is None:
        raise ValidationError({"branch_id": ["Invalid ID format."]})
    try:
        Branch.objects.get(id=branch_id, is_deleted=False)
    except Branch.DoesNotExist:
        raise ValidationError({"branch_id": ["Branch does not exist or does not belong to this tenant."]})
    return branch_id


class DashboardReportView(views.APIView):
    def get(self, request):
        branch_id = validate_request_branch(request)

        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        now = timezone.now()
        month = int(month_str) if month_str.isdigit() else now.month
        year = int(year_str) if year_str.isdigit() else now.year

        active_lic = ClientLicense.objects.filter(is_active=True, is_deleted=False).exclude(machine_id="DEMO_MACHINE").order_by('-expiry_date').first()
        is_pre_license_month = False
        if active_lic and active_lic.start_date:
            if (year < active_lic.start_date.year) or (year == active_lic.start_date.year and month < active_lic.start_date.month):
                is_pre_license_month = True

        # 1. Revenue & Returns (Card 1)
        if is_pre_license_month:
            sales_receipts = Receipt.objects.none()
            return_receipts = Receipt.objects.none()
        else:
            sales_receipts = Receipt.objects.filter(
                branch_id=branch_id,
                sale_month=month, sale_year=year,
                is_deleted=False
            ).exclude(receipt_type='RETURN')

            return_receipts = Receipt.objects.filter(
                branch_id=branch_id,
                receipt_type='RETURN',
                is_deleted=False
            ).filter(
                Q(parent_receipt__sale_month=month, parent_receipt__sale_year=year) |
                Q(parent_receipt__isnull=True, sale_month=month, sale_year=year)
            )

        sales_rev = sales_receipts.aggregate(s=Sum('total_amount'))['s'] or 0
        returns_rev = return_receipts.aggregate(s=Sum('total_amount'))['s'] or 0
        total_revenue = float(sales_rev) - float(returns_rev)

        # 2. Bulk Resolvers
        branch_item_ids = list(InventoryItem.objects.filter(branch_id=branch_id, is_deleted=False).values_list('id', flat=True))
        get_cached_price = get_bulk_price_resolver(branch_item_ids)
        get_cached_comm = get_bulk_commission_resolver(branch_item_ids)

        # 3. COGS and Sales Commission (Card 1)
        sale_items = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__sale_month=month, receipt__sale_year=year,
            receipt__is_deleted=False,
            is_deleted=False
        ).exclude(receipt__receipt_type='RETURN').select_related('inventory_item', 'receipt')

        total_cogs = 0
        total_sales_comm_fixed = 0
        for item in sale_items:
            qty = item.quantity
            cost_unit = get_cached_price(item.inventory_item, item.receipt.sale_month, item.receipt.sale_year)
            comm_unit = get_cached_comm(item.inventory_item, item.receipt.sale_month, item.receipt.sale_year)
            total_cogs += float(qty) * float(cost_unit)
            total_sales_comm_fixed += float(qty) * float(comm_unit)

        return_sale_items = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__receipt_type='RETURN',
            receipt__is_deleted=False,
            is_deleted=False
        ).filter(
            Q(receipt__parent_receipt__sale_month=month, receipt__parent_receipt__sale_year=year) |
            Q(receipt__parent_receipt__isnull=True, receipt__sale_month=month, receipt__sale_year=year)
        ).select_related('inventory_item', 'receipt')

        for item in return_sale_items:
            qty = item.quantity
            orig_m = item.receipt.parent_receipt.sale_month if item.receipt.parent_receipt else item.receipt.sale_month
            orig_y = item.receipt.parent_receipt.sale_year if item.receipt.parent_receipt else item.receipt.sale_year
            cost_unit = get_cached_price(item.inventory_item, orig_m, orig_y)
            comm_unit = get_cached_comm(item.inventory_item, orig_m, orig_y)
            total_cogs -= float(qty) * float(cost_unit)
            total_sales_comm_fixed -= float(qty) * float(comm_unit)

        # 4. Reserve Deduction (Upfront Credit Reserve for Card 1)
        coll_rate = get_collection_commission_rate()
        credit_receipts = sales_receipts.filter(is_cash_sale=False)
        credit_returns = return_receipts.filter(is_cash_sale=False)
        reserve_deduction = calculate_upfront_credit_reserve(credit_receipts, credit_returns, coll_rate)

        total_sales_commissions = total_sales_comm_fixed
        total_collection_commissions = reserve_deduction

        # 5. Operating Expenses
        operating_expenses = Expense.objects.filter(
            branch_id=branch_id,
            expense_month=month, expense_year=year,
            is_deleted=False
        ).aggregate(s=Sum('amount'))['s'] or 0

        # 6. Auto Salaries
        perf_data = calculate_branch_salespersons_performance(branch_id, month, year, get_cached_comm, coll_rate)
        auto_salaries = perf_data["auto_salaries_sum"]

        # 7. Cash Drawer Summary (Card 2)
        cash_drawer = calculate_cash_drawer_summary(branch_id, month, year, auto_salaries)
        safe_balance = cash_drawer["safe_balance"]

        # 8. Deficit Losses & Estimated Net Profit (Card 1)
        total_deficit_loss = calculate_deficit_loss(branch_id, month, year, get_cached_price)

        estimated_net_profit = float(total_revenue) - (
            float(total_cogs)
            + float(total_sales_commissions)
            + float(total_collection_commissions)
            + float(operating_expenses)
            + float(total_deficit_loss)
        )

        # 9. Current Inventory Value & Low Stock Count
        inventory_items = list(InventoryItem.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        ))
        current_inventory_value = 0
        low_stock_count = 0
        if inventory_items:
            stock_data = calculate_bulk_stock_timeline(inventory_items, month, year, month, year)
            for item in inventory_items:
                c_stock = stock_data[item.id]['get_stock'](month, year)
                c_price = get_cached_price(item, month, year)
                current_inventory_value += c_stock * c_price
                if c_stock <= 3:
                    low_stock_count += 1

        # 10. Avg Basket Size
        receipt_count = Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month, sale_year=year,
            is_deleted=False
        ).count()
        avg_basket_size = total_revenue // receipt_count if receipt_count > 0 else 0

        # 11. Top Products
        top_products_qs = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__sale_month=month, receipt__sale_year=year,
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
            sale_month=month, sale_year=year,
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
            "period": {"year": year, "month": month},
            "kpis": {
                "safe_balance": safe_balance,
                "total_revenue": total_revenue,
                "total_cogs": total_cogs,
                "total_sales_commissions": total_sales_commissions,
                "total_collection_commissions": total_collection_commissions,
                "total_deficit_loss": total_deficit_loss,
                "estimated_net_profit": estimated_net_profit,
                "current_inventory_value": current_inventory_value,
                "low_stock_count": low_stock_count,
                "avg_basket_size": avg_basket_size
            },
            "cash_drawer_summary": cash_drawer,
            "top_products": top_products,
            "top_areas": top_areas
        })


class SalespersonPerformanceReportView(views.APIView):
    def get(self, request):
        branch_id = validate_request_branch(request)

        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        now = timezone.now()
        month = int(month_str) if month_str.isdigit() else now.month
        year = int(year_str) if year_str.isdigit() else now.year

        perf_data = calculate_branch_salespersons_performance(branch_id, month, year)

        return Response({
            "totals": perf_data["totals"],
            "salespersons": perf_data["salespersons"],
            "results": perf_data["salespersons"]
        })


class InventoryMovementReportView(views.APIView):
    def get(self, request):
        branch_id = validate_request_branch(request)

        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        sp_id_str = request.query_params.get("salesperson_id", "").strip()
        salesperson_id = None
        if sp_id_str:
            try:
                salesperson_id = int(to_english_numerals(sp_id_str))
            except ValueError:
                pass

        now = timezone.now()
        month = int(month_str) if month_str.isdigit() else now.month
        year = int(year_str) if year_str.isdigit() else now.year

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

        items = list(inventory_items)
        items_list = []
        total_inventory_value = 0

        total_adjustments_count = InventoryAdjustment.objects.filter(
            item__branch_id=branch_id,
            month=month, year=year,
            is_deleted=False
        ).count()

        if items:
            stock_data = calculate_bulk_stock_timeline(items, prev_month, prev_year, month, year)
            resolve_price = get_bulk_price_resolver(items)

            sp_sales_map = defaultdict(lambda: {'sales': 0, 'sales_returns': 0})
            if salesperson_id:
                sp_sales_qs = SaleItem.objects.filter(
                    receipt__branch_id=branch_id,
                    receipt__salesperson_id=salesperson_id,
                    receipt__sale_month=month, receipt__sale_year=year,
                    inventory_item_id__in=[item.id for item in items],
                    is_deleted=False,
                    receipt__is_deleted=False
                ).values('inventory_item_id', 'receipt__receipt_type').annotate(s=Sum('quantity'))
                for row in sp_sales_qs:
                    iid = row['inventory_item_id']
                    rtype = row['receipt__receipt_type']
                    qty = row['s'] or 0
                    if rtype == 'SALE':
                        sp_sales_map[iid]['sales'] += qty
                    elif rtype == 'RETURN':
                        sp_sales_map[iid]['sales_returns'] += qty

            for item in items:
                item_info = stock_data.get(item.id, {})
                get_stock = item_info.get('get_stock', lambda m, y: 0)
                movements = item_info.get('movements', {}).get((year, month), {
                    'purchases': 0, 'purchase_returns': 0, 'sales': 0, 'sales_returns': 0, 'deficit': 0
                })

                opening_stock = get_stock(prev_month, prev_year)
                if item.initial_year == year and item.initial_month == month:
                    opening_stock += item.initial_quantity

                purchases = movements['purchases']
                returns = movements['purchase_returns']

                if salesperson_id:
                    sales = sp_sales_map[item.id]['sales']
                    sales_returns = sp_sales_map[item.id]['sales_returns']
                else:
                    sales = movements['sales']
                    sales_returns = movements['sales_returns']

                surplus = 0
                deficit = movements['deficit']

                final_stock = get_stock(month, year)
                unit_cost = resolve_price(item, month, year)
                total_value = final_stock * unit_cost
                deficit_loss = deficit * unit_cost

                total_inventory_value += total_value

                items_list.append({
                    "product_id": str(item.id),
                    "id": item.id,
                    "product_name": item.name,
                    "opening_stock": opening_stock,
                    "purchases": purchases,
                    "returns": returns,
                    "purchase_returns": returns,
                    "sales_returns": sales_returns,
                    "sales": sales,
                    "surplus": surplus,
                    "deficit": deficit,
                    "deficit_loss": deficit_loss,
                    "final_stock": final_stock,
                    "unit_cost": unit_cost,
                    "total_value": total_value
                })

        return Response({
            "total_inventory_value": total_inventory_value,
            "total_adjustments_count": total_adjustments_count,
            "items": items_list,
            "results": items_list
        })


class ProfitAndLossReportView(views.APIView):
    def get(self, request):
        branch_id = validate_request_branch(request)

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
            receipt__sale_month=month, receipt__sale_year=year,
            receipt__is_deleted=False,
            is_deleted=False
        ).exclude(receipt__receipt_type='RETURN')
        if salesperson_id:
            sale_items_qs = sale_items_qs.filter(receipt__salesperson_id=salesperson_id)

        return_items_qs = SaleItem.objects.filter(
            receipt__branch_id=branch_id,
            receipt__receipt_type='RETURN',
            receipt__is_deleted=False,
            is_deleted=False
        ).filter(
            Q(receipt__parent_receipt__sale_month=month, receipt__parent_receipt__sale_year=year) |
            Q(receipt__parent_receipt__isnull=True, receipt__sale_month=month, receipt__sale_year=year)
        )
        if salesperson_id:
            return_items_qs = return_items_qs.filter(
                Q(receipt__salesperson_id=salesperson_id) |
                Q(receipt__parent_receipt__salesperson_id=salesperson_id)
            )

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

        for item in return_items_qs.select_related('inventory_item', 'receipt'):
            item_id = item.inventory_item.id
            is_cash = item.receipt.is_cash_sale

            group = cash_groups if is_cash else installment_groups

            if item_id in group:
                group[item_id]["qty"] -= item.quantity
                group[item_id]["total_rev"] -= item.quantity * item.unit_price
                if not is_cash:
                    if "return_items" not in group[item_id]:
                        group[item_id]["return_items"] = []
                    group[item_id]["return_items"].append(item)

        cash_sales_profitability = []
        installment_sales_profitability = []

        grand_revenue = 0
        grand_cost = 0
        grand_commission = 0

        all_item_ids = list(set(list(cash_groups.keys()) + list(installment_groups.keys())))
        resolve_price = get_bulk_price_resolver(all_item_ids)
        resolve_commission = get_bulk_commission_resolver(all_item_ids)

        # Cash sales calculations
        for item_id, data in cash_groups.items():
            item = data["item"]
            qty = max(0, data["qty"])
            total_rev = max(0.0, float(data["total_rev"]))

            avg_sell = total_rev // qty if qty > 0 else 0
            cost_per_unit = float(resolve_price(item, month, year))
            total_cost = float(qty) * cost_per_unit
            sales_comm_per_unit = float(resolve_commission(item, month, year))
            total_sales_comm = float(qty) * sales_comm_per_unit

            coll_comm_per_unit = 0
            total_coll_comm = 0.0

            total_profit = total_rev - total_cost - total_sales_comm - total_coll_comm
            avg_profit = total_profit // qty if qty > 0 else 0

            grand_revenue += total_rev
            grand_cost += total_cost
            grand_commission += (total_sales_comm + total_coll_comm)

            cash_sales_profitability.append({
                "id": str(item.id),
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
        coll_rate = get_collection_commission_rate()
        for item_id, data in installment_groups.items():
            item = data["item"]
            qty = max(0, data["qty"])
            total_rev = max(0.0, float(data["total_rev"]))

            avg_sell = total_rev // qty if qty > 0 else 0
            cost_per_unit = float(resolve_price(item, month, year))
            total_cost = float(qty) * cost_per_unit
            sales_comm_per_unit = float(resolve_commission(item, month, year))
            total_sales_comm = float(qty) * sales_comm_per_unit

            total_coll_comm = 0.0
            for sale_item in data["sale_items"]:
                receipt = sale_item.receipt
                if receipt.total_amount > 0:
                    item_rev = float(sale_item.quantity * sale_item.unit_price)
                    payment_diff = float(receipt.total_amount - receipt.down_payment)
                    item_coll_comm = (item_rev * payment_diff * coll_rate) / float(receipt.total_amount)
                    total_coll_comm += item_coll_comm

            # Subtract returned credit items' collection commission
            for ret_item in data.get("return_items", []):
                ret_rev = float(ret_item.quantity * ret_item.unit_price)
                total_coll_comm -= (ret_rev * coll_rate)

            total_coll_comm = max(0.0, total_coll_comm)

            coll_comm_per_unit = total_coll_comm / qty if qty > 0 else 0
            total_profit = float(total_rev) - float(total_cost) - float(total_sales_comm) - total_coll_comm
            avg_profit = total_profit / qty if qty > 0 else 0

            grand_revenue += total_rev
            grand_cost += total_cost
            grand_commission += (float(total_sales_comm) + float(total_coll_comm))

            installment_sales_profitability.append({
                "id": str(item.id),
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

        # Operating Expenses
        expenses_total = float(Expense.objects.filter(
            branch_id=branch_id,
            expense_month=month, expense_year=year,
            is_deleted=False
        ).aggregate(s=Sum('amount'))['s'] or 0)

        # Deficit Losses
        deficit_loss = float(calculate_deficit_loss(branch_id, month, year, resolve_price))

        net_profit_final = (
            float(grand_revenue) - float(grand_cost) - float(grand_commission) - float(expenses_total) - float(deficit_loss)
        )

        return Response({
            "summary": {
                "grand_revenue": float(grand_revenue),
                "grand_cost": float(grand_cost),
                "grand_commission": float(grand_commission),
                "expenses_total": float(expenses_total),
                "deficit_loss": float(deficit_loss),
                "net_profit_final": float(net_profit_final)
            },
            "cash_sales_profitability": cash_sales_profitability,
            "installment_sales_profitability": installment_sales_profitability
        })


class CashDrawerReportView(views.APIView):
    def get(self, request):
        branch_id = validate_request_branch(request)

        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        now = timezone.now()
        month = int(month_str) if month_str.isdigit() else now.month
        year = int(year_str) if year_str.isdigit() else now.year

        # 1. Cash Sales receipts
        cash_receipts = Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month, sale_year=year,
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

        # 2. Down payments
        down_payment_receipts = Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month, sale_year=year,
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

        # 3. Collection payments with indexed date range
        import calendar
        import datetime
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, last_day)

        collections_payments = InstallmentPayment.objects.filter(
            receipt__branch_id=branch_id,
            receipt__is_confirmed=True,
            payment_date__range=(start_date, end_date),
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
        branch_id = validate_request_branch(request)

        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        salesperson_id_str = request.query_params.get("salesperson_id")

        sale_from_year_str = request.query_params.get("sale_from_year")
        sale_from_month_str = request.query_params.get("sale_from_month")
        sale_to_year_str = request.query_params.get("sale_to_year")
        sale_to_month_str = request.query_params.get("sale_to_month")

        year = int(year_str) if year_str else None
        month = int(month_str) if month_str else None

        filters = Q(receipt__branch_id=branch_id, receipt__is_confirmed=True, is_deleted=False, receipt__is_deleted=False)

        if year and month:
            import calendar
            import datetime
            _, last_day = calendar.monthrange(year, month)
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, last_day)
            filters &= Q(payment_date__range=(start_date, end_date))
        elif year:
            import datetime
            filters &= Q(payment_date__range=(datetime.date(year, 1, 1), datetime.date(year, 12, 31)))
        elif month:
            filters &= Q(payment_date__month=month)

        if salesperson_id_str:
            try:
                sp_id = int(salesperson_id_str)
                filters &= Q(receipt__salesperson_id=sp_id)
            except ValueError:
                pass

        customer_name = request.query_params.get("customer_name")
        phone = request.query_params.get("phone")
        area = request.query_params.get("area")

        if customer_name:
            filters &= Q(receipt__customer_name__icontains=customer_name)
        if phone:
            filters &= Q(receipt__phone_number__icontains=phone)
        if area:
            filters &= Q(receipt__area__icontains=area)

        installments = InstallmentPayment.objects.filter(filters)

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


class PurchasesReportView(views.APIView):
    """
    GET /api/v1/reports/purchases/
    Dedicated Purchases & Purchase Returns Report.
    Returns 6 KPI summary metrics + detailed invoice rows.
    """
    def get(self, request):
        branch_id = validate_request_branch(request)

        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        supplier_id_str = request.query_params.get("supplier_id", "").strip()
        item_id_str = request.query_params.get("item_id", "").strip()
        invoice_type = request.query_params.get("invoice_type", "").strip()
        invoice_from = request.query_params.get("invoice_from", "").strip()
        invoice_to = request.query_params.get("invoice_to", "").strip()

        filters = Q(branch_id=branch_id, is_deleted=False)

        if year_str.isdigit():
            filters &= Q(invoice_year=int(year_str))
        if month_str.isdigit():
            filters &= Q(invoice_month=int(month_str))

        if supplier_id_str.isdigit():
            filters &= Q(supplier_id=int(supplier_id_str))

        if invoice_type in ("PURCHASE", "RETURN"):
            filters &= Q(invoice_type=invoice_type)

        if invoice_from.isdigit():
            filters &= Q(invoice_number__gte=int(invoice_from))
        if invoice_to.isdigit():
            filters &= Q(invoice_number__lte=int(invoice_to))

        if item_id_str.isdigit():
            filters &= Q(items__inventory_item_id=int(item_id_str), items__is_deleted=False)

        invoices_qs = (
            PurchaseInvoice.objects.filter(filters)
            .distinct()
            .select_related("supplier")
            .prefetch_related("items__inventory_item")
            .order_by("-invoice_year", "-invoice_month", "-invoice_number")
        )

        invoices_list = []
        gross_purchases_amount = 0.0
        gross_returns_amount = 0.0
        purchases_count = 0
        returns_count = 0
        total_items_quantity = 0
        distinct_suppliers = set()

        for inv in invoices_qs:
            items_list = list(inv.items.filter(is_deleted=False).select_related("inventory_item"))
            inv_total = sum(float(it.quantity * it.purchase_price) for it in items_list)
            inv_units = sum(it.quantity for it in items_list)

            if inv.supplier_id:
                distinct_suppliers.add(inv.supplier_id)

            if inv.invoice_type == "RETURN":
                returns_count += 1
                gross_returns_amount += inv_total
                total_items_quantity -= inv_units
            else:
                purchases_count += 1
                gross_purchases_amount += inv_total
                total_items_quantity += inv_units

            summary_parts = [f"{it.inventory_item.name} ({it.quantity})" for it in items_list]
            items_summary = " - ".join(summary_parts) if summary_parts else "بدون بنود"

            invoices_list.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_type": inv.invoice_type,
                "invoice_month": inv.invoice_month,
                "invoice_year": inv.invoice_year,
                "invoice_date": f"{inv.invoice_year}/{inv.invoice_month:02d}",
                "supplier_id": inv.supplier_id,
                "supplier_name": inv.supplier.name if inv.supplier else "مورد عام",
                "items_summary": items_summary,
                "total_units": inv_units,
                "total_cost": inv_total,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            })

        net_purchases_amount = gross_purchases_amount - gross_returns_amount

        summary_data = {
            "total_purchases_amount": net_purchases_amount,
            "gross_purchases_amount": gross_purchases_amount,
            "total_purchases_count": purchases_count,
            "total_returns_count": returns_count,
            "total_returns_amount": gross_returns_amount,
            "total_items_quantity": total_items_quantity,
            "suppliers_count": len(distinct_suppliers),
            # Aliases for frontend convenience
            "purchase_invoices_count": purchases_count,
            "returns_count": returns_count,
            "returns_amount": gross_returns_amount,
            "net_purchases_amount": net_purchases_amount,
            "total_units": total_items_quantity,
        }

        return Response({
            "summary": summary_data,
            "kpis": summary_data,
            "invoices": invoices_list,
        })


class ReportDesktopPrintView(views.APIView):
    def post(self, request):
        title = request.data.get("title")
        if not title:
            return Response({"status": "error", "message": "عنوان التقرير مطلوب."}, status=status.HTTP_400_BAD_REQUEST)

        columns = request.data.get("columns", [])
        if not columns or len(columns) == 0:
            return Response({"status": "error", "message": "أعمدة التقرير مطلوبة."}, status=status.HTTP_400_BAD_REQUEST)

        branch_id = request.data.get("branch_id")
        branch_name = request.data.get("branch_name", "")
        if not branch_name and branch_id:
            try:
                b = Branch.objects.get(id=branch_id)
                branch_name = b.name
            except Exception:
                pass
        if not branch_name:
            branch_name = "الفرع الرئيسي"

        period_label = request.data.get("period_label", "")
        filters_summary = request.data.get("filters_summary", [])
        kpis = request.data.get("kpis", [])
        rows = request.data.get("rows", [])
        footer_row = request.data.get("footer_row", None)
        action_type = request.data.get("action", "print")
        target_printer = request.data.get("target_printer", None)
        orientation = request.data.get("orientation", "portrait")

        company_settings = CompanySetting.objects.first()
        comp_name = company_settings.name if company_settings and company_settings.name else "VentaPOS NextGen"

        formatted_kpis = []
        for k in kpis:
            formatted_kpis.append({
                'label': k.get('label', ''),
                'value': k.get('value', ''),
                'value_ar': to_arabic_numerals(k.get('value', '')),
                'color': k.get('color', 'primary')
            })

        formatted_filters = []
        for f in filters_summary:
            formatted_filters.append({
                'label': f.get('label', ''),
                'value': to_arabic_numerals(f.get('value', ''))
            })

        formatted_rows = []
        for r in rows:
            if isinstance(r, dict) and 'cells' in r:
                cells = []
                for cell in r['cells']:
                    val = cell.get('value', '')
                    cells.append({
                        'value': val,
                        'value_ar': to_arabic_numerals(val),
                        'align': cell.get('align', 'center'),
                        'is_bold': cell.get('is_bold', False),
                        'color': cell.get('color', '')
                    })
                formatted_rows.append({'cells': cells})
            elif isinstance(r, dict):
                cells = []
                for col in columns:
                    col_key = col.get('key') or col.get('id')
                    val = r.get(col_key, '')
                    cells.append({
                        'value': val,
                        'value_ar': to_arabic_numerals(val),
                        'align': col.get('align', 'center'),
                        'is_bold': col.get('is_bold', False),
                        'color': col.get('color', '')
                    })
                formatted_rows.append({'cells': cells})

        formatted_footer = None
        if footer_row:
            formatted_footer = []
            for fcell in footer_row:
                val = fcell.get('value', '')
                formatted_footer.append({
                    'value': val,
                    'value_ar': to_arabic_numerals(val),
                    'align': fcell.get('align', 'center'),
                    'colspan': fcell.get('colspan', None)
                })

        now_str = timezone.now().strftime("%Y/%m/%d %H:%M")

        ctx = {
            'title': title,
            'company_name': comp_name,
            'branch_name': branch_name,
            'period_label': to_arabic_numerals(period_label),
            'printed_at_ar': to_arabic_numerals(now_str),
            'filters_summary': formatted_filters,
            'kpis': formatted_kpis,
            'columns': columns,
            'rows': formatted_rows,
            'footer_row': formatted_footer,
            'orientation': orientation,
            'footer_text': company_settings.footer_text if company_settings and company_settings.footer_text else None
        }

        html_content = render_to_string('api/pdf_report_content.html', ctx)

        if action_type == "view":
            success, result_msg = generate_and_open_pdf(
                html_content, "View_Report",
                target_printer=None, action="view", paper_size="A4"
            )
            if success:
                return Response({"status": "success", "message": result_msg}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": result_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            success, msg = generate_and_open_pdf(
                html_content, "Print_Report",
                target_printer=target_printer, action="print", paper_size="A4"
            )
            if success:
                return Response({"status": "success", "message": msg}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

