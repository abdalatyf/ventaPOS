import re
import os

filepath = 'backend/api/tools_views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace the post method in ApprovePendingReceiptView
# I need to match class ApprovePendingReceiptView to the end of the class.

start_str = "class ApprovePendingReceiptView(ToolsBaseView):"
next_class_str = "class SmartImportWizardView(ToolsBaseView):"

start_idx = content.find(start_str)
end_idx = content.find(next_class_str)

if start_idx == -1 or end_idx == -1:
    print("Could not find classes")
    exit(1)

new_class = """class ApprovePendingReceiptView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            from datetime import datetime
            import uuid
            from django.db.models import Max
            from .models import PendingExternalReceipt, Salesperson, Receipt, InventoryItem, SaleItem
            
            pending = PendingExternalReceipt.objects.get(pk=pk, tenant=request.tenant, branch=request.branch)
            if pending.is_processed:
                return Response({"error": "تم معالجة هذه الفاتورة مسبقاً"}, status=400)

            data = pending.payload
            items_data = data.get('items', [])
            if not items_data:
                return Response({"error": "الفاتورة لا تحتوي على أصناف"}, status=400)

            salesperson = None
            if data.get('salesperson_id'):
                salesperson = Salesperson.objects.filter(id=data.get('salesperson_id'), tenant=request.tenant).first()
            if not salesperson:
                salesperson = Salesperson.objects.filter(tenant=request.tenant, branch=request.branch).first() # Fallback

            with transaction.atomic():
                max_local = Receipt.objects.filter(tenant=request.tenant).aggregate(Max('local_id'))['local_id__max'] or 0
                max_rn = Receipt.objects.filter(tenant=request.tenant).aggregate(Max('receipt_number'))['receipt_number__max'] or 0
                
                receipt = Receipt.objects.create(
                    tenant=request.tenant,
                    branch=request.branch,
                    salesperson=salesperson,
                    local_id=max_local + 1,
                    receipt_number=max_rn + 1,
                    client_uuid=uuid.uuid4(),
                    receipt_hash=str(uuid.uuid4()),
                    customer_name=data.get('customer_name', 'عميل أوفلاين'),
                    phone_number=data.get('phone_number', ''),
                    address='',
                    area='',
                    total_amount=int(data.get('total_amount', 0)),
                    down_payment=int(data.get('total_amount', 0)),
                    sale_year=datetime.now().year,
                    sale_month=datetime.now().month,
                    is_cash_sale=data.get('is_cash_sale', True),
                    products_text=f"معتمدة من الموبايل (دفعة {pending.batch_id})"
                )

                for item in items_data:
                    item_id = item.get('id') or item.get('item_id')
                    qty = int(float(item.get('quantity') or item.get('qty') or 1))
                    price = int(float(item.get('price') or item.get('unit_price') or 0))
                    
                    inv_item = InventoryItem.objects.filter(id=item_id, tenant=request.tenant).first()
                    if not inv_item:
                        inv_item = InventoryItem.objects.filter(name=item.get('name'), tenant=request.tenant).first()

                    if not inv_item:
                        raise Exception(f"الصنف غير موجود: {item.get('name', item_id)}")

                    SaleItem.objects.create(
                        tenant=request.tenant,
                        receipt=receipt,
                        inventory_item=inv_item,
                        quantity=qty,
                        unit_price=price,
                    )
                    
                pending.is_processed = True
                pending.status = "SUCCESS"
                pending.save()

        except Exception as e:
            pending.is_processed = True
            pending.status = f"FAILED: {str(e)}"
            pending.save()
            return Response({"error": f"فشل اعتماد الفاتورة: {str(e)}"}, status=400)

        return Response({"message": "تم اعتماد الفاتورة بنجاح"}, status=200)

"""

new_content = content[:start_idx] + new_class + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replaced ApprovePendingReceiptView successfully.")
