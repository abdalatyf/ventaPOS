"""
serializers.py — VentaPOS NextGen Backend
==========================================
Serializers for all 19 schema-approved models.

Design decisions:
- Nested writable serializers are used only where the API contract specifies
  embedded creation (PurchaseInvoice → items, Receipt → sale_items + installments).
- Financial fields (IntegerField) are serialized as strings to preserve
  precision across JSON boundaries.
- The `is_deleted` field is read-only everywhere; soft-delete happens via a
  dedicated action, never via direct PATCH.
- Field name mapping (SQLite ↔ PostgreSQL) follows the translation layer
  documented in api_contract.md §3.
"""

from collections.abc import Mapping
import datetime
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Branch,
    Salesperson,
    InventoryItem,
    CommissionHistory,
    InventoryAdjustment,
    Supplier,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    InstallmentPayment,
    Expense,
    CompanySetting,
    ClientLicense,
    UsedLicense,
    LicenseHistory,
    )
from .utils.security_utils import (
    generate_receipt_signature,
    generate_record_signature,
    get_machine_id,
)


def _copy_mapping(data):
    """Ensures serializer input is a mutable dict-like mapping, rejecting lists/primitives cleanly."""
    if not isinstance(data, Mapping):
        raise ValidationError({"non_field_errors": ["تنسيق البيانات المرسلة غير صالح."]})
    return data.copy() if hasattr(data, "copy") else dict(data)


def normalize_dirty_number_str(value):
    """Converts Arabic-Indic/Persian numerals to ASCII digits and strips thousands commas/spaces."""
    if value is None or isinstance(value, bool) or not isinstance(value, str):
        return value
    from .views.base import to_english_numerals
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    ascii_digits = '0123456789'
    cleaned = to_english_numerals(value).translate(str.maketrans(persian_digits, ascii_digits))
    return cleaned.replace('٬', '').replace(',', '').replace('٫', '.').strip()


def normalize_numeric_fields(data, numeric_fields):
    """Normalizes string numeric fields in a copied payload mapping before DRF field parsing."""
    data_copy = _copy_mapping(data)
    for field in numeric_fields:
        if field in data_copy and isinstance(data_copy[field], str):
            data_copy[field] = normalize_dirty_number_str(data_copy[field])
    return data_copy


def validate_month_year(month, year, *, min_year=2000, max_year=2100, month_field="month", year_field="year"):
    """Enforces valid calendar month (1..12) and bounded year range."""
    errors = {}
    if month is not None and not (1 <= month <= 12):
        errors[month_field] = "الشهر يجب أن يكون بين 1 و 12."
    if year is not None and not (min_year <= year <= max_year):
        errors[year_field] = f"السنة يجب أن تكون بين {min_year} و {max_year}."
    if errors:
        raise ValidationError(errors)


def _strip_required_name(value, label):
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValidationError(f"يجب إدخال {label} بشكل صحيح ولا يقبل مساحات فارغة.")
    return cleaned


# ---------------------------------------------------------------------------
# 1. Branch
# ---------------------------------------------------------------------------

class BranchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = [
            "id", "name",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def validate_name(self, value):
        return _strip_required_name(value, "اسم الفرع")


# ---------------------------------------------------------------------------
# 4. Salesperson
# ---------------------------------------------------------------------------

class SalespersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Salesperson
        fields = [
            "id", "branch", "name",
            "device_token", "is_device_active", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "device_token", "is_deleted", "created_at"]

    def validate_name(self, value):
        return _strip_required_name(value, "اسم المندوب")


# ---------------------------------------------------------------------------
# 5. InventoryItem
# ---------------------------------------------------------------------------

class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Includes a computed read-only field `current_stock` matching the
    ProductSchema in api_contract.md.

    The SQLite translation layer field names used during sync push/pull:
      quantity               → initial_quantity
      purchase_price         → initial_purchase_price
      salesperson_commission → initial_commission_amount
      created_at_local       → stored in created_at_local
    """

    current_stock = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "branch", "name",
            "initial_quantity", "initial_purchase_price",
            "initial_commission_amount", "initial_month", "initial_year",
            "is_deleted", "created_at", "current_stock",
        ]
        read_only_fields = ["id", "is_deleted", "created_at", "current_stock"]

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(
            data,
            ["initial_quantity", "initial_purchase_price", "initial_commission_amount", "initial_month", "initial_year"],
        )
        return super().to_internal_value(data_copy)

    def validate_name(self, value):
        return _strip_required_name(value, "اسم الصنف")

    def validate(self, data):
        init_qty = data.get("initial_quantity", self.instance.initial_quantity if self.instance else 0)
        init_price = data.get("initial_purchase_price", self.instance.initial_purchase_price if self.instance else 0)
        init_comm = data.get("initial_commission_amount", self.instance.initial_commission_amount if self.instance else 0)
        init_month = data.get("initial_month", self.instance.initial_month if self.instance else None)
        init_year = data.get("initial_year", self.instance.initial_year if self.instance else None)

        if init_qty is not None and init_qty < 0:
            raise ValidationError({"initial_quantity": "الرصيد الافتتاحي لا يمكن أن يكون سالباً."})
        if init_price is not None and init_price < 0:
            raise ValidationError({"initial_purchase_price": "سعر الشراء الافتتاحي لا يمكن أن يكون سالباً."})
        if init_comm is not None and init_comm < 0:
            raise ValidationError({"initial_commission_amount": "المندبة لا يمكن أن تكون سالبة."})
        validate_month_year(
            init_month,
            init_year,
            min_year=2025,
            max_year=2100,
            month_field="initial_month",
            year_field="initial_year",
        )
        return data

    def get_current_stock(self, obj):
        if hasattr(obj, '_precomputed_stock'):
            return obj._precomputed_stock
        from django.utils import timezone
        from api.views import get_default_date
        now = timezone.now()
        def_year, def_month = get_default_date(branch_id=obj.branch_id)
        eff_year, eff_month = max((now.year, now.month), (def_year, def_month))
        return obj.get_stock_at_date(eff_month, eff_year)


# ---------------------------------------------------------------------------
# 6. CommissionHistory
# ---------------------------------------------------------------------------

class CommissionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = CommissionHistory
        fields = [
            "id", "item", "commission_amount",
            "activation_month", "activation_year", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(
            data,
            ["item", "commission_amount", "activation_month", "activation_year"],
        )
        return super().to_internal_value(data_copy)

    def validate(self, data):
        amount = data.get("commission_amount", self.instance.commission_amount if self.instance else None)
        act_month = data.get("activation_month", self.instance.activation_month if self.instance else None)
        act_year = data.get("activation_year", self.instance.activation_year if self.instance else None)
        item = data.get("item", self.instance.item if self.instance else None)

        if amount is not None and amount < 0:
            raise ValidationError({"commission_amount": "قيمة المندبة لا يمكن أن تكون سالبة."})
        validate_month_year(
            act_month,
            act_year,
            min_year=2025,
            max_year=2100,
            month_field="activation_month",
            year_field="activation_year",
        )
        request = self.context.get("request") if isinstance(self.context, dict) else None
        if request and item:
            from .views.base import get_request_branch_id
            req_branch_id = get_request_branch_id(request)
            if req_branch_id and item.branch_id != req_branch_id:
                raise ValidationError({"item": "الصنف المحدد لا يتبع هذا الفرع."})
        return data


# ---------------------------------------------------------------------------
# 7. InventoryAdjustment
# ---------------------------------------------------------------------------

class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    adjustment_type = serializers.CharField(default="DEFICIT", required=False)

    class Meta:
        model = InventoryAdjustment
        fields = [
            "id", "item", "adjustment_type",
            "quantity", "reason", "month", "year",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = _copy_mapping(data)
        if "adjustment_month" in data_copy and "month" not in data_copy:
            data_copy["month"] = data_copy["adjustment_month"]
        if "adjustment_year" in data_copy and "year" not in data_copy:
            data_copy["year"] = data_copy["adjustment_year"]
        if "inventory_item" in data_copy and "item" not in data_copy:
            data_copy["item"] = data_copy["inventory_item"]
        if not data_copy.get("adjustment_type"):
            data_copy["adjustment_type"] = "DEFICIT"
        data_copy = normalize_numeric_fields(data_copy, ["item", "quantity", "month", "year"])
        return super().to_internal_value(data_copy)

    def validate(self, data):
        from api.views.base import get_default_date, get_request_branch_id

        adj_type = data.get("adjustment_type", self.instance.adjustment_type if self.instance else "DEFICIT")
        if adj_type != "DEFICIT":
            raise ValidationError({"adjustment_type": "نوع التسوية المسموح به هو عجز المخزن فقط (DEFICIT)."})

        target_year = data.get("year", self.instance.year if self.instance else None)
        target_month = data.get("month", self.instance.month if self.instance else None)
        item = data.get("item", self.instance.item if self.instance else None)
        qty = data.get("quantity", self.instance.quantity if self.instance else None)

        if qty is not None and qty <= 0:
            raise ValidationError({"quantity": "كمية العجز يجب أن تكون أكبر من صفر."})
        validate_month_year(target_month, target_year, min_year=2025, max_year=2100)

        request = self.context.get("request") if isinstance(self.context, dict) else None
        if request and item:
            req_branch_id = get_request_branch_id(request)
            if req_branch_id and item.branch_id != req_branch_id:
                raise ValidationError({"item": "الصنف المحدد لا يتبع هذا الفرع."})

        default_year, default_month = get_default_date(branch_id=item.branch_id if item else None)

        if item and target_month and target_year and qty:
            safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)

            if self.instance and not self.instance.is_deleted:
                safe_limit += self.instance.quantity

            if qty > safe_limit:
                raise ValidationError({
                    "error": f"عفواً، أقصى كمية يمكن تسويتها بالنقصان للصنف '{item.name}' في هذا التاريخ هي ({safe_limit})."
                })
        return data


# ---------------------------------------------------------------------------
# 8. Supplier
# ---------------------------------------------------------------------------

class SupplierSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Supplier
        fields = ["id", "name", "branch", "branch_name", "is_deleted", "created_at"]
        read_only_fields = ["id", "is_deleted", "created_at", "branch_name"]

    def validate_name(self, value):
        return _strip_required_name(value, "اسم المورد")


# ---------------------------------------------------------------------------
# 9 & 10. PurchaseInvoice + PurchaseInvoiceItem
# ---------------------------------------------------------------------------

class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseInvoiceItem
        fields = [
            "id", "invoice", "inventory_item",
            "quantity", "purchase_price", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "invoice", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(data, ["inventory_item", "quantity", "purchase_price"])
        return super().to_internal_value(data_copy)

    def validate(self, data):
        qty = data.get("quantity", self.instance.quantity if self.instance else None)
        price = data.get("purchase_price", self.instance.purchase_price if self.instance else None)
        if qty is not None and qty <= 0:
            raise ValidationError({"quantity": "الكمية يجب أن تكون أكبر من صفر."})
        if price is not None and price <= 0:
            raise ValidationError({"purchase_price": "سعر الشراء يجب أن يكون أكبر من صفر."})
        return data


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, required=False)
    invoice_number = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            "id", "branch", "supplier",
            "invoice_number", "invoice_type", "invoice_month", "invoice_year",
            "is_deleted", "created_at", "items",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]
        validators = []

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(
            data,
            ["branch", "supplier", "invoice_number", "invoice_month", "invoice_year"],
        )
        return super().to_internal_value(data_copy)

    def validate(self, data):
        branch = data.get("branch", self.instance.branch if self.instance else None)
        supplier = data.get("supplier", self.instance.supplier if self.instance else None)
        inv_month = data.get("invoice_month", self.instance.invoice_month if self.instance else None)
        inv_year = data.get("invoice_year", self.instance.invoice_year if self.instance else None)
        inv_num = data.get("invoice_number", None)
        items = data.get("items", None)

        if inv_num is not None and inv_num <= 0:
            raise ValidationError({"invoice_number": "رقم الفاتورة يجب أن يكون رقماً موجباً."})

        if inv_num is not None and branch and supplier:
            dup_qs = PurchaseInvoice.all_objects.filter(
                branch=branch, invoice_number=inv_num, supplier=supplier
            )
            if self.instance:
                dup_qs = dup_qs.exclude(pk=self.instance.pk)
            if dup_qs.exists():
                raise ValidationError({"invoice_number": "رقم الفاتورة مسجل مسبقاً لهذا المورد في هذا الفرع."})

        validate_month_year(
            inv_month,
            inv_year,
            min_year=2025,
            max_year=2100,
            month_field="invoice_month",
            year_field="invoice_year",
        )

        if self.instance and branch and branch.id != self.instance.branch_id:
            raise ValidationError({"branch": "لا يمكن نقل الفاتورة لفرع آخر."})

        if not self.instance and not items:
            raise ValidationError({"items": "يجب إضافة صنف واحد على الأقل للفاتورة."})
        if items is not None and len(items) == 0:
            raise ValidationError({"items": "يجب أن تحتوي الفاتورة على صنف واحد على الأقل."})

        if supplier and branch and supplier.branch_id is not None and supplier.branch_id != branch.id:
            raise ValidationError({"supplier": "المورد المحدد لا يتبع هذا الفرع."})

        if items and branch:
            for item_data in items:
                inv_item = item_data.get("inventory_item")
                if inv_item and inv_item.branch_id != branch.id:
                    raise ValidationError({"items": f"الصنف '{inv_item.name}' لا يتبع هذا الفرع."})

        return data

    def create(self, validated_data):
        from api.services.purchase_service import create_purchase_invoice
        items_data = validated_data.pop("items", [])
        return create_purchase_invoice(validated_data, items_data)

    def update(self, instance, validated_data):
        from api.services.purchase_service import update_purchase_invoice
        items_data = validated_data.pop("items", None)
        return update_purchase_invoice(instance, validated_data, items_data)


# ---------------------------------------------------------------------------
# 11 & 12. SaleItem + Receipt
# ---------------------------------------------------------------------------

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="inventory_item.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            "id", "receipt", "inventory_item", "product_name",
            "quantity", "unit_price", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "receipt", "product_name", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = _copy_mapping(data)
        # Allow the API contract field alias `inventory_item_id`
        if "inventory_item_id" in data_copy and "inventory_item" not in data_copy:
            data_copy["inventory_item"] = data_copy.pop("inventory_item_id")
        # Allow `sell_price` alias for `unit_price` (used by POS frontend)
        if "sell_price" in data_copy and "unit_price" not in data_copy:
            data_copy["unit_price"] = data_copy.pop("sell_price")
        data_copy = normalize_numeric_fields(data_copy, ["inventory_item", "quantity", "unit_price"])
        return super().to_internal_value(data_copy)

    def validate(self, data):
        qty = data.get("quantity", self.instance.quantity if self.instance else None)
        unit_price = data.get("unit_price", self.instance.unit_price if self.instance else None)
        if qty is not None and qty <= 0:
            raise ValidationError({"quantity": "الكمية المباعة يجب أن تكون أكبر من صفر."})
        if unit_price is not None and unit_price <= 0:
            raise ValidationError({"unit_price": "سعر البيع يجب أن يكون أكبر من صفر."})
        return data


class InstallmentPaymentSerializer(serializers.ModelSerializer):
    # Virtual write-only fields for POS frontend convenience
    payment_month = serializers.IntegerField(write_only=True, required=False)
    payment_year = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = InstallmentPayment
        fields = [
            "id", "receipt", "payment_date",
            "payment_month", "payment_year",
            "amount", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "receipt", "is_deleted", "created_at"]
        extra_kwargs = {
            "payment_date": {"required": False},
        }

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(data, ["payment_month", "payment_year", "amount"])
        if "payment_date" not in data_copy and "payment_month" in data_copy and "payment_year" in data_copy:
            try:
                month = int(data_copy["payment_month"])
                year = int(data_copy["payment_year"])
            except (ValueError, TypeError):
                raise ValidationError({"payment_date": "تاريخ القسط غير صحيح."})
            validate_month_year(
                month,
                year,
                min_year=2000,
                max_year=2100,
                month_field="payment_month",
                year_field="payment_year",
            )
            data_copy["payment_date"] = datetime.date(year, month, 25).isoformat()
        elif "payment_date" not in data_copy and not self.partial:
            raise ValidationError({"payment_date": "يجب تحديد تاريخ استحقاق القسط."})
        return super().to_internal_value(data_copy)

    def validate(self, data):
        amount = data.get("amount", self.instance.amount if self.instance else None)
        if amount is not None and amount <= 0:
            raise ValidationError({"amount": "قيمة القسط يجب أن تكون أكبر من صفر."})
        return data



class ReceiptSerializer(serializers.ModelSerializer):
    """
    Handles nested creation of SaleItems and InstallmentPayments.

    Field name aliasing (api_contract.md §3 — Receipts Mapping):
      phone_number   ← stored as `phone_number` in DB
      address        ← stored as `address` in DB
      area           ← stored as `area` in DB
      created_at_local ← stored as `created_at_local` (device time)
    """

    # Nested writable collections
    sale_items = SaleItemSerializer(many=True, required=False)
    installment_payments = InstallmentPaymentSerializer(source="payments", many=True, required=False)
    has_returns = serializers.SerializerMethodField()
    receipt_number = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Receipt
        fields = [
            "id", "branch", "salesperson",
            "receipt_number", "receipt_hash",
            "customer_name", "phone_number", "address", "area",
            "total_amount", "down_payment", "installment_system",
            "sale_year", "sale_month", "is_cash_sale", "products_text",
            "receipt_type", "parent_receipt",
            "is_confirmed", "is_deleted", "created_at",
            "sale_items", "installment_payments", "has_returns",
        ]
        read_only_fields = [
            "id", "receipt_hash", "is_confirmed",
            "is_deleted", "created_at",
        ]
        validators = []
        extra_kwargs = {
            "receipt_number": {"required": False},
            "products_text": {"required": False},
            "address": {"required": False, "allow_blank": True},
            "area": {"required": False, "allow_blank": True},
            "phone_number": {"required": False, "allow_blank": True},
            "installment_system": {"required": False, "allow_blank": True},
        }

    def get_has_returns(self, obj):
        # Check if this receipt has any associated RETURN receipts
        if hasattr(obj, '_has_returns'):
            return bool(obj._has_returns)
        return obj.child_receipts.filter(receipt_type="RETURN", is_deleted=False).exists()

    def to_internal_value(self, data):
        data_copy = _copy_mapping(data)

        # Field aliases
        if "customer_phone" in data_copy:
            data_copy["phone_number"] = data_copy.pop("customer_phone")
        if "customer_address" in data_copy:
            data_copy["address"] = data_copy.pop("customer_address")
        if "customer_area" in data_copy:
            data_copy["area"] = data_copy.pop("customer_area")

        # Map items -> sale_items
        if "items" in data_copy and "sale_items" not in data_copy:
            data_copy["sale_items"] = data_copy.pop("items")
        # Map installments -> installment_payments
        if "installments" in data_copy and "installment_payments" not in data_copy:
            data_copy["installment_payments"] = data_copy.pop("installments")

        data_copy = normalize_numeric_fields(
            data_copy,
            ["branch", "salesperson", "receipt_number", "total_amount", "down_payment", "sale_year", "sale_month"],
        )

        # If is_cash_sale is True and customer_name is empty/blank/whitespace, default to "عميل نقدي"
        is_cash = data_copy.get("is_cash_sale")
        if isinstance(is_cash, str):
            is_cash = is_cash.lower() in ("true", "1")
        if "customer_name" in data_copy and isinstance(data_copy["customer_name"], str):
            data_copy["customer_name"] = data_copy["customer_name"].strip()
        if is_cash and not str(data_copy.get("customer_name") or "").strip():
            data_copy["customer_name"] = "عميل نقدي"

        return super().to_internal_value(data_copy)

    def validate(self, data):
        from api.services.receipt_service import get_active_license
        from rest_framework import exceptions

        branch = data.get("branch", self.instance.branch if self.instance else None)
        salesperson = data.get("salesperson", self.instance.salesperson if self.instance else None)
        sale_year = data.get("sale_year", self.instance.sale_year if self.instance else None)
        sale_month = data.get("sale_month", self.instance.sale_month if self.instance else None)
        is_cash = data.get("is_cash_sale", self.instance.is_cash_sale if self.instance else False)
        customer_name = data.get("customer_name", self.instance.customer_name if self.instance else "")
        total_amount = data.get("total_amount", self.instance.total_amount if self.instance else None)
        down_payment = data.get("down_payment", self.instance.down_payment if self.instance else 0)
        receipt_type = data.get("receipt_type", self.instance.receipt_type if self.instance else "SALE")
        receipt_number = data.get("receipt_number", None)
        items = data.get("sale_items", None)

        if receipt_number is not None and receipt_number <= 0:
            raise ValidationError({"receipt_number": "رقم الفاتورة يجب أن يكون رقماً موجباً."})

        validate_month_year(
            sale_month,
            sale_year,
            min_year=2000,
            max_year=2100,
            month_field="sale_month",
            year_field="sale_year",
        )

        if not is_cash and not str(customer_name or "").strip():
            raise ValidationError({"customer_name": "يجب إدخال اسم العميل لفاتورة التقسيط."})

        if total_amount is not None and float(total_amount) <= 0:
            raise ValidationError({"total_amount": "إجمالي الفاتورة يجب أن يكون أكبر من صفر."})
        if down_payment is not None and float(down_payment) < 0:
            raise ValidationError({"down_payment": "المقدم لا يمكن أن يكون سالباً."})
        if (
            receipt_type != "RETURN"
            and total_amount is not None
            and down_payment is not None
            and float(down_payment) > float(total_amount) + 0.01
        ):
            raise ValidationError({"down_payment": "المقدم لا يمكن أن يتجاوز إجمالي الفاتورة."})

        if self.instance and branch and branch.id != self.instance.branch_id:
            raise ValidationError({"branch": "لا يمكن نقل الفاتورة لفرع آخر."})

        if salesperson and branch and salesperson.branch_id != branch.id:
            raise ValidationError({"salesperson": "المندوب المحدد لا يتبع هذا الفرع."})

        if items and branch:
            for item_data in items:
                inv_item = item_data.get("inventory_item")
                if inv_item and inv_item.branch_id != branch.id:
                    raise ValidationError({"items": f"الصنف '{inv_item.name}' لا يتبع هذا الفرع."})

        from api.services.receipt_service import get_first_production_license_start_date
        active_lic = get_active_license()
        is_print_only = bool(active_lic and active_lic.product_id in (2, 3))

        is_pre_license = False
        first_start = get_first_production_license_start_date()
        if first_start and sale_year and sale_month:
            try:
                inv_date = datetime.date(int(sale_year), int(sale_month), 1)
                lic_start = first_start.replace(day=1)
                if inv_date < lic_start:
                    is_pre_license = True
            except (ValueError, TypeError):
                pass

        if is_print_only or is_pre_license:
            if items and len(items) > 0:
                raise exceptions.ValidationError({
                    "items": "لا يمكن إضافة بنود أصناف مجزأة في هذه الفاتورة (باقة طباعة فقط أو فاتورة سابقة للاشتراك)."
                })
            products_text = data.get("products_text", self.instance.products_text if self.instance else "")
            if not str(products_text or "").strip():
                raise exceptions.ValidationError({
                    "products_text": "يجب إدخال وصف البضاعة كنص."
                })
            if float(total_amount or 0) <= 0:
                raise exceptions.ValidationError({
                    "total_amount": "يجب إدخال إجمالي الفاتورة بشكل صحيح."
                })

        return data

    def create(self, validated_data):
        from api.services.receipt_service import create_receipt
        items_data = validated_data.pop("sale_items", [])
        installments_data = validated_data.pop("payments", [])
        return create_receipt(validated_data, items_data, installments_data)

    def update(self, instance, validated_data):
        from api.services.receipt_service import update_receipt
        items_data = validated_data.pop("sale_items", None)
        installments_data = validated_data.pop("payments", None)
        return update_receipt(instance, validated_data, items_data, installments_data)


# ---------------------------------------------------------------------------
# 13. Expense
# ---------------------------------------------------------------------------

class ExpenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense
        fields = [
            "id", "branch", "category", "amount", "description",
            "expense_year", "expense_month",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(data, ["branch", "amount", "expense_year", "expense_month"])
        return super().to_internal_value(data_copy)

    def validate_description(self, value):
        return _strip_required_name(value, "بيان المصروف")

    def validate(self, data):
        amount = data.get("amount", self.instance.amount if self.instance else None)
        exp_month = data.get("expense_month", self.instance.expense_month if self.instance else None)
        exp_year = data.get("expense_year", self.instance.expense_year if self.instance else None)
        if amount is not None and amount <= 0:
            raise ValidationError({"amount": "قيمة المصروف يجب أن تكون أكبر من صفر."})
        validate_month_year(
            exp_month,
            exp_year,
            min_year=2000,
            max_year=2100,
            month_field="expense_month",
            year_field="expense_year",
        )
        return data


# ---------------------------------------------------------------------------
# 14. CompanySetting
# ---------------------------------------------------------------------------

class CompanySettingSerializer(serializers.ModelSerializer):
    admin_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CompanySetting
        fields = [
            "id", "name", "description",
            "phone1", "phone2", "footer_text",
            "collection_commission_rate", "zoom_level",
            "is_deleted", "created_at", "admin_password"
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        data_copy = normalize_numeric_fields(data, ["collection_commission_rate", "zoom_level"])
        return super().to_internal_value(data_copy)

    def validate(self, data):
        rate = data.get("collection_commission_rate", None)
        zoom = data.get("zoom_level", None)
        if rate is not None and (rate < 0 or rate > 100):
            raise ValidationError({"collection_commission_rate": "نسبة عمولة التحصيل يجب أن تكون بين 0 و 100."})
        if zoom is not None and (zoom < 0.5 or zoom > 2.5):
            raise ValidationError({"zoom_level": "نسبة التكبير يجب أن تكون بين 0.5 و 2.5."})
        return data

    def update(self, instance, validated_data):
        admin_password = validated_data.pop('admin_password', None)
        if admin_password:
            from django.contrib.auth.models import User
            user = User.objects.filter(is_superuser=True).first()
            if user:
                user.set_password(admin_password)
                user.save()
        return super().update(instance, validated_data)

    def create(self, validated_data):
        admin_password = validated_data.pop('admin_password', None)
        instance = super().create(validated_data)
        if admin_password:
            from django.contrib.auth.models import User
            user = User.objects.filter(is_superuser=True).first()
            if user:
                user.set_password(admin_password)
                user.save()
        return instance


# ---------------------------------------------------------------------------
# 15. ClientLicense
# ---------------------------------------------------------------------------

class ClientLicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClientLicense
        fields = [
            "id", "product_id",
            "start_date", "expiry_date", "invoices_balance",
            "is_active", "machine_id", "company_code", "license_code_hash",
            "last_checkin", "is_deleted", "created_at",
        ]
        read_only_fields = [
            "id", "license_code_hash",
            "last_checkin", "is_deleted", "created_at",
        ]
        extra_kwargs = {
            "license_code_hash": {"write_only": False},  # readable for audit
        }


# ---------------------------------------------------------------------------
# 16. UsedLicense
# ---------------------------------------------------------------------------

class UsedLicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = UsedLicense
        fields = ["id", "code_hash", "used_at", "is_deleted"]
        read_only_fields = ["id", "used_at", "is_deleted"]


# ---------------------------------------------------------------------------
# 17. LicenseHistory
# ---------------------------------------------------------------------------

class LicenseHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = LicenseHistory
        fields = [
            "id", "machine_id", "product_name", "operation_type",
            "start_date", "end_date", "added_balance", "archived_at",
            "status", "is_deleted", ]
        read_only_fields = ["id", "archived_at", "is_deleted"]


