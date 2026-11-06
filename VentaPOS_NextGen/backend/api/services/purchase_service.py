"""
Purchase Service Layer for VentaPOS NextGen.
Encapsulates purchase invoice creation, updates, sequential numbering,
and historical stock integrity validation.
"""
from collections import defaultdict
from django.db import transaction
from django.db.models import Sum, Max
from rest_framework.exceptions import ValidationError


def validate_items_stock_integrity(items, default_year=None, default_month=None):
    """
    Validates that none of the specified InventoryItem objects has a negative raw stock balance
    in any month from its initial date up to the default business date or latest transaction.
    Raises ValidationError if any month's running stock drops below 0.
    """
    if not items:
        return

    from api.models import PurchaseInvoiceItem, SaleItem, InventoryAdjustment
    from api.views.base import get_default_date

    item_list = list(items)
    item_ids = [item.id for item in item_list]

    if default_year is None or default_month is None:
        first_branch = item_list[0].branch_id if item_list else None
        default_year, default_month = get_default_date(branch_id=first_branch)

    # 1. Purchases & Purchase Returns
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

    # 2. Sales & Sales Returns (Confirmed only)
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

    # 3. Deficits
    deficits_qs = InventoryAdjustment.objects.filter(
        item_id__in=item_ids,
        is_deleted=False,
        adjustment_type='DEFICIT'
    ).values(
        'item_id',
        'year',
        'month'
    ).annotate(total_qty=Sum('quantity'))

    monthly_deltas = defaultdict(lambda: defaultdict(int))

    for row in purchases_qs:
        iid = row['inventory_item_id']
        y = row['invoice__invoice_year']
        m = row['invoice__invoice_month']
        qty = row['total_qty'] or 0
        if row['invoice__invoice_type'] == 'PURCHASE':
            monthly_deltas[iid][(y, m)] += qty
        elif row['invoice__invoice_type'] == 'RETURN':
            monthly_deltas[iid][(y, m)] -= qty

    for row in sales_qs:
        iid = row['inventory_item_id']
        y = row['receipt__sale_year']
        m = row['receipt__sale_month']
        qty = row['total_qty'] or 0
        if row['receipt__receipt_type'] == 'SALE':
            monthly_deltas[iid][(y, m)] -= qty
        elif row['receipt__receipt_type'] == 'RETURN':
            monthly_deltas[iid][(y, m)] += qty

    for row in deficits_qs:
        iid = row['item_id']
        y = row['year']
        m = row['month']
        qty = row['total_qty'] or 0
        monthly_deltas[iid][(y, m)] -= qty

    for item in item_list:
        iid = item.id
        init_y = item.initial_year
        init_m = item.initial_month
        init_qty = item.initial_quantity
        deltas = monthly_deltas[iid]

        all_dates = list(deltas.keys())
        if all_dates:
            max_delta_date = max(all_dates)
        else:
            max_delta_date = (init_y, init_m)

        end_y = max(default_year, max_delta_date[0])
        end_m = default_month if end_y == default_year else max_delta_date[1]
        if max_delta_date[0] > default_year or (max_delta_date[0] == default_year and max_delta_date[1] > default_month):
            end_y, end_m = max_delta_date

        curr_y, curr_m = init_y, init_m
        running_stock = init_qty

        # Add any deltas prior to init date (if any)
        for dt, d in deltas.items():
            if dt < (init_y, init_m):
                running_stock += d

        while (curr_y, curr_m) <= (end_y, end_m):
            running_stock += deltas.get((curr_y, curr_m), 0)
            if running_stock < 0:
                raise ValidationError({
                    "error": (
                        f"عفواً، لا يمكن تعديل الفاتورة! تعديل الصنف '{item.name}' "
                        f"يتسبب في رصيد سالب ({running_stock}) في شهر {curr_m}/{curr_y}."
                    )
                })

            curr_m += 1
            if curr_m > 12:
                curr_m = 1
                curr_y += 1


def create_purchase_invoice(validated_data, items_data):
    """
    Creates a PurchaseInvoice with its child PurchaseInvoiceItems atomically,
    validating safe available return limits and assigning sequential invoice_number.
    """
    from api.models import PurchaseInvoice, PurchaseInvoiceItem
    from api.views.base import get_default_date

    branch = validated_data.get("branch")
    invoice_type = validated_data.get("invoice_type", "PURCHASE")
    target_year = validated_data.get("invoice_year")
    target_month = validated_data.get("invoice_month")

    if invoice_type == "RETURN" and items_data:
        default_year, default_month = get_default_date(branch_id=branch.id if branch else None)
        for item_data in items_data:
            item = item_data["inventory_item"]
            qty = item_data["quantity"]
            safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
            if qty > safe_limit:
                raise ValidationError({
                    "error": f"عفواً، لا يمكن الإرجاع! أقصى كمية يمكن إرجاعها للمورد للصنف '{item.name}' هي ({safe_limit})."
                })

    if "invoice_number" not in validated_data or not validated_data["invoice_number"]:
        last_invoice = PurchaseInvoice.all_objects.filter(
            branch=branch
        ).aggregate(Max("invoice_number"))
        last_num = last_invoice.get("invoice_number__max") or 0
        validated_data["invoice_number"] = last_num + 1

    with transaction.atomic():
        invoice = PurchaseInvoice.objects.create(**validated_data)
        for item_data in items_data:
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                **item_data
            )
    return invoice


def update_purchase_invoice(instance, validated_data, items_data):
    """
    Updates a PurchaseInvoice and its items within an atomic transaction,
    ensuring that no affected item's historical stock dips below zero in any month.
    """
    from api.models import PurchaseInvoiceItem
    from api.views.base import get_default_date

    branch = instance.branch
    default_year, default_month = get_default_date(branch_id=branch.id if branch else None)

    with transaction.atomic():
        old_items = list(instance.items.filter(is_deleted=False).select_related('inventory_item'))
        affected_items = {item.inventory_item for item in old_items}

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Soft-delete previous items
            instance.items.all().update(is_deleted=True)

            target_year = validated_data.get("invoice_year", instance.invoice_year)
            target_month = validated_data.get("invoice_month", instance.invoice_month)
            invoice_type = validated_data.get("invoice_type", instance.invoice_type)

            for item_data in items_data:
                item = item_data["inventory_item"]
                affected_items.add(item)
                qty = item_data["quantity"]

                if invoice_type == "RETURN":
                    safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                    if qty > safe_limit:
                        raise ValidationError({
                            "error": f"عفواً، لا يمكن الإرجاع! أقصى كمية يمكن إرجاعها للمورد للصنف '{item.name}' هي ({safe_limit})."
                        })

                PurchaseInvoiceItem.objects.create(
                    invoice=instance, **item_data
                )

        # Validate that historical stock integrity is preserved across all affected items
        validate_items_stock_integrity(affected_items, default_year=default_year, default_month=default_month)

    return instance
