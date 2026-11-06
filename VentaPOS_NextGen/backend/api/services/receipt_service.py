"""
Receipt Service Layer for VentaPOS NextGen.
Encapsulates atomic receipt operations, return processing, installment debt recalculation,
installment rescheduling, and receipt numbering.
"""
import datetime
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone


class ReceiptServiceError(Exception):
    """Domain exception raised when receipt operations fail validation."""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_next_receipt_number(branch, select_for_update=False):
    """
    Returns the next sequential receipt number for a branch.
    """
    from api.models import Receipt
    if not branch:
        from api.models import Branch
        branch = Branch.objects.first()

    if not branch:
        return 1

    qs = Receipt.all_objects.filter(branch=branch)
    if select_for_update:
        qs = qs.select_for_update()
    last = qs.order_by("receipt_number").last()
    return (last.receipt_number + 1) if last else 1


def process_return_receipt(original_receipt, data):
    """
    Processes a customer return against an existing original receipt.
    Validates items, checks return date sequence, computes cash refund vs installment debt,
    reschedules future installments for credit sales, generates HMAC signature,
    and creates the RETURN receipt atomically.

    Returns:
    {"status": "success", "return_receipt_id": return_receipt.id}
    """
    from api.models import Receipt, SaleItem, InstallmentPayment

    returned_items_data = data.get("returned_items", [])
    new_installments_data = data.get("new_installments", [])
    new_installment_system = data.get("new_installment_system", "")

    if not returned_items_data:
        raise ReceiptServiceError("لا توجد عناصر للإرجاع", status_code=400)

    now = timezone.now()
    return_month = int(data.get("return_month", now.month))
    return_year = int(data.get("return_year", now.year))

    min_month = original_receipt.sale_month + 1
    min_year = original_receipt.sale_year
    if min_month > 12:
        min_month = 1
        min_year += 1

    if return_year < min_year or (return_year == min_year and return_month < min_month):
        raise ReceiptServiceError(
            f"تاريخ المرتجع لا يمكن أن يكون قبل الشهر التالي لتاريخ البيع ({min_month}/{min_year})",
            status_code=400
        )

    with transaction.atomic():
        original_items_qs = original_receipt.sale_items.filter(is_deleted=False).select_related('inventory_item')
        original_items_map = {item.inventory_item_id: item for item in original_items_qs}

        previously_returned = SaleItem.objects.filter(
            receipt__parent_receipt=original_receipt,
            receipt__receipt_type="RETURN",
            is_deleted=False
        ).values('inventory_item_id').annotate(total_returned=Sum('quantity'))
        returned_map = {item['inventory_item_id']: item['total_returned'] for item in previously_returned}

        calculated_return_value = 0
        validated_returned_items = []

        for item_data in returned_items_data:
            inv_id = item_data.get('inventory_item_id')
            req_qty = item_data.get('quantity', 0)

            if req_qty <= 0:
                continue

            orig_item = original_items_map.get(inv_id)
            if not orig_item:
                raise ReceiptServiceError("الصنف غير موجود في الفاتورة الأصلية", status_code=400)

            prev_returned_qty = returned_map.get(inv_id, 0)
            available_to_return = orig_item.quantity - prev_returned_qty

            if req_qty > available_to_return:
                raise ReceiptServiceError(
                    f"الكمية المرتجعة للصنف '{orig_item.inventory_item.name}' ({req_qty}) تتخطى الكمية المتاحة للإرجاع ({available_to_return})",
                    status_code=400
                )

            calculated_return_value += req_qty * orig_item.unit_price
            validated_returned_items.append({
                "inventory_item_id": inv_id,
                "inventory_item": orig_item.inventory_item,
                "quantity": req_qty,
                "unit_price": orig_item.unit_price
            })

        if not validated_returned_items:
            raise ReceiptServiceError("لا توجد عناصر صالحة للإرجاع", status_code=400)

        new_debt = 0
        if not original_receipt.is_cash_sale:
            current_date = datetime.date(return_year, return_month, 1)

            paid_so_far = original_receipt.down_payment
            past_payments = original_receipt.payments.filter(
                is_deleted=False,
                payment_date__lt=current_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            paid_so_far += past_payments

            new_debt = original_receipt.total_amount - calculated_return_value - paid_so_far

            if new_debt > 0:
                total_new_installments = sum(float(inst.get("amount", 0)) for inst in new_installments_data)
                if abs(float(new_debt) - total_new_installments) > 0.01:
                    raise ReceiptServiceError(
                        f"إجمالي الأقساط الجديدة ({total_new_installments}) لا يتطابق مع المديونية المتبقية ({new_debt}).",
                        status_code=400
                    )

        if original_receipt.is_cash_sale:
            cash_refund = Decimal(str(calculated_return_value))
        else:
            cash_refund = max(Decimal('0.00'), -Decimal(str(new_debt)))

        next_receipt_number = get_next_receipt_number(original_receipt.branch, select_for_update=True)

        return_receipt = Receipt.objects.create(
            branch=original_receipt.branch,
            salesperson=original_receipt.salesperson,
            customer_name=original_receipt.customer_name,
            phone_number=original_receipt.phone_number,
            receipt_type="RETURN",
            parent_receipt=original_receipt,
            total_amount=calculated_return_value,
            down_payment=cash_refund,
            sale_year=return_year,
            sale_month=return_month,
            is_cash_sale=original_receipt.is_cash_sale,
            receipt_number=next_receipt_number
        )

        try:
            from api.utils.security_utils import generate_receipt_signature
            sig_items = [{"inventory_item": item["inventory_item"], "quantity": item["quantity"]} for item in validated_returned_items]
            return_receipt.products_text = " + ".join([
                f"{i['inventory_item'].name}" if i['quantity'] == 1 else f"{i['quantity']} {i['inventory_item'].name}"
                for i in sig_items
            ])
            return_receipt.receipt_hash = generate_receipt_signature(
                return_receipt.receipt_number,
                return_receipt.total_amount,
                return_receipt.sale_month,
                return_receipt.sale_year,
                sig_items
            )
        except ImportError:
            return_receipt.products_text = ""
            return_receipt.receipt_hash = ""

        return_receipt.save(update_fields=['receipt_number', 'receipt_hash', 'products_text'])

        for item in validated_returned_items:
            SaleItem.objects.create(
                receipt=return_receipt,
                inventory_item_id=item['inventory_item_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )

        if not original_receipt.is_cash_sale:
            current_date = datetime.date(return_year, return_month, 1)

            # Delete future installments
            original_receipt.payments.filter(
                is_deleted=False,
                payment_date__gte=current_date
            ).update(is_deleted=True)

            if new_debt > 0:
                for inst_data in new_installments_data:
                    payment_month = int(inst_data.get("payment_month", now.month))
                    payment_year = int(inst_data.get("payment_year", now.year))
                    payment_date = inst_data.get("payment_date")
                    if not payment_date:
                        payment_date = datetime.date(payment_year, payment_month, 25)

                    InstallmentPayment.objects.create(
                        receipt=original_receipt,
                        amount=inst_data["amount"],
                        payment_date=payment_date
                    )

            original_receipt.installment_system = new_installment_system
            original_receipt.save(update_fields=["installment_system"])

        return {"status": "success", "return_receipt_id": return_receipt.id}


def get_active_license(select_for_update=False):
    """
    Centralized lookup for the active license.
    Prefers production licenses (excluding DEMO_MACHINE), falling back to DEMO_MACHINE
    when only demo licenses exist. Orders by -expiry_date.
    """
    from api.models import ClientLicense
    qs = ClientLicense.objects.filter(is_active=True, is_deleted=False)
    prod_qs = qs.exclude(machine_id="DEMO_MACHINE")
    target_qs = prod_qs if prod_qs.exists() else qs
    if select_for_update:
        target_qs = target_qs.select_for_update()
    return target_qs.order_by('-expiry_date').first()


def get_license_date_bounds(active_lic=None):
    """
    Computes (start_date, last_allowed_month, grace_end) for an active license.
    - If expiry_date.day == 1 and start_date is earlier:
        last_allowed_month = (expiry_date - 1 month).replace(day=1)
        grace_end = expiry_date.replace(day=25)
    - If expiry_date.day != 1 (e.g. test fixtures):
        last_allowed_month = expiry_date.replace(day=1)
        grace_end = expiry_date (or max(expiry_date, expiry_date.replace(day=25)) if in future month)
    """
    if active_lic is None:
        active_lic = get_active_license()

    if not active_lic or not active_lic.expiry_date:
        return None, None, None

    from dateutil.relativedelta import relativedelta
    start_date = active_lic.start_date
    expiry_date = active_lic.expiry_date

    if expiry_date.day == 1 and (not start_date or start_date < expiry_date):
        last_allowed_month = (expiry_date - relativedelta(months=1)).replace(day=1)
        grace_end = expiry_date.replace(day=25)
    else:
        last_allowed_month = expiry_date.replace(day=1)
        today = datetime.date.today()
        if (expiry_date.year, expiry_date.month) > (today.year, today.month):
            grace_end = max(expiry_date, expiry_date.replace(day=25))
        else:
            grace_end = expiry_date

    return start_date, last_allowed_month, grace_end


def create_receipt(validated_data, items_data, installments_data):
    """
    Atomically creates a Receipt and its SaleItems & InstallmentPayments.
    Enforces financial balance, license validation with date bounds, stock limit check,
    deterministic HMAC signature, and license deduction.
    """
    from api.models import Receipt, SaleItem, InstallmentPayment, ClientLicense
    from api.utils.security_utils import generate_receipt_signature, generate_record_signature
    from api.views.base import get_default_date
    from rest_framework.exceptions import ValidationError

    is_cash_sale = validated_data.get("is_cash_sale", False)
    if not is_cash_sale:
        total_amount = validated_data.get("total_amount", 0)
        down_payment = validated_data.get("down_payment", 0)
        installments_total = sum(item.get("amount", 0) for item in installments_data)
        if abs(float(total_amount) - float(down_payment + installments_total)) > 0.01:
            raise ValidationError({
                "error": "إجمالي الأقساط والمقدم لا يتطابق مع إجمالي الفاتورة المدخلة بالنظام."
            })

    is_confirmed = validated_data.get("is_confirmed", True)
    with transaction.atomic():
        active_lic = None
        if is_confirmed:
            qs = ClientLicense.objects.select_for_update().filter(is_active=True, is_deleted=False, invoices_balance__gt=0)
            prod_qs = qs.exclude(machine_id="DEMO_MACHINE")
            active_lic = (prod_qs if prod_qs.exists() else qs).order_by('-expiry_date').first()
            if not active_lic:
                raise ValidationError({
                    "license": (
                        "لا يمكن طباعة أو إصدار الفاتورة، رصيد الفواتير المسموح به "
                        "للرخصة قد نفد. يرجى الشحن أولاً."
                    )
                })

            try:
                sale_year = int(validated_data.get("sale_year"))
                sale_month = int(validated_data.get("sale_month"))
                invoice_date = datetime.date(sale_year, sale_month, 1)
            except Exception:
                raise ValidationError({"error": "تاريخ الفاتورة غير صحيح."})

            start_date, last_allowed_month, grace_end = get_license_date_bounds(active_lic)
            is_pre_license = False
            if start_date:
                lic_start_month = start_date.replace(day=1)
                if invoice_date < lic_start_month:
                    is_pre_license = True

            if is_pre_license:
                if items_data and len(items_data) > 0:
                    raise ValidationError({"error": "فواتير ما قبل الاشتراك لا تقبل بنود أصناف مجزأة، يرجى كتابة وصف البضاعة كنص فقط."})
                if not validated_data.get("products_text") or float(validated_data.get("total_amount", 0)) <= 0:
                    raise ValidationError({"error": "يجب إدخال وصف البضاعة وإجمالي الفاتورة بشكل صحيح لفواتير ما قبل الاشتراك."})
            else:
                if last_allowed_month and invoice_date > last_allowed_month:
                    raise ValidationError({"error": "التاريخ بعد انتهاء الاشتراك."})

                if grace_end and datetime.date.today() > grace_end:
                    raise ValidationError({"error": "انتهت فترة الاشتراك."})

            if not validated_data.get("receipt_number"):
                branch = validated_data.get("branch")
                validated_data["receipt_number"] = get_next_receipt_number(branch, select_for_update=True)

        branch = validated_data.get("branch")
        branch_id = branch.id if branch else None
        default_year, default_month = get_default_date(branch_id=branch_id)
        target_year = validated_data["sale_year"]
        target_month = validated_data["sale_month"]

        if is_confirmed and validated_data.get("receipt_type") != "RETURN" and not is_pre_license:
            for item_data in items_data:
                item = item_data["inventory_item"]
                qty = item_data["quantity"]
                safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                if qty > safe_limit:
                    raise ValidationError({
                        "error": f"عفواً، لا يمكن البيع! أقصى كمية يمكن بيعها بأثر رجعي للصنف '{item.name}' هي ({safe_limit}) لتجنب حدوط رصيد سالب في الشهور اللاحقة."
                    })

        if not validated_data.get("products_text") and items_data:
            validated_data["products_text"] = " - ".join([f"{i['inventory_item'].name} ({i['quantity']})" for i in items_data])

        receipt = Receipt.objects.create(**validated_data)

        for item_data in items_data:
            SaleItem.objects.create(receipt=receipt, **item_data)

        for inst_data in installments_data:
            payment_month = inst_data.pop("payment_month", 1)
            payment_year = inst_data.pop("payment_year", 2026)
            if "payment_date" not in inst_data:
                inst_data["payment_date"] = datetime.date(payment_year, payment_month, 25)
            InstallmentPayment.objects.create(
                receipt=receipt, **inst_data
            )

        if is_confirmed:
            receipt.receipt_hash = generate_receipt_signature(
                receipt.receipt_number,
                receipt.total_amount,
                receipt.sale_month,
                receipt.sale_year,
                items_data,
            )
            receipt.save(update_fields=["receipt_hash"])

            if not is_pre_license:
                machine_id = active_lic.machine_id
                active_lic.invoices_balance -= 1
                active_lic.license_code_hash = generate_record_signature(
                    active_lic.expiry_date,
                    active_lic.invoices_balance,
                    machine_id,
                    active_lic.product_id,
                    active_lic.is_active,
                )
                active_lic.save(update_fields=["invoices_balance", "license_code_hash"])

    return receipt


def update_receipt(instance, validated_data, items_data, installments_data):
    """
    Atomically updates a Receipt and its items/payments, validating safe stock and re-signing HMAC.
    """
    from api.models import SaleItem, InstallmentPayment
    from api.utils.security_utils import generate_receipt_signature
    from api.views.base import get_default_date
    from rest_framework.exceptions import ValidationError

    if instance.receipt_type == "RETURN":
        raise ValidationError({"error": "لا يمكن تعديل فواتير المرتجعات. برجاء إنشاء مرتجع جديد أو حذفه وإعادة إنشائه."})

    # Strict Financial Balance Validation for Installment Sales
    is_cash_sale = validated_data.get("is_cash_sale", instance.is_cash_sale)
    if not is_cash_sale:
        total_amount = validated_data.get("total_amount", instance.total_amount)
        down_payment = validated_data.get("down_payment", instance.down_payment)

        if installments_data is not None:
            installments_total = sum(item.get("amount", 0) for item in installments_data)
        else:
            from django.db.models import Sum
            installments_total = instance.payments.filter(is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0

        if abs(float(total_amount) - float(down_payment + installments_total)) > 0.01:
            raise ValidationError({
                "error": "إجمالي الأقساط والمقدم لا يتطابق مع إجمالي الفاتورة المدخلة بالنظام."
            })

    # Date Boundary Validation using centralized bounds
    active_lic = get_active_license()
    if not active_lic:
        raise ValidationError({"license": "لا يوجد ترخيص ساري."})

    target_year = validated_data.get("sale_year", instance.sale_year)
    target_month = validated_data.get("sale_month", instance.sale_month)
    try:
        invoice_date = datetime.date(target_year, target_month, 1)
    except Exception:
        raise ValidationError({"error": "تاريخ الفاتورة غير صحيح."})

    start_date, last_allowed_month, grace_end = get_license_date_bounds(active_lic)
    is_pre_license = False
    if start_date:
        lic_start_month = start_date.replace(day=1)
        if invoice_date < lic_start_month:
            is_pre_license = True

    if is_pre_license:
        if items_data and len(items_data) > 0:
            raise ValidationError({"error": "فواتير ما قبل الاشتراك لا تقبل بنود أصناف مجزأة، يرجى كتابة وصف البضاعة كنص فقط."})
        if not validated_data.get("products_text", instance.products_text) or float(validated_data.get("total_amount", instance.total_amount) or 0) <= 0:
            raise ValidationError({"error": "يجب إدخال وصف البضاعة وإجمالي الفاتورة بشكل صحيح لفواتير ما قبل الاشتراك."})
    else:
        if last_allowed_month and invoice_date > last_allowed_month:
            raise ValidationError({"error": "التاريخ بعد انتهاء الاشتراك."})

        if grace_end and datetime.date.today() > grace_end:
            raise ValidationError({"error": "انتهت فترة الاشتراك."})

    with transaction.atomic():
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.sale_items.all().update(is_deleted=True)

            branch = instance.branch
            branch_id = branch.id if branch else None
            default_year, default_month = get_default_date(branch_id=branch_id)

            if validated_data.get("receipt_type", instance.receipt_type) != "RETURN":
                for item_data in items_data:
                    item = item_data["inventory_item"]
                    qty = item_data["quantity"]
                    safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                    if qty > safe_limit:
                        raise ValidationError({
                            "error": f"عفواً، أقصى كمية يمكن بيعها أو تعديلها للصنف '{item.name}' في هذا التاريخ هي ({safe_limit})."
                        })

            for item_data in items_data:
                SaleItem.objects.create(receipt=instance, **item_data)

        if installments_data is not None:
            instance.payments.all().update(is_deleted=True)
            for inst_data in installments_data:
                payment_month = inst_data.pop("payment_month", 1)
                payment_year = inst_data.pop("payment_year", 2026)
                if "payment_date" not in inst_data:
                    inst_data["payment_date"] = datetime.date(payment_year, payment_month, 25)
                InstallmentPayment.objects.create(receipt=instance, **inst_data)

        current_items = (
            items_data
            if items_data is not None
            else list(instance.sale_items.filter(is_deleted=False).values(
                "inventory_item_id", "quantity", "unit_price"
            ))
        )
        if items_data is not None:
            instance.products_text = " + ".join([f"{i['inventory_item'].name}" if i['quantity'] == 1 else f"{i['quantity']} {i['inventory_item'].name}" for i in items_data])

        instance.receipt_hash = generate_receipt_signature(
            instance.receipt_number,
            instance.total_amount,
            instance.sale_month,
            instance.sale_year,
            current_items,
        )
        update_fields = ["receipt_hash"]
        if items_data is not None:
            update_fields.append("products_text")
        instance.save(update_fields=update_fields)

    return instance
