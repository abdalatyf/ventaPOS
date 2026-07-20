import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/tests/test_reporting_endpoints.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(', "15000.00")', ', 15000)')
content = content.replace(', "80000.00")', ', 80000)')
content = content.replace(', "60000.00")', ', 60000)')
content = content.replace(', "5500.00")', ', 5500)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
