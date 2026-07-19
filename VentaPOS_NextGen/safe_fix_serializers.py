import re

with open('backend/api/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove classes safely
content = re.sub(r'^class TenantSerializer[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class CloudUserSerializer[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class ActionLogSerializer[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)
content = re.sub(r'^class SyncLogSerializer[\s\S]*?(?=^class )', '', content, flags=re.MULTILINE)

# 2. Remove fields specifically from lists
content = content.replace('"tenant", ', '')
content = content.replace(', "tenant"', '')
content = content.replace('"tenant_id", ', '')
content = content.replace(', "tenant_id"', '')
content = content.replace("'tenant', ", '')
content = content.replace(", 'tenant'", '')
content = content.replace("'tenant_id', ", '')
content = content.replace(", 'tenant_id'", '')

# 3. Fix the context tenant logic
# Specifically, in validate() of InventoryAdjustmentSerializer, remove tenant and get_default_date_for_tenant
old_validate = r'''    def validate\(self, data\):
        if data\.get\("adjustment_type"\) == "DEFICIT":
            from api\.views import get_default_date_for_tenant
            from rest_framework\.exceptions import ValidationError
            tenant = self\.context\.get\('tenant'\)
            default_year, default_month = get_default_date_for_tenant\(tenant\)'''

new_validate = '''    def validate(self, data):
        if data.get("adjustment_type") == "DEFICIT":
            from api.views import get_default_date_for_tenant
            from rest_framework.exceptions import ValidationError
            default_year, default_month = get_default_date_for_tenant()'''
content = re.sub(old_validate, new_validate, content)

# 4. Remove imports
content = re.sub(r'\bTenant,\s*', '', content)
content = re.sub(r'\bCloudUser,\s*', '', content)
content = re.sub(r'\bActionLog,\s*', '', content)
content = re.sub(r'\bSyncLog,\s*', '', content)

with open('backend/api/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Serializers rewritten safely.")
