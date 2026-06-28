from django.db import models
from django.utils import timezone
from datetime import timedelta
from .utils.crypto import LicenseGenerator

class Client(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم العميل")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    machine_id = models.CharField(max_length=100, unique=True, verbose_name="بصمة الجهاز (Machine ID)")
    store_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="اسم المحل")
    
    # الجدار الثامن: حظر الجهاز من السيرفر
    is_banned = models.BooleanField(default=False, verbose_name="حظر هذا الجهاز (Blacklist)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")

    def __str__(self):
        return f"{self.name} - {self.store_name}"

class License(models.Model):
    PRODUCT_CHOICES = [
        (1, 'تجربة مجانية (Trial 60 Days)'),
        (2, 'طباعة فقط - سنة واحدة'),
        (3, 'طباعة فقط - مدى الحياة'),
        (4, 'إدارة كاملة - سنة واحدة'),
        (5, 'إدارة كاملة - 3 سنوات'),
        (6, 'إدارة كاملة - 5 سنوات'),
        (7, 'إدارة كاملة - مدى الحياة (VIP)'),
        (8, 'إضافة الأونلاين - سنة'),
        (9, 'إضافة الأونلاين - 5 سنوات'),
        (10, 'كود شحن (100 فاتورة)'),
        (11, 'كود شحن (300 فاتورة)'),
        (12, 'كود شحن (500 فاتورة)'),
        (13, 'كود شحن (1000 فاتورة)'),
        (14, 'كود شحن (3000 فاتورة)'),
        (15, 'كود شحن (5000 فاتورة)'),
        (16, 'كود الطوارئ (استعادة وضبط - لمرة واحدة)'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='licenses', verbose_name="العميل")
    product_id = models.IntegerField(choices=PRODUCT_CHOICES, verbose_name="نوع الباقة")
    
    # النظام المالي
    price = models.IntegerField(default=0, verbose_name="المبلغ المدفوع (جنية)")
    
    # الملاحظات السرية
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات فنية (سري)")

    start_date = models.DateField(default=timezone.now, verbose_name="تاريخ بداية الترخيص")
    generated_code = models.CharField(max_length=20, editable=False, verbose_name="كود التفعيل")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def save(self, *args, **kwargs):
        # توليد الكود تلقائياً عند الحفظ لأول مرة
        if not self.generated_code:
            self.generated_code = LicenseGenerator.generate(
                machine_id=self.client.machine_id,
                product_id=self.product_id,
                start_date=self.start_date
            )
        super().save(*args, **kwargs)

    @property
    def is_lifetime(self):
        return self.product_id in [3, 7]

    @property
    def is_base_plan(self):
        return 1 <= self.product_id <= 7

    @property
    def is_online_product(self):
        return self.product_id in [8, 9]

    @property
    def is_invoice_based(self):
        return 10 <= self.product_id <= 15

    @property
    def is_emergency_code(self):
        return self.product_id == 16

    def get_duration_days(self):
        duration_map = {
            1: 60, 2: 365, 4: 365, 8: 365, 
            5: 365*3, 6: 365*5, 9: 365*5,
            3: 365*99, 7: 365*99
        }
        return duration_map.get(self.product_id, 0)

    def get_expiry_date(self):
        if self.is_invoice_based or self.is_emergency_code or self.is_lifetime:
            return None
        days = self.get_duration_days()
        if days > 0:
            return self.start_date + timedelta(days=days)
        return None

    def get_whatsapp_date_str(self):
        if self.is_lifetime:
            return "مدى الحياة (Lifetime)"
        elif self.is_emergency_code:
            return "استخدام لمرة واحدة (One-Time Use)"
        elif self.is_invoice_based:
            return "رصيد فواتير (غير محدد المدة)"
        else:
            expiry = self.get_expiry_date()
            if expiry:
                return expiry.strftime('%Y-%m-%d')
            return "غير محدد"

    def __str__(self):
        return f"{self.client.name} ({self.get_product_id_display()})"