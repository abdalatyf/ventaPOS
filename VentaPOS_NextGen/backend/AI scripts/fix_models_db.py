import re

path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add db_constraint=False to models in the system db
models_to_fix = [
    ('cloud_users', 'Tenant, on_delete=models.CASCADE, related_name="cloud_users", db_constraint=False'),
    ('company_setting', 'Tenant, on_delete=models.CASCADE, related_name="company_setting", db_constraint=False'),
    ('client_licenses', 'Tenant, on_delete=models.CASCADE, related_name="client_licenses", db_constraint=False'),
    ('used_licenses', 'Tenant, on_delete=models.CASCADE, related_name="used_licenses", db_constraint=False'),
    ('license_histories', 'Tenant, on_delete=models.CASCADE, related_name="license_histories", db_constraint=False'),
]

for related_name, replacement in models_to_fix:
    target = f'Tenant, on_delete=models.CASCADE, related_name="{related_name}"'
    content = content.replace(target, replacement)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
