import requests
from django.shortcuts import render, redirect , get_object_or_404
from django.db.models import Sum, Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Client, License
from .forms import ClientForm, LicenseForm
from .utils.crypto import LicenseGenerator

# 1. نظام الحماية البسيط (Check Session)
def is_authenticated(request):
    return request.session.get('is_logged_in', False)

# 2. صفحة الدخول (Login)
def login_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if password == settings.MASTER_PASSWORD:
            request.session['is_logged_in'] = True
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'كلمة المرور غير صحيحة'})
    
    # لو هو أصلاً مسجل دخول، حوله للداشبورد
    if is_authenticated(request):
        return redirect('dashboard')
        
    return render(request, 'login.html')

# 3. صفحة الخروج
def logout_view(request):
    request.session['is_logged_in'] = False
    return redirect('login')

def dashboard_view(request):
    if not is_authenticated(request):
        return redirect('login')

    # --- الإحصائيات العامة ---
    total_clients = Client.objects.count()
    active_licenses = License.objects.filter(is_active=True).count()
    total_revenue = License.objects.aggregate(Sum('price'))['price__sum'] or 0

    # --- إحصائيات الشهر الحالي ---
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    new_clients_this_month = Client.objects.filter(created_at__gte=current_month_start).count()
    licenses_this_month = License.objects.filter(created_at__gte=current_month_start)
    revenue_this_month = licenses_this_month.aggregate(Sum('price'))['price__sum'] or 0
    licenses_count_this_month = licenses_this_month.count()

    # --- منطق "الاشتراكات التي ستنتهي قريباً" ---
    expiring_soon_list = []
    licenses = License.objects.filter(is_active=True).select_related('client')
    
    for lic in licenses:
        end_date = lic.get_expiry_date()
        if not end_date:
            continue
            
        days_left = (end_date - today).days
        
        if 0 <= days_left <= 30:
            expiring_soon_list.append({
                'client_name': lic.client.name,
                'phone': lic.client.phone,
                'days_left': days_left,
                'end_date': end_date
            })

    context = {
        'total_clients': total_clients,
        'active_licenses': active_licenses,
        'total_revenue': total_revenue,
        'new_clients_this_month': new_clients_this_month,
        'revenue_this_month': revenue_this_month,
        'licenses_count_this_month': licenses_count_this_month,
        'expiring_soon': expiring_soon_list,
        'recent_licenses': License.objects.order_by('-created_at')[:5]
    }
    return render(request, 'dashboard.html', context)   

# 5. إضافة عميل جديد
def add_client_view(request):
    if not is_authenticated(request):
        return redirect('login')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            # بعد الحفظ، نذهب لصفحة إصدار رخصة فوراً لتسهيل العمل
            return redirect('add_license')
    else:
        form = ClientForm()

    return render(request, 'add_client.html', {'form': form})

def register_license_in_supabase(client, product_id, start_date, price, generated_code, notes=""):
    """
    Mandatory append-only cloud registration of generated licenses in Supabase.
    Enforces fail-closed rule: offline key generation is strictly blocked.
    """
    supabase_url = getattr(settings, 'SUPABASE_URL', '').rstrip('/')
    supabase_key = getattr(settings, 'SUPABASE_KEY', '').strip()
    marketeer_id = getattr(settings, 'MARKETEER_ID', '').strip() or "default_marketeer"

    if not supabase_key:
        return False, "مفتاح الربط السحابي (SUPABASE_KEY) غير معين في الإعدادات. يمنع إصدار الرخص أوفلاين لحماية النظام."

    endpoint = f"{supabase_url}/rest/v1/licenses"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    product_name = dict(License.PRODUCT_CHOICES).get(product_id, str(product_id))

    # Expiry calculation matching License model
    duration_map = {
        1: 60, 2: 365, 4: 365, 8: 365, 
        5: 365*3, 6: 365*5, 9: 365*5,
        3: 365*99, 7: 365*99
    }
    expiry_date_str = None
    if product_id not in [3, 7, 16] and not (10 <= product_id <= 15):
        days = duration_map.get(product_id, 0)
        if days > 0:
            expiry_date_str = (start_date + timedelta(days=days)).isoformat()

    payload = {
        "marketeer_id": marketeer_id,
        "client_name": client.name,
        "client_phone": client.phone,
        "store_name": client.store_name or "",
        "machine_id": client.machine_id,
        "product_id": product_id,
        "product_name": product_name,
        "license_code": generated_code,
        "price": price,
        "start_date": start_date.isoformat(),
        "expiry_date": expiry_date_str,
        "created_at": timezone.now().isoformat()
    }

    try:
        res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if res.status_code in (200, 201, 204):
            return True, None
        return False, f"رفض خادم Supabase تسجيل الترخيص ({res.status_code}): {res.text}"
    except requests.RequestException as e:
        return False, f"فشل الاتصال بخادم التراخيص السحابي: {str(e)}. يمنع إصدار وتوليد الرخص في وضع عدم الاتصال (Offline)."


def add_license_view(request):
    if not is_authenticated(request):
        return redirect('login')

    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data['client']
            # 1. Reject banned clients
            if client.is_banned:
                form.add_error(None, 'هذا العميل محظور من إصدار الرخص (Blacklisted). يرجى إلغاء الحظر أولاً إذا كان مصرحاً.')
                return render(request, 'add_license.html', {'form': form})

            product_id = form.cleaned_data['product_id']
            start_date = form.cleaned_data['start_date']
            price = form.cleaned_data['price']
            notes = form.cleaned_data.get('notes', '')

            # 2. Pre-generate code
            generated_code = LicenseGenerator.generate(
                machine_id=client.machine_id,
                product_id=product_id,
                start_date=start_date
            )

            # 3. Mandatory Supabase cloud registration (Fail-Closed)
            success, err_msg = register_license_in_supabase(
                client=client,
                product_id=product_id,
                start_date=start_date,
                price=price,
                generated_code=generated_code,
                notes=notes
            )

            if not success:
                form.add_error(None, f"فشل تسجيل الترخيص سحابياً على Supabase: {err_msg}")
                return render(request, 'add_license.html', {'form': form})

            # 4. Save to local SQLite database only upon cloud success
            license_obj = form.save(commit=False)
            license_obj.generated_code = generated_code
            license_obj.save()
            return redirect('license_success', license_id=license_obj.id)
    else:
        form = LicenseForm(initial={'price': 2000})

    return render(request, 'add_license.html', {'form': form})

# --- دالة جديدة: شاشة النجاح وتفاصيل الكود ---
def license_success_view(request, license_id):
    if not is_authenticated(request):
        return redirect('login')
        
    license_obj = get_object_or_404(License, id=license_id)
    
    expiry_date = license_obj.get_expiry_date()
    is_lifetime = license_obj.is_lifetime
    date_str = license_obj.get_whatsapp_date_str()

    whatsapp_msg = (
        f"مرحباً {license_obj.client.name}،%0A"
        f"شكراً لاشتراكك في برنامج VentaPOS!%0A%0A"
        f"📦 الباقة: {license_obj.get_product_id_display()}%0A"
        f"🔑 كود التفعيل: {license_obj.generated_code}%0A"
        f"📅 تاريخ الانتهاء: {date_str}%0A%0A"
        f"📌 خطوات التفعيل السريعة:%0A"
        f"1. افتح البرنامج وتوجه إلى: الإعدادات ⚙️ ⬅️ تبويب الاشتراك.%0A"
        f"2. الصق أو اكتب كود التفعيل في خانة 'كود التفعيل'.%0A"
        f"3. اضغط على زر 'تفعيل البرنامج'.%0A%0A"
        f"نتمنى لك تجارة رابحة وتجربة ممتازة!"
    )

    context = {
        'license': license_obj,
        'expiry_date': expiry_date,
        'is_lifetime': is_lifetime,
        'whatsapp_msg': whatsapp_msg
    }
    return render(request, 'license_success.html', context)

# ----------------- Management Views -----------------

def clients_list_view(request):
    if not is_authenticated(request):
        return redirect('login')
        
    query = request.GET.get('q', '')
    if query:
        clients = Client.objects.filter(
            Q(name__icontains=query) | 
            Q(phone__icontains=query) | 
            Q(machine_id__icontains=query)
        ).order_by('-created_at')
    else:
        clients = Client.objects.all().order_by('-created_at')
        
    return render(request, 'clients_list.html', {'clients': clients})

def delete_client_view(request, client_id):
    if not is_authenticated(request):
        return redirect('login')
        
    if request.method == 'POST':
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        
    return redirect('clients_list')

def licenses_list_view(request):
    if not is_authenticated(request):
        return redirect('login')
        
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    licenses = License.objects.select_related('client').all().order_by('-created_at')
    
    if query:
        licenses = licenses.filter(
            Q(client__name__icontains=query) | 
            Q(generated_code__icontains=query)
        )
        
    if status_filter == 'active':
        licenses = licenses.filter(is_active=True)
    elif status_filter == 'inactive':
        licenses = licenses.filter(is_active=False)
        
    return render(request, 'licenses_list.html', {'licenses': licenses})

def delete_license_view(request, license_id):
    if not is_authenticated(request):
        return redirect('login')
        
    if request.method == 'POST':
        lic = get_object_or_404(License, id=license_id)
        lic.delete()
        
    return redirect('licenses_list')
