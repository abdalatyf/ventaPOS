import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server_backend.settings")
django.setup()

import json
from django.test import RequestFactory
from sync_api.views import AdminSyncPushView
from sync_api.models import ServerLicense, ServerCompanySetting, ServerInventoryItem, ServerSalesperson

# Setup
machine_id = "test-manager-123"
company_code = "9999"

ServerLicense.objects.get_or_create(
    machine_id=machine_id,
    company_code=company_code,
    is_active=True,
    is_online_active=True,
    online_expiry_date="2030-01-01"
)

factory = RequestFactory()
payload = {
    "company_code": company_code,
    "machine_id": machine_id,
    "payload": {
        "settings": {
            "company_name": "Test Company",
            "footer_text": "Test Footer"
        },
        "products": [
            {
                "local_id": 100,
                "name": "Test Product",
                "initial_quantity": 10,
                "initial_purchase_price": 50.0,
                "action": "CREATE"
            }
        ],
        "users": [
            {
                "local_id": 200,
                "name": "Test User",
                "branch_id": 1,
                "offline_pin": "1234",
                "action": "CREATE"
            }
        ]
    }
}

request = factory.post('/api/v1/sync/admin-push/', data=json.dumps(payload), content_type='application/json')
response = AdminSyncPushView.as_view()(request)
print("Status Code:", response.status_code)
print("Response:", response.content.decode())

# Verify DB
print("Settings:", ServerCompanySetting.objects.filter(source_machine_id=machine_id).values())
print("Products:", ServerInventoryItem.objects.filter(source_machine_id=machine_id).values())
print("Users:", ServerSalesperson.objects.filter(source_machine_id=machine_id).values())

# Test UPDATE and DELETE
payload['payload']['products'][0]['action'] = 'UPDATE'
payload['payload']['products'][0]['name'] = 'Updated Product'

payload['payload']['users'][0]['action'] = 'DELETE'

request = factory.post('/api/v1/sync/admin-push/', data=json.dumps(payload), content_type='application/json')
response = AdminSyncPushView.as_view()(request)
print("Status Code Update/Delete:", response.status_code)
print("Response Update/Delete:", response.content.decode())

print("Products after Update:", ServerInventoryItem.objects.filter(source_machine_id=machine_id).values())
print("Users after Delete:", ServerSalesperson.objects.filter(source_machine_id=machine_id).values())
