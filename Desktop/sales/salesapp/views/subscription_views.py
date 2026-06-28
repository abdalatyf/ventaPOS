# salesapp/views/subscription_views.py
# نظام الاشتراك والترخيص المطور (Subscription & Licensing)

import hashlib
from datetime import date
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import ClientLicense, UsedLicense, LicenseHistory
from ..security_utils import get_machine_id, save_license_file
from ..license_validator import LicenseValidator


PRODUCT_NAMES = {
    1: "نسخة تجريبية", 2: "باقة سنوية (Basic)", 4: "باقة سنوية (Pro)",
    5: "باقة 3 سنوات", 6: "باقة 5 سنوات", 3: "Lifetime (Standard)", 7: "Lifetime (Unlimited)",
    8: "خدمة أونلاين (سنة)", 9: "خدمة أونلاين (5 سنوات)",
    10: "كارت شحن (100 فاتورة)", 11: "كارت شحن (300 فاتورة)",
    12: "كارت شحن (500 فاتورة)", 13: "كارت شحن (1000 فاتورة)",
    14: "كارت شحن (3000 فاتورة)", 15: "كارت شحن (5000 فاتورة)",
    16: "كود الطوارئ (استعادة وضبط)",
}

MONTHS_MAP = {
    1: 2,    # تجريبي — شهران (60 يوم)
    2: 12,   # Basic سنة
    4: 12,   # Pro سنة
    5: 36,   # Pro 3 سنوات
    6: 60,   # Pro 5 سنوات
}
INVOICES_PER_MONTH = 300


def _build_license_data(pid, code_start_date):
    """دالة مساعدة: تحسب خصائص الباقة وتعيد (expiry_date, usage_limit, is_online)"""
    usage_limit = 0
    is_online_product = False
    final_expiry_date = None

    # أ) كروت الشحن (رصيد فقط)
    if pid >= 10:
        limits_map = {10: 100, 11: 300, 12: 500, 13: 1000, 14: 3000, 15: 5000}
        usage_limit = limits_map.get(pid, 0)

    # ب) باقات الأونلاين
    elif pid in [8, 9]:
        is_online_product = True
        duration_years = 1 if pid == 8 else 5
        final_expiry_date = code_start_date + relativedelta(years=duration_years)

    # ج) الاشتراكات الزمنية (الباقات الأساسية)
    else:
        durations_map = {1: 0, 2: 1, 4: 1, 5: 3, 6: 5, 3: 100, 7: 100}
        duration_years = durations_map.get(pid, 1)

        if pid == 1:  # تجريبي
            final_expiry_date = code_start_date + relativedelta(months=MONTHS_MAP.get(pid, 2))
            usage_limit = INVOICES_PER_MONTH * MONTHS_MAP.get(pid, 2)
        elif pid in [3, 7]:  # مدى الحياة
            final_expiry_date = code_start_date + relativedelta(years=duration_years)
            usage_limit = 999999
        else:
            final_expiry_date = code_start_date + relativedelta(years=duration_years)
            months = MONTHS_MAP.get(pid, 12)
            usage_limit = INVOICES_PER_MONTH * months

    return final_expiry_date, usage_limit, is_online_product


def _process_license_code(code, machine_id, operation_type="تفعيل جديد"):
    """
    معالجة كود الترخيص:
    - التحقق من عدم الاستخدام المسبق.
    - تحديث آخر ترخيص إذا كان كود شحن (pid >= 10).
    - إنشاء ترخيص جديد إذا كانت باقة زمنية (pid < 10).
    """
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # 1. منع تكرار الاستخدام
    if UsedLicense.objects.filter(code_hash=code_hash).exists():
        return None, "❌ عفواً، تم استخدام كود التفعيل هذا من قبل."

    # 2. فحص الكود برمجياً
    result = LicenseValidator.validate(code, machine_id)
    if not result["valid"]:
        return None, f"فشل التفعيل: {result.get('error')}"

    pid = result['product_id']
    if pid == 16:
        return None, "❌ هذا الكود مخصص للطوارئ فقط ولا يمكن استخدامه لتفعيل أو شحن النظام."

    code_start_date = date(result['start_year'], result['start_month'], 1)
    final_expiry_date, usage_limit, is_online_product = _build_license_data(pid, code_start_date)

    # 3. منطق التحديث (شحن رصيد أم باقة جديدة)
    if pid >= 10:
        # تحديث رصيد الفواتير في آخر ترخيص متاح
        active_lic = ClientLicense.objects.filter(machine_id=machine_id, is_active=True).order_by('-id').first()
        if active_lic:
            active_lic.invoices_balance += usage_limit
            active_lic.save() # سيقوم الموديل بتحديث البصمة تلقائياً
        else:
            # إذا لم يوجد ترخيص أساسي، ننشئ واحداً جديداً يحمل الرصيد
            ClientLicense.objects.create(
                product_id=pid,
                start_date=date.today(),
                invoices_balance=usage_limit,
                is_active=True,
                machine_id=machine_id,
                license_code_hash=code_hash
            )
    else:
        company_code = None
        if is_online_product:
            import requests
            from django.conf import settings
            from django.apps import apps
            CompanySetting = apps.get_model('salesapp', 'CompanySetting')
            company = CompanySetting.objects.first()
            client_name = company.name if company else "Unknown"
            
            try:
                base_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
                target_url = f"{base_url.rstrip('/')}/api/v1/sync/register-online-license/"
                resp = requests.post(target_url, json={
                    'machine_id': machine_id,
                    'client_name': client_name,
                    'online_expiry_date': str(final_expiry_date)
                }, timeout=10)
                if resp.status_code != 200:
                    return None, f"فشل تسجيل الرخصة أونلاين على السيرفر: {resp.text}"
                
                resp_data = resp.json()
                company_code = resp_data.get('company_code')
            except Exception as e:
                return None, f"تعذر الاتصال بالسيرفر المركزي لتسجيل الرخصة: {e}"

        # إنشاء ترخيص زمني جديد (باقة أساسية)
        ClientLicense.objects.create(
            product_id=pid,
            start_date=code_start_date,
            expiry_date=final_expiry_date,
            invoices_balance=usage_limit,
            is_active=True,
            machine_id=machine_id,
            license_code_hash=code_hash,
            company_code=company_code,
            is_online_active=is_online_product,
            online_start_date=code_start_date if is_online_product else None,
            online_expiry_date=final_expiry_date if is_online_product else None
        )

    # 4. تسجيل العملية في الأرشيف والحرق
    LicenseHistory.objects.create(
        machine_id=machine_id,
        product_name=PRODUCT_NAMES.get(pid, "غير معروف"),
        operation_type=operation_type,
        start_date=code_start_date,
        end_date=final_expiry_date,
        added_balance=usage_limit,
        status="تم التفعيل بنجاح"
    )

    UsedLicense.objects.create(code_hash=code_hash)
    save_license_file(code)

    return pid, None


# ========================================================
# 1. دالة تفعيل التطبيق (شاشة التفعيل الرئيسية)
# ========================================================

import requests
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from ..models import CompanySetting

def activate_app_view(request):
    machine_id = get_machine_id()

    if request.method == 'POST':
        if request.POST.get('is_viewer_login'):
            cloud_username_full = request.POST.get('cloud_username', '').strip()
            cloud_password = request.POST.get('cloud_password', '')

            if '-' not in cloud_username_full:
                messages.error(request, "تنسيق اسم المستخدم غير صحيح. يجب أن يكون [CompanyCode]-[Username]")
                return render(request, 'salesapp/activation_page.html', {'machine_id': machine_id})

            company_code, username = cloud_username_full.split('-', 1)

            base_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
            target_url = f"{base_url.rstrip('/')}/api/v1/auth/viewer/"

            try:
                resp = requests.post(target_url, json={
                    'company_code': company_code,
                    'username': username,
                    'password': cloud_password
                }, timeout=10)

                if resp.status_code == 200:
                    user, created = User.objects.get_or_create(username='_cloud_viewer_')
                    if created:
                        user.set_unusable_password()
                        user.save()

                    login(request, user)

                    setting, _ = CompanySetting.objects.get_or_create()
                    setting.is_cloud_viewer = True
                    setting.save()

                    # Create mock license
                    ClientLicense.objects.create(
                        product_id=8,
                        is_online_active=True,
                        is_active=True,
                        machine_id=machine_id,
                        company_code=company_code
                    )

                    request.session['is_licensed'] = True
                    request.session['last_license_check'] = 0

                    messages.success(request, "تم تسجيل الدخول بنجاح كجهاز فرعي (Viewer).")
                    return redirect('cloud_initial_sync')
                else:
                    messages.error(request, f"فشل تسجيل الدخول: بيانات غير صحيحة.")
            except Exception as e:
                messages.error(request, f"خطأ في الاتصال بالخادم: {str(e)}")

            return render(request, 'salesapp/activation_page.html', {'machine_id': machine_id})

        code = request.POST.get('license_code', '').strip()
        try:
            pid, error = _process_license_code(code, machine_id, operation_type="تفعيل نظام")
            if error:
                messages.error(request, error)
            else:
                request.session['is_licensed'] = True
                request.session['last_license_check'] = 0 # إجبار الميدل وير على الفحص الفوري
                messages.success(request, f"🚀 تم تفعيل {PRODUCT_NAMES.get(pid)} بنجاح!")
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"خطأ تقني: {e}")

    return render(request, 'salesapp/activation_page.html', {'machine_id': machine_id})


# ========================================================
# 2. لوحة تحكم الاشتراك (داخل البرنامج)
# ========================================================

@login_required(login_url='login')
def subscription_dashboard(request):
    machine_id = get_machine_id()

    if request.method == 'POST':
        code = request.POST.get('license_code', '').strip()
        try:
            pid, error = _process_license_code(code, machine_id, operation_type="إضافة رصيد/باقة")
            if error:
                messages.error(request, error)
            else:
                request.session['is_licensed'] = True
                request.session['last_license_check'] = 0
                messages.success(request, f"✅ تم تحديث اشتراكك ({PRODUCT_NAMES.get(pid)}) بنجاح.")
                return redirect('subscription_dashboard')
        except Exception as e:
            messages.error(request, f"خطأ: {e}")

    # جلب البيانات المدمجة للعرض
    merged_license = ClientLicense.get_active_license()
    history_records = LicenseHistory.objects.filter(machine_id=machine_id).order_by('-archived_at')

    days_left = 0
    if merged_license and merged_license.expiry_date:
        days_left = (merged_license.expiry_date - date.today()).days
        if days_left < 0: days_left = 0

    context = {
        'machine_id': machine_id,
        'license': merged_license,
        'days_remaining': days_left,
        'history_records': history_records,
        'product_map': PRODUCT_NAMES
    }
    return render(request, 'salesapp/subscription_dashboard.html', context)