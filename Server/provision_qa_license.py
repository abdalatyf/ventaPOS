import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()

from sync_api.models import ServerLicense

# Create the test license
license, created = ServerLicense.objects.get_or_create(
    machine_id='E2E_QA_MACHINE_123',
    defaults={
        'client_name': 'E2E Test Client',
        'is_active': True,
        'is_online_active': True
    }
)
if not created:
    license.is_online_active = True
    license.save()

print("Test license provisioned.")
