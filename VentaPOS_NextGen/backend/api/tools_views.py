import os
import sqlite3
import tempfile
import json
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
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
        branch_id = request.headers.get('X-Branch-ID') or request.GET.get('branch_id')
        branch = None
        if branch_id:
            try:
                branch = Branch.objects.filter(id=int(branch_id), is_deleted=False).first()
            except (ValueError, TypeError):
                pass
        if not branch:
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

            # Flush WAL changes to main database before backup
            try:
                checkpoint_conn = sqlite3.connect(db_path, timeout=30)
                checkpoint_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                checkpoint_conn.close()
            except Exception as cp_err:
                print(f"Warning during WAL checkpoint: {cp_err}")

            # Hot backup using sqlite3 backup API
            source_conn = sqlite3.connect(db_path, timeout=30)
            dest_conn = sqlite3.connect(temp_backup_path)
            with dest_conn:
                source_conn.backup(dest_conn, pages=100, sleep=0.01)
            dest_conn.close()
            source_conn.close()

            file_handle = open(temp_backup_path, 'rb')
            response = FileResponse(file_handle, as_attachment=True, filename=filename)
            orig_close = response.close
            def _cleanup():
                orig_close()
                try:
                    if os.path.exists(temp_backup_path):
                        os.unlink(temp_backup_path)
                except OSError:
                    pass
            response.close = _cleanup
            return response
        except Exception as e:
            return Response({"error": f"فشل النسخ الاحتياطي: {str(e)}"}, status=500)

class BackupUploadView(ToolsBaseView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        import shutil
        from pathlib import Path
        from django.db import connections

        file_obj = request.FILES.get('backup_file')
        if not file_obj:
            return Response({"error": "يرجى اختيار ملف النسخة الاحتياطية"}, status=400)
        
        safe_filename = os.path.basename(file_obj.name)
        if not safe_filename.endswith(('.sqlite3', '.db')):
            return Response({"error": "امتداد الملف غير مدعوم، يرجى اختيار ملف .sqlite3 أو .db"}, status=400)

        temp_file_path = os.path.join(tempfile.gettempdir(), safe_filename)
        with open(temp_file_path, 'wb+') as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)

        # 1. Integrity Check & Table Schema Validation
        try:
            conn = sqlite3.connect(temp_file_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            if not result or result[0] != "ok":
                conn.close()
                return Response({"error": "ملف قاعدة البيانات تالف أو غير صالح للاستعادة"}, status=400)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            required_tables = {
                'salesapp_receipt', 'salesapp_saleitem', 'salesapp_inventoryitem',
                'salesapp_purchaseinvoice', 'salesapp_branch', 'salesapp_salesperson',
                'salesapp_companysetting', 'salesapp_clientlicense'
            }
            if not required_tables.issubset(tables):
                return Response({"error": "ملف قاعدة البيانات غير متوافق مع نظام VentaPOS (جداول مفقودة)"}, status=400)
        except Exception as e:
            return Response({"error": f"فشل فحص النسخة: {str(e)}"}, status=400)

        # 2. Perform Immediate Live Restore with Fallback Staging
        db_path = Path(settings.DATABASES['default']['NAME'])
        pending_path = db_path.parent / 'restore_pending.bin'

        # Stage fallback copy first
        try:
            shutil.copy2(temp_file_path, pending_path)
        except Exception as stage_err:
            print(f"Warning staging restore file: {stage_err}")

        try:
            # Close existing active Django DB connections to release locks on Windows
            connections.close_all()

            # Automatic pre-restore snapshot
            backups_dir = db_path.parent / 'backups'
            backups_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_file = backups_dir / f"pre_restore_{timestamp}.sqlite3"
            if db_path.exists() and db_path.stat().st_size > 0:
                try:
                    src_conn = sqlite3.connect(str(db_path))
                    dst_conn = sqlite3.connect(str(pre_restore_file))
                    with dst_conn:
                        src_conn.backup(dst_conn)
                    dst_conn.close()
                    src_conn.close()
                except Exception as pre_err:
                    print(f"Warning creating pre-restore backup: {pre_err}")

            # Live overwrite of the primary database file FIRST (before deleting wal/shm)
            # If copy2 fails (e.g. PermissionError on Windows), live WAL/SHM are preserved intact!
            shutil.copy2(temp_file_path, db_path)

            # Remove stale WAL and SHM files to prevent replaying old transactions
            wal_file = Path(str(db_path) + '-wal')
            shm_file = Path(str(db_path) + '-shm')
            if wal_file.exists():
                wal_file.unlink(missing_ok=True)
            if shm_file.exists():
                shm_file.unlink(missing_ok=True)

            # Re-initialize WAL and truncate on the new file
            verify_conn = sqlite3.connect(str(db_path), timeout=30)
            verify_conn.execute("PRAGMA journal_mode=WAL;")
            verify_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            cur = verify_conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()
            verify_conn.close()

            connections.close_all()

            # Run migrations to automatically upgrade older backup schemas
            from django.core.management import call_command
            try:
                call_command('migrate', interactive=False)
            except Exception as mig_err:
                # If migration fails, rollback to pre-restore snapshot
                if pre_restore_file.exists():
                    shutil.copy2(pre_restore_file, db_path)
                    if wal_file.exists():
                        wal_file.unlink(missing_ok=True)
                    if shm_file.exists():
                        shm_file.unlink(missing_ok=True)
                connections.close_all()
                return Response({"error": f"فشل ترقية مخطط قاعدة البيانات المستعادة: {str(mig_err)}"}, status=400)

            connections.close_all()

            # Clean up pending file since live restore succeeded
            if pending_path.exists():
                pending_path.unlink(missing_ok=True)

            return Response({
                "status": "success",
                "message": "تم استعادة قاعدة البيانات بنجاح. جاري تحديث بيانات البرنامج..."
            }, status=200)

        except Exception as swap_err:
            # Staged file remains in pending_path for launcher.py startup recovery
            return Response({
                "status": "pending_restart",
                "message": f"تم فحص النسخة واعتمادها بنجاح. تعذر التبديل الحي بسبب قفل النظام ({str(swap_err)}). يرجى إعادة تشغيل البرنامج لتطبيق الاستعادة."
            }, status=200)

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
                    serializer.save(is_confirmed=False)
                    created_count += 1
                else:
                    return Response({"error": f"بيانات فاتورة غير صالحة: {serializer.errors}"}, status=400)

        return Response({"message": f"تم استقبال {created_count} فاتورة بنجاح وبانتظار الاعتماد"}, status=200)

class PendingReceiptsListView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import Receipt
        from .serializers import ReceiptSerializer
        branch = getattr(request, 'branch', None)
        pending = Receipt.objects.filter(is_confirmed=False, is_deleted=False)
        if branch:
            pending = pending.filter(branch=branch)
        pending = pending.order_by("-created_at")
        serializer = ReceiptSerializer(pending, many=True)
        return Response(serializer.data, status=200)

class ApprovePendingReceiptView(ToolsBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from .models import Receipt
        try:
            branch = getattr(request, 'branch', None)
            receipt = None
            if branch:
                receipt = Receipt.objects.filter(pk=pk, branch=branch).first()
            if not receipt:
                receipt = Receipt.objects.get(pk=pk)
        except Receipt.DoesNotExist:
            return Response({"error": "الفاتورة غير موجودة"}, status=404)

        if receipt.is_confirmed:
            return Response({"error": "تم اعتماد هذه الفاتورة مسبقاً"}, status=400)

        from dateutil.relativedelta import relativedelta
        from datetime import date
        from .models import ClientLicense
        from api.utils.security_utils import generate_record_signature, generate_receipt_signature
        from django.db.models import Max
        from api.views import get_default_date

        try:
            with transaction.atomic():
                # 1. License Check & Deduction
                from api.services.receipt_service import get_active_license, get_license_date_bounds
                active_lic = get_active_license(select_for_update=True)
                if not active_lic:
                    return Response({"error": "لا توجد رخصة نشطة للنظام."}, status=400)
                
                if active_lic.invoices_balance is not None and active_lic.invoices_balance <= 0:
                    return Response({"error": "لا يمكن الاعتماد، رصيد الفواتير للرخصة قد نفد. يرجى الشحن أولاً."}, status=400)
                
                try:
                    invoice_date = date(receipt.sale_year, receipt.sale_month, 1)
                except Exception:
                    return Response({"error": "تاريخ الفاتورة غير صحيح."}, status=400)
                    
                start_date, last_allowed_month, grace_end = get_license_date_bounds(active_lic)
                if start_date:
                    lic_start_month = start_date.replace(day=1)
                    if invoice_date < lic_start_month:
                        return Response({"error": "التاريخ يسبق بداية الاشتراك."}, status=400)
                    
                if last_allowed_month and invoice_date > last_allowed_month:
                    return Response({"error": "التاريخ بعد انتهاء الاشتراك."}, status=400)
                if grace_end and date.today() > grace_end:
                    return Response({"error": "انتهت فترة الاشتراك."}, status=400)

                # 2. Assign receipt_number
                receipt.receipt_number = Receipt.get_next_receipt_number(receipt.branch)

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
