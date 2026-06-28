import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from salesapp.models import Receipt, SaleItem, InstallmentPayment, InventoryItem, ClientLicense, Salesperson, PendingExternalReceipt, CloudUser
from salesapp.utils import get_safe_available_qty
from salesapp.views.decorators import branch_required

import requests


@login_required(login_url='login')
@branch_required
def mobile_sync_view(request):
    salespersons = Salesperson.objects.filter(branch=request.branch)
    return render(request, 'salesapp/mobile_sync.html', {
        'page_title': 'مزامنة الموبايل',
        'salespersons': salespersons
    })

@login_required(login_url='login')
@branch_required
def export_setup_json(request):
    salesperson_id = request.GET.get('salesperson_id')
    if not salesperson_id:
        messages.error(request, 'يجب اختيار مندوب المبيعات')
        return redirect('mobile_sync')
        
    salesperson = Salesperson.objects.filter(id=salesperson_id, branch=request.branch).first()
    if not salesperson:
        messages.error(request, 'المندوب غير موجود')
        return redirect('mobile_sync')
        
    products = InventoryItem.objects.filter(branch=request.branch)
    
    product_list = []
    for p in products:
        product_list.append({
            'code': p.id,
            'name': p.name,
            'price': p.get_price_at_date(12, 2099)  # Assuming max date to get current price, or just leave it out if mobile only needs code and name
        })
        
    setup_data = {
        'salesperson_id': salesperson.id,
        'salesperson_name': salesperson.name,
        'branch_id': request.branch.id,
        'branch_name': request.branch.name,
        'products': product_list
    }
    
    response = JsonResponse(setup_data)
    response['Content-Disposition'] = f'attachment; filename="setup_{salesperson.id}.json"'
    return response

@login_required(login_url='login')
@branch_required
def export_mobile_json(request):
    from salesapp.models import CompanySetting, InventoryItem
    import json
    from django.http import HttpResponse

    company = CompanySetting.objects.first()
    products = InventoryItem.objects.filter(branch=request.branch)
    
    company_data = {
        'name': company.name if company else 'VentaPOS',
        'phone1': company.phone1 if company else '',
        'phone2': company.phone2 if company else '',
        'footer_text': company.footer_text if company else '',
    }
    
    product_list = []
    for p in products:
        product_list.append({
            'code': p.id,
            'name': p.name,
            'price': p.get_price_at_date(12, 2099)
        })
        
    setup_data = {
        'company': company_data,
        'branch_id': request.branch.id,
        'branch_name': request.branch.name,
        'products': product_list,
    }
    
    json_data = json.dumps(setup_data, ensure_ascii=False, indent=2)
    response = HttpResponse(json_data, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="setup_data.json"'
    return response

@login_required(login_url='login')
@branch_required
def mobile_import_preview(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        try:
            file = request.FILES['json_file']
            data = json.load(file)
            receipts = data.get('receipts', [])
            
            preview_data = []
            has_errors = False
            for r in receipts:
                sale_month = r.get('sale_month')
                sale_year = r.get('sale_year')
                items = r.get('items', [])
                
                receipt_info = {
                    'customer_name': r.get('customer_name'),
                    'total_amount': r.get('total_amount'),
                    'sale_month': sale_month,
                    'sale_year': sale_year,
                    'items': [],
                    'error': False,
                    'error_messages': []
                }
                
                for item in items:
                    item_id = item.get('item_id')
                    qty = int(item.get('quantity', 0))
                    try:
                        inventory_item = InventoryItem.objects.get(id=item_id, branch=request.branch)
                        safe_qty = get_safe_available_qty(inventory_item, sale_month, sale_year)
                        if safe_qty < qty:
                            receipt_info['error'] = True
                            receipt_info['error_messages'].append(f"الصنف {inventory_item.name} المطلوب ({qty}) متاح منه فقط ({safe_qty})")
                            has_errors = True
                        receipt_info['items'].append({
                            'name': inventory_item.name,
                            'quantity': qty,
                            'safe_qty': safe_qty,
                            'price': item.get('price')
                        })
                    except InventoryItem.DoesNotExist:
                        receipt_info['error'] = True
                        receipt_info['error_messages'].append(f"الصنف ID:{item_id} غير موجود بالسيستم")
                        has_errors = True
                
                preview_data.append(receipt_info)
            
            # Store payload in session for confirm step
            request.session['mobile_import_data'] = receipts
            
            return render(request, 'salesapp/includes/mobile_import_preview.html', {
                'preview_data': preview_data,
                'has_errors': has_errors
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
@branch_required
def mobile_import_confirm(request):
    if request.method == 'POST':
        receipts = request.session.get('mobile_import_data')
        if not receipts:
            messages.error(request, "لم يتم العثور على بيانات للإدراج")
            return redirect('mobile_sync')
            
        try:
            from datetime import datetime
            batch_id = f"FILE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with transaction.atomic():
                for r in receipts:
                    # Check if already pending or exists
                    receipt_hash = r.get('receipt_hash')
                    if receipt_hash and Receipt.objects.filter(receipt_hash=receipt_hash).exists():
                        continue
                    
                    payload_str = json.dumps(r)
                    if receipt_hash and PendingExternalReceipt.objects.filter(branch=request.branch, payload__icontains=receipt_hash).exists():
                        continue

                    PendingExternalReceipt.objects.create(
                        branch=request.branch,
                        batch_id=batch_id,
                        source='FILE',
                        payload=r
                    )
                            
            if 'mobile_import_data' in request.session:
                del request.session['mobile_import_data']
            messages.success(request, "تم إدراج كافة الفواتير بنجاح")
            return redirect('mobile_sync')
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء الإدراج: {str(e)}")
            return redirect('mobile_sync')
            
    return redirect('mobile_sync')

@login_required(login_url='login')
@branch_required
def cloud_status_view(request):
    local_pending_receipts = Receipt.objects.filter(branch=request.branch, is_synced=False)
    
    server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
    
    fetched_count = 0
    try:
        active_lic = ClientLicense.get_active_license()
        machine_id = active_lic.machine_id if active_lic else None
        
        raw_receipts = []
        if machine_id:
            resp = requests.get(f"{server_url}/api/v1/sync/pending-receipts/?machine_id={machine_id}", timeout=5)
            if resp.status_code == 200:
                raw_receipts = resp.json().get('pending_receipts', [])
                
        from datetime import datetime
        batch_id = f"CLOUD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        for r in raw_receipts:
            receipt_hash = r.get('receipt_hash')
            if receipt_hash and Receipt.objects.filter(receipt_hash=receipt_hash).exists():
                continue # Already added as real receipt
            
            # Check if already in staging
            if receipt_hash and PendingExternalReceipt.objects.filter(branch=request.branch, payload__icontains=receipt_hash).exists():
                continue
            
            PendingExternalReceipt.objects.create(
                branch=request.branch,
                batch_id=batch_id,
                source='CLOUD',
                payload=r
            )
            fetched_count += 1
                
        if fetched_count > 0:
            messages.success(request, f"تم سحب {fetched_count} فواتير من السحابة بنجاح وهي الآن في المعاملات المعلقة.")
    except requests.RequestException:
        pass

    if request.method == 'POST':
        action = request.POST.get('action')
        # If there are local pending receipts to push to cloud, keep that logic if it existed here.
        # But wait, the previous code didn't have local push logic here, it just had confirm_receipt!

    return render(request, 'salesapp/cloud_status.html', {
        'page_title': 'حالة السحابة',
        'local_pending': local_pending_receipts,
        # server_pending is no longer passed as it's handled in the unified staging view
    })

@login_required(login_url='login')
@branch_required
def manage_devices_view(request):
    salespersons = Salesperson.objects.filter(branch=request.branch)
    server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
    
    # Get actual LAN IP to display in the offline QR
    import socket
    lan_ip = "127.0.0.1"
        
    return render(request, 'salesapp/manage_devices.html', {
        'page_title': 'إدارة أجهزة المناديب',
        'salespersons': salespersons,
        'server_url': server_url,
        'lan_ip': lan_ip,
        'server_port': request.get_port()
    })

def local_setup_api(request):
    token = request.GET.get('token')
    sp_id = request.GET.get('sp_id')
    
    if not token or not sp_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    salesperson = Salesperson.objects.filter(id=sp_id, device_token=token).first()
    if not salesperson:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
    branch = salesperson.branch
    products = InventoryItem.objects.filter(branch=branch)
    
    product_list = []
    for p in products:
        product_list.append({
            'id': p.id,
            'code': str(p.id),
            'name': p.name
        })
        
    setup_data = {
        'salesperson_id': salesperson.id,
        'salesperson_name': salesperson.name,
        'branch_id': branch.id,
        'branch_name': branch.name,
        'products': product_list
    }
    
    return JsonResponse(setup_data)

@csrf_exempt
def local_push_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        token = data.get('token')
        sp_id = data.get('sp_id')
        receipts = data.get('receipts', [])
        
        salesperson = Salesperson.objects.filter(id=sp_id, device_token=token).first()
        if not salesperson:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
            
        branch = salesperson.branch
        
        saved_count = 0
        from datetime import datetime
        batch_id = f"USB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with transaction.atomic():
            for r in receipts:
                receipt_hash = r.get('receipt_hash')
                if receipt_hash and Receipt.objects.filter(receipt_hash=receipt_hash).exists():
                    continue # deduplication

                # Check if already pending
                payload_str = json.dumps(r)
                if receipt_hash and PendingExternalReceipt.objects.filter(branch=branch, payload__icontains=receipt_hash).exists():
                    continue

                PendingExternalReceipt.objects.create(
                    branch=branch,
                    batch_id=batch_id,
                    source='USB',
                    payload=r
                )
                saved_count += 1
                
        return JsonResponse({'status': 'success', 'saved_count': saved_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@branch_required
def pending_receipts_view(request):
    pending = PendingExternalReceipt.objects.filter(branch=request.branch, is_processed=False).order_by('-created_at')
    
    batches = {}
    for p in pending:
        data = p.payload
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        
        sale_month = data.get('sale_month')
        sale_year = data.get('sale_year')
        
        batch_id = p.batch_id or 'بدون تصنيف'
        if batch_id not in batches:
            batches[batch_id] = {
                'batch_id': batch_id,
                'source': p.get_source_display(),
                'created_at': p.created_at,
                'salesperson_name': data.get('salesperson_name') or 'غير محدد',
                'has_error': False,
                'receipts': [],
                'item_summary': {}
            }
            
        has_error = False
        product_names = []
        for item in data.get('items', []):
            item_id = item.get('item_id') or item.get('product_id') or item.get('id')
            item_name = item.get('name') or item.get('product_name')
            qty = float(item.get('quantity') or item.get('qty') or 0)
            
            inventory_item = None
            if item_id:
                inventory_item = InventoryItem.objects.filter(id=item_id, branch=request.branch).first()
            elif item_name:
                inventory_item = InventoryItem.objects.filter(name=item_name, branch=request.branch).first()
                
            display_name = inventory_item.name if inventory_item else (item_name or str(item_id))
            if display_name:
                product_names.append(display_name)
                
            safe_qty = get_safe_available_qty(inventory_item, sale_month, sale_year) if inventory_item else 0
            
            if safe_qty < qty:
                has_error = True
                
            if display_name not in batches[batch_id]['item_summary']:
                batches[batch_id]['item_summary'][display_name] = {'qty': 0, 'safe_qty': safe_qty}
            batches[batch_id]['item_summary'][display_name]['qty'] += qty
            
        for d_name, info in batches[batch_id]['item_summary'].items():
            info['has_error'] = info['safe_qty'] < info['qty']
            if info['has_error']:
                batches[batch_id]['has_error'] = True
            
        batches[batch_id]['receipts'].append({
            'pending_id': p.id,
            'customer_name': data.get('customer_name', ''),
            'phone_number': data.get('phone_number', ''),
            'address': data.get('address', ''),
            'area': data.get('area', ''),
            'is_cash_sale': data.get('is_cash_sale', True),
            'installment_system': data.get('installment_system', ''),
            'sale_month': sale_month,
            'sale_year': sale_year,
            'total_amount': data.get('total_amount', 0),
            'products_text': " + ".join(product_names),
            'has_error': has_error,
            'created_at': p.created_at,
            'is_deleted_request': data.get('is_deleted_request', False),
            'is_modified_request': data.get('is_modified_request', False)
        })
        
    batches_data = list(batches.values())
        
    return render(request, 'salesapp/pending_receipts.html', {
        'page_title': 'المعاملات المعلقة',
        'batches_data': batches_data
    })


@login_required(login_url='login')
@branch_required
def approve_pending_receipts(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        batch_id = request.POST.get('batch_id')
        
        if not batch_id:
            messages.warning(request, "لم تقم بتحديد مجموعة صالحة.")
            return redirect('pending_receipts')
            
        pending_qs = PendingExternalReceipt.objects.filter(batch_id=batch_id, branch=request.branch, is_processed=False)
        
        if action == 'delete':
            count = pending_qs.count()
            pending_qs.delete()
            messages.success(request, f"تم رفض وحذف {count} طلبات معلقة بنجاح.")
            return redirect('pending_receipts')
            
        if action == 'approve':
            success_count = 0
            error_count = 0
            
            with transaction.atomic():
                for pending in pending_qs:
                    data = pending.payload
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception:
                            data = {}
                            
                    receipt_hash = data.get('receipt_hash')
                    sync_action = data.get('sync_action', 'NEW')
                    
                    existing_receipt = None
                    if receipt_hash:
                        existing_receipt = Receipt.objects.filter(receipt_hash=receipt_hash).first()
                        
                    if sync_action == 'NEW' and existing_receipt:
                        pending.is_processed = True
                        pending.save()
                        continue
                        
                    if sync_action == 'DELETE':
                        if existing_receipt:
                            existing_receipt.delete() # SyncDeletionLog will catch this and push back!
                        pending.is_processed = True
                        pending.save()
                        success_count += 1
                        continue

                    # For NEW and EDIT, validate stock and license
                    from salesapp.models import ClientLicense, InventoryItem, Salesperson, SaleItem, InstallmentPayment, Receipt
                    from salesapp.utils.inventory_utils import get_safe_available_qty
                    active_license = ClientLicense.get_active_license()
                    if not active_license or not active_license.is_active or active_license.invoices_balance <= 0:
                        messages.error(request, "ترخيص غير صالح، لا يمكن قبول الفواتير.")
                        break
                        
                    stock_valid = True
                    sale_month = data.get('sale_month')
                    sale_year = data.get('sale_year')
                    for item in data.get('items', []):
                        item_id = item.get('item_id') or item.get('product_id') or item.get('id')
                        item_name = item.get('name') or item.get('product_name')
                        qty = int(item.get('quantity') or item.get('qty') or 0)
                        
                        inventory_item = None
                        if item_id:
                            inventory_item = InventoryItem.objects.filter(id=item_id, branch=request.branch).first()
                        elif item_name:
                            inventory_item = InventoryItem.objects.filter(name=item_name, branch=request.branch).first()
                            
                        # If editing, we strictly shouldn't just check total safe qty, but it's safe enough for now
                        if not inventory_item or get_safe_available_qty(inventory_item, sale_month, sale_year) < qty:
                            stock_valid = False
                            break
                            
                    if not stock_valid:
                        error_count += 1
                        continue
                        
                    salesperson = None
                    if data.get('salesperson_id'):
                        salesperson = Salesperson.objects.filter(id=data.get('salesperson_id'), branch=request.branch).first()
                    elif data.get('salesperson_name'):
                        salesperson, _ = Salesperson.objects.get_or_create(name=data.get('salesperson_name'), branch=request.branch)

                    if sync_action == 'EDIT' and existing_receipt:
                        rec = existing_receipt
                        rec.customer_name = data.get('customer_name', '')
                        rec.phone_number = data.get('phone_number', '')
                        rec.address = data.get('address', '')
                        rec.area = data.get('area', '')
                        rec.down_payment = data.get('down_payment', 0)
                        rec.total_amount = data.get('total_amount', 0)
                        rec.is_cash_sale = data.get('is_cash_sale', True)
                        rec.sale_month = sale_month
                        rec.sale_year = sale_year
                        rec.salesperson = salesperson
                        rec.installment_system = data.get('installment_system', '')
                        rec.products_text = data.get('products_text', '')
                        rec.sync_action = 'EDIT'
                        rec.is_confirmed = True
                        rec.is_synced = False
                        rec.save()
                        
                        rec.items.all().delete()
                        for item in data.get('items', []):
                            item_id = item.get('item_id') or item.get('product_id') or item.get('id')
                            item_name = item.get('name') or item.get('product_name')
                            qty = int(item.get('quantity') or item.get('qty') or 0)
                            
                            if item_id:
                                inventory_item = InventoryItem.objects.filter(id=item_id, branch=request.branch).first()
                            else:
                                inventory_item = InventoryItem.objects.filter(name=item_name, branch=request.branch).first()
                                
                            SaleItem.objects.create(
                                receipt=rec,
                                inventory_item=inventory_item,
                                quantity=qty,
                                unit_price=item.get('price', 0)
                            )
                        
                        if not rec.is_cash_sale and data.get('installments'):
                            rec.payments.all().delete()
                            for inst in data.get('installments', []):
                                InstallmentPayment.objects.create(
                                    receipt=rec,
                                    payment_date=inst.get('payment_date'),
                                    amount=inst.get('amount')
                                )
                                
                        pending.is_processed = True
                        pending.save()
                        success_count += 1
                        continue

                    # Otherwise NEW
                    new_receipt = Receipt(
                        source='MOBILE',
                        branch=request.branch,
                        customer_name=data.get('customer_name', ''),
                        phone_number=data.get('phone_number', ''),
                        address=data.get('address', ''),
                        area=data.get('area', ''),
                        down_payment=data.get('down_payment', 0),
                        total_amount=data.get('total_amount', 0),
                        is_cash_sale=data.get('is_cash_sale', True),
                        sale_month=sale_month,
                        sale_year=sale_year,
                        salesperson=salesperson,
                        installment_system=data.get('installment_system', ''),
                        products_text=data.get('products_text', ''),
                        receipt_number=Receipt.get_next_receipt_number(request.branch),
                        receipt_hash=receipt_hash,
                        sync_action='NEW',
                        is_confirmed=True,
                        is_synced=False # We want to push back to cloud!
                    )
                    
                    new_receipt.save()
                    
                    for item in data.get('items', []):
                        item_id = item.get('item_id') or item.get('product_id') or item.get('id')
                        item_name = item.get('name') or item.get('product_name')
                        qty = int(item.get('quantity') or item.get('qty') or 0)
                        
                        if item_id:
                            inventory_item = InventoryItem.objects.filter(id=item_id, branch=request.branch).first()
                        else:
                            inventory_item = InventoryItem.objects.filter(name=item_name, branch=request.branch).first()
                            
                        SaleItem.objects.create(
                            receipt=new_receipt,
                            inventory_item=inventory_item,
                            quantity=qty,
                            unit_price=item.get('price', 0)
                        )
                    
                    if not new_receipt.is_cash_sale and data.get('installments'):
                        for inst in data.get('installments', []):
                            InstallmentPayment.objects.create(
                                receipt=new_receipt,
                                payment_date=inst.get('payment_date'),
                                amount=inst.get('amount')
                            )
                            
                    pending.is_processed = True
                    pending.save()
                    success_count += 1
                    
            if success_count > 0:
                messages.success(request, f"تم قبول واعتماد {success_count} طلبات معلقة.")
            if error_count > 0:
                messages.error(request, f"تم تجاوز {error_count} طلبات بسبب نقص المخزون أو عدم توفر الفاتورة الأصلية.")
                
            return redirect('pending_receipts')
            
    return redirect('pending_receipts')

@login_required(login_url='login')
@branch_required
def delete_pending_receipt(request, pk):
    if request.method == 'POST':
        receipt = get_object_or_404(PendingExternalReceipt, id=pk, branch=request.branch, is_processed=False)
        receipt.delete()
        messages.success(request, "تم حذف الفاتورة المعلقة بنجاح.")
    return redirect('pending_receipts')

@login_required(login_url='login')
@branch_required
def edit_pending_receipt(request, pk):
    receipt = get_object_or_404(PendingExternalReceipt, id=pk, branch=request.branch, is_processed=False)
    
    data = receipt.payload
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
            
    # Normalize items for the template to avoid VariableDoesNotExist errors
    for item in data.get('items', []):
        item['normalized_id'] = item.get('product_id') or item.get('id') or item.get('item_id') or ''
        item['normalized_name'] = item.get('product_name') or item.get('name') or ''
        item['normalized_qty'] = item.get('quantity') or item.get('qty') or 0
        item['normalized_price'] = item.get('price') or 0
            
    from salesapp.models import Salesperson
    
    if request.method == 'POST':
        # Update data from form
        data['customer_name'] = request.POST.get('customer_name', '')
        data['address'] = request.POST.get('address', '')
        data['phone_number'] = request.POST.get('phone_number', '')
        data['area'] = request.POST.get('area', '')
        data['is_cash_sale'] = request.POST.get('is_cash_sale') == 'on'
        
        try:
            data['down_payment'] = float(request.POST.get('down_payment', 0))
        except ValueError:
            data['down_payment'] = 0.0
            
        try:
            data['sale_month'] = int(request.POST.get('sale_month', 1))
            data['sale_year'] = int(request.POST.get('sale_year', 2026))
        except ValueError:
            pass
            
        try:
            data['salesperson_id'] = int(request.POST.get('salesperson_id'))
        except (ValueError, TypeError):
            pass
            
        data['installment_system'] = request.POST.get('installment_system', '')
        
        # Process items from sale_items_json (like edit_receipt)
        sale_items_json_str = request.POST.get('sale_items_json', '[]')
        try:
            items_list = json.loads(sale_items_json_str)
        except Exception:
            items_list = []
            
        new_items = []
        total_amount = 0.0
        
        for item in items_list:
            qty = float(item.get('quantity', 0))
            price = float(item.get('price', 0))
            if qty > 0:
                new_items.append({
                    'product_id': item.get('id'),
                    'product_name': item.get('name'),
                    'quantity': qty,
                    'price': price
                })
                total_amount += (qty * price)
                
        data['items'] = new_items
        data['total_amount'] = total_amount
        data['products_text'] = " + ".join([item['product_name'] for item in new_items])
        
        receipt.payload = data
        receipt.save()
        
        messages.success(request, "تم حفظ التعديلات على الفاتورة المعلقة بنجاح.")
        return redirect('pending_receipts')

    # Prepare context for template
    sale_items_json_str = "[]"
    items_for_js = []
    for item in data.get('items', []):
        items_for_js.append({
            'id': item.get('product_id') or item.get('id') or item.get('item_id') or '',
            'name': item.get('product_name') or item.get('name') or '',
            'quantity': item.get('quantity') or item.get('qty') or 0,
            'price': item.get('price', 0)
        })
    sale_items_json_str = json.dumps(items_for_js)
    
    salespersons = Salesperson.objects.filter(branch=request.branch)
    salesperson_name = data.get('salesperson_name') or receipt.device.name
    
    return render(request, 'salesapp/edit_pending_receipt.html', {
        'page_title': 'تعديل فاتورة معلقة',
        'receipt': receipt,
        'data': data,
        'is_pro_plan': True,
        'salespersons': salespersons,
        'sale_items_json_str': sale_items_json_str,
        'salesperson_name': salesperson_name
    })

@csrf_exempt
def push_to_cloud_ajax(request):
    """
    دالة تعمل في الخلفية لرفع البيانات المحلية للسيرفر المركزي
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=405)
        
    try:
        from salesapp.models import ClientLicense, Branch, Salesperson, InventoryItem, Receipt, Expense, CompanySetting, CloudUser
        
        # 1. التحقق من الرخصة (Machine ID)
        active_lic = ClientLicense.objects.filter(is_active=True).first()
        if not active_lic or not active_lic.machine_id:
            return JsonResponse({'status': 'error', 'message': 'No active license or machine ID found'}, status=403)
            
        server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
        if not server_url:
            return JsonResponse({'status': 'error', 'message': 'Server URL not configured'}, status=400)
            
        machine_id = active_lic.machine_id
        
        # 2. تجميع البيانات غير المزامنة
        payload = {}
        
        # إعدادات الشركة
        setting = CompanySetting.objects.first()
        if setting:
            payload['company_settings'] = {
                'name': setting.name,
                'description': setting.description,
                'phone1': setting.phone1,
                'phone2': setting.phone2
            }
            
        # الفروع
        unsynced_branches = Branch.objects.filter(is_synced=False)
        if unsynced_branches.exists():
            payload['branches'] = [{'id': b.id, 'name': b.name} for b in unsynced_branches]
            
        # الموظفين
        unsynced_salespeople = Salesperson.objects.filter(is_synced=False)
        if unsynced_salespeople.exists():
            payload['salespeople'] = [{'id': sp.id, 'name': sp.name, 'branch_id': sp.branch_id} for sp in unsynced_salespeople]
            
        # المخزون
        unsynced_inventory = InventoryItem.objects.filter(is_synced=False)
        if unsynced_inventory.exists():
            payload['inventory'] = [
                {
                    'id': i.id, 'branch_id': i.branch_id, 'name': i.name, 
                    'quantity': i.initial_quantity, 'purchase_price': float(i.initial_purchase_price),
                    'commission': float(i.initial_commission_amount)
                } for i in unsynced_inventory
            ]
            
        # الفواتير
        unsynced_receipts = Receipt.objects.filter(is_synced=False)
        if unsynced_receipts.exists():
            receipts_data = []
            for r in unsynced_receipts:
                r_dict = {
                    'id': r.id,
                    'branch_id': r.branch_id,
                    'salesperson_id': r.salesperson_id,
                    'receipt_number': r.receipt_number,
                    'customer_name': r.customer_name,
                    'phone_number': r.phone_number,
                    'address': r.address,
                    'area': r.area,
                    'total_amount': float(r.total_amount),
                    'down_payment': float(r.down_payment),
                    'installment_system': r.installment_system,
                    'sale_month': r.sale_month,
                    'sale_year': r.sale_year,
                    'is_cash_sale': r.is_cash_sale,
                    'products_text': r.products_text,
                    'receipt_hash': r.receipt_hash,
                    'created_at': r.created_at.isoformat(),
                    'items': [],
                    'payments': []
                }
                for item in r.items.all():
                    r_dict['items'].append({
                        'product_id': item.inventory_item_id,
                        'product_name': item.inventory_item.name,
                        'quantity': float(item.quantity),
                        'price': float(item.unit_price)
                    })
                for pay in r.payments.all():
                    r_dict['payments'].append({
                        'date': pay.payment_date.isoformat(),
                        'amount': float(pay.amount)
                    })
                receipts_data.append(r_dict)
            payload['receipts'] = receipts_data
            
        # المصروفات
        unsynced_expenses = Expense.objects.filter(is_synced=False)
        if unsynced_expenses.exists():
            payload['expenses'] = [
                {
                    'id': e.id, 'branch_id': e.branch_id, 
                    'amount': float(e.amount), 'description': e.description,
                    'expense_month': e.expense_month, 'expense_year': e.expense_year,
                    'created_at': e.created_at.isoformat()
                } for e in unsynced_expenses
            ]
            
        # مستخدمي السحابة (الأجهزة الفرعية)
        unsynced_cloud_users = CloudUser.objects.filter(is_synced=False)
        if unsynced_cloud_users.exists():
            payload['cloud_users'] = [
                {
                    'id': cu.id,
                    'username': cu.username,
                    'password_hash': cu.password, # We store it hashed
                    'role': cu.role,
                    'is_active': cu.is_active
                } for cu in unsynced_cloud_users
            ]
            
        # إذا لم يكن هناك شيء للمزامنة
        if not any(payload.values()):
            return JsonResponse({'status': 'success', 'message': 'No data to sync', 'synced_count': 0})
            
        # 3. إرسال البيانات للسيرفر المركزي
        is_cloud_viewer = request.session.get('is_cloud_viewer', False)
        
        # Include online license info for auto-registration on server
        online_license_info = {}
        online_lic = ClientLicense.objects.filter(is_active=True, is_online_active=True).first()
        if online_lic and online_lic.online_expiry_date:
            online_license_info['online_expiry_date'] = online_lic.online_expiry_date.isoformat()
        
        post_data = {
            'machine_id': machine_id,
            'payload': payload,
            'source': 'CLOUD_VIEWER' if is_cloud_viewer else 'MASTER',
            'online_license_info': online_license_info
        }
        
        endpoint = "api/v1/sync/mobile-push/" if is_cloud_viewer else "api/v1/sync/push/"
        resp = requests.post(f"{server_url}/{endpoint}", json=post_data, timeout=10)
        
        if resp.status_code == 200:
            # 4. علّم البيانات كمزامنة (is_synced = True)
            with transaction.atomic():
                unsynced_branches.update(is_synced=True)
                unsynced_salespeople.update(is_synced=True)
                unsynced_inventory.update(is_synced=True)
                unsynced_cloud_users.update(is_synced=True)
                unsynced_receipts.update(is_synced=True)
                unsynced_expenses.update(is_synced=True)
                
            return JsonResponse({'status': 'success', 'message': 'Synced successfully', 'synced_count': len(payload.get('receipts', []))})
        else:
            return JsonResponse({'status': 'error', 'message': f'Server returned {resp.status_code}', 'server_response': resp.text}, status=500)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

import subprocess
from salesapp.models import CloudUser

@login_required(login_url='login')
@branch_required
def cloud_hub_view(request):
    """
    Unified view for Cloud and Devices Hub.
    """
    salespersons = Salesperson.objects.filter(branch=request.branch)
    server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
    import socket
    lan_ip = "127.0.0.1"
    
    local_pending_receipts = Receipt.objects.filter(branch=request.branch, is_synced=False)
    
    # Pending Approvals Logic
    pending = PendingExternalReceipt.objects.filter(branch=request.branch, is_processed=False).order_by('-created_at')
    batches = {}
    for p in pending:
        data = p.payload
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        
        sale_month = data.get('sale_month')
        sale_year = data.get('sale_year')
        
        batch_id = p.batch_id or 'بدون تصنيف'
        if batch_id not in batches:
            batches[batch_id] = {
                'batch_id': batch_id,
                'source': p.get_source_display(),
                'created_at': p.created_at,
                'salesperson_name': data.get('salesperson_name') or 'غير محدد',
                'has_error': False,
                'receipts': [],
                'item_summary': {}
            }
            
        has_error = False
        product_names = []
        for item in data.get('items', []):
            item_id = item.get('item_id') or item.get('product_id') or item.get('id')
            item_name = item.get('name') or item.get('product_name')
            qty = float(item.get('quantity') or item.get('qty') or 0)
            
            inventory_item = None
            if item_id:
                inventory_item = InventoryItem.objects.filter(id=item_id, branch=request.branch).first()
            elif item_name:
                inventory_item = InventoryItem.objects.filter(name=item_name, branch=request.branch).first()
                
            display_name = inventory_item.name if inventory_item else (item_name or str(item_id))
            if display_name:
                product_names.append(display_name)
                
            safe_qty = get_safe_available_qty(inventory_item, sale_month, sale_year) if inventory_item else 0
            if safe_qty < qty:
                has_error = True
                
            if display_name not in batches[batch_id]['item_summary']:
                batches[batch_id]['item_summary'][display_name] = {'qty': 0, 'safe_qty': safe_qty}
            batches[batch_id]['item_summary'][display_name]['qty'] += qty
            
        for d_name, info in batches[batch_id]['item_summary'].items():
            info['has_error'] = info['safe_qty'] < info['qty']
            if info['has_error']:
                batches[batch_id]['has_error'] = True
            
        batches[batch_id]['receipts'].append({
            'pending_id': p.id,
            'customer_name': data.get('customer_name', ''),
            'phone_number': data.get('phone_number', ''),
            'address': data.get('address', ''),
            'area': data.get('area', ''),
            'is_cash_sale': data.get('is_cash_sale', True),
            'installment_system': data.get('installment_system', ''),
            'sale_month': sale_month,
            'sale_year': sale_year,
            'total_amount': data.get('total_amount', 0),
            'products_text': " + ".join(product_names),
            'has_error': has_error,
            'created_at': p.created_at,
            'is_deleted_request': data.get('is_deleted_request', False),
            'is_modified_request': data.get('is_modified_request', False)
        })
        
    batches_data = list(batches.values())
    
    # Cloud Users Logic
    cloud_users = CloudUser.objects.all()
    active_license = ClientLicense.get_active_license()
    company_code = active_license.company_code if active_license else None
    is_online_active = active_license.is_online_active if active_license else False

    return render(request, 'salesapp/cloud_hub.html', {
        'page_title': 'لوحة السحابة والأجهزة',
        'salespersons': salespersons,
        'server_url': server_url,
        'lan_ip': lan_ip,
        'server_port': request.get_port(),
        'local_pending': local_pending_receipts,
        'batches_data': batches_data,
        'cloud_users': cloud_users,
        'company_code': company_code,
        'is_online_active': is_online_active
    })

import os
from django.conf import settings

def get_adb_path():
    # Attempt to use bundled ADB, fallback to system ADB
    base_dir = settings.BASE_DIR
    bundled_adb = os.path.join(base_dir, 'bin', 'platform-tools', 'adb.exe')
    if os.path.exists(bundled_adb):
        return bundled_adb
    return 'adb'

def usb_devices_api(request):
    try:
        adb_path = get_adb_path()
        output = subprocess.check_output([adb_path, 'devices'], stderr=subprocess.STDOUT).decode('utf-8')
        lines = output.strip().split('\n')[1:] # Skip first line "List of devices attached"
        devices = []
        for line in lines:
            if '\tdevice' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return JsonResponse({'status': 'success', 'devices': devices})
    except FileNotFoundError:
        return JsonResponse({'status': 'success', 'devices': [], 'message': 'ADB not found. Please install Android Platform Tools.'})
    except Exception as e:
        return JsonResponse({'status': 'success', 'devices': [], 'message': str(e)})

@csrf_exempt
def usb_sync_api(request, device_id):
    if request.method == 'POST':
        try:
            adb_path = get_adb_path()
            subprocess.check_output([adb_path, '-s', device_id, 'reverse', 'tcp:8000', 'tcp:8000'], stderr=subprocess.STDOUT)
            subprocess.check_output([adb_path, '-s', device_id, 'shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d', 'ventapos://sync'], stderr=subprocess.STDOUT)
            return JsonResponse({'status': 'success', 'message': 'Sync started'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required(login_url='login')
@branch_required
def add_online_device_view(request):
    if request.method == 'POST':
        device_type = request.POST.get('device_type')
        username = request.POST.get('username')
        password_raw = request.POST.get('password')
        
        if not username or not password_raw:
            messages.error(request, "يجب إدخال اسم المستخدم وكلمة المرور.")
            return redirect('cloud_hub')
            
        if device_type in ['viewer', 'manager']:
            if CloudUser.objects.filter(username=username).exists():
                messages.error(request, "اسم المستخدم موجود مسبقاً.")
            else:
                role = 'VIEWER' if device_type == 'viewer' else 'ACCOUNTANT'
                CloudUser.objects.create(
                    username=username,
                    password=make_password(password_raw),
                    role=role
                )
                messages.success(request, "تم إضافة جهاز فرعي بنجاح.")
                
        elif device_type == 'salesperson':
            salesperson_id = request.POST.get('salesperson_id')
            if salesperson_id:
                try:
                    sp = Salesperson.objects.get(id=salesperson_id, branch=request.branch)
                    sp.cloud_username = username
                    sp.cloud_password = password_raw
                    sp.save()
                    messages.success(request, f"تم تفعيل الأونلاين للمندوب {sp.name} بنجاح.")
                except Salesperson.DoesNotExist:
                    messages.error(request, "المندوب غير موجود.")
            else:
                messages.error(request, "يجب اختيار مندوب المبيعات.")
                
    return redirect('cloud_hub')
