import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Receipt
from django.db import transaction

receipts = Receipt.objects.filter(products_text__isnull=True) | Receipt.objects.filter(products_text="")
count = 0
for r in receipts:
    items = r.sale_items.filter(is_deleted=False)
    if items.exists():
        r.products_text = " - ".join([f"{i.inventory_item.name} ({i.quantity})" for i in items])
        r.save(update_fields=["products_text"])
        count += 1
print(f"Updated {count} receipts.")
