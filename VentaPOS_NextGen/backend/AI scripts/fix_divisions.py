import os
import re
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(' / current_qty if current_qty > 0 else 0.0', ' // current_qty if current_qty > 0 else 0')
content = content.replace(' // 100 / receipt_total', ' // (100 * receipt_total)')
content = content.replace(' / receipt_count if receipt_count > 0 else 0', ' // receipt_count if receipt_count > 0 else 0')
content = content.replace(' / qty if qty > 0 else 0', ' // qty if qty > 0 else 0')
content = content.replace(' / receipt.total_amount', ' // receipt.total_amount')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
