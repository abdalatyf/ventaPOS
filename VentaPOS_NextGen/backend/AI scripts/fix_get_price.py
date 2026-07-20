import os
path = 'D:/Projects/VentaPOS/VentaPOS_NextGen/backend/api/models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

get_price_method = '''
    def get_price_at_date(self, month: int, year: int) -> int:
        from django.db.models import Q
        
        latest_purchase = (
            self.purchase_invoice_items.filter(
                purchase_invoice__invoice_type="PURCHASE", is_deleted=False
            )
            .filter(
                Q(purchase_invoice__invoice_year__lt=year)
                | (Q(purchase_invoice__invoice_year=year) & Q(purchase_invoice__invoice_month__lte=month))
            )
            .order_by("-purchase_invoice__invoice_year", "-purchase_invoice__invoice_month", "-created_at")
            .first()
        )
        
        if latest_purchase:
            return latest_purchase.purchase_price
        return self.initial_purchase_price
'''

content = content.replace('def get_commission_at_date', get_price_method.lstrip() + '\n    def get_commission_at_date')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
