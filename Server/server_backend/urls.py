from django.contrib import admin
from django.urls import path, include  # 1. تأكد من إضافة include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 2. ربط تطبيق الـ API
    path('', include('sync_api.urls')),
    path('api/', include('api.urls')),
]