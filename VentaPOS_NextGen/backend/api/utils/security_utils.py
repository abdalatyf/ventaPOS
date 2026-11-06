import os
import platform
import hashlib
import hmac
from .license_validator import LicenseValidator

def get_machine_id():
    """
    استخراج بصمة الجهاز الثابتة من سجل النظام (Windows Registry MachineGuid)
    """
    guid = None
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
    except Exception:
        pass

    if not guid:
        guid = platform.node() or "UNKNOWN-PC-001"

    return hashlib.sha256(str(guid).strip().encode('utf-8')).hexdigest()[:32]

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
            formatted_items = []
            for item in items_data:
                if isinstance(item, dict):
                    raw_id = item.get('inventory_item_id', item.get('inventory_item', ''))
                    qty = item.get('quantity', '')
                else:
                    raw_id = getattr(item, 'inventory_item_id', getattr(item, 'inventory_item', ''))
                    qty = getattr(item, 'quantity', '')
                item_id = getattr(raw_id, 'id', getattr(raw_id, 'pk', raw_id))
                formatted_items.append(f"{item_id}:{qty}")
            formatted_items.sort()
            items_str = "-".join(formatted_items)
            data_to_sign += f"-ITEMS[{items_str}]"
        except Exception:
            pass
            
    # توليد البصمة
    return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
