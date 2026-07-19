import re

with open('backend/api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean up the mangled broken lines that look like `class = SomeSerializer`
content = re.sub(r'class = [a-zA-Z]+Serializer\s*', '', content)

with open('backend/api/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Views cleaned again 3.")
