import requests
import json
import threading
import time
from django.db import transaction
from django.conf import settings
from .models import (
    Branch, Receipt, Salesperson, InventoryItem, 
    CompanySetting, Expense, SyncDeletionLog
)
from .security_utils import get_machine_id

# إزالة الرابط الثابت حسب التعليمات

def check_internet():
    """
    فحص سريع جداً للإنترنت (بينغ على جوجل)
    """
    try:
        # Timeout 3 ثواني فقط، لو لم يرد يعتبر النت مقطوع
        requests.get('https://www.google.com', timeout=3)
        return True
    except:
        return False

def collect_payload():
    """
    تجميع البيانات التي لم ترفع بعد (is_synced=False)
    وتجميع سجلات المحذوفات
    """
    machine_id = get_machine_id()
    
    # القوائم التي سنملؤها بالبيانات
    payload = {
        'company_settings': {},
        'branches': [],
        'salespeople': [],
        'inventory': [],
        'receipts': [],
        'expenses': [],
        'stock_transactions': [],
        'deleted_items': []
    }
    
    has_data = False

    # 1. سجل المحذوفات (Deletions) 🗑️
    deleted_logs = SyncDeletionLog.objects.all()
    if deleted_logs.exists():
        has_data = True
        for log in deleted_logs:
            payload['deleted_items'].append({
                'table_name': log.table_name,
                'record_id': log.record_id
            })

    # 2. إعدادات الشركة ⚙️
    # نرسلها دائماً لضمان تطابق البيانات (أو يمكنك إضافة is_synced لها أيضاً)
    setting = CompanySetting.objects.first()
    if setting:
        payload['company_settings'] = {
            'name': setting.name,
            'description': setting.description,
            'phone1': setting.phone1,
            'phone2': setting.phone2,
            'footer_text': setting.footer_text
        }

    # 3. الفروع 🏢
    unsynced_branches = Branch.objects.filter(is_synced=False)
    if unsynced_branches.exists(): has_data = True
    for b in unsynced_branches:
        payload['branches'].append({
            'id': b.id,
            'name': b.name
        })

    # 4. الموظفين 👔
    unsynced_salespeople = Salesperson.objects.filter(is_synced=False)
    if unsynced_salespeople.exists(): has_data = True
    for sp in unsynced_salespeople:
        payload['salespeople'].append({
            'id': sp.id,
            'branch_id': sp.branch.id,
            'name': sp.name,
            'cloud_username': sp.cloud_username,
            'cloud_password': sp.cloud_password
        })

    # 5. المخزون / المنتجات 📦
    unsynced_inventory = InventoryItem.objects.filter(is_synced=False)
    if unsynced_inventory.exists(): has_data = True
    for item in unsynced_inventory:
        payload['inventory'].append({
            'id': item.id,
            'branch_id': item.branch.id,
            'name': item.name,
            'quantity': item.initial_quantity,
            'purchase_price': float(item.initial_purchase_price),
            'commission': float(item.initial_commission_amount),
            'created_at': item.created_at.isoformat() if item.created_at else None
        })

    # 6. الفواتير 🧾 (البيانات الأضخم)
    # نأخذ دفعة صغيرة (20 فاتورة) في المرة الواحدة لتجنب التحميل الزائد
    unsynced_receipts = Receipt.objects.filter(is_synced=False)[:20]
    if unsynced_receipts.exists(): has_data = True
    
    for r in unsynced_receipts:
        # أ) تجهيز العناصر (Items)
        items_data = []
        for item in r.items.all():
            items_data.append({
                'product_id': item.inventory_item.id,
                'product_name': item.inventory_item.name, # نأخذ الاسم الحالي
                'quantity': item.quantity,
                'price': float(item.unit_price)
            })

        # ب) تجهيز الأقساط (Payments)
        payments_data = []
        for p in r.payments.all():
            payments_data.append({
                'date': str(p.payment_date),
                'amount': float(p.amount)
            })

        # ج) تجميع الفاتورة نفسها
        payload['receipts'].append({
            'id': r.id,
            'receipt_number': r.receipt_number,
            'receipt_hash': r.receipt_hash,
            'sync_action': r.sync_action,
            'is_confirmed': r.is_confirmed,
            'branch_id': r.branch.id,
            'salesperson_id': r.salesperson.id if r.salesperson else None,
            'customer_name': r.customer_name,
            'phone_number': r.phone_number,
            'address': r.address,
            'area': r.area,
            'total_amount': float(r.total_amount),
            'down_payment': float(r.down_payment),
            'installment_system': r.installment_system,
            'sale_year': r.sale_year,
            'sale_month': r.sale_month,
            'is_cash_sale': r.is_cash_sale,
            'products_text': r.products_text,
            'receipt_hash': r.receipt_hash,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'items': items_data,
            'payments': payments_data
        })

    # 7. المصروفات 💸
    unsynced_expenses = Expense.objects.filter(is_synced=False)
    if unsynced_expenses.exists(): has_data = True
    for exp in unsynced_expenses:
        payload['expenses'].append({
            'id': exp.id,
            'branch_id': exp.branch.id,
            'amount': float(exp.amount),
            'description': exp.description,
            'expense_year': exp.expense_year,
            'expense_month': exp.expense_month,
            'created_at': exp.created_at.isoformat() if exp.created_at else None
        })

    # 8. حركات المخزن 🔄
    unsynced_stock_trans = []
    # Removed StockTransaction because it does not exist

    # نرجع كل الكائنات عشان نقدر نحدث حالتها بعد النجاح
    return (
        machine_id, payload, has_data,
        unsynced_branches, unsynced_salespeople, unsynced_inventory, 
        unsynced_receipts, unsynced_expenses, unsynced_stock_trans, deleted_logs
    )

def push_data_background():
    """
    الدالة التي ستعمل في الخلفية لإرسال البيانات
    """
    # 1. فحص الإنترنت أولاً
    if not check_internet():
        return # خروج صامت

    try:
        # 2. تجميع البيانات
        (
            machine_id, payload, has_data,
            branches_objs, salespeople_objs, inventory_objs, 
            receipts_objs, expenses_objs, stock_trans_objs, deleted_logs_objs
        ) = collect_payload()

        if not has_data:
            return # لا يوجد شيء لرفعه

        # 3. الإرسال للسيرفر
        setting = CompanySetting.objects.first()
        is_viewer = setting.is_cloud_viewer if setting else False
        
        base_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
        if is_viewer:
            target_url = f"{base_url.rstrip('/')}/api/v1/sync/mobile-push/"
        else:
            target_url = f"{base_url.rstrip('/')}/api/v1/sync/push/"
            
        full_data = {'machine_id': machine_id, 'payload': payload}
        response = requests.post(target_url, json=full_data, timeout=15)

        # 4. التحديث المحلي عند النجاح
        if response.status_code == 200:
            with transaction.atomic():
                # تحديث حالة is_synced لكل الجداول
                # نستخدم loops بدلاً من update() المباشر أحياناً لتجنب تضارب الـ Signals إذا وجدت
                # ولكن هنا update() أسرع وأكفأ
                
                branches_objs.update(is_synced=True)
                salespeople_objs.update(is_synced=True)
                inventory_objs.update(is_synced=True)
                
                # الفواتير (كل فاتورة على حدة لضمان الأمان)
                for r in receipts_objs:
                    r.is_synced = True
                    r.save()

                expenses_objs.update(is_synced=True)

                # حذف سجلات المحذوفات لأن السيرفر علم بها خلاص
                # نحذف بالـ ID لضمان عدم حذف سجلات جديدة أضيفت أثناء الارسال
                log_ids = list(deleted_logs_objs.values_list('id', flat=True))
                SyncDeletionLog.objects.filter(id__in=log_ids).delete()

    except Exception:
        # تجاهل أي خطأ (صمت تام) لعدم إزعاج المستخدم
        pass 

def get_last_sync_time():
    try:
        with open('last_sync_time.txt', 'r') as f:
            return f.read().strip()
    except:
        return '1970-01-01T00:00:00Z'

def set_last_sync_time(t):
    with open('last_sync_time.txt', 'w') as f:
        f.write(t)

def pull_from_cloud():
    if not check_internet():
        return
        
    if not CompanySetting.objects.exists():
        return
    
    last_sync = get_last_sync_time()
    base_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
    machine_id = get_machine_id()
    
    try:
        resp = requests.post(f"{base_url.rstrip('/')}/api/v1/sync/pull/", json={
            'machine_id': machine_id,
            'last_sync': last_sync
        }, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                payload = data.get('payload', {})
                with transaction.atomic():
                    # Branches
                    for b in payload.get('branches', []):
                        Branch.objects.update_or_create(
                            id=b.get('local_id', b.get('id')),
                            defaults={'name': b['name'], 'is_synced': True}
                        )
                    
                    # Salespeople
                    for s in payload.get('salespeople', []):
                        Salesperson.objects.update_or_create(
                            id=s.get('local_id', s.get('id')),
                            defaults={
                                'branch_id': s['branch_id'],
                                'name': s['name'],
                                'cloud_username': s.get('cloud_username'),
                                'cloud_password': s.get('cloud_password'),
                                'is_synced': True
                            }
                        )
                    
                    # Inventory
                    for i in payload.get('inventory', []):
                        InventoryItem.objects.update_or_create(
                            id=i.get('local_id', i.get('id')),
                            defaults={
                                'branch_id': i['branch_id'],
                                'name': i['name'],
                                'initial_quantity': i.get('quantity', 0),
                                'initial_purchase_price': i.get('purchase_price', 0),
                                'initial_commission_amount': i.get('commission', 0),
                                'initial_month': i.get('initial_month', 1),
                                'initial_year': i.get('initial_year', 2026),
                                'is_synced': True
                            }
                        )
                    
                    # Expenses
                    for e in payload.get('expenses', []):
                        Expense.objects.update_or_create(
                            id=e.get('local_id', e.get('id')),
                            defaults={
                                'branch_id': e['branch_id'],
                                'amount': e['amount'],
                                'description': e['description'],
                                'expense_year': e['expense_year'],
                                'expense_month': e['expense_month'],
                                'is_synced': True
                            }
                        )
                        
                    # Receipts
                    from .models import Receipt, SaleItem, InstallmentPayment
                    for r in payload.get('receipts', []):
                        r_hash = r.get('receipt_hash')
                        r_id = r.get('local_id', r.get('id'))
                        
                        receipt, created = Receipt.objects.update_or_create(
                            receipt_hash=r_hash,
                            defaults={
                                'id': r_id,
                                'receipt_number': r['receipt_number'],
                                'branch_id': r['branch_id'],
                                'salesperson_id': r.get('salesperson_id'),
                                'customer_name': r.get('customer_name', ''),
                                'phone_number': r.get('phone_number', ''),
                                'address': r.get('address', ''),
                                'area': r.get('area', ''),
                                'total_amount': r.get('total_amount', 0),
                                'down_payment': r.get('down_payment', 0),
                                'installment_system': r.get('installment_system', ''),
                                'sale_year': r['sale_year'],
                                'sale_month': r['sale_month'],
                                'is_cash_sale': r.get('is_cash_sale', False),
                                'products_text': r.get('products_text', ''),
                                'is_synced': True
                            }
                        )
                        
                        SaleItem.objects.filter(receipt=receipt).delete()
                        for item in r.get('items', []):
                            SaleItem.objects.create(
                                receipt=receipt,
                                inventory_item_id=item['product_id'],
                                quantity=item['quantity'],
                                unit_price=item['price']
                            )
                            
                        InstallmentPayment.objects.filter(receipt=receipt).delete()
                        for payment in r.get('payments', []):
                            InstallmentPayment.objects.create(
                                receipt=receipt,
                                payment_date=payment['date'],
                                amount=payment['amount']
                            )
                                
                from datetime import datetime, timezone
                now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                set_last_sync_time(now_str)
                
    except Exception as e:
        pass

# ==========================================
# المشغل الآلي (The Auto Runner) 🤖
# ==========================================
def start_auto_sync():
    """
    تشغيل المزامنة في Thread منفصل
    """
    thread = threading.Thread(target=_sync_loop, daemon=True)
    thread.start()

def _sync_loop():
    while True:
        # تنفيذ محاولة المزامنة
        push_data_background()
        pull_from_cloud()
        pull_pending_receipts()
        
        # الانتظار دقيقة قبل المحاولة التالية
        time.sleep(60)

def pull_pending_receipts():
    if not check_internet() or not CompanySetting.objects.exists():
        return
        
    base_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
    machine_id = get_machine_id()
    
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/v1/sync/pending-receipts/", params={
            'machine_id': machine_id,
            'role': 'manager'
        }, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                pending = data.get('pending_receipts', [])
                with transaction.atomic():
                    for r in pending:
                        action = r.get('sync_action', 'NEW')
                        receipt_hash = r.get('receipt_hash')
                        if not receipt_hash:
                            continue
                            
                        # Extract basic fields
                        r_number = r.get('receipt_number', 0)
                        branch_id = r.get('branch_id')
                        salesperson_id = r.get('salesperson_id')
                        total = r.get('total_amount', 0)
                        
                        # We put the entire payload in PendingExternalReceipt
                        from salesapp.models import PendingExternalReceipt, Branch
                        branch_obj = Branch.objects.filter(id=branch_id).first()
                        if branch_obj:
                            r_payload = dict(r)
                            r_payload['sync_action'] = action
                            if action == 'EDIT':
                                r_payload['is_modified_request'] = True
                            elif action == 'DELETE':
                                r_payload['is_deleted_request'] = True
                            
                            exists = PendingExternalReceipt.objects.filter(
                                branch=branch_obj, source='CLOUD', is_processed=False
                            ).filter(payload__icontains=receipt_hash).exists()
                            
                            if not exists:
                                PendingExternalReceipt.objects.create(
                                    batch_id=f"CLOUD_{machine_id}_{r.get('sale_month', 1)}_{r.get('sale_year', 2026)}",
                                    branch=branch_obj,
                                    source='CLOUD',
                                    payload=r_payload
                                )
                                
    except Exception as e:
        print(f"Error pulling pending receipts: {e}")