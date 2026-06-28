import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()

from sync_api.models import ServerLicense
from django.utils import timezone
from datetime import timedelta

machine_id = sys.argv[1] if len(sys.argv) > 1 else None
if not machine_id:
    print("Please provide machine_id")
    sys.exit(1)

lic, created = ServerLicense.objects.get_or_create(machine_id=machine_id)
lic.is_active = True
lic.is_online_active = True
lic.expiry_date = timezone.now() + timedelta(days=365)
lic.invoices_balance = 99999
lic.save()

print(f"Provisioned ServerLicense for {machine_id}")
