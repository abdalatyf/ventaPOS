import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.test import Client
import traceback

try:
    c = Client()
    res = c.get("/api/v1/reports/inventory-movement/?branch_id=1&year=2026&month=7")
    print(res.status_code)
    if res.status_code == 500:
        print(res.content.decode('utf-8'))
except Exception as e:
    traceback.print_exc()
