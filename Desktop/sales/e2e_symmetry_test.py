import os
import sys
import django
import requests
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
django.setup()

from salesapp.models import Branch, InventoryItem, Receipt, SaleItem, SyncDeletionLog
from salesapp.security_utils import get_machine_id
from salesapp.sync_agent import collect_payload

SERVER_URL = "http://127.0.0.1:8000/api/v1/sync/push/"

def run_test():
    print("--- Phase A: Data Seeding ---")
    branch, _ = Branch.objects.get_or_create(name='E2E Symmetry Branch')
    branch.is_synced = False
    branch.save()
    
    i1, _ = InventoryItem.objects.get_or_create(name='Symmetry Product 1', branch=branch, defaults={'initial_quantity': 50, 'initial_purchase_price': 100})
    i2, _ = InventoryItem.objects.get_or_create(name='Symmetry Product 2', branch=branch, defaults={'initial_quantity': 20, 'initial_purchase_price': 50})
    i3, _ = InventoryItem.objects.get_or_create(name='Symmetry Product 3', branch=branch, defaults={'initial_quantity': 10, 'initial_purchase_price': 200})
    
    for item in [i1, i2, i3]:
        item.is_synced = False
        item.save()

    # Generate a unique receipt number based on current time
    import time
    receipt_num = int(time.time()) % 100000

    r = Receipt.objects.create(
        receipt_number=receipt_num,
        branch=branch,
        customer_name='E2E Customer',
        total_amount=300,
        sale_year=2026,
        sale_month=6,
        is_cash_sale=True,
        is_synced=False,
        receipt_hash=str(uuid.uuid4())
    )
    SaleItem.objects.create(receipt=r, inventory_item=i1, quantity=2, unit_price=100)
    SaleItem.objects.create(receipt=r, inventory_item=i2, quantity=2, unit_price=50)

    machine_id = get_machine_id()
    print(f"[SEEDED] Machine ID: {machine_id}")
    print(f"[SEEDED] Branch: {branch.name}")
    print(f"[SEEDED] Items: 3")
    print(f"[SEEDED] Receipt: #{receipt_num}")

    # Ensure provisioned on server first
    print("\n--- Provisioning Machine on Server ---")
    os.system(f'set DJANGO_SETTINGS_MODULE=server_backend.settings&& cd /d D:\\Projects\\VentaPOS\\Server && .\\venv\\Scripts\\python.exe provision_machine.py "{machine_id}"')

    print("\n--- Phase B: Push to Central Server ---")
    _, payload, has_data, _, _, _, _, _, _, _ = collect_payload()
    
    if not has_data:
        print("ERROR: No data to push!")
        sys.exit(1)

    print("Pushing data to", SERVER_URL)
    full_data = {'machine_id': machine_id, 'payload': payload}
    response = requests.post(SERVER_URL, json=full_data)
    
    print("HTTP Status:", response.status_code)
    try:
        resp_json = response.json()
        print("Response:", resp_json)
        if resp_json.get('status') != 'success':
            print("SYNC FAILED: Status != success")
            sys.exit(1)
    except Exception as e:
        print("SYNC FAILED: Error parsing JSON -", response.text)
        sys.exit(1)
        
    print("\n--- Gate 3: Idempotency Check (Duplicate Push) ---")
    response2 = requests.post(SERVER_URL, json=full_data)
    print("Idempotency Push HTTP Status:", response2.status_code)
    try:
        resp_json2 = response2.json()
        if resp_json2.get('status') != 'success':
            print("SYNC FAILED on second push!")
            sys.exit(1)
    except:
        pass
        
    # Mark as synced (mimicking sync_agent)
    branch.is_synced = True; branch.save()
    i1.is_synced = True; i1.save()
    i2.is_synced = True; i2.save()
    i3.is_synced = True; i3.save()
    r.is_synced = True; r.save()

    print("\n--- Phase C: Symmetry Verification (via Server script) ---")
    verify_cmd = f'set DJANGO_SETTINGS_MODULE=server_backend.settings&& cd /d D:\\Projects\\VentaPOS\\Server && .\\venv\\Scripts\\python.exe verify_symmetry.py "{machine_id}" "{receipt_num}"'
    os.system(verify_cmd)

if __name__ == '__main__':
    run_test()
