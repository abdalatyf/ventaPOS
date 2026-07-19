import re

with open('backend/api/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Tenant, CloudUser, ActionLog classes
content = re.sub(r'class TenantSerializer[\s\S]*?(?=class )', '', content)
content = re.sub(r'class CloudUserSerializer[\s\S]*?(?=class )', '', content)
content = re.sub(r'class ActionLogSerializer[\s\S]*?(?=class )', '', content)

# 2. Remove imports for Tenant, CloudUser, ActionLog
content = re.sub(r'\bTenant,\b\s*', '', content)
content = re.sub(r'\bCloudUser,\b\s*', '', content)
content = re.sub(r'\bActionLog,\b\s*', '', content)

# 3. Remove tenant from fields array
content = re.sub(r"(['\"]tenant['\"],\s*)", '', content)
content = re.sub(r"(,\s*['\"]tenant['\"])", '', content)
content = re.sub(r"(['\"]tenant['\"])", '', content)

# 4. Remove tenant overriding in create/update
# e.g., validated_data['tenant'] = Tenant.objects.using("default").first()
content = re.sub(r'[ \t]*tenant\s*=\s*Tenant\.objects\.using\("default"\)\.first\(\)\n', '', content)
content = re.sub(r'[ \t]*validated_data\[["\']tenant["\']\]\s*=\s*tenant\n', '', content)

with open('backend/api/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Serializers updated.")
