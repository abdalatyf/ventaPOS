# salesapp/views/inventory_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Sum, F, Q, ExpressionWrapper, FloatField, Prefetch
from django.db.models import ProtectedError
from django.views.decorators.http import require_POST

from ..models import (
    InventoryItem, CommissionHistory, InventoryAdjustment, 
    PurchaseInvoiceItem, SaleItem
)
from .decorators import branch_required, pro_plan_required
from ..utils import get_default_date, is_date_within_subscription

# ==========================================================
# 📦 1. إدارة الأصناف والمخزن (Products)
# ==========================================================

@login_required(login_url='login')
@branch_required
@pro_plan_required
def manage_products(request):
    current_branch = request.branch
    error_message = None
    def_year, def_month = get_default_date(current_branch)

    if request.method == 'POST':
        item_id = request.POST.get('item_id') 
        product_name = request.POST.get('product_name')
        
        try:
            qty = int(request.POST.get('initial_quantity', 0) or 0)
            price = float(request.POST.get('initial_purchase_price', 0) or 0.0)
            comm = float(request.POST.get('initial_commission', 0) or 0.0)
            s_month = int(request.POST.get('start_month') or def_month)
            s_year = int(request.POST.get('start_year') or def_year)
        except ValueError:
            qty, price, comm, s_month, s_year = 0, 0.0, 0.0, def_month, def_year

        if not is_date_within_subscription(s_year, s_month):
            error_message = "❌ خطأ: تاريخ بداية الصنف يقع خارج فترة الرخصة الفعالة."
        else:
            if item_id:
                try:
                    item = InventoryItem.objects.get(id=item_id, branch=current_branch)
                    item.name = product_name
                    item.initial_quantity = qty
                    item.initial_purchase_price = price
                    item.initial_commission_amount = comm
                    item.initial_month = s_month
                    item.initial_year = s_year
                    item.save()
                    messages.success(request, f"✅ تم تعديل الصنف '{product_name}' بنجاح.")
                except InventoryItem.DoesNotExist:
                    error_message = "❌ الصنف غير موجود."
                except IntegrityError:
                    error_message = "❌ هذا الاسم مستخدم لمنتج آخر."
            else:
                if product_name:
                    try:
                        new_item = InventoryItem.objects.create(
                            name=product_name, branch=current_branch,
                            initial_quantity=qty, initial_purchase_price=price,
                            initial_commission_amount=comm, initial_month=s_month, initial_year=s_year
                        )
                        CommissionHistory.objects.create(
                            item=new_item, commission_amount=new_item.initial_commission_amount,
                            activation_month=new_item.initial_month, activation_year=new_item.initial_year
                        )
                        messages.success(request, f"✅ تم تعريف الصنف '{product_name}' بنجاح.")
                    except IntegrityError:
                        error_message = f"❌ خطأ: اسم الصنف '{product_name}' موجود مسبقاً."

        if not error_message:
            return redirect('manage_products')

    # التشخيص الذاتي
    all_items_for_healing = InventoryItem.objects.filter(branch=current_branch)
    for item in all_items_for_healing:
        if not CommissionHistory.objects.filter(item=item).exists():
            CommissionHistory.objects.create(
                item=item,
                activation_month=item.initial_month or def_month,
                activation_year=item.initial_year or def_year,
                commission_amount=item.initial_commission_amount or 0
            )

    history_prefetch = Prefetch('commission_records', queryset=CommissionHistory.objects.order_by('-activation_year', '-activation_month'))
    all_products = InventoryItem.objects.filter(branch=current_branch).prefetch_related(history_prefetch)
    
    total_inventory_value = sum((p.initial_quantity or 0) * (p.initial_purchase_price or 0) for p in all_products)
    for product in all_products:
        product.initial_total_cost = (product.initial_quantity or 0) * (product.initial_purchase_price or 0)

    context = {
        'products': all_products, 'total_inventory_value': total_inventory_value,
        'page_title': 'المخزن والأصناف', 'error_message': error_message,
        'current_month': def_month, 'current_year': def_year,
    }
    return render(request, 'salesapp/manage_products.html', context)


@login_required(login_url='login')
@branch_required
@pro_plan_required
def edit_product(request, pk):
    product = get_object_or_404(InventoryItem, pk=pk, branch=request.branch)
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name').strip()
            product.save()
            messages.success(request, f"تم تعديل الصنف {product.name} بنجاح.")
        except IntegrityError:
            messages.error(request, "خطأ: اسم الصنف موجود مسبقاً في هذا الفرع.")
    return redirect('manage_products')


@login_required(login_url='login')
@branch_required
@pro_plan_required
def delete_product(request, pk):
    product = get_object_or_404(InventoryItem, pk=pk, branch=request.branch)
    try:
        product_name = product.name
        product.delete()
        messages.success(request, f"تم حذف الصنف '{product_name}' بنجاح.")
    except ProtectedError:
        messages.error(request, "خطأ: لا يمكن الحذف لوجود عمليات مرتبطة به.")
    return redirect('manage_products')


# ==========================================================
# 💸 2. إدارة المندبات (Commission Time Machine)
# ==========================================================

@login_required(login_url='login')
@branch_required
@pro_plan_required
@require_POST
def update_commission(request):
    item_id = request.POST.get('item_id')
    try:
        new_comm = float(request.POST.get('new_commission', 0))
        apply_month = int(request.POST.get('apply_month'))
        apply_year = int(request.POST.get('apply_year'))
    except ValueError:
        messages.error(request, "❌ بيانات غير صحيحة.")
        return redirect('manage_products')

    if not is_date_within_subscription(apply_year, apply_month):
        messages.error(request, "❌ خطأ: تاريخ يقع خارج الرخصة.")
        return redirect('manage_products')

    try:
        item = InventoryItem.objects.get(id=item_id, branch=request.branch)
        commission_record, created = CommissionHistory.objects.update_or_create(
            item=item, activation_month=apply_month, activation_year=apply_year,
            defaults={'commission_amount': new_comm}
        )
        messages.success(request, f"✅ تم {'تسجيل' if created else 'تعديل'} مندبة الصنف '{item.name}'.")
    except InventoryItem.DoesNotExist:
        messages.error(request, "❌ الصنف غير موجود.")
        
    return redirect('manage_products')


@login_required(login_url='login')
@branch_required
@pro_plan_required
@require_POST
def edit_commission_record(request, record_id):
    record = get_object_or_404(CommissionHistory, id=record_id, item__branch=request.branch)
    try:
        record.commission_amount = float(request.POST.get('commission_amount', 0))
        record.activation_month = int(request.POST.get('activation_month'))
        record.activation_year = int(request.POST.get('activation_year'))
        record.save()
        messages.success(request, f"✏️ تم تعديل المندبة بنجاح.")
    except ValueError:
        messages.error(request, "❌ بيانات غير صحيحة.")
    return redirect('manage_products')


@login_required(login_url='login')
@branch_required
@pro_plan_required
def delete_commission_record(request, record_id):
    record = get_object_or_404(CommissionHistory, id=record_id, item__branch=request.branch)
    if CommissionHistory.objects.filter(item=record.item).count() <= 1:
        messages.error(request, "❌ لا يمكن حذف هذا السجل لأنه الوحيد.")
    else:
        record.delete()
        messages.success(request, "🗑️ تم حذف السجل بنجاح.")
    return redirect('manage_products')


# ==========================================================
# 📊 3. التسويات الجردية وكارت الصنف
# ==========================================================

@login_required(login_url='login')
@branch_required
@require_POST
def add_adjustment(request):
    item_id = request.POST.get('item_id')
    month = int(request.POST.get('month'))
    year = int(request.POST.get('year'))
    adj_type = request.POST.get('adjustment_type')
    qty = request.POST.get('quantity')
    reason = request.POST.get('reason', '')

    if not is_date_within_subscription(year, month):
        messages.error(request, "❌ خطأ: يقع خارج فترة الرخصة.")
        return redirect(f"/reports/sales/?month={month}&year={year}")

    try:
        item = InventoryItem.objects.get(id=item_id, branch=request.branch)
        if int(qty) > 0:
            InventoryAdjustment.objects.create(item=item, adjustment_type=adj_type, quantity=int(qty), reason=reason, month=month, year=year)
            messages.success(request, f"تم التسجيل بنجاح.")
        else:
            messages.error(request, "الكمية يجب أن تكون أكبر من الصفر.")
    except Exception:
        messages.error(request, "بيانات غير صحيحة.")
    return redirect(f"/reports/sales/?month={month}&year={year}")


@login_required(login_url='login')
@branch_required
@pro_plan_required
def product_ledger(request, pk):
    product = get_object_or_404(InventoryItem, pk=pk, branch=request.branch)
    def_y, def_m = get_default_date(request.branch)
    def_y, def_m = int(def_y), int(def_m)

    from_y = request.GET.get('from_year')
    from_m = request.GET.get('from_month')
    to_y = request.GET.get('to_year')
    to_m = request.GET.get('to_month')

    start_y = int(from_y) if from_y else product.initial_year
    start_m = int(from_m) if from_m else product.initial_month

    if to_y and to_m:
        end_y, end_m = int(to_y), int(to_m)
    else:
        end_y, end_m = def_y, def_m
        last_purchase = PurchaseInvoiceItem.objects.filter(inventory_item=product).order_by('-invoice__invoice_year', '-invoice__invoice_month').first()
        if last_purchase and (last_purchase.invoice.invoice_year > end_y or (last_purchase.invoice.invoice_year == end_y and last_purchase.invoice.invoice_month > end_m)):
            end_y, end_m = last_purchase.invoice.invoice_year, last_purchase.invoice.invoice_month
            
        last_sale = SaleItem.objects.filter(inventory_item=product).order_by('-receipt__sale_year', '-receipt__sale_month').first()
        if last_sale and (last_sale.receipt.sale_year > end_y or (last_sale.receipt.sale_year == end_y and last_sale.receipt.sale_month > end_m)):
            end_y, end_m = last_sale.receipt.sale_year, last_sale.receipt.sale_month

    available_years = range(product.initial_year, end_y + 2)
    available_months = range(1, 13)

    monthly_summary = []
    grand_totals = {'cash_profit': 0.0, 'inst_profit': 0.0, 'adj_profit': 0.0, 'net_profit': 0.0, 'cash_qty': 0, 'inst_qty': 0}

    temp_y, temp_m = start_y, start_m
    while (temp_y < end_y) or (temp_y == end_y and temp_m <= end_m):
        prev_m, prev_y = (12, temp_y - 1) if temp_m == 1 else (temp_m - 1, temp_y)
        
        opening = product.get_stock_at_date(prev_m, prev_y)
        if temp_y == product.initial_year and temp_m == product.initial_month:
            opening += product.initial_quantity

        closing = product.get_stock_at_date(temp_m, temp_y)
        cost_unit = float(product.get_price_at_date(temp_m, temp_y))
        comm_unit = float(product.get_commission_at_date(temp_m, temp_y))

        # 🔴 الاعتماد على PurchaseInvoiceItem بدلاً من StockTransaction
        purchases = PurchaseInvoiceItem.objects.filter(inventory_item=product, invoice__invoice_month=temp_m, invoice__invoice_year=temp_y, invoice__invoice_type='PURCHASE').aggregate(s=Sum('quantity'))['s'] or 0
        returns = PurchaseInvoiceItem.objects.filter(inventory_item=product, invoice__invoice_month=temp_m, invoice__invoice_year=temp_y, invoice__invoice_type='RETURN').aggregate(s=Sum('quantity'))['s'] or 0
        net_purchases = purchases - returns

        adjs = InventoryAdjustment.objects.filter(item=product, month=temp_m, year=temp_y)
        surplus = adjs.filter(adjustment_type__in=['SURPLUS', 'ADD']).aggregate(s=Sum('quantity'))['s'] or 0
        deficit = adjs.filter(adjustment_type__in=['DEFICIT', 'SUBTRACT']).aggregate(s=Sum('quantity'))['s'] or 0
        
        cash_sales = SaleItem.objects.filter(inventory_item=product, receipt__sale_year=temp_y, receipt__sale_month=temp_m, receipt__is_cash_sale=True).aggregate(
            qty=Sum('quantity'), rev=Sum(F('quantity') * F('unit_price'), output_field=FloatField())
        )
        c_qty, c_rev = cash_sales['qty'] or 0, cash_sales['rev'] or 0.0
        c_cost, c_profit = c_qty * cost_unit, c_rev - (c_qty * cost_unit)

        inst_sales = SaleItem.objects.filter(inventory_item=product, receipt__sale_year=temp_y, receipt__sale_month=temp_m, receipt__is_cash_sale=False).annotate(
            coll_comm=ExpressionWrapper(((F('quantity') * F('unit_price')) * (F('receipt__total_amount') - F('receipt__down_payment')) * 0.10) / F('receipt__total_amount'), output_field=FloatField())
        ).aggregate(qty=Sum('quantity'), rev=Sum(F('quantity') * F('unit_price'), output_field=FloatField()), coll=Sum('coll_comm', output_field=FloatField()))
        
        i_qty, i_rev, i_coll_comm = inst_sales['qty'] or 0, inst_sales['rev'] or 0.0, inst_sales['coll'] or 0.0
        i_profit = i_rev - (i_qty * cost_unit) - (i_qty * comm_unit) - i_coll_comm
        adj_profit = (surplus * cost_unit) - (deficit * cost_unit)
        month_net_profit = c_profit + i_profit + adj_profit

        if opening > 0 or net_purchases > 0 or (c_qty + i_qty) > 0 or surplus > 0 or deficit > 0 or closing > 0:
            monthly_summary.append({
                'year': temp_y, 'month': temp_m, 'opening': opening, 'purchases': net_purchases, 'sales': c_qty + i_qty,
                'surplus': surplus, 'deficit': deficit, 'closing': closing, 'cost_unit': cost_unit, 'total_val': closing * cost_unit, 
                'cash': {'qty': c_qty, 'avg_sell': (c_rev / c_qty) if c_qty > 0 else 0.0, 'rev': c_rev, 'cost': c_cost, 'profit': c_profit, 'profit_unit': (c_profit / c_qty) if c_qty > 0 else 0.0},
                'inst': {'qty': i_qty, 'avg_sell': (i_rev / i_qty) if i_qty > 0 else 0.0, 'rev': i_rev, 'cost': i_qty * cost_unit, 'sales_comm_unit': comm_unit, 'sales_comm': i_qty * comm_unit, 'coll_comm': i_coll_comm, 'profit': i_profit, 'coll_comm_unit': (i_coll_comm / i_qty) if i_qty > 0 else 0.0, 'profit_unit': (i_profit / i_qty) if i_qty > 0 else 0.0},
                'adj_profit': adj_profit, 'month_net_profit': month_net_profit
            })
            grand_totals['cash_profit'] += c_profit
            grand_totals['inst_profit'] += i_profit
            grand_totals['adj_profit'] += adj_profit
            grand_totals['net_profit'] += month_net_profit
            grand_totals['cash_qty'] += c_qty
            grand_totals['inst_qty'] += i_qty

        temp_m += 1
        if temp_m > 12:
            temp_m = 1
            temp_y += 1
            
    monthly_summary.reverse()
    prev_start_m, prev_start_y = (12, start_y - 1) if start_m == 1 else (start_m - 1, start_y)
    brought_forward_qty = product.get_stock_at_date(prev_start_m, prev_start_y)
    if start_y == product.initial_year and start_m == product.initial_month:
        brought_forward_qty += product.initial_quantity

    all_movements = [{'year': start_y, 'month': start_m, 'id': 0, 'label': 'رصيد مرحل (بداية الفترة)', 'type': 'INITIAL', 'in_qty': brought_forward_qty, 'out_qty': 0, 'ref': '-', 'person': 'النظام'}]
    
    for s in SaleItem.objects.filter(inventory_item=product).values('id', 'receipt__sale_year', 'receipt__sale_month', 'quantity', 'unit_price', 'receipt__receipt_number', 'receipt__customer_name'):
        y, m = s['receipt__sale_year'], s['receipt__sale_month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            all_movements.append({'year': y, 'month': m, 'id': s['id'], 'label': 'فاتورة بيع', 'type': 'OUT', 'in_qty': 0, 'out_qty': s['quantity'], 'ref': s['receipt__receipt_number'], 'person': s['receipt__customer_name']})

    for p in PurchaseInvoiceItem.objects.filter(inventory_item=product).values('id', 'invoice__invoice_year', 'invoice__invoice_month', 'quantity', 'invoice__invoice_type', 'invoice__invoice_number', 'invoice__supplier__name'):
        y, m = p['invoice__invoice_year'], p['invoice__invoice_month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            is_in = p['invoice__invoice_type'] == 'PURCHASE'
            all_movements.append({'year': y, 'month': m, 'id': p['id'], 'label': 'شراء' if is_in else 'مرتجع مصنع', 'type': 'IN' if is_in else 'OUT', 'in_qty': p['quantity'] if is_in else 0, 'out_qty': 0 if is_in else p['quantity'], 'ref': p['invoice__invoice_number'], 'person': p['invoice__supplier__name']})

    for a in InventoryAdjustment.objects.filter(item=product).values('id', 'year', 'month', 'quantity', 'adjustment_type', 'reason'):
        y, m = a['year'], a['month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            is_add = a['adjustment_type'] in ['ADD', 'SURPLUS']
            all_movements.append({'year': y, 'month': m, 'id': a['id'], 'label': 'تسوية (زيادة)' if is_add else 'تسوية (عجز)', 'type': 'IN' if is_add else 'OUT', 'in_qty': a['quantity'] if is_add else 0, 'out_qty': 0 if is_add else a['quantity'], 'ref': '-', 'person': a['reason']})

    all_movements.sort(key=lambda x: (x['year'], x['month'], x['id']))
    running_balance = 0
    for mov in all_movements:
        running_balance += (mov['in_qty'] - mov['out_qty'])
        mov['balance'] = running_balance

    context = {
        'product': product, 'detailed_movements': reversed(all_movements), 'monthly_summary': monthly_summary,
        'grand_totals': grand_totals, 'start_m': start_m, 'start_y': start_y, 'end_m': end_m, 'end_y': end_y,
        'available_months': available_months, 'available_years': available_years, 'page_title': f'كارت صنف: {product.name}'
    }
    return render(request, 'salesapp/product_ledger.html', context)