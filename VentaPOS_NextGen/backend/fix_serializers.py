import os
import re

serializers_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\serializers.py"

with open(serializers_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace "is_synced",
content = re.sub(r'\"is_synced\",\s*', '', content)
# Replace "is_synced" at the end of lists if any
content = re.sub(r',\s*\"is_synced\"', '', content)
content = re.sub(r'\"is_synced\"', '', content)

with open(serializers_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed is_synced from serializers.py successfully!")
