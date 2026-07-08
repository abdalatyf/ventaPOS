import os
import platform
import pdfkit
from django.conf import settings
from django.utils import timezone
import sys
import glob

def clean_invoices_directory():
    try:
        save_dir = get_save_directory()
        files = glob.glob(os.path.join(save_dir, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
    except Exception:
        pass

def to_arabic_numerals(text):
    if text is None:
        return ""
    arabic_numbers = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
    return str(text).translate(arabic_numbers)

def to_english_numerals(text):
    if text is None:
        return ""
    english_numbers = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return str(text).translate(english_numbers)

def ed2ad(text):
    return to_arabic_numerals(text)

def get_wkhtmltopdf_config():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS 
    else:
        base_path = settings.BASE_DIR
    
    wkhtmltopdf_path = os.path.join(base_path, 'bin', 'wkhtmltox', 'bin', 'wkhtmltopdf.exe')
    
    if os.path.exists(wkhtmltopdf_path):
        return pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    else:
        return pdfkit.configuration() 

def get_save_directory():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = settings.BASE_DIR
    
    invoices_dir = os.path.join(base_path, 'media', 'Invoices')
    
    if not os.path.exists(invoices_dir):
        os.makedirs(invoices_dir)
        
    return invoices_dir

def get_num_to_words_ar(amount):
    try:
        from num2words import num2words
        return num2words(amount, lang='ar')
    except ImportError:
        return str(amount)
    except Exception:
        return str(amount)

def generate_and_open_pdf(html_content, filename_prefix="document", target_printer=None, action="print", paper_size="DL"):
    try:
        config = get_wkhtmltopdf_config()
        
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
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }
        else:
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
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }

        save_dir = get_save_directory()
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{filename_prefix}_{timestamp}.pdf"
        full_path = os.path.join(save_dir, filename)

        pdfkit.from_string(html_content, full_path, configuration=config, options=options)
        import time
        time.sleep(1) 

        if platform.system() == 'Windows':
            if action == "view":
                os.startfile(full_path)
                return True, f"تم فتح الملف للمعاينة: {filename}"
            
            elif action == "print":
                import subprocess
                
                if getattr(sys, 'frozen', False):
                    base_dir = sys._MEIPASS
                else:
                    base_dir = settings.BASE_DIR
                    
                sumatra_path = os.path.join(base_dir, 'bin', 'SumatraPDF.exe')
                
                if not os.path.exists(sumatra_path):
                    return False, "أداة الطباعة SumatraPDF.exe غير موجودة في مجلد البرنامج!"

                if target_printer:
                    print_command = [
                        sumatra_path, 
                        '-print-to', target_printer, 
                        '-silent', 
                        full_path
                    ]
                else:
                    print_command = [
                        sumatra_path, 
                        '-print-to-default', 
                        '-silent', 
                        full_path
                    ]
                
                try:
                    subprocess.Popen(print_command, creationflags=subprocess.CREATE_NO_WINDOW)
                    return True, "تم إرسال أمر الطباعة بنجاح"
                except Exception as e:
                    return False, f"خطأ أثناء استدعاء الطابعة: {e}"
        return False, "نظام التشغيل غير مدعوم للطباعة الصامتة"
    except Exception as e:
        return False, f"حدث خطأ أثناء إنشاء PDF: {str(e)}"
