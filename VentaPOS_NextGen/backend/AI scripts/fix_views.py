import os
import re
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove imports
content = content.replace('from decimal import Decimal', '')

# Replace Decimal literals
content = content.replace('Decimal("0.00")', '0')
content = content.replace('Decimal("0.10")', '0.1')

# Replace Decimal wrappers
content = re.sub(r'Decimal\(([a-zA-Z0-9_.]+)\)', r'\1', content)

# Replace f-strings for floats
content = re.sub(r'f"\{([a-zA-Z0-9_.\'\[\]\(\)\+\-\s]+):\.2f\}"', r'\1', content)

# Fix commission calculation: * 0.1 to // 10 to keep it integer
content = content.replace('* 0.1', '// 10')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
