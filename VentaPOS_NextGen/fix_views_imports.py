import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'\bTenant,\s*', '', content)
content = re.sub(r'\bCloudUser,\s*', '', content)
content = re.sub(r'\bActionLog,\s*', '', content)
content = re.sub(r'\bSyncLog,\s*', '', content)
content = re.sub(r'\bTenant\b\s*', '', content)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Imports cleaned.")
