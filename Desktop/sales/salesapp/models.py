import datetime
import uuid
from django.db import models
from django.db.models import Max, Min, Sum, Q
from django.utils import timezone


class ValidReceiptManager(models.Manager):
    def get_queryset(self):
        # 1. استبعاد أولي لأي فاتورة ملهاش بصمة (تمت إضافتها يدوياً وتُركت فارغة)
        qs = super().get_queryset().exclude(receipt_hash__isnull=True).exclude(receipt_hash__exact='')
        
        # 2. فلتر الزمن الشهري (استبعاد فواتير المستقبل الوهمية)
        try:
            from .models import ClientLicense
            # جلب رخصة الزمن الحالية (اللي فيها تاريخ انتهاء)
            active_lic = ClientLicense.objects.filter(is_active=True, product_id__lt=10).order_by('-id').first()
            
            if active_lic and active_lic.expiry_date:
                exp_year = active_lic.expiry_date.year
                exp_month = active_lic.expiry_date.month
                
                # السماح فقط للفواتير اللي سنتها أقل، أو (نفس السنة وشهرها أقل أو يساوي)
                qs = qs.filter(
                    Q(sale_year__lt=exp_year) | 
                    Q(sale_year=exp_year, sale_month__lte=exp_month)
                )
        except Exception:
            pass
            
        return qs

# ==========================================================
# 0. نظام تتبع المحذوفات (للمزامنة) 🗑️
# ==========================================================
class SyncDeletionLog(models.Model):
    MODEL_CHOICES = (
        ('Receipt', 'Receipt'),
        ('InventoryItem', 'InventoryItem'),
        ('Salesperson', 'Salesperson'),
        ('Expense', 'Expense'),
        ('StockTransaction', 'StockTransaction'),
    )
    table_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    record_id = models.IntegerField(verbose_name="ID العنصر المحذوف")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delete {self.table_name} #{self.record_id}"

# ==========================================================
# 1. سجل النشاطات (Action Log) 📝
# ==========================================================
class ActionLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'إضافة جديد'),
        ('UPDATE', 'تعديل بيانات'),
        ('DELETE', 'حذف'),
        ('SYNC', 'مزامنة بيانات'),
        ('LOGIN', 'تسجيل دخول'),
    )
    
    actor = models.CharField(max_length=100, verbose_name="القائم بالعملية", null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="نوع العملية")
    model_name = models.CharField(max_length=50, verbose_name="القسم")
    details = models.TextField(verbose_name="التفاصيل", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "سجل النشاطات"

    def __str__(self):
        return f"{self.action_type} - {self.model_name}"


# ==========================================================
# 2. النماذج الأساسية (الإعدادات)
# ==========================================================

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الفرع")
    is_synced = models.BooleanField(default=False)  # 🔄

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)
    
    def __str__(self): 
        return self.name

class Salesperson(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الموظف")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع التابع له")
    is_synced = models.BooleanField(default=False)  # 🔄

    device_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True, verbose_name="توكن الجهاز")
    is_device_active = models.BooleanField(default=False, verbose_name="الجهاز مفعل؟")
    
    cloud_username = models.CharField(max_length=150, null=True, blank=True, verbose_name="اسم المستخدم السحابي")
    cloud_password = models.CharField(max_length=128, null=True, blank=True, verbose_name="كلمة المرور السحابية")

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ('name', 'branch')

    def __str__(self): 
        return f"{self.name} ({self.branch.name})"


class CloudUser(models.Model):
    """مستخدم سحابي للأجهزة الفرعية (Viewer PCs)"""
    username = models.CharField(max_length=150, unique=True, verbose_name="اسم المستخدم")
    password = models.CharField(max_length=255, verbose_name="كلمة المرور")
    role = models.CharField(max_length=50, default='VIEWER', choices=[('VIEWER', 'مشاهد'), ('CASHIER', 'كاشير فرعي')], verbose_name="الصلاحية")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    is_synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


# ==========================================================
# 🔴 التحديث الجذري للمخزن: 3. المنتجات وسجل العمولات والتسويات
# ==========================================================
class InventoryItem(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم الصنف")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="مخزن الفرع")
    
    # --- بيانات أول المدة (The Opening Balance) ---
    initial_quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية الافتتاحية")
    initial_purchase_price = models.PositiveIntegerField(default=0, verbose_name="سعر الشراء الافتتاحي")
    initial_commission_amount = models.PositiveIntegerField(default=0, verbose_name="المندبة الابتدائية")
    
    # تواريخ البداية (عشان آلة الزمن)
    initial_month = models.PositiveIntegerField(verbose_name="شهر البداية", default=1)
    initial_year = models.PositiveIntegerField(verbose_name="سنة البداية", default=2026)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_synced = models.BooleanField(default=False)

    # 1. دالة حساب الرصيد لأي تاريخ (آلة الزمن)
    def get_stock_at_date(self, month, year):
        # 1. التأكد من تاريخ البداية
        if year < self.initial_year or (year == self.initial_year and month < self.initial_month):
            return 0

        # 2. الوارد (مشتريات) - من الفواتير مباشرة لتطابق التواريخ المنطقية
        total_purchased = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='PURCHASE'
        ).filter(
            Q(invoice__invoice_year__lt=year) | 
            Q(invoice__invoice_year=year, invoice__invoice_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # 3. المنصرف (مرتجع مصنع) - من الفواتير مباشرة
        total_returned = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='RETURN'
        ).filter(
            Q(invoice__invoice_year__lt=year) | 
            Q(invoice__invoice_year=year, invoice__invoice_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # 4. المبيعات (كما هي من الوصلات المنطقية)
        total_sold = self.saleitem_set.filter(
            Q(receipt__sale_year__lt=year) | 
            Q(receipt__sale_year=year, receipt__sale_month__lte=month)
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # 5. التسويات (عجز وزيادة - بالتواريخ المنطقية)
        adjustments = self.adjustments.filter(
            Q(year__lt=year) | 
            Q(year=year, month__lte=month)
        )
        total_deficit = adjustments.filter(adjustment_type='DEFICIT').aggregate(total=Sum('quantity'))['total'] or 0
        total_surplus = adjustments.filter(adjustment_type='SURPLUS').aggregate(total=Sum('quantity'))['total'] or 0

        # 6. المعادلة النهائية
        final_stock = (self.initial_quantity + total_purchased + total_surplus) - (total_sold + total_returned + total_deficit)
        return max(0, final_stock)
    # 2. محرك البحث عن "سعر الشراء" في تاريخ معين
    def get_price_at_date(self, month, year):
        """تأتي بأحدث سعر شراء تم تسجيله في أو قبل هذا التاريخ"""
        latest_purchase = self.purchaseinvoiceitem_set.filter(
            invoice__invoice_type='PURCHASE',
            invoice__invoice_year__lte=year
        ).filter(
            Q(invoice__invoice_year__lt=year) | Q(invoice__invoice_month__lte=month)
        ).order_by('-invoice__invoice_year', '-invoice__invoice_month', '-id').first()

        if latest_purchase:
            return latest_purchase.purchase_price
        return self.initial_purchase_price

    # 3. محرك البحث عن "المندبة" في تاريخ معين
    def get_commission_at_date(self, month, year):
        """تأتي بأحدث مندبة تم تفعيلها في أو قبل هذا التاريخ"""
        latest_comm = self.commission_records.filter(
            activation_year__lte=year
        ).filter(
            Q(activation_year__lt=year) | Q(activation_month__lte=month)
        ).order_by('-activation_year', '-activation_month', '-id').first()

        if latest_comm:
            return latest_comm.commission_amount
        return self.initial_commission_amount
    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [('name', 'branch')]
        ordering = ['name']

    def __str__(self): 
        return f"{self.name} - {self.branch.name}"


class CommissionHistory(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='commission_records', verbose_name="المنتج")
    commission_amount = models.PositiveIntegerField(verbose_name="المندبة الجديدة")
    
    # تاريخ تفعيل المندبة الجديدة
    activation_month = models.PositiveIntegerField(verbose_name="شهر التفعيل")
    activation_year = models.PositiveIntegerField(verbose_name="سنة التفعيل")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activation_year', '-activation_month']
        unique_together = ('item', 'activation_month', 'activation_year')
        
    def __str__(self):
        return f"تحديث مندبة {self.item.name} - {self.activation_month}/{self.activation_year}"


class InventoryAdjustment(models.Model):
    ADJUSTMENT_TYPES = (
        ('DEFICIT', 'عجز (-)'),
        ('SURPLUS', 'زيادة (+)'),
    )
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='adjustments', verbose_name="المنتج")
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES, verbose_name="نوع التسوية")
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="السبب / ملاحظات")
    
    # تاريخ التسوية (عشان يسمع في جرد الشهر الصح)
    month = models.PositiveIntegerField(verbose_name="شهر التسوية")
    year = models.PositiveIntegerField(verbose_name="سنة التسوية")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year', '-month', '-id']

    def __str__(self):
        sign = "-" if self.adjustment_type == 'DEFICIT' else "+"
        return f"تسوية {self.item.name} ({sign}{self.quantity}) - {self.month}/{self.year}"
# ==========================================================
# 5. نظام فواتير الشراء (التسعير التاريخي) 🛒 (معدل)
# ==========================================================
class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم المورد / المصنع")
    is_synced = models.BooleanField(default=False)  # 🔄

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class PurchaseInvoice(models.Model):
    INVOICE_TYPES = (
        ('PURCHASE', 'فاتورة شراء (إضافة للمخزن)'),
        ('RETURN', 'فاتورة مرتجع (خصم من المخزن)'),
    )

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع")
    invoice_number = models.PositiveIntegerField(unique=True, verbose_name="رقم الفاتورة")    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name="المورد")
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='PURCHASE', verbose_name="نوع الفاتورة")
    invoice_month = models.PositiveIntegerField(verbose_name="شهر الفاتورة", db_index=True)
    invoice_year = models.PositiveIntegerField(verbose_name="سنة الفاتورة", db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)  # 🔄

    class Meta:
        unique_together = ('branch', 'invoice_number', 'supplier') 
        ordering = ['-invoice_year', '-invoice_month', '-id']

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    def __str__(self):
        type_name = "شراء" if self.invoice_type == 'PURCHASE' else "مرتجع"
        return f"{type_name} {self.invoice_number} - {self.supplier.name}"


class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, related_name='items', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, verbose_name="الصنف")
    
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    purchase_price = models.PositiveIntegerField(verbose_name="السعر بالفاتورة", null=True, blank=True, default=0)
    # ⚠️ تم حذف عمولة المندوب (commission_amount)
    
    is_synced = models.BooleanField(default=False)  # 🔄

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.is_synced = False
        super().save(*args, **kwargs)
        

    def __str__(self):
        return str(self.invoice.invoice_number)

# ==========================================================
# 6. النماذج الخاصة بالبيع والتحصيل 🧾
# ==========================================================

class Receipt(models.Model):
    SOURCE_CHOICES = (
        ('DESKTOP', 'الكمبيوتر الرئيسي'),
        ('MOBILE', 'تطبيق المندوب'),
    )

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='DESKTOP', verbose_name="المصدر")
    receipt_number = models.PositiveIntegerField(verbose_name="رقم الوصل", db_index=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع", db_index=True)
    customer_name = models.CharField(max_length=150, verbose_name="اسم العميل", blank=True, db_index=True)
    products_text = models.TextField(verbose_name="نص المنتجات (للطباعة)", blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف", db_index=True)
    address = models.CharField(max_length=255, blank=True, verbose_name="العنوان")
    area = models.CharField(max_length=100, blank=True, verbose_name="المنطقة", db_index=True)
    total_amount = models.PositiveIntegerField(default=0, verbose_name="الإجمالي")
    down_payment = models.PositiveIntegerField(default=0, verbose_name="المقدم")
    installment_system = models.CharField(max_length=200, blank=True, verbose_name="وصف نظام القسط")
    salesperson = models.ForeignKey(Salesperson, on_delete=models.PROTECT, null=True, blank=True, verbose_name="المندوب")
    sale_year = models.PositiveIntegerField(verbose_name="سنة البيع", db_index=True)
    sale_month = models.PositiveIntegerField(verbose_name="شهر البيع", db_index=True)
    is_cash_sale = models.BooleanField(default=False, verbose_name="كاش فقط")
    receipt_hash = models.CharField(max_length=64, blank=True, null=True, verbose_name="بصمة الفاتورة")
    
    # Manager Approval Fields for Mobile Sync
    sync_action = models.CharField(max_length=20, default='NEW', verbose_name="إجراء المزامنة")
    is_confirmed = models.BooleanField(default=True, verbose_name="تم التأكيد (للمدير)")

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    objects = ValidReceiptManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_synced = models.BooleanField(default=False)  # 🔄

    @property
    def is_authentic(self):
        from .security_utils import generate_receipt_signature
        expected_hash = generate_receipt_signature(
            self.receipt_number, self.total_amount, self.sale_month, self.sale_year
        )
        return self.receipt_hash == expected_hash

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            from .models import ClientLicense
            base_license = ClientLicense.objects.filter(
                is_active=True, 
                product_id__lt=10, 
                invoices_balance__gt=0
            ).order_by('-id').first()
            
            if base_license:
                base_license.invoices_balance -= 1
                base_license.save() 
            else:
                recharge_code = ClientLicense.objects.filter(
                    is_active=True, 
                    product_id__gte=10, 
                    invoices_balance__gt=0
                ).order_by('id').first()
                
                if recharge_code:
                    recharge_code.invoices_balance -= 1
                    recharge_code.save()
                else:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        "لا يوجد رصيد فواتير كافٍ. يرجى شحن رصيد جديد لإصدار الفواتير."
                    )

        from .security_utils import generate_receipt_signature
        self.receipt_hash = generate_receipt_signature(
            self.receipt_number, self.total_amount, self.sale_month, self.sale_year
        )

        self.is_synced = False
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('branch', 'receipt_number')
        ordering = ['-receipt_number']

    def __str__(self): 
        return f"[{self.source}] - {self.receipt_number} - {self.customer_name}"

    @classmethod
    def get_next_receipt_number(cls, branch):
        last_num = cls.objects.filter(branch=branch).aggregate(Max('receipt_number'))['receipt_number__max']
        return (last_num or 0) + 1

class SaleItem(models.Model):
    receipt = models.ForeignKey(Receipt, related_name='items', on_delete=models.CASCADE, verbose_name="الوصل التابع له")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, verbose_name="الصنف") 
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    unit_price = models.PositiveIntegerField(verbose_name="سعر الوحدة")

    def __str__(self):
        return f"{self.quantity} x {self.inventory_item.name}"

class InstallmentPayment(models.Model):
    receipt = models.ForeignKey(Receipt, related_name='payments', on_delete=models.CASCADE, verbose_name="الوصل التابع له")
    payment_date = models.DateField(verbose_name="تاريخ الدفعة المستحقة")
    amount = models.PositiveIntegerField(verbose_name="المبلغ")

    def __str__(self):
        return f"قسط {self.amount} - تاريخ {self.payment_date}"

# ==========================================================
# 7. إعدادات ومصروفات الشركة
# ==========================================================

class Expense(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    expense_year = models.IntegerField()
    expense_month = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)  # 🔄

    def save(self, *args, **kwargs):
        self.is_synced = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.amount})"

class CompanySetting(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الشركة")
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name="وصف الشركة") 
    phone1 = models.CharField(max_length=20, verbose_name="رقم تليفون 1")
    phone2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم تليفون 2")
    footer_text = models.CharField(max_length=250, default="تطبق الشروط والأحكام", verbose_name="الفوتر")
    is_cloud_viewer = models.BooleanField(default=False, verbose_name="جهاز مشاهد سحابي")
    
    def save(self, *args, **kwargs):
        if not self.pk and CompanySetting.objects.exists():
            return CompanySetting.objects.first().save(*args, **kwargs)
        return super(CompanySetting, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    
# ==========================================================
# 8. نظام الترخيص (Local Licensing) 🔒
# ==========================================================

class UsedLicense(models.Model):
    code_hash = models.CharField(max_length=64, unique=True, verbose_name="بصمة الكود")
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code_hash


class ClientLicense(models.Model):
    PRODUCT_CHOICES = [
        (1,  'تجربة مجانية (Trial 60 Days)'),
        (2,  'طباعة فقط - سنة واحدة'),
        (3,  'طباعة فقط - مدى الحياة'),
        (4,  'إدارة كاملة - سنة واحدة'),
        (5,  'إدارة كاملة - 3 سنوات'),
        (6,  'إدارة كاملة - 5 سنوات'),
        (7,  'إدارة كاملة - مدى الحياة (VIP)'),
        (8,  'إضافة الأونلاين - سنة'),
        (9,  'إضافة الأونلاين - 5 سنوات'),
        (10, 'كود شحن (100 فاتورة)'),
        (11, 'كود شحن (300 فاتورة)'),
        (12, 'كود شحن (500 فاتورة)'),
        (13, 'كود شحن (1000 فاتورة)'),
        (14, 'كود شحن (3000 فاتورة)'),
        (15, 'كود شحن (5000 فاتورة)'),
        (16, 'كود الطوارئ (استعادة وضبط)'),
    ]

    product_id        = models.IntegerField(choices=PRODUCT_CHOICES, default=1, verbose_name="نوع الباقة")
    start_date        = models.DateField(null=True, blank=True, verbose_name="تاريخ التفعيل")
    expiry_date       = models.DateField(null=True, blank=True, verbose_name="تاريخ الانتهاء")
    invoices_balance  = models.PositiveIntegerField(default=0, verbose_name="رصيد الفواتير")
    is_active         = models.BooleanField(default=True, verbose_name="حالة الكود")
    machine_id        = models.CharField(max_length=255, null=True, blank=True, verbose_name="الجهاز")
    company_code      = models.CharField(max_length=10, null=True, blank=True, verbose_name="كود الشركة (للأونلاين)")
    license_code_hash = models.CharField(max_length=64, null=True, blank=True, verbose_name="توقيع الكود")
    last_checkin      = models.DateTimeField(auto_now=True, verbose_name="آخر نشاط")
    is_online_active  = models.BooleanField(default=False, verbose_name="يدعم الأونلاين")
    online_start_date = models.DateField(null=True, blank=True, verbose_name="بداية الأونلاين")
    online_expiry_date= models.DateField(null=True, blank=True, verbose_name="انتهاء الأونلاين")
    created_at        = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        if self.product_id in [3, 7] or self.product_id >= 10:
            return False
        if self.expiry_date is None:
            if self.pk is None:
                return False
            return True
        return timezone.now().date() > self.expiry_date

    @classmethod
    def get_active_license(cls):
        today = timezone.now().date()

        valid_licenses = cls.objects.filter(
            Q(expiry_date__gte=today) | Q(expiry_date__isnull=True),
            is_active=True
        )

        if not valid_licenses.exists():
            return None

        stats = valid_licenses.aggregate(
            combined_start=Min('start_date'),
            combined_end=Max('expiry_date'),
            total_balance=Sum('invoices_balance'),
        )

        base_licenses = valid_licenses.filter(product_id__lte=7)
        if base_licenses.exists():
            best_product = base_licenses.order_by('-product_id').first().product_id
        else:
            best_product = 1

        online_licenses = valid_licenses.filter(
            Q(online_expiry_date__gte=today) | Q(online_expiry_date__isnull=True),
            is_online_active=True
        )

        has_online = False
        on_start = None
        on_end = None
        comp_code = None

        if online_licenses.exists():
            has_online = True
            on_stats = online_licenses.aggregate(
                min_start=Min('online_start_date'),
                max_end=Max('online_expiry_date')
            )
            on_start = on_stats['min_start']
            on_end = on_stats['max_end']
            
            # Find any valid company code
            lic_with_code = online_licenses.exclude(company_code__isnull=True).first()
            if lic_with_code:
                comp_code = lic_with_code.company_code

        merged_license = cls(
            product_id=best_product,            
            start_date=stats['combined_start'],
            expiry_date=stats['combined_end'],
            invoices_balance=stats['total_balance'] or 0,
            is_active=True,
            machine_id=valid_licenses.first().machine_id,
            company_code=comp_code,
            is_online_active=has_online,
            online_start_date=on_start,
            online_expiry_date=on_end
        )

        return merged_license

    def __str__(self):
        return f"License {self.pk} - Product {self.product_id}"

    def save(self, *args, **kwargs):
        from .security_utils import generate_record_signature, get_machine_id
        
        if not self.machine_id:
            self.machine_id = get_machine_id()
            
        self.license_code_hash = generate_record_signature(
            self.expiry_date, 
            self.invoices_balance, 
            self.machine_id,
            self.product_id,
            self.is_active
        )
        super().save(*args, **kwargs)

class LicenseHistory(models.Model):
    machine_id     = models.CharField(max_length=100)
    product_name   = models.CharField(max_length=100)
    operation_type = models.CharField(max_length=50, default="تجديد/تفعيل", verbose_name="نوع العملية")
    start_date     = models.DateField(null=True, blank=True)
    end_date       = models.DateField(null=True, blank=True)
    added_balance  = models.IntegerField(default=0, verbose_name="الرصيد المضاف")
    archived_at    = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ العملية")
    status         = models.CharField(max_length=50, default="أرشيف")

    def __str__(self):
        return f"{self.operation_type} - {self.product_name}"

# ==========================================================
# 9. منطقة المراجعة للفواتير الخارجية (Staging Area)
# ==========================================================

class PendingExternalReceipt(models.Model):
    SOURCE_CHOICES = (
        ('CLOUD', 'السحابة (أونلاين)'),
        ('USB', 'سلك الـ USB'),
        ('FILE', 'ملف JSON'),
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="الفرع")
    batch_id = models.CharField(max_length=100, default='', blank=True, verbose_name="معرف التصدير")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, verbose_name="المصدر")
    payload = models.JSONField(verbose_name="بيانات الفاتورة (JSON)")
    is_processed = models.BooleanField(default=False, verbose_name="تم المراجعة والإضافة؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الوصول")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "فاتورة خارجية معلقة"
        verbose_name_plural = "الفواتير الخارجية المعلقة"

    def __str__(self):
        return f"[{self.get_source_display()}] - {self.branch.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"