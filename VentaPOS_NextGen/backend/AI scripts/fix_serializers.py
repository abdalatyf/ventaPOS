import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/serializers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from decimal import Decimal\n', '')
content = content.replace('Financial fields (DecimalField)', 'Financial fields (IntegerField)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
