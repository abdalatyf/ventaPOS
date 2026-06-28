import os, sys
sys.path.insert(0, r'd:\Projects\VentaPOS\Server')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')

import django
django.setup()

from sync_api.models import ServerLicense
from datetime import date

existing = ServerLicense.objects.filter(machine_id='90853299-041E-93E9-236B-B87A3D437E9F').first()
if existing:
    print(f"EXISTING: code={existing.company_code}, active={existing.is_active}, online={existing.is_online_active}")
else:
    lic = ServerLicense(
        machine_id='90853299-041E-93E9-236B-B87A3D437E9F',
        client_name='VentaPOS Test Company',
        is_active=True,
        is_online_active=True,
        online_expiry_date=date(2027, 6, 21)
    )
    lic.save()
    print(f"CREATED: code={lic.company_code}, active={lic.is_active}, online={lic.is_online_active}")

# Also count total licenses
print(f"Total licenses: {ServerLicense.objects.count()}")
