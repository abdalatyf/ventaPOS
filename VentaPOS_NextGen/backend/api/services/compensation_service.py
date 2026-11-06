"""
Compensation Service Layer for VentaPOS NextGen.
Calculates salesperson monthly sales commissions (مندبة), collection commissions,
and net salaries taking into account returns in their original sale month.
"""
from django.db.models import Sum, Count, Q
import calendar
import datetime


def calculate_branch_salespersons_performance(branch_id, month, year, get_cached_comm=None, coll_rate=None, salesperson_id=None, area=None):
    """
    Computes performance and due salary for active salespersons in a branch for a given month/year.
    Supports optional salesperson_id and area filters.
    Optimized with bulk grouped queries and B-Tree date range scanning.
    Returns:
    {
        'salespersons': [list of dicts per salesperson],
        'totals': {
            'grand_total_cash': float,
            'grand_total_credit': float,
            'grand_total_down_payments': float,
            'grand_total_sales': float,
            'grand_total_collected': float,
            'grand_total_comm_sales': float,
            'grand_total_comm_coll': float,
            'grand_total_due': float
        },
        'auto_salaries_sum': float
    }
    """
    from api.models import Salesperson, Receipt, SaleItem, InstallmentPayment, InventoryItem
    from api.services.stock_service import get_bulk_commission_resolver
    from api.services.financial_service import get_collection_commission_rate

    if coll_rate is None:
        coll_rate = get_collection_commission_rate()

    if get_cached_comm is None:
        branch_item_ids = list(InventoryItem.objects.filter(branch_id=branch_id, is_deleted=False).values_list('id', flat=True))
        get_cached_comm = get_bulk_commission_resolver(branch_item_ids)

    sp_query = Q(branch_id=branch_id, is_deleted=False)
    if salesperson_id:
        sp_query &= Q(id=salesperson_id)

    salespersons = list(Salesperson.objects.filter(sp_query))

    if not salespersons:
        return {
            "salespersons": [],
            "totals": {
                "grand_total_cash": 0,
                "grand_total_credit": 0,
                "grand_total_down_payments": 0,
                "grand_total_sales": 0,
                "grand_total_collected": 0,
                "grand_total_comm_sales": 0,
                "grand_total_comm_coll": 0,
                "grand_total_due": 0,
            },
            "auto_salaries_sum": 0.0,
        }

    sp_data = {
        sp.id: {
            "receipts_count": 0,
            "cash_sales_raw": 0,
            "credit_sales_raw": 0,
            "down_payments": 0,
            "cash_returns": 0,
            "credit_returns": 0,
            "collected": 0,
            "comm_sales": 0.0,
        }
        for sp in salespersons
    }

    # 1. Non-return receipts bulk grouped
    non_return_qs = Receipt.objects.filter(
        branch_id=branch_id,
        sale_month=month,
        sale_year=year,
        is_deleted=False,
    ).exclude(receipt_type="RETURN")

    if salesperson_id:
        non_return_qs = non_return_qs.filter(salesperson_id=salesperson_id)
    if area:
        non_return_qs = non_return_qs.filter(area__icontains=area)

    non_return_receipts = (
        non_return_qs
        .values("salesperson_id")
        .annotate(
            count=Count("id"),
            cash_sales=Sum("total_amount", filter=Q(is_cash_sale=True)),
            credit_sales=Sum("total_amount", filter=Q(is_cash_sale=False)),
            down_payments=Sum("down_payment", filter=Q(is_cash_sale=False)),
        )
    )
    for row in non_return_receipts:
        sid = row["salesperson_id"]
        if sid in sp_data:
            sp_data[sid]["receipts_count"] = row["count"] or 0
            sp_data[sid]["cash_sales_raw"] = row["cash_sales"] or 0
            sp_data[sid]["credit_sales_raw"] = row["credit_sales"] or 0
            sp_data[sid]["down_payments"] = row["down_payments"] or 0

    # 2. Return receipts bulk
    return_qs = Receipt.objects.filter(
        branch_id=branch_id,
        receipt_type="RETURN",
        is_deleted=False,
    ).filter(
        Q(parent_receipt__sale_month=month, parent_receipt__sale_year=year)
        | Q(parent_receipt__isnull=True, sale_month=month, sale_year=year)
    )
    if salesperson_id:
        return_qs = return_qs.filter(
            Q(salesperson_id=salesperson_id) | Q(parent_receipt__salesperson_id=salesperson_id)
        )
    if area:
        return_qs = return_qs.filter(
            Q(area__icontains=area) | Q(parent_receipt__area__icontains=area)
        )

    return_receipts = list(return_qs.select_related("parent_receipt"))
    for ret in return_receipts:
        affected_sp_ids = set()
        if ret.salesperson_id and ret.salesperson_id in sp_data:
            affected_sp_ids.add(ret.salesperson_id)
        if ret.parent_receipt and ret.parent_receipt.salesperson_id and ret.parent_receipt.salesperson_id in sp_data:
            affected_sp_ids.add(ret.parent_receipt.salesperson_id)

        amt = ret.total_amount or 0
        for sid in affected_sp_ids:
            if ret.is_cash_sale:
                sp_data[sid]["cash_returns"] += amt
            else:
                sp_data[sid]["credit_returns"] += amt

    # 3. Installment collections with indexed date range
    _, last_day = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, last_day)

    collections_filter = Q(
        receipt__branch_id=branch_id,
        receipt__is_confirmed=True,
        payment_date__range=(start_date, end_date),
        is_deleted=False,
        receipt__is_deleted=False,
    )
    if salesperson_id:
        collections_filter &= Q(receipt__salesperson_id=salesperson_id)
    if area:
        collections_filter &= Q(receipt__area__icontains=area)

    collections_qs = InstallmentPayment.objects.filter(collections_filter)
    collections = (
        collections_qs
        .values("receipt__salesperson_id")
        .annotate(total=Sum("amount"))
    )
    for row in collections:
        sid = row["receipt__salesperson_id"]
        if sid in sp_data:
            sp_data[sid]["collected"] = row["total"] or 0

    # 4. Sale items (Sales commission)
    sale_items_qs = SaleItem.objects.filter(
        receipt__branch_id=branch_id,
        receipt__sale_month=month,
        receipt__sale_year=year,
        receipt__is_deleted=False,
        is_deleted=False,
    ).exclude(receipt__receipt_type="RETURN")

    if salesperson_id:
        sale_items_qs = sale_items_qs.filter(receipt__salesperson_id=salesperson_id)
    if area:
        sale_items_qs = sale_items_qs.filter(receipt__area__icontains=area)

    sale_items = sale_items_qs.select_related("inventory_item", "receipt")
    for item in sale_items:
        sid = item.receipt.salesperson_id
        if sid in sp_data:
            qty = item.quantity
            comm_unit = get_cached_comm(item.inventory_item, item.receipt.sale_month, item.receipt.sale_year)
            sp_data[sid]["comm_sales"] += float(qty) * float(comm_unit)

    # 5. Return items (Commission deduction)
    return_items_qs = SaleItem.objects.filter(
        receipt__branch_id=branch_id,
        receipt__receipt_type="RETURN",
        receipt__is_deleted=False,
        is_deleted=False,
    ).filter(
        Q(receipt__parent_receipt__sale_month=month, receipt__parent_receipt__sale_year=year)
        | Q(receipt__parent_receipt__isnull=True, receipt__sale_month=month, receipt__sale_year=year)
    )
    if salesperson_id:
        return_items_qs = return_items_qs.filter(
            Q(receipt__salesperson_id=salesperson_id) | Q(receipt__parent_receipt__salesperson_id=salesperson_id)
        )
    if area:
        return_items_qs = return_items_qs.filter(
            Q(receipt__area__icontains=area) | Q(receipt__parent_receipt__area__icontains=area)
        )

    return_items = return_items_qs.select_related("inventory_item", "receipt", "receipt__parent_receipt")
    for item in return_items:
        affected_sp_ids = set()
        if item.receipt.salesperson_id and item.receipt.salesperson_id in sp_data:
            affected_sp_ids.add(item.receipt.salesperson_id)
        if (
            item.receipt.parent_receipt
            and item.receipt.parent_receipt.salesperson_id
            and item.receipt.parent_receipt.salesperson_id in sp_data
        ):
            affected_sp_ids.add(item.receipt.parent_receipt.salesperson_id)

        if not affected_sp_ids:
            continue

        qty = item.quantity
        orig_m = item.receipt.parent_receipt.sale_month if item.receipt.parent_receipt else item.receipt.sale_month
        orig_y = item.receipt.parent_receipt.sale_year if item.receipt.parent_receipt else item.receipt.sale_year
        comm_unit = get_cached_comm(item.inventory_item, orig_m, orig_y)
        item_comm_deduction = float(qty) * float(comm_unit)

        for sid in affected_sp_ids:
            sp_data[sid]["comm_sales"] -= item_comm_deduction

    # 6. Aggregate results
    list_data = []
    grand_total_cash = 0
    grand_total_credit = 0
    grand_total_down_payments = 0
    grand_total_collected = 0
    grand_total_comm_sales = 0
    grand_total_comm_coll = 0

    for sp in salespersons:
        d = sp_data[sp.id]
        cash_sales = d["cash_sales_raw"] - d["cash_returns"]
        credit_sales = d["credit_sales_raw"] - d["credit_returns"]
        down_payments = d["down_payments"]
        total_sales_val = cash_sales + credit_sales
        collected = d["collected"]
        comm_sales = d["comm_sales"]
        comm_coll = float(collected) * coll_rate
        due_salary = float(comm_sales) + float(comm_coll)

        # If area is filtered, exclude salespersons with zero transactions in that area
        if area and d["receipts_count"] == 0 and collected == 0 and total_sales_val == 0 and d["cash_returns"] == 0 and d["credit_returns"] == 0 and comm_sales == 0:
            continue

        grand_total_cash += cash_sales
        grand_total_credit += credit_sales
        grand_total_down_payments += down_payments
        grand_total_collected += float(collected)
        grand_total_comm_sales += float(comm_sales)
        grand_total_comm_coll += float(comm_coll)

        list_data.append({
            "salesperson_id": str(sp.id),
            "id": sp.id,
            "name": sp.name,
            "receipts_count": d["receipts_count"],
            "cash_sales": cash_sales,
            "credit_sales": credit_sales,
            "down_payments": down_payments,
            "total_sales_val": total_sales_val,
            "collected": collected,
            "comm_sales": comm_sales,
            "comm_coll": comm_coll,
            "due_salary": due_salary
        })

    totals = {
        "grand_total_cash": grand_total_cash,
        "grand_total_credit": grand_total_credit,
        "grand_total_down_payments": grand_total_down_payments,
        "grand_total_sales": (grand_total_cash + grand_total_credit),
        "grand_total_collected": grand_total_collected,
        "grand_total_comm_sales": grand_total_comm_sales,
        "grand_total_comm_coll": grand_total_comm_coll,
        "grand_total_due": (float(grand_total_comm_sales) + float(grand_total_comm_coll))
    }

    return {
        "salespersons": list_data,
        "totals": totals,
        "auto_salaries_sum": totals["grand_total_due"]
    }
