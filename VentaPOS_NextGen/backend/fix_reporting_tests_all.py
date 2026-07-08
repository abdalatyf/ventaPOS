import re

path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/tests/test_reporting_endpoints.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all "\d+.00" with \1
content = re.sub(r'"(\d+)\.00"', r'\1', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
