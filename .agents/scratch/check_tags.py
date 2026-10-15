import sys
import django
from django.conf import settings
from django.template import Engine
settings.configure(INSTALLED_APPS=[])
django.setup()
engine = Engine()
files = ['general_settings.html', 'manage_branches.html', 'manage_salespersons.html', 'manage_expenses.html', 'import_wizard.html', 'subscription_dashboard.html', 'base.html']
for f in files:
    with open('sales/salesapp/templates/salesapp/'+f, 'r', encoding='utf-8') as file:
        try:
            engine.from_string(file.read())
            print(f + ': OK')
        except Exception as e:
            print(f + ': ERROR - ' + str(e))
