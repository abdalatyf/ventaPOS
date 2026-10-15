import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return stock + purchases + adj_plus - sales - returns - adj_minus',
    'return max(0, stock + purchases + adj_plus - sales - returns - adj_minus)'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
