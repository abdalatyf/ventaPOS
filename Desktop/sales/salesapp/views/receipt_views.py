# salesapp/views/receipt_views.py
# إدارة الوصلات / الفواتير (Receipts)

import json
from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Max, F, Count, Case, When, Value, IntegerField, Q
from django.views.decorators.http import require_POST
from django.http import HttpResponse ,JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from dateutil.relativedelta import relativedelta

from ..models import (
    Branch, Salesperson, Receipt, SaleItem,
    InstallmentPayment, InventoryItem, ClientLicense
)
from ..utils import to_english_numerals, to_arabic_numerals ,get_available_printers ,clean_invoices_directory , get_default_date
from ..app_functions import parse_installment_string
from .decorators import branch_required


# =========================================================
# دالة مساعدة لتوليد رقم الوصل
# =========================================================

def generate_receipt_number():
    last = Receipt.objects.aggregate(Max('receipt_number'))['receipt_number__max']
    return (last or 0) + 1


# =========================================================
# 1. البحث الذكي للعملاء (Autocomplete API)
# =========================================================

from ..utils import is_date_within_subscription, get_safe_available_qty # 🔴 استيراد الدالة الجديدة

@login_required(login_url='login')
@branch_required
def product_suggestions_api(request):
    term = request.GET.get('term', '')
    
    # 1. الاعتماد على الدالة الذكية لجلب التاريخ الافتراضي (لإلغاء الرقم الوهمي)
    default_year, default_month = get_default_date(request.branch)
    
    try:
        month = int(request.GET.get('month', default_month))
        year = int(request.GET.get('year', default_year))
    except ValueError:
        month, year = default_month, default_year

    if not is_date_within_subscription(year, month):
         return JsonResponse([], safe=False)

    items = InventoryItem.objects.filter(branch=request.branch, name__icontains=term)[:10]
    
    data = []
    for item in items:
        # جلب أقل رصيد مستقبلي آمن
        safe_stock = get_safe_available_qty(item, month, year)
        
        # 2. إرسال الداتا النظيفة بدون كشف سعر الشراء (التكلفة)
        data.append({
            'id': item.id,
            'value': item.name,
            'max': safe_stock,
        })
        
    return JsonResponse(data, safe=False)

def get_customer_suggestions(request):
    from django.http import JsonResponse
    term = to_english_numerals(request.GET.get('term', '').strip())
    field_type = request.GET.get('field', 'name')
    salesperson_id = request.GET.get('salesperson_id')
    current_area = to_english_numerals(request.GET.get('current_area', '').strip())
    current_name = to_english_numerals(request.GET.get('current_name', '').strip())

    if len(term) < 1:
        return JsonResponse([], safe=False)

    suggestions = []
    limit = 15

    try:
        sp_id = int(salesperson_id)
    except:
        sp_id = None

    if field_type == 'area':
        qs = Receipt.objects.filter(area__icontains=term).values('area').annotate(
            use_count=Count('id'),
            relevance=Max(Case(
                When(area__istartswith=term, then=Value(50)),
                When(salesperson_id=sp_id, then=Value(20)),
                default=Value(0), output_field=IntegerField()
            ))
        ).exclude(area='').order_by('-relevance', '-use_count')[:limit]
        for item in qs:
            suggestions.append({'value': to_arabic_numerals(item['area'])})

    elif field_type == 'name':
        qs = Receipt.objects.filter(customer_name__icontains=term).values('customer_name').annotate(
            relevance=Max(Case(
                When(customer_name__istartswith=term, then=Value(50)),
                When(salesperson_id=sp_id, then=Value(20)),
                When(area=current_area, area__gt='', then=Value(10)),
                default=Value(0), output_field=IntegerField()
            ))
        ).order_by('-relevance', 'customer_name')[:limit]
        for item in qs:
            suggestions.append({'value': to_arabic_numerals(item['customer_name'])})

    elif field_type == 'address':
        filters = Q(address__icontains=term) & ~Q(address='')
        qs = Receipt.objects.filter(filters).values('address').annotate(
            relevance=Max(Case(
                When(address__istartswith=term, then=Value(50)),
                When(area=current_area, area__gt='', then=Value(30)),
                When(salesperson_id=sp_id, then=Value(10)),
                When(customer_name=current_name, customer_name__gt='', then=Value(5)),
                default=Value(0), output_field=IntegerField()
            ))
        ).order_by('-relevance', 'address')[:limit]
        for item in qs:
            suggestions.append({'value': to_arabic_numerals(item['address'])})

    elif field_type == 'phone':
        filters = Q(phone_number__icontains=term) & ~Q(phone_number='')
        qs = Receipt.objects.filter(filters).values('phone_number').annotate(
            relevance=Max(Case(
                When(phone_number__istartswith=term, then=Value(50)),
                When(area=current_area, area__gt='', then=Value(30)),
                When(salesperson_id=sp_id, then=Value(10)),
                When(customer_name=current_name, customer_name__gt='', then=Value(5)),
                default=Value(0), output_field=IntegerField()
            ))
        ).order_by('-relevance', 'phone_number')[:limit]
        for item in qs:
            suggestions.append({'value': to_arabic_numerals(item['phone_number'])})

    return JsonResponse(suggestions, safe=False)


# =========================================================
# 2. إضافة وصل (Add Receipt)
# =========================================================

@login_required(login_url='login')
@branch_required
def add_receipt(request):
    current_branch = request.branch
    active_license = ClientLicense.get_active_license()
    is_pro_plan = bool(active_license and active_license.product_id in [1, 4, 5, 6, 7])

    def_year = request.session.get('retained_year')
    def_month = request.session.get('retained_month')

    if not def_year or not def_month:
        def_year, def_month = get_default_date(current_branch)
        
    total_balance = ClientLicense.objects.filter(is_active=True).aggregate(s=Sum('invoices_balance'))['s'] or 0
    if request.method == 'GET' and total_balance > 0 and total_balance <= 50:
        messages.warning(request, "تنبيه هام: يرجى التواصل سريعاً مع خدمة العملاء لتحديث ومراجعة اشتراكك لضمان عدم توقف النظام.")

    context = {
        'salespersons': Salesperson.objects.filter(branch=current_branch),
        'products': InventoryItem.objects.filter(branch=current_branch).order_by('name'),
        'default_year': int(def_year),
        'default_month': int(def_month),
        'next_receipt_number': generate_receipt_number(),
        'success_message': request.session.pop('success_message', None),
        'retained_salesperson_id': request.session.pop('retained_salesperson_id', None),
        'retained_area': request.session.pop('retained_area', ''),
    }

    if request.method == 'POST':
        try:
            with transaction.atomic(using='system'), transaction.atomic(using='default'):
                if not active_license:
                    raise ValueError("عفواً، لا يوجد ترخيص ساري.")

                try:
                    sale_year = int(to_english_numerals(request.POST.get('sale_year')))
                    sale_month = int(to_english_numerals(request.POST.get('sale_month')))
                    invoice_date = date(sale_year, sale_month, 1)
                except:
                    raise ValueError("تاريخ الفاتورة غير صحيح.")

                lic_start_month = active_license.start_date.replace(day=1)
                if invoice_date < lic_start_month:
                    raise ValueError("التاريخ يسبق بداية الاشتراك.")

                if active_license.expiry_date:
                    last_allowed_month = (active_license.expiry_date - relativedelta(months=1)).replace(day=1)
                    if invoice_date > last_allowed_month:
                        raise ValueError("التاريخ بعد انتهاء الاشتراك.")

                    grace_end = active_license.expiry_date + relativedelta(days=25)
                    if date.today() > grace_end:
                        raise ValueError("انتهت فترة الاشتراك.")

                salesperson_id = request.POST.get('salesperson_id')
                if not salesperson_id:
                    raise ValueError("يجب اختيار المندوب.")

                is_cash = request.POST.get('is_cash_sale') == 'on'
                customer_name = to_english_numerals(request.POST.get('customer_name', ''))
                phone = to_english_numerals(request.POST.get('phone_number', ''))
                address = to_english_numerals(request.POST.get('address', ''))
                area = to_english_numerals(request.POST.get('area', ''))

                dp_str = to_english_numerals(request.POST.get('down_payment', '0')).strip()
                down_payment = int(dp_str) if dp_str else 0

                installment_sys = ''
                installment_amounts = []

                if not is_cash:
                    for i in range(1, 4):
                        count_str = request.POST.get(f'sys{i}_count', '0')
                        amount_str = request.POST.get(f'sys{i}_amount', '0')
                        try:
                            m = int(to_english_numerals(count_str)) if count_str else 0
                            a = int(to_english_numerals(amount_str)) if amount_str else 0
                            if m > 0 and a > 0:
                                installment_amounts.extend([a] * m)
                        except ValueError:
                            pass

                    if installment_amounts:
                        parts = []
                        for i in range(1, 4):
                            c = request.POST.get(f'sys{i}_count')
                            a = request.POST.get(f'sys{i}_amount')
                            if c and a and int(to_english_numerals(c)) > 0:
                                parts.append(f"{to_english_numerals(a)}*{to_english_numerals(c)}")
                        installment_sys = " + ".join(parts)
                    else:
                        installment_sys_str = to_english_numerals(request.POST.get('installment_system', ''))
                        parsed = parse_installment_string(installment_sys_str)
                        if isinstance(parsed, str):
                            raise ValueError(parsed)
                        installment_amounts = parsed
                        installment_sys = installment_sys_str

                # إنشاء الوصل الأساسي
                receipt = Receipt.objects.using('default').create(
                    receipt_number=generate_receipt_number(),
                    branch=current_branch,
                    salesperson_id=salesperson_id,
                    sale_year=sale_year,
                    sale_month=sale_month,
                    is_cash_sale=is_cash,
                    customer_name=customer_name,
                    phone_number=phone,
                    address=address,
                    area=area,
                    down_payment=down_payment,
                    installment_system=installment_sys
                )

                if is_pro_plan:
                    items_data = json.loads(request.POST.get('sale_items_json', '[]'))
                    if not items_data:
                        raise ValueError("يجب إضافة أصناف.")

                    total_amount = 0
                    products_list = []
                    items_objs = []
                    
                    now = timezone.now()
                    curr_y, curr_m = now.year, now.month

                    for item in items_data:
                        prod = InventoryItem.objects.using('default').get(pk=item['id'])
                        qty = int(item['quantity'])
                        price = Decimal(item['price'])
                        
                        # 🔴 فحص الرصيد التراكمي المستقبلي (Minimum Running Balance)
                        # 🔴 فحص الرصيد التراكمي باستخدام الدالة الذكية الموحدة
                        min_future_stock = get_safe_available_qty(prod, sale_month, sale_year)
                                
                        if min_future_stock < qty:
                            raise ValueError(f"عفواً، لا يمكن البيع! أقصى كمية يمكن بيعها بأثر رجعي للصنف '{prod.name}' هي ({min_future_stock}) لتجنب حدوث رصيد سالب في الشهور اللاحقة.")
                        
                        # إدراج الصنف بدون تعديل خانة quantity
                        items_objs.append(SaleItem(receipt=receipt, inventory_item=prod, quantity=qty, unit_price=price))
                        total_amount += (qty * float(price))
                        products_list.append(f"{qty} {prod.name}" if qty > 1 else prod.name)

                    SaleItem.objects.using('default').bulk_create(items_objs)
                    total_agreed_installments = sum(installment_amounts) if installment_amounts else 0
                    actual_receipt_total = down_payment + total_agreed_installments
                    receipt.total_amount = total_amount if is_cash else actual_receipt_total
                    receipt.products_text = " + ".join(products_list)

                else:
                    basic_text = request.POST.get('basic_products_text', '').strip()
                    if not basic_text:
                        raise ValueError("يرجى كتابة الأصناف في الفاتورة.")
                    bt_str = to_english_numerals(request.POST.get('basic_total_amount', '0')).strip()
                    basic_total = float(bt_str) if bt_str else 0
                    receipt.products_text = basic_text
                    receipt.total_amount = down_payment if is_cash else basic_total

                if is_cash:
                    receipt.down_payment = receipt.total_amount
                
                receipt.save()

                if not is_cash and installment_amounts:
                    inst_objs = []
                    start_date = date(sale_year, sale_month, 25)
                    for i, amt in enumerate(installment_amounts):
                        due_date = start_date + relativedelta(months=i + 1)
                        inst_objs.append(InstallmentPayment(receipt=receipt, payment_date=due_date, amount=amt))
                    InstallmentPayment.objects.using('default').bulk_create(inst_objs)

                request.session['success_message'] = f"تم حفظ الوصل {receipt.receipt_number}"
                request.session['retained_salesperson_id'] = salesperson_id
                request.session['retained_area'] = area
                request.session['retained_year'] = sale_year
                request.session['retained_month'] = sale_month

                return redirect('add_receipt')

        except Exception as e:
            context['error_message'] = str(e)
            context['retained_customer_name'] = request.POST.get('customer_name', '')
            context['retained_phone'] = request.POST.get('phone_number', '')
            context['retained_address'] = request.POST.get('address', '')
            context['retained_area'] = request.POST.get('area', '')
            context['retained_installment_system'] = request.POST.get('installment_system', '')
            context['retained_down_payment'] = request.POST.get('down_payment', '')
            context['retained_sale_items_json'] = request.POST.get('sale_items_json', '[]')
            context['retained_basic_products'] = request.POST.get('basic_products_text', '')
            context['retained_is_cash'] = request.POST.get('is_cash_sale') == 'on'
            context['retained_salesperson_id'] = request.POST.get('salesperson_id')

    return render(request, 'salesapp/add_receipt.html', context)


# =========================================================
# 3. تعديل وصل (Edit Receipt)
# =========================================================

@login_required(login_url='login')
@branch_required
def edit_receipt(request, receipt_id):
    current_branch = request.branch
    receipt = get_object_or_404(Receipt, pk=receipt_id, branch=current_branch)

    active_license = ClientLicense.get_active_license()
    user_has_pro_license = bool(active_license and active_license.product_id in [1, 4, 5, 6, 7])
    has_items = receipt.items.exists()
    is_pro_plan = user_has_pro_license and has_items

    if request.method == 'POST':
        try:
            with transaction.atomic():
                if not active_license or not active_license.is_active:
                    raise ValueError("لا يوجد ترخيص ساري.")

                try:
                    sale_year = int(to_english_numerals(request.POST.get('sale_year')))
                    sale_month = int(to_english_numerals(request.POST.get('sale_month')))
                    invoice_date = date(sale_year, sale_month, 1)
                except:
                    raise ValueError("تاريخ الفاتورة غير صحيح.")

                lic_start_month = active_license.start_date.replace(day=1)
                if invoice_date < lic_start_month:
                    raise ValueError("التاريخ يسبق بداية الاشتراك.")

                if active_license.expiry_date:
                    last_allowed_month = (active_license.expiry_date - relativedelta(months=2)).replace(day=1)
                    if invoice_date > last_allowed_month:
                        raise ValueError("التاريخ بعد انتهاء الاشتراك.")
                    grace_end = active_license.expiry_date + relativedelta(days=25)
                    if date.today() > grace_end:
                        raise ValueError("انتهت فترة الاشتراك.")

                receipt.customer_name = to_english_numerals(request.POST.get('customer_name'))
                receipt.phone_number = to_english_numerals(request.POST.get('phone_number'))
                receipt.address = to_english_numerals(request.POST.get('address'))
                receipt.area = to_english_numerals(request.POST.get('area'))
                receipt.sale_year = sale_year
                receipt.sale_month = sale_month
                receipt.is_cash_sale = request.POST.get('is_cash_sale') == 'on'

                dp_str = to_english_numerals(request.POST.get('down_payment', '0')).strip()
                receipt.down_payment = int(dp_str) if dp_str else 0

                salesperson_id = request.POST.get('salesperson_id')
                if salesperson_id:
                    receipt.salesperson_id = salesperson_id

                installment_amounts = []
                if receipt.is_cash_sale:
                    receipt.installment_system = ""
                else:
                    for i in range(1, 4):
                        count_str = request.POST.get(f'sys{i}_count', '0')
                        amount_str = request.POST.get(f'sys{i}_amount', '0')
                        try:
                            m = int(count_str) if count_str else 0
                            a = int(amount_str) if amount_str else 0
                            if m > 0 and a > 0:
                                installment_amounts.extend([a] * m)
                        except ValueError:
                            pass

                    if installment_amounts:
                        parts = []
                        for i in range(1, 4):
                            c = request.POST.get(f'sys{i}_count')
                            a = request.POST.get(f'sys{i}_amount')
                            if c and a and int(c) > 0:
                                parts.append(f"{a}*{c}")
                        receipt.installment_system = " + ".join(parts)
                    else:
                        installment_sys_str = to_english_numerals(request.POST.get('installment_system', ''))
                        parsed = parse_installment_string(installment_sys_str)
                        if isinstance(parsed, str):
                            raise ValueError(parsed)
                        installment_amounts = parsed
                        receipt.installment_system = installment_sys_str

                if is_pro_plan:
                    items_data = json.loads(request.POST.get('sale_items_json', '[]'))
                    if not items_data:
                        raise ValueError("يجب إضافة أصناف.")

                    # تنظيف الفاتورة القديمة أولاً لكي لا تتعارض مع حساب الرصيد القادم
                    receipt.items.all().delete()

                    new_items = []
                    new_total = 0
                    str_list = []
                    
                    now = timezone.now()
                    curr_y, curr_m = now.year, now.month

                    for item in items_data:
                        prod = InventoryItem.objects.get(pk=item['id'])
                        qty = int(item['quantity'])
                        price = float(item['price'])
                        
                        # 🔴 فحص الرصيد التراكمي المستقبلي
                        # 🔴 فحص الرصيد التراكمي باستخدام الدالة الذكية الموحدة
                        min_future_stock = get_safe_available_qty(prod, sale_month, sale_year)
                                
                        if min_future_stock < qty:
                            raise ValueError(f"عفواً، أقصى كمية يمكن بيعها أو تعديلها للصنف '{prod.name}' في هذا التاريخ هي ({min_future_stock}).")
                        
                        new_items.append(SaleItem(receipt=receipt, inventory_item=prod, quantity=qty, unit_price=price))
                        new_total += (qty * price)
                        str_list.append(f"{qty} {prod.name}" if qty > 1 else prod.name)

                    SaleItem.objects.bulk_create(new_items)
                    total_agreed_installments = sum(installment_amounts) if installment_amounts else 0
                    actual_receipt_total = receipt.down_payment + total_agreed_installments
                    receipt.total_amount = new_total if receipt.is_cash_sale else actual_receipt_total
                    receipt.products_text = " + ".join(str_list)

                else:
                    basic_text = request.POST.get('basic_products_text', '').strip()
                    if not basic_text:
                        raise ValueError("يرجى كتابة الأصناف في الفاتورة.")
                    bt_str = to_english_numerals(request.POST.get('basic_total_amount', '0')).strip()
                    basic_total = float(bt_str) if bt_str else 0
                    receipt.products_text = basic_text
                    receipt.total_amount = receipt.down_payment if receipt.is_cash_sale else basic_total
                    
                    if receipt.items.exists():
                        receipt.items.all().delete()

                if receipt.is_cash_sale:
                    receipt.down_payment = receipt.total_amount
                receipt.save()

                receipt.payments.all().delete()
                if not receipt.is_cash_sale and installment_amounts:
                    inst_objs = []
                    start_date = date(sale_year, sale_month, 25)
                    for i, amt in enumerate(installment_amounts):
                        due_date = start_date + relativedelta(months=i + 1)
                        inst_objs.append(InstallmentPayment(receipt=receipt, payment_date=due_date, amount=amt))
                    InstallmentPayment.objects.bulk_create(inst_objs)

                messages.success(request, f"تم تعديل الفاتورة رقم {receipt.receipt_number} بنجاح.")
                return redirect('search_receipts')

        except Exception as e:
            items = receipt.items.all()
            current_items_json = json.dumps([{
                'id': str(i.inventory_item.id), 'name': i.inventory_item.name,
                'quantity': i.quantity, 'price': str(i.unit_price)
            } for i in items])
            products = InventoryItem.objects.filter(branch=current_branch)
            context = {
                'receipt': receipt, 'products': products,
                'sale_items_json_str': current_items_json,
                'salespersons': Salesperson.objects.filter(branch=current_branch),
                'error_message': f"حدث خطأ: {str(e)}",
                'is_pro_plan': is_pro_plan
            }
            return render(request, 'salesapp/edit_receipt.html', context)

    items = receipt.items.all()
    current_items_json = json.dumps([{
        'id': str(i.inventory_item.id), 'name': i.inventory_item.name,
        'quantity': i.quantity, 'price': str(i.unit_price)
    } for i in items])
    products = InventoryItem.objects.filter(branch=current_branch)
    context = {
        'receipt': receipt, 'products': products,
        'sale_items_json_str': current_items_json,
        'salespersons': Salesperson.objects.filter(branch=current_branch),
        'page_title': f'تعديل وصل {receipt.receipt_number}',
        'is_pro_plan': is_pro_plan
    }
    return render(request, 'salesapp/edit_receipt.html', context)


# =========================================================
# 4. بحث الوصلات (Search Receipts)
# =========================================================

@login_required(login_url='login')
@branch_required
def search_receipts(request):
    clean_invoices_directory()
    current_branch = request.branch
    receipts = Receipt.objects.filter(branch=current_branch).order_by('-receipt_number', '-id')

    salesperson_id = request.GET.get('salesperson')
    year = request.GET.get('year')
    month = request.GET.get('month')
    receipt_from = request.GET.get('receipt_from')
    receipt_to = request.GET.get('receipt_to')
    customer = request.GET.get('customer')
    phone = request.GET.get('phone')
    address = request.GET.get('address')
    area = request.GET.get('area')

    if salesperson_id: receipts = receipts.filter(salesperson_id=salesperson_id)
    if year: receipts = receipts.filter(sale_year=year)
    if month: receipts = receipts.filter(sale_month=month)
    if receipt_from: receipts = receipts.filter(receipt_number__gte=receipt_from)
    if receipt_to: receipts = receipts.filter(receipt_number__lte=receipt_to)
    if customer: receipts = receipts.filter(customer_name__icontains=customer)
    if phone: receipts = receipts.filter(phone_number__icontains=phone)
    if address: receipts = receipts.filter(address__icontains=address)
    if area: receipts = receipts.filter(area__icontains=area)

    paginator = Paginator(receipts, 100)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    search_params = request.GET.copy()
    if 'page' in search_params:
        del search_params['page']

    context = {
        'page_title': 'بحث / طباعة الوصلات',
        'receipts': page_obj,
        'page_obj': page_obj,
        'salespersons': Salesperson.objects.filter(branch=current_branch),
        'available_years': Receipt.objects.filter(branch=current_branch).values_list('sale_year', flat=True).distinct().order_by('-sale_year'),
        'req_get': request.GET,
        'printers': get_available_printers(),
        'search_params': search_params
    }

    if request.headers.get('HX-Request'):
        return render(request, 'salesapp/includes/receipt_list_rows.html', context)

    return render(request, 'salesapp/search_receipts.html', context)


# =========================================================
# 5. حذف وصل واحد
# =========================================================

@login_required(login_url='login')
@branch_required
@require_POST
def delete_receipt(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk, branch=request.branch)
    try:
        with transaction.atomic():
            # تم حذف الاعتماد على تحديث الكمية يدوياً
            receipt.delete()
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">حدث خطأ أثناء الحذف: {str(e)}</div>')

    return search_receipts(request)


# =========================================================
# 6. حذف جماعي للوصلات
# =========================================================

@login_required(login_url='login')
@branch_required
@require_POST
def delete_all_receipts(request):
    current_branch = request.branch
    receipts_to_delete = Receipt.objects.filter(branch=current_branch)

    salesperson_id = request.POST.get('salesperson')
    year = request.POST.get('year')
    month = request.POST.get('month')
    receipt_from = request.POST.get('receipt_from')
    receipt_to = request.POST.get('receipt_to')
    customer = request.POST.get('customer')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    area = request.POST.get('area')

    if salesperson_id: receipts_to_delete = receipts_to_delete.filter(salesperson_id=salesperson_id)
    if year: receipts_to_delete = receipts_to_delete.filter(sale_year=year)
    if month: receipts_to_delete = receipts_to_delete.filter(sale_month=month)
    if receipt_from: receipts_to_delete = receipts_to_delete.filter(receipt_number__gte=receipt_from)
    if receipt_to: receipts_to_delete = receipts_to_delete.filter(receipt_number__lte=receipt_to)
    if customer: receipts_to_delete = receipts_to_delete.filter(customer_name__icontains=customer)
    if phone: receipts_to_delete = receipts_to_delete.filter(phone_number__icontains=phone)
    if address: receipts_to_delete = receipts_to_delete.filter(address__icontains=address)
    if area: receipts_to_delete = receipts_to_delete.filter(area__icontains=area)

    count = receipts_to_delete.count()

    if count > 0:
        try:
            with transaction.atomic():
                # تم حذف الاعتماد على تحديث الكمية يدوياً
                receipts_to_delete.delete()

            response = HttpResponse(f'<div class="alert alert-danger">تم حذف {count} وصل بنجاح.</div>')
            response['HX-Trigger'] = 'receiptsDeleted'
            return response

        except Exception as e:
            return HttpResponse(f'<div class="alert alert-danger">حدث خطأ أثناء الحذف الجماعي: {str(e)}</div>')
    else:
        return HttpResponse('<div class="alert alert-warning">لا توجد بيانات للحذف</div>')