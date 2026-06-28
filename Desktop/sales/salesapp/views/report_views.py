# salesapp/views/report_views.py
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField, Case, When, Value, ExpressionWrapper
from django.utils import timezone
from ..models import Receipt, SaleItem, Salesperson, Expense, InventoryItem, InventoryAdjustment,PurchaseInvoiceItem
from .decorators import branch_required, pro_plan_required
from ..utils import get_default_date

@login_required(login_url='login')
@branch_required
@pro_plan_required
def sales_reports(request):
    """تقرير الجرد الموحد (مخزن + أرباح + سجل تفصيلي)"""
    current_branch = request.branch

# 1. تحديد التاريخ (الشهر والسنة) باستخدام الدالة الذكية
    default_year, default_month = get_default_date(current_branch)

    try:
        selected_year = int(request.GET.get('year', default_year))
        selected_month = int(request.GET.get('month', default_month))
    except:
        selected_year, selected_month = default_year, default_month


    selected_salesperson_id = request.GET.get('salesperson', '')
    salespersons = Salesperson.objects.filter(branch=current_branch)

    available_years = sorted(list(set(Receipt.objects.filter(branch=current_branch).values_list('sale_year', flat=True))), reverse=True)
    if not available_years:
        available_years = [default_year]
    available_months = list(range(1, 13))

    # ==========================================================
    # 💰 الجزء الأول: بيانات التبويب المالي (الأرباح والخسائر)
    # ==========================================================
    report_queryset = SaleItem.objects.filter(
        receipt__branch=current_branch,
        receipt__sale_year=selected_year,
        receipt__sale_month=selected_month
    )
    if selected_salesperson_id:
        report_queryset = report_queryset.filter(receipt__salesperson_id=selected_salesperson_id)

    # التوزيع النسبي الذكي لعمولة التحصيل (استبعاد المقدمات من الحسبة)
    report_queryset = report_queryset.annotate(
        item_coll_comm=Case(
            When(receipt__is_cash_sale=True, then=Value(0.0)),
            When(receipt__total_amount__gt=0, then=ExpressionWrapper(
                ((F('quantity') * F('unit_price')) * (F('receipt__total_amount') - F('receipt__down_payment')) * 0.10) / F('receipt__total_amount'),
                output_field=FloatField()
            )),
            default=Value(0.0),
            output_field=FloatField()
        )
    )

    grouped_items = report_queryset.values(
        'inventory_item__id', 'inventory_item__name', 'receipt__is_cash_sale'
    ).annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum(F('quantity') * F('unit_price'), output_field=FloatField()),
        total_coll_comm_sum=Sum('item_coll_comm', output_field=FloatField())
    ).order_by('-total_qty')

    item_ids = [item['inventory_item__id'] for item in grouped_items]
    items_dict = {item.id: item for item in InventoryItem.objects.filter(id__in=item_ids)}

    cash_sales_list, installment_sales_list = [], []
    grand_cost = total_sales_comm_fixed = 0.0
    grand_revenue_items = grand_qty = 0

    for item in grouped_items:
        inv_item = items_dict.get(item['inventory_item__id'])
        if not inv_item: continue
        
        qty = int(item['total_qty'] or 0)
        total_rev = float(item['total_rev'] or 0)
        coll_comm = float(item['total_coll_comm_sum'] or 0.0) 
        
        # استخدام الدوال التاريخية الذكية
        cost_unit = float(inv_item.get_price_at_date(selected_month, selected_year))
        comm_unit = float(inv_item.get_commission_at_date(selected_month, selected_year))

        total_cost = qty * cost_unit
        total_sales_comm = qty * comm_unit
        avg_sell = total_rev / qty if qty > 0 else 0

        row = {
            'name': item['inventory_item__name'], 'qty': qty, 'avg_sell': avg_sell,
            'cost_per_unit': cost_unit, 'sales_comm_per_unit': comm_unit,
            'total_rev': total_rev, 'total_cost': total_cost, 
            'total_sales_comm': total_sales_comm, 
            'coll_comm_per_unit': coll_comm / qty if qty else 0,
            'total_coll_comm': coll_comm,
            'total_profit': total_rev - total_cost - total_sales_comm - coll_comm,
            'avg_profit': (total_rev - total_cost - total_sales_comm - coll_comm) / qty if qty else 0
        }
        if item['receipt__is_cash_sale']: cash_sales_list.append(row)
        else: installment_sales_list.append(row)

        grand_cost += total_cost
        total_sales_comm_fixed += total_sales_comm
        grand_revenue_items += total_rev
        grand_qty += qty

    # ==========================================================
    # 📦 الجزء الثاني: بيانات تبويب المخزن (آلة الزمن والتسويات)
    # ==========================================================
    prev_m, prev_y = (12, selected_year-1) if selected_month == 1 else (selected_month-1, selected_year)
    
    inventory_report_list = []
    total_inventory_value = 0.0
    total_adjustments_count = 0
    
    all_branch_items = InventoryItem.objects.filter(branch=current_branch)
    for item in all_branch_items:
        if selected_year < item.initial_year or (selected_year == item.initial_year and selected_month < item.initial_month):
            continue

        opening = item.get_stock_at_date(prev_m, prev_y)
        # إظهار الرصيد الافتتاحي في خانة رصيد أول لو ده شهر البداية للمنتج
        if item.initial_year == selected_year and item.initial_month == selected_month:
            opening += item.initial_quantity

        final = item.get_stock_at_date(selected_month, selected_year)
        price = float(item.get_price_at_date(selected_month, selected_year))
        comm = float(item.get_commission_at_date(selected_month, selected_year))
        
# الاعتماد على الفواتير بدلاً من جدول الحركات الملغي
        purchases = PurchaseInvoiceItem.objects.filter(
            inventory_item=item, 
            invoice__invoice_month=selected_month, 
            invoice__invoice_year=selected_year, 
            invoice__invoice_type='PURCHASE'
        ).aggregate(s=Sum('quantity'))['s'] or 0
        
        returns = PurchaseInvoiceItem.objects.filter(
            inventory_item=item, 
            invoice__invoice_month=selected_month, 
            invoice__invoice_year=selected_year, 
            invoice__invoice_type='RETURN'
        ).aggregate(s=Sum('quantity'))['s'] or 0
        sales = SaleItem.objects.filter(inventory_item=item, receipt__sale_month=selected_month, receipt__sale_year=selected_year).aggregate(s=Sum('quantity'))['s'] or 0
        
        adjs = InventoryAdjustment.objects.filter(item=item, month=selected_month, year=selected_year)
        surplus = adjs.filter(adjustment_type='SURPLUS').aggregate(s=Sum('quantity'))['s'] or 0
        deficit = adjs.filter(adjustment_type='DEFICIT').aggregate(s=Sum('quantity'))['s'] or 0
        
        total_inventory_value += (final * price)
        total_adjustments_count += (surplus + deficit)

        inventory_report_list.append({
            'item': item, 'opening': opening, 'purchases': purchases, 'returns': returns,
            'sales': sales, 'surplus': surplus, 'deficit': deficit, 'final': final,
            'price': price, 'comm': comm, 'total_val': final * price
        })

    # ==========================================================
    # 📑 الجزء الثالث: السجل التفصيلي (مدمج مع تفاصيل الفواتير)
    # ==========================================================
    receipts_qs = Receipt.objects.filter(branch=current_branch, sale_year=selected_year, sale_month=selected_month)
    if selected_salesperson_id: receipts_qs = receipts_qs.filter(salesperson_id=selected_salesperson_id)
    
    actual_revenue = float(receipts_qs.aggregate(s=Sum('total_amount'))['s'] or 0)
    
    actual_coll_comm = float(receipts_qs.filter(is_cash_sale=False).aggregate(
        net=Sum(F('total_amount') - F('down_payment'))
    )['net'] or 0) * 0.10

    expenses_total = float(Expense.objects.filter(branch=current_branch, expense_year=selected_year, expense_month=selected_month).aggregate(s=Sum('amount'))['s'] or 0)

    # المعالجة الذكية للدمج
    raw_items = report_queryset.values(
        'receipt__receipt_number', 'inventory_item__name', 'unit_price', 'receipt__is_cash_sale', 'quantity'
    )
    
    grouped_details = {}
    for row in raw_items:
        key = (row['inventory_item__name'], float(row['unit_price']), row['receipt__is_cash_sale'])
        if key not in grouped_details:
            grouped_details[key] = {
                'name': row['inventory_item__name'],
                'unit_price': float(row['unit_price']),
                'is_cash': row['receipt__is_cash_sale'],
                'total_qty': 0,
                'total_price': 0.0,
                'receipts_info': []
            }
        
        grouped_details[key]['total_qty'] += int(row['quantity'])
        grouped_details[key]['total_price'] += (int(row['quantity']) * float(row['unit_price']))
        grouped_details[key]['receipts_info'].append({
            'receipt_no': row['receipt__receipt_number'],
            'qty': int(row['quantity'])
        })

    final_table_data = list(grouped_details.values())
    final_table_data.sort(key=lambda x: x['total_qty'], reverse=True)

    # تحويل تفاصيل الفواتير لـ JSON
    for r in final_table_data:
        r['receipts_json'] = json.dumps(r['receipts_info'])

    context = {
        'selected_year': selected_year, 'selected_month': selected_month,
        'available_years': available_years, 'available_months': available_months,
        'salespersons': salespersons, 'selected_salesperson_id': int(selected_salesperson_id) if selected_salesperson_id else '',
        
        'cash_sales_list': cash_sales_list, 'installment_sales_list': installment_sales_list,
        'grand_revenue': actual_revenue, 'grand_cost': grand_cost, 'grand_qty': grand_qty,
        'grand_commission': total_sales_comm_fixed + actual_coll_comm,
        'expenses_total': expenses_total, 
        'net_profit_final': actual_revenue - grand_cost - (total_sales_comm_fixed + actual_coll_comm) - expenses_total,
        
        'inventory_report_list': inventory_report_list, 
        'total_inventory_value': total_inventory_value, 'total_adjustments_count': total_adjustments_count,

        'raw_table_data': final_table_data,
    }
    return render(request, 'salesapp/sales_reports.html', context)

@login_required(login_url='login')
@branch_required
@pro_plan_required
def invoices_report(request):
    """سجل تقرير الفواتير (ملخصات في الأعلى وجدول 6 أعمدة في الأسفل)"""
    current_branch = request.branch
    default_year, default_month = get_default_date(current_branch)

    try:
        selected_year = int(request.GET.get('year', default_year))
        selected_month = int(request.GET.get('month', default_month))
    except:
        selected_year, selected_month = default_year, default_month

    selected_salesperson_id = request.GET.get('salesperson', '')
    salespersons = Salesperson.objects.filter(branch=current_branch)

    available_years = sorted(list(set(Receipt.objects.filter(branch=current_branch).values_list('sale_year', flat=True))), reverse=True)
    if not available_years:
        available_years = [default_year]
    available_months = list(range(1, 13))

    # فلترة الفواتير
    receipts_qs = Receipt.objects.filter(branch=current_branch, sale_year=selected_year, sale_month=selected_month)
    if selected_salesperson_id:
        receipts_qs = receipts_qs.filter(salesperson_id=selected_salesperson_id)

    receipts_qs = receipts_qs.order_by('-receipt_number', '-id')

    # حسابات الكروت التلخيصية
    actual_revenue = float(receipts_qs.aggregate(s=Sum('total_amount'))['s'] or 0)
    
    # حساب عمولة التحصيل للفواتير القسط
    actual_coll_comm = float(receipts_qs.filter(is_cash_sale=False).aggregate(
        net=Sum(F('total_amount') - F('down_payment'))
    )['net'] or 0) * 0.10

    expenses_total = float(Expense.objects.filter(branch=current_branch, expense_year=selected_year, expense_month=selected_month).aggregate(s=Sum('amount'))['s'] or 0)

    # حساب التكلفة وعمولة المبيعات الثابتة للأصناف المباعة
    report_queryset = SaleItem.objects.filter(
        receipt__branch=current_branch,
        receipt__sale_year=selected_year,
        receipt__sale_month=selected_month
    )
    if selected_salesperson_id:
        report_queryset = report_queryset.filter(receipt__salesperson_id=selected_salesperson_id)

    grouped_items = report_queryset.values('inventory_item__id').annotate(total_qty=Sum('quantity'))
    item_ids = [item['inventory_item__id'] for item in grouped_items]
    items_dict = {item.id: item for item in InventoryItem.objects.filter(id__in=item_ids)}

    grand_cost = 0.0
    total_sales_comm_fixed = 0.0

    for item in grouped_items:
        inv_item = items_dict.get(item['inventory_item__id'])
        if not inv_item: continue
        qty = int(item['total_qty'] or 0)
        cost_unit = float(inv_item.get_price_at_date(selected_month, selected_year))
        comm_unit = float(inv_item.get_commission_at_date(selected_month, selected_year))
        
        grand_cost += (qty * cost_unit)
        total_sales_comm_fixed += (qty * comm_unit)

    net_profit_final = actual_revenue - grand_cost - (total_sales_comm_fixed + actual_coll_comm) - expenses_total

    context = {
        'selected_year': selected_year, 'selected_month': selected_month,
        'available_years': available_years, 'available_months': available_months,
        'salespersons': salespersons, 'selected_salesperson_id': int(selected_salesperson_id) if selected_salesperson_id else '',
        
        'grand_revenue': actual_revenue, 'grand_cost': grand_cost, 
        'grand_commission': total_sales_comm_fixed + actual_coll_comm,
        'expenses_total': expenses_total, 
        'net_profit_final': net_profit_final,
        
        'receipts_list': receipts_qs,
    }
    return render(request, 'salesapp/invoices_report.html', context)