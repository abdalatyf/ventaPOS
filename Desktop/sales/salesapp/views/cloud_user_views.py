from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from salesapp.models import CloudUser, ClientLicense

def manage_cloud_users(request):
    """إدارة مستخدمي السحابة للأجهزة الفرعية (الكمبيوتر الأساسي فقط)"""
    license = ClientLicense.get_active_license()
    if not license or not license.is_online_active:
        messages.error(request, "هذه الميزة تتطلب اشتراك أونلاين فعال.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password_raw = request.POST.get('password')
        role = request.POST.get('role', 'VIEWER')
        
        if username and password_raw:
            if CloudUser.objects.filter(username=username).exists():
                messages.error(request, "اسم المستخدم موجود مسبقاً.")
            else:
                CloudUser.objects.create(
                    username=username,
                    password=make_password(password_raw),
                    role=role
                )
                messages.success(request, "تم إضافة المستخدم السحابي بنجاح.")
        return redirect('cloud_hub')
        
    # Redirect GET to cloud hub
    return redirect('cloud_hub')

def delete_cloud_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CloudUser, id=user_id)
        user.delete()
        messages.success(request, "تم حذف المستخدم بنجاح.")
    return redirect('cloud_hub')

def edit_cloud_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CloudUser, id=user_id)
        password_raw = request.POST.get('password')
        if password_raw:
            user.password = make_password(password_raw)
            user.save()
            messages.success(request, "تم تعديل كلمة المرور بنجاح.")
        else:
            messages.error(request, "يجب إدخال كلمة مرور جديدة.")
    return redirect('cloud_hub')
