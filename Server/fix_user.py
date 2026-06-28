import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_backend.settings')
django.setup()
from sync_api.models import ServerCloudUser
user = ServerCloudUser.objects.filter(username='XXXX-admin').first()
if user:
    user.username = '4037-admin'
    user.save()
    print('Fixed user XXXX-admin to 4037-admin')
else:
    print('User not found.')
