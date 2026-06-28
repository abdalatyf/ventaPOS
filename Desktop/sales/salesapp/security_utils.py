import os
import subprocess
import platform
import winreg
import ctypes

# اسم المجلد والملف في AppData
APP_FOLDER = 'VentaPOS'
LICENSE_FILE_NAME = 'license.key'

def get_appdata_path():
    """
    دالة مساعدة للوصول لمسار AppData/Local وإنشاء المجلد
    """
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return os.path.join(os.getcwd(), LICENSE_FILE_NAME)
    
    full_folder_path = os.path.join(local_app_data, APP_FOLDER)
    if not os.path.exists(full_folder_path):
        try:
            os.makedirs(full_folder_path)
        except:
            pass
            
    return os.path.join(full_folder_path, LICENSE_FILE_NAME)

def get_machine_id():
    """
    استخراج بصمة الجهاز (قوية جداً)
    """
    uuid = None
    # 1. WMIC
    try:
        cmd = "wmic csproduct get uuid"
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(cmd, startupinfo=startupinfo).decode()
        parts = output.split('\n')
        if len(parts) > 1:
            uuid = parts[1].strip()
    except:
        uuid = None

    # 2. PowerShell
    if not uuid or "Err" in uuid or uuid == "":
        try:
            cmd = ["powershell", "-Command", "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            uuid = subprocess.check_output(cmd, startupinfo=startupinfo).decode().strip()
        except:
            pass

    # 3. Registry
    if not uuid or "Err" in uuid or uuid == "":
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Cryptography")
            uuid, _ = winreg.QueryValueEx(key, "MachineGuid")
        except:
            uuid = "UNKNOWN-ID-999"

    return str(uuid).strip()

def save_license_file(code):
    """
    حفظ ملف الرخصة في المسار الآمن
    """
    file_path = get_appdata_path()
    try:
        # إزالة سمات الإخفاء مؤقتاً للكتابة
        if os.path.exists(file_path):
            ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x80)

        with open(file_path, "w", encoding='utf-8') as f:
            f.write(code.strip())
        
        # إعادة الإخفاء (Hidden + System)
        ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x02 | 0x04)
        return True
    except Exception as e:
        print(f"Error saving license: {e}")
        return False

# ========================================================
# 🔴 الحل السحري: توحيد الأسماء (Alias)
# ========================================================
# هذا السطر يجعل الدالة متاحة بالاسمين، حتى لا يحدث خطأ Import
save_license = save_license_file
import hmac
import hashlib
from .license_validator import LicenseValidator

# ==========================================
# 1. دالة الختم السري للتراخيص (الخلطة الشاملة)
# ==========================================
def generate_record_signature(expiry_date, balance, machine_id, product_id, is_active):
    # 1. استدعاء المفتاح المبعثر بأمان وقت التشغيل فقط
    SECRET_DB_KEY = LicenseValidator._get_key()
    
    # 2. معالجة التاريخ (لأن أكواد الشحن قد يكون تاريخها None)
    exp_str = str(expiry_date) if expiry_date else "None"
    
    # 3. دمج البيانات (التاريخ - الرصيد - الجهاز - نوع الباقة - حالة التفعيل)
    data_to_sign = f"{exp_str}-{balance}-{machine_id}-{product_id}-{is_active}"
    
    # 4. توليد البصمة وحمايتها
    return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()


# ==========================================
# 2. دالة الختم السري للفواتير (لمنع الإضافة اليدوية)
# ==========================================
def generate_receipt_signature(receipt_number, total_amount, sale_month, sale_year):
    # نستخدم نفس المفتاح السري المبعثر
    SECRET_DB_KEY = LicenseValidator._get_key()
    
    # دمج بيانات الفاتورة الأساسية
    data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
    
    # توليد البصمة
    return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()