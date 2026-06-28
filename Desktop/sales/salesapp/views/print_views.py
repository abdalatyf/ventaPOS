# salesapp/views/print_views.py
import time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string

from ..models import Receipt, InstallmentPayment, CompanySetting
from ..utils import ed2ad, get_num_to_words_ar, generate_and_open_pdf 
from .decorators import branch_required

# =========================================================
# دالة مساعدة: تجهيز سياق الـ PDF
# =========================================================
def _prepare_pdf_context(receipt, installment=None, current_i=1, total_i=1):
    is_cash = receipt.is_cash_sale
    total = int(receipt.total_amount)

    if is_cash:
        amount = receipt.total_amount
        pay_date = f"{receipt.sale_month}/{receipt.sale_year}"
        rem_text = "خالص"
        sys_text = "كاش"
    else:
        amount = installment.amount if installment else 0
        pay_date = installment.payment_date.strftime("25/%m/%Y") if installment else ""
        sys_text = str(receipt.installment_system).replace('*', 'x').replace(" ", "")
        rem_text = "..."
        if str(total)[-1] in ("1", "6"):
            total -= 1
            total = str(total)
        elif str(total)[-1] in ("9", "4"):
            total += 1
            total = str(total)

    # حماية من خطأ السيرفر 500 إذا كان المندوب محذوفاً
    sp_name = receipt.salesperson.name if receipt.salesperson else "بدون مندوب"

    return {
        'receipt_number': ed2ad(str(int(receipt.receipt_number))),
        'current_installment_index': ed2ad(current_i),
        'total_installments_count': ed2ad(total_i),
        'total_amount': ed2ad(total),
        'area': ed2ad(receipt.area),
        'down_payment': ed2ad(receipt.down_payment),
        'customer_name': ed2ad(receipt.customer_name),
        'remaining_amount': rem_text,
        'address': ed2ad(receipt.address),
        'phone_number': ed2ad(receipt.phone_number),
        'amount_to_pay': ed2ad(amount),
        'amount_in_words': get_num_to_words_ar(amount),
        'payment_date': ed2ad(pay_date),
        'products_text': ed2ad(receipt.products_text),
        'sale_date': ed2ad(f"25/{receipt.sale_month}/{receipt.sale_year}"),
        'installment_system': ed2ad(sys_text),
        'salesperson_name': ed2ad(sp_name),
    }


# =========================================================
# دالة طباعة إيصالات التحصيلات المستهدفة
# =========================================================
def _generate_installment_vouchers_pdf(filtered_installments, installments_map, action_type="view", target_printer=None):
    if not filtered_installments:
        return False, "لا توجد أقساط مطابقة للطباعة."

    company_settings = CompanySetting.objects.first()
    content_html_parts = []
    total_count = len(filtered_installments)

    for idx, payment in enumerate(filtered_installments):
        receipt = payment.receipt
        all_payments = list(installments_map.get(receipt.id, []))
        total_installments = len(all_payments)

        try:
            current_index = all_payments.index(payment) + 1
        except ValueError:
            current_index = 1

        paid_so_far = receipt.down_payment
        for sub_p in all_payments[:current_index]:
            paid_so_far += sub_p.amount

        remaining_val = receipt.total_amount - paid_so_far
        remaining_text = ed2ad(remaining_val) if remaining_val > 0 else "خالص"

        ctx = _prepare_pdf_context(receipt, payment, current_index, total_installments)
        ctx['remaining_amount'] = remaining_text
        ctx['company_settings'] = company_settings

        part_html = render_to_string('salesapp/pdf_invoice_content.html', ctx)
        content_html_parts.append(part_html)
        content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')

    if action_type == "view":
        full_content_body = "".join(content_html_parts)
        final_html = render_to_string('salesapp/pdf_base.html', {'content': full_content_body})
        success, msg = generate_and_open_pdf(final_html, "Collections_Vouchers", action="view", paper_size="DL")
        return success, msg
    else:
# ==========================================
    # 🔴 الحالة الثانية: الطباعة المباشرة (نظام الدفعات 50)
    # ==========================================
        BATCH_SIZE = 50
        actual_batch_size = BATCH_SIZE * 2
        total_parts = len(content_html_parts)
        batches_sent = 0

        for i in range(0, total_parts, actual_batch_size):
            chunk = content_html_parts[i:i + actual_batch_size]
            full_content_body = "".join(chunk)
            final_html = render_to_string('salesapp/pdf_base.html', {'content': full_content_body})

            batch_number = batches_sent + 1
            success, msg = generate_and_open_pdf(
                final_html,
                f"Batch_Collections_Vouchers_Part_{batch_number}",
                target_printer=target_printer,
                action="print",
                paper_size="DL"
            )
            
            # 🔴 التعديل هنا: إذا نجح نزيد العداد، وإذا فشل نوقف العملية ونظهر الخطأ
            if success:
                batches_sent += 1
            else:
                return False, f"توقفت الطباعة عند الدفعة {batch_number} بسبب: {msg}"
            
            # استراحة 3 ثوانٍ بين كل دفعة ودفعة لراحة الطابعة
            if i + actual_batch_size < total_parts:
                time.sleep(3)

        return True, f"تم إرسال {batches_sent} دفعات للطابعة بنجاح."


# =========================================================
# دالة فلترة الوصلات الأساسية
# =========================================================
def _get_filtered_receipts(request):
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

    return receipts


# =========================================================
# طباعة أو عرض وصل واحد (من جدول البحث)
# =========================================================
@login_required(login_url='login')
@branch_required
def print_single_receipt_view(request, receipt_id):
    try:
        receipt = Receipt.objects.prefetch_related('payments').get(pk=receipt_id, branch=request.branch)
    except Receipt.DoesNotExist:
        return redirect('search_receipts')

    action_type = "print" if request.method == "POST" else "view"
    target_printer = request.POST.get('selected_printer')
    company_settings = CompanySetting.objects.first()
    content_html_parts = []

    installments_from_db = list(receipt.payments.all().order_by('payment_date'))
    total_installments = len(installments_from_db)
    paid_so_far = receipt.down_payment

    if receipt.is_cash_sale:
        ctx = _prepare_pdf_context(receipt)
        ctx['company_settings'] = company_settings
        part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
        content_html_parts.append(part)
    else:
        if not installments_from_db:
            return HttpResponse('<script>alert("خطأ: هذا الوصل التقسيط لا يحتوي على أقساط مجدولة."); history.back();</script>')

        for i, inst in enumerate(installments_from_db):
            total = int(receipt.total_amount)
            if str(total)[-1] in ("1", "6"): total -= 1
            elif str(total)[-1] in ("9", "4"): total += 1

            paid_so_far += inst.amount
            rem = total - paid_so_far
            rem_text = ed2ad(rem) if rem > 0 else "خالص"

            ctx = _prepare_pdf_context(receipt, inst, i + 1, total_installments)
            ctx['remaining_amount'] = rem_text
            ctx['company_settings'] = company_settings

            part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
            content_html_parts.append(part)
            if i < total_installments - 1:
                content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')

    full_content_body = "".join(content_html_parts)
    final_html = render_to_string('salesapp/pdf_base.html', {'content': full_content_body})

    success, result_msg = generate_and_open_pdf(
        final_html, f"Receipt_{receipt.receipt_number}", 
        target_printer=target_printer, action=action_type, paper_size="DL"
    )

    if success:
        if action_type == "view":
            return HttpResponse('<script>history.back();</script>')
        else:
            return HttpResponse(f'<script>alert("تمت الطباعة بنجاح"); history.back();</script>')
    else:
        return HttpResponse(f'<script>alert("خطأ: {result_msg}"); history.back();</script>')


# =========================================================
# طباعة أو عرض القائمة المجمعة (Batch Print) لصفحة البحث
# =========================================================
from django.http import JsonResponse

@login_required(login_url='login')
@branch_required
def print_batch_receipts_view(request):
    receipts_list = _get_filtered_receipts(request).prefetch_related('payments')
    total_receipts_count = receipts_list.count()

    if total_receipts_count == 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'لا توجد وصلات للطباعة.'})
        return HttpResponse('<script>alert("لا توجد وصلات للطباعة."); history.back();</script>')

    company_settings = CompanySetting.objects.first()

    # ==========================================
    # 1. حالة الطباعة الصامتة المجمعة (AJAX POST)
    # ==========================================
    if request.method == "POST":
        target_printer = request.POST.get('selected_printer')
        
        try:
            # نستقبل من الجافاسكريبت نقطة البداية وحجم الدفعة
            offset = int(request.POST.get('offset', 0))
            limit = int(request.POST.get('limit', 5)) # نقسم كل 10 وصلات في دفعة لحماية الطابعة
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'بيانات الدفعة غير صحيحة.'})

        # قطع الجزء المطلوب فقط من الداتا بيز (Slicing)
        receipts_chunk = receipts_list[offset:offset+limit]
        content_html_parts = []
        chunk_length = len(receipts_chunk)

        for receipt_counter, receipt in enumerate(receipts_chunk):
            installments_from_db = list(receipt.payments.all().order_by('payment_date'))
            total_inst = len(installments_from_db)
            paid_so_far = receipt.down_payment

            if receipt.is_cash_sale:
                ctx = _prepare_pdf_context(receipt)
                ctx['remaining_amount'] = "خالص"
                ctx['company_settings'] = company_settings
                part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
                content_html_parts.append(part)
                
                # فاصل الصفحات
                if receipt_counter < chunk_length - 1:
                    content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')
            else:
                if not installments_from_db: continue

                for i, inst in enumerate(installments_from_db):
                    total = int(receipt.total_amount)
                    if str(total)[-1] in ("1", "6"): total -= 1
                    elif str(total)[-1] in ("9", "4"): total += 1

                    paid_so_far += inst.amount
                    rem = total - paid_so_far
                    rem_text = ed2ad(rem) if rem > 0 else "خالص"

                    ctx = _prepare_pdf_context(receipt, inst, i + 1, total_inst)
                    ctx['remaining_amount'] = rem_text
                    ctx['company_settings'] = company_settings

                    part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
                    content_html_parts.append(part)

                    is_last_installment = (i == total_inst - 1)
                    is_last_receipt = (receipt_counter == chunk_length - 1)
                    if not is_last_installment or (is_last_installment and not is_last_receipt):
                        content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')

        if not content_html_parts:
            return JsonResponse({'status': 'success', 'message': 'لا توجد صفحات في هذه الدفعة.'})

        full_content_body = "".join(content_html_parts)
        final_html = render_to_string('salesapp/pdf_base.html', {'content': full_content_body})

        batch_number = (offset // limit) + 1
        success, result_msg = generate_and_open_pdf(
            final_html, f"Batch_Receipts_Part_{batch_number}", 
            target_printer=target_printer, action="print", paper_size="DL"
        )

        if success:
            return JsonResponse({'status': 'success', 'message': f'تمت طباعة الدفعة {batch_number}'})
        else:
            return JsonResponse({'status': 'error', 'message': result_msg})

    # ==========================================
    # 2. حالة معاينة PDF لجميع الملفات (GET)
    # ==========================================
    else:
        content_html_parts = []
        total_receipts_count = receipts_list.count()
        receipt_counter = 0

        for receipt in receipts_list:
            receipt_counter += 1
            installments_from_db = list(receipt.payments.all().order_by('payment_date'))
            total_inst = len(installments_from_db)
            paid_so_far = receipt.down_payment

            if receipt.is_cash_sale:
                ctx = _prepare_pdf_context(receipt)
                ctx['remaining_amount'] = "خالص"
                ctx['company_settings'] = company_settings
                part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
                content_html_parts.append(part)
                if receipt_counter < total_receipts_count:
                    content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')
            else:
                if not installments_from_db: continue

                for i, inst in enumerate(installments_from_db):
                    total = int(receipt.total_amount)
                    if str(total)[-1] in ("1", "6"): total -= 1
                    elif str(total)[-1] in ("9", "4"): total += 1

                    paid_so_far += inst.amount
                    rem = total - paid_so_far
                    rem_text = ed2ad(rem) if rem > 0 else "خالص"

                    ctx = _prepare_pdf_context(receipt, inst, i + 1, total_inst)
                    ctx['remaining_amount'] = rem_text
                    ctx['company_settings'] = company_settings

                    part = render_to_string('salesapp/pdf_invoice_content.html', ctx)
                    content_html_parts.append(part)

                    is_last_installment = (i == total_inst - 1)
                    is_last_receipt = (receipt_counter == total_receipts_count)
                    if not is_last_installment or (is_last_installment and not is_last_receipt):
                        content_html_parts.append('<div style="page-break-after: always; display: block; clear: both; height: 1px;"></div>')

        if not content_html_parts:
            return HttpResponse('<script>alert("لا توجد صفحات للطباعة."); history.back();</script>')

        full_content_body = "".join(content_html_parts)
        final_html = render_to_string('salesapp/pdf_base.html', {'content': full_content_body})
        generate_and_open_pdf(final_html, "Batch_Receipts_Preview", action="view", paper_size="DL")
        return HttpResponse('<script>history.back();</script>')