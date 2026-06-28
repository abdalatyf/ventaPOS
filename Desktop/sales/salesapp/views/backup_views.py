# salesapp/views/backup_views.py
# النسخ الاحتياطي والاستعادة (Backup & Restore)

import os
import sqlite3
import shutil
import tempfile

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils import timezone


@login_required(login_url='login')
def backup_dashboard(request):
    """شاشة النسخ الاحتياطي المستقلة"""
    context = {
        'page_title': 'النسخ الاحتياطي وقاعدة البيانات',
    }
    return render(request, 'salesapp/backup_dashboard.html', context)

@login_required(login_url='login')
def download_backup(request):
    """نسخ احتياطي ساخن (Hot Backup) آمن"""
    db_path = settings.DATABASES['default']['NAME']

    try:
        timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"Backup_SalesPro_{timestamp}.sqlite3"

        temp_dir = tempfile.gettempdir()
        temp_backup_path = os.path.join(temp_dir, filename)

        source_conn = sqlite3.connect(db_path, timeout=20)
        dest_conn = sqlite3.connect(temp_backup_path)

        with dest_conn:
            source_conn.backup(dest_conn, pages=100, sleep=0.01)

        dest_conn.close()
        source_conn.close()

        response = FileResponse(open(temp_backup_path, 'rb'), as_attachment=True, filename=filename)
        return response

    except Exception as e:
        return HttpResponse(f"حدث خطأ أثناء النسخ: {str(e)}", status=500)


@login_required(login_url='login')
def restore_backup(request):
    """استعادة النسخة عبر وضع 'الملف المعلق' (Pending Restore)"""
    if request.method == 'POST' and request.FILES.get('backup_file'):
        uploaded_file = request.FILES['backup_file']

        if not uploaded_file.name.endswith(('.sqlite3', '.db')):
            messages.error(request, "نوع الملف غير مدعوم.")
            return redirect('search_receipts')

        try:
            local_app_data = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
            db_dir = os.path.join(local_app_data, 'VentaPOS')

            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            pending_path = os.path.join(db_dir, 'restore_pending.bin')

            with open(pending_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            logout(request)
            messages.success(request, "تم رفع النسخة بنجاح. يرجى إغلاق البرنامج وتشغيله مرة أخرى لإتمام الاستعادة.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"فشل الرفع: {e}")

    return redirect('search_receipts')
