# salesapp/views/branch_views.py
# اختيار الفرع ولوحة التحكم (Branch Selection & Dashboard)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, DecimalField, FloatField
from django.db.models.functions import Coalesce
from django.db.models import Value
from django.utils import timezone

from ..models import (
    Branch, Salesperson, Receipt, SaleItem,
    InstallmentPayment, InventoryItem, Expense, ClientLicense
)
from .decorators import branch_required


@login_required(login_url='login')
def select_branch(request):
    request.session.pop('selected_branch_id', None)
    request.session.pop('selected_branch_name', None)
    branches = Branch.objects.all()
    return render(request, 'salesapp/select_branch.html', {'branches': branches})


@login_required(login_url='login')
def set_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    request.session['selected_branch_id'] = str(branch.id)
    request.session['selected_branch_name'] = branch.name
    return redirect('add_receipt')


@login_required(login_url='login')
@branch_required
def dashboard(request):
    current_branch = request.branch

    # 1. تحديد النطاق الزمني بناءً على أقدم ترخيص نشط
    oldest_license = ClientLicense.objects.filter(is_active=True).order_by('start_date').first()

    if oldest_license and oldest_license.start_date:
        license_start_year = oldest_license.start_date.year
        license_start_month = oldest_license.start_date.month
    else:
        now = timezone.now()
        license_start_year = now.year
        license_start_month = now.month

    # 2. تحديد أحدث سنة مسجلة في الفواتير
    last_receipt = Receipt.objects.filter(branch=current_branch).order_by('-sale_year', '-sale_month').first()

    if last_receipt:
        end_year = last_receipt.sale_year
        default_year = last_receipt.sale_year
        default_month = last_receipt.sale_month
    else:
        end_year = license_start_year
        default_year = license_start_year
        default_month = license_start_month

    if end_year < license_start_year:
        end_year = license_start_year

    all_years = list(range(end_year, license_start_year - 1, -1))
    months_range = range(1, 13)

    # 3. استقبال طلبات المستخدم
    try:
        selected_year = int(request.GET.get('year', default_year))
        selected_month = int(request.GET.get('month', default_month))
    except ValueError:
        selected_year, selected_month = default_year, default_month

    if selected_year < license_start_year or (selected_year == license_start_year and selected_month < license_start_month):
        messages.warning(request, "⚠️ هذه الفترة تسبق تاريخ اشتراكك.")
        selected_year, selected_month = license_start_year, license_start_month

    # 4. QuerySets الأساسية
    monthly_sales_qs = Receipt.objects.filter(
        branch=current_branch, sale_year=selected_year, sale_month=selected_month
    )
    monthly_items_qs = SaleItem.objects.filter(receipt__in=monthly_sales_qs)
    monthly_expenses_val = Expense.objects.filter(
        branch=current_branch, expense_year=selected_year, expense_month=selected_month
    ).aggregate(s=Sum('amount'))['s'] or 0

    # 5. السيولة
    cash_sales_inflow = monthly_sales_qs.filter(is_cash_sale=True).aggregate(s=Sum('total_amount'))['s'] or 0
    down_payment_inflow = monthly_sales_qs.filter(is_cash_sale=False).aggregate(s=Sum('down_payment'))['s'] or 0
    collection_inflow = InstallmentPayment.objects.filter(
        receipt__branch=current_branch,
        payment_date__year=selected_year,
        payment_date__month=selected_month,
    ).aggregate(s=Sum('amount'))['s'] or 0

    total_cash_inflow = float(cash_sales_inflow) + float(down_payment_inflow) + float(collection_inflow)

    # === جلب الأصناف لتسريع الحسابات ===
    all_items = InventoryItem.objects.filter(branch=current_branch)
    items_dict = {item.id: item for item in all_items}

    # 6. معالجة المناديب
    salespersons_stats = []
    grand_total_cash = grand_total_credit = grand_total_sales = 0
    grand_total_collected = grand_total_comm_sales = grand_total_comm_coll = grand_total_due = 0
    total_auto_salaries = 0

    net_cash_in_hand = 0
    total_revenue_paper = 0
    total_cogs = total_sales_comm_fixed = 0.0
    reserve_deduction = 0
    estimated_net_profit = 0

    current_inventory_value = 0.0
    low_stock_count = 0
    inv_count = 0
    avg_basket = 0
    top_products = []
    top_areas = []

    for sp in Salesperson.objects.filter(branch=current_branch):
        sp_sales_qs = monthly_sales_qs.filter(salesperson=sp)
        sp_cash = sp_sales_qs.filter(is_cash_sale=True).aggregate(s=Sum('total_amount'))['s'] or 0
        sp_credit = sp_sales_qs.filter(is_cash_sale=False).aggregate(s=Sum('total_amount'))['s'] or 0
        sp_total_sales_val = float(sp_cash) + float(sp_credit)

        # حساب المندبة
        sp_items = SaleItem.objects.filter(receipt__salesperson=sp, receipt__in=monthly_sales_qs)
        comm_from_sales = 0.0
        for item in sp_items.values('inventory_item_id').annotate(qty=Sum('quantity')):
            inv_item = items_dict.get(item['inventory_item_id'])
            if inv_item:
                comm_unit = float(inv_item.get_commission_at_date(selected_month, selected_year))
                comm_from_sales += (item['qty'] * comm_unit)

        sp_collected = InstallmentPayment.objects.filter(
            receipt__branch=current_branch, receipt__salesperson=sp,
            payment_date__year=selected_year, payment_date__month=selected_month
        ).aggregate(s=Sum('amount'))['s'] or 0

        comm_from_collection = float(sp_collected) * 0.10
        sp_total_due = float(comm_from_sales) + comm_from_collection
        total_auto_salaries += sp_total_due

        if sp_total_sales_val > 0 or sp_collected > 0:
            salespersons_stats.append({
                'receipts_count': sp_sales_qs.count(),
                'name': sp.name, 'cash_sales': sp_cash, 'credit_sales': sp_credit,
                'total_sales_val': sp_total_sales_val, 'collected': sp_collected,
                'comm_sales': comm_from_sales, 'comm_coll': comm_from_collection,
                'due_salary': sp_total_due
            })
            grand_total_cash += float(sp_cash)
            grand_total_credit += float(sp_credit)
            grand_total_sales += sp_total_sales_val
            grand_total_collected += float(sp_collected)
            grand_total_comm_sales += comm_from_sales
            grand_total_comm_coll += comm_from_collection
            grand_total_due += sp_total_due

    # 7. حسابات السيولة والربح
    net_cash_in_hand = total_cash_inflow - (float(monthly_expenses_val) + total_auto_salaries)
    total_revenue_paper = float(monthly_sales_qs.aggregate(s=Sum('total_amount'))['s'] or 0)

    # حساب التكلفة (بالنظام التاريخي)
    for item in monthly_items_qs.values('inventory_item_id').annotate(qty=Sum('quantity')):
        inv_item = items_dict.get(item['inventory_item_id'])
        if inv_item:
            qty = item['qty'] or 0
            cost_unit = float(inv_item.get_price_at_date(selected_month, selected_year))
            comm_unit = float(inv_item.get_commission_at_date(selected_month, selected_year))
            total_cogs += (qty * cost_unit)
            total_sales_comm_fixed += (qty * comm_unit)

    # جلب إجمالي القسط وإجمالي المقدمات المدفوعة فيه
    credit_sales_data = monthly_sales_qs.filter(is_cash_sale=False).aggregate(
        total=Sum('total_amount'), 
        down=Sum('down_payment')
    )
    credit_revenue_paper = float(credit_sales_data['total'] or 0)
    credit_down_payments = float(credit_sales_data['down'] or 0)
    
    # نسبة التحصيل 10% تُحسب على "المتبقي" فقط (الإجمالي - المقدم)
    reserve_deduction = (credit_revenue_paper - credit_down_payments) * 0.10
    
    estimated_net_profit = total_revenue_paper - (total_cogs + total_sales_comm_fixed + reserve_deduction + float(monthly_expenses_val))

    # 8. المخزن (KPIs) بالنظام الجديد
    now = timezone.now()
    for inv_item in all_items:
        c_stock = inv_item.get_stock_at_date(now.month, now.year)
        c_price = float(inv_item.get_price_at_date(now.month, now.year))
        current_inventory_value += (c_stock * c_price)
        if c_stock <= 3: low_stock_count += 1

    inv_count = monthly_sales_qs.count()
    avg_basket = (float(total_revenue_paper) / inv_count) if inv_count > 0 else 0

    top_products = monthly_items_qs.values('inventory_item__name').annotate(qty=Sum('quantity')).order_by('-qty')[:5]
    top_areas = monthly_sales_qs.values('area').annotate(val=Sum('total_amount'), count=Count('id')).exclude(area='').order_by('-val')[:5]

    context = {
        'current_branch': current_branch,
        'selected_year': selected_year, 'selected_month': selected_month,
        'all_years': all_years, 'months_range': months_range,
        'inv_count': inv_count, 'net_cash_in_hand': net_cash_in_hand,
        'estimated_net_profit': estimated_net_profit, 'current_inventory_value': current_inventory_value,
        'low_stock_count': low_stock_count, 'avg_basket': avg_basket,
        'cash_sales_inflow': cash_sales_inflow, 'down_payment_inflow': down_payment_inflow,
        'collection_inflow': collection_inflow, 'monthly_expenses_val': monthly_expenses_val,
        'total_auto_salaries': total_auto_salaries, 'total_cash_inflow': total_cash_inflow,
        'total_revenue_paper': total_revenue_paper, 'total_cogs': total_cogs,
        'total_sales_comm_fixed': total_sales_comm_fixed, 'reserve_deduction': reserve_deduction,
        'salespersons_stats': salespersons_stats, 'grand_total_cash': grand_total_cash,
        'grand_total_credit': grand_total_credit, 'grand_total_sales': grand_total_sales,
        'grand_total_collected': grand_total_collected, 'grand_total_comm_sales': grand_total_comm_sales,
        'grand_total_comm_coll': grand_total_comm_coll, 'grand_total_due': grand_total_due,
        'top_products': top_products, 'top_areas': top_areas,
        'chart_cash_val': float(cash_sales_inflow),
        'chart_credit_val': float(total_revenue_paper) - float(cash_sales_inflow),
    }

    return render(request, 'salesapp/dashboard.html', context)