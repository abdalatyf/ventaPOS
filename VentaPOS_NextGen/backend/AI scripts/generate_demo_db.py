import os
import django
from django.conf import settings

# 1. Setup Django environment pointing to demo_seed.sqlite3
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# We must override the DB before django.setup() if possible,
# but sometimes settings are already loaded. We'll try.
import backend.settings as app_settings
app_settings.DATABASES['default']['NAME'] = os.path.join(app_settings.BASE_DIR, 'db_demo.sqlite3')

django.setup()

from django.core.management import call_command
from api.models import (
    Branch, CompanySetting, InventoryItem, Supplier, Salesperson,
    PurchaseInvoice, PurchaseInvoiceItem, ClientLicense
)
from django.utils import timezone
import random
from datetime import timedelta

def create_demo_data():
    print("Migrating demo database...")
    call_command('migrate', interactive=False)

    print("Clearing old data...")
    Branch.objects.all().delete()
    CompanySetting.objects.all().delete()
    ClientLicense.objects.all().delete()
    
    print("Creating Company Settings...")
    CompanySetting.objects.create(
        name="محلات الأمانة للبيع بالتجزئة (نسخة تجريبية)",
        phone1="01012345678",
        phone2="01112345678",
        footer_text="نسخة تجريبية - جميع البيانات وهمية وسيتم حذفها",
        is_cloud_viewer=False
    )
    
    print("Creating Branch...")
    branch = Branch.objects.create(name="الفرع الرئيسي")
    
    print("Creating Salesperson...")
    salesperson = Salesperson.objects.create(name="أحمد محمد", branch=branch)
    
    print("Creating Supplier...")
    supplier = Supplier.objects.create(name="شركة التوريدات العامة")
    
    print("Creating Demo License (VIP)...")
    ClientLicense.objects.create(
        product_id=7, # Lifetime Pro
        start_date=timezone.now().date(),
        expiry_date=None,
        invoices_balance=999999,
        is_active=True,
        machine_id="DEMO_MACHINE",
        license_code_hash="DEMO_HASH"
    )
    
    print("Creating Inventory Items...")
    items = [
        ("ايفون 15 برو ماكس 256 جيجا", 50, 45000),
        ("سامسونج S24 الترا", 30, 42000),
        ("شاحن انكر 20 وات اصلي", 150, 450),
        ("جراب سيليكون شفاف", 300, 50),
        ("سماعة ايربودز برو كوبي", 100, 600),
        ("اسكرينة زجاج", 500, 30),
        ("كابل ايفون اصلي", 200, 350),
        ("باور بانك 10000 ملي", 80, 800),
    ]
    
    for name, qty, price in items:
        InventoryItem.objects.create(
            name=name,
            branch=branch,
            initial_quantity=qty,
            initial_purchase_price=price,
            initial_commission_amount=0
        )
        
    print("Demo DB created successfully at db_demo.sqlite3!")
    print("Please rename db_demo.sqlite3 to demo_seed.sqlite3 if this is the final seed.")

if __name__ == "__main__":
    create_demo_data()
