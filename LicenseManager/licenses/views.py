from django.shortcuts import render, redirect , get_object_or_404
from django.db.models import Sum, Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Client, License
from .forms import ClientForm, LicenseForm

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

def add_license_view(request):
    if not is_authenticated(request):
        return redirect('login')

    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            license_obj = form.save()
            # التغيير هنا: بدلاً من الداشبورد، نذهب لصفحة النجاح مع رقم الرخصة
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
        f"شكراً لاشتراكك معنا!%0A"
        f"بيانات الترخيص الخاصة بك:%0A"
        f"📦 الباقة: {license_obj.get_product_id_display()}%0A"
        f"🔑 كود التفعيل: {license_obj.generated_code}%0A"
        f"📅 تاريخ الانتهاء: {date_str}%0A"
        f"نتمنى لك تجربة ممتعة!"
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
