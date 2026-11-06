"""
Financial Service Layer for VentaPOS NextGen.
Centralizes financial calculations, commission rates, cash drawer flows,
credit reserves, and deficit loss valuations.
"""
from django.db.models import Sum, F, Q
from decimal import Decimal


def get_collection_commission_rate():
    """
    Returns the company-wide collection commission rate as a float decimal (e.g. 0.10 for 10%).
    Defaults to 0.10 if not configured.
    """
    from api.models import CompanySetting
    setting = CompanySetting.objects.first()
    if setting and setting.collection_commission_rate is not None:
        try:
            val = float(setting.collection_commission_rate)
            return (val / 100.0) if val > 1.0 else val
        except (ValueError, TypeError):
            pass
    return 0.10


def calculate_upfront_credit_reserve(credit_receipts, credit_returns, coll_rate=None):
    """
    Calculates upfront credit collection reserve deduction for Card 1 profit:
    net_credit_debt = max(0, (credit_rev - credit_down_payments) - credit_returns_rev)
    reserve_deduction = net_credit_debt * coll_rate
    """
    if coll_rate is None:
        coll_rate = get_collection_commission_rate()

    credit_rev_sum = credit_receipts.aggregate(s=Sum('total_amount'))['s'] or 0
    credit_down_payment_sum = credit_receipts.aggregate(s=Sum('down_payment'))['s'] or 0
    credit_returns_rev_sum = credit_returns.aggregate(s=Sum('total_amount'))['s'] or 0

    net_credit_debt = max(0.0, float(credit_rev_sum - credit_down_payment_sum) - float(credit_returns_rev_sum))
    return net_credit_debt * coll_rate


def calculate_cash_drawer_summary(branch_id, month, year, auto_salaries=0.0):
    """
    Calculates the 10-point cash flow breakdown for Card 2 (تفاصيل السيولة):
    Inflows: Cash sales, Down payments, Installment collections, Purchase returns
    Outflows: Operating expenses, Auto salaries, Purchases, Sales return cash refunds
    Net cash in hand: total_cash_inflow - total_cash_outgoing
    """
    from api.models import Receipt, InstallmentPayment, PurchaseInvoiceItem, Expense, ClientLicense

    active_lic = ClientLicense.objects.filter(is_active=True, is_deleted=False).exclude(machine_id="DEMO_MACHINE").order_by('-expiry_date').first()
    is_pre_license_month = False
    if active_lic and active_lic.start_date:
        if (year < active_lic.start_date.year) or (year == active_lic.start_date.year and month < active_lic.start_date.month):
            is_pre_license_month = True

    # 1. Cash Inflows
    if is_pre_license_month:
        cash_sales_inflow = 0
        down_payment_inflow = 0
    else:
        cash_sales_inflow = Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month, sale_year=year,
            is_cash_sale=True,
            is_deleted=False
        ).exclude(receipt_type='RETURN').aggregate(s=Sum('total_amount'))['s'] or 0

        down_payment_inflow = Receipt.objects.filter(
            branch_id=branch_id,
            sale_month=month, sale_year=year,
            is_cash_sale=False,
            is_deleted=False
        ).exclude(receipt_type='RETURN').aggregate(s=Sum('down_payment'))['s'] or 0

    import calendar
    import datetime
    _, last_day = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, last_day)

    collection_inflow = InstallmentPayment.objects.filter(
        receipt__branch_id=branch_id,
        receipt__is_confirmed=True,
        payment_date__range=(start_date, end_date),
        is_deleted=False,
        receipt__is_deleted=False
    ).aggregate(s=Sum('amount'))['s'] or 0

    purchase_returns_total = PurchaseInvoiceItem.objects.filter(
        invoice__branch_id=branch_id,
        invoice__invoice_month=month, invoice__invoice_year=year,
        invoice__invoice_type="RETURN",
        is_deleted=False,
        invoice__is_deleted=False
    ).aggregate(s=Sum(F('quantity') * F('purchase_price')))['s'] or 0

    total_cash_inflow = (
        float(cash_sales_inflow)
        + float(down_payment_inflow)
        + float(collection_inflow)
        + float(purchase_returns_total)
    )

    # 2. Cash Outflows
    total_purchases = PurchaseInvoiceItem.objects.filter(
        invoice__branch_id=branch_id,
        invoice__invoice_month=month, invoice__invoice_year=year,
        invoice__invoice_type="PURCHASE",
        is_deleted=False,
        invoice__is_deleted=False
    ).aggregate(s=Sum(F('quantity') * F('purchase_price')))['s'] or 0

    sales_returns_cash = Receipt.objects.filter(
        branch_id=branch_id,
        receipt_type='RETURN',
        sale_month=month, sale_year=year,
        is_deleted=False
    ).aggregate(s=Sum('down_payment'))['s'] or 0

    operating_expenses = Expense.objects.filter(
        branch_id=branch_id,
        expense_month=month, expense_year=year,
        is_deleted=False
    ).aggregate(s=Sum('amount'))['s'] or 0

    total_cash_outgoing = (
        float(operating_expenses)
        + float(auto_salaries)
        + float(total_purchases)
        + float(sales_returns_cash)
    )
    net_cash_in_hand = float(total_cash_inflow) - total_cash_outgoing

    return {
        "cash_sales_inflow": cash_sales_inflow,
        "down_payment_inflow": down_payment_inflow,
        "collection_inflow": collection_inflow,
        "purchase_returns_total": purchase_returns_total,
        "total_cash_inflow": total_cash_inflow,
        "total_purchases": total_purchases,
        "sales_returns_cash": sales_returns_cash,
        "operating_expenses": operating_expenses,
        "auto_salaries": auto_salaries,
        "net_cash_in_hand": net_cash_in_hand,
        "safe_balance": net_cash_in_hand,
    }


def calculate_deficit_loss(branch_id, month, year, price_resolver=None):
    """
    Calculates total inventory deficit loss for a branch and month:
    sum(adjustment.quantity * price_at_date(item, month, year))
    """
    from api.models import InventoryAdjustment
    branch_deficit_adjustments = InventoryAdjustment.objects.filter(
        item__branch_id=branch_id,
        month=month, year=year,
        is_deleted=False
    ).select_related('item')

    total_loss = 0.0
    for adj in branch_deficit_adjustments:
        if price_resolver is not None:
            price = price_resolver(adj.item, month, year)
            if not price and hasattr(adj.item, 'get_price_at_date'):
                price = adj.item.get_price_at_date(month, year)
        else:
            price = adj.item.get_price_at_date(month, year)
        total_loss += float(adj.quantity) * float(price)

    return total_loss

