import re

with open('backend/api/tools_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove dangling commas left by tenant removal
content = re.sub(r'^\s*,\s*\n', '', content, flags=re.MULTILINE)

with open('backend/api/tools_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dangling commas removed.")
