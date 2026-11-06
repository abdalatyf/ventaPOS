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

    def get_current_stock(self, obj):
        if hasattr(obj, '_precomputed_stock'):
            return obj._precomputed_stock
        from django.utils import timezone
        now = timezone.now()
        return obj.get_stock_at_date(now.month, now.year)


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
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)
        if "adjustment_month" in data_copy and "month" not in data_copy:
            data_copy["month"] = data_copy["adjustment_month"]
        if "adjustment_year" in data_copy and "year" not in data_copy:
            data_copy["year"] = data_copy["adjustment_year"]
        if "inventory_item" in data_copy and "item" not in data_copy:
            data_copy["item"] = data_copy["inventory_item"]
        if not data_copy.get("adjustment_type"):
            data_copy["adjustment_type"] = "DEFICIT"
        return super().to_internal_value(data_copy)

    def validate(self, data):
        from api.views import get_default_date
        from rest_framework.exceptions import ValidationError
        default_year, default_month = get_default_date()
        
        target_year = data.get("year", self.instance.year if self.instance else None)
        target_month = data.get("month", self.instance.month if self.instance else None)
        item = data.get("item", self.instance.item if self.instance else None)
        qty = data.get("quantity", self.instance.quantity if self.instance else None)
        
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

    class Meta:
        model = Supplier
        fields = ["id", "name", "is_deleted", "created_at"]
        read_only_fields = ["id", "is_deleted", "created_at"]


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


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, required=False)
    invoice_number = serializers.IntegerField(required=False)

    class Meta:
        model = PurchaseInvoice
        fields = [
            "id", "branch", "supplier",
            "invoice_number", "invoice_type", "invoice_month", "invoice_year",
            "is_deleted", "created_at", "items",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
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
        # Allow the API contract field alias `inventory_item_id`
        if "inventory_item_id" in data and "inventory_item" not in data:
            data = data.copy()
            data["inventory_item"] = data.pop("inventory_item_id")
        # Allow `sell_price` alias for `unit_price` (used by POS frontend)
        if "sell_price" in data and "unit_price" not in data:
            data = data.copy() if not isinstance(data, dict) else dict(data)
            data["unit_price"] = data.pop("sell_price")
        return super().to_internal_value(data)


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
        # Build payment_date from payment_month + payment_year if not provided
        data = dict(data) if not isinstance(data, dict) else dict(data)
        if "payment_date" not in data and "payment_month" in data and "payment_year" in data:
            month = int(data["payment_month"])
            year = int(data["payment_year"])
            data["payment_date"] = f"{year}-{month:02d}-25"
        return super().to_internal_value(data)


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
        data = data.copy() if hasattr(data, "copy") else dict(data)
        
        # Field aliases
        if "customer_phone" in data:
            data["phone_number"] = data.pop("customer_phone")
        if "customer_address" in data:
            data["address"] = data.pop("customer_address")
        if "customer_area" in data:
            data["area"] = data.pop("customer_area")
            
        # Map items -> sale_items
        if "items" in data and "sale_items" not in data:
            data["sale_items"] = data.pop("items")
        # Map installments -> installment_payments
        if "installments" in data and "installment_payments" not in data:
            data["installment_payments"] = data.pop("installments")
            
        # Support id -> local_id removed

        # If is_cash_sale is True and customer_name is empty/blank/None, default to "عميل نقدي"
        is_cash = data.get("is_cash_sale")
        if isinstance(is_cash, str):
            is_cash = is_cash.lower() in ("true", "1")
        if is_cash and not data.get("customer_name"):
            data["customer_name"] = "عميل نقدي"
            
        return super().to_internal_value(data)

    def validate(self, data):
        from api.services.receipt_service import get_active_license
        from rest_framework import exceptions
        import datetime

        active_lic = get_active_license()
        is_print_only = bool(active_lic and active_lic.product_id in (2, 3))

        sale_year = data.get("sale_year", self.instance.sale_year if self.instance else None)
        sale_month = data.get("sale_month", self.instance.sale_month if self.instance else None)
        items = data.get("sale_items", None)

        is_pre_license = False
        if active_lic and active_lic.start_date and sale_year and sale_month:
            try:
                inv_date = datetime.date(int(sale_year), int(sale_month), 1)
                lic_start = active_lic.start_date.replace(day=1)
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
            total_amount = data.get("total_amount", self.instance.total_amount if self.instance else 0)
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


