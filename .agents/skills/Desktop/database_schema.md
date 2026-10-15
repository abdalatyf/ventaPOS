# Venta POS Database Schema Documentation

This document provides an exhaustively detailed breakdown of the database schema for the Venta POS Django application. It covers every table (model), column, data type, foreign key relationship, custom manager logic, overriden methods, and signals based on `models.py` and `signals.py` in `salesapp`.

---

## 1. SyncDeletionLog

Tracks deleted records for synchronization purposes.

**Columns:**
* `id`: Auto-generated primary key.
* `table_name`: `models.CharField(max_length=50, choices=MODEL_CHOICES)`
  * **Choices:** `('Receipt', 'Receipt')`, `('InventoryItem', 'InventoryItem')`, `('Salesperson', 'Salesperson')`, `('Expense', 'Expense')`, `('StockTransaction', 'StockTransaction')`
* `record_id`: `models.IntegerField(verbose_name="ID العنصر المحذوف")` - The ID of the deleted record.
* `timestamp`: `models.DateTimeField(auto_now_add=True)` - Automatically set to the current time when created.

**Overrides & Logic:**
* `__str__(self)`: Returns `f"Delete {self.table_name} #{self.record_id}"`

---

## 2. ActionLog

Logs various actions performed in the system for auditing purposes.

**Columns:**
* `id`: Auto-generated primary key.
* `actor`: `models.CharField(max_length=100, verbose_name="القائم بالعملية", null=True, blank=True)`
* `action_type`: `models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="نوع العملية")`
  * **Choices:** `('CREATE', 'إضافة جديد')`, `('UPDATE', 'تعديل بيانات')`, `('DELETE', 'حذف')`, `('SYNC', 'مزامنة بيانات')`, `('LOGIN', 'تسجيل دخول')`
* `model_name`: `models.CharField(max_length=50, verbose_name="القسم")`
* `details`: `models.TextField(verbose_name="التفاصيل", blank=True, null=True)`
* `timestamp`: `models.DateTimeField(auto_now_add=True)`

**Meta:**
* `ordering = ['-timestamp']`
* `verbose_name = "سجل النشاطات"`

**Overrides & Logic:**
* `__str__(self)`: Returns `f"{self.action_type} - {self.model_name}"`

---

## 3. Branch

Represents a company branch or store location.

**Columns:**
* `id`: Auto-generated primary key.
* `name`: `models.CharField(max_length=100, unique=True, verbose_name="اسم الفرع")`
* `is_synced`: `models.BooleanField(default=False)` - Flag to indicate synchronization status.

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before calling `super().save(*args, **kwargs)`.
* `__str__(self)`: Returns `self.name`

---

## 4. Salesperson

Represents an employee/salesperson.

**Columns:**
* `id`: Auto-generated primary key.
* `name`: `models.CharField(max_length=100, verbose_name="اسم الموظف")`
* `branch`: `models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع التابع له")`
* `is_synced`: `models.BooleanField(default=False)`

**Meta:**
* `unique_together = ('name', 'branch')`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before calling `super().save(*args, **kwargs)`.
* `__str__(self)`: Returns `f"{self.name} ({self.branch.name})"`

---

## 5. InventoryItem

The core product model managing historical pricing, commissions, and stock calculation logic.

**Columns:**
* `id`: Auto-generated primary key.
* `name`: `models.CharField(max_length=200, verbose_name="اسم الصنف")`
* `branch`: `models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="مخزن الفرع")`
* `initial_quantity`: `models.PositiveIntegerField(default=0, verbose_name="الكمية الافتتاحية")`
* `initial_purchase_price`: `models.PositiveIntegerField(default=0, verbose_name="سعر الشراء الافتتاحي")`
* `initial_commission_amount`: `models.PositiveIntegerField(default=0, verbose_name="المندبة الابتدائية")`
* `initial_month`: `models.PositiveIntegerField(verbose_name="شهر البداية", default=1)`
* `initial_year`: `models.PositiveIntegerField(verbose_name="سنة البداية", default=2026)`
* `created_at`: `models.DateTimeField(auto_now_add=True)`
* `updated_at`: `models.DateTimeField(auto_now=True)`
* `is_synced`: `models.BooleanField(default=False)`

**Meta:**
* `unique_together = [('name', 'branch')]`
* `ordering = ['name']`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before saving.
* `__str__(self)`: Returns `f"{self.name} - {self.branch.name}"`

**Custom Methods:**
* `get_stock_at_date(self, month, year)`:
  Calculates the exact stock amount for a given point in time.
  1. Validates the given date against `initial_month` and `initial_year`. Returns 0 if prior to initialization.
  2. Calculates `total_purchased` from `purchaseinvoiceitem_set` where invoice is `PURCHASE` type up to the specified date.
  3. Calculates `total_returned` from `purchaseinvoiceitem_set` where invoice is `RETURN` type up to the specified date.
  4. Calculates `total_sold` from `saleitem_set` up to the specified date.
  5. Calculates `total_deficit` and `total_surplus` from `adjustments` relation up to the specified date.
  6. Returns `max(0, (initial_quantity + total_purchased + total_surplus) - (total_sold + total_returned + total_deficit))`
* `get_price_at_date(self, month, year)`:
  Finds the most recent `purchase_price` from `PURCHASE` invoices prior to or during the specified month and year. If none exist, returns `self.initial_purchase_price`.
* `get_commission_at_date(self, month, year)`:
  Finds the most recent `commission_amount` from `commission_records` (CommissionHistory) prior to or during the specified month and year. If none exist, returns `self.initial_commission_amount`.

---

## 6. CommissionHistory

Tracks historical changes to salesperson commissions for specific items.

**Columns:**
* `id`: Auto-generated primary key.
* `item`: `models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='commission_records', verbose_name="المنتج")`
* `commission_amount`: `models.PositiveIntegerField(verbose_name="المندبة الجديدة")`
* `activation_month`: `models.PositiveIntegerField(verbose_name="شهر التفعيل")`
* `activation_year`: `models.PositiveIntegerField(verbose_name="سنة التفعيل")`
* `created_at`: `models.DateTimeField(auto_now_add=True)`

**Meta:**
* `ordering = ['-activation_year', '-activation_month']`
* `unique_together = ('item', 'activation_month', 'activation_year')`

**Overrides & Logic:**
* `__str__(self)`: Returns `f"تحديث مندبة {self.item.name} - {self.activation_month}/{self.activation_year}"`

---

## 7. InventoryAdjustment

Logs manual stock adjustments (deficit or surplus).

**Columns:**
* `id`: Auto-generated primary key.
* `item`: `models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='adjustments', verbose_name="المنتج")`
* `adjustment_type`: `models.CharField(max_length=10, choices=ADJUSTMENT_TYPES, verbose_name="نوع التسوية")`
  * **Choices:** `('DEFICIT', 'عجز (-)')`, `('SURPLUS', 'زيادة (+)')`
* `quantity`: `models.PositiveIntegerField(verbose_name="الكمية")`
* `reason`: `models.CharField(max_length=255, blank=True, null=True, verbose_name="السبب / ملاحظات")`
* `month`: `models.PositiveIntegerField(verbose_name="شهر التسوية")`
* `year`: `models.PositiveIntegerField(verbose_name="سنة التسوية")`
* `created_at`: `models.DateTimeField(auto_now_add=True)`

**Meta:**
* `ordering = ['-year', '-month', '-id']`

**Overrides & Logic:**
* `__str__(self)`: Generates string showing if it's a positive or negative adjustment. Example: `f"تسوية {self.item.name} (+5) - 6/2026"`

---

## 8. Supplier

Suppliers or factories providing inventory.

**Columns:**
* `id`: Auto-generated primary key.
* `name`: `models.CharField(max_length=200, unique=True, verbose_name="اسم المورد / المصنع")`
* `is_synced`: `models.BooleanField(default=False)`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before saving.
* `__str__(self)`: Returns `self.name`

---

## 9. PurchaseInvoice

Tracks purchase orders and manufacturer returns.

**Columns:**
* `id`: Auto-generated primary key.
* `branch`: `models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع")`
* `invoice_number`: `models.PositiveIntegerField(unique=True, verbose_name="رقم الفاتورة")`
* `supplier`: `models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name="المورد")`
* `invoice_type`: `models.CharField(max_length=20, choices=INVOICE_TYPES, default='PURCHASE', verbose_name="نوع الفاتورة")`
  * **Choices:** `('PURCHASE', 'فاتورة شراء (إضافة للمخزن)')`, `('RETURN', 'فاتورة مرتجع (خصم من المخزن)')`
* `invoice_month`: `models.PositiveIntegerField(verbose_name="شهر الفاتورة", db_index=True)`
* `invoice_year`: `models.PositiveIntegerField(verbose_name="سنة الفاتورة", db_index=True)`
* `created_at`: `models.DateTimeField(auto_now_add=True)`
* `is_synced`: `models.BooleanField(default=False)`

**Meta:**
* `unique_together = ('branch', 'invoice_number', 'supplier')`
* `ordering = ['-invoice_year', '-invoice_month', '-id']`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before saving.
* `__str__(self)`: Returns `f"{type_name} {self.invoice_number} - {self.supplier.name}"`

---

## 10. PurchaseInvoiceItem

Individual items tied to a PurchaseInvoice.

**Columns:**
* `id`: Auto-generated primary key.
* `invoice`: `models.ForeignKey(PurchaseInvoice, related_name='items', on_delete=models.CASCADE)`
* `inventory_item`: `models.ForeignKey(InventoryItem, on_delete=models.PROTECT, verbose_name="الصنف")`
* `quantity`: `models.PositiveIntegerField(default=1, verbose_name="الكمية")`
* `purchase_price`: `models.PositiveIntegerField(verbose_name="السعر بالفاتورة", null=True, blank=True, default=0)`
* `is_synced`: `models.BooleanField(default=False)`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before saving.
* `__str__(self)`: Returns the string cast of the parent invoice number.

---

## 11. Receipt

The core entity tracking a customer sale/receipt.

**Columns:**
* `id`: Auto-generated primary key.
* `source`: `models.CharField(max_length=20, choices=SOURCE_CHOICES, default='DESKTOP', verbose_name="المصدر")`
  * **Choices:** `('DESKTOP', 'الكمبيوتر الرئيسي')`, `('MOBILE', 'تطبيق المندوب')`
* `receipt_number`: `models.PositiveIntegerField(verbose_name="رقم الوصل", db_index=True)`
* `branch`: `models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع", db_index=True)`
* `customer_name`: `models.CharField(max_length=150, verbose_name="اسم العميل", blank=True, db_index=True)`
* `products_text`: `models.TextField(verbose_name="نص المنتجات (للطباعة)", blank=True, null=True)`
* `phone_number`: `models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف", db_index=True)`
* `address`: `models.CharField(max_length=255, blank=True, verbose_name="العنوان")`
* `area`: `models.CharField(max_length=100, blank=True, verbose_name="المنطقة", db_index=True)`
* `total_amount`: `models.PositiveIntegerField(default=0, verbose_name="الإجمالي")`
* `down_payment`: `models.PositiveIntegerField(default=0, verbose_name="المقدم")`
* `installment_system`: `models.CharField(max_length=200, blank=True, verbose_name="وصف نظام القسط")`
* `salesperson`: `models.ForeignKey(Salesperson, on_delete=models.PROTECT, null=True, blank=True, verbose_name="المندوب")`
* `sale_year`: `models.PositiveIntegerField(verbose_name="سنة البيع", db_index=True)`
* `sale_month`: `models.PositiveIntegerField(verbose_name="شهر البيع", db_index=True)`
* `is_cash_sale`: `models.BooleanField(default=False, verbose_name="بيع كاش؟")`
* `receipt_hash`: `models.CharField(max_length=64, blank=True, null=True, verbose_name="بصمة الفاتورة")`
* `created_at`: `models.DateTimeField(auto_now_add=True)`
* `updated_at`: `models.DateTimeField(auto_now=True)`
* `is_synced`: `models.BooleanField(default=False)`

**Custom Manager (`ValidReceiptManager`):**
* `objects = ValidReceiptManager()`
* Overrides `get_queryset()`:
  1. Excludes receipts missing a `receipt_hash` (`isnull=True` or exact `''`).
  2. Fetches the active `ClientLicense` (where `is_active=True`, `product_id < 10`).
  3. If a license with an `expiry_date` exists, filters out "future" invoices by restricting the queryset to `sale_year < exp_year` OR (`sale_year == exp_year` AND `sale_month <= exp_month`).

**Meta:**
* `unique_together = ('branch', 'receipt_number')`
* `ordering = ['-receipt_number']`

**Overrides, Properties & Logic:**
* `@property is_authentic`: Verifies if the stored `receipt_hash` matches a dynamically generated hash (`generate_receipt_signature`) using `receipt_number`, `total_amount`, `sale_month`, and `sale_year`.
* `@classmethod get_next_receipt_number(cls, branch)`: Fetches the maximum `receipt_number` for the given branch and returns `max + 1`. Defaults to 1.
* `save(self, *args, **kwargs)`:
  * Detects if it's a new instance (`self.pk is None`).
  * If new, it consumes an invoice balance from the `ClientLicense`:
    * First tries to find a base license (`product_id < 10`, `invoices_balance > 0`). If found, decrements `invoices_balance` by 1 and saves.
    * If no base license has balance, searches for a recharge code license (`product_id >= 10`, `invoices_balance > 0`). If found, decrements `invoices_balance` by 1 and saves.
  * Regenerates `receipt_hash` via `generate_receipt_signature`.
  * Sets `self.is_synced = False`.
  * Calls `super().save`.
* `__str__(self)`: Returns `f"[{self.source}] - {self.receipt_number} - {self.customer_name}"`

---

## 12. SaleItem

Individual items associated with a Receipt.

**Columns:**
* `id`: Auto-generated primary key.
* `receipt`: `models.ForeignKey(Receipt, related_name='items', on_delete=models.CASCADE, verbose_name="الوصل التابع له")`
* `inventory_item`: `models.ForeignKey(InventoryItem, on_delete=models.PROTECT, verbose_name="الصنف")`
* `quantity`: `models.PositiveIntegerField(default=1, verbose_name="الكمية")`
* `unit_price`: `models.PositiveIntegerField(verbose_name="سعر الوحدة")`

**Overrides & Logic:**
* `__str__(self)`: Returns `f"{self.quantity} x {self.inventory_item.name}"`

---

## 13. InstallmentPayment

Tracks installment plans attached to a Receipt.

**Columns:**
* `id`: Auto-generated primary key.
* `receipt`: `models.ForeignKey(Receipt, related_name='payments', on_delete=models.CASCADE, verbose_name="الوصل التابع له")`
* `payment_date`: `models.DateField(verbose_name="تاريخ الدفعة المستحقة")`
* `amount`: `models.PositiveIntegerField(verbose_name="المبلغ")`

**Overrides & Logic:**
* `__str__(self)`: Returns `f"قسط {self.amount} - تاريخ {self.payment_date}"`

---

## 14. Expense

Company expenses.

**Columns:**
* `id`: Auto-generated primary key.
* `branch`: `models.ForeignKey(Branch, on_delete=models.CASCADE)`
* `amount`: `models.DecimalField(max_digits=10, decimal_places=2)`
* `description`: `models.CharField(max_length=255)`
* `expense_year`: `models.IntegerField()`
* `expense_month`: `models.IntegerField()`
* `created_at`: `models.DateTimeField(auto_now_add=True)`
* `is_synced`: `models.BooleanField(default=False)`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Resets `self.is_synced = False` before saving.
* `__str__(self)`: Returns `f"{self.description} ({self.amount})"`

---

## 15. CompanySetting

Global company configuration using a Singleton pattern logic.

**Columns:**
* `id`: Auto-generated primary key.
* `name`: `models.CharField(max_length=100, verbose_name="اسم الشركة")`
* `description`: `models.CharField(max_length=200, blank=True, null=True, verbose_name="وصف الشركة")`
* `phone1`: `models.CharField(max_length=20, verbose_name="رقم تليفون 1")`
* `phone2`: `models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم تليفون 2")`
* `footer_text`: `models.CharField(max_length=250, default="تطبق الشروط والأحكام", verbose_name="الفوتر")`

**Overrides & Logic:**
* `save(self, *args, **kwargs)`: Ensures only one row exists. If saving a new instance and one already exists, delegates the save call to the first existing object.
* `__str__(self)`: Returns `self.name`

---

## 16. UsedLicense

Tracks previously used license codes to prevent replay attacks.

**Columns:**
* `id`: Auto-generated primary key.
* `code_hash`: `models.CharField(max_length=64, unique=True, verbose_name="بصمة الكود")`
* `used_at`: `models.DateTimeField(auto_now_add=True)`

**Overrides & Logic:**
* `__str__(self)`: Returns `self.code_hash`

---

## 17. ClientLicense

Manages local desktop software licensing, invoicing balances, and VIP status.

**Columns:**
* `id`: Auto-generated primary key.
* `product_id`: `models.IntegerField(choices=PRODUCT_CHOICES, default=1, verbose_name="نوع الباقة")`
  * **Choices:** IDs 1 to 16 representing different license types (trials, lifetime, 1-year, invoice top-up codes, emergency codes).
* `start_date`: `models.DateField(null=True, blank=True, verbose_name="تاريخ التفعيل")`
* `expiry_date`: `models.DateField(null=True, blank=True, verbose_name="تاريخ الانتهاء")`
* `invoices_balance`: `models.PositiveIntegerField(default=0, verbose_name="رصيد الفواتير")`
* `is_active`: `models.BooleanField(default=True, verbose_name="حالة الكود")`
* `machine_id`: `models.CharField(max_length=255, null=True, blank=True, verbose_name="الجهاز")`
* `license_code_hash`: `models.CharField(max_length=64, null=True, blank=True, verbose_name="توقيع الكود")`
* `last_checkin`: `models.DateTimeField(auto_now=True, verbose_name="آخر نشاط")`
* `is_online_active`: `models.BooleanField(default=False, verbose_name="يدعم الأونلاين")`
* `online_start_date`: `models.DateField(null=True, blank=True, verbose_name="بداية الأونلاين")`
* `online_expiry_date`: `models.DateField(null=True, blank=True, verbose_name="انتهاء الأونلاين")`
* `created_at`: `models.DateTimeField(auto_now_add=True)`

**Properties & Methods:**
* `@property is_expired`:
  * Returns `False` instantly if `product_id` is 3, 7 (lifetime) or >= 10 (recharge codes).
  * If `expiry_date` is `None`: returns `False` if instance is unsaved (`pk is None`), else returns `True`.
  * Returns `True` if `timezone.now().date() > self.expiry_date`.
* `@classmethod get_active_license(cls)`:
  Returns a dynamically generated (merged) unsaved `ClientLicense` instance summing up the privileges of all valid, active licenses in the database.
  1. Finds `valid_licenses` (where `expiry_date >= today` OR `isnull`, AND `is_active=True`). Returns `None` if zero exist.
  2. Aggregates combined earliest `start_date`, maximum `expiry_date`, and total summed `invoices_balance`.
  3. Identifies the strongest active subscription product (`best_product`).
  4. Checks for active online subscriptions to determine boolean flags and max online expiry.
  5. Returns a virtual `ClientLicense` object encapsulating these merged attributes.
* `save(self, *args, **kwargs)`:
  * Generates `machine_id` via `get_machine_id()` if empty.
  * Secures the record by updating `license_code_hash` using `generate_record_signature` with arguments: `expiry_date`, `invoices_balance`, `machine_id`, `product_id`, `is_active`.
  * Calls `super().save`.
* `__str__(self)`: Returns `f"License {self.pk} - Product {self.product_id}"`

---

## 18. LicenseHistory

Archives historical licensing operations.

**Columns:**
* `id`: Auto-generated primary key.
* `machine_id`: `models.CharField(max_length=100)`
* `product_name`: `models.CharField(max_length=100)`
* `operation_type`: `models.CharField(max_length=50, default="تجديد/تفعيل", verbose_name="نوع العملية")`
* `start_date`: `models.DateField(null=True, blank=True)`
* `end_date`: `models.DateField(null=True, blank=True)`
* `added_balance`: `models.IntegerField(default=0, verbose_name="الرصيد المضاف")`
* `archived_at`: `models.DateTimeField(auto_now_add=True, verbose_name="تاريخ العملية")`
* `status`: `models.CharField(max_length=50, default="أرشيف")`

**Overrides & Logic:**
* `__str__(self)`: Returns `f"{self.operation_type} - {self.product_name}"`

---

## Django Signals (`signals.py`)

A post-delete receiver is utilized to hook into object deletion across several models to support database synchronization.

* **Trigger:** `post_delete` signal.
* **Senders:** `Receipt`, `InventoryItem`, `Salesperson`, `Expense`.
* **Receiver Function:** `log_deletion(sender, instance, **kwargs)`
* **Logic:** When an object of these models is deleted, it automatically instantiates and saves a `SyncDeletionLog` record. It captures `sender.__name__` as the `table_name` and `instance.id` as the `record_id`.
