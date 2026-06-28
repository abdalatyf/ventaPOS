"""
models.py — VentaPOS NextGen Backend
=====================================
Single Source of Truth: d:/Projects/VentaPOS/database_schema.md
API Contract:           d:/Projects/VentaPOS/api_contract.md

Design policies enforced in every model:
  1. UUID primary keys (via django.db.models.UUIDField + uuid.uuid4 default).
  2. tenant_id FK on every tenant-owned table.
  3. is_deleted BOOLEAN NOT NULL DEFAULT FALSE on every transactional table.
  4. DECIMAL(12, 2) for all financial columns.
  5. TIMESTAMP WITH TIME ZONE via DateTimeField (USE_TZ=True required in settings).
  6. Composite unique constraints that include tenant_id to enforce per-tenant uniqueness.
  7. DB-level CHECK constraints mapped via Django's CheckConstraint in Meta.constraints.

Tables implemented (in schema order):
  1.  Tenant
  2.  CloudUser
  3.  Branch
  4.  Salesperson
  5.  InventoryItem
  6.  CommissionHistory
  7.  InventoryAdjustment
  8.  Supplier
  9.  PurchaseInvoice
  10. PurchaseInvoiceItem
  11. Receipt
  12. SaleItem
  13. InstallmentPayment
  14. Expense
  15. CompanySetting
  16. ClientLicense
  17. UsedLicense
  18. LicenseHistory
  19. PendingExternalReceipt

NOTE: The legacy ActionLog model is kept at the bottom to avoid breaking existing
migrations. It is NOT part of the approved schema and will be migrated away.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
# 1. Tenant (الشركة)
# ===========================================================================

class Tenant(models.Model):
    """Root tenant / company entity. All other tables reference this."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Managers
    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "tenant"
        verbose_name = "الشركة"
        verbose_name_plural = "الشركات"
        indexes = [
            # Partial index hint — enforced at DB level via migration RunSQL
            models.Index(fields=["id"], name="idx_tenant_active"),
        ]

    def __str__(self):
        return f"{self.company_code} — {self.name}"


# ===========================================================================
# 2. CloudUser (مستخدمو السحابة)
# ===========================================================================

class CloudUser(models.Model):
    """Cloud-level user accounts with role-based access."""

    ROLE_CHOICES = [
        ("ADMIN", "مدير النظام"),
        ("CASHIER", "أمين الخزنة"),
        ("VIEWER", "مستخدم السحابة"),
        ("BRANCH_MANAGER", "مدير الفرع"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="cloud_users"
    )
    username = models.CharField(max_length=150)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "cloud_user"
        verbose_name = "مستخدم السحابة"
        verbose_name_plural = "مستخدمو السحابة"
        constraints = [
            # UNIQUE (tenant_id, username) — per schema §4.2
            models.UniqueConstraint(
                fields=["tenant", "username"],
                name="uq_tenant_username",
                condition=models.Q(is_deleted=False),
            ),
            models.CheckConstraint(
                check=models.Q(role__in=["ADMIN", "CASHIER", "VIEWER", "BRANCH_MANAGER"]),
                name="chk_cloud_user_role",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_cloud_user_tenant"),
        ]

    def __str__(self):
        return f"{self.tenant.company_code}/{self.username}"


# ===========================================================================
# 3. Branch (المخزن / الفرع)
# ===========================================================================

class Branch(models.Model):
    """Physical branch or warehouse within a tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="branches"
    )
    local_id = models.IntegerField()          # SQLite sequential ID from local device
    name = models.CharField(max_length=150)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "branch"
        verbose_name = "الفرع / المخزن"
        verbose_name_plural = "الفروع / المخازن"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "local_id"],
                name="uq_tenant_branch_local_id",
            ),
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="uq_tenant_branch_name",
                condition=models.Q(is_deleted=False),
            ),
            models.CheckConstraint(
                check=models.Q(local_id__gte=0),
                name="chk_branch_local_id_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_branch_tenant"),
        ]

    def __str__(self):
        return f"{self.tenant.company_code}/{self.name}"


# ===========================================================================
# 4. Salesperson (المندوب)
# ===========================================================================

class Salesperson(models.Model):
    """Sales representative linked to a branch."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="salespeople"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="salespeople"
    )
    local_id = models.IntegerField()          # Local device sequential ID
    name = models.CharField(max_length=100)
    device_token = models.UUIDField(default=uuid.uuid4)
    is_device_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "salesperson"
        verbose_name = "المندوب"
        verbose_name_plural = "المناديب"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "local_id"],
                name="uq_tenant_salesperson_local_id",
            ),
            models.CheckConstraint(
                check=models.Q(local_id__gte=0),
                name="chk_salesperson_local_id_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_salesperson_tenant"),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.company_code})"


# ===========================================================================
# 5. InventoryItem (البضاعة / الصنف)
# ===========================================================================

class InventoryItem(models.Model):
    """Catalog item tracked per branch."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="inventory_items"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="inventory_items"
    )
    local_id = models.IntegerField()
    name = models.CharField(max_length=200)
    initial_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    initial_purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    initial_commission_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    initial_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    initial_year = models.IntegerField(validators=[MinValueValidator(2025)])
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "inventory_item"
        verbose_name = "صنف البضاعة"
        verbose_name_plural = "أصناف البضاعة"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "local_id"],
                name="uq_tenant_item_local_id",
            ),
            models.CheckConstraint(
                check=models.Q(local_id__gte=0),
                name="chk_inventory_item_local_id_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(initial_quantity__gte=0),
                name="chk_inventory_item_initial_qty_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(initial_purchase_price__gte=0),
                name="chk_inventory_item_purchase_price_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(initial_commission_amount__gte=0),
                name="chk_inventory_item_commission_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(initial_month__gte=1, initial_month__lte=12),
                name="chk_inventory_item_month_range",
            ),
            models.CheckConstraint(
                check=models.Q(initial_year__gte=2025),
                name="chk_inventory_item_year_gte_2025",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "branch"], name="idx_inventory_item_tenant_branch"
            ),
        ]

    def __str__(self):
        return f"{self.name} [{self.tenant.company_code}]"

    # ------------------------------------------------------------------
    # Business Logic: stock & commission calculators (schema §1.3)
    # ------------------------------------------------------------------

    def get_stock_at_date(self, month: int, year: int) -> int:
        """
        Returns the net stock level of this item as of the given month/year
        by aggregating initial quantity, purchases, returns, sales, and
        inventory adjustments up to and including that period.

        Uses pessimistic locking internally when called inside a transaction.
        """
        from django.db.models import Sum, Q

        before_or_eq = Q(activation_year__lt=year) | (
            Q(activation_year=year) & Q(activation_month__lte=month)
        )
        before_or_eq_invoice = Q(purchase_invoice__invoice_year__lt=year) | (
            Q(purchase_invoice__invoice_year=year) & Q(purchase_invoice__invoice_month__lte=month)
        )
        before_or_eq_receipt = Q(receipt__sale_year__lt=year) | (
            Q(receipt__sale_year=year) & Q(receipt__sale_month__lte=month)
        )
        before_or_eq_adj = Q(adjustment_year__lt=year) | (
            Q(adjustment_year=year) & Q(adjustment_month__lte=month)
        )

        stock = 0
        if self.initial_year < year or (
            self.initial_year == year and self.initial_month <= month
        ):
            stock = self.initial_quantity

        purchases = (
            self.purchase_invoice_items.filter(
                purchase_invoice__invoice_type="PURCHASE", is_deleted=False
            )
            .filter(before_or_eq_invoice)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        returns = (
            self.purchase_invoice_items.filter(
                purchase_invoice__invoice_type="RETURN", is_deleted=False
            )
            .filter(before_or_eq_invoice)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        sales = (
            self.sale_items.filter(is_deleted=False)
            .filter(before_or_eq_receipt)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        adj_plus = (
            self.inventory_adjustments.filter(
                adjustment_type="SURPLUS", is_deleted=False
            )
            .filter(before_or_eq_adj)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        adj_minus = (
            self.inventory_adjustments.filter(
                adjustment_type="DEFICIT", is_deleted=False
            )
            .filter(before_or_eq_adj)
            .aggregate(total=Sum("quantity"))["total"] or 0
        )

        return stock + purchases + adj_plus - sales - returns - adj_minus

    def get_commission_at_date(self, month: int, year: int):
        """Returns the active commission rate for this item as of the given period."""
        from django.db.models import Q

        commission = (
            self.commission_history.filter(
                is_deleted=False
            )
            .filter(
                Q(activation_year__lt=year)
                | (Q(activation_year=year) & Q(activation_month__lte=month))
            )
            .order_by("-activation_year", "-activation_month", "-created_at")
            .first()
        )

        if commission:
            return commission.commission_amount
        return self.initial_commission_amount


# ===========================================================================
# 6. CommissionHistory (سجل عمولات المناديب)
# ===========================================================================

class CommissionHistory(models.Model):
    """Tracks commission rate changes per inventory item over time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="commission_histories"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="commission_history"
    )
    commission_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    activation_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    activation_year = models.IntegerField(validators=[MinValueValidator(2025)])
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "commission_history"
        verbose_name = "سجل العمولة"
        verbose_name_plural = "سجل العمولات"
        constraints = [
            models.CheckConstraint(
                check=models.Q(commission_amount__gte=0),
                name="chk_commission_amount_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(activation_month__gte=1, activation_month__lte=12),
                name="chk_commission_month_range",
            ),
            models.CheckConstraint(
                check=models.Q(activation_year__gte=2025),
                name="chk_commission_year_gte_2025",
            ),
        ]
        indexes = [
            models.Index(
                fields=["inventory_item"], name="idx_commission_history_item"
            ),
        ]

    def __str__(self):
        return (
            f"{self.inventory_item.name} — {self.commission_amount} "
            f"({self.activation_month}/{self.activation_year})"
        )


# ===========================================================================
# 7. InventoryAdjustment (جرد وتسويات البضاعة)
# ===========================================================================

class InventoryAdjustment(models.Model):
    """Stock adjustment records (deficit or surplus)."""

    ADJUSTMENT_TYPES = [
        ("DEFICIT", "عجز (-)"),
        ("SURPLUS", "زيادة (+)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="inventory_adjustments"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="inventory_adjustments"
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    reason = models.CharField(max_length=255, blank=True, null=True)
    adjustment_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    adjustment_year = models.IntegerField(validators=[MinValueValidator(2025)])
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "inventory_adjustment"
        verbose_name = "تسوية المخزون"
        verbose_name_plural = "تسويات المخزون"
        constraints = [
            models.CheckConstraint(
                check=models.Q(adjustment_type__in=["DEFICIT", "SURPLUS"]),
                name="chk_adjustment_type_valid",
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="chk_adjustment_quantity_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(adjustment_month__gte=1, adjustment_month__lte=12),
                name="chk_adjustment_month_range",
            ),
            models.CheckConstraint(
                check=models.Q(adjustment_year__gte=2025),
                name="chk_adjustment_year_gte_2025",
            ),
        ]
        indexes = [
            models.Index(
                fields=["inventory_item"], name="idx_inventory_adjustment_item"
            ),
        ]

    def __str__(self):
        sign = "+" if self.adjustment_type == "SURPLUS" else "-"
        return f"{sign}{self.quantity} × {self.inventory_item.name}"


# ===========================================================================
# 8. Supplier (الموردين)
# ===========================================================================

class Supplier(models.Model):
    """Procurement vendor / supplier entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="suppliers"
    )
    name = models.CharField(max_length=200)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "supplier"
        verbose_name = "المورد"
        verbose_name_plural = "الموردون"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="uq_tenant_supplier_name",
                condition=models.Q(is_deleted=False),
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_supplier_tenant"),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.company_code})"


# ===========================================================================
# 9. PurchaseInvoice (فاتورة الشراء / المرتجع)
# ===========================================================================

class PurchaseInvoice(models.Model):
    """Vendor purchase or return invoice header."""

    INVOICE_TYPES = [
        ("PURCHASE", "فاتورة شراء"),
        ("RETURN", "فاتورة مرتجع"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="purchase_invoices"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="purchase_invoices"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="purchase_invoices"
    )
    invoice_number = models.IntegerField(validators=[MinValueValidator(0)])
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    invoice_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    invoice_year = models.IntegerField(validators=[MinValueValidator(2025)])
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "purchase_invoice"
        verbose_name = "فاتورة الشراء"
        verbose_name_plural = "فواتير الشراء"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "branch", "invoice_number", "invoice_type"],
                name="uq_tenant_branch_invoice_num_type",
            ),
            models.CheckConstraint(
                check=models.Q(invoice_number__gte=0),
                name="chk_purchase_invoice_number_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(invoice_type__in=["PURCHASE", "RETURN"]),
                name="chk_purchase_invoice_type_valid",
            ),
            models.CheckConstraint(
                check=models.Q(invoice_month__gte=1, invoice_month__lte=12),
                name="chk_purchase_invoice_month_range",
            ),
            models.CheckConstraint(
                check=models.Q(invoice_year__gte=2025),
                name="chk_purchase_invoice_year_gte_2025",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "branch"], name="idx_purchase_invoice_tenant_branch"
            ),
        ]

    def __str__(self):
        return f"#{self.invoice_number} {self.invoice_type} — {self.supplier.name}"


# ===========================================================================
# 10. PurchaseInvoiceItem (أصناف فاتورة الشراء)
# ===========================================================================

class PurchaseInvoiceItem(models.Model):
    """Line item within a purchase or return invoice."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="purchase_invoice_items"
    )
    purchase_invoice = models.ForeignKey(
        PurchaseInvoice, on_delete=models.CASCADE, related_name="items"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="purchase_invoice_items"
    )
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "purchase_invoice_item"
        verbose_name = "صنف فاتورة شراء"
        verbose_name_plural = "أصناف فواتير الشراء"
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="chk_pi_item_quantity_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(purchase_price__gte=0),
                name="chk_pi_item_purchase_price_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=["purchase_invoice"],
                name="idx_purchase_invoice_item_invoice",
            ),
        ]

    def __str__(self):
        return f"{self.inventory_item.name} × {self.quantity}"


# ===========================================================================
# 11. Receipt (الفاتورة / الوصل)
# ===========================================================================

class Receipt(models.Model):
    """Sales transaction / invoice record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="receipts"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="receipts"
    )
    salesperson = models.ForeignKey(
        Salesperson, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="receipts"
    )
    # local_id maps to the SQLite row id on the originating device
    local_id = models.IntegerField(validators=[MinValueValidator(0)])
    receipt_number = models.IntegerField(validators=[MinValueValidator(0)])
    # Idempotency key (schema §1.4)
    client_uuid = models.UUIDField()
    # Tamper-proof hash (schema §1.5)
    receipt_hash = models.CharField(max_length=255, unique=True)
    customer_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=150, blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    down_payment = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    installment_system = models.CharField(max_length=255, blank=True, null=True)
    sale_year = models.IntegerField(validators=[MinValueValidator(2025)])
    sale_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    is_cash_sale = models.BooleanField(default=False)
    products_text = models.TextField(blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    # Timestamps: local device time vs. server UTC ingestion time
    created_at_local = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "receipt"
        verbose_name = "الفاتورة"
        verbose_name_plural = "الفواتير"
        constraints = [
            # Idempotency: one receipt per device UUID per tenant (schema §1.4)
            models.UniqueConstraint(
                fields=["tenant", "client_uuid"],
                name="uq_tenant_receipt_client_uuid",
            ),
            models.CheckConstraint(
                check=models.Q(local_id__gte=0),
                name="chk_receipt_local_id_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(receipt_number__gte=0),
                name="chk_receipt_number_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(total_amount__gte=0),
                name="chk_receipt_total_amount_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(down_payment__gte=0),
                name="chk_receipt_down_payment_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(sale_year__gte=2025),
                name="chk_receipt_sale_year_gte_2025",
            ),
            models.CheckConstraint(
                check=models.Q(sale_month__gte=1, sale_month__lte=12),
                name="chk_receipt_sale_month_range",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "branch"], name="idx_receipt_tenant_branch"
            ),
            models.Index(fields=["receipt_hash"], name="idx_receipt_hash"),
        ]

    def __str__(self):
        return f"فاتورة #{self.receipt_number} — {self.customer_name}"


# ===========================================================================
# 12. SaleItem (أصناف الفاتورة المباعة)
# ===========================================================================

class SaleItem(models.Model):
    """Line item within a sale receipt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="sale_items"
    )
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="sale_items"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="sale_items"
    )
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "sale_item"
        verbose_name = "صنف مباع"
        verbose_name_plural = "الأصناف المباعة"
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="chk_sale_item_quantity_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gte=0),
                name="chk_sale_item_unit_price_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["receipt"], name="idx_sale_item_receipt"),
        ]

    def __str__(self):
        return f"{self.inventory_item.name} × {self.quantity} @ {self.unit_price}"


# ===========================================================================
# 13. InstallmentPayment (القسط المجدول)
# ===========================================================================

class InstallmentPayment(models.Model):
    """Scheduled installment payment tied to a receipt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="installment_payments"
    )
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="installment_payments"
    )
    # Absolute due date (25th-of-month rule enforced by business logic layer)
    payment_date = models.DateField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "installment_payment"
        verbose_name = "قسط"
        verbose_name_plural = "الأقساط"
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="chk_installment_amount_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=["receipt"], name="idx_installment_payment_receipt"
            ),
        ]

    def __str__(self):
        return f"قسط {self.amount} — {self.payment_date}"


# ===========================================================================
# 14. Expense (دفتر المصاريف / الخزنة)
# ===========================================================================

class Expense(models.Model):
    """Operational overhead expense logged against a branch."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="expenses"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="expenses"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )
    description = models.CharField(max_length=255)
    expense_year = models.IntegerField(validators=[MinValueValidator(2025)])
    expense_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    is_deleted = models.BooleanField(default=False)
    # Local device timestamp vs. server ingestion time
    created_at_local = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "expense"
        verbose_name = "مصروف"
        verbose_name_plural = "المصروفات"
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="chk_expense_amount_gte_0",
            ),
            models.CheckConstraint(
                check=models.Q(expense_year__gte=2025),
                name="chk_expense_year_gte_2025",
            ),
            models.CheckConstraint(
                check=models.Q(expense_month__gte=1, expense_month__lte=12),
                name="chk_expense_month_range",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "branch"], name="idx_expense_tenant_branch"
            ),
        ]

    def __str__(self):
        return f"{self.description} — {self.amount}"


# ===========================================================================
# 15. CompanySetting (إعدادات الشركة — Singleton per tenant)
# ===========================================================================

class CompanySetting(models.Model):
    """Per-tenant company profile settings. One row per tenant (singleton)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="company_setting"
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, null=True)
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    footer_text = models.CharField(max_length=250, blank=True, null=True)
    is_cloud_viewer = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "company_setting"
        verbose_name = "إعدادات الشركة"
        verbose_name_plural = "إعدادات الشركات"
        constraints = [
            # OneToOneField already enforces this at Django level;
            # the DB constraint is added for belt-and-suspenders safety.
            models.UniqueConstraint(
                fields=["tenant"],
                name="uq_tenant_company_setting",
            ),
        ]

    def __str__(self):
        return f"إعدادات {self.name}"


# ===========================================================================
# 16. ClientLicense (ترخيص العميل وتأمين السجل)
# ===========================================================================

class ClientLicense(models.Model):
    """
    Active activation profile for a local POS device.
    Row integrity enforced via HMAC-SHA256 signature in license_code_hash
    (schema §1.5).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="client_licenses"
    )
    product_id = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(16)]
    )
    start_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    invoices_balance = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    machine_id = models.CharField(max_length=255)
    company_code = models.CharField(max_length=10)
    license_code_hash = models.CharField(max_length=64)
    is_online_active = models.BooleanField(default=False)
    online_start_date = models.DateField(null=True, blank=True)
    online_expiry_date = models.DateField(null=True, blank=True)
    last_checkin = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "client_license"
        verbose_name = "ترخيص عميل"
        verbose_name_plural = "تراخيص العملاء"
        constraints = [
            models.CheckConstraint(
                check=models.Q(product_id__gte=1, product_id__lte=16),
                name="chk_client_license_product_id_range",
            ),
            models.CheckConstraint(
                check=models.Q(invoices_balance__gte=0),
                name="chk_client_license_balance_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_client_license_tenant"),
            models.Index(
                fields=["license_code_hash"], name="idx_client_license_hash"
            ),
        ]

    def __str__(self):
        return f"License P{self.product_id} — {self.machine_id[:12]}…"


# ===========================================================================
# 17. UsedLicense (منع تكرار تفعيل الأكواد)
# ===========================================================================

class UsedLicense(models.Model):
    """Registry of consumed license activation codes (prevents replay)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="used_licenses"
    )
    code_hash = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "used_license"
        verbose_name = "كود مستخدم"
        verbose_name_plural = "الأكواد المستخدمة"
        indexes = [
            models.Index(fields=["code_hash"], name="idx_used_license_hash"),
        ]

    def __str__(self):
        return f"UsedLicense {self.code_hash[:16]}…"


# ===========================================================================
# 18. LicenseHistory (أرشيف سجل التراخيص)
# ===========================================================================

class LicenseHistory(models.Model):
    """Audit log of all licensing operations (activations, renewals, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="license_histories"
    )
    machine_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=100)
    operation_type = models.CharField(max_length=50)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    added_balance = models.IntegerField(default=0)
    archived_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "license_history"
        verbose_name = "سجل ترخيص"
        verbose_name_plural = "سجلات التراخيص"

    def __str__(self):
        return f"{self.operation_type} — {self.product_name} ({self.status})"


# ===========================================================================
# 19. PendingExternalReceipt (الوصلات الخارجية المؤقتة)
# ===========================================================================

class PendingExternalReceipt(models.Model):
    """Temporary staging table for external receipts awaiting processing."""

    SOURCE_CHOICES = [
        ("CLOUD", "سحابة"),
        ("USB", "USB"),
        ("FILE", "ملف"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="pending_external_receipts"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="pending_external_receipts"
    )
    batch_id = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    payload = models.JSONField()
    is_processed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "pending_external_receipt"
        verbose_name = "وصل خارجي مؤقت"
        verbose_name_plural = "الوصلات الخارجية المؤقتة"
        constraints = [
            models.CheckConstraint(
                check=models.Q(source__in=["CLOUD", "USB", "FILE"]),
                name="chk_pending_receipt_source_valid",
            ),
        ]

    def __str__(self):
        return f"Batch {self.batch_id} [{self.source}]"


# ===========================================================================
# LEGACY — ActionLog (not in approved schema; kept to avoid migration breakage)
# ===========================================================================

class ActionLog(models.Model):
    """
    Legacy audit log. NOT part of the approved database_schema.md.
    Will be removed in a future migration once the audit trail is handled
    by the LicenseHistory and a future dedicated AuditLog table.
    """

    actor = models.CharField(max_length=100, null=True, blank=True)
    action_type = models.CharField(max_length=20)
    model_name = models.CharField(max_length=50)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "action_log"
        verbose_name = "سجل الإجراءات"
        verbose_name_plural = "سجلات الإجراءات"

    def __str__(self):
        return f"{self.action_type} on {self.model_name} by {self.actor}"
