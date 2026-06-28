import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Sum, F, Q, Case, When, Value, CharField, IntegerField, FloatField, ExpressionWrapper, Prefetch
from django.db.models import ProtectedError
from django.views.decorators.http import require_POST

from ..models import (
    Branch, Salesperson, InventoryItem,
    CommissionHistory, Supplier, PurchaseInvoice, 
    PurchaseInvoiceItem, InventoryAdjustment, SaleItem
)
from .decorators import branch_required, pro_plan_required
from ..utils import get_default_date, is_date_within_subscription

# =======================================
# الفروع (Branches)
# =======================================

@login_required(login_url='login')
def manage_branches(request):
    error_message = None
    if request.method == 'POST':
        branch_name = request.POST.get('branch_name')
        if branch_name:
            try:
                Branch.objects.create(name=branch_name)
                return redirect('manage_branches')
            except IntegrityError:
                error_message = f"خطأ: الاسم '{branch_name}' موجود مسبقاً."
    branches = Branch.objects.all()
    return render(request, 'salesapp/manage_branches.html', {'branches': branches, 'error_message': error_message})


@login_required(login_url='login')
@require_POST
def edit_branch(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    new_name = request.POST.get('branch_name')
    if new_name:
        try:
            branch.name = new_name
            branch.save()
            messages.success(request, f"تم تعديل اسم الفرع إلى '{new_name}' بنجاح.")
        except IntegrityError:
            messages.error(request, f"خطأ: الاسم '{new_name}' موجود مسبقاً.")
    return redirect('manage_branches')


@login_required(login_url='login')
def delete_branch(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    try:
        branch.delete()
        if str(request.session.get('selected_branch_id')) == str(pk):
            request.session.pop('selected_branch_id', None)
            request.session.pop('selected_branch_name', None)
            messages.info(request, "تم حذف الفرع الحالي، يرجى اختيار فرع آخر.")
            return redirect('select_branch')
        messages.success(request, "تم حذف الفرع بنجاح.")
        return redirect('manage_branches')
    except ProtectedError:
        messages.error(request, "خطأ: لا يمكن حذف هذا الفرع لأنه يحتوي على بيانات (موظفين/فواتير).")
        return redirect('manage_branches')


# =======================================
# المناديب (Salespersons)
# =======================================

@login_required(login_url='login')
@branch_required
def manage_salespersons(request):
    current_branch = request.branch
    error_message = None
    if request.method == 'POST':
        person_name = request.POST.get('person_name')
        cloud_username = request.POST.get('cloud_username')
        cloud_password = request.POST.get('cloud_password')
        if person_name:
            try:
                Salesperson.objects.create(
                    name=person_name, branch=current_branch,
                    cloud_username=cloud_username, cloud_password=cloud_password
                )
                return redirect('manage_salespersons')
            except IntegrityError:
                error_message = f"خطأ: الاسم '{person_name}' موجود مسبقاً."
    all_salespersons = Salesperson.objects.filter(branch=current_branch)
    return render(request, 'salesapp/manage_salespersons.html', {'salespersons': all_salespersons, 'error_message': error_message})


@login_required(login_url='login')
@branch_required
@require_POST
def edit_salesperson(request, pk):
    person = get_object_or_404(Salesperson, pk=pk, branch=request.branch)
    new_name = request.POST.get('person_name')
    cloud_username = request.POST.get('cloud_username')
    cloud_password = request.POST.get('cloud_password')
    if new_name:
        try:
            person.name = new_name
            person.cloud_username = cloud_username
            person.cloud_password = cloud_password
            person.save()
            messages.success(request, f"تم تعديل المندوب إلى '{new_name}' بنجاح.")
        except IntegrityError:
            messages.error(request, f"خطأ: الاسم '{new_name}' موجود مسبقاً.")
    return redirect('manage_salespersons')


@login_required(login_url='login')
@branch_required
def delete_salesperson(request, pk):
    person = get_object_or_404(Salesperson, pk=pk, branch=request.branch)
    try:
        person.delete()
        messages.success(request, "تم حذف الموظف بنجاح.")
        return redirect('manage_salespersons')
    except ProtectedError:
        messages.error(request, "خطأ: لا يمكن حذف هذا الموظف لوجود فواتير أو حركات مرتبطة به.")
        return redirect('manage_salespersons')


# =======================================
# الأصناف (Products)
# =======================================

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
        initial_quantity = request.POST.get('initial_quantity', 0)
        initial_purchase_price = request.POST.get('initial_purchase_price', 0)
        initial_commission = request.POST.get('initial_commission', 0)
        start_month = request.POST.get('start_month')
        start_year = request.POST.get('start_year')

        try:
            qty = int(initial_quantity) if initial_quantity else 0
            price = float(initial_purchase_price) if initial_purchase_price else 0.0
            comm = float(initial_commission) if initial_commission else 0.0
            s_month = int(start_month) if start_month else def_month
            s_year = int(start_year) if start_year else def_year
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
                        messages.success(request, f"✅ تم تعريف الصنف '{product_name}' برصيد افتتاحي بنجاح.")
                    except IntegrityError:
                        error_message = f"❌ خطأ: اسم الصنف '{product_name}' موجود مسبقاً."

        if not error_message:
            return redirect('manage_products')

    # 🟢 التشخيص الذاتي (Self-Healing) للمنتجات القديمة
    all_items_for_healing = InventoryItem.objects.filter(branch=current_branch)
    for item in all_items_for_healing:
        if not CommissionHistory.objects.filter(item=item).exists():
            CommissionHistory.objects.create(
                item=item,
                activation_month=item.initial_month or def_month,
                activation_year=item.initial_year or def_year,
                commission_amount=item.initial_commission_amount or 0
            )

    # 🟢 الحل السحري لعرض البيانات في الجدول: استخدام 'commission_records'
    history_prefetch = Prefetch('commission_records', queryset=CommissionHistory.objects.order_by('-activation_year', '-activation_month'))
    all_products = InventoryItem.objects.filter(branch=current_branch).prefetch_related(history_prefetch)
    
    total_inventory_value = 0.0
    for product in all_products:
        product.initial_total_cost = (product.initial_quantity or 0) * (product.initial_purchase_price or 0)
        total_inventory_value += product.initial_total_cost

    context = {
        'products': all_products, 'total_inventory_value': total_inventory_value,
        'page_title': 'تعريف الأصناف (أرصدة أول المدة)', 'error_message': error_message,
        'current_month': def_month, 'current_year': def_year,
    }
    return render(request, 'salesapp/manage_products.html', context)


@login_required(login_url='login')
@branch_required
@pro_plan_required
def edit_product(request, pk):
    """دالة احتياطية لتجنب خطأ ImportError في الـ urls.py"""
    product = get_object_or_404(InventoryItem, pk=pk, branch=request.branch)

    if request.method == 'POST':
        try:
            product.name = request.POST.get('name').strip()
            product.save()
            messages.success(request, f"تم تعديل الصنف {product.name} بنجاح.")
        except IntegrityError:
            messages.error(request, "خطأ: اسم الصنف موجود مسبقاً في هذا الفرع.")
        except ValueError:
            messages.error(request, "خطأ: يرجى إدخال أرقام صحيحة في خانات الكمية والسعر.")

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
        return redirect('manage_products')
    except ProtectedError:
        messages.error(request, "خطأ: لا يمكن حذف هذا الصنف لوجود عمليات مرتبطة به.")
        return redirect('manage_products')


# ==========================================================
# 💸 إدارة المندبات (لآلة الزمن)
# ==========================================================

@login_required(login_url='login')
@branch_required
@pro_plan_required
@require_POST
def update_commission(request):
    """تحديث مندبة الصنف بتاريخ جديد (لآلة الزمن) مع الحفاظ على الجدول الرئيسي ثابت"""
    item_id = request.POST.get('item_id')
    try:
        new_comm = float(request.POST.get('new_commission', 0))
        apply_month = int(request.POST.get('apply_month'))
        apply_year = int(request.POST.get('apply_year'))
    except ValueError:
        messages.error(request, "❌ بيانات غير صحيحة، يرجى كتابة أرقام فقط.")
        return redirect('manage_products')

    if not is_date_within_subscription(apply_year, apply_month):
        messages.error(request, "❌ خطأ: تاريخ تطبيق المندبة يقع خارج فترة الرخصة الفعالة.")
        return redirect('manage_products')

    try:
        item = InventoryItem.objects.get(id=item_id, branch=request.branch)
        
        commission_record, created = CommissionHistory.objects.update_or_create(
            item=item,
            activation_month=apply_month,
            activation_year=apply_year,
            defaults={'commission_amount': new_comm}
        )

        if created:
            messages.success(request, f"✅ تم تسجيل مندبة جديدة ({new_comm}) للصنف '{item.name}' بتاريخ {apply_month}/{apply_year}.")
        else:
            messages.success(request, f"✏️ تم تعديل مندبة الصنف '{item.name}' لتاريخ {apply_month}/{apply_year} لتصبح ({new_comm}).")

    except InventoryItem.DoesNotExist:
        messages.error(request, "❌ الصنف غير موجود.")
        
    return redirect('manage_products')


@login_required(login_url='login')
@branch_required
@pro_plan_required
@require_POST
def edit_commission_record(request, record_id):
    """تعديل سجل مندبة موجود من لوحة التحكم"""
    record = get_object_or_404(CommissionHistory, id=record_id, item__branch=request.branch)

    try:
        new_comm = float(request.POST.get('commission_amount', 0))
        new_month = int(request.POST.get('activation_month'))
        new_year = int(request.POST.get('activation_year'))
    except ValueError:
        messages.error(request, "❌ بيانات غير صحيحة.")
        return redirect('manage_products')

    if not is_date_within_subscription(new_year, new_month):
        messages.error(request, "❌ خطأ: التاريخ الجديد يقع خارج فترة الرخصة الفعالة.")
        return redirect('manage_products')

    record.commission_amount = new_comm
    record.activation_month = new_month
    record.activation_year = new_year
    record.save()
    
    messages.success(request, f"✏️ تم تعديل المندبة للمنتج '{record.item.name}' لتاريخ {new_month}/{new_year}.")
    return redirect('manage_products')


@login_required(login_url='login')
@branch_required
@pro_plan_required
def delete_commission_record(request, record_id):
    """حذف سجل مندبة"""
    record = get_object_or_404(CommissionHistory, id=record_id, item__branch=request.branch)
    
    if CommissionHistory.objects.filter(item=record.item).count() <= 1:
        messages.error(request, "❌ لا يمكن حذف هذا السجل لأنه السجل الوحيد للمندبة الخاص بهذا الصنف.")
        return redirect('manage_products')

    record.delete()
    messages.success(request, "🗑️ تم حذف سجل المندبة بنجاح.")
    return redirect('manage_products')


# =======================================
# حركات المخزون القديمة
# =======================================
@login_required(login_url='login')
@branch_required
@pro_plan_required
def manage_inventory_movements(request):
    current_branch = request.branch

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        qty_str = request.POST.get('quantity', '0').strip()
        movement_type = request.POST.get('movement_type')

        try:
            quantity = int(qty_str) if qty_str else 0
            if product_id and quantity > 0:
                product = get_object_or_404(InventoryItem, pk=product_id, branch=current_branch)

                if movement_type == 'add':
                    StockTransaction.objects.create(
                        item=product,
                        transaction_type='PURCHASE',
                        quantity=quantity
                    )
                    messages.success(request, f"تمت إضافة {quantity} وحدة لـ {product.name} بنجاح.")

                elif movement_type == 'return':
                    if product.quantity >= quantity:
                        StockTransaction.objects.create(
                            item=product,
                            transaction_type='RETURN_TO_FACTORY',
                            quantity=quantity
                        )
                        messages.success(request, f"تم إرجاع {quantity} وحدة من {product.name} بنجاح.")
                    else:
                        messages.error(request, "خطأ: الكمية المتاحة في المخزن غير كافية للإرجاع.")
        except ValueError:
            messages.error(request, "خطأ: يرجى إدخال كمية صحيحة.")

    products = InventoryItem.objects.filter(branch=current_branch)
    context = {'page_title': 'حركات المخزون', 'products': products}
    return render(request, 'salesapp/manage_inventory_movements.html', context)


# ==========================================================
# 🏭 إدارة الموردين والمصانع
# ==========================================================

@login_required(login_url='login')
@branch_required
def manage_suppliers(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name', '').strip()
        
        if supplier_name:
            if Supplier.objects.filter(name=supplier_name).exists():
                messages.error(request, "اسم المورد مسجل بالفعل!")
            else:
                Supplier.objects.create(name=supplier_name)
                messages.success(request, "تمت إضافة المورد بنجاح.")
        else:
            messages.error(request, "يرجى كتابة اسم المورد.")
            
        return redirect('manage_suppliers')

    suppliers = Supplier.objects.all().order_by('-id')
    context = {'page_title': 'إدارة الموردين', 'suppliers': suppliers}
    return render(request, 'salesapp/manage_suppliers.html', context)


@login_required(login_url='login')
@branch_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    try:
        supplier.delete()
        messages.success(request, "تم حذف المورد بنجاح.")
    except Exception as e:
        messages.error(request, "لا يمكن حذف هذا المورد لأنه مرتبط بفواتير شراء مسجلة في النظام.")
        
    return redirect('manage_suppliers')


# ==========================================================
# 🔍 4. سجل فواتير الشراء والمرتجعات (البحث والأرشيف)
# ==========================================================

# ضيف الاستدعاءات دي فوق في بداية الملف لو مش موجودة
from django.template.loader import render_to_string
from django.http import HttpResponse
from ..models import CompanySetting
from ..utils import generate_and_open_pdf, get_available_printers

@login_required(login_url='login')
@branch_required
def search_purchase_invoices(request):
    # 🟢 1. استدعاءات محمية ومخفية داخل الدالة عشان مستحيل تضرب منك أي إيرور (ImportError)
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from django.utils import timezone
    from ..models import CompanySetting, Supplier, PurchaseInvoice
    from ..utils import generate_and_open_pdf, get_available_printers

    # 🟢 2. اعتراض أمر الطباعة والتعامل مع الـ PDF قبل كود البحث
    if 'print_invoice_id' in request.GET:
        invoice_id = request.GET.get('print_invoice_id')
        target_invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
        
        # تحديد السلوك: لو المودال بعت POST تبقى طباعة صامتة، لو GET يبقى عرض
        action_type = "print" if request.method == "POST" else "view"
        target_printer = request.POST.get('selected_printer')

        try:
            company_settings = CompanySetting.objects.first()
            # تحويل العناصر لـ List عشان نقدر نضيف حقل الإجمالي الوهمي (line_total) ويظهر في الـ PDF
            items_list = list(target_invoice.items.all())
            total_invoice_amount = 0
            
            for item in items_list:
                item.line_total = item.quantity * (item.purchase_price or 0)
                total_invoice_amount += item.line_total

            context_a4 = {
                'company': company_settings,
                'invoice': target_invoice,
                'items': items_list,
                'total_invoice_amount': total_invoice_amount,
                'print_date': timezone.now().strftime("%Y-%m-%d %H:%M"),
            }

            html_string = render_to_string('salesapp/pdf_a4_purchase_invoice.html', context_a4)

            success, result_msg = generate_and_open_pdf(
                html_string, f"Invoice_{target_invoice.invoice_number}", 
                target_printer=target_printer, action=action_type, paper_size="A4"
            )

            if success:
                if action_type == "view":
                    return HttpResponse('<script>history.back();</script>')
                else:
                    return HttpResponse(f'<script>alert("✅ تم إرسال الفاتورة بنجاح للطابعة!"); history.back();</script>')
            else:
                # لو أداة SumatraPDF فيها مشكلة هيطلعلك الـ Alert ده
                return HttpResponse(f'<script>alert("❌ حدث خطأ أثناء إخراج الـ PDF: {result_msg}"); history.back();</script>')

        except Exception as e:
            # لو نسيت تنشئ ملف الـ HTML بتاع الفاتورة هيطلعلك إيرور هنا بدل ما يسكت!
            return HttpResponse(f'<script>alert("❌ خطأ برمجي أثناء تحضير الطباعة: {str(e)}"); history.back();</script>')

    # 🟢 3. كود البحث الطبيعي للفواتير
    current_branch = getattr(request, 'branch', None) 
    
    if current_branch:
        invoices = PurchaseInvoice.objects.filter(branch=current_branch).order_by('-id')
    else:
        invoices = PurchaseInvoice.objects.all().order_by('-id')
    
    search_query = request.GET.get('search_query', '').strip()
    supplier_id = request.GET.get('supplier_id', '')
    invoice_type = request.GET.get('invoice_type', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    if search_query:
        invoices = invoices.filter(invoice_number__icontains=search_query)
    if supplier_id:
        invoices = invoices.filter(supplier_id=supplier_id)
    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)
    if month:
        invoices = invoices.filter(invoice_month=month)
    if year:
        invoices = invoices.filter(invoice_year=year)

    suppliers = Supplier.objects.all()

    context = {
        'page_title': 'سجل فواتير المشتريات',
        'invoices': invoices,
        'suppliers': suppliers,
        'current_search': search_query,
        'current_supplier': supplier_id,
        'current_type': invoice_type,
        'current_month': month,
        'current_year': year,
        'printers': get_available_printers() # 🟢 مهمة جداً لظهور قائمة الطابعات جوه المودال
    }
    return render(request, 'salesapp/search_purchase_invoices.html', context)
# ==========================================================
# 🛒 1. إضافة فاتورة جديدة (شراء / مرتجع)
# ==========================================================

@login_required(login_url='login')
@branch_required
def manage_purchase_invoices(request):
    def_year, def_month = get_default_date(request.branch)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                invoice_type = request.POST.get('invoice_type')
                supplier_id = request.POST.get('supplier_id')
                month = int(request.POST.get('invoice_month'))
                year = int(request.POST.get('invoice_year'))
                items_json = request.POST.get('invoice_items_json')

                if not is_date_within_subscription(year, month):
                    raise ValueError("❌ خطأ: تاريخ الفاتورة يقع خارج فترة الرخصة الفعالة.")

                if not items_json or items_json == '[]':
                    raise ValueError("لا يمكن حفظ فاتورة فارغة.")

                last_invoice = PurchaseInvoice.objects.order_by('invoice_number').last()
                next_number = (last_invoice.invoice_number + 1) if last_invoice else 1

                invoice = PurchaseInvoice.objects.create(
                    invoice_number=next_number,
                    invoice_type=invoice_type,
                    supplier_id=supplier_id,
                    invoice_month=month,
                    invoice_year=year,
                    branch=request.branch
                )

                new_items = json.loads(items_json)
                for item_data in new_items:
                    inv_item = InventoryItem.objects.get(id=item_data['id'])
                    qty = int(item_data['quantity'])
                    price = float(item_data.get('price', 0))

                    if invoice_type == 'RETURN':
                        if qty > inv_item.quantity:
                            raise ValueError(f"⚠️ لا يمكن عمل مرتجع بـ ({qty}) للصنف '{inv_item.name}'! الرصيد المتاح بالمخزن حالياً هو ({inv_item.quantity}) فقط.")
                    
                    # 🔴 تم مسح commission_amount تماماً من هنا
                    PurchaseInvoiceItem.objects.create(
                        invoice=invoice,
                        inventory_item=inv_item,
                        quantity=qty,
                        purchase_price=price
                    )

            messages.success(request, f"✅ تم حفظ الفاتورة رقم ({next_number}) بنجاح وتحديث المخزن.")
            return redirect('manage_purchase_invoices')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"❌ حدث خطأ غير متوقع: {str(e)}")

    suppliers = Supplier.objects.all()
    products = InventoryItem.objects.all()

    context = {
        'page_title': 'فاتورة مشتريات جديدة',
        'suppliers': suppliers,
        'products': products,
        'current_month': def_month,
        'current_year': def_year,
    }
    return render(request, 'salesapp/manage_purchase_invoices.html', context)
# ==========================================================
# ✏️ 2. تعديل فاتورة (نظام اللوحة النظيفة - Clean Slate)
# ==========================================================

@login_required(login_url='login')
@branch_required
def edit_purchase_invoice(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                new_invoice_type = request.POST.get('invoice_type')
                new_month = int(request.POST.get('invoice_month'))
                new_year = int(request.POST.get('invoice_year'))

                if not is_date_within_subscription(new_year, new_month):
                    raise ValueError("❌ خطأ: التاريخ الجديد للفاتورة يقع خارج فترة الرخصة الفعالة.")

                old_invoice_type = invoice.invoice_type
                for item in invoice.items.all():
                    inv_item = item.inventory_item
                    if old_invoice_type == 'PURCHASE':
                        if inv_item.quantity < item.quantity:
                            raise ValueError(f"لا يمكن تعديل الفاتورة! تم بيع جزء من الصنف '{inv_item.name}' والرصيد الحالي لا يكفي لخصم الكمية القديمة.")
                        inv_item.quantity -= item.quantity
                    else:
                        inv_item.quantity += item.quantity
                    inv_item.save()
                
                invoice.items.all().delete()

                invoice.invoice_type = new_invoice_type
                invoice.supplier_id = request.POST.get('supplier_id')
                invoice.invoice_month = new_month
                invoice.invoice_year = new_year
                invoice.save()

                items_json = request.POST.get('invoice_items_json')
                if not items_json or items_json == '[]':
                    raise ValueError("لا يمكن حفظ فاتورة فارغة.")

                new_items = json.loads(items_json)
                for item_data in new_items:
                    inv_item = InventoryItem.objects.get(id=item_data['id'])
                    qty = int(item_data['quantity'])
                    price = float(item_data.get('price', 0))

                    # 🔴 تم مسح commission_amount تماماً من هنا
                    PurchaseInvoiceItem.objects.create(
                        invoice=invoice,
                        inventory_item=inv_item,
                        quantity=qty,
                        purchase_price=price
                    )

                    if new_invoice_type == 'RETURN':
                        if qty > inv_item.quantity:
                            raise ValueError(f"⚠️ لا يمكن عمل مرتجع بـ ({qty}) للصنف '{inv_item.name}'! الرصيد المتاح هو ({inv_item.quantity}).")
                        inv_item.quantity -= qty
                    else:
                        inv_item.quantity += qty
                        inv_item.purchase_price = price
                    
                    inv_item.save()

            messages.success(request, f"✏️ تم تعديل الفاتورة رقم ({invoice.invoice_number}) وتحديث المخزن بنجاح.")
            return redirect('search_purchase_invoices')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"❌ حدث خطأ غير متوقع: {str(e)}")

    suppliers = Supplier.objects.all()
    products = InventoryItem.objects.all()
    
    context = {
        'page_title': f'تعديل فاتورة رقم: {invoice.invoice_number}',
        'invoice': invoice,
        'suppliers': suppliers,
        'products': products,
    }
    return render(request, 'salesapp/edit_purchase_invoice.html', context)
# ==========================================================
# 🗑️ 3. الحذف العكسي للفاتورة
# ==========================================================

@login_required(login_url='login')
@branch_required
def delete_purchase_invoice(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    invoice_number = invoice.invoice_number

    try:
        with transaction.atomic():
            items_to_update = []
            
            for item in invoice.items.all():
                inventory_item = item.inventory_item
                
                if invoice.invoice_type == 'PURCHASE':
                    if inventory_item.quantity < item.quantity:
                        raise ValueError(f"⚠️ لا يمكن حذف الفاتورة! الصنف '{inventory_item.name}' تم بيع جزء منه، والرصيد الحالي لا يكفي لخصمه.")
                    inventory_item.quantity -= item.quantity
                elif invoice.invoice_type == 'RETURN':
                    inventory_item.quantity += item.quantity
                
                inventory_item.save()
                items_to_update.append(inventory_item)

            invoice.delete()

            for inventory_item in items_to_update:
                latest_purchase = PurchaseInvoiceItem.objects.filter(
                    inventory_item=inventory_item,
                    invoice__invoice_type='PURCHASE'
                ).order_by('-invoice__invoice_year', '-invoice__invoice_month', '-id').first()

                if latest_purchase:
                    inventory_item.purchase_price = latest_purchase.purchase_price
                else:
                    inventory_item.purchase_price = getattr(inventory_item, 'initial_purchase_price', 0)
                
                inventory_item.save()

        messages.success(request, f"🗑️ تم حذف الفاتورة رقم ({invoice_number}) وتصحيح المخزون والأسعار تلقائياً.")

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"❌ حدث خطأ غير متوقع أثناء الحذف: {str(e)}")

    return redirect('search_purchase_invoices')


# ==========================================================
# التسويات الجردية
# ==========================================================

@login_required(login_url='login')
@branch_required
@require_POST
def add_adjustment(request):
    item_id = request.POST.get('item_id')
    month = int(request.POST.get('month'))
    year = int(request.POST.get('year'))
    adjustment_type = request.POST.get('adjustment_type')
    quantity = request.POST.get('quantity')
    reason = request.POST.get('reason', '')

    if not is_date_within_subscription(year, month):
        messages.error(request, "❌ خطأ: تاريخ التسوية يقع خارج فترة الرخصة الفعالة.")
        return redirect(f"/reports/sales/?month={month}&year={year}")

    try:
        item = InventoryItem.objects.get(id=item_id, branch=request.branch)
        qty = int(quantity)

        if qty > 0:
            InventoryAdjustment.objects.create(
                item=item,
                adjustment_type=adjustment_type,
                quantity=qty,
                reason=reason,
                month=month,
                year=year
            )
            messages.success(request, f"تم تسجيل التسوية بنجاح للمنتج: {item.name}")
        else:
            messages.error(request, "الكمية يجب أن تكون أكبر من الصفر.")
            
    except InventoryItem.DoesNotExist:
        messages.error(request, "الصنف غير موجود.")
    except ValueError:
        messages.error(request, "بيانات غير صحيحة.")

    return redirect(f"/reports/sales/?month={month}&year={year}")


# ==========================================================
# دفتر كارت الصنف (Ledger)
# ==========================================================

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
    grand_totals = {
        'cash_profit': 0.0, 'inst_profit': 0.0, 'adj_profit': 0.0, 'net_profit': 0.0,
        'cash_qty': 0, 'inst_qty': 0
    }

    temp_y, temp_m = start_y, start_m
    while (temp_y < end_y) or (temp_y == end_y and temp_m <= end_m):
        prev_m, prev_y = (12, temp_y - 1) if temp_m == 1 else (temp_m - 1, temp_y)
        
        opening = product.get_stock_at_date(prev_m, prev_y)
        if temp_y == product.initial_year and temp_m == product.initial_month:
            opening += product.initial_quantity

        closing = product.get_stock_at_date(temp_m, temp_y)
        cost_unit = float(product.get_price_at_date(temp_m, temp_y))
        comm_unit = float(product.get_commission_at_date(temp_m, temp_y))

        purchases = PurchaseInvoiceItem.objects.filter(inventory_item=product, invoice__invoice_month=temp_m, invoice__invoice_year=temp_y, invoice__invoice_type='PURCHASE').aggregate(s=Sum('quantity'))['s'] or 0
        returns = PurchaseInvoiceItem.objects.filter(inventory_item=product, invoice__invoice_month=temp_m, invoice__invoice_year=temp_y, invoice__invoice_type='RETURN').aggregate(s=Sum('quantity'))['s'] or 0
        net_purchases = purchases - returns

        adjs = InventoryAdjustment.objects.filter(item=product, month=temp_m, year=temp_y)
        surplus = adjs.filter(adjustment_type__in=['SURPLUS', 'ADD']).aggregate(s=Sum('quantity'))['s'] or 0
        deficit = adjs.filter(adjustment_type__in=['DEFICIT', 'SUBTRACT']).aggregate(s=Sum('quantity'))['s'] or 0
        
        cash_sales = SaleItem.objects.filter(inventory_item=product, receipt__sale_year=temp_y, receipt__sale_month=temp_m, receipt__is_cash_sale=True).aggregate(
            qty=Sum('quantity'), rev=Sum(F('quantity') * F('unit_price'), output_field=FloatField())
        )
        c_qty = cash_sales['qty'] or 0
        c_rev = cash_sales['rev'] or 0.0
        c_avg_sell = (c_rev / c_qty) if c_qty > 0 else 0.0
        c_cost = c_qty * cost_unit
        c_profit = c_rev - c_cost

        inst_sales = SaleItem.objects.filter(inventory_item=product, receipt__sale_year=temp_y, receipt__sale_month=temp_m, receipt__is_cash_sale=False).annotate(
            coll_comm=ExpressionWrapper(((F('quantity') * F('unit_price')) * (F('receipt__total_amount') - F('receipt__down_payment')) * 0.10) / F('receipt__total_amount'), output_field=FloatField())
        ).aggregate(
            qty=Sum('quantity'), rev=Sum(F('quantity') * F('unit_price'), output_field=FloatField()), coll=Sum('coll_comm', output_field=FloatField())
        )
        i_qty = inst_sales['qty'] or 0
        i_rev = inst_sales['rev'] or 0.0
        i_avg_sell = (i_rev / i_qty) if i_qty > 0 else 0.0
        i_cost = i_qty * cost_unit
        i_sales_comm = i_qty * comm_unit
        i_coll_comm = inst_sales['coll'] or 0.0
        i_profit = i_rev - i_cost - i_sales_comm - i_coll_comm
        
        c_profit_unit = (c_profit / c_qty) if c_qty > 0 else 0.0
        i_coll_comm_unit = (i_coll_comm / i_qty) if i_qty > 0 else 0.0
        i_profit_unit = (i_profit / i_qty) if i_qty > 0 else 0.0
        total_val = closing * cost_unit 

        adj_profit = (surplus * cost_unit) - (deficit * cost_unit)
        month_net_profit = c_profit + i_profit + adj_profit

        total_sales_qty = c_qty + i_qty

        if opening > 0 or net_purchases > 0 or total_sales_qty > 0 or surplus > 0 or deficit > 0 or closing > 0:
            monthly_summary.append({
                'year': temp_y, 'month': temp_m,
                'opening': opening, 'purchases': net_purchases, 'sales': total_sales_qty,
                'surplus': surplus, 'deficit': deficit, 'closing': closing, 'cost_unit': cost_unit,
                'total_val': total_val, 
                'cash': {
                    'qty': c_qty, 'avg_sell': c_avg_sell, 'rev': c_rev, 
                    'cost': c_cost, 'profit': c_profit, 
                    'profit_unit': c_profit_unit 
                },
                'inst': {
                    'qty': i_qty, 'avg_sell': i_avg_sell, 'rev': i_rev, 
                    'cost': i_cost, 'sales_comm_unit': comm_unit, 
                    'sales_comm': i_sales_comm, 'coll_comm': i_coll_comm, 'profit': i_profit,
                    'coll_comm_unit': i_coll_comm_unit, 
                    'profit_unit': i_profit_unit 
                },
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

    all_movements = []
    all_movements.append({
        'year': start_y, 'month': start_m, 'id': 0, 'label': 'رصيد مرحل (بداية الفترة)', 'type': 'INITIAL',
        'in_qty': brought_forward_qty, 'out_qty': 0, 'ref': '-', 'person': 'النظام'
    })

    sales_qs = SaleItem.objects.filter(inventory_item=product)
    purchases_qs = PurchaseInvoiceItem.objects.filter(inventory_item=product)
    adjs_qs = InventoryAdjustment.objects.filter(item=product)

    for s in sales_qs.values('id', 'receipt__sale_year', 'receipt__sale_month', 'quantity', 'unit_price', 'receipt__receipt_number', 'receipt__customer_name'):
        y, m = s['receipt__sale_year'], s['receipt__sale_month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            all_movements.append({'year': y, 'month': m, 'id': s['id'], 'label': 'فاتورة بيع', 'type': 'OUT', 'in_qty': 0, 'out_qty': s['quantity'], 'ref': s['receipt__receipt_number'], 'person': s['receipt__customer_name']})

    for p in purchases_qs.values('id', 'invoice__invoice_year', 'invoice__invoice_month', 'quantity', 'invoice__invoice_type', 'invoice__invoice_number', 'invoice__supplier__name'):
        y, m = p['invoice__invoice_year'], p['invoice__invoice_month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            is_in = p['invoice__invoice_type'] == 'PURCHASE'
            label = 'شراء' if is_in else 'مرتجع مصنع'
            all_movements.append({'year': y, 'month': m, 'id': p['id'], 'label': label, 'type': 'IN' if is_in else 'OUT', 'in_qty': p['quantity'] if is_in else 0, 'out_qty': 0 if is_in else p['quantity'], 'ref': p['invoice__invoice_number'], 'person': p['invoice__supplier__name']})

    for a in adjs_qs.values('id', 'year', 'month', 'quantity', 'adjustment_type', 'reason'):
        y, m = a['year'], a['month']
        if (y > start_y or (y == start_y and m >= start_m)) and (y < end_y or (y == end_y and m <= end_m)):
            is_add = a['adjustment_type'] in ['ADD', 'SURPLUS']
            label = 'تسوية (زيادة)' if is_add else 'تسوية (عجز)'
            all_movements.append({'year': y, 'month': m, 'id': a['id'], 'label': label, 'type': 'IN' if is_add else 'OUT', 'in_qty': a['quantity'] if is_add else 0, 'out_qty': 0 if is_add else a['quantity'], 'ref': '-', 'person': a['reason']})

    all_movements.sort(key=lambda x: (x['year'], x['month'], x['id']))

    running_balance = 0
    for mov in all_movements:
        running_balance += (mov['in_qty'] - mov['out_qty'])
        mov['balance'] = running_balance

    context = {
        'product': product,
        'detailed_movements': reversed(all_movements),
        'monthly_summary': monthly_summary,
        'grand_totals': grand_totals,
        'start_m': start_m, 'start_y': start_y, 'end_m': end_m, 'end_y': end_y,
        'available_months': available_months, 'available_years': available_years,
        'page_title': f'كارت صنف: {product.name}'
    }
    return render(request, 'salesapp/product_ledger.html', context)