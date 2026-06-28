import time
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages

class LicenseEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. تحسين الأداء: تجاهل ملفات الستايل والأدمن فوراً قبل أي فحص
        if request.path.startswith('/static/') or request.path.startswith('/admin/') or request.path.startswith('/media/'):
            return self.get_response(request)

        # 2. استثناء صفحات التفعيل والشحن عشان ميدخلش في Loop (حلقة مفرغة)
        try:
            excluded_urls = [reverse('activate_app'), reverse('subscription_dashboard')]
            if request.path in excluded_urls:
                return self.get_response(request)
        except Exception:
            pass

        # 3. 🔴 تحديد ما إذا كان الكاشير يقوم بحفظ فاتورة الآن
        is_saving_receipt = False
        try:
            # ⚠️ ملاحظة: استبدل 'create_receipt' بالاسم الفعلي لرابط حفظ الفاتورة في ملف urls.py الخاص بك
            if request.path == reverse('add_receipt'): 
                is_saving_receipt = True
        except Exception:
            pass

        # 4. الحل السحري للسرعة (معدل للأمان): 
        # لو المستخدم معاه ترخيص، ولم يمر 5 دقائق، "وليس" في عملية حفظ إيصال -> خليه يمر بسرعة
        last_check = request.session.get('last_license_check', 0)
        if request.session.get('is_licensed') and (time.time() - last_check < 300) and not is_saving_receipt:
            return self.get_response(request)

        # ============================================================
        # 🛡️ المنطقة "الثقيلة" (تتم كل 5 دقائق أو إجبارياً عند حفظ أي فاتورة)
        # ============================================================
        try:
            # استدعاء الموديلات والأدوات هنا لتجنب تداخل الاستدعاءات (Circular Import)
            from .models import ClientLicense
            from .security_utils import generate_record_signature, get_machine_id
            
            machine_id = get_machine_id()
            today = timezone.now().date()
            
            # جلب كل التراخيص النشطة
            all_active_licenses = ClientLicense.objects.filter(is_active=True)
            
            valid_time_license = None
            total_invoices_balance = 0

            for lic in all_active_licenses:
                # أ. الفحص الجنائي: التأكد من البصمة السرية لاكتشاف أي تلاعب يدوي
                expected_sig = generate_record_signature(lic.expiry_date, lic.invoices_balance, machine_id, lic.product_id, lic.is_active)
                if lic.license_code_hash != expected_sig:
                    # تم اكتشاف تلاعب! نقوم بإبطال هذه الرخصة فوراً في قاعدة البيانات
                    # نستخدم update لكي لا يتم استدعاء دالة save وتحديث البصمة بالغلط
                    ClientLicense.objects.filter(pk=lic.pk).update(is_active=False)
                    continue

                # ب. جلب أحدث رخصة زمنية (للباقات من 1 إلى 9)
                if lic.product_id < 10:
                    if not valid_time_license or (lic.expiry_date and lic.expiry_date > valid_time_license.expiry_date):
                        valid_time_license = lic
                
                # ج. تجميع رصيد الفواتير المتاح من كل التراخيص السليمة
                total_invoices_balance += lic.invoices_balance

            # ============================================================
            # ⚖️ اتخاذ القرارات (الفخ المزدوج)
            # ============================================================

            # القرار الأول (بوابة الزمن): هل انتهت الصلاحية الزمنية للبرنامج؟
            if not valid_time_license or (valid_time_license.expiry_date and today > valid_time_license.expiry_date):
                request.session['is_licensed'] = False
                return redirect('activate_app')
            
            # القرار الثاني (جدار الحماية): هل يحاول حفظ فاتورة ورصيده صفر؟
            if is_saving_receipt and total_invoices_balance <= 0:
                # نمنعه من الحفظ ونوجهه لصفحة الشحن مع رسالة تنبيه
                messages.error(request, "عفواً، لقد استنفدت رصيد الفواتير بالكامل. برجاء تفعيل كود شحن فواتير للاستمرار.")
                return redirect('subscription_dashboard')

            # القرار الثالث (السحابة): إذا كان المستخدم فرعياً (Cloud Viewer)، يجب أن يكون اشتراك الأونلاين فعالاً
            if request.session.get('is_cloud_viewer'):
                active_lic = ClientLicense.get_active_license()
                if not active_lic or not active_lic.is_online_active:
                    request.session['is_licensed'] = False
                    messages.error(request, "تنبيه هام: لقد انتهى اشتراك الأونلاين الخاص بالشركة. كجهاز فرعي، لا يمكنك العمل على النظام حتى يقوم الكمبيوتر الأساسي بتجديد الاشتراك.")
                    return redirect('shutdown_app')

            # ============================================================
            # ✅ كل شيء سليم: تجديد الثقة لمدة 5 دقائق قادمة
            # ============================================================
            request.session['is_licensed'] = True
            request.session['last_license_check'] = time.time()
            return self.get_response(request)

        except Exception as e:
            # لو حصل أي خطأ تقني، نعتبره غير مرخص للأمان
            print(f"License Middleware Error: {e}")
            return redirect('activate_app')