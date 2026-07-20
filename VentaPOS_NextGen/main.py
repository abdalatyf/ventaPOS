import os
import sys
import threading
import time
import socket
import tempfile
import webview
from waitress import serve
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.db import connections

# =========================================================
# 🔕 Console Silence
# =========================================================
class DummyConsole:
    def __init__(self, original):
        self.original = original
    def write(self, text):
        try:
            if "Failed to unregister class" not in str(text) and "Error = 1411" not in str(text):
                self.original.write(str(text))
        except UnicodeEncodeError:
            pass
    def flush(self):
        try: self.original.flush()
        except: pass

sys.stdout = DummyConsole(sys.stdout)
sys.stderr = DummyConsole(sys.stderr)

# =========================================================
# 🔒 Encryption Settings
# =========================================================
def _get_cipher():
    _k = [87, 122, 45, 120, 82, 57, 111, 68, 55, 76, 113, 106, 50, 99, 95,
          89, 49, 118, 65, 52, 110, 66, 56, 101, 70, 53, 116, 72, 48, 109,
          75, 51, 112, 81, 54, 115, 86, 57, 119, 88, 50, 117, 73, 61]
    return Fernet(bytes(_k))

cipher_suite = _get_cipher()

# =========================================================
# 🛠️ Paths
# =========================================================
LOCAL_APP_DATA = os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
BASE_DB_FOLDER = os.path.join(LOCAL_APP_DATA, 'VentaPOS')

if not os.path.exists(BASE_DB_FOLDER):
    try: os.makedirs(BASE_DB_FOLDER)
    except: pass

ENCRYPTED_DB = os.path.join(BASE_DB_FOLDER, 'business_data.enc')
RUNTIME_DB = os.path.join(tempfile.gettempdir(), '~sys_runtime_cache_v1.tmp')

# =========================================================
# 🛡️ Security Engine
# =========================================================
def initialize_database_security():
    print("🛡️ Initializing Decryption Engine...")
    for ext in ['', '-wal', '-shm']:
        old_file = RUNTIME_DB + ext
        if os.path.exists(old_file):
            try: os.remove(old_file)
            except: pass

    if os.path.exists(ENCRYPTED_DB):
        with open(ENCRYPTED_DB, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        with open(RUNTIME_DB, 'wb') as f:
            f.write(decrypted_data)
        print("✅ Runtime DB Ready.")
    else:
        if os.path.exists(RUNTIME_DB):
            try: os.remove(RUNTIME_DB)
            except: pass

def _is_valid_sqlite(path):
    try:
        import sqlite3
        con = sqlite3.connect(path)
        con.execute("SELECT name FROM sqlite_master LIMIT 1")
        con.close()
        return True
    except Exception:
        return False

def is_demo_mode():
    if not os.path.exists(RUNTIME_DB): return True
    try:
        import sqlite3
        con = sqlite3.connect(RUNTIME_DB)
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM api_clientlicense WHERE is_active=1 AND machine_id != 'DEMO_MACHINE'")
        count = cursor.fetchone()[0]
        con.close()
        return count == 0
    except Exception:
        return True

def encrypt_and_save_db():
    # Database saving now applies to both activated and demo environments

    if os.path.exists(RUNTIME_DB):
        try:
            if not _is_valid_sqlite(RUNTIME_DB):
                print("⚠️ DB corruption detected! Auto-save aborted.")
                return

            import sqlite3
            con = sqlite3.connect(RUNTIME_DB)
            con.execute("PRAGMA wal_checkpoint(FULL)")
            con.close()

            with open(RUNTIME_DB, 'rb') as f:
                raw_data = f.read()
            encrypted_data = cipher_suite.encrypt(raw_data)
            
            temp_enc_path = ENCRYPTED_DB + ".tmp"
            with open(temp_enc_path, 'wb') as f:
                f.write(encrypted_data)
            
            os.replace(temp_enc_path, ENCRYPTED_DB)
            print("💾 [Auto-Save Successful]")
        except Exception as e:
            print(f"❌ Auto-Save Error: {e}")

def auto_save_worker():
    while True:
        time.sleep(300)
        encrypt_and_save_db()

def cleanup_on_exit():
    print("🛑 Shutting down and saving data...")
    try: connections.close_all() 
    except: pass
    encrypt_and_save_db() 
    try:
        os.remove(RUNTIME_DB)
        os.remove(RUNTIME_DB + "-wal")
        os.remove(RUNTIME_DB + "-shm")
    except: pass
    os._exit(0)

# =========================================================
# 🔌 Server Startup
# =========================================================
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def ensure_databases_are_ready():
    print("🛠️ Running Migrations...")
    try:
        call_command('migrate', interactive=False)
        
        # Populate demo data if no license exists
        if is_demo_mode():
            print("📦 Populating Demo Data...")
            call_command('init_demo_db')
            
    except Exception as e:
        print(f"❌ Migration/Init Failed: {e}")

def start_server(port, application):
    print(f"🚀 Waitress Server on Port {port}...")
    serve(application, host='127.0.0.1', port=port, threads=6)

if __name__ == '__main__':
    # Add backend folder to sys.path so django settings can be found
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    import django
    django.setup()
    from backend.wsgi import application

    initialize_database_security()
    ensure_databases_are_ready()

    saver_thread = threading.Thread(target=auto_save_worker, daemon=True)
    saver_thread.start()

    ACTIVE_PORT = get_free_port()
    # If React is in dev mode, we could point to localhost:5173, but in prod we point to django
    LOCAL_URL = f"http://127.0.0.1:{ACTIVE_PORT}/"

    server_thread = threading.Thread(target=start_server, args=(ACTIVE_PORT, application), daemon=True)
    server_thread.start()
    time.sleep(2)

    window = webview.create_window(
        'VentaPOS NextGen', 
        LOCAL_URL,
        width=1280, 
        height=800,
        resizable=True,
        confirm_close=True,
    )
    window.events.closed += cleanup_on_exit
    webview.start()
