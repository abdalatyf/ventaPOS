from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from salesapp.models import CompanySetting, Branch, Salesperson, InventoryItem, ClientLicense, Receipt, SaleItem, InstallmentPayment, Expense
import requests
import json

@login_required(login_url='login')
def cloud_initial_sync(request):
    if not request.session.get('is_cloud_viewer'):
        return redirect('dashboard')
        
    company_code = request.GET.get('company_code')
    if not company_code:
        # Fallback to fetching from user input if not passed
        pass

    if request.method == 'POST':
        company_code = request.POST.get('company_code')
        server_url = getattr(settings, 'SERVER_URL', 'http://127.0.0.1:8000')
        
        try:
            machine_id = request.session.get('cloud_master_machine_id', 'init')
            resp = requests.post(f"{server_url}/api/v1/sync/pull/", json={
                'company_code': company_code,
                'last_sync': '1970-01-01T00:00:00Z',
                'machine_id': machine_id
            }, timeout=30)
            
            data = resp.json()
            if resp.status_code == 200 and data.get('status') == 'success':
                payload = data.get('payload', data)
                # Clear existing basic data
                SaleItem.objects.all().delete()
                InstallmentPayment.objects.all().delete()
                Receipt.objects.all().delete()
                Expense.objects.all().delete()
                try:
                    from salesapp.models import InventoryAdjustment, PurchaseInvoiceItem, PurchaseInvoice, CommissionHistory
                    InventoryAdjustment.objects.all().delete()
                    PurchaseInvoiceItem.objects.all().delete()
                    PurchaseInvoice.objects.all().delete()
                    CommissionHistory.objects.all().delete()
                except Exception:
                    pass
                InventoryItem.objects.all().delete()
                Salesperson.objects.all().delete()
                Branch.objects.all().delete()
                
                # Insert basic company setting so login passes next time
                if not CompanySetting.objects.exists():
                    CompanySetting.objects.create(
                        name=f"فرع من: {company_code}",
                        phone1="00000000000",
                        description="متصل سحابيا",
                        is_cloud_viewer=True
                    )
                else:
                    cs = CompanySetting.objects.first()
                    cs.is_cloud_viewer = True
                    cs.save()
                
                for b in payload.get('branches', []):
                    Branch.objects.create(id=b.get('local_id', b.get('id')), name=b['name'], is_synced=True)
                    
                for s in payload.get('salespeople', []):
                    Salesperson.objects.create(
                        id=s.get('local_id', s.get('id')),
                        name=s['name'], 
                        branch_id=s['branch_id'],
                        cloud_username=s.get('cloud_username'),
                        cloud_password=s.get('cloud_password'),
                        is_synced=True
                    )
                    
                for p in payload.get('inventory', []):
                    InventoryItem.objects.create(
                        id=p.get('local_id', p.get('id')),
                        name=p['name'],
                        branch_id=p['branch_id'],
                        initial_quantity=p.get('quantity', 0),
                        initial_purchase_price=p.get('purchase_price', 0),
                        initial_commission_amount=p.get('commission', 0),
                        initial_month=p.get('initial_month', 1),
                        initial_year=p.get('initial_year', 2026),
                        is_synced=True
                    )

                for e in payload.get('expenses', []):
                    Expense.objects.create(
                        id=e.get('local_id', e.get('id')),
                        branch_id=e['branch_id'],
                        amount=e['amount'],
                        description=e['description'],
                        expense_year=e['expense_year'],
                        expense_month=e['expense_month'],
                        is_synced=True
                    )
                    
                for r in payload.get('receipts', []):
                    receipt = Receipt.objects.create(
                        id=r.get('local_id', r.get('id')),
                        receipt_number=r['receipt_number'],
                        branch_id=r['branch_id'],
                        salesperson_id=r.get('salesperson_id'),
                        customer_name=r.get('customer_name', ''),
                        phone_number=r.get('phone_number', ''),
                        address=r.get('address', ''),
                        area=r.get('area', ''),
                        total_amount=r.get('total_amount', 0),
                        down_payment=r.get('down_payment', 0),
                        installment_system=r.get('installment_system', ''),
                        sale_year=r['sale_year'],
                        sale_month=r['sale_month'],
                        is_cash_sale=r.get('is_cash_sale', False),
                        products_text=r.get('products_text', ''),
                        receipt_hash=r.get('receipt_hash'),
                        is_synced=True
                    )
                    
                    for item in r.get('items', []):
                        SaleItem.objects.create(
                            receipt=receipt,
                            inventory_item_id=item['product_id'],
                            quantity=item['quantity'],
                            unit_price=item['price']
                        )
                        
                    for payment in r.get('payments', []):
                        InstallmentPayment.objects.create(
                            receipt=receipt,
                            payment_date=payment['date'],
                            amount=payment['amount']
                        )
                
                # License sync - mock it to allow app functionality
                ClientLicense.objects.update_or_create(
                    product_id=16, # PRO online
                    defaults={
                        'is_active': True,
                        'is_online_active': True,
                        'company_code': company_code,
                        'machine_id': request.session.get('cloud_master_machine_id')
                    }
                )
                
                messages.success(request, "تم جلب البيانات الأولية بنجاح.")
                return redirect('select_branch')
            else:
                messages.error(request, data.get('message', 'خطأ في جلب البيانات'))
                
        except Exception as e:
            messages.error(request, f"فشل الاتصال: {str(e)}")
            
    return render(request, 'salesapp/initial_sync.html', {})
