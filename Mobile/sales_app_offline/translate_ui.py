import os
import re

SCREENS_DIR = r"D:\Projects\VentaPOS\Mobile\sales_app_offline\lib\screens"

TRANSLATIONS = {
    # AppBars and Titles
    r"'VentaPOS Mobile'": r"'فينتا-پوس موبايل'",
    r"'Manage Products'": r"'إدارة المنتجات'",
    r"'Select Mode'": r"'اختيار وضع التشغيل'",
    r"'Offline Setup'": r"'إعداد وضع الأوفلاين'",
    r"'Print Invoice'": r"'طباعة الفاتورة'",
    r"'Sync Hub'": r"'مركز المزامنة'",
    r"'Manage Users'": r"'إدارة المستخدمين'",
    r"'Manage Branches'": r"'إدارة الفروع'",
    r"'Manage Suppliers'": r"'إدارة الموردين'",
    r"'Purchase Invoices'": r"'فواتير المشتريات'",
    r"'Product Ledger'": r"'حركة المنتج'",
    r"'Sales Reports'": r"'تقارير المبيعات'",
    r"'Dashboard'": r"'لوحة التحكم'",

    # Common Buttons and Labels
    r"'SYNC NOW'": r"'بدء المزامنة الآن'",
    r"'Total Pending Items: ": r"'إجمالي العناصر المعلقة: ",
    r"'Branch: ": r"'الفرع: ",
    r"'CloudUser: ": r"'المستخدم السحابي: ",
    r"'Cancel'": r"'إلغاء'",
    r"'Add Override'": r"'إضافة تسوية'",
    r"'Add Product'": r"'إضافة منتج'",
    r"'Add Branch'": r"'إضافة فرع'",
    r"'Add Supplier'": r"'إضافة مورد'",
    r"'Add User'": r"'إضافة مستخدم'",
    r"'Add Invoice'": r"'إضافة فاتورة'",
    r"'Save'": r"'حفظ'",
    r"'Close'": r"'إغلاق'",

    # Table Headers
    r"Text\('ID'\)": r"Text('الرقم')",
    r"Text\('Name'\)": r"Text('الاسم')",
    r"Text\('Qty'\)": r"Text('الكمية')",
    r"Text\('Price'\)": r"Text('السعر')",
    r"Text\('Commission'\)": r"Text('العمولة')",
    r"Text\('Actions'\)": r"Text('إجراءات')",
    r"Text\('Phone'\)": r"Text('الهاتف')",
    r"Text\('Address'\)": r"Text('العنوان')",
    r"Text\('Date'\)": r"Text('التاريخ')",
    r"Text\('Type'\)": r"Text('النوع')",

    # Roles and Dropdowns
    r"'Salespersons'": r"'المندوبين'",
    r"'Cloud Users'": r"'المستخدمين السحابيين'",
    r"Text\('VIEWER'\)": r"Text('مراقب')",
    r"Text\('CASHIER'\)": r"Text('كاشير')",

    # Login and setup
    r"'Online Mode'": r"'وضع الأونلاين (سحابي)'",
    r"'Offline Mode'": r"'وضع الأوفلاين (محلي)'",
    r"'Placeholder for Offline Setup'": r"'واجهة إعداد قاعدة البيانات محلياً (قيد التطوير)'",
    
    # Placeholders
    r"Text\('Manage Branches'\)": r"Text('إدارة الفروع')",
    r"Text\('Manage Suppliers'\)": r"Text('إدارة الموردين')",
    r"Text\('Manage Users'\)": r"Text('إدارة المستخدمين')",
}

def translate_files():
    for filename in os.listdir(SCREENS_DIR):
        if not filename.endswith('.dart'):
            continue
            
        filepath = os.path.join(SCREENS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        for eng, ar in TRANSLATIONS.items():
            content = re.sub(eng, ar, content)
            
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Translated strings in: {filename}")
        else:
            print(f"ℹ️ No changes needed in: {filename}")

if __name__ == '__main__':
    translate_files()
