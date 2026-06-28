import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from salesapp.models import Branch, InventoryItem

b, _ = Branch.objects.get_or_create(name='Test Branch')
user, _ = User.objects.get_or_create(username='admin', is_superuser=True)
if not user.password:
    user.set_password('admin')
    user.save()

c = Client()
c.force_login(user)
session = c.session
session['branch_id'] = b.id
session.save()

with open('mock_mobile_data.json', 'rb') as f:
    resp = c.post('/sync/mobile-import/preview/', {'json_file': f})
    
print("PREVIEW RESP STATUS:", resp.status_code)
if resp.status_code == 200:
    print("Preview successful.")
    # Now confirm
    resp_confirm = c.post('/sync/mobile-import/confirm/')
    print("CONFIRM RESP STATUS:", resp_confirm.status_code)
else:
    print("Preview failed:", resp.content.decode())
