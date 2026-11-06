from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import IntegrityError
from django.contrib import messages
from datetime import timedelta
from .models import Client, License

# ---------------------------------------------------------
# تخصيص لوحة التحكم للعملاء (Clients)
# ---------------------------------------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'machine_id_display', 'store_name', 'licenses_count', 'is_banned_status')
    list_filter = ('is_banned', 'created_at')
    search_fields = ('name', 'phone', 'machine_id', 'store_name')
    actions = ['ban_clients', 'unban_clients']

    def machine_id_display(self, obj):
        return format_html('<code style="color: #d63384;">{}</code>', obj.machine_id)
    machine_id_display.short_description = "بصمة الجهاز"

    def licenses_count(self, obj):
        count = obj.licenses.count()
        return format_html('<b style="color: blue;">{}</b>', count)
    licenses_count.short_description = "عدد الرخص"

    def is_banned_status(self, obj):
        if obj.is_banned:
            # التعديل هنا: أضفنا {} والنص كمتغير ثاني
            return format_html('<span style="color: white; background: red; padding: 3px 8px; border-radius: 10px;">{}</span>', "محظور 🚫")
        return format_html('<span style="color: green;">{}</span>', "نشط ✅")
    is_banned_status.short_description = "الحالة الأمنية"

    def ban_clients(self, request, queryset):
        queryset.update(is_banned=True)
        self.message_user(request, "تم حظر الأجهزة المحددة بنجاح.")
    ban_clients.short_description = "🚫 حظر الأجهزة المحددة (Blacklist)"

    def unban_clients(self, request, queryset):
        queryset.update(is_banned=False)
        self.message_user(request, "تم رفع الحظر عن الأجهزة المحددة.")
    unban_clients.short_description = "✅ رفع الحظر (Whitelist)"


# ---------------------------------------------------------
# تخصيص لوحة التحكم للتراخيص (Licenses)
# ---------------------------------------------------------
@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('client_link', 'product_display', 'price_display', 'start_date', 'expiry_status', 'generated_code_display')
    list_filter = ('product_id', 'created_at')
    search_fields = ('client__name', 'generated_code', 'client__phone')
    readonly_fields = ('generated_code',)
    
    fieldsets = (
        ('بيانات العميل والباقة', {
            'fields': ('client', 'product_id', 'start_date', 'price')
        }),
        ('الأمان والكود', {
            'fields': ('generated_code', 'is_active')
        }),
        ('ملاحظات الإدارة', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )

    def client_link(self, obj):
        return format_html('<b>{}</b>', obj.client.name)
    client_link.short_description = "العميل"

    def product_display(self, obj):
        return obj.get_product_id_display()
    product_display.short_description = "الباقة"

    def price_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">{} EGP</span>', obj.price)
    price_display.short_description = "المبلغ"

    def generated_code_display(self, obj):
        return format_html('<code style="background-color: #f0f0f0; padding: 2px 5px; border: 1px solid #ccc;">{}</code>', obj.generated_code)
    generated_code_display.short_description = "كود التفعيل"

    def expiry_status(self, obj):
        duration_map = {
            1: 60,       # تجربة
            2: 365,      # سنة
            4: 365,      # سنة
            8: 365,      # سنة
            5: 365 * 3,  # 3 سنوات
            6: 365 * 5,  # 5 سنوات
            9: 365 * 5,  # 5 سنوات
            3: 365 * 99, # مدى الحياة
            7: 365 * 99, # مدى الحياة
        }

        # إصلاح الخطأ هنا أيضاً
        if obj.product_id >= 10:
            return format_html('<span style="color: gray;">{}</span>', "رصيد فواتير")

        days = duration_map.get(obj.product_id, 0)
        end_date = obj.start_date + timedelta(days=days)
        today = timezone.now().date()
        days_left = (end_date - today).days

        if days_left < 0:
            return format_html('<span style="color: white; background: red; padding: 3px 8px; border-radius: 10px;">منتهي منذ {} يوم</span>', abs(days_left))
        elif days_left <= 30:
            return format_html('<span style="color: black; background: orange; padding: 3px 8px; border-radius: 10px;">ينتهي قريباً ({} يوم) ⚠️</span>', days_left)
        elif days_left > 10000:
            return format_html('<span style="color: white; background: #28a745; padding: 3px 8px; border-radius: 10px;">{}</span>', "مدى الحياة ∞")
        else:
            return format_html('<span style="color: white; background: #28a745; padding: 3px 8px; border-radius: 10px;">ساري ({} يوم)</span>', days_left)
    
    expiry_status.short_description = "حالة الاشتراك"

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except IntegrityError:
            messages.error(request, "خطأ: هذا العميل لديه بالفعل كود مفعل لنفس الباقة ونفس التاريخ.")