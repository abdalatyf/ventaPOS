import os
import platform
import pdfkit
import win32print
import win32api
from django.conf import settings
from django.utils import timezone
import sys
from .models import PurchaseInvoiceItem

import glob # تأكد من وجود هذا الاستدعاء في أعلى الملف أو أضفه
    
from django.db.models import Q

def get_historical_pricing(inventory_item, target_month, target_year):
    """
    آلة الزمن: تجلب سعر الشراء وعمولة المندوب لصنف معين (InventoryItem) 
    في شهر وسنة محددين، وترجع للقيم الابتدائية إذا لم تجد فواتير سابقة.
    """
    
    latest_invoice_item = PurchaseInvoiceItem.objects.filter(
        inventory_item=inventory_item,
        invoice__invoice_type='PURCHASE' 
    ).filter(
        Q(invoice__invoice_year__lt=target_year) | 
        Q(invoice__invoice_year=target_year, invoice__invoice_month__lte=target_month)
    ).order_by(
        '-invoice__invoice_year', 
        '-invoice__invoice_month', 
        '-id'
    ).first()

    if latest_invoice_item:
        return {
            'purchase_price': latest_invoice_item.purchase_price,
            'commission': latest_invoice_item.commission_amount,
            'is_historical': True
        }
    else:
        # لم يتم شراء الصنف أبداً قبل أو خلال هذا التاريخ (مخزون قديم جداً)
        return {
            'purchase_price': inventory_item.initial_purchase_price,
            'commission': inventory_item.initial_commission_amount,
            'is_historical': False
        }


def clean_invoices_directory():
    """
    تقوم هذه الدالة بمسح جميع الملفات المتراكمة 
    داخل مجلد Invoices لتفريغ مساحة الهارد ديسك
    """
    try:
        save_dir = get_save_directory()
        # جلب كل الملفات داخل المجلد
        files = glob.glob(os.path.join(save_dir, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f) # مسح الملف
    except Exception:
        # إذا كان هناك ملف مفتوح حالياً في الـ PDF Reader، يتم تجاهله بصمت
        pass

# ==========================================
# دوال تحويل الأرقام (عربي / إنجليزي)
# ==========================================

def to_arabic_numerals(text):
    """تحويل الأرقام الإنجليزية إلى أرقام عربية (هندية)"""
    if text is None:
        return ""
    arabic_numbers = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
    return str(text).translate(arabic_numbers)

def to_english_numerals(text):
    """تحويل الأرقام العربية (الهندية) إلى أرقام إنجليزية"""
    if text is None:
        return ""
    english_numbers = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return str(text).translate(english_numbers)

def ed2ad(text):
    """دالة بديلة مختصرة لتحويل الأرقام (تستخدم في بعض الملفات)"""
    return to_arabic_numerals(text)


# ==========================================
# 2. دوال إعداد المسارات (القلب النابض للتطبيق)
# ==========================================

def get_wkhtmltopdf_config():
    """
    تحديد مكان أداة التحويل ديناميكياً
    """
    # 1. تحديد المجلد الجذري (سواء كان exe أو كود)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS # مسار مؤقت عند التشغيل كـ exe
    else:
        base_path = settings.BASE_DIR
    
    # 2. المسار المتوقع داخل مشروعك
    wkhtmltopdf_path = os.path.join(base_path,'bin', 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
    
    # 3. التحقق وإرجاع الإعدادات
    if os.path.exists(wkhtmltopdf_path):
        return pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    else:
        # محاولة احتياطية: البحث في مسار النظام
        return pdfkit.configuration() 

def get_save_directory():
    """
    تحديد مكان حفظ الفواتير (بجانب ملف التشغيل)
    """
    if getattr(sys, 'frozen', False):
        # بجانب ملف الـ exe
        base_path = os.path.dirname(sys.executable)
    else:
        # بجانب ملف manage.py
        base_path = settings.BASE_DIR
    
    invoices_dir = os.path.join(base_path,'media', 'Invoices')
    
    # إنشاء المجلد إذا لم يكن موجوداً
    if not os.path.exists(invoices_dir):
        os.makedirs(invoices_dir)
        
    return invoices_dir

# ==========================================
# دالة التفقيط (تحويل الأرقام إلى كلمات عربية)
# ==========================================

def get_num_to_words_ar(amount):
    """تحويل الأرقام إلى كلمات عربية (تفقيط الفواتير)"""
    try:
        from num2words import num2words
        return num2words(amount, lang='ar')
    except ImportError:
        return str(amount)
    except Exception:
        return str(amount)

# ==========================================
# 1. دالة جلب قائمة الطابعات من الويندوز
# ==========================================
def get_available_printers():
    """جلب جميع الطابعات المعرفة على الويندوز لاستخدامها في القوائم المنسدلة"""
    printers = []
    if platform.system() == 'Windows':
        try:
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            for p in win32print.EnumPrinters(flags):
                printers.append(p[2])
        except Exception:
            pass
    return printers


# ==========================================
# 2. دالة توليد الـ PDF (الطباعة الصامتة أو العرض)
# ==========================================
def generate_and_open_pdf(html_content, filename_prefix="document", target_printer=None, action="print", paper_size="DL"):
    """
    توليد PDF وتحديد السلوك والمقاس:
    - action="print" -> طباعة صامتة في الخلفية (للطابعة المحددة أو الافتراضية).
    - action="view"  -> فتح الملف فوراً للمعاينة.
    - paper_size="DL" أو "A4" لتحديد مقاس الورقة.
    """
    try:
        config = get_wkhtmltopdf_config()
        
        # 🔴 تحديد إعدادات الورقة بناءً على النوع
        if paper_size == "A4":
            options = {
                'encoding': "UTF-8",
                'page-size': 'A4',
                'orientation': 'Portrait',
                'margin-top': '10mm',
                'margin-right': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm',
                'enable-local-file-access': '',
                'disable-smart-shrinking': '',
                'quiet': '',
                # 🔴 هذان السطران هما الرصاصة السحرية لمنع توقف الأداة
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }
        else:
            # مقاس إيصالات العملاء (DL Landscape)
            options = {
                'encoding': "UTF-8",
                'page-width': '220mm',
                'page-height': '110mm',
                'margin-top': '0mm', 
                'margin-right': '0mm',
                'margin-bottom': '0mm', 
                'margin-left': '0mm',
                'enable-local-file-access': '',
                'disable-smart-shrinking': '',
                'quiet': '' ,
                # 🔴 هذان السطران هما الرصاصة السحرية لمنع توقف الأداة
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }

        save_dir = get_save_directory()
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        full_path = os.path.join(save_dir, filename)

        # إنشاء ملف الـ PDF
        pdfkit.from_string(html_content, full_path, configuration=config, options=options)
        import time
        time.sleep(1) # 🔴 إعطاء الويندوز ثانية واحدة لإغلاق الملف وحفظه تماماً

        if platform.system() == 'Windows':
            
            # --- حالة العرض (فتح الملف للمستخدم) ---
            if action == "view":
                os.startfile(full_path)
                return True, f"تم فتح الملف للمعاينة: {filename}"
            
            # --- حالة الطباعة الصامتة ---
# --- حالة الطباعة الصامتة (باستخدام SumatraPDF) ---
            elif action == "print":
                import subprocess
                printer_name = target_printer if target_printer else win32print.GetDefaultPrinter()
                
                # 1. تحديد مسار أداة SumatraPDF
                if getattr(sys, 'frozen', False):
                    base_dir = sys._MEIPASS
                else:
                    base_dir = settings.BASE_DIR
                    
                sumatra_path = os.path.join(base_dir, 'bin', 'SumatraPDF.exe')
                
                if not os.path.exists(sumatra_path):
                    return False, "أداة الطباعة SumatraPDF.exe غير موجودة في مجلد البرنامج!"

                # 2. تجهيز أمر الطباعة الصامتة
                print_command = [
                    sumatra_path, 
                    '-print-to', printer_name, 
                    '-silent', 
                    full_path
                ]
                
                try:
                    # 3. إرسال الأمر للويندوز بدون إظهار شاشة سوداء
                    # استخدمنا CREATE_NO_WINDOW لضمان عدم إزعاج الكاشير بنوافذ الـ CMD
                    subprocess.run(
                        print_command, 
                        check=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if os.path.exists(full_path):
                        os.remove(full_path) 

                    return True, f"تم الإرسال للطابعة: {printer_name}"
                    
                except subprocess.CalledProcessError as e:
                    return False, f"فشل في التواصل مع الطابعة: {str(e)}"
                
        else:
            # لأنظمة Linux/Mac
            if action == "view":
                os.system(f'xdg-open "{full_path}"')
            else:
                os.system(f'lpr "{full_path}"')
            return True, full_path

    except Exception as e:
        return False, str(e)
    
def get_default_date(current_branch):
    """
    جلب التاريخ الافتراضي (سنة وشهر) للفرع بناءً على:
    1. تاريخ آخر فاتورة مسجلة للفرع.
    2. أو تاريخ بداية اشتراك الترخيص الفعال.
    3. أو تاريخ اليوم كاحتياطي.
    """
    from .models import Receipt, ClientLicense
    from django.utils import timezone

    # 1. محاولة جلب آخر فاتورة مسجلة للفرع
    last_receipt = Receipt.objects.filter(branch=current_branch).order_by('-sale_year', '-sale_month').first()
    if last_receipt:
        return last_receipt.sale_year, last_receipt.sale_month
        
    # 2. سحب تاريخ بداية الاشتراك كأولوية لو مفيش فواتير
    active_license = ClientLicense.get_active_license()
    if active_license and active_license.start_date:
        return active_license.start_date.year, active_license.start_date.month
        
    # 3. آخر ملاذ لو مفيش ترخيص نشط (تاريخ اليوم)
    now = timezone.now()
    return now.year, now.month

def is_date_within_subscription(year, month):
    from .models import ClientLicense
    import datetime

    active_license = ClientLicense.get_active_license()
    
    # تأكد من الأسماء هنا: هل هي end_date أم expiry_date؟
    # لو ضرب إيرور تاني، بص في موديل ClientLicense وشوف اسم حقل النهاية إيه
    if not active_license or not active_license.start_date or not hasattr(active_license, 'expiry_date'):
        now = datetime.datetime.now()
        return year == now.year and month == now.month

    check_date = datetime.date(int(year), int(month), 1)
    start_date = datetime.date(active_license.start_date.year, active_license.start_date.month, 1)
    
    # تعديل المسمى هنا للموجود في الداتا بيز عندك
    end_val = active_license.expiry_date # غير 'expiry_date' للاسم الصح عندك
    end_date = datetime.date(end_val.year, end_val.month, 1)

    return start_date <= check_date <= end_date


def get_safe_available_qty(product, start_month, start_year):
    """
    حساب 'الرصيد الآمن' للبيع. 
    يفحص أقل رصيد متوفر للمنتج في الفترة بين 'تاريخ الفاتورة' و 'التاريخ الافتراضي للفرع' (سواء كانت الفاتورة في الماضي أو المستقبل).
    """
    
    end_year, end_month = get_default_date(product.branch)
    start_m, start_y = int(start_month), int(start_year)

    # 🟢 تحديد نقطة البداية والنهاية للوب بذكاء (ليدعم الفواتير القديمة والمستقبلية)
    if start_y > end_year or (start_y == end_year and start_m > end_month):
        # حالة الفاتورة المستقبلية (Post-dated / Pre-order)
        loop_start_y, loop_start_m = end_year, end_month
        loop_end_y, loop_end_m = start_y, start_m
    else:
        # حالة الفاتورة القديمة أو الحالية (Back-dated / Current)
        loop_start_y, loop_start_m = start_y, start_m
        loop_end_y, loop_end_m = end_year, end_month

    months_to_check = []
    curr_m, curr_y = loop_start_m, loop_start_y

    # إنشاء قائمة الشهور المراد فحصها (من البداية للنهاية المحددة)
    while curr_y < loop_end_y or (curr_y == loop_end_y and curr_m <= loop_end_m):
        months_to_check.append((curr_m, curr_y))
        curr_m += 1
        if curr_m > 12:
            curr_m = 1
            curr_y += 1

    safe_qty = None

    for m, y in months_to_check:
        hist_stock = product.get_stock_at_date(m, y)
        
        # تحسين أداء: لو الرصيد وصل لصفر في أي شهر، إذن أقصى كمية يمكن بيعها هي صفر (وقف اللوب فوراً)
        if hist_stock <= 0:
            return 0
            
        if safe_qty is None or hist_stock < safe_qty:
            safe_qty = hist_stock
            
    if safe_qty is None or safe_qty < 0:
        safe_qty = 0

    return safe_qty