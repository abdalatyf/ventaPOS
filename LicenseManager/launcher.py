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
if not getattr(sys, 'frozen', False):
    try:
        import waitress
        import webview
        import requests
    except ImportError:
        venv_python = Path(__file__).resolve().parent.parent / 'VentaPOS_NextGen' / 'venv' / 'Scripts' / 'python.exe'
        if venv_python.exists():
            import subprocess
            sys.exit(subprocess.call([str(venv_python), *sys.argv]))

import threading
import time
import socket
import urllib.request
import webview

# Add LicenseManager root directory to sys.path so we can import core
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

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
    from core.wsgi import application
    print(f"Starting Waitress server on 127.0.0.1:{port}...")
    serve(application, host='127.0.0.1', port=port, threads=4)

def setup_database():
    import django
    from django.core.management import call_command
    django.setup()
    print("Running migrations...")
    call_command('migrate', interactive=False)

def background_init(window, port, url):
    try:
        setup_database()
    except Exception as e:
        print(f"Database setup failed: {e}")
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
                <p>حدث خطأ أثناء فحص أو ترقية قاعدة البيانات. يرجى إعادة تشغيل التطبيق أو التواصل مع الدعم الفني.</p>
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

def on_closing(*args, **kwargs):
    try:
        import ctypes
        MB_YESNO = 0x04
        MB_ICONWARNING = 0x30
        MB_RTLREADING = 0x100000
        MB_RIGHT = 0x80000
        MB_TOPMOST = 0x40000
        IDYES = 6

        flags = MB_YESNO | MB_ICONWARNING | MB_RTLREADING | MB_RIGHT | MB_TOPMOST
        res = ctypes.windll.user32.MessageBoxW(
            None,
            "هل أنت متأكد من إغلاق برنامج إدارة التراخيص والخروج؟\nتأكد من حفظ وتصدير كافة الرخص قبل الخروج.",
            "تحذير إغلاق مدير التراخيص - VentaPOS License Manager",
            flags
        )
        return res == IDYES
    except Exception as e:
        print(f"Error showing closing confirmation: {e}")
        return True

def main():
    port = get_free_port()
    url = f"http://127.0.0.1:{port}"

    print(f"Starting VentaPOS License Manager on {url}...")

    # HTML Splash screen
    splash_html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>VentaPOS License Manager</title>
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
            <h1>جاري تشغيل مدير التراخيص...</h1>
            <p>الرجاء الانتظار، يتم الآن تجهيز قاعدة البيانات والخادم</p>
        </div>
    </body>
    </html>
    """

    # Create window with splash screen html
    window = webview.create_window(
        'VentaPOS License Manager v1.0.0',
        html=splash_html,
        width=1280,
        height=800,
        min_size=(1024, 768),
        maximized=True
    )
    window.events.closing += on_closing

    # Start the init process in a background thread
    init_thread = threading.Thread(target=background_init, args=(window, port, url), daemon=True)
    init_thread.start()

    # Start PyWebView loop (blocks main thread)
    webview.start(debug=not getattr(sys, 'frozen', False))

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
