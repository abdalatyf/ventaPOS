import os
import sys

# PyInstaller --windowed mode sets sys.stdout/stderr to None which breaks print()
class DummyWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()

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

from waitress import serve
from backend.wsgi import application

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
    print(f"Starting Waitress server on 127.0.0.1:{port}...")
    serve(application, host='127.0.0.1', port=port, threads=4)

def setup_database():
    import django
    from django.core.management import call_command
    django.setup()
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
        'VentaPOS NextGen',
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
    webview.start(debug=True)

if __name__ == '__main__':
    # Initialize PyInstaller multiprocessing support (required if waitress or other libs use multiprocessing)
    import multiprocessing
    multiprocessing.freeze_support()
    main()
