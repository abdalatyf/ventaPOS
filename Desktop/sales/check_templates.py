import os
import django
from django.conf import settings
from django.template.loader import get_template

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'salesapp',
    ],
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
        },
    ]
)
django.setup()

templates = ['salesapp/general_settings.html', 'salesapp/manage_branches.html', 'salesapp/manage_salespersons.html', 'salesapp/manage_expenses.html', 'salesapp/import_wizard.html', 'salesapp/subscription_dashboard.html', 'salesapp/base.html']
for t in templates:
    try:
        get_template(t)
        print(f'{t}: OK')
    except Exception as e:
        print(f'{t}: ERROR - {e}')
