import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()
from sync_api.models import ServerCloudUser
for cu in ServerCloudUser.objects.all():
    print(cu.username, cu.password_hash, cu.role)
