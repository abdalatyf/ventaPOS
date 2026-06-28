"""
serializers.py — VentaPOS NextGen Backend
==========================================
Serializers for all 19 schema-approved models.

Design decisions:
- Every serializer exposes `tenant` as a read-only UUID field (injected by the
  view from the authenticated request context, not supplied by the client).
- Nested writable serializers are used only where the API contract specifies
  embedded creation (PurchaseInvoice → items, Receipt → sale_items + installments).
- Financial fields (DecimalField) are serialized as strings to preserve
  precision across JSON boundaries.
- The `is_deleted` field is read-only everywhere; soft-delete happens via a
  dedicated action, never via direct PATCH.
- Field name mapping (SQLite ↔ PostgreSQL) follows the translation layer
  documented in api_contract.md §3.
"""

from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Tenant,
    CloudUser,
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
    ActionLog,
)
from .utils.security_utils import (
    generate_receipt_signature,
    generate_record_signature,
    get_machine_id,
)


# ---------------------------------------------------------------------------
# 1. Tenant
# ---------------------------------------------------------------------------

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id", "company_code", "name", "is_active",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 2. CloudUser
# ---------------------------------------------------------------------------

class CloudUserSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = CloudUser
        fields = [
            "id", "tenant_id", "username", "password_hash", "role",
            "is_active", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]
        extra_kwargs = {
            "password_hash": {"write_only": True},
        }


# ---------------------------------------------------------------------------
# 3. Branch
# ---------------------------------------------------------------------------

class BranchSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id", "tenant_id", "local_id", "name",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 4. Salesperson
# ---------------------------------------------------------------------------

class SalespersonSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = Salesperson
        fields = [
            "id", "tenant_id", "branch", "local_id", "name",
            "device_token", "is_device_active", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "device_token", "is_deleted", "created_at"]


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

    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    current_stock = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "tenant_id", "branch", "local_id", "name",
            "initial_quantity", "initial_purchase_price",
            "initial_commission_amount", "initial_month", "initial_year",
            "is_deleted", "created_at", "current_stock",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at", "current_stock"]

    def get_current_stock(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return obj.get_stock_at_date(now.month, now.year)


# ---------------------------------------------------------------------------
# 6. CommissionHistory
# ---------------------------------------------------------------------------

class CommissionHistorySerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = CommissionHistory
        fields = [
            "id", "tenant_id", "inventory_item", "commission_amount",
            "activation_month", "activation_year", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 7. InventoryAdjustment
# ---------------------------------------------------------------------------

class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = InventoryAdjustment
        fields = [
            "id", "tenant_id", "inventory_item", "adjustment_type",
            "quantity", "reason", "adjustment_month", "adjustment_year",
            "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 8. Supplier
# ---------------------------------------------------------------------------

class SupplierSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = Supplier
        fields = ["id", "tenant_id", "name", "is_deleted", "created_at"]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 9 & 10. PurchaseInvoice + PurchaseInvoiceItem
# ---------------------------------------------------------------------------

class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = PurchaseInvoiceItem
        fields = [
            "id", "tenant_id", "purchase_invoice", "inventory_item",
            "quantity", "purchase_price", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "purchase_invoice", "is_deleted", "created_at"]


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    items = PurchaseInvoiceItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseInvoice
        fields = [
            "id", "tenant_id", "branch", "supplier",
            "invoice_number", "invoice_type", "invoice_month", "invoice_year",
            "is_deleted", "created_at", "items",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        tenant = self.context["tenant"]
        with transaction.atomic():
            invoice = PurchaseInvoice.objects.create(tenant=tenant, **validated_data)
            for item_data in items_data:
                PurchaseInvoiceItem.objects.create(
                    tenant=tenant,
                    purchase_invoice=invoice,
                    **item_data,
                )
        return invoice


# ---------------------------------------------------------------------------
# 11 & 12. SaleItem + Receipt
# ---------------------------------------------------------------------------

class SaleItemSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            "id", "tenant_id", "receipt", "inventory_item",
            "quantity", "unit_price", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "receipt", "is_deleted", "created_at"]

    def to_internal_value(self, data):
        # Allow the API contract field alias `inventory_item_id`
        if "inventory_item_id" in data and "inventory_item" not in data:
            data = data.copy()
            data["inventory_item"] = data.pop("inventory_item_id")
        return super().to_internal_value(data)


class InstallmentPaymentSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = InstallmentPayment
        fields = [
            "id", "tenant_id", "receipt", "payment_date",
            "amount", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "receipt", "is_deleted", "created_at"]


class ReceiptSerializer(serializers.ModelSerializer):
    """
    Handles nested creation of SaleItems and InstallmentPayments.

    Field name aliasing (api_contract.md §3 — Receipts Mapping):
      phone_number   ← stored as `phone_number` in DB
      address        ← stored as `address` in DB
      area           ← stored as `area` in DB
      created_at_local ← stored as `created_at_local` (device time)
    """

    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    # Nested writable collections
    sale_items = SaleItemSerializer(many=True, required=False)
    installment_payments = InstallmentPaymentSerializer(many=True, required=False)

    class Meta:
        model = Receipt
        fields = [
            "id", "tenant_id", "branch", "salesperson",
            "local_id", "receipt_number", "client_uuid", "receipt_hash",
            "customer_name", "phone_number", "address", "area",
            "total_amount", "down_payment", "installment_system",
            "sale_year", "sale_month", "is_cash_sale", "products_text",
            "is_confirmed", "is_deleted",
            "created_at_local", "created_at",
            "sale_items", "installment_payments",
        ]
        read_only_fields = [
            "id", "tenant_id", "receipt_hash", "is_confirmed",
            "is_deleted", "created_at",
        ]

    def to_internal_value(self, data):
        # Support the push payload alias `items` → `sale_items`
        if "items" in data and "sale_items" not in data:
            data = data.copy()
            data["sale_items"] = data.pop("items")
        # Support the push payload alias `installments` → `installment_payments`
        if "installments" in data and "installment_payments" not in data:
            data = data.copy()
            data["installment_payments"] = data.pop("installments")
        return super().to_internal_value(data)

    def create(self, validated_data):
        items_data = validated_data.pop("sale_items", [])
        installments_data = validated_data.pop("installment_payments", [])
        tenant = self.context["tenant"]

        with transaction.atomic():
            # Deduct from license balance (pessimistic lock)
            active_lic = (
                ClientLicense.objects
                .select_for_update()
                .filter(
                    tenant=tenant,
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
                    .filter(tenant=tenant, is_deleted=False)
                    .order_by("receipt_number")
                    .last()
                )
                validated_data["receipt_number"] = (
                    (last.receipt_number + 1) if last else 1
                )

            receipt = Receipt.objects.create(tenant=tenant, **validated_data)

            for item_data in items_data:
                SaleItem.objects.create(tenant=tenant, receipt=receipt, **item_data)

            for inst_data in installments_data:
                InstallmentPayment.objects.create(
                    tenant=tenant, receipt=receipt, **inst_data
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
        tenant = self.context["tenant"]

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                instance.sale_items.all().update(is_deleted=True)
                for item_data in items_data:
                    SaleItem.objects.create(
                        tenant=tenant, receipt=instance, **item_data
                    )

            if installments_data is not None:
                instance.installment_payments.all().update(is_deleted=True)
                for inst_data in installments_data:
                    InstallmentPayment.objects.create(
                        tenant=tenant, receipt=instance, **inst_data
                    )

            # Re-hash the receipt
            current_items = (
                items_data
                if items_data is not None
                else list(instance.sale_items.filter(is_deleted=False).values(
                    "quantity", "unit_price"
                ))
            )
            instance.receipt_hash = generate_receipt_signature(
                instance.receipt_number,
                instance.total_amount,
                instance.sale_month,
                instance.sale_year,
                current_items,
            )
            instance.save(update_fields=["receipt_hash"])

        return instance


# ---------------------------------------------------------------------------
# 13. Expense
# ---------------------------------------------------------------------------

class ExpenseSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id", "tenant_id", "branch", "amount", "description",
            "expense_year", "expense_month",
            "is_deleted", "created_at_local", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 14. CompanySetting
# ---------------------------------------------------------------------------

class CompanySettingSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = CompanySetting
        fields = [
            "id", "tenant_id", "name", "description",
            "phone1", "phone2", "footer_text",
            "is_cloud_viewer", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# 15. ClientLicense
# ---------------------------------------------------------------------------

class ClientLicenseSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = ClientLicense
        fields = [
            "id", "tenant_id", "product_id",
            "start_date", "expiry_date", "invoices_balance",
            "is_active", "machine_id", "company_code", "license_code_hash",
            "is_online_active", "online_start_date", "online_expiry_date",
            "last_checkin", "is_deleted", "created_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "license_code_hash",
            "last_checkin", "is_deleted", "created_at",
        ]
        extra_kwargs = {
            "license_code_hash": {"write_only": False},  # readable for audit
        }


# ---------------------------------------------------------------------------
# 16. UsedLicense
# ---------------------------------------------------------------------------

class UsedLicenseSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = UsedLicense
        fields = ["id", "tenant_id", "code_hash", "used_at", "is_deleted"]
        read_only_fields = ["id", "tenant_id", "used_at", "is_deleted"]


# ---------------------------------------------------------------------------
# 17. LicenseHistory
# ---------------------------------------------------------------------------

class LicenseHistorySerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = LicenseHistory
        fields = [
            "id", "tenant_id", "machine_id", "product_name", "operation_type",
            "start_date", "end_date", "added_balance", "archived_at",
            "status", "is_deleted",
        ]
        read_only_fields = ["id", "tenant_id", "archived_at", "is_deleted"]


# ---------------------------------------------------------------------------
# 18. PendingExternalReceipt
# ---------------------------------------------------------------------------

class PendingExternalReceiptSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)

    class Meta:
        model = PendingExternalReceipt
        fields = [
            "id", "tenant_id", "branch", "batch_id", "source",
            "payload", "is_processed", "is_deleted", "created_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_deleted", "created_at"]


# ---------------------------------------------------------------------------
# LEGACY — ActionLog (not in approved schema)
# ---------------------------------------------------------------------------

class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = ["id", "actor", "action_type", "model_name", "details", "created_at"]
        read_only_fields = ["id", "created_at"]
