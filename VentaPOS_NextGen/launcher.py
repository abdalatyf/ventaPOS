import os
import sys
from pathlib import Path

# PyInstaller --windowed mode sets sys.stdout/stderr to None which breaks print()
class DummyWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()

# Re-exec with virtual environment python if running in dev under global python
if not getattr(sys, 'frozen', False) and sys.prefix == sys.base_prefix:
    venv_python = Path(__file__).resolve().parent / 'venv' / 'Scripts' / 'python.exe'
    if venv_python.exists():
        import subprocess
        sys.exit(subprocess.call([str(venv_python), *sys.argv]))

import threading
import time
import socket
import urllib.request
import webview

# Add backend directory to sys.path so we can import the wsgi application
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def start_server(port):
    from waitress import serve
    from backend.wsgi import application
    print(f"Starting Waitress server on 127.0.0.1:{port}...")
    serve(application, host='127.0.0.1', port=port, threads=4)

def check_pending_restore():
    """
    Checks for restore_pending.bin staged by BackupUploadView and applies it before database initialization.
    """
    try:
        from django.conf import settings
        from pathlib import Path
        import shutil
        db_path = Path(settings.DATABASES['default']['NAME'])
        pending_path = db_path.parent / 'restore_pending.bin'
        if pending_path.exists():
            print("Applying pending database restore...")
            wal_file = Path(str(db_path) + '-wal')
            shm_file = Path(str(db_path) + '-shm')
            if wal_file.exists():
                wal_file.unlink(missing_ok=True)
            if shm_file.exists():
                shm_file.unlink(missing_ok=True)
            shutil.copy2(pending_path, db_path)
            pending_path.unlink(missing_ok=True)
            print("Pending database restore applied successfully.")
    except Exception as e:
        print(f"Error checking pending restore: {e}")

def setup_database():
    import django
    from django.core.management import call_command
    from django.conf import settings
    from pathlib import Path
    import sqlite3
    from datetime import datetime

    check_pending_restore()
    django.setup()

    # Pre-migration backup
    try:
        db_path = Path(settings.DATABASES['default']['NAME'])
        if db_path.exists() and db_path.stat().st_size > 0:
            backups_dir = settings.DB_DIR / 'backups'
            backups_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backups_dir / f"auto_backup_{timestamp}.sqlite3"
            
            src = sqlite3.connect(str(db_path))
            dst = sqlite3.connect(str(backup_file))
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            print(f"Pre-migration backup created: {backup_file.name}")

            # Retain only the latest 10 auto_backup_*.sqlite3 files
            auto_backups = sorted(backups_dir.glob("auto_backup_*.sqlite3"), key=lambda p: p.stat().st_mtime)
            if len(auto_backups) > 10:
                for old_b in auto_backups[:-10]:
                    old_b.unlink(missing_ok=True)
    except Exception as b_err:
        print(f"Warning creating pre-migration backup: {b_err}")

    print("Running migrations...")
    call_command('migrate', interactive=False)
    print("Checking demo initialization...")
    call_command('init_demo_db')

def background_init(window, port, url):
    # Ensure DB is ready before starting the server
    try:
        setup_database()
    except Exception as e:
        print(f"Database setup failed: {e}")
        # Roll back to latest auto_backup_*.sqlite3 in DB_DIR / 'backups' if available
        try:
            from django.conf import settings
            import shutil
            from pathlib import Path
            backups_dir = settings.DB_DIR / 'backups'
            auto_backups = sorted(backups_dir.glob("auto_backup_*.sqlite3"), key=lambda p: p.stat().st_mtime)
            if auto_backups:
                latest_backup = auto_backups[-1]
                db_path = Path(settings.DATABASES['default']['NAME'])
                shutil.copy2(latest_backup, db_path)
                wal_file = Path(str(db_path) + '-wal')
                shm_file = Path(str(db_path) + '-shm')
                if wal_file.exists():
                    wal_file.unlink(missing_ok=True)
                if shm_file.exists():
                    shm_file.unlink(missing_ok=True)
                print(f"Rolled back database to: {latest_backup.name}")
        except Exception as rb_err:
            print(f"Rollback failed: {rb_err}")

        # Halt startup with an informative splash screen instead of launching Waitress
        error_html = f'''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>خطأ في تشغيل النظام</title>
            <style>
                body {{ margin: 0; padding: 20px; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .card {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 600px; text-align: center; }}
                h1 {{ color: #d63939; margin-bottom: 15px; }}
                p {{ color: #495057; line-height: 1.6; font-size: 1.1rem; }}
                .err {{ background: #f1f3f5; padding: 10px; border-radius: 4px; font-family: monospace; direction: ltr; font-size: 0.9rem; color: #c92a2a; margin-top: 15px; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>تعذر تشغيل قاعدة البيانات</h1>
                <p>حدث خطأ أثناء فحص أو ترقية قاعدة البيانات. تم محاولة التراجع للنسخة الاحتياطية الأخيرة. يرجى إعادة تشغيل التطبيق أو التواصل مع الدعم الفني.</p>
                <div class="err">{str(e)}</div>
            </div>
        </body>
        </html>
        '''
        window.load_html(error_html)
        return

    # Start Django server via Waitress in a background thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    print("Waiting for server to be ready...")
    if wait_for_server(url):
        print("Server is ready, redirecting PyWebView...")
        window.load_url(url)
    else:
        window.load_html('<h1 style="color:red; text-align:center; margin-top:20%; font-family:sans-serif;">فشل تشغيل الخادم. يرجى مراجعة سجلات النظام.</h1>')

def main():
    port = get_free_port()
    url = f"http://127.0.0.1:{port}"

    print(f"Starting VentaPOS on {url}...")

    # HTML Splash screen
    splash_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>VentaPOS NextGen</title>
        <style>
            body { margin: 0; padding: 0; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .container { text-align: center; }
            .spinner { border: 8px solid #e9ecef; border-top: 8px solid #123F68; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 0 auto 20px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            h1 { color: #123F68; margin-bottom: 10px; }
            p { color: #6c757d; font-size: 1.1rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h1>جاري تشغيل النظام...</h1>
            <p>الرجاء الانتظار، يتم الآن تجهيز قاعدة البيانات والخادم</p>
        </div>
    </body>
    </html>
    """

    # Create window with splash screen html
    window = webview.create_window(
        'VentaPOS NextGen v1.0.0',
        html=splash_html,
        width=1280,
        height=800,
        min_size=(1024, 768),
        maximized=True
    )

    # Start the init process in a background thread
    init_thread = threading.Thread(target=background_init, args=(window, port, url), daemon=True)
    init_thread.start()

    # Start PyWebView loop (blocks main thread)
    webview.start(debug=not getattr(sys, 'frozen', False))

if __name__ == '__main__':
    # Initialize PyInstaller multiprocessing support (required if waitress or other libs use multiprocessing)
    import multiprocessing
    multiprocessing.freeze_support()
    main()
