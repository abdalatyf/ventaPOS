# salesapp/views/collections_views.py
import json
import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, F, Q, ExpressionWrapper, IntegerField
from django.template.loader import render_to_string
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from ..models import Branch, Salesperson, Receipt, InstallmentPayment, CompanySetting
from .decorators import branch_required, pro_plan_required
from ..utils import get_available_printers, generate_and_open_pdf

@login_required(login_url='login')
@branch_required
@pro_plan_required
def manage_collections(request):
    current_branch = request.branch
    context = {'current_branch': current_branch, 'all_branches': Branch.objects.all()}

    salespersons = Salesperson.objects.filter(branch=current_branch)

    available_dates = InstallmentPayment.objects.filter(receipt__branch=current_branch).annotate(
        year=F('payment_date__year'), month=F('payment_date__month')
    ).values('year', 'month').distinct()
    available_years = sorted(list(set(d['year'] for d in available_dates if d['year'])), reverse=True)
    available_months = sorted(list(set(d['month'] for d in available_dates if d['month'])))

    now = timezone.now()
    default_year = now.year
    default_month = now.month

    last_receipt = Receipt.objects.filter(branch=current_branch).order_by('-sale_year', '-sale_month').first()

    if last_receipt:
        first_upcoming_payment = InstallmentPayment.objects.filter(receipt=last_receipt).order_by('payment_date').first()
        if first_upcoming_payment:
            default_year = first_upcoming_payment.payment_date.year
            default_month = first_upcoming_payment.payment_date.month
        else:
            try:
                temp_date = datetime.date(last_receipt.sale_year, last_receipt.sale_month, 1)
                next_month_date = temp_date + relativedelta(months=1)
                default_year = next_month_date.year
                default_month = next_month_date.month
            except Exception:
                pass

    timeline = []
    oldest_receipt = Receipt.objects.filter(branch=current_branch).order_by('sale_year', 'sale_month').first()
    newest_receipt = Receipt.objects.filter(branch=current_branch).order_by('-sale_year', '-sale_month').first()

    if oldest_receipt and newest_receipt:
        curr_y, curr_m = oldest_receipt.sale_year, oldest_receipt.sale_month
        end_y, end_m = newest_receipt.sale_year, newest_receipt.sale_month

        while (curr_y < end_y) or (curr_y == end_y and curr_m <= end_m):
            timeline.append({'year': curr_y, 'month': curr_m, 'label': f"{curr_y}/{curr_m}"})
            curr_m += 1
            if curr_m > 12:
                curr_m = 1
                curr_y += 1

    if not timeline:
        timeline.append({'year': default_year, 'month': default_month, 'label': f"{default_year}/{default_month}"})

    selected_year_str = request.GET.get('year') or str(default_year)
    selected_month_str = request.GET.get('month') or str(default_month)
    selected_salesperson_id = request.GET.get('salesperson', '')

    try:
        selected_year = int(selected_year_str)
    except (ValueError, TypeError):
        selected_year = default_year
        selected_year_str = str(default_year)

    try:
        selected_month = int(selected_month_str)
    except (ValueError, TypeError):
        selected_month = default_month
        selected_month_str = str(default_month)

    use_sale_date_filter = request.GET.get('use_sale_date_filter', '')
    sale_from_year = request.GET.get('sale_from_year', '')
    sale_from_month = request.GET.get('sale_from_month', '')
    sale_to_year = request.GET.get('sale_to_year', '')
    sale_to_month = request.GET.get('sale_to_month', '')

    if not sale_from_year or not sale_from_month or not sale_to_year or not sale_to_month:
        base_installments = InstallmentPayment.objects.filter(receipt__branch=current_branch)
        if selected_year: base_installments = base_installments.filter(payment_date__year=selected_year)
        if selected_month: base_installments = base_installments.filter(payment_date__month=selected_month)
        if selected_salesperson_id: base_installments = base_installments.filter(receipt__salesperson_id=selected_salesperson_id)

        ordered_inst = base_installments.order_by('receipt__sale_year', 'receipt__sale_month')
        oldest_inst = ordered_inst.first()
        newest_inst = ordered_inst.last()

        if oldest_inst and newest_inst:
            sale_from_year = str(oldest_inst.receipt.sale_year)
            sale_from_month = str(oldest_inst.receipt.sale_month)
            sale_to_year = str(newest_inst.receipt.sale_year)
            sale_to_month = str(newest_inst.receipt.sale_month)
        else:
            if timeline:
                sale_from_year = str(timeline[0]['year'])
                sale_from_month = str(timeline[0]['month'])
                sale_to_year = str(timeline[-1]['year'])
                sale_to_month = str(timeline[-1]['month'])
            else:
                sale_from_year = sale_to_year = str(default_year)
                sale_from_month = sale_to_month = str(default_month)

    context.update({
        'salespersons': salespersons,
        'available_years': available_years,
        'available_months': available_months,
        'selected_year': selected_year_str,
        'selected_month': selected_month_str,
        'selected_salesperson_id': selected_salesperson_id,
        'timeline_json': json.dumps(timeline),
        'use_sale_date_filter': use_sale_date_filter,
        'sale_from_year': sale_from_year, 'sale_from_month': sale_from_month,
        'sale_to_year': sale_to_year, 'sale_to_month': sale_to_month,
        'search_query': request.GET.get('search_query', ''),
        'receipt_from': request.GET.get('receipt_from', ''),
        'receipt_to': request.GET.get('receipt_to', ''),
    })

    installments = InstallmentPayment.objects.filter(
        receipt__branch=current_branch
    ).select_related('receipt', 'receipt__salesperson')

    search_query = request.GET.get('search_query', '').strip()
    receipt_from = request.GET.get('receipt_from', '')
    receipt_to = request.GET.get('receipt_to', '')

    filters = Q()
    if selected_year: filters &= Q(payment_date__year=selected_year)
    if selected_month: filters &= Q(payment_date__month=selected_month)
    if selected_salesperson_id: filters &= Q(receipt__salesperson_id=selected_salesperson_id)

    if search_query:
        filters &= (
            Q(receipt__customer_name__icontains=search_query) |
            Q(receipt__phone_number__icontains=search_query)
        )
    if receipt_from:
        filters &= Q(receipt__receipt_number__gte=receipt_from)
    if receipt_to:
        filters &= Q(receipt__receipt_number__lte=receipt_to)

    if (sale_from_year and sale_from_month) or (sale_to_year and sale_to_month):
        sale_period_expr = ExpressionWrapper(
            F('receipt__sale_year') * 100 + F('receipt__sale_month'),
            output_field=IntegerField()
        )
        installments = installments.annotate(sale_period=sale_period_expr)

        if sale_from_year and sale_from_month:
            try:
                from_val = int(sale_from_year) * 100 + int(sale_from_month)
                filters &= Q(sale_period__gte=from_val)
            except ValueError:
                pass

        if sale_to_year and sale_to_month:
            try:
                to_val = int(sale_to_year) * 100 + int(sale_to_month)
                filters &= Q(sale_period__lte=to_val)
            except ValueError:
                pass

    installments = installments.filter(filters).order_by('receipt__salesperson__name', 'payment_date')

    action_type = "print" if request.method == "POST" else "view"
    target_printer = request.POST.get('selected_printer')

    # ---> أولاً: كشف الإدارة المجمع (A4)
    if 'print_a4_report' in request.GET:
        try:
            company_settings = CompanySetting.objects.first()
            report_data_by_salesperson = {}
            total_report_amount = 0

            for payment in installments:
                sp_name = payment.receipt.salesperson.name if payment.receipt.salesperson else "بدون مندوب"
                if sp_name not in report_data_by_salesperson:
                    report_data_by_salesperson[sp_name] = {'payments': [], 'sp_total': 0}

                area_str = payment.receipt.area or ""
                addr_str = payment.receipt.address or ""
                full_address = f"{area_str} - {addr_str}".strip(" -")

                report_data_by_salesperson[sp_name]['payments'].append({
                    'receipt_num': payment.receipt.receipt_number,
                    'customer_name': payment.receipt.customer_name or "بدون اسم",
                    'phone': payment.receipt.phone_number or "-",
                    'address': full_address,
                    'sale_date': f"{payment.receipt.sale_month}/{payment.receipt.sale_year}",
                    'due_date': payment.payment_date.strftime("%Y-%m-%d"),
                    'amount': payment.amount,
                })

                report_data_by_salesperson[sp_name]['sp_total'] += payment.amount
                total_report_amount += payment.amount

            context_a4 = {
                'company': company_settings,
                'report_data': report_data_by_salesperson,
                'total_amount': total_report_amount,
                'print_date': timezone.now().strftime("%Y-%m-%d %H:%M"),
                'req_month': selected_month_str,
                'req_year': selected_year_str,
            }

            html_string = render_to_string('salesapp/pdf_a4_collection_report.html', context_a4)

            success, result_msg = generate_and_open_pdf(
                html_string, "Collection_Report_A4", 
                target_printer=target_printer, action=action_type, paper_size="A4"
            )

            if success:
                if action_type == "view":
                    return HttpResponse('<script>history.back();</script>')
                else:
                    return HttpResponse(f'<script>alert("تمت الطباعة"); history.back();</script>')
            else:
                return HttpResponse(f'<script>alert("خطأ: {result_msg}"); history.back();</script>')

        except Exception as e:
            return HttpResponse(f'<script>alert("حدث خطأ فني: {str(e)}"); history.back();</script>')

    # ---> ثانياً: إيصالات العملاء المفلترة (Vouchers)
    elif 'print_vouchers' in request.GET:
        try:
            from collections import defaultdict
            installments_map = defaultdict(list)
            for p in InstallmentPayment.objects.filter(receipt__branch=current_branch).order_by('payment_date'):
                installments_map[p.receipt_id].append(p)

            from .print_views import _generate_installment_vouchers_pdf
            
            success, msg = _generate_installment_vouchers_pdf(
                filtered_installments=installments,
                installments_map=installments_map,
                action_type=action_type, 
                target_printer=target_printer
            )

            if success:
                if action_type == "view":
                    return HttpResponse('<script>history.back();</script>')
                else:
                    return HttpResponse(f'<script>alert("{msg}"); history.back();</script>')
            else:
                return HttpResponse(f'<script>alert("حدث خطأ: {msg}"); history.back();</script>')
                
        except Exception as e:
            return HttpResponse(f'<script>alert("خطأ فني في الإيصالات: {str(e)}"); history.back();</script>')

    # ---> ثالثاً: طباعة إيصال فردي (Single Voucher)
    elif 'print_single_voucher' in request.GET:
        try:
            payment_id = request.GET.get('print_single_voucher')
            target_payment = InstallmentPayment.objects.filter(id=payment_id, receipt__branch=current_branch)
            
            if not target_payment.exists():
                return HttpResponse('<script>alert("القسط غير موجود!"); history.back();</script>')
                
            from collections import defaultdict
            installments_map = defaultdict(list)
            for p in target_payment:
                installments_map[p.receipt_id].append(p)
                
            from .print_views import _generate_installment_vouchers_pdf
            
            success, msg = _generate_installment_vouchers_pdf(
                filtered_installments=target_payment,
                installments_map=installments_map,
                action_type=action_type, 
                target_printer=target_printer
            )

            if success:
                if action_type == "view":
                    return HttpResponse('<script>history.back();</script>')
                else:
                    return HttpResponse(f'<script>alert("تمت الطباعة!"); history.back();</script>')
            else:
                return HttpResponse(f'<script>alert("حدث خطأ: {msg}"); history.back();</script>')
                
        except Exception as e:
            return HttpResponse(f'<script>alert("خطأ فني في الإيصال: {str(e)}"); history.back();</script>')

    installments_by_salesperson = {}
    total_amount_due = 0
    total_installments_count = 0

    for payment in installments:
        sp_name = payment.receipt.salesperson.name if payment.receipt.salesperson else "بدون مندوب"
        if sp_name not in installments_by_salesperson:
            installments_by_salesperson[sp_name] = {'payments': [], 'sp_total': 0}
        installments_by_salesperson[sp_name]['payments'].append(payment)
        installments_by_salesperson[sp_name]['sp_total'] += payment.amount
        total_amount_due += payment.amount
        total_installments_count += 1

    context.update({
        'installments_by_salesperson': installments_by_salesperson,
        'total_amount_due': total_amount_due,
        'total_installments_count': total_installments_count,
        'printers': get_available_printers()
    })

    return render(request, 'salesapp/manage_collections.html', context)