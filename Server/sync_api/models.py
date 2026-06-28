from django.db import models
import uuid

# ==========================================================
# 1. بوابة التراخيص (Security Gate) 🛡️
# ==========================================================
class ServerLicense(models.Model):
    machine_id = models.CharField(max_length=255, unique=True, verbose_name="بصمة الجهاز")
    company_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="كود الشركة")
    client_name = models.CharField(max_length=150, verbose_name="اسم العميل", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="مسموح له بالمزامنة؟")
    is_online_active = models.BooleanField(default=False, verbose_name="مسموح له بالمزامنة الأونلاين؟")
    online_expiry_date = models.DateField(null=True, blank=True, verbose_name="تاريخ انتهاء الأونلاين")
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name="آخر مزامنة")

    def save(self, *args, **kwargs):
        if not self.company_code:
            import random
            while True:
                code = str(random.randint(1000, 9999))
                if not ServerLicense.objects.filter(company_code=code).exists():
                    self.company_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client_name} ({self.machine_id})"

# ==========================================================
# 2. البيانات الأساسية (الإعدادات - الفروع - الموظفين - المنتجات) 🏗️
# ==========================================================

# أ) إعدادات الشركة (Company Setting) - (جديد) ⚙️
class ServerCompanySetting(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    # عادة لا يوجد غير صف واحد، لكن سنستخدم local_id للحفاظ على النسق
    local_id = models.IntegerField(default=1) 
    
    name = models.CharField(max_length=100, verbose_name="اسم الشركة")
    description = models.CharField(max_length=200, blank=True, null=True)
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    footer_text = models.CharField(max_length=250, blank=True, null=True)
    
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')
        verbose_name = "إعدادات شركة عميل"
        verbose_name_plural = "إعدادات شركات العملاء"

# ب) الفروع
class ServerBranch(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID الفرع المحلي")
    name = models.CharField(max_length=150)
    synced_at = models.DateTimeField(auto_now=True) 

    class Meta:
        unique_together = ('source_machine_id', 'local_id')

# ج) الموظفين (Salesperson) 👔
class ServerSalesperson(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID الموظف المحلي")
    local_branch_id = models.IntegerField(verbose_name="ID فرع الموظف")
    
    name = models.CharField(max_length=100)
    cloud_username = models.CharField(max_length=150, null=True, blank=True, verbose_name="اسم مستخدم السحابة")
    cloud_password = models.CharField(max_length=150, null=True, blank=True, verbose_name="كلمة مرور السحابة")
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')

# د) المخزون/المنتجات (InventoryItem) 📦
class ServerInventoryItem(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID المنتج المحلي")
    local_branch_id = models.IntegerField(verbose_name="ID المخزن")
    
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    
    # حولناها Decimal للدقة في السيرفر
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salesperson_commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at_local = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')

# ==========================================================
# 3. الفواتير (Server Receipt) 🧾
# ==========================================================
class ServerReceipt(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID الفاتورة المحلي")
    receipt_hash = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="هاش الفاتورة")
    
    receipt_number = models.PositiveIntegerField()
    local_branch_id = models.IntegerField()
    local_salesperson_id = models.IntegerField(null=True, blank=True) # ربطنا الفاتورة بالموظف
    
    customer_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=150, blank=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    installment_system = models.CharField(max_length=255, blank=True)
    
    sale_year = models.IntegerField()
    sale_month = models.IntegerField()
    is_cash_sale = models.BooleanField(default=False)
    products_text = models.TextField(blank=True, null=True)
    
    sync_action = models.CharField(max_length=20, default='NEW', verbose_name="Action from Mobile")
    is_confirmed = models.BooleanField(default=False, verbose_name="تم التأكيد")
    
    synced_at = models.DateTimeField(auto_now_add=True)
    created_at_local = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at_local']

# ==========================================================
# 4. تفاصيل الفاتورة (Sale Items) 🛒
# ==========================================================
class ServerSaleItem(models.Model):
    receipt = models.ForeignKey(ServerReceipt, related_name='items', on_delete=models.CASCADE)
    
    local_product_id = models.IntegerField()
    product_name_snapshot = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

# ==========================================================
# 5. الأقساط (Installments) 📅
# ==========================================================
class ServerInstallmentPayment(models.Model):
    receipt = models.ForeignKey(ServerReceipt, related_name='payments', on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

# ==========================================================
# 6. المصروفات (Server Expense) 💸
# ==========================================================
class ServerExpense(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID المصروف المحلي")
    local_branch_id = models.IntegerField()
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    expense_year = models.IntegerField()
    expense_month = models.IntegerField()
    
    created_at_local = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')

# ==========================================================
# 7. حركات المخزن (Server Stock Transaction) 📦
# ==========================================================
class ServerStockTransaction(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID الحركة المحلي")
    
    local_product_id = models.IntegerField()
    product_name_snapshot = models.CharField(max_length=255, blank=True)
    
    transaction_type = models.CharField(max_length=50)
    quantity = models.IntegerField()
    created_at_local = models.DateTimeField(null=True, blank=True)
    
    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')

# ==========================================================
# 8. توفير الإعدادات عن بعد للموبايل (Remote Provisioning) 📱
# ==========================================================
class MobileProvisionToken(models.Model):
    token = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token {self.token} created at {self.created_at}"

# ==========================================================
# 9. مستخدمي السحابة (Cloud Users for Viewer PCs)
# ==========================================================
class ServerCloudUser(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID المستخدم المحلي")
    
    username = models.CharField(max_length=150)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=50, default='VIEWER') # VIEWER, CASHIER
    
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')
        verbose_name = "مستخدم سحابي (فرعي)"
        verbose_name_plural = "مستخدمي السحابة (فروع)"

# ==========================================================
# 10. الموردين (Server Supplier) 🏭
# ==========================================================
class ServerSupplier(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID المورد المحلي")

    name = models.CharField(max_length=200, verbose_name="اسم المورد")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="رقم التليفون")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="العنوان")

    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')
        verbose_name = "مورد"
        verbose_name_plural = "الموردين"

    def __str__(self):
        return f"{self.name} ({self.source_machine_id})"

# ==========================================================
# 11. فواتير الشراء (Server Purchase Invoice) 🧾📥
# ==========================================================
class ServerPurchaseInvoice(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID الفاتورة المحلي")

    invoice_number = models.PositiveIntegerField(verbose_name="رقم الفاتورة")
    invoice_month = models.IntegerField(verbose_name="شهر الفاتورة")
    invoice_year = models.IntegerField(verbose_name="سنة الفاتورة")

    INVOICE_TYPE_CHOICES = [
        ('PURCHASE', 'مشتريات'),
        ('RETURN', 'مرتجع'),
    ]
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='PURCHASE', verbose_name="نوع الفاتورة")

    local_supplier_id = models.IntegerField(null=True, blank=True, verbose_name="ID المورد المحلي")

    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')
        verbose_name = "فاتورة مشتريات"
        verbose_name_plural = "فواتير المشتريات"

# ==========================================================
# 12. تفاصيل فواتير الشراء (Server Purchase Invoice Item) 🛒
# ==========================================================
class ServerPurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(ServerPurchaseInvoice, related_name='items', on_delete=models.CASCADE)

    local_product_id = models.IntegerField(verbose_name="ID الصنف المحلي")
    product_name_snapshot = models.CharField(max_length=255, blank=True, verbose_name="اسم الصنف وقت الشراء")
    quantity = models.IntegerField(verbose_name="الكمية")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="سعر الشراء")

    class Meta:
        verbose_name = "بند فاتورة مشتريات"
        verbose_name_plural = "بنود فواتير المشتريات"

# ==========================================================
# 13. سجل العمولات (Server Commission History) 💰
# ==========================================================
class ServerCommissionHistory(models.Model):
    source_machine_id = models.CharField(max_length=255, db_index=True)
    local_id = models.IntegerField(verbose_name="ID السجل المحلي")

    local_salesperson_id = models.IntegerField(verbose_name="ID المندوب المحلي")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="قيمة العمولة")
    reason = models.CharField(max_length=255, blank=True, verbose_name="السبب")
    commission_date = models.DateField(null=True, blank=True, verbose_name="تاريخ العمولة")

    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_machine_id', 'local_id')
        verbose_name = "سجل عمولة"
        verbose_name_plural = "سجلات العمولات"
