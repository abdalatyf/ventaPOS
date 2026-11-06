from collections import defaultdict
from django.db.models import Sum


def calculate_bulk_stock_timeline(items, target_month=None, target_year=None, default_month=None, default_year=None):
    """
    Computes monthly stock timelines and safe available quantities for one or many InventoryItems
    using exactly 3 grouped SQL queries.
    
    Returns a dict keyed by item.id:
    {
        item.id: {
            'safe_available_qty': int,
            'bottleneck_month': int,
            'bottleneck_year': int,
            'stock_at_target': int,
            'current_stock': int,
            'timeline': {(year, month): stock, ...},
            'movements': {(year, month): {'purchases': int, 'purchase_returns': int, 'sales': int, 'sales_returns': int, 'deficit': int}},
            'get_stock': callable(month, year) -> int
        }
    }
    """
    if not items:
        return {}

    first = next(iter(items))
    if isinstance(first, (int, str)):
        from api.models import InventoryItem
        items_list = list(InventoryItem.objects.filter(id__in=items))
    else:
        items_list = list(items)

    if not items_list:
        return {}

    item_ids = [item.id for item in items_list]
    items_map = {item.id: item for item in items_list}

    from api.models import PurchaseInvoiceItem, SaleItem, InventoryAdjustment

    # 1. Purchases & Purchase Returns (Grouped)
    purchases_qs = PurchaseInvoiceItem.objects.filter(
        inventory_item_id__in=item_ids,
        is_deleted=False,
        invoice__is_deleted=False
    ).values(
        'inventory_item_id',
        'invoice__invoice_year',
        'invoice__invoice_month',
        'invoice__invoice_type'
    ).annotate(total_qty=Sum('quantity'))

    # 2. Sales & Sales Returns (Grouped, confirmed only)
    sales_qs = SaleItem.objects.filter(
        inventory_item_id__in=item_ids,
        is_deleted=False,
        receipt__is_deleted=False,
        receipt__is_confirmed=True
    ).values(
        'inventory_item_id',
        'receipt__sale_year',
        'receipt__sale_month',
        'receipt__receipt_type'
    ).annotate(total_qty=Sum('quantity'))

    # 3. Inventory Adjustments / Deficits (Grouped)
    deficits_qs = InventoryAdjustment.objects.filter(
        item_id__in=item_ids,
        is_deleted=False,
        adjustment_type='DEFICIT'
    ).values(
        'item_id',
        'year',
        'month'
    ).annotate(total_qty=Sum('quantity'))

    # Organize transactions by item and (year, month)
    monthly_deltas = defaultdict(lambda: defaultdict(int))
    monthly_movements = defaultdict(lambda: defaultdict(lambda: {
        'purchases': 0, 'purchase_returns': 0, 'sales': 0, 'sales_returns': 0, 'deficit': 0
    }))

    for row in purchases_qs:
        iid = row['inventory_item_id']
        y = row['invoice__invoice_year']
        m = row['invoice__invoice_month']
        qty = row['total_qty'] or 0
        itype = row['invoice__invoice_type']
        if itype == 'PURCHASE':
            monthly_deltas[iid][(y, m)] += qty
            monthly_movements[iid][(y, m)]['purchases'] += qty
        elif itype == 'RETURN':
            monthly_deltas[iid][(y, m)] -= qty
            monthly_movements[iid][(y, m)]['purchase_returns'] += qty

    for row in sales_qs:
        iid = row['inventory_item_id']
        y = row['receipt__sale_year']
        m = row['receipt__sale_month']
        qty = row['total_qty'] or 0
        rtype = row['receipt__receipt_type']
        if rtype == 'SALE':
            monthly_deltas[iid][(y, m)] -= qty
            monthly_movements[iid][(y, m)]['sales'] += qty
        elif rtype == 'RETURN':
            monthly_deltas[iid][(y, m)] += qty
            monthly_movements[iid][(y, m)]['sales_returns'] += qty

    for row in deficits_qs:
        iid = row['item_id']
        y = row['year']
        m = row['month']
        qty = row['total_qty'] or 0
        monthly_deltas[iid][(y, m)] -= qty
        monthly_movements[iid][(y, m)]['deficit'] += qty

    # Resolve default / target dates
    if default_month is None or default_year is None:
        from api.views import get_default_date
        def_year, def_month = get_default_date()
        if default_year is None:
            default_year = def_year
        if default_month is None:
            default_month = def_month

    if target_month is None:
        target_month = default_month
    if target_year is None:
        target_year = default_year

    max_end_year = max(target_year, default_year)
    max_end_month = target_month if target_year > default_year else (
        default_month if default_year > target_year else max(target_month, default_month)
    )

    results = {}

    for item in items_list:
        iid = item.id
        init_m = item.initial_month
        init_y = item.initial_year
        init_qty = item.initial_quantity

        item_deltas = monthly_deltas[iid]
        item_movements = monthly_movements[iid]

        # Calculate stock timeline
        # Exact parity with get_stock_at_date(month, year):
        # If (year, month) < (init_y, init_m): stock = 0
        # If (year, month) >= (init_y, init_m):
        # stock = max(0, init_qty + sum(all deltas with date <= (year, month)))
        
        # Find earliest delta date
        all_dates = list(item_deltas.keys())
        if all_dates:
            min_delta_date = min(all_dates)
            max_delta_date = max(all_dates)
        else:
            min_delta_date = (init_y, init_m)
            max_delta_date = (init_y, init_m)

        # Sum of deltas that occurred strictly before (init_y, init_m)
        prior_deltas = sum(
            delta for date, delta in item_deltas.items()
            if date < (init_y, init_m)
        )

        timeline = {}
        # Walk timeline from (init_y, init_m) to max(end_date, max_delta_date)
        end_y = max(max_end_year, max_delta_date[0])
        end_m = max_end_month if end_y == max_end_year else max_delta_date[1]
        if max_delta_date[0] > max_end_year or (max_delta_date[0] == max_end_year and max_delta_date[1] > max_end_month):
            end_y, end_m = max_delta_date

        curr_y, curr_m = init_y, init_m
        running_unclamped = init_qty + prior_deltas

        while (curr_y, curr_m) <= (end_y, end_m):
            running_unclamped += item_deltas.get((curr_y, curr_m), 0)
            timeline[(curr_y, curr_m)] = max(0, running_unclamped)

            curr_m += 1
            if curr_m > 12:
                curr_m = 1
                curr_y += 1

        def make_stock_getter(i_init_y, i_init_m, i_init_qty, i_deltas, i_timeline):
            def get_stock(m, y):
                if (y, m) < (i_init_y, i_init_m):
                    return 0
                if (y, m) in i_timeline:
                    return i_timeline[(y, m)]
                # Fallback for future months beyond walked range:
                raw = i_init_qty + sum(
                    d for dt, d in i_deltas.items() if dt <= (y, m)
                )
                return max(0, raw)
            return get_stock

        get_stock = make_stock_getter(init_y, init_m, init_qty, item_deltas, timeline)

        stock_at_target = get_stock(target_month, target_year)
        current_stock = get_stock(default_month, default_year)

        # Bottleneck calculation:
        # If (target_year, target_month) >= (default_year, default_month):
        # safe_available_qty = stock_at_target, bottleneck = (target_month, target_year)
        if (target_year, target_month) >= (default_year, default_month):
            safe_qty = stock_at_target
            b_month = target_month
            b_year = target_year
        else:
            min_stock = None
            b_month = target_month
            b_year = target_year
            curr_y, curr_m = target_year, target_month
            while (curr_y, curr_m) <= (default_year, default_month):
                stock = get_stock(curr_m, curr_y)
                if min_stock is None or stock < min_stock:
                    min_stock = stock
                    b_month = curr_m
                    b_year = curr_y

                curr_m += 1
                if curr_m > 12:
                    curr_m = 1
                    curr_y += 1

            safe_qty = min_stock if min_stock is not None else 0

        results[iid] = {
            'safe_available_qty': safe_qty,
            'bottleneck_month': b_month,
            'bottleneck_year': b_year,
            'stock_at_target': stock_at_target,
            'current_stock': current_stock,
            'timeline': timeline,
            'movements': item_movements,
            'get_stock': get_stock,
        }

    return results


def get_bulk_price_resolver(item_ids_or_items):
    """
    Prefetches all historical purchase prices for the specified items in 1 query
    and returns a fast in-memory resolver function:
    resolve_price(item, month, year) -> Decimal

    Exact parity with InventoryItem.get_price_at_date(month, year):
    Returns the purchase_price of the most recent purchase invoice item
    with (invoice_year < year) or (invoice_year == year and invoice_month <= month),
    tie-broken by id descending. If none exists, returns item.initial_purchase_price.
    """
    if not item_ids_or_items:
        return lambda item, month, year: (item.get_price_at_date(month, year) if hasattr(item, 'get_price_at_date') else 0)

    first = next(iter(item_ids_or_items))
    if hasattr(first, 'id'):
        item_ids = [i.id for i in item_ids_or_items]
        initial_prices = {i.id: i.initial_purchase_price for i in item_ids_or_items}
    else:
        item_ids = list(item_ids_or_items)
        initial_prices = {}

    from api.models import PurchaseInvoiceItem

    purchases = PurchaseInvoiceItem.objects.filter(
        inventory_item_id__in=item_ids,
        invoice__invoice_type='PURCHASE',
        is_deleted=False,
        invoice__is_deleted=False
    ).values(
        'inventory_item_id',
        'invoice__invoice_year',
        'invoice__invoice_month',
        'id',
        'purchase_price'
    ).order_by('inventory_item_id', 'invoice__invoice_year', 'invoice__invoice_month', 'id')

    price_history = defaultdict(list)
    for p in purchases:
        price_history[p['inventory_item_id']].append((
            p['invoice__invoice_year'],
            p['invoice__invoice_month'],
            p['id'],
            p['purchase_price']
        ))

    def resolve_price(item, month, year):
        iid = item.id if hasattr(item, 'id') else item
        records = price_history.get(iid, [])
        # Search backwards since records are sorted ascending
        for r_year, r_month, r_id, r_price in reversed(records):
            if (r_year < year) or (r_year == year and r_month <= month):
                return r_price

        if hasattr(item, 'initial_purchase_price'):
            return item.initial_purchase_price
        return initial_prices.get(iid, 0)

    return resolve_price


def get_bulk_commission_resolver(item_ids_or_items):
    """
    Prefetches all commission records for the specified items in 1 query
    and returns a fast in-memory resolver function:
    resolve_commission(item, month, year) -> Decimal

    Exact parity with InventoryItem.get_commission_at_date(month, year):
    Returns the commission_amount of the most recent CommissionHistory record
    with (activation_year < year) or (activation_year == year and activation_month <= month),
    tie-broken by id descending. If none exists, returns item.initial_commission_amount.
    """
    if not item_ids_or_items:
        return lambda item, month, year: (item.get_commission_at_date(month, year) if hasattr(item, 'get_commission_at_date') else 0)

    first = next(iter(item_ids_or_items))
    if hasattr(first, 'id'):
        item_ids = [i.id for i in item_ids_or_items]
        initial_comms = {i.id: i.initial_commission_amount for i in item_ids_or_items}
    else:
        item_ids = list(item_ids_or_items)
        initial_comms = {}

    from api.models import CommissionHistory

    comms = CommissionHistory.objects.filter(
        item_id__in=item_ids,
        is_deleted=False
    ).values(
        'item_id',
        'activation_year',
        'activation_month',
        'id',
        'commission_amount'
    ).order_by('item_id', 'activation_year', 'activation_month', 'id')

    comm_history = defaultdict(list)
    for c in comms:
        comm_history[c['item_id']].append((
            c['activation_year'],
            c['activation_month'],
            c['id'],
            c['commission_amount']
        ))

    def resolve_commission(item, month, year):
        iid = item.id if hasattr(item, 'id') else item
        records = comm_history.get(iid, [])
        for r_year, r_month, r_id, r_comm in reversed(records):
            if (r_year < year) or (r_year == year and r_month <= month):
                return r_comm

        if hasattr(item, 'initial_commission_amount'):
            return item.initial_commission_amount
        return initial_comms.get(iid, 0)

    return resolve_commission
