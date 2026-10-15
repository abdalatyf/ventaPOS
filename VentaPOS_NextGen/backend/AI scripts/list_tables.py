import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
django.setup()
from django.db import connection
with connection.cursor() as c:
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print("Tables in default DB:")
    for t in tables:
        print(" -", t[0])
