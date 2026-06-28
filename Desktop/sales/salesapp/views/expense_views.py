# salesapp/views/expense_views.py
# إدارة المصروفات (Expenses)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from ..models import Receipt, Expense
from .decorators import branch_required, pro_plan_required


@branch_required
@pro_plan_required
def manage_expenses(request):
    current_branch = request.branch

    last_receipt = Receipt.objects.filter(branch=current_branch).order_by('-sale_year', '-sale_month').first()
    if last_receipt:
        default_year = last_receipt.sale_year
        default_month = last_receipt.sale_month
    else:
        default_year = timezone.now().year
        default_month = timezone.now().month

    try:
        selected_year = int(request.GET.get('year', default_year))
        selected_month = int(request.GET.get('month', default_month))
    except:
        selected_year, selected_month = default_year, default_month

    if request.method == 'POST':
        description = request.POST.get('description')
        amount = request.POST.get('amount')

        if description and amount:
            Expense.objects.create(
                branch=current_branch,
                description=description,
                amount=amount,
                expense_year=selected_year,
                expense_month=selected_month
            )
            messages.success(request, "تم إضافة المصروف بنجاح.")
            return redirect(f"{reverse('manage_expenses')}?year={selected_year}&month={selected_month}")

    expenses = Expense.objects.filter(
        branch=current_branch,
        expense_year=selected_year,
        expense_month=selected_month
    ).order_by('-id')

    total_expenses = expenses.aggregate(sum=Sum('amount'))['sum'] or 0

    receipt_years = list(set(Receipt.objects.filter(branch=current_branch).values_list('sale_year', flat=True)))
    available_years = sorted(list(set(list(receipt_years) + [timezone.now().year])), reverse=True)
    available_months = list(range(1, 13))

    context = {
        'page_title': 'إدارة المصروفات',
        'expenses': expenses,
        'total_expenses': total_expenses,
        'filter_year': selected_year,
        'filter_month': selected_month,
        'available_years': available_years,
        'available_months': available_months,
    }
    return render(request, 'salesapp/manage_expenses.html', context)


@branch_required
@pro_plan_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, branch=request.branch)
    year = expense.expense_year
    month = expense.expense_month
    expense.delete()
    try:
        messages.success(request, "تم حذف المصروف بنجاح")
    except:
        pass
    return redirect(f"{reverse('manage_expenses')}?year={year}&month={month}")
