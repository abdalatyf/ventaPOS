from api.models import Receipt
r = Receipt.objects.filter(is_deleted=False).order_by('-sale_year', '-sale_month').first()
print('Latest receipt year:', r.sale_year, 'month:', r.sale_month, 'branch:', r.branch_id)
