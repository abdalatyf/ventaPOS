import django, os, sys
sys.stdout.reconfigure(encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
django.setup()
from api.models import Tenant, Branch, Salesperson, InventoryItem, Receipt, SaleItem, InstallmentPayment

print("=== TENANTS ===")
for t in Tenant.objects.all():
    print(f"ID: {t.id}, Company Code: {t.company_code}, Name: {t.name}, Active: {t.is_active}")

print("\n=== BRANCHES ===")
for b in Branch.objects.all():
    print(f"ID: {b.id}, Local ID: {b.local_id}, Tenant: {b.tenant.company_code}, Name: {b.name}")

print("\n=== SALESPERSONS ===")
for s in Salesperson.objects.all():
    print(f"ID: {s.id}, Local ID: {s.local_id}, Name: {s.name}, Branch: {s.branch}")

print("\n=== INVENTORY ITEMS ===")
for item in InventoryItem.objects.all():
    print(f"ID: {item.id}, Local ID: {item.local_id}, Name: {item.name}, Initial Qty: {item.initial_quantity}, Purchase Price: {item.initial_purchase_price}, Commission: {item.initial_commission_amount}")

print("\n=== RECEIPTS ===")
for r in Receipt.objects.all():
    hash_str = r.receipt_hash[:16] if r.receipt_hash else 'None'
    print(f"ID: {r.id}, Receipt No: {r.receipt_number}, Type: {'Cash' if r.is_cash_sale else 'Installment'}, Customer: '{r.customer_name}', Total: {r.total_amount}, Down Payment: {r.down_payment}, Hash: {hash_str}...")

print("\n=== SALE ITEMS ===")
for item in SaleItem.objects.all():
    print(f"ID: {item.id}, Receipt ID: {item.receipt_id}, Product: {item.inventory_item.name}, Qty: {item.quantity}, Price: {item.unit_price}")

print("\n=== INSTALLMENT PAYMENTS ===")
for ip in InstallmentPayment.objects.all():
    print(f"ID: {ip.id}, Receipt ID: {ip.receipt_id}, Due Date: {ip.payment_date}, Amount: {ip.amount}")
