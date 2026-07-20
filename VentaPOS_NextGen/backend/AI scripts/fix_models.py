import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''models.DecimalField(
        max_digits=12, decimal_places=2, default="0.00",
        validators=[MinValueValidator("0.00")]
    )'''

replacement = '''models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )'''

content = content.replace(target, replacement)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
