import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'[ \t]*tenant = self\._get_tenant\(\)\n', '', content)
content = content.replace('tenant=self._get_tenant(), ', '')
content = content.replace(', tenant=self._get_tenant()', '')
content = content.replace('tenant=self._get_tenant()', '')

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed all _get_tenant usages.")
