# salesapp/views/import_views.py
# معالج الاستيراد الذكي (Smart Import Wizard)

import os
import json
import datetime

import pandas as pd
from dateutil import parser
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.db.models import Max

from ..models import Receipt, Salesperson, InstallmentPayment, ClientLicense
from ..utils import to_english_numerals
from .decorators import branch_required


@login_required(login_url='login')
@branch_required
def smart_import_wizard(request):
    current_branch = request.branch

    active_license = ClientLicense.get_active_license()
    if not active_license or not active_license.start_date:
        messages.error(request, "لا يمكن استيراد بيانات قديمة لعدم وجود تاريخ اشتراك محدد.")
        return redirect('dashboard')

    license_start_date = active_license.start_date.replace(day=1)

    MAPPABLE_FIELDS = {
        '': '--- تجاهل هذا العمود ---',
        'customer_name': 'اسم العميل',
        'phone_number': 'رقم الموبايل',
        'address': 'العنوان / جهة العمل',
        'area': 'المنطقة',
        'products_text': 'الأصناف المباعة',
        'total_amount': 'إجمالي الفاتورة',
        'down_payment': 'المقدم المدفوع',
        'salesperson': 'المندوب (البائع)',
        'selling_date': 'تاريخ البيع',
        'sys1_months': 'عدد الشهور (نظام 1)',
        'sys1_amount': 'المبلغ (نظام 1)',
        'sys2_months': 'عدد الشهور (نظام 2)',
        'sys2_amount': 'المبلغ (نظام 2)',
        'sys3_months': 'عدد الشهور (نظام 3)',
        'sys3_amount': 'المبلغ (نظام 3)',
    }

    temp_dir = os.path.join(settings.BASE_DIR, 'salesapp', 'temp_imports')
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, 'uploaded_excel.xlsx')

    context = {
        'page_title': 'استيراد البيانات القديمة',
        'step': 'upload',
        'mappable_fields': MAPPABLE_FIELDS,
    }

    if request.method == 'POST':
        step = request.POST.get('step')

        # -------------------------------------------------------
        # الخطوة 1: رفع الملف واكتشاف الدفاتر
        # -------------------------------------------------------
        if step == 'upload':
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, "يرجى اختيار ملف أولاً.")
                return redirect('smart_import_wizard')

            with open(temp_file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            try:
                xls = pd.ExcelFile(temp_file_path)
                sheet_names = xls.sheet_names
                context['step'] = 'select_sheet'
                context['sheet_names'] = sheet_names
                return render(request, 'salesapp/import_wizard.html', context)
            except Exception as e:
                messages.error(request, f"فشل قراءة الملف: {str(e)}")
                return redirect('smart_import_wizard')

        # -------------------------------------------------------
        # الخطوة 2: اختيار الدفتر والمطابقة
        # -------------------------------------------------------
        elif step == 'select_sheet':
            selected_sheet = request.POST.get('sheet_name')
            try:
                df = pd.read_excel(temp_file_path, sheet_name=selected_sheet)
                df = df.iloc[:, :20].fillna('')

                for col in df.select_dtypes(include=['datetime64', 'datetime']).columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d')

                context['step'] = 'mapping'
                context['sheet_name'] = selected_sheet
                context['columns'] = list(df.columns)
                context['preview_data'] = df.head(20).values.tolist()
                return render(request, 'salesapp/import_wizard.html', context)
            except Exception:
                messages.error(request, "حدث خطأ أثناء قراءة الدفتر المختار.")
                return redirect('smart_import_wizard')

        # -------------------------------------------------------
        # الخطوة 3: غرفة عمليات المناديب
        # -------------------------------------------------------
        elif step == 'mapping':
            selected_sheet = request.POST.get('sheet_name')
            mapping = {}
            salesperson_col_excel = None
            customer_name_col = None

            df = pd.read_excel(temp_file_path, sheet_name=selected_sheet)
            df = df.iloc[:, :20].fillna('')

            for i, col_name in enumerate(df.columns):
                field_selected = request.POST.get(f'map_col_{i}')
                if field_selected:
                    mapping[field_selected] = col_name
                    if field_selected == 'salesperson': salesperson_col_excel = col_name
                    if field_selected == 'customer_name': customer_name_col = col_name

            unique_excel_sps = []
            if salesperson_col_excel and customer_name_col:
                valid_sps = set()
                for index, row in df.iterrows():
                    cname = str(row[customer_name_col]).strip()
                    sp_name = str(row[salesperson_col_excel]).strip()
                    if cname == customer_name_col or not cname:
                        continue
                    if sp_name:
                        valid_sps.add(sp_name)
                unique_excel_sps = list(valid_sps)

            if not unique_excel_sps:
                unique_excel_sps = ["مندوب غير محدد (مفقود في الإكسيل)"]

            current_db_sps = Salesperson.objects.filter(branch=current_branch)

            context['step'] = 'salesperson_room'
            context['sheet_name'] = selected_sheet
            context['mapping_json'] = json.dumps(mapping)
            context['unique_excel_sps'] = unique_excel_sps
            context['current_db_sps'] = current_db_sps
            return render(request, 'salesapp/import_wizard.html', context)

        # -------------------------------------------------------
        # الخطوة 4: الحقن والتسوية المالية
        # -------------------------------------------------------
        elif step == 'process':
            selected_sheet = request.POST.get('sheet_name')
            mapping = json.loads(request.POST.get('mapping_json', '{}'))

            try:
                df = pd.read_excel(temp_file_path, sheet_name=selected_sheet).fillna('')
            except:
                messages.error(request, "الملف المؤقت مفقود، يرجى إعادة الرفع.")
                return redirect('smart_import_wizard')

            # قراءة خريطة المناديب
            sp_resolution_map = {}
            for key in request.POST:
                if key.startswith('sp_original_'):
                    counter = key.replace('sp_original_', '')
                    excel_sp_name = request.POST.get(key).strip()
                    action = request.POST.get(f'sp_action_{counter}')
                    if action == 'link':
                        db_sp_id = request.POST.get(f'sp_link_{counter}')
                        if db_sp_id:
                            sp_resolution_map[excel_sp_name] = Salesperson.objects.get(id=db_sp_id)
                    elif action == 'create':
                        new_name = request.POST.get(f'sp_create_{counter}').strip()
                        if new_name:
                            new_sp, _ = Salesperson.objects.get_or_create(name=new_name, branch=current_branch)
                            sp_resolution_map[excel_sp_name] = new_sp

            success_count, skipped_count, error_count = 0, 0, 0
            error_list = []

            max_receipt = Receipt.objects.filter(branch=current_branch).aggregate(Max('receipt_number'))['receipt_number__max']
            next_receipt_num = (max_receipt or 0) + 1

            def get_val(row, field_name):
                col_name = mapping.get(field_name)
                return str(row[col_name]).strip() if col_name else ''

            def get_num(row, field_name):
                val = get_val(row, field_name)
                try:
                    return int(float(to_english_numerals(val or '0')))
                except:
                    return 0

            with transaction.atomic():
                for index, row in df.iterrows():
                    row_idx = index + 2

                    total_str = get_val(row, 'total_amount')
                    down_str = get_val(row, 'down_payment')
                    products = get_val(row, 'products_text')
                    selling_date_str = get_val(row, 'selling_date')

                    # تخطي الصفوف الفارغة
                    try:
                        if not total_str and not down_str and not products and not selling_date_str and not int(total_str):
                            skipped_count += 1
                            continue
                    except:
                        pass

                    cname = get_val(row, 'customer_name')

                    if cname == mapping.get('customer_name') or cname in ['اسم العميل', 'الاسم', 'Customer']:
                        skipped_count += 1
                        continue

                    if not cname:
                        cname = "عميل غير محدد (مستورد)"

                    phone = get_val(row, 'phone_number')
                    address = get_val(row, 'address')
                    area = get_val(row, 'area')

                    if not selling_date_str:
                        error_list.append({'row': row_idx, 'client': cname, 'reason': "مرفوض: لا يوجد تاريخ بيع."})
                        continue

                    try:
                        clean_date_str = selling_date_str.replace('-', '/').split(' ')[0]
                        parsed_date = parser.parse(clean_date_str).date()
                        sale_year = parsed_date.year
                        sale_month = parsed_date.month

                        temp_start_date = datetime.date(sale_year, sale_month, 1)
                        if temp_start_date >= license_start_date:
                            error_list.append({'row': row_idx, 'client': cname, 'reason': f"مرفوض: تاريخ الفاتورة ({sale_year}/{sale_month}) يتخطى تاريخ اشتراكك."})
                            continue
                    except Exception:
                        error_list.append({'row': row_idx, 'client': cname, 'reason': f"مرفوض: التاريخ ({selling_date_str}) غير مفهوم."})
                        continue

                    salesperson_obj = sp_resolution_map.get(excel_sp_name if (excel_sp_name := get_val(row, 'salesperson')) else '')
                    if not salesperson_obj:
                        error_list.append({'row': row_idx, 'client': cname, 'reason': "لم يتم تحديد مصير المندوب."})
                        continue

                    if phone and not phone.startswith('0') and len(phone) == 10:
                        phone = '0' + phone

                    excel_total_price = get_num(row, 'total_amount')
                    retainer = get_num(row, 'down_payment')

                    m1, a1 = get_num(row, 'sys1_months'), get_num(row, 'sys1_amount')
                    m2, a2 = get_num(row, 'sys2_months'), get_num(row, 'sys2_amount')
                    m3, a3 = get_num(row, 'sys3_months'), get_num(row, 'sys3_amount')

                    is_cash = True if (m1 == 0 and m2 == 0 and m3 == 0) else False
                    total_installments = (m1 * a1) + (m2 * a2) + (m3 * a3)
                    calculated_total_amount = retainer + total_installments

                    if is_cash:
                        final_total_amount = excel_total_price if excel_total_price > 0 else retainer
                    else:
                        final_total_amount = calculated_total_amount

                    inst_sys_parts = []
                    if m1 > 0 and a1 > 0: inst_sys_parts.append(f"{a1}*{m1}")
                    if m2 > 0 and a2 > 0: inst_sys_parts.append(f"{a2}*{m2}")
                    if m3 > 0 and a3 > 0: inst_sys_parts.append(f"{a3}*{m3}")
                    inst_system_text = " + ".join(inst_sys_parts)

                    try:
                        receipt = Receipt.objects.create(
                            receipt_number=next_receipt_num,
                            branch=current_branch,
                            customer_name=cname, phone_number=phone,
                            address=address, area=area,
                            total_amount=final_total_amount,
                            down_payment=retainer,
                            products_text=products or "بدون أصناف",
                            installment_system=inst_system_text,
                            salesperson=salesperson_obj,
                            sale_year=sale_year, sale_month=sale_month,
                            is_cash_sale=is_cash, source='DESKTOP'
                        )
                        next_receipt_num += 1

                        if not is_cash:
                            inst_objs = []
                            current_date = datetime.date(sale_year, sale_month, 15)
                            schedules = [(m1, a1), (m2, a2), (m3, a3)]
                            for months_count, amount in schedules:
                                if months_count > 0 and amount > 0:
                                    for _ in range(months_count):
                                        current_date += relativedelta(months=1)
                                        inst_objs.append(InstallmentPayment(receipt=receipt, payment_date=current_date, amount=amount))
                            InstallmentPayment.objects.bulk_create(inst_objs)

                        success_count += 1
                    except Exception as db_e:
                        error_list.append({'row': row_idx, 'client': cname, 'reason': f"خطأ قواعد بيانات: {str(db_e)}"})
                        error_count += 1

            context['step'] = 'result'
            context['success_count'] = success_count
            context['skipped_count'] = skipped_count
            context['error_count'] = error_count
            context['error_list'] = error_list
            return render(request, 'salesapp/import_wizard.html', context)

    return render(request, 'salesapp/import_wizard.html', context)
