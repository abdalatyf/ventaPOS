import os
import re
import glob

files = glob.glob('D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/tests/*.py')
for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('from decimal import Decimal\n', '')
    content = re.sub(r'Decimal\("([0-9]+)\.[0-9]+"\)', r'\1', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
