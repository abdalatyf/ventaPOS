"""
models.py — VentaPOS NextGen Backend
=====================================
Single Source of Truth: d:/Projects/VentaPOS/VentaPOS_NextGen/docs/architecture/02_data_models.md

Design policies enforced:
  1. AutoField/BigAutoField primary keys (no UUIDs).
  2. Single-tenant (no tenant_id FK).
  3. is_deleted BOOLEAN NOT NULL DEFAULT FALSE on every transactional table.
  4. DECIMAL(12, 2) for all financial columns.
  5. Integer fields for all quantities.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Q, Max
import uuid

# ---------------------------------------------------------------------------
# Helper: base soft-delete queryset
# ---------------------------------------------------------------------------

class ActiveManager(models.Manager):
    """Default manager that filters out soft-deleted rows (is_deleted=FALSE)."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Unfiltered manager — use when you explicitly need deleted rows."""
    pass


# ===========================================================================
# 1. Branch (المخزن / الفرع)
# ===========================================================================

class Branch(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="اسم الفرع")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_branch"
        verbose_name = "الفرع / المخزن"
        verbose_name_plural = "الفروع / المخازن"

    def __str__(self):
        return self.name


# ===========================================================================
# 2. Salesperson (المندوب)
# ===========================================================================

class Salesperson(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="salespeople")
    device_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    is_device_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_salesperson"
        verbose_name = "المندوب"
        verbose_name_plural = "المناديب"
        constraints = [
            models.UniqueConstraint(fields=["name", "branch"], name="uq_salesperson_name_branch")
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


# ===========================================================================
# 3. InventoryItem (البضاعة / الصنف)
# ===========================================================================

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="inventory_items")
    initial_quantity = models.PositiveIntegerField(default=0)
    initial_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    initial_commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    initial_month = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    initial_year = models.PositiveIntegerField(default=2026, validators=[MinValueValidator(2025)])
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_inventoryitem"
        verbose_name = "صنف البضاعة"
        verbose_name_plural = "أصناف البضاعة"
        constraints = [
            models.UniqueConstraint(fields=["name", "branch"], name="uq_inventory_item_name_branch")
        ]
        ordering = ['name']
        indexes = [
            models.Index(fields=["branch", "name"], name="idx_inv_item_branch_name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"

    def get_stock_at_date(self, month, year):
        if year < self.initial_year or (year == self.initial_year and month < self.initial_month):
            return 0

        total_purchased = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='PURCHASE',
            is_deleted=False, invoice__is_deleted=False
        ).filter(
            Q(invoice__invoice_year__lt=year) |
            Q(invoice__invoice_year=year, invoice__invoice_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_returned = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='RETURN',
            is_deleted=False, invoice__is_deleted=False
        ).filter(
            Q(invoice__invoice_year__lt=year) |
            Q(invoice__invoice_year=year, invoice__invoice_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_sold = self.saleitem_set.filter(
            is_deleted=False, receipt__is_deleted=False
        ).filter(
            Q(receipt__sale_year__lt=year) |
            Q(receipt__sale_year=year, receipt__sale_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        adjustments = self.adjustments.filter(
            is_deleted=False
        ).filter(
            Q(year__lt=year) | Q(year=year, month__lte=month)
        )
        total_deficit = adjustments.filter(adjustment_type='DEFICIT').aggregate(total=Sum('quantity'))['total'] or 0
        total_surplus = adjustments.filter(adjustment_type='SURPLUS').aggregate(total=Sum('quantity'))['total'] or 0

        final_stock = (
            self.initial_quantity + total_purchased + total_surplus
        ) - (total_sold + total_returned + total_deficit)
        return max(0, final_stock)

    def get_commission_at_date(self, month, year):
        latest_comm = self.commission_records.filter(
            is_deleted=False
        ).filter(
            Q(activation_year__lt=year) |
            Q(activation_year=year, activation_month__lte=month)
        ).order_by('-activation_year', '-activation_month', '-id').first()

        if latest_comm:
            return latest_comm.commission_amount
        return self.initial_commission_amount

    def get_price_at_date(self, month, year):
        latest_purchase = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='PURCHASE',
            is_deleted=False, invoice__is_deleted=False
        ).filter(
            Q(invoice__invoice_year__lt=year) |
            Q(invoice__invoice_year=year, invoice__invoice_month__lte=month)
        ).order_by('-invoice__invoice_year', '-invoice__invoice_month', '-id').first()

        if latest_purchase:
            return latest_purchase.purchase_price
        return self.initial_purchase_price


# ===========================================================================
# 4. CommissionHistory (سجل عمولات المناديب)
# ===========================================================================

class CommissionHistory(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="commission_records")
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    activation_month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    activation_year = models.PositiveIntegerField(validators=[MinValueValidator(2025)])
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_commissionhistory"
        verbose_name = "سجل العمولة"
        verbose_name_plural = "سجل العمولات"
        constraints = [
            models.UniqueConstraint(fields=["item", "activation_month", "activation_year"], name="uq_comm_hist_item_date")
        ]
        ordering = ['-activation_year', '-activation_month']

    def __str__(self):
        return f"{self.item.name} — {self.commission_amount} ({self.activation_month}/{self.activation_year})"


# ===========================================================================
# 5. InventoryAdjustment (جرد وتسويات البضاعة)
# ===========================================================================

class InventoryAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ("DEFICIT", "عجز (-)"),
        ("SURPLUS", "زيادة (+)"),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="adjustments")
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.PositiveIntegerField(validators=[MinValueValidator(2025)])
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_inventoryadjustment"
        verbose_name = "تسوية المخزون"
        verbose_name_plural = "تسويات المخزون"
        ordering = ['-year', '-month', '-id']

    def __str__(self):
        sign = "+" if self.adjustment_type == "SURPLUS" else "-"
        return f"{sign}{self.quantity} × {self.item.name}"


# ===========================================================================
# 6. Supplier (الموردين)
# ===========================================================================

class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_supplier"
        verbose_name = "المورد"
        verbose_name_plural = "الموردون"

    def __str__(self):
        return self.name


# ===========================================================================
# 7. PurchaseInvoice (فاتورة الشراء / المرتجع)
# ===========================================================================

class PurchaseInvoice(models.Model):
    INVOICE_TYPES = [
        ("PURCHASE", "فاتورة شراء"),
        ("RETURN", "فاتورة مرتجع"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="purchase_invoices")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_invoices")
    invoice_number = models.PositiveIntegerField()
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default="PURCHASE")
    invoice_month = models.PositiveIntegerField(db_index=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    invoice_year = models.PositiveIntegerField(db_index=True, validators=[MinValueValidator(2025)])
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_purchaseinvoice"
        verbose_name = "فاتورة الشراء"
        verbose_name_plural = "فواتير الشراء"
        constraints = [
            models.UniqueConstraint(fields=["branch", "invoice_number", "supplier"], name="uq_pur_inv_branch_num_supp")
        ]
        ordering = ['-invoice_year', '-invoice_month', '-id']

    def __str__(self):
        return f"#{self.invoice_number} {self.invoice_type} — {self.supplier.name}"


# ===========================================================================
# 8. PurchaseInvoiceItem (أصناف فاتورة الشراء)
# ===========================================================================

class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="items")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="purchaseinvoiceitem_set")
    quantity = models.PositiveIntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_purchaseinvoiceitem"
        verbose_name = "صنف فاتورة شراء"
        verbose_name_plural = "أصناف فواتير الشراء"

    def __str__(self):
        return f"{self.inventory_item.name} × {self.quantity}"


# ===========================================================================
# 9. Receipt (الفاتورة / الوصل)
# ===========================================================================

class Receipt(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="receipts", db_index=True)
    salesperson = models.ForeignKey(Salesperson, on_delete=models.PROTECT, related_name="receipts", null=True, blank=True)
    receipt_number = models.PositiveIntegerField(db_index=True)
    client_uuid = models.UUIDField(default=uuid.uuid4)
    receipt_hash = models.CharField(max_length=64, null=True, blank=True)
    
    customer_name = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    installment_system = models.CharField(max_length=200, blank=True, null=True)
    
    sale_year = models.PositiveIntegerField(db_index=True)
    sale_month = models.PositiveIntegerField(db_index=True)
    is_cash_sale = models.BooleanField(default=False)
    
    products_text = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=20, default="DESKTOP")
    sync_action = models.CharField(max_length=20, default="NEW")
    is_confirmed = models.BooleanField(default=True)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_receipt"
        verbose_name = "الفاتورة"
        verbose_name_plural = "الفواتير"
        constraints = [
            models.UniqueConstraint(fields=["branch", "receipt_number"], name="uq_receipt_branch_number")
        ]
        ordering = ['-receipt_number']
        indexes = [
            models.Index(fields=["branch", "sale_year", "sale_month"], name="idx_receipt_branch_date"),
            models.Index(fields=["receipt_hash"], name="idx_receipt_hash"),
        ]

    def __str__(self):
        return f"فاتورة #{self.receipt_number} — {self.customer_name}"

    @classmethod
    def get_next_receipt_number(cls, branch):
        last_num = cls.objects.filter(branch=branch).aggregate(Max('receipt_number'))['receipt_number__max']
        return (last_num or 0) + 1

    @property
    def is_authentic(self):
        try:
            from .utils.security_utils import generate_receipt_signature
            expected_hash = generate_receipt_signature(
                self.receipt_number, self.total_amount, self.sale_month, self.sale_year
            )
            return self.receipt_hash == expected_hash
        except ImportError:
            return True


# ===========================================================================
# 10. SaleItem (أصناف الفاتورة المباعة)
# ===========================================================================

class SaleItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="sale_items")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="saleitem_set")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_saleitem"
        verbose_name = "الصنف المباع"
        verbose_name_plural = "الأصناف المباعة"

    def __str__(self):
        return f"{self.inventory_item.name} × {self.quantity}"


# ===========================================================================
# 11. InstallmentPayment (القسط)
# ===========================================================================

class InstallmentPayment(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_installmentpayment"
        verbose_name = "القسط"
        verbose_name_plural = "الأقساط"

    def __str__(self):
        return f"قسط {self.amount} مستحق في {self.payment_date}"


# ===========================================================================
# 12. Expense (المصاريف / الخزنة)
# ===========================================================================

class Expense(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    expense_year = models.IntegerField()
    expense_month = models.IntegerField()
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_expense"
        verbose_name = "المصروف"
        verbose_name_plural = "المصروفات"

    def __str__(self):
        return f"{self.description} ({self.amount})"


# ===========================================================================
# 13. CompanySetting (إعدادات الشركة)
# ===========================================================================

class CompanySetting(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, null=True)
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    footer_text = models.CharField(max_length=250, default="تطبق الشروط والأحكام")
    is_cloud_viewer = models.BooleanField(default=False)
    collection_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        verbose_name="نسبة عمولة التحصيل"
    )
    zoom_level = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.00,
        verbose_name="مستوى التكبير"
    )
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_companysetting"
        verbose_name = "إعدادات الشركة"
        verbose_name_plural = "إعدادات الشركة"

    def save(self, *args, **kwargs):
        if not self.pk and CompanySetting.objects.exists():
            # Ensure Singleton
            existing = CompanySetting.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ===========================================================================
# 14. ClientLicense (الترخيص)
# ===========================================================================

class ClientLicense(models.Model):
    product_id = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    invoices_balance = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    machine_id = models.CharField(max_length=255, null=True, blank=True)
    company_code = models.CharField(max_length=10, null=True, blank=True)
    license_code_hash = models.CharField(max_length=64, null=True, blank=True)
    is_online_active = models.BooleanField(default=False)
    online_start_date = models.DateField(null=True, blank=True)
    online_expiry_date = models.DateField(null=True, blank=True)
    last_checkin = models.DateTimeField(auto_now=True)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_clientlicense"
        verbose_name = "الترخيص"
        verbose_name_plural = "التراخيص"

    def __str__(self):
        return f"License Type {self.product_id} - Active: {self.is_active}"


# ===========================================================================
# 15. UsedLicense (الأكواد المستخدمة)
# ===========================================================================

class UsedLicense(models.Model):
    code_hash = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_usedlicense"
        verbose_name = "الكود المستخدم"
        verbose_name_plural = "الأكواد المستخدمة"

    def __str__(self):
        return self.code_hash


# ===========================================================================
# 16. LicenseHistory (أرشيف التراخيص)
# ===========================================================================

class LicenseHistory(models.Model):
    machine_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    operation_type = models.CharField(max_length=50, default="تجديد/تفعيل")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    added_balance = models.IntegerField(default=0)
    archived_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="أرشيف")
    
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_licensehistory"
        verbose_name = "أرشيف الترخيص"
        verbose_name_plural = "أرشيف التراخيص"


# ===========================================================================
# 17. PendingExternalReceipt (الفواتير الخارجية المعلقة)
# ===========================================================================

class PendingExternalReceipt(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="pending_receipts")
    batch_id = models.CharField(max_length=100, default="", blank=True)
    source = models.CharField(max_length=20)
    payload = models.JSONField()
    is_processed = models.BooleanField(default=False)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesapp_pendingexternalreceipt"
        verbose_name = "الفاتورة المعلقة"
        verbose_name_plural = "الفواتير المعلقة"
        ordering = ['-created_at']

    def __str__(self):
        return f"Pending Receipt (Batch {self.batch_id}) - {self.source}"
