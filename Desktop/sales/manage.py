#!/usr/bin/env python
import os
import sys
import ctypes
from pathlib import Path

def is_admin():
    """فحص هل البرنامج يعمل كمسؤول"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def protect_database_file():
    """إخفاء وحماية ملف قاعدة البيانات في المسار الجديد"""
    try:
        # تحديد المسار في AppData
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            db_path = Path(local_app_data) / 'VentaPOS' / 'system_core.bin'
            
            if db_path.exists():
                FILE_ATTRIBUTE_HIDDEN = 0x02
                FILE_ATTRIBUTE_SYSTEM = 0x04
                # تطبيق الإخفاء
                ctypes.windll.kernel32.SetFileAttributesW(str(db_path), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    except Exception as e:
        print(f"Protection Warning: {e}")

def main():
    # ---------------------------------------------------------
    # 🔴 كود إجبار الصلاحيات (Auto-Elevate)
    # ---------------------------------------------------------
    # ---------------------------------------------------------

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings') # تأكد من اسم مشروعك
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # تطبيق الحماية عند كل تشغيل
    protect_database_file()
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()