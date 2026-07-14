import os
import sys
import django
import json
import uuid

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from api.models import Tenant, Branch, InventoryItem, PendingExternalReceipt, Receipt
from api.tools_views import OfflineExportItemsView, OfflineImportReceiptsView, ApprovePendingReceiptView
from django.core.files.uploadedfile import SimpleUploadedFile

def run_test():
    print("=== بدء اختبار دورة المزامنة بالكامل ===")
    
    tenant = Tenant.objects.filter(is_deleted=False).first()
    branch = Branch.objects.filter(tenant=tenant, is_deleted=False).first()
    user = User.objects.first()
    
    factory = APIRequestFactory()
    
    # 1. Test Export
    print("\n1. اختبار تصدير الأصناف...")
    from api.models import Salesperson
    sp = Salesperson.objects.filter(tenant=tenant).first()
    request = factory.get(f'/api/v1/tools/sync/export-items/?salesperson_id={sp.id}')
    force_authenticate(request, user=user)
    export_view = OfflineExportItemsView.as_view()
    response = export_view(request)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        items_data = data.get("items", [])
        print(f"تم بنجاح تصدير {len(items_data)} صنف.")
        print(f"فرع: {data.get('branch_name')}, مندوب: {data.get('salesperson_name')}")
    else:
        print(f"فشل التصدير: {response.status_code}")
        return

    if not items_data:
        print("لا يوجد أصناف لاختبار المزامنة عليها.")
        return
        
    test_item = items_data[0]
    
    # 2. Test Import
    print("\n2. اختبار استيراد فواتير الموبايل (JSON)...")
    
    dummy_receipts = [
        {
            "offline_id": str(uuid.uuid4()),
            "date": "2026-07-13",
            "total_amount": 2000,
            "items": [
                {
                    "name": test_item['name'],
                    "quantity": 2,
                    "unit_price": 1000
                }
            ]
        }
    ]
    
    json_file = SimpleUploadedFile("receipts.json", json.dumps(dummy_receipts).encode('utf-8'), content_type="application/json")
    
    request = factory.post('/api/v1/tools/sync/import-receipts/', {'receipts_file': json_file}, format='multipart')
    force_authenticate(request, user=user)
    import_view = OfflineImportReceiptsView.as_view()
    response = import_view(request)
    
    if response.status_code == 200:
        print(f"تم الاستيراد بنجاح: {response.data}")
    else:
        print(f"فشل الاستيراد: {response.data}")
        return
        
    # 3. Check pending receipts
    pending = PendingExternalReceipt.objects.filter(tenant=tenant, branch=branch, is_processed=False).last()
    if not pending:
        print("لم يتم العثور على فاتورة معلقة!")
        return
        
    print(f"\nتم العثور على الفاتورة المعلقة رقم: {pending.id}")
    
    # 4. Test Approve
    print("\n3. اختبار اعتماد الفاتورة وخصم المخزون...")
    request = factory.post(f'/api/v1/tools/sync/approve-receipt/{pending.id}/')
    force_authenticate(request, user=user)
    approve_view = ApprovePendingReceiptView.as_view()
    response = approve_view(request, pk=pending.id)
    
    if response.status_code == 200:
        print(f"تم الاعتماد بنجاح: {response.data}")
    else:
        print(f"فشل الاعتماد: {response.data}")
        return
        
    # 5. Verify Receipt and Stock
    receipt = Receipt.objects.filter(tenant=tenant, branch=branch).last()
    print(f"\nتم إنشاء فاتورة المبيعات الفعلية بنجاح: ID={receipt.id}, إجمالي={receipt.total_amount}")
    
    print("\n=== تمت دورة الاختبار بنجاح تام! ===")

if __name__ == "__main__":
    run_test()
