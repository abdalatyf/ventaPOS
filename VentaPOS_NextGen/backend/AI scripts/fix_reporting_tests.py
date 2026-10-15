import re

path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/tests/test_reporting_endpoints.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace "xxxx.00" with xxxx
content = re.sub(r'self\.assertEqual\(data\["(.+?)"\]\[([0-9]+)\]\["amount"\], "([0-9]+)\.00"\)', r'self.assertEqual(data["\1"][\2]["amount"], \3)', content)
content = re.sub(r'self\.assertEqual\(data\["totals"\]\["(.+?)"\], "([0-9]+)\.00"\)', r'self.assertEqual(data["totals"]["\1"], \2)', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
