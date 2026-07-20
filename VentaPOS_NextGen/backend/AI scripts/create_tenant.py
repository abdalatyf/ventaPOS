import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Tenant, Branch

t, created = Tenant.objects.get_or_create(
    company_code='1234',
    defaults={'name': 'Local Dev Company', 'is_active': True}
)

b, created_b = Branch.objects.get_or_create(
    tenant=t,
    local_id=1,
    defaults={'name': 'الفرع الرئيسي'}
)

print(f"Tenant: {t.company_code}, Branch: {b.name}")
