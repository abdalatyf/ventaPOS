import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('def get_default_date_for_tenant(tenant):', 'def get_default_date_for_tenant():')
content = content.replace('def is_date_within_subscription(tenant, year, month):', 'def is_date_within_subscription(year, month):')
content = content.replace('if not is_date_within_subscription(tenant, year, month):', 'if not is_date_within_subscription(year, month):')
content = content.replace('if not is_date_within_subscription(tenant, sale_year, sale_month):', 'if not is_date_within_subscription(sale_year, sale_month):')
content = content.replace('is_date_within_subscription(tenant,', 'is_date_within_subscription(')

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed get_default_date_for_tenant args in views.py")
