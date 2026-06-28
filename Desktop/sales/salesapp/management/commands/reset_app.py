import os
import shutil
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = 'Completely wipes the SalesApp installation data to return to Day 1 (Factory Reset).'

    def handle(self, *args, **kwargs):
        # طباعة تحذير باللون الأحمر
        self.stdout.write(self.style.ERROR("=" * 50))
        self.stdout.write(self.style.ERROR("⚠️  WARNING: COMPLETE FACTORY RESET ⚠️"))
        self.stdout.write(self.style.ERROR("=" * 50))
        self.stdout.write("This will delete ALL data, including:")
        self.stdout.write(" - All Receipts, Inventory, and Customers")
        self.stdout.write(" - All User Accounts and Passwords")
        self.stdout.write(" - Your License Activation (You will need to re-enter your code)")
        self.stdout.write(" - All PDF Invoices generated in the 'Invoices' folder")
        self.stdout.write("")
        
        # طلب التأكيد من المستخدم
        confirm = input("Are you ABSOLUTELY sure you want to proceed? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            self.stdout.write(self.style.SUCCESS("Reset cancelled. No data was deleted."))
            return

        deleted_count = 0

        # 1. إغلاق اتصال قاعدة البيانات الحالي حتى يسمح الويندوز بحذف الملف
        connection.close()

        # 2. تحديد مسار AppData (لنسخة الديسكتوب المشفرة)
        LOCAL_APP_DATA = os.environ.get('LOCALAPPDATA')
        if not LOCAL_APP_DATA:
            LOCAL_APP_DATA = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')

        BASE_DB_FOLDER = os.path.join(LOCAL_APP_DATA, 'VentaPOS')

        files_to_delete = [
            'business_data.enc', 'business_data.bin', 'business_data.bin.bak',
            'system_licensing.enc', 'system_licensing.bin', 'system_licensing.bin.bak',
            'system_core.bin', 'restore_pending.bin', 'license.key'
        ]

        # 3. حذف قاعدة البيانات المحلية (db.sqlite3) الخاصة ببيئة التطوير
        local_db = settings.DATABASES['default'].get('NAME')
        if local_db and os.path.exists(local_db):
            try:
                os.remove(local_db)
                self.stdout.write(self.style.SUCCESS(f"  [DELETED] Local DB: {os.path.basename(local_db)}"))
                deleted_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  [ERROR] Failed to delete local DB: {e}"))

        # 4. حذف بيانات الـ AppData الخاصة بنسخة الإنتاج (Production)
        if os.path.exists(BASE_DB_FOLDER):
            self.stdout.write(f"\nScanning secure folder: {BASE_DB_FOLDER}...")
            for filename in files_to_delete:
                file_path = os.path.join(BASE_DB_FOLDER, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.stdout.write(self.style.SUCCESS(f"  [DELETED] {filename}"))
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  [ERROR] Failed to delete {filename}: {e}"))
            
            # محاولة حذف المجلد نفسه إذا كان فارغاً
            try:
                os.rmdir(BASE_DB_FOLDER)
                self.stdout.write(self.style.SUCCESS(f"  [DELETED] Secure Folder Removed."))
            except OSError:
                pass 
        else:
            self.stdout.write("\nNo secure folder found. The production system appears to be clean.")

        # 5. تنظيف ملفات الذاكرة المؤقتة (Temp Runtime Files)
        temp_dir = tempfile.gettempdir()
        self.stdout.write(f"\nScanning temp folder: {temp_dir}...")
        temp_files_to_delete = [
            '~sys_runtime_cache_v1.tmp', '~sys_runtime_cache_v1.tmp-wal', '~sys_runtime_cache_v1.tmp-shm',
            '~sys_lic_runtime.tmp', '~sys_lic_runtime.tmp-wal', '~sys_lic_runtime.tmp-shm',
        ]
        for filename in temp_files_to_delete:
            file_path = os.path.join(temp_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.stdout.write(self.style.SUCCESS(f"  [DELETED] {filename}"))
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  [ERROR] Failed to delete {filename}: {e}"))

        # 6. تنظيف مجلد الفواتير (Invoices) لتوفير المساحة
        invoices_dir = os.path.join(settings.BASE_DIR, 'Invoices')
        if os.path.exists(invoices_dir):
            self.stdout.write(f"\nScanning Invoices folder: {invoices_dir}...")
            for f in os.listdir(invoices_dir):
                file_path = os.path.join(invoices_dir, f)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception:
                        pass
            self.stdout.write(self.style.SUCCESS("  [CLEARED] Invoices Directory emptied."))

        # 7. الخاتمة والنتائج
        self.stdout.write("\n" + "=" * 50)
        if deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Reset Successful! Deleted {deleted_count} files."))
            self.stdout.write(self.style.WARNING("The app is now completely empty. Please run 'python manage.py migrate' to build a fresh database."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Finished. No files needed deletion."))
        self.stdout.write("=" * 50)