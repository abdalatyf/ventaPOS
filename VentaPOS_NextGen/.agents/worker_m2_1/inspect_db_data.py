import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import (
    Tenant, Branch, Salesperson, InventoryItem, ClientLicense, CompanySetting, Receipt
)

print("=== TENANTS ===")
for t in Tenant.objects.all():
    print(f"Tenant ID: {t.id}, Company Code: {t.company_code}, Name: {t.name}, Active: {t.is_active}")

print("\n=== BRANCHES ===")
for b in Branch.objects.all():
    print(f"Branch ID: {b.id}, Local ID: {b.local_id}, Name: {b.name}, Tenant: {b.tenant.company_code if b.tenant else None}")

print("\n=== SALESPERSONS ===")
for s in Salesperson.objects.all():
    print(f"Salesperson ID: {s.id}, Local ID: {s.local_id}, Name: {s.name}, Tenant: {s.tenant.company_code if s.tenant else None}")

print("\n=== INVENTORY ITEMS ===")
for item in InventoryItem.objects.all()[:15]:
    print(f"Item ID: {item.id}, Local ID: {item.local_id}, Name: {item.name}, Initial Qty: {item.initial_quantity}, Initial Price: {item.initial_purchase_price}, Branch Local ID: {item.branch.local_id if item.branch else None}")

print("\n=== CLIENT LICENSES ===")
for l in ClientLicense.objects.all():
    print(f"License ID: {l.id}, Active: {l.is_active}, Balance: {l.invoices_balance}, Expiry: {l.expiry_date}, Tenant: {l.tenant.company_code if l.tenant else None}")

print("\n=== COMPANY SETTINGS ===")
for c in CompanySetting.objects.all():
    print(f"Setting ID: {c.id}, Name: {c.company_name}, Code: {c.company_code}")

print(f"\nTotal Receipts in DB: {Receipt.objects.count()}")
