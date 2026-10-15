import os
import subprocess
import platform
import winreg
import ctypes

def get_machine_id():
    """
    استخراج بصمة الجهاز المجمعة (Motherboard + Registry + MAC)
    """
    components = []
    
    # 1. WMIC Motherboard UUID
    try:
        cmd = "wmic csproduct get uuid"
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(cmd, startupinfo=startupinfo).decode()
        parts = output.split('\n')
        if len(parts) > 1:
            mb_uuid = parts[1].strip()
            if mb_uuid and "FFFFFFFF" not in mb_uuid:
                components.append(mb_uuid)
    except:
        pass

    # 2. Registry MachineGuid
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Cryptography")
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        if machine_guid:
            components.append(machine_guid)
    except:
        pass
        
    # 3. MAC Address
    try:
        import uuid as _uuid_lib
        mac = _uuid_lib.getnode()
        components.append(str(mac))
    except:
        pass

    if not components:
        return "UNKNOWN-ID-999"
        
    raw_id = "-".join(components)
    return hashlib.sha256(raw_id.encode()).hexdigest()[:32]

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
def generate_receipt_signature(receipt_number, total_amount, sale_month, sale_year, items_data=None):
    # نستخدم نفس المفتاح السري المبعثر
    SECRET_DB_KEY = LicenseValidator._get_key()
    
    # دمج بيانات الفاتورة الأساسية
    data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
    
    if items_data:
        try:
            items_str = "-".join([
                f"{getattr(item, 'inventory_item_id', item.get('inventory_item_id', item.get('inventory_item', '')))}:{getattr(item, 'quantity', item.get('quantity', ''))}"
                for item in items_data
            ])
            data_to_sign += f"-ITEMS[{items_str}]"
        except Exception:
            pass
            
    # توليد البصمة
    return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
