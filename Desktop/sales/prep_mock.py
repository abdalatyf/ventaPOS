import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
django.setup()

from django.test import Client
from salesapp.models import Branch, InventoryItem

# Ensure we have at least one branch and item
b, _ = Branch.objects.get_or_create(name='Test Branch')
item, _ = InventoryItem.objects.get_or_create(name='Item A', branch=b, initial_quantity=100)

with open('mock_mobile_data.json', 'r') as f:
    json_data = f.read()

import json
data = json.loads(json_data)
# Fix item_id
data['receipts'][0]['items'][0]['item_id'] = item.id
with open('mock_mobile_data.json', 'w') as f:
    f.write(json.dumps(data))

print("Mock JSON ready with valid item ID:", item.id)
