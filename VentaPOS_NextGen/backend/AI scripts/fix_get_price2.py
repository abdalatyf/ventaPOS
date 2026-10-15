import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('purchase_invoice__invoice_type="PURCHASE", is_deleted=False', 'purchase_invoice__invoice_type="PURCHASE", is_deleted=False, purchase_invoice__is_deleted=False')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
