import os
import sys
import threading
import time
import shutil
import socket
import tempfile
import webview
from cryptography.fernet import Fernet
from waitress import serve
from django.core.management import call_command
from sales.wsgi import application
from django.db import connections

# إصلاح Unicode على Windows (يمنع UnicodeEncodeError في الـ console)
import os
import sys
import threading
import time
import shutil
import socket
import tempfile
import webview
from cryptography.fernet import Fernet
from waitress import serve
from django.core.management import call_command
from sales.wsgi import application
from django.db import connections 

# =========================================================
# 🔕 كاتم صوت لأخطاء الكروميوم ولغة العربية في الكونسول المخفي
# =========================================================
class DummyConsole:
    def __init__(self, original):
        self.original = original

    def write(self, text):
        try:
            # نحاول الطباعة العادية، وإذا فشلت بسبب ترميز الويندوز، نتجاهل الخطأ تماماً
            if "Failed to unregister class" not in str(text) and "Error = 1411" not in str(text):
                self.original.write(str(text))
        except UnicodeEncodeError:
            pass # تجاهل أخطاء اللغة العربية والرموز التعبيرية بصمت

    def flush(self):
        try:
            self.original.flush()
        except:
            pass

# إعادة توجيه كل المخرجات القياسية والأخطاء لكاتم الصوت
sys.stdout = DummyConsole(sys.stdout)
sys.stderr = DummyConsole(sys.stderr)
# =========================================================


import io
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass  # في بيئة الـ exe ممكن stdout يكون مغلق — نتجاهل بأمان 




# =========================================================
# 🔕 كاتم صوت لأخطاء Chromium المزعجة وغير الضارة
# =========================================================
class FilteredStderr(object):
    def __init__(self, target):
        self.target = target
        self.ignore_strings = [
            "Failed to unregister class Chrome_WidgetWin_0",
            "Error = 1411"
        ]

    def write(self, s):
        for ignore_str in self.ignore_strings:
            if ignore_str in s:
                return # تجاهل الرسالة ولا تطبعها
        self.target.write(s)

    def flush(self):
        self.target.flush()

# توجيه مخرجات الخطأ إلى الكاتم
sys.stderr = FilteredStderr(sys.stderr)
# =========================================================
# 🔒 إعدادات التشفير (ENCRYPTION CORE)
# =========================================================
def _get_cipher():
    """
    نفس أسلوب VALIDATOR.py — المفتاح مبعثر كأرقام وقت التشغيل فقط
    لا يظهر كـ string في الـ exe أو عند عمل strings analysis
    """
    _k = [87, 122, 45, 120, 82, 57, 111, 68, 55, 76, 113, 106, 50, 99, 95,
          89, 49, 118, 65, 52, 110, 66, 56, 101, 70, 53, 116, 72, 48, 109,
          75, 51, 112, 81, 54, 115, 86, 57, 119, 88, 50, 117, 73, 61]
    return Fernet(bytes(_k))

cipher_suite = _get_cipher()

# =========================================================
# 🛠️ مسارات الملفات (PATHS)
# pyinstaller --noconfirm --onedir --windowed --clean --uac-admin --icon="venta.ico" --name="VentaPOS" --add-data "salesapp/templates;salesapp/templates" --add-data "staticfiles;staticfiles" --add-data "wkhtmltox;wkhtmltox" --hidden-import="webview" --hidden-import="waitress" --hidden-import="whitenoise" --hidden-import="whitenoise.middleware" --hidden-import="django.contrib.humanize.templatetags.humanize" --hidden-import="salesapp.apps" --hidden-import="salesapp.db_router" run_app.py

# =========================================================
LOCAL_APP_DATA = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
BASE_DB_FOLDER = os.path.join(LOCAL_APP_DATA, 'VentaPOS')

# الملف القديم غير المشفر (لترحيله)
LEGACY_DB = os.path.join(BASE_DB_FOLDER, 'business_data.bin')
# الملف المشفر الجديد (الخزنة)
ENCRYPTED_DB = os.path.join(BASE_DB_FOLDER, 'business_data.enc')
# ملف التشغيل السريع في الذاكرة المؤقتة (يتم تدميره بعد الإغلاق)
RUNTIME_DB = os.path.join(tempfile.gettempdir(), '~sys_runtime_cache_v1.tmp')

RESTORE_FILE = os.path.join(BASE_DB_FOLDER, 'restore_pending.bin')

# =========================================================
# 🛡️ محرك التشفير وفك التشفير (CRYPTO ENGINE)
# =========================================================
def initialize_database_security():
    print("🛡️ جاري تهيئة الحماية وفك التشفير...")
    
    # 🔴 1. التنظيف الاستباقي (Pre-cleanup): 
    # مسح أي ملفات مؤقتة من الجلسة السابقة (قبل أن يبدأ جانجو أي اتصال)
    for ext in ['', '-wal', '-shm']:
        old_file = RUNTIME_DB + ext
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                print(f"🧹 تم تنظيف مخلفات الجلسة السابقة: {old_file}")
            except Exception as e:
                print(f"⚠️ فشل تنظيف الملف القديم (قد يكون قيد الاستخدام ببرنامج آخر): {e}")

    # 2. تشفير الداتا القديمة لو كان أول تشغيل
    if os.path.exists(LEGACY_DB) and not os.path.exists(ENCRYPTED_DB):
        print("⚠️ تم اكتشاف قاعدة بيانات غير مشفرة! جاري تشفيرها وتأمينها...")
        with open(LEGACY_DB, 'rb') as f:
            raw_data = f.read()
        encrypted_data = cipher_suite.encrypt(raw_data)
        with open(ENCRYPTED_DB, 'wb') as f:
            f.write(encrypted_data)
        os.rename(LEGACY_DB, LEGACY_DB + ".bak")

    # 3. فك التشفير ووضعه في مسار الـ Temp
    if os.path.exists(ENCRYPTED_DB):
        with open(ENCRYPTED_DB, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        with open(RUNTIME_DB, 'wb') as f:
            f.write(decrypted_data)
        print("✅ تم تجهيز بيئة التشغيل الآمنة.")
    else:
        # تأكيد إضافي لو لم يكن هناك داتا أصلية
        if os.path.exists(RUNTIME_DB):
            try: os.remove(RUNTIME_DB)
            except: pass

def _is_valid_sqlite(path):
    """التحقق من أن الملف قاعدة بيانات SQLite صالحة"""
    try:
        import sqlite3
        con = sqlite3.connect(path)
        con.execute("SELECT name FROM sqlite_master LIMIT 1")
        con.close()
        return True
    except Exception:
        return False

def _wal_checkpoint(path):
    """تفريغ WAL إلى الـ DB الأساسي قبل الحفظ — بدون ده البيانات الأخيرة تضيع"""
    try:
        import sqlite3
        con = sqlite3.connect(path)
        con.execute("PRAGMA wal_checkpoint(FULL)")
        con.close()
    except Exception as e:
        print(f"⚠️ WAL checkpoint warning: {e}")

def encrypt_and_save_db():
    """تقوم بأخذ نسخة من الـ Temp، تشفيرها، وحفظها في الخزنة بأمان تام"""
    if os.path.exists(RUNTIME_DB):
        try:
            # 🔴 صمام الأمان (Safety Check) 🔴
            # التحقق من أن الملف قاعدة بيانات SQLite صالحة وليس ملف فارغ أو تالف
            if not _is_valid_sqlite(RUNTIME_DB):
                print("⚠️ تحذير: تم إيقاف الحفظ التلقائي لأن قاعدة البيانات المؤقتة تالفة. (حماية للبيانات)")
                return

            # ✅ تفريغ WAL أولاً — بدون ده البيانات الأخيرة تضيع
            _wal_checkpoint(RUNTIME_DB)

            with open(RUNTIME_DB, 'rb') as f:
                raw_data = f.read()
            encrypted_data = cipher_suite.encrypt(raw_data)
            
            # حفظ ذري (Atomic Save) لمنع التلف لو انقطعت الكهرباء أثناء الحفظ
            temp_enc_path = ENCRYPTED_DB + ".tmp"
            with open(temp_enc_path, 'wb') as f:
                f.write(encrypted_data)
            
            # استبدال الملف القديم بالجديد بأمان
            os.replace(temp_enc_path, ENCRYPTED_DB)
            print("💾 [تم الحفظ التلقائي المشفر بنجاح]")
        except Exception as e:
            print(f"❌ خطأ أثناء الحفظ التلقائي: {e}")

def auto_save_worker():
    """Thread يعمل في الخلفية للحفظ كل 5 دقائق"""
    while True:
        time.sleep(300) # 300 ثانية = 5 دقائق
        encrypt_and_save_db()

def cleanup_on_exit():
    """تدمير الأدلة وتشفير النهائي عند إغلاق البرنامج"""
    print("🛑 جاري إغلاق النظام وتأمين البيانات...")
    
    # 1. إغلاق اتصالات جانجو قدر الإمكان
    try:
        connections.close_all() 
    except: pass
    
    # 2. أخذ اللقطة الأخيرة وتشفيرها (أهم خطوة)
    encrypt_and_save_db() 
    
    # 3. محاولة مسح سريعة واحدة (مجرد محاولة، لو فشلت سيتكفل بها التشغيل القادم)
    try:
        os.remove(RUNTIME_DB)
        os.remove(RUNTIME_DB + "-wal")
        os.remove(RUNTIME_DB + "-shm")
        print("🧹 تم تنظيف الذاكرة المؤقتة بنجاح.")
    except:
        print("⚠️ سيتم تنظيف الذاكرة المؤقتة عند التشغيل القادم.")
    
    # الإغلاق الفوري
    os._exit(0)


# =========================================================
# 🔌 PORT FINDER
# =========================================================
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# =========================================================
# 🔄 AUTO-MIGRATE & RESTORE
# =========================================================
def check_and_restore_backup():
    if os.path.exists(RESTORE_FILE):
        try:
            print("🔄 جاري استعادة النسخة الاحتياطية...")
            connections.close_all()
            time.sleep(1)
            
            # بما أن الملف المرفوع غير مشفر (مؤقتاً)، نشفره ثم نضعه في الخزنة
            with open(RESTORE_FILE, 'rb') as f:
                raw_backup = f.read()
            encrypted_backup = cipher_suite.encrypt(raw_backup)
            with open(ENCRYPTED_DB, 'wb') as f:
                f.write(encrypted_backup)
                
            os.remove(RESTORE_FILE)
            
            # نعيد فك التشفير للـ Temp لكي يبدأ البرنامج بالنسخة الجديدة
            initialize_database_security()
            
            call_command('migrate', interactive=False)
            print("✅ تمت الاستعادة بنجاح.")
        except Exception as e:
            print(f"❌ فشل الاستعادة: {e}")

def ensure_databases_are_ready():
    print("🛠️ التأكد من الجداول...")
    try:
        # 🔴 1. بناء جداول التراخيص أولاً (System DB)
        call_command('migrate', database='system', interactive=False)
        
        # 🔴 2. تشغيل المايجريشن الأساسي (والذي سيقوم بنقل وتشفير البيانات بأمان)
        call_command('migrate', interactive=False)
    except Exception as e:
        print(f"❌ Auto-Migrate Failed: {e}")

# =========================================================
# 🚀 SERVER STARTUP
# =========================================================
def start_server(port):
    print(f"🚀 بدء خادم Waitress على البورت {port}...")
    import subprocess
    import os
    adb_path = r"C:\Users\Abdo\AppData\Local\Android\Sdk\platform-tools\adb.exe"
    try:
        if os.path.exists(adb_path):
            subprocess.run([adb_path, "reverse", f"tcp:{port}", f"tcp:{port}"], check=False)
            print("🔗 تم تفعيل جسر ADB للاتصال المباشر عبر سلك الـ USB بنجاح")
    except Exception as e:
        pass
    serve(application, host='0.0.0.0', port=port, threads=6)

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
    import django
    django.setup()

    # 1. فك التشفير وتجهيز البيئة الآمنة
    initialize_database_security()
    
    # 2. الاستعادة والتحديث
    check_and_restore_backup()
    ensure_databases_are_ready()

    # 3. تشغيل الحفظ التلقائي في الخلفية (Auto-Saver)
    saver_thread = threading.Thread(target=auto_save_worker, daemon=True)
    saver_thread.start()

    # 4. تشغيل السيرفر
    ACTIVE_PORT = get_free_port()
    LOCAL_URL = f"http://127.0.0.1:{ACTIVE_PORT}"

    server_thread = threading.Thread(target=start_server, args=(ACTIVE_PORT,), daemon=True)
    server_thread.start()
    time.sleep(2)

    # 5. تشغيل واجهة المستخدم في المتصفح
    import webbrowser
    webbrowser.open(LOCAL_URL)
    print(f"🌍 تم فتح التطبيق في المتصفح الأساسي على الرابط: {LOCAL_URL}")
    print("🛑 لإغلاق السيرفر وحفظ البيانات بأمان، اضغط Ctrl+C في هذه النافذة.")
    
    try:
        # إبقاء السكريبت يعمل حتى يتدخل المستخدم
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_on_exit()