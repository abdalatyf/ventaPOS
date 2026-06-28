# salesapp/views/auth_views.py
# المصادقة والإعدادات العامة (Authentication & General Settings)

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import CompanySetting, ClientLicense, UsedLicense
from ..forms import UserLoginForm, EmergencyResetForm, CompanyProtectedForm, CompanyFreeForm, SetupCombinedForm
from .decorators import DEV_MASTER_KEY
from ..security_utils import get_machine_id
from ..license_validator import LicenseValidator
import hashlib

# Import for subscription handling
from .subscription_views import _process_license_code, PRODUCT_NAMES
from ..models import ClientLicense, LicenseHistory
from datetime import date
import requests
from django.conf import settings

def login_view(request):
    if request.user.is_authenticated:
        logout(request)

    # التحقق من نوع الجهاز (أساسي أم فرعي)
    from ..models import CompanySetting
    settings_obj = CompanySetting.objects.first()
    is_cloud = False
    
    if not settings_obj:
        if request.GET.get('cloud') == '1':
            is_cloud = True
        else:
            return redirect('setup_company')
    else:
        is_cloud = settings_obj.is_cloud_viewer

    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'local')
        
        if login_type == 'local':
            form = UserLoginForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                
                # إزالة أي بيانات سحابية من الجلسة (للتأكد)
                if 'is_cloud_viewer' in request.session:
                    del request.session['is_cloud_viewer']
                
                return redirect('select_branch')
            else:
                messages.error(request, "بيانات الدخول الأساسية غير صحيحة")
                
        elif login_type == 'cloud':
            cloud_username_full = request.POST.get('cloud_username_full', '')
            cloud_password = request.POST.get('cloud_password', '')
            
            if '-' in cloud_username_full:
                company_code, cloud_username = cloud_username_full.split('-', 1)
            else:
                company_code = ''
                cloud_username = cloud_username_full
            
            server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
            
            try:
                # 1. الاتصال بالسيرفر المركزي
                resp = requests.post(f"{server_url}/api/v1/auth/viewer/", json={
                    'company_code': company_code,
                    'username': cloud_username,
                    'password_hash': hashlib.sha256(cloud_password.encode()).hexdigest()
                }, timeout=10)
                
                data = resp.json()
                
                if resp.status_code == 200 and data.get('status') == 'success':
                    # الدخول ناجح من السيرفر
                    # 2. إنشاء مستخدم وهمي محلي للـ Session إذا لم يكن موجود
                    cloud_django_user, created = User.objects.get_or_create(username='_cloud_viewer_')
                    if created:
                        cloud_django_user.set_unusable_password()
                        cloud_django_user.save()
                        
                    login(request, cloud_django_user)
                    
                    # 3. حفظ بيانات الجلسة السحابية
                    request.session['is_cloud_viewer'] = True
                    request.session['cloud_master_machine_id'] = data.get('master_machine_id')
                    request.session['cloud_username'] = data['user']['username']
                    request.session['cloud_role'] = data['user']['role']
                    request.session['cloud_local_id'] = data['user']['local_id']
                    request.session['cloud_company_code'] = company_code
                    
                    messages.success(request, f"مرحباً {cloud_username}! تم الاتصال بالسحابة بنجاح.")
                    
                    # ملاحظة: هنا يجب أن نوجهه لشاشة جلب البيانات الأولية (Initial Sync) إذا كانت أول مرة
                    if not CompanySetting.objects.exists():
                        return redirect('cloud_initial_sync')
                    return redirect('select_branch')
                else:
                    messages.error(request, data.get('message', 'فشل الاتصال بالسحابة'))
            except requests.exceptions.RequestException:
                messages.error(request, "لا يمكن الاتصال بالسيرفر السحابي. تأكد من اتصال الإنترنت.")

    else:
        form = UserLoginForm()
    return render(request, 'salesapp/login.html', {'form': form, 'is_cloud': is_cloud})


def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    return redirect('login')


def emergency_reset_view(request):
    """صفحة الطوارئ لاستعادة الباسورد بالكود الماستر"""
    if request.method == 'POST':
        form = EmergencyResetForm(request.POST)
        if form.is_valid():
            key = form.cleaned_data['master_key']
            new_username = form.cleaned_data['new_username']
            new_pass = form.cleaned_data['new_password']

            if key == DEV_MASTER_KEY:
                # Fallback for dev only
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    admin_user.username = new_username
                    admin_user.set_password(new_pass)
                    admin_user.save()
                    update_session_auth_hash(request, admin_user)
                    messages.success(request, f"تمت إعادة تعيين كلمة المرور بنجاح للمستخدم: {admin_user.username}!")
                    return redirect('login')
            else:
                machine_id = get_machine_id()
                code_hash = hashlib.sha256(key.encode()).hexdigest()
                
                if UsedLicense.objects.filter(code_hash=code_hash).exists():
                    messages.error(request, "عفواً، لقد تم استخدام كود الطوارئ هذا من قبل.")
                    return redirect('emergency_reset')

                result = LicenseValidator.validate(key, machine_id)
                if result['valid'] and result['product_id'] == 16:
                    UsedLicense.objects.create(code_hash=code_hash)
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        admin_user.username = new_username
                        admin_user.set_password(new_pass)
                        admin_user.save()
                        update_session_auth_hash(request, admin_user)
                        messages.success(request, f"تم تغيير اسم المستخدم وكلمة المرور بنجاح للمدير: {admin_user.username} باستخدام كود الطوارئ!")
                        return redirect('login')
                else:
                    messages.error(request, "كود الطوارئ غير صحيح أو غير مخصص لهذه العملية.")
    else:
        form = EmergencyResetForm()

    return render(request, 'salesapp/emergency_reset.html', {'form': form})


def setup_company(request):
    if CompanySetting.objects.exists():
        return redirect('login')

    if request.method == 'POST':
        form = SetupCombinedForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.description = "مفروشات - ادوات منزلية - اجهزة كهربائية"
            company.footer_text = "رجاء الاحتفاظ بهذا الايصال"
            company.save()
            
            branch_name = form.cleaned_data['branch_name']
            from ..models import Branch
            Branch.objects.create(name=branch_name)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
            else:
                user = User.objects.create_superuser(username=username, email='', password=password)

            login(request, user)
            messages.success(request, "تم إعداد النظام بنجاح! أهلاً بك.")
            return redirect('select_branch')
    else:
        form = SetupCombinedForm()

    return render(request, 'salesapp/setup_company.html', {'form': form})


@login_required(login_url='login')
def general_settings(request):
    company_setting = CompanySetting.objects.first()

    protected_form = CompanyProtectedForm(instance=company_setting)
    free_form = CompanyFreeForm(instance=company_setting)
    password_form = PasswordChangeForm(request.user)

    for field in protected_form.fields.values():
        field.widget.attrs.update({
            'readonly': 'readonly',
            'style': 'background-color: #e9ecef; cursor: not-allowed;'
        })

    if request.method == 'POST':
        if 'save_protected_settings' in request.POST:
            code = request.POST.get('emergency_code', '').strip()
            if code == DEV_MASTER_KEY:
                pass
            else:
                machine_id = get_machine_id()
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                if UsedLicense.objects.filter(code_hash=code_hash).exists():
                    messages.error(request, "هذا الكود مستخدم من قبل.")
                    return redirect('general_settings')
                
                result = LicenseValidator.validate(code, machine_id)
                if not result['valid'] or result['product_id'] != 16:
                    messages.error(request, "كود صلاحية التعديل غير صحيح أو غير مخصص لهذه العملية.")
                    return redirect('general_settings')
                
                UsedLicense.objects.create(code_hash=code_hash)

            protected_form = CompanyProtectedForm(request.POST, instance=company_setting)
            if protected_form.is_valid():
                protected_form.save()
                messages.success(request, "تم تحديث البيانات الأساسية للشركة بنجاح.")
                return redirect('general_settings')
            else:
                messages.error(request, "يوجد خطأ في البيانات الأساسية.")

        elif 'save_free_settings' in request.POST:
            free_form = CompanyFreeForm(request.POST, instance=company_setting)
            if free_form.is_valid():
                free_form.save()
                messages.success(request, "تم تحديث البيانات الإضافية (الوصف والفوتر) بنجاح.")
                return redirect('general_settings')
            else:
                messages.error(request, "يوجد خطأ في البيانات الإضافية.")

        elif 'change_password_btn' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "تم تغيير كلمة المرور بنجاح!")
                return redirect('general_settings')
            else:
                messages.error(request, "يرجى تصحيح الأخطاء في كلمة المرور.")

        elif 'activate_license_btn' in request.POST:
            code = request.POST.get('license_code', '').strip()
            machine_id = get_machine_id()
            try:
                pid, error = _process_license_code(code, machine_id, operation_type="إضافة رصيد/باقة")
                if error:
                    messages.error(request, error)
                else:
                    request.session['is_licensed'] = True
                    request.session['last_license_check'] = 0
                    messages.success(request, f"✅ تم تحديث اشتراكك ({PRODUCT_NAMES.get(pid)}) بنجاح.")
                    return redirect('general_settings')
            except Exception as e:
                messages.error(request, f"خطأ: {e}")

    # جلب بيانات الاشتراك
    machine_id = get_machine_id()
    merged_license = ClientLicense.get_active_license()
    history_records = LicenseHistory.objects.filter(machine_id=machine_id).order_by('-archived_at')
    days_left = 0
    if merged_license and merged_license.expiry_date:
        days_left = (merged_license.expiry_date - date.today()).days
        if days_left < 0: days_left = 0

    # قراءة رقم الإصدار من ملف version.txt
    version_text = "v1.0.0"
    try:
        from django.conf import settings
        import os
        version_file_path = os.path.join(settings.BASE_DIR.parent, 'version.txt')
        if os.path.exists(version_file_path):
            with open(version_file_path, 'r', encoding='utf-8') as f:
                version_text = f"v{f.read().strip()}"
    except:
        pass

    context = {
        'page_title': 'الإعدادات العامة',
        'protected_form': protected_form,
        'free_form': free_form,
        'pwd_form': password_form,
        'app_version': version_text,
        'machine_id': machine_id,
        'license': merged_license,
        'days_remaining': days_left,
        'history_records': history_records,
        'product_map': PRODUCT_NAMES,
    }
    return render(request, 'salesapp/general_settings.html', context)
