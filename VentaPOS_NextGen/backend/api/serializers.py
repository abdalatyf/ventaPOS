"""
serializers.py — VentaPOS NextGen Backend
==========================================
Serializers for all 19 schema-approved models.

Design decisions:
- Every serializer exposes `tenant` as a read-only UUID field (injected by the
  view from the authenticated request context, not supplied by the client).
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
    PendingExternalReceipt,
    )
from .utils.security_utils import (
    generate_receipt_signature,
    generate_record_signature,
    get_machine_id,
)


# ---------------------------------------------------------------------------
# 1. Tenant
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
            "id", "inventory_item", "commission_amount",
            "activation_month", "activation_year", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 7. InventoryAdjustment
# ---------------------------------------------------------------------------

class InventoryAdjustmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = InventoryAdjustment
        fields = [
            "id", "inventory_item", "adjustment_type",
            "quantity", "reason", "adjustment_month", "adjustment_year",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

    def validate(self, data):
        if data.get("adjustment_type") == "DEFICIT":
            from api.views import get_default_date_for_tenant
            from rest_framework.exceptions import ValidationError
            default_year, default_month = get_default_date_for_tenant()
            
            target_year = data.get("adjustment_year", self.instance.adjustment_year if self.instance else None)
            target_month = data.get("adjustment_month", self.instance.adjustment_month if self.instance else None)
            item = data.get("inventory_item", self.instance.inventory_item if self.instance else None)
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
        branch = validated_data.get("branch")
        
        # Stock validation for RETURNS
        if validated_data.get("invoice_type") == "RETURN":
            from api.views import get_default_date_for_tenant
            from rest_framework.exceptions import ValidationError
            default_year, default_month = get_default_date_for_tenant()
            target_year = validated_data["invoice_year"]
            target_month = validated_data["invoice_month"]
            
            for item_data in items_data:
                item = item_data["inventory_item"]
                qty = item_data["quantity"]
                safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                if qty > safe_limit:
                    raise ValidationError({
                        "error": f"عفواً، لا يمكن الإرجاع! أقصى كمية يمكن إرجاعها للمورد للصنف '{item.name}' هي ({safe_limit})."
                    })

        # Auto-generate invoice_number sequentially per branch if not provided
        if "invoice_number" not in validated_data:
            from django.db.models import Max
            last_invoice = PurchaseInvoice.objects.filter(
                branch=branch
            ).aggregate(Max("invoice_number"))
            last_num = last_invoice.get("invoice_number__max") or 0
            validated_data["invoice_number"] = last_num + 1

        with transaction.atomic():
            invoice = PurchaseInvoice.objects.create(**validated_data)
            for item_data in items_data:
                PurchaseInvoiceItem.objects.create(
                    invoice=invoice,
                    **item_data,
                )
        return invoice


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

    class Meta:
        model = Receipt
        fields = [
            "id", "branch", "salesperson",
            "receipt_number", "receipt_hash",
            "customer_name", "phone_number", "address", "area",
            "total_amount", "down_payment", "installment_system",
            "sale_year", "sale_month", "is_cash_sale", "products_text",
            "is_confirmed", "is_deleted",
            "created_at",
            "sale_items", "installment_payments",
        ]
        read_only_fields = [
            "id", "receipt_hash", "is_confirmed",
            "is_deleted", "created_at",
        ]
        extra_kwargs = {
            "receipt_number": {"required": False},
            "products_text": {"required": False},
            "address": {"required": False, "allow_blank": True},
            "area": {"required": False, "allow_blank": True},
            "phone_number": {"required": False, "allow_blank": True},
            "installment_system": {"required": False, "allow_blank": True},
        }

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

    def create(self, validated_data):
        items_data = validated_data.pop("sale_items", [])
        installments_data = validated_data.pop("installment_payments", [])


        with transaction.atomic():
            # Deduct from license balance (pessimistic lock)
            active_lic = (
                ClientLicense.objects
                .select_for_update()
                .filter(
                    is_active=True,
                    is_deleted=False,
                    invoices_balance__gt=0,
                )
                .first()
            )
            if not active_lic:
                raise ValidationError({
                    "license": (
                        "لا يمكن طباعة أو إصدار الفاتورة، رصيد الفواتير المسموح به "
                        "للرخصة قد نفد. يرجى الشحن أولاً."
                    )
                })

            # Auto-assign receipt_number if not provided
            if not validated_data.get("receipt_number"):
                last = (
                    Receipt.all_objects
                    .select_for_update()
                    .filter(is_deleted=False)
                    .order_by("receipt_number")
                    .last()
                )
                validated_data["receipt_number"] = (
                    (last.receipt_number + 1) if last else 1
                )

            # Auto-assign logic for local_id and created_at_local removed
            # Stock validation
            from api.views import get_default_date_for_tenant
            default_year, default_month = get_default_date_for_tenant()
            target_year = validated_data["sale_year"]
            target_month = validated_data["sale_month"]
            for item_data in items_data:
                item = item_data["inventory_item"]
                qty = item_data["quantity"]
                safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                if qty > safe_limit:
                    raise ValidationError({
                        "error": f"عفواً، لا يمكن البيع! أقصى كمية يمكن بيعها بأثر رجعي للصنف '{item.name}' هي ({safe_limit}) لتجنب حدوث رصيد سالب في الشهور اللاحقة."
                    })

            # legacy local_id assignment removed

            if "products_text" not in validated_data and items_data:
                validated_data["products_text"] = " + ".join([f"{i['inventory_item'].name}" if i['quantity'] == 1 else f"{i['quantity']} {i['inventory_item'].name}" for i in items_data])

            receipt = Receipt.objects.create(**validated_data)

            for item_data in items_data:
                SaleItem.objects.create(receipt=receipt, **item_data)

            for inst_data in installments_data:
                payment_month = inst_data.pop("payment_month", 1)
                payment_year = inst_data.pop("payment_year", 2026)
                if "payment_date" not in inst_data:
                    import datetime
                    inst_data["payment_date"] = datetime.date(payment_year, payment_month, 25)
                InstallmentPayment.objects.create(
                    receipt=receipt, **inst_data
                )

            # Generate & store receipt hash (schema §1.5)
            receipt.receipt_hash = generate_receipt_signature(
                receipt.receipt_number,
                receipt.total_amount,
                receipt.sale_month,
                receipt.sale_year,
                items_data,
            )
            receipt.save(update_fields=["receipt_hash"])

            # Deduct license balance & re-sign the license row
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

    def update(self, instance, validated_data):
        items_data = validated_data.pop("sale_items", None)
        installments_data = validated_data.pop("installment_payments", None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            from dateutil.relativedelta import relativedelta
            from datetime import date
            active_lic = ClientLicense.objects.filter(
                is_active=True, is_deleted=False
            ).first()
            if not active_lic:
                raise ValidationError({"license": "لا يوجد ترخيص ساري."})
                
            try:
                invoice_date = date(instance.sale_year, instance.sale_month, 1)
            except:
                raise ValidationError({"error": "تاريخ الفاتورة غير صحيح."})
                
            lic_start_month = active_lic.start_date.replace(day=1)
            if invoice_date < lic_start_month:
                raise ValidationError({"error": "التاريخ يسبق بداية الاشتراك."})
                
            if active_lic.expiry_date:
                last_allowed_month = (active_lic.expiry_date - relativedelta(months=2)).replace(day=1)
                if invoice_date > last_allowed_month:
                    raise ValidationError({"error": "التاريخ بعد انتهاء الاشتراك."})
                grace_end = active_lic.expiry_date + relativedelta(days=25)
                if date.today() > grace_end:
                    raise ValidationError({"error": "انتهت فترة الاشتراك."})

            instance.save()

            if items_data is not None:
                # Soft delete old items BEFORE calculating safe limits
                instance.sale_items.all().update(is_deleted=True)

                # Stock validation
                from api.views import get_default_date_for_tenant
                default_year, default_month = get_default_date_for_tenant()
                target_year = validated_data.get("sale_year", instance.sale_year)
                target_month = validated_data.get("sale_month", instance.sale_month)

                for item_data in items_data:
                    item = item_data["inventory_item"]
                    qty = item_data["quantity"]

                    safe_limit = item.get_safe_available_qty(target_month, target_year, default_month, default_year)
                    if qty > safe_limit:
                        raise ValidationError({
                            "error": f"عفواً، أقصى كمية يمكن بيعها أو تعديلها للصنف '{item.name}' في هذا التاريخ هي ({safe_limit})."
                        })

                for item_data in items_data:
                    SaleItem.objects.create(
                        receipt=instance, **item_data
                    )

            if installments_data is not None:
                instance.payments.all().update(is_deleted=True)
                for inst_data in installments_data:
                    payment_month = inst_data.pop("payment_month", 1)
                    payment_year = inst_data.pop("payment_year", 2026)
                    if "payment_date" not in inst_data:
                        import datetime
                        inst_data["payment_date"] = datetime.date(payment_year, payment_month, 25)
                    InstallmentPayment.objects.create(
                        receipt=instance, **inst_data
                    )

            # Re-hash the receipt
            current_items = (
                items_data
                if items_data is not None
                else list(instance.sale_items.filter(is_deleted=False).values(
                    "quantity", "unit_price"
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


# ---------------------------------------------------------------------------
# 13. Expense
# ---------------------------------------------------------------------------

class ExpenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense
        fields = [
            "id", "branch", "amount", "description",
            "expense_year", "expense_month",
            "is_deleted", "created_at_local", "created_at",
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
            "phone1", "phone2", "footer_text", "is_cloud_viewer",
            "collection_commission_rate", "zoom_level",
            "is_deleted", "created_at"
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
            "is_online_active", "online_start_date", "online_expiry_date",
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
            "status", "is_deleted",
        ]
        read_only_fields = ["id", "archived_at", "is_deleted"]


# ---------------------------------------------------------------------------
# 18. PendingExternalReceipt
# ---------------------------------------------------------------------------

class PendingExternalReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingExternalReceipt
        fields = [
            "id", "branch", "batch_id", "source",
            "payload", "is_processed", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]

