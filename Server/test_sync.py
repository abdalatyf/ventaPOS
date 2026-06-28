import os
import django
import json
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()

from django.test import Client
from sync_api.models import (
    ServerLicense, ServerReceipt, ServerCloudUser, 
    ServerInventoryItem, ServerBranch, ServerSalesperson
)

def run_tests():
    print("Setting up test data...")
    ServerLicense.objects.all().delete()
    ServerReceipt.objects.all().delete()
    
    machine_id = "TEST_MACHINE_123"
    
    # Test 1: License Gatekeeper - Unauthorized
    print("Test 1: Unauthorized Sync Push")
    client = Client()
    response = client.post('/api/v1/sync/push/', json.dumps({
        'machine_id': machine_id,
        'payload': {}
    }), content_type="application/json")
    print("Unauthorized Response (expect 403):", response.status_code, response.json())
    
    # Setup License
    license = ServerLicense.objects.create(
        machine_id=machine_id,
        client_name="Test Client",
        company_code="COMP123",
        is_active=True,
        is_online_active=False
    )
    
    # Test 2: Online Sync Disabled
    print("\nTest 2: Online Sync Disabled")
    response = client.post('/api/v1/sync/push/', json.dumps({
        'machine_id': machine_id,
        'payload': {}
    }), content_type="application/json")
    print("Online Sync Disabled Response (expect 403):", response.status_code, response.json())
    
    # Enable Online Sync
    license.is_online_active = True
    license.online_expiry_date = timezone.now().date() + timedelta(days=30)
    license.save()
    
    # Test 3: Authorized Sync Push with Receipts
    print("\nTest 3: Authorized Sync Push")
    payload = {
        'machine_id': machine_id,
        'payload': {
            'company_settings': {
                'name': 'Test Company',
                'phone1': '123456789'
            },
            'receipts': [
                {
                    'receipt_hash': 'hash1',
                    'id': 1,
                    'receipt_number': 1001,
                    'branch_id': 1,
                    'total_amount': 150.00,
                    'down_payment': 0,
                    'sale_year': 2026,
                    'sale_month': 6,
                    'is_cash_sale': True,
                    'items': [
                        {'product_id': 1, 'product_name': 'Item A', 'quantity': 2, 'price': 75.00}
                    ]
                },
                {
                    'receipt_hash': 'hash2',
                    'id': 2,
                    'receipt_number': 1002,
                    'branch_id': 1,
                    'total_amount': 200.00,
                    'down_payment': 0,
                    'sale_year': 2026,
                    'sale_month': 6,
                    'is_cash_sale': True,
                    'items': []
                }
            ]
        }
    }
    
    response = client.post('/api/v1/sync/push/', json.dumps(payload), content_type="application/json")
    print("Authorized Push Response (expect 200):", response.status_code, response.json())
    
    # Test 4: Deduplication - Sending same payload
    print("\nTest 4: Deduplication test (same payload)")
    response = client.post('/api/v1/sync/push/', json.dumps(payload), content_type="application/json")
    print("Deduplicated Push Response (expect 200):", response.status_code, response.json())
    print("Total Receipts in DB:", ServerReceipt.objects.count())
    
    # Test 5: Mobile Push
    print("\nTest 5: Mobile Push Endpoint")
    response = client.post('/api/v1/sync/mobile-push/', json.dumps({
        'machine_id': machine_id,
        'payload': {
            'receipts': [
                {
                    'receipt_hash': 'mob_hash1',
                    'local_id': 101,
                    'receipt_number': 5001,
                    'branch_id': 1,
                    'total_amount': 250.00,
                    'items': [
                        {'product_id': 1, 'quantity': 1, 'price': 250.00}
                    ]
                }
            ]
        }
    }), content_type="application/json")
    print("Mobile Push Response (expect 200):", response.status_code, response.json())
    
    # Test 6: Remote Provisioning - Upload Setup
    print("\nTest 6: Remote Provisioning - Upload Setup")
    setup_payload = {
        'machine_id': machine_id,
        'payload': {
            'salesperson_id': 10,
            'name': 'John Doe',
            'inventory': [{'id': 1, 'name': 'Item A', 'price': 100}]
        }
    }
    response = client.post('/api/v1/sync/upload-setup/', json.dumps(setup_payload), content_type="application/json")
    print("Upload Setup Response (expect 200):", response.status_code, response.json())
    
    token = response.json().get('token')
    
    # Test 7: Remote Provisioning - Download Setup
    print("\nTest 7: Remote Provisioning - Download Setup")
    if token:
        response = client.get(f'/api/v1/sync/download-setup/?token={token}')
        print("Download Setup Response (expect 200):", response.status_code, response.json())
        
        # Test 8: Verify One-Time Use
        print("\nTest 8: Verify One-Time Use (Second Download)")
        response2 = client.get(f'/api/v1/sync/download-setup/?token={token}')
        print("Second Download Response (expect 404):", response2.status_code, response2.json())
    else:
        print("Skipping Test 7/8 - No token returned.")

    # Create test branch, salesperson, inventory item, and cloud user
    ServerBranch.objects.all().delete()
    ServerSalesperson.objects.all().delete()
    ServerInventoryItem.objects.all().delete()
    ServerCloudUser.objects.all().delete()
    
    ServerBranch.objects.create(source_machine_id=machine_id, local_id=1, name="Main Branch")
    ServerSalesperson.objects.create(source_machine_id=machine_id, local_id=1, local_branch_id=1, name="Salesperson A")
    ServerInventoryItem.objects.create(
        source_machine_id=machine_id,
        local_id=1,
        local_branch_id=1,
        name="Product A",
        quantity=10,
        purchase_price=50.00,
        salesperson_commission_amount=5.00,
        created_at_local=timezone.now()
    )
    ServerCloudUser.objects.create(
        source_machine_id=machine_id,
        local_id=1,
        username="clouduser",
        password_hash="pwd_hash_123",
        role="VIEWER",
        is_active=True
    )
    
    # Test 9: Viewer Authentication
    print("\nTest 9: Viewer Authentication (expect 200)")
    response = client.post('/api/v1/auth/viewer/', json.dumps({
        'company_code': 'COMP123',
        'username': 'clouduser',
        'password_hash': 'pwd_hash_123'
    }), content_type="application/json")
    print("Viewer Auth Response:", response.status_code, response.json())
    
    # Test 10: Viewer Download Sync
    print("\nTest 10: Viewer Download Sync (expect 200)")
    response = client.post('/api/v1/sync/viewer/download/', json.dumps({
        'company_code': 'COMP123'
    }), content_type="application/json")
    print("Viewer Download Response:", response.status_code, response.json())

    print("\nAll tests completed.")

if __name__ == "__main__":
    run_tests()
