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
    InventoryItem, Receipt, SaleItem, 
    Salesperson, Branch
)
from .serializers import InventoryItemSerializer, ReceiptSerializer

class ToolsBaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        from .models import Branch
        branch = Branch.objects.filter(is_deleted=False).first()
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
        salesperson = Salesperson.objects.filter(id=salesperson_id).first()
        if not salesperson:
            return JsonResponse({"error": "المندوب غير موجود"}, status=404)

        items = InventoryItem.objects.filter(branch=request.branch)
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
            for rcpt_data in data:
                # Add is_confirmed=False so that it skips license and stock deduction
                rcpt_data['is_confirmed'] = False
                rcpt_data['sync_action'] = "NEW"
                rcpt_data['source'] = "USB"
                
                serializer = ReceiptSerializer(data=rcpt_data)
                if serializer.is_valid():
                    serializer.save()
                    created_count += 1
                else:
                    return Response({"error": f"بيانات فاتورة غير صالحة: {serializer.errors}"}, status=400)

        return Response({"message": f"تم استقبال {created_count} فاتورة بنجاح وبانتظار الاعتماد"}, status=200)

class ApprovePendingReceiptView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from .models import Receipt
        try:
            receipt = Receipt.objects.get(pk=pk, branch=request.branch)
        except Receipt.DoesNotExist:
            return Response({"error": "الفاتورة غير موجودة"}, status=404)

        if receipt.is_confirmed:
            return Response({"error": "تم اعتماد هذه الفاتورة مسبقاً"}, status=400)

        from dateutil.relativedelta import relativedelta
        from datetime import date
        from .models import ClientLicense
        from api.utils import generate_record_signature, generate_receipt_signature
        from django.db.models import Max
        from api.views import get_default_date

        try:
            with transaction.atomic():
                # 1. License Check & Deduction
                active_lic = (
                    ClientLicense.objects
                    .select_for_update()
                    .filter(is_deleted=False, invoices_balance__gt=0)
                    .first()
                )
                if not active_lic:
                    return Response({"error": "لا يمكن الاعتماد، رصيد الفواتير للرخصة قد نفد. يرجى الشحن أولاً."}, status=400)
                
                try:
                    invoice_date = date(receipt.sale_year, receipt.sale_month, 1)
                except Exception:
                    return Response({"error": "تاريخ الفاتورة غير صحيح."}, status=400)
                    
                lic_start_month = active_lic.start_date.replace(day=1)
                if invoice_date < lic_start_month:
                    return Response({"error": "التاريخ يسبق بداية الاشتراك."}, status=400)
                    
                if active_lic.expiry_date:
                    last_allowed_month = (active_lic.expiry_date - relativedelta(months=2)).replace(day=1)
                    if invoice_date > last_allowed_month:
                        return Response({"error": "التاريخ بعد انتهاء الاشتراك."}, status=400)
                    grace_end = active_lic.expiry_date + relativedelta(days=25)
                    if date.today() > grace_end:
                        return Response({"error": "انتهت فترة الاشتراك."}, status=400)

                # 2. Assign receipt_number
                last = Receipt.objects.select_for_update().filter(branch=receipt.branch, receipt_number__isnull=False).aggregate(m=Max('receipt_number'))['m']
                receipt.receipt_number = (last + 1) if last else 1

                # 3. Stock Validation
                default_year, default_month = get_default_date()
                if receipt.receipt_type != "RETURN":
                    for item in receipt.sale_items.filter(is_deleted=False):
                        safe_limit = item.inventory_item.get_safe_available_qty(receipt.sale_month, receipt.sale_year, default_month, default_year)
                        if item.quantity > safe_limit:
                            return Response({"error": f"عفواً، لا يمكن الاعتماد! أقصى كمية يمكن بيعها للصنف '{item.inventory_item.name}' هي ({safe_limit})."}, status=400)

                # 4. Generate Hash
                items_data = list(receipt.sale_items.filter(is_deleted=False).values("inventory_item_id", "quantity", "unit_price"))
                receipt.receipt_hash = generate_receipt_signature(
                    receipt.receipt_number,
                    receipt.total_amount,
                    receipt.sale_month,
                    receipt.sale_year,
                    items_data,
                )
                
                # 5. Confirm and Save Receipt
                receipt.is_confirmed = True
                receipt.save(update_fields=["receipt_number", "receipt_hash", "is_confirmed"])

                # 6. Save License
                active_lic.invoices_balance -= 1
                active_lic.license_code_hash = generate_record_signature(
                    active_lic.expiry_date,
                    active_lic.invoices_balance,
                    active_lic.machine_id,
                    active_lic.product_id,
                    active_lic.is_active,
                )
                active_lic.save(update_fields=["invoices_balance", "license_code_hash"])

            return Response({"message": "تم اعتماد الفاتورة بنجاح"}, status=200)

        except Exception as e:
            return Response({"error": f"فشل اعتماد الفاتورة: {str(e)}"}, status=400)
