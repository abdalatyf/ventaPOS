import os
import sqlite3
import tempfile
import json
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from django.db import transaction

from .models import (
    InventoryItem, PendingExternalReceipt, Receipt, SaleItem, 
    ActionLog, Salesperson, Branch, Tenant
)
from .serializers import InventoryItemSerializer

class ToolsBaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        tenant = Tenant.objects.filter(is_deleted=False).first()
        branch = Branch.objects.filter(tenant=tenant, is_deleted=False).first()
        request.tenant = tenant
        request.branch = branch
        return super().dispatch(request, *args, **kwargs)

class BackupDownloadView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        db_path = settings.DATABASES['default']['NAME']
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            filename = f"Backup_VentaPOS_{timestamp}.sqlite3"
            
            temp_dir = tempfile.gettempdir()
            temp_backup_path = os.path.join(temp_dir, filename)

            # Hot backup
            source_conn = sqlite3.connect(db_path, timeout=20)
            dest_conn = sqlite3.connect(temp_backup_path)
            with dest_conn:
                source_conn.backup(dest_conn, pages=100, sleep=0.01)
            dest_conn.close()
            source_conn.close()

            return FileResponse(open(temp_backup_path, 'rb'), as_attachment=True, filename=filename)
        except Exception as e:
            return Response({"error": f"فشل النسخ الاحتياطي: {str(e)}"}, status=500)

class BackupUploadView(ToolsBaseView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('backup_file')
        if not file_obj:
            return Response({"error": "يرجى اختيار ملف النسخة الاحتياطية"}, status=400)
        
        if not file_obj.name.endswith(('.sqlite3', '.db')):
            return Response({"error": "امتداد الملف غير مدعوم"}, status=400)

        temp_file_path = os.path.join(tempfile.gettempdir(), file_obj.name)
        with open(temp_file_path, 'wb+') as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)

        # Integrity Check
        try:
            conn = sqlite3.connect(temp_file_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            if result[0] != "ok":
                return Response({"error": "ملف قاعدة البيانات تالف أو غير صالح للاستعادة"}, status=400)
        except Exception as e:
            return Response({"error": f"فشل فحص النسخة: {str(e)}"}, status=400)

        # Stage for restore
        try:
            local_app_data = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
            db_dir = os.path.join(local_app_data, 'VentaPOS')
            os.makedirs(db_dir, exist_ok=True)
            pending_path = os.path.join(db_dir, 'restore_pending.bin')
            
            with open(pending_path, 'wb') as dest:
                with open(temp_file_path, 'rb') as src:
                    dest.write(src.read())
            
            return Response({"message": "تم رفع وفحص النسخة بنجاح. سيتم تطبيقها عند إعادة تشغيل البرنامج."}, status=200)
        except Exception as e:
            return Response({"error": f"فشل حفظ النسخة المعلقة: {str(e)}"}, status=500)

class OfflineExportItemsView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        salesperson_id = request.GET.get('salesperson_id')
        if not salesperson_id:
            return JsonResponse({"error": "يرجى تحديد المندوب"}, status=400)

        from .models import Salesperson
        salesperson = Salesperson.objects.filter(id=salesperson_id, tenant=request.tenant).first()
        if not salesperson:
            return JsonResponse({"error": "المندوب غير موجود"}, status=404)

        items = InventoryItem.objects.filter(tenant=request.tenant, branch=request.branch)
        items_data = [{"id": item.id, "name": item.name} for item in items]
        
        data = {
            "branch_id": request.branch.id,
            "branch_name": request.branch.name,
            "salesperson_id": salesperson.id,
            "salesperson_name": salesperson.name,
            "items": items_data
        }
        
        return JsonResponse(data, safe=False)

class OfflineImportReceiptsView(ToolsBaseView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        if 'receipts_file' in request.FILES:
            file_obj = request.FILES['receipts_file']
            try:
                data = json.load(file_obj)
            except Exception as e:
                return Response({"error": "ملف JSON غير صالح"}, status=400)
        else:
            data = request.data
            
        if not isinstance(data, list):
            return Response({"error": "يجب أن تكون البيانات قائمة من الفواتير"}, status=400)

        created_count = 0
        batch_id = f"OFFLINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with transaction.atomic():
            for rcpt in data:
                PendingExternalReceipt.objects.create(
                    tenant=request.tenant,
                    branch=request.branch,
                    batch_id=batch_id,
                    source='USB',  # Generic for offline JSON/USB
                    payload=rcpt,
                    is_processed=False
                )
                created_count += 1

        return Response({"message": f"تم استقبال {created_count} فاتورة بنجاح في قائمة الانتظار"}, status=200)

class ApprovePendingReceiptView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            pending = PendingExternalReceipt.objects.get(pk=pk, tenant=request.tenant, branch=request.branch)
        except PendingExternalReceipt.DoesNotExist:
            return Response({"error": "الفاتورة المعلقة غير موجودة"}, status=404)

        if pending.is_processed:
            return Response({"error": "تم اعتماد هذه الفاتورة مسبقاً"}, status=400)

        data = pending.payload
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                data = {}

        items_data = data.get('items', [])
        if not items_data:
            return Response({"error": "لا يوجد أصناف في الفاتورة"}, status=400)

        from django.utils import timezone
        from django.db.models import Max

        try:
            with transaction.atomic():
                # Get max local_id and receipt_number
                max_local = Receipt.objects.filter(tenant=request.tenant).aggregate(Max('local_id'))['local_id__max'] or 0
                max_rn = Receipt.objects.filter(tenant=request.tenant).aggregate(Max('receipt_number'))['receipt_number__max'] or 0

                local_time = data.get('created_at_local')
                if local_time:
                    from dateutil.parser import parse
                    try:
                        local_time = parse(local_time)
                    except:
                        local_time = timezone.now()
                else:
                    local_time = timezone.now()

                salesperson = Salesperson.objects.filter(tenant=request.tenant, branch=request.branch).first() # Fallback
                receipt = Receipt.objects.create(
                    tenant=request.tenant,
                    branch=request.branch,
                    local_id=max_local + 1,
                    receipt_number=max_rn + 1,
                    customer_name=data.get('customer_name', 'عميل أوفلاين'),
                    phone_number=data.get('phone_number', ''),
                    salesperson=salesperson,
                    total_amount=data.get('total_amount', 0),
                    down_payment=data.get('total_amount', 0),
                    sale_year=local_time.year,
                    sale_month=local_time.month,
                    is_cash_sale=data.get('is_cash_sale', True),
                    products_text=f"معتمدة من الموبايل (دفعة {pending.batch_id})",
                    created_at_local=local_time
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
                        unit_price=price
                    )
                    
                pending.is_processed = True
                pending.status = "SUCCESS"
                pending.save()

            return Response({"message": "تم اعتماد الفاتورة وخصم المخزون بنجاح"}, status=200)

        except Exception as e:
            pending.is_processed = True
            pending.status = f"FAILED: {str(e)}"
            pending.save()
            return Response({"error": f"فشل اعتماد الفاتورة: {str(e)}"}, status=400)

class SmartImportWizardView(ToolsBaseView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            return Response({"error": "يرجى اختيار ملف"}, status=400)
            
        try:
            df = pd.read_excel(excel_file).fillna('')
            imported_count = 0
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    name = str(row.get('اسم الصنف', '')).strip()
                    if not name:
                        continue
                    
                    price = float(row.get('سعر البيع', 0) or 0)
                    qty = float(row.get('الكمية', 0) or 0)
                    
                    InventoryItem.objects.update_or_create(
                        tenant=request.tenant,
                        branch=request.branch,
                        name=name,
                        defaults={
                            'selling_price_cash': price,
                            'available_quantity': qty,
                        }
                    )
                    imported_count += 1

            return Response({"message": f"تم استيراد {imported_count} صنف بنجاح"}, status=200)
        except Exception as e:
            return Response({"error": f"فشل الاستيراد: {str(e)}"}, status=500)
