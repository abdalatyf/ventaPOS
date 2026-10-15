import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Receipt
from django.db import transaction

receipts = Receipt.objects.all()
count = 0
for r in receipts:
    items = r.sale_items.filter(is_deleted=False)
    if items.exists():
        new_text = " + ".join([f"{i.inventory_item.name}" if i.quantity == 1 else f"{i.quantity} {i.inventory_item.name}" for i in items])
        if r.products_text != new_text:
            r.products_text = new_text
            r.save(update_fields=["products_text"])
            count += 1
print(f"Updated {count} receipts.")
