import os
import sys
import threading
import webview

def start_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    import django
    django.setup()
    
    from backend.wsgi import application
    import waitress
    
    print("Starting Waitress server on http://127.0.0.1:8085")
    waitress.serve(application, host='127.0.0.1', port=8085, clear_untrusted_proxy_headers=False)

if __name__ == '__main__':
    if not getattr(sys, 'frozen', False):
        base_path = os.path.dirname(os.path.abspath(__file__))
        backend_path = os.path.join(base_path, 'backend')
        sys.path.insert(0, backend_path)
    else:
        sys.path.insert(0, os.path.join(sys._MEIPASS, 'backend'))

    threading.Thread(target=start_django, daemon=True).start()
    
    webview.create_window("VentaPOS", "http://127.0.0.1:8085", width=1280, height=800)
    webview.start()
