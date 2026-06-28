import json
import uuid
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import (
    ServerLicense, ServerReceipt, ServerSaleItem, ServerInstallmentPayment, 
    ServerBranch, ServerInventoryItem, ServerExpense, ServerStockTransaction,
    ServerSalesperson, ServerCompanySetting, MobileProvisionToken, ServerCloudUser,
    ServerSupplier, ServerPurchaseInvoice, ServerPurchaseInvoiceItem, ServerCommissionHistory
)

@method_decorator(csrf_exempt, name='dispatch')
class SyncIngestView(View):
    def post(self, request):
        try:
            # 1. استقبال وتفكيك البيانات
            data = json.loads(request.body)
            machine_id = data.get('machine_id')
            payload = data.get('payload', {})
            
            # 2. التفتيش الأمني 👮‍♂️ — Auto-register on first sync
            license = ServerLicense.objects.filter(machine_id=machine_id).first()
            
            if not license:
                # Auto-register: Desktop is syncing for the first time
                online_info = data.get('online_license_info', {})
                client_name = payload.get('company_settings', {}).get('name', '')
                expiry_str = online_info.get('online_expiry_date')
                expiry_date = None
                if expiry_str:
                    from datetime import datetime
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        pass
                
                license = ServerLicense(
                    machine_id=machine_id,
                    client_name=client_name,
                    is_active=True,
                    is_online_active=True,
                    online_expiry_date=expiry_date
                )
                license.save()  # company_code auto-generated
            
            if not license.is_active:
                return JsonResponse({'status': 'error', 'message': 'License is deactivated'}, status=403)
            
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online sync is disabled for this machine'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online sync license has expired'}, status=403)

            # تحديث وقت آخر ظهور
            license.last_sync_at = timezone.now()
            license.save()

            processed_count = 0

            # 3. الحفظ في قاعدة البيانات (كتلة واحدة)
            with transaction.atomic():
                
                # ==========================
                # أ) البيانات الأساسية (Reference Data)
                # ==========================
                
                # 1. إعدادات الشركة
                settings_data = payload.get('company_settings', None)
                if settings_data:
                    ServerCompanySetting.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=1, # نفترض دائماً وجود إعداد واحد
                        defaults={
                            'name': settings_data.get('name', ''),
                            'description': settings_data.get('description', ''),
                            'phone1': settings_data.get('phone1', ''),
                            'phone2': settings_data.get('phone2', ''),
                            'footer_text': settings_data.get('footer_text', '')
                        }
                    )

                # 2. الفروع
                for b in payload.get('branches', []):
                    ServerBranch.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=b['id'],
                        defaults={'name': b['name']}
                    )

                # 3. الموظفين
                for sp in payload.get('salespeople', []):
                    defaults_dict = {
                        'local_branch_id': sp['branch_id'],
                        'name': sp['name']
                    }
                    if 'cloud_username' in sp:
                        defaults_dict['cloud_username'] = sp['cloud_username']
                    if 'cloud_password' in sp:
                        defaults_dict['cloud_password'] = sp['cloud_password']
                        
                    ServerSalesperson.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=sp['id'],
                        defaults=defaults_dict
                    )

                # 4. المنتجات (المخزون)
                for item in payload.get('inventory', []):
                    ServerInventoryItem.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=item['id'],
                        defaults={
                            'local_branch_id': item['branch_id'],
                            'name': item['name'],
                            'quantity': item['quantity'],
                            'purchase_price': item['purchase_price'],
                            'salesperson_commission_amount': item['commission'],
                            'created_at_local': item.get('created_at')
                        }
                    )

                # ==========================
                # ب) المعاملات المالية (Transactions)
                # ==========================

                # 5. الفواتير (Receipts)
                for r in payload.get('receipts', []):
                    receipt_hash = r.get('receipt_hash')
                    if not receipt_hash:
                        continue # تخطي الفواتير بدون هاش لتجنب التكرار الخاطئ

                    receipt_obj, _ = ServerReceipt.objects.update_or_create(
                        receipt_hash=receipt_hash,
                        defaults={
                            'source_machine_id': machine_id,
                            'local_id': r['id'],
                            'receipt_number': r['receipt_number'],
                            'local_branch_id': r['branch_id'],
                            'local_salesperson_id': r.get('salesperson_id'), # الجديد
                            'customer_name': r.get('customer_name', ''),
                            'phone_number': r.get('phone_number', ''),
                            'address': r.get('address', ''),
                            'area': r.get('area', ''),
                            'total_amount': r['total_amount'],
                            'down_payment': r['down_payment'],
                            'installment_system': r.get('installment_system', ''),
                            'sale_year': r['sale_year'],
                            'sale_month': r['sale_month'],
                            'is_cash_sale': r['is_cash_sale'],
                            'products_text': r.get('products_text', ''),
                            'created_at_local': r.get('created_at'),
                            'sync_action': r.get('sync_action', 'NEW'),
                            'is_confirmed': r.get('is_confirmed', True),
                        }
                    )
                    
                    # إعادة بناء العناصر والأقساط
                    receipt_obj.items.all().delete()
                    for item in r.get('items', []):
                        ServerSaleItem.objects.create(
                            receipt=receipt_obj,
                            local_product_id=item['product_id'],
                            product_name_snapshot=item['product_name'],
                            quantity=item['quantity'],
                            unit_price=item['price']
                        )

                    receipt_obj.payments.all().delete()
                    for pay in r.get('payments', []):
                        ServerInstallmentPayment.objects.create(
                            receipt=receipt_obj,
                            payment_date=pay['date'],
                            amount=pay['amount']
                        )
                    
                    processed_count += 1

                # 6. المصروفات
                for exp in payload.get('expenses', []):
                    ServerExpense.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=exp['id'],
                        defaults={
                            'local_branch_id': exp['branch_id'],
                            'amount': exp['amount'],
                            'description': exp['description'],
                            'expense_year': exp['expense_year'],
                            'expense_month': exp['expense_month'],
                            'created_at_local': exp.get('created_at')
                        }
                    )

                # 7. حركات المخزن
                for st in payload.get('stock_transactions', []):
                    ServerStockTransaction.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=st['id'],
                        defaults={
                            'local_product_id': st['product_id'],
                            'product_name_snapshot': st['product_name'],
                            'transaction_type': st['transaction_type'],
                            'quantity': st['quantity'],
                            'created_at_local': st.get('created_at')
                        }
                    )

                # 8. مستخدمي السحابة
                for cu in payload.get('cloud_users', []):
                    ServerCloudUser.objects.update_or_create(
                        source_machine_id=machine_id,
                        local_id=cu['id'],
                        defaults={
                            'username': cu['username'],
                            'password_hash': cu['password_hash'],
                            'role': cu['role'],
                            'is_active': cu['is_active']
                        }
                    )

            return JsonResponse({
                'status': 'success', 
                'message': f'Data synced successfully. Receipts processed: {processed_count}',
                'global_price_updates': [],
                'config_changes': {}
            })

        except Exception as e:
            # لو حصل خطأ، اطبع الخطأ بالتفصيل عشان نعرف نصلحه
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MobilePushIngestView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            machine_id = data.get('machine_id')
            payload = data.get('payload', {})
            
            # 2. التفتيش الأمني 👮‍♂️
            license = ServerLicense.objects.filter(machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized Machine ID'}, status=403)
            
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online sync is disabled for this machine'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online sync license has expired'}, status=403)

            # تحديث وقت آخر ظهور
            license.last_sync_at = timezone.now()
            license.save()
            
            # Save unconfirmed receipts for Master to pull
            synced_receipt_ids = []
            for r in payload.get('receipts', []):
                receipt_hash = r.get('receipt_hash')
                if not receipt_hash: continue
                
                receipt_obj, _ = ServerReceipt.objects.update_or_create(
                    receipt_hash=receipt_hash,
                    defaults={
                        'source_machine_id': machine_id,
                        'local_id': r['local_id'],
                        'receipt_number': r['receipt_number'],
                        'local_branch_id': r['branch_id'],
                        'local_salesperson_id': r.get('salesperson_id'),
                        'customer_name': r.get('customer_name', ''),
                        'phone_number': r.get('phone_number', ''),
                        'address': r.get('address', ''),
                        'area': r.get('area', ''),
                        'total_amount': r['total_amount'],
                        'down_payment': r.get('down_payment', 0),
                        'installment_system': r.get('installment_system', ''),
                        'sale_year': r.get('sale_year', 2026),
                        'sale_month': r.get('sale_month', 1),
                        'is_cash_sale': r.get('is_cash_sale', True),
                        'created_at_local': r.get('created_at'),
                        'sync_action': r.get('sync_action', 'NEW'),
                        'is_confirmed': False, # Critical: Master must pull and confirm
                    }
                )
                
                receipt_obj.items.all().delete()
                for item in r.get('items', []):
                    ServerSaleItem.objects.create(
                        receipt=receipt_obj,
                        local_product_id=item['product_id'],
                        product_name_snapshot=item.get('product_name', 'Cloud Item'),
                        quantity=item['quantity'],
                        unit_price=item['price']
                    )

                receipt_obj.payments.all().delete()
                for pay in r.get('installments', []):
                    ServerInstallmentPayment.objects.create(
                        receipt=receipt_obj,
                        payment_date=pay['payment_date'],
                        amount=pay['amount']
                    )
                    
                synced_receipt_ids.append(r['local_id'])

            # 7. Process Deletions
            for d in payload.get('deleted_items', []):
                if d.get('table_name') == 'Receipt':
                    ServerReceipt.objects.filter(
                        source_machine_id=machine_id, 
                        local_id=d.get('record_id')
                    ).update(sync_action='DELETE', is_confirmed=True)

            # Expenses can be treated similarly if needed, but for now we just log success.
            return JsonResponse({
                'status': 'success', 
                'message': 'Cloud Viewer push data received and staged.',
                'synced_receipt_ids': synced_receipt_ids
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class PendingReceiptsView(View):
    def get(self, request):
        try:
            machine_id = request.GET.get('machine_id')
            role = request.GET.get('role')
            salesperson_id = request.GET.get('salesperson_id')
            
            if not machine_id:
                return JsonResponse({'status': 'error', 'message': 'machine_id required'}, status=400)
            
            license = ServerLicense.objects.filter(machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized Machine ID'}, status=403)
            
            receipts = ServerReceipt.objects.filter(source_machine_id=machine_id, is_confirmed=False)
            if role == 'salesperson' and salesperson_id:
                receipts = receipts.filter(local_salesperson_id=salesperson_id)
            receipts_data = []
            for r in receipts:
                items_data = []
                for item in r.items.all():
                    items_data.append({
                        'product_id': item.local_product_id,
                        'product_name': item.product_name_snapshot,
                        'quantity': item.quantity,
                        'price': str(item.unit_price)
                    })
                
                payments_data = []
                for p in r.payments.all():
                    payments_data.append({
                        'date': p.payment_date.isoformat() if p.payment_date else None,
                        'amount': str(p.amount)
                    })
                
                receipts_data.append({
                    'id': r.local_id,
                    'receipt_hash': r.receipt_hash,
                    'receipt_number': r.receipt_number,
                    'branch_id': r.local_branch_id,
                    'salesperson_id': r.local_salesperson_id,
                    'customer_name': r.customer_name,
                    'phone_number': r.phone_number,
                    'address': r.address,
                    'area': r.area,
                    'total_amount': str(r.total_amount),
                    'down_payment': str(r.down_payment),
                    'installment_system': r.installment_system,
                    'sale_year': r.sale_year,
                    'sale_month': r.sale_month,
                    'is_cash_sale': r.is_cash_sale,
                    'sync_action': r.sync_action,
                    'products_text': r.products_text,
                    'created_at': r.created_at_local.isoformat() if r.created_at_local else None,
                    'items': items_data,
                    'payments': payments_data
                })
            
            return JsonResponse({'status': 'success', 'pending_receipts': receipts_data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ConfirmReceiptsView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            machine_id = data.get('machine_id')
            receipt_hashes = data.get('receipt_hashes', [])
            
            if not machine_id:
                return JsonResponse({'status': 'error', 'message': 'machine_id required'}, status=400)
            
            if not isinstance(receipt_hashes, list):
                return JsonResponse({'status': 'error', 'message': 'receipt_hashes must be a list'}, status=400)
            
            license = ServerLicense.objects.filter(machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized Machine ID'}, status=403)
                
            updated_count = ServerReceipt.objects.filter(
                source_machine_id=machine_id,
                receipt_hash__in=receipt_hashes
            ).update(is_confirmed=True)
            
            return JsonResponse({'status': 'success', 'updated_count': updated_count})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UploadSetupView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            machine_id = data.get('machine_id')
            payload = data.get('payload')
            
            if not machine_id or not payload:
                return JsonResponse({'status': 'error', 'message': 'Missing machine_id or payload'}, status=400)
                
            # Security check
            license = ServerLicense.objects.filter(machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized Machine ID'}, status=403)
            
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online sync is disabled for this machine'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online sync license has expired'}, status=403)

            # Generate token and save payload
            token_str = str(uuid.uuid4())
            MobileProvisionToken.objects.create(token=token_str, payload=payload)
            
            return JsonResponse({'status': 'success', 'token': token_str})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class DownloadSetupView(View):
    def get(self, request):
        try:
            token = request.GET.get('token')
            role = request.GET.get('role')
            salesperson_id = request.GET.get('salesperson_id')
            
            if not token:
                return JsonResponse({'status': 'error', 'message': 'Token parameter is missing'}, status=400)
            
            provision = MobileProvisionToken.objects.filter(token=token).first()
            if not provision:
                return JsonResponse({'status': 'error', 'message': 'Invalid or expired token'}, status=404)
            
            payload = provision.payload
            
            # Immediately delete the token (One-Time Use)
            provision.delete()
            
            if role == 'salesperson' and salesperson_id:
                sp_id = int(salesperson_id)
                if 'salespeople' in payload:
                    payload['salespeople'] = [sp for sp in payload['salespeople'] if sp.get('id') == sp_id]
                
                my_branch_ids = [sp.get('branch_id') for sp in payload.get('salespeople', [])]
                if 'branches' in payload:
                    payload['branches'] = [b for b in payload['branches'] if b.get('id') in my_branch_ids]
            
            return JsonResponse({'status': 'success', 'payload': payload})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ViewerAuthView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_code = data.get('company_code')
            username = data.get('username')
            password_hash = data.get('password_hash')
            
            if not company_code or not username or not password_hash:
                return JsonResponse({'status': 'error', 'message': 'Missing credentials'}, status=400)
                
            full_username = f"{company_code}-{username}"
                
            # 1. Check Company License
            license = ServerLicense.objects.filter(company_code=company_code, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Invalid Company Code'}, status=404)
                
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online subscription is not active for this company'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online subscription has expired'}, status=403)
                
            # 2. Check User Credentials
            user = ServerCloudUser.objects.filter(
                source_machine_id=license.machine_id,
                username=full_username,
                password_hash=password_hash,
                is_active=True
            ).first()
            
            if not user:
                return JsonResponse({'status': 'error', 'message': 'Invalid Username or Password'}, status=401)
                
            # 3. Return Authentication Details and Data for Initial Sync
            # In a production environment, you should return a JWT. 
            # For this hybrid architecture, returning the master_machine_id acts as the binding token.
            return JsonResponse({
                'status': 'success',
                'master_machine_id': license.machine_id,
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'local_id': user.local_id
                }
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ViewerDownloadSyncView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            company_code = payload.get('company_code')
            
            # Find the license and source_machine_id
            license_obj = ServerLicense.objects.filter(company_code=company_code, is_online_active=True).first()
            if not license_obj:
                return JsonResponse({'status': 'error', 'message': 'Invalid company code or inactive online subscription'}, status=403)
                
            machine_id = license_obj.machine_id
            
            # Gather all products, branches, users, settings
            from .models import ServerInventoryItem, ServerBranch, ServerSalesperson
            
            items = ServerInventoryItem.objects.filter(source_machine_id=machine_id)
            products = []
            for item in items:
                month = item.created_at_local.month if item.created_at_local else 1
                year = item.created_at_local.year if item.created_at_local else 2026
                products.append({
                    'name': item.name,
                    'initial_quantity': item.quantity,
                    'initial_purchase_price': int(item.purchase_price),
                    'initial_commission_amount': int(item.salesperson_commission_amount),
                    'initial_month': month,
                    'initial_year': year,
                })
                
            response_payload = {
                'status': 'success',
                'products': products,
                'branches': list(ServerBranch.objects.filter(source_machine_id=machine_id).values(
                    'local_id', 'name'
                )),
                'salespersons': list(ServerSalesperson.objects.filter(source_machine_id=machine_id).values(
                    'local_id', 'name'
                ))
            }
            return JsonResponse(response_payload)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MobileAuthView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_code = data.get('company_code')
            username = data.get('username')
            password = data.get('password')
            
            if not company_code or not username or not password:
                return JsonResponse({'status': 'error', 'message': 'Missing credentials'}, status=400)
                
            full_username = f"{company_code}-{username}"
                
            # 1. Check Company License
            license = ServerLicense.objects.filter(company_code=company_code, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Invalid Company Code'}, status=404)
                
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online subscription is not active for this company'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online subscription has expired'}, status=403)
                
            # 2. Find User or Salesperson
            from .models import ServerCloudUser, ServerSalesperson
            from django.contrib.auth.hashers import check_password
            
            # Query by machine_id + username, then verify password with check_password
            cloud_users = ServerCloudUser.objects.filter(
                source_machine_id=license.machine_id,
                username=full_username
            )
            user = None
            for candidate in cloud_users:
                if check_password(password, candidate.password_hash):
                    user = candidate
                    break
            
            auth_role = None
            auth_salesperson_id = None
            
            if user:
                auth_role = 'manager'
            else:
                salesperson = ServerSalesperson.objects.filter(
                    source_machine_id=license.machine_id,
                    cloud_username=full_username,
                    cloud_password=password
                ).first()
                
                if not salesperson:
                    return JsonResponse({'status': 'error', 'message': 'Invalid Username or Password'}, status=401)
                    
                auth_role = 'salesperson'
                auth_salesperson_id = salesperson.local_id
                
            # 3. Gather Setup Payload
            # Same structure as DownloadSetupView expects to be in the token payload:
            from .models import ServerInventoryItem, ServerBranch, ServerCompanySetting
            
            # Fetch Data
            items = ServerInventoryItem.objects.filter(source_machine_id=license.machine_id)
            branches = ServerBranch.objects.filter(source_machine_id=license.machine_id)
            settings = ServerCompanySetting.objects.filter(source_machine_id=license.machine_id).first()
            
            inventory_data = []
            for item in items:
                inventory_data.append({
                    'id': item.local_id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'purchase_price': float(item.purchase_price),
                    'commission': float(item.salesperson_commission_amount),
                    'branch_id': item.local_branch_id,
                })
                
            if user:
                all_sp = ServerSalesperson.objects.filter(source_machine_id=license.machine_id)
                salespeople_data = [{
                    'id': sp.local_id,
                    'name': sp.name,
                    'branch_id': sp.local_branch_id,
                    'cloud_username': sp.cloud_username
                } for sp in all_sp]
                branches_data = [{
                    'id': b.local_id,
                    'name': b.name
                } for b in branches]
            else:
                salespeople_data = [{
                    'id': salesperson.local_id,
                    'name': salesperson.name,
                    'branch_id': salesperson.local_branch_id,
                    'cloud_username': salesperson.cloud_username
                }]
                branches_data = [{
                    'id': b.local_id,
                    'name': b.name
                } for b in branches if b.local_id == salesperson.local_branch_id]
            
            company_settings_data = {}
            if settings:
                company_settings_data = {
                    'name': settings.name,
                    'description': settings.description,
                    'phone1': settings.phone1,
                    'phone2': settings.phone2,
                    'footer_text': settings.footer_text
                }
            
            setup_payload = {
                'branch_id': branches_data[0]['id'] if branches_data else 1,
                'products': inventory_data,
                'role': auth_role,
                'salesperson_id': auth_salesperson_id,
                'inventory': inventory_data,
                'branches': branches_data,
                'salespeople': salespeople_data,
                'company_settings': company_settings_data
            }
            
            return JsonResponse({
                'status': 'success',
                'role': auth_role,
                'salesperson_id': auth_salesperson_id,
                'master_machine_id': license.machine_id,
                'payload': setup_payload
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PullSyncView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_code = data.get('company_code')
            machine_id = data.get('machine_id')
            last_sync_str = data.get('last_sync')
            role = data.get('role')
            salesperson_id = data.get('salesperson_id')
            
            if not machine_id or not last_sync_str:
                return JsonResponse({'status': 'error', 'message': 'Missing machine_id or last_sync'}, status=400)
                
            from django.utils.dateparse import parse_datetime
            last_sync = parse_datetime(last_sync_str)
            if not last_sync:
                from dateutil.parser import parse
                last_sync = parse(last_sync_str)
                
            from .models import ServerLicense
            
            if company_code:
                license_obj = ServerLicense.objects.filter(company_code=company_code).first()
                if not license_obj:
                    return JsonResponse({'status': 'error', 'message': 'Invalid company code'}, status=404)
            else:
                license_obj = ServerLicense.objects.filter(machine_id=machine_id).first()
                if not license_obj:
                    return JsonResponse({'status': 'error', 'message': 'Invalid master machine ID'}, status=404)
                
            master_machine_id = license_obj.machine_id
            
            from django.db.models import Q
            from .models import (
                ServerInventoryItem, ServerReceipt, ServerExpense, ServerStockTransaction, 
                ServerSaleItem, ServerInstallmentPayment, ServerBranch, ServerSalesperson, 
                ServerSupplier, ServerPurchaseInvoice, ServerCommissionHistory, ServerPurchaseInvoiceItem
            )
            
            products = ServerInventoryItem.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            receipts = ServerReceipt.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).filter(Q(is_confirmed=True) | ~Q(source_machine_id=machine_id))
            
            if role and role.lower() == 'salesperson' and salesperson_id is not None:
                receipts = receipts.filter(local_salesperson_id=salesperson_id)
                
            expenses = ServerExpense.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            stock_txs = ServerStockTransaction.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            receipt_filter = Q(receipt__is_confirmed=True) | ~Q(receipt__source_machine_id=machine_id)
            
            sale_items = ServerSaleItem.objects.filter(
                receipt__source_machine_id=master_machine_id,
                receipt__synced_at__gt=last_sync
            ).filter(receipt_filter)
            
            if role and role.lower() == 'salesperson' and salesperson_id is not None:
                sale_items = sale_items.filter(receipt__local_salesperson_id=salesperson_id)
                
            installments = ServerInstallmentPayment.objects.filter(
                receipt__source_machine_id=master_machine_id,
                receipt__synced_at__gt=last_sync
            ).filter(receipt_filter)
            
            if role and role.lower() == 'salesperson' and salesperson_id is not None:
                installments = installments.filter(receipt__local_salesperson_id=salesperson_id)
                
            branches = ServerBranch.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            users = ServerSalesperson.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            suppliers = ServerSupplier.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            purchase_invoices = ServerPurchaseInvoice.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()
            
            purchase_items = ServerPurchaseInvoiceItem.objects.filter(
                invoice__source_machine_id=master_machine_id,
                invoice__synced_at__gt=last_sync
            ).values()
            
            commissions = ServerCommissionHistory.objects.filter(
                source_machine_id=master_machine_id,
                synced_at__gt=last_sync
            ).values()

            from django.core.serializers.json import DjangoJSONEncoder
            
            response_data = {
                "products": list(products),
                "receipts": list(receipts.values()),
                "expenses": list(expenses),
                "stock_transactions": list(stock_txs),
                "sale_items": list(sale_items.values()),
                "installments": list(installments.values()),
                "branches": list(branches),
                "users": list(users),
                "suppliers": list(suppliers),
                "purchase_invoices": list(purchase_invoices),
                "purchase_items": list(purchase_items),
                "commissions": list(commissions),
            }
            
            return JsonResponse({"status": "success", **response_data}, encoder=DjangoJSONEncoder)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterOnlineLicenseView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            machine_id = data.get('machine_id')
            client_name = data.get('client_name', 'Unknown')
            online_expiry_date_str = data.get('online_expiry_date')
            
            if not machine_id or not online_expiry_date_str:
                return JsonResponse({'status': 'error', 'message': 'Missing machine_id or online_expiry_date'}, status=400)
                
            from datetime import datetime
            expiry_date = datetime.strptime(online_expiry_date_str, '%Y-%m-%d').date()
            
            from .models import ServerLicense
            license, created = ServerLicense.objects.get_or_create(
                machine_id=machine_id,
                defaults={
                    'client_name': client_name,
                    'is_active': True,
                    'is_online_active': True,
                    'online_expiry_date': expiry_date
                }
            )
            if not created:
                license.client_name = client_name
                license.is_active = True
                license.is_online_active = True
                license.online_expiry_date = expiry_date
                license.save()
                
            return JsonResponse({'status': 'success', 'company_code': license.company_code})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class ManagerDashboardView(View):
    def get(self, request):
        try:
            machine_id = request.GET.get('machine_id')
            if not machine_id:
                return JsonResponse({'status': 'error', 'message': 'machine_id required'}, status=400)
                
            from .models import ServerLicense, ServerReceipt, ServerSaleItem, ServerInstallmentPayment, ServerInventoryItem
            license = ServerLicense.objects.filter(machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized Machine ID'}, status=403)
                
            receipts = ServerReceipt.objects.filter(source_machine_id=machine_id, is_confirmed=True)
            
            from django.db.models import Sum
            
            cash_sales = receipts.filter(is_cash_sale=True).aggregate(s=Sum('total_amount'))['s'] or 0
            down_payments = receipts.filter(is_cash_sale=False).aggregate(s=Sum('down_payment'))['s'] or 0
            installments = ServerInstallmentPayment.objects.filter(
                receipt__source_machine_id=machine_id, receipt__is_confirmed=True
            ).aggregate(s=Sum('amount'))['s'] or 0
            
            net_cash = float(cash_sales + down_payments + installments)
            
            sale_items = ServerSaleItem.objects.filter(receipt__source_machine_id=machine_id, receipt__is_confirmed=True)
            inventory_items = {i.local_id: i.purchase_price for i in ServerInventoryItem.objects.filter(source_machine_id=machine_id)}
            
            estimated_profit = 0.0
            product_counts = {}
            for item in sale_items:
                qty = float(item.quantity)
                price = float(item.unit_price)
                cost = float(inventory_items.get(item.local_product_id, 0))
                estimated_profit += (price - cost) * qty
                
                if item.product_name_snapshot not in product_counts:
                    product_counts[item.product_name_snapshot] = 0
                product_counts[item.product_name_snapshot] += int(qty)
                
            top_products = sorted([
                {"product_name": name, "quantity_sold": qty} for name, qty in product_counts.items()
            ], key=lambda x: x['quantity_sold'], reverse=True)[:5]
            
            return JsonResponse({
                'status': 'success',
                'dashboard': {
                    'net_cash': net_cash,
                    'estimated_profit': estimated_profit,
                    'top_products': top_products
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AdminSyncPushView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            company_code = data.get('company_code')
            machine_id = data.get('machine_id')
            payload = data.get('payload', {})
            
            # Security Check
            license = ServerLicense.objects.filter(company_code=company_code, machine_id=machine_id, is_active=True).first()
            if not license:
                return JsonResponse({'status': 'error', 'message': 'Forbidden. Machine ID does not belong to a Manager.'}, status=403)
            
            if not license.is_online_active:
                return JsonResponse({'status': 'error', 'message': 'Online sync is disabled for this machine'}, status=403)
                
            if license.online_expiry_date and license.online_expiry_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Online sync license has expired'}, status=403)

            synced_products = []
            synced_users = []
            synced_suppliers = []
            synced_branches = []
            synced_receipts = []
            synced_expenses = []
            synced_purchases = []
            synced_commissions = []

            with transaction.atomic():
                # ── 1. إعدادات الشركة ─────────────────────────────────────
                settings_data = payload.get('settings', {})
                if settings_data:
                    company_setting, _ = ServerCompanySetting.objects.get_or_create(
                        source_machine_id=machine_id,
                        local_id=1,
                        defaults={'name': settings_data.get('company_name', 'Default Company')}
                    )
                    if 'company_name' in settings_data:
                        company_setting.name = settings_data['company_name']
                    if 'footer_text' in settings_data:
                        company_setting.footer_text = settings_data['footer_text']
                    company_setting.save()

                # ── 2. الفروع ──────────────────────────────────────────────
                for branch in payload.get('branches', []):
                    local_id = branch.get('local_id') or branch.get('id')
                    if not local_id:
                        continue
                    action = branch.get('action', 'CREATE')
                    if action == 'DELETE':
                        ServerBranch.objects.filter(source_machine_id=machine_id, local_id=local_id).delete()
                    else:
                        obj, created = ServerBranch.objects.get_or_create(
                            source_machine_id=machine_id,
                            local_id=local_id,
                            defaults={'name': branch.get('name', '')}
                        )
                        if not created:
                            obj.name = branch.get('name', obj.name)
                            obj.save()
                    synced_branches.append(local_id)

                # ── 3. المنتجات / المخزون ─────────────────────────────────
                for prod in payload.get('products', []):
                    action = prod.get('action', 'CREATE')
                    local_id = prod.get('local_id') or prod.get('id')
                    if not local_id:
                        continue
                    if action == 'DELETE':
                        ServerInventoryItem.objects.filter(source_machine_id=machine_id, local_id=local_id).delete()
                    else:
                        item, created = ServerInventoryItem.objects.get_or_create(
                            source_machine_id=machine_id,
                            local_id=local_id,
                            defaults={
                                'name': prod.get('name', ''),
                                'quantity': prod.get('initial_quantity', 0),
                                'purchase_price': prod.get('initial_purchase_price', 0),
                                'local_branch_id': prod.get('branch_id', 1)
                            }
                        )
                        if not created:
                            if 'name' in prod: item.name = prod['name']
                            if 'initial_quantity' in prod: item.quantity = prod['initial_quantity']
                            if 'initial_purchase_price' in prod: item.purchase_price = prod['initial_purchase_price']
                            item.save()
                    synced_products.append(local_id)

                # ── 4. المندوبين ───────────────────────────────────────────
                for usr in payload.get('users', []):
                    action = usr.get('action', 'CREATE')
                    local_id = usr.get('local_id') or usr.get('id')
                    if not local_id:
                        continue
                    if action == 'DELETE':
                        ServerSalesperson.objects.filter(source_machine_id=machine_id, local_id=local_id).delete()
                    else:
                        sp, created = ServerSalesperson.objects.get_or_create(
                            source_machine_id=machine_id,
                            local_id=local_id,
                            defaults={
                                'name': usr.get('name', ''),
                                'local_branch_id': usr.get('branch_id', 1),
                                'cloud_username': usr.get('cloud_username', ''),
                                'cloud_password': usr.get('cloud_password', '') or usr.get('offline_pin', '')
                            }
                        )
                        if not created:
                            if 'name' in usr: sp.name = usr['name']
                            if 'branch_id' in usr: sp.local_branch_id = usr['branch_id']
                            if 'cloud_password' in usr: sp.cloud_password = usr['cloud_password']
                            sp.save()
                    synced_users.append(local_id)

                # ── 5. الموردين ────────────────────────────────────────────
                for sup in payload.get('suppliers', []):
                    action = sup.get('action', 'CREATE')
                    local_id = sup.get('local_id') or sup.get('id')
                    if not local_id:
                        continue
                    if action == 'DELETE':
                        ServerSupplier.objects.filter(source_machine_id=machine_id, local_id=local_id).delete()
                    else:
                        obj, created = ServerSupplier.objects.get_or_create(
                            source_machine_id=machine_id,
                            local_id=local_id,
                            defaults={
                                'name': sup.get('name', ''),
                                'phone': sup.get('phone', ''),
                                'address': sup.get('address', '')
                            }
                        )
                        if not created:
                            if 'name' in sup: obj.name = sup['name']
                            if 'phone' in sup: obj.phone = sup['phone']
                            if 'address' in sup: obj.address = sup['address']
                            obj.save()
                    synced_suppliers.append(local_id)

                # ── 6. المصروفات ───────────────────────────────────────────
                for exp in payload.get('expenses', []):
                    local_id = exp.get('local_id') or exp.get('id')
                    if not local_id:
                        continue
                    ServerExpense.objects.get_or_create(
                        source_machine_id=machine_id,
                        local_id=local_id,
                        defaults={
                            'amount': exp.get('amount', 0),
                            'description': exp.get('description', ''),
                            'expense_year': exp.get('expense_year', timezone.now().year),
                            'expense_month': exp.get('expense_month', timezone.now().month),
                            'local_branch_id': exp.get('branch_id', 1)
                        }
                    )
                    synced_expenses.append(local_id)

                # ── 7. فواتير المشتريات ────────────────────────────────────
                for inv in payload.get('purchase_invoices', []):
                    local_id = inv.get('local_id') or inv.get('id')
                    if not local_id:
                        continue
                    pi, created = ServerPurchaseInvoice.objects.get_or_create(
                        source_machine_id=machine_id,
                        local_id=local_id,
                        defaults={
                            'invoice_number': inv.get('invoice_number', 0),
                            'invoice_month': inv.get('invoice_month', timezone.now().month),
                            'invoice_year': inv.get('invoice_year', timezone.now().year),
                            'invoice_type': inv.get('invoice_type', 'PURCHASE'),
                            'local_supplier_id': inv.get('supplier_id')
                        }
                    )
                    if created:
                        for item in inv.get('items', []):
                            ServerPurchaseInvoiceItem.objects.create(
                                invoice=pi,
                                local_product_id=item.get('inventory_item_id', 0),
                                product_name_snapshot=item.get('product_name', ''),
                                quantity=item.get('quantity', 0),
                                purchase_price=item.get('purchase_price', 0)
                            )
                        # Update ServerInventoryItem quantity on server side
                        for item in inv.get('items', []):
                            prod_local_id = item.get('inventory_item_id')
                            qty = item.get('quantity', 0)
                            if prod_local_id:
                                server_item = ServerInventoryItem.objects.filter(
                                    source_machine_id=machine_id, local_id=prod_local_id
                                ).first()
                                if server_item:
                                    if inv.get('invoice_type') == 'PURCHASE':
                                        server_item.quantity += qty
                                    else:
                                        server_item.quantity = max(0, server_item.quantity - qty)
                                    server_item.save()
                    synced_purchases.append(local_id)

                # ── 8. الفواتير / الوصلات ──────────────────────────────────
                for rec in payload.get('receipts', []):
                    local_id = rec.get('local_id') or rec.get('id')
                    receipt_hash = rec.get('receipt_hash')
                    if not local_id:
                        continue
                    receipt, created = ServerReceipt.objects.get_or_create(
                        source_machine_id=machine_id,
                        local_id=local_id,
                        defaults={
                            'receipt_hash': receipt_hash,
                            'receipt_number': rec.get('receipt_number', 0),
                            'local_branch_id': rec.get('branch_id', 1),
                            'local_salesperson_id': rec.get('salesperson_id'),
                            'customer_name': rec.get('customer_name', ''),
                            'phone_number': rec.get('phone_number', ''),
                            'address': rec.get('address', ''),
                            'area': rec.get('area', ''),
                            'total_amount': rec.get('total_amount', 0),
                            'down_payment': rec.get('down_payment', 0),
                            'installment_system': rec.get('installment_system', ''),
                            'sale_year': rec.get('sale_year', timezone.now().year),
                            'sale_month': rec.get('sale_month', timezone.now().month),
                            'is_cash_sale': rec.get('is_cash_sale', False),
                            'products_text': rec.get('products_text', ''),
                            'sync_action': rec.get('sync_action', 'NEW'),
                            'is_confirmed': rec.get('is_confirmed', False)
                        }
                    )
                    if created:
                        for item in rec.get('items', []):
                            ServerSaleItem.objects.create(
                                receipt=receipt,
                                local_product_id=item.get('inventory_item_id', 0),
                                product_name_snapshot=item.get('product_name', ''),
                                quantity=item.get('quantity', 1),
                                unit_price=item.get('unit_price', 0)
                            )
                        for pay in rec.get('installment_payments', []):
                            ServerInstallmentPayment.objects.create(
                                receipt=receipt,
                                payment_date=pay.get('payment_date', timezone.now().date()),
                                amount=pay.get('amount', 0)
                            )
                    synced_receipts.append(local_id)

                # ── 9. سجلات العمولات ──────────────────────────────────────
                for comm in payload.get('commission_history', []):
                    local_id = comm.get('local_id') or comm.get('id')
                    if not local_id:
                        continue
                    ServerCommissionHistory.objects.get_or_create(
                        source_machine_id=machine_id,
                        local_id=local_id,
                        defaults={
                            'local_salesperson_id': comm.get('salesperson_id', 0),
                            'amount': comm.get('amount', 0),
                            'reason': comm.get('reason', ''),
                            'commission_date': comm.get('date')
                        }
                    )
                    synced_commissions.append(local_id)

            return JsonResponse({
                'status': 'success',
                'synced_branches': synced_branches,
                'synced_products': synced_products,
                'synced_users': synced_users,
                'synced_suppliers': synced_suppliers,
                'synced_expenses': synced_expenses,
                'synced_purchases': synced_purchases,
                'synced_receipts': synced_receipts,
                'synced_commissions': synced_commissions
            })
            
        except Exception as e:
            import traceback
            return JsonResponse({'status': 'error', 'message': str(e), 'detail': traceback.format_exc()}, status=500)
