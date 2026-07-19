import re

with open('backend/api/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove tenant_id
content = re.sub(r'[ \t]*tenant_id = serializers\.IntegerField\(source="tenant\.id", read_only=True\)\n', '', content)

# Remove tenant kwargs in objects.create
content = re.sub(r'tenant=tenant,\s*', '', content)
content = re.sub(r',\s*tenant=tenant', '', content)
content = content.replace('tenant=tenant', '')

# Fix get_default_date_for_tenant
content = content.replace('get_default_date_for_tenant(tenant)', 'get_default_date_for_tenant()')
content = re.sub(r'[ \t]*tenant = self\.context\["tenant"\]\n', '', content)
content = re.sub(r'[ \t]*tenant = validated_data\.get\("tenant"\) or self\.context\.get\("tenant"\)\n', '', content)

# Remove the tenant fetching logic in create
old_tenant_fetch = r'''        if not tenant:
            branch = validated_data\.get\("branch"\)
            if branch:
                tenant = branch\.tenant
            else:
                tenant = Tenant\.objects\.using\("default"\)\.first\(\)
        validated_data\["tenant"\] = tenant'''
content = re.sub(old_tenant_fetch, '', content)

# Fix ClientLicense.objects.filter(tenant=tenant)
content = content.replace('.filter(tenant=tenant, is_deleted=False)', '.filter(is_deleted=False)')
content = content.replace('ClientLicense.objects.filter(\n                is_active=True, is_deleted=False\n            )', 'ClientLicense.objects.filter(\n                is_active=True, is_deleted=False\n            )') # just safely remove tenant if present
content = content.replace('ClientLicense.objects.filter(\n                tenant=tenant, is_active=True, is_deleted=False\n            )', 'ClientLicense.objects.filter(\n                is_active=True, is_deleted=False\n            )')

# Fix receipt filter tenant
content = content.replace('Receipt.objects.filter(tenant=tenant)', 'Receipt.objects.filter()')

# Also replace any other tenant references left over
content = content.replace('tenant=tenant', '')

with open('backend/api/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Serializers fully cleaned of tenant references.")
