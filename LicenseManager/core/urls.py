from django.contrib import admin
from django.urls import path
from licenses import views  # استيراد ملف الفيو الجديد

urlpatterns = [
    path('admin/', admin.site.urls), # اترك القديم للطوارئ
    path('', views.login_view, name='login'), # الصفحة الرئيسية هي الدخول
    path('dashboard/', views.dashboard_view, name='dashboard'), # لوحة الإحصائيات
    # الروابط الجديدة
    path('clients/', views.clients_list_view, name='clients_list'),
    path('clients/delete/<int:client_id>/', views.delete_client_view, name='delete_client'),
    path('clients/add/', views.add_client_view, name='add_client'),
    path('licenses/', views.licenses_list_view, name='licenses_list'),
    path('licenses/delete/<int:license_id>/', views.delete_license_view, name='delete_license'),
    path('licenses/add/', views.add_license_view, name='add_license'),
    path('licenses/success/<int:license_id>/', views.license_success_view, name='license_success'),
    path('logout/', views.logout_view, name='logout'),
]