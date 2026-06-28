import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()

from sync_api.models import ServerBranch, ServerInventoryItem, ServerReceipt

def run_verify():
    if len(sys.argv) < 3:
        print("Usage: verify_symmetry.py <machine_id> <receipt_number>")
        sys.exit(1)
        
    machine_id = sys.argv[1]
    receipt_num = int(sys.argv[2])
    
    print("\n--- Gate 1 & 2: Server Verification ---")
    b = ServerBranch.objects.filter(source_machine_id=machine_id, name='E2E Symmetry Branch').first()
    if not b:
        print("Gate 1 Failed: Branch 'E2E Symmetry Branch' not found on server")
        sys.exit(1)
        
    items = ServerInventoryItem.objects.filter(source_machine_id=machine_id, local_branch_id=b.local_id)
    if items.count() < 3:
        print(f"Gate 1 Failed: Expected at least 3 items, found {items.count()}")
        sys.exit(1)
        
    r = ServerReceipt.objects.filter(source_machine_id=machine_id, receipt_number=receipt_num).first()
    if not r:
        print(f"Gate 1 Failed: Receipt #{receipt_num} not found on server")
        sys.exit(1)
        
    print(f"Found Receipt #{r.receipt_number}, Customer: {r.customer_name}, Total: {r.total_amount}")
    if r.total_amount != 300:
        print("Gate 2 Failed: Receipt total mismatch (expected 300)")
        sys.exit(1)
        
    # Check Gate 3: Idempotency (Optional - the script can trigger push again)
    print("Verification SUCCESS! Gates 1 and 2 passed. Data is symmetrical.")

if __name__ == '__main__':
    run_verify()
