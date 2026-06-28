# salesapp/views/purchase_views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import timezone

from ..models import (
    Supplier, PurchaseInvoice, PurchaseInvoiceItem, InventoryItem, CompanySetting
)
from .decorators import branch_required
from ..utils import get_default_date, is_date_within_subscription, generate_and_open_pdf, get_available_printers

# ==========================================================
# 🏭 1. إدارة الموردين والمصانع
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
    return render(request, 'salesapp/manage_suppliers.html', {'page_title': 'الموردين', 'suppliers': suppliers})

@login_required(login_url='login')
@branch_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    try:
        supplier.delete()
        messages.success(request, "تم حذف المورد بنجاح.")
    except Exception:
        messages.error(request, "لا يمكن الحذف لوجود فواتير مرتبطة به.")
    return redirect('manage_suppliers')


# ==========================================================
# 🛒 2. فواتير الشراء والمرتجعات (والطباعة)
# ==========================================================

@login_required(login_url='login')
@branch_required
def search_purchase_invoices(request):
    current_branch = getattr(request, 'branch', None) 
    invoices = PurchaseInvoice.objects.filter(branch=current_branch).order_by('-id') if current_branch else PurchaseInvoice.objects.all().order_by('-id')
    
    # 🔴 معالجة طلب الطباعة A4 أو الـ PDF
    if 'print_invoice_id' in request.GET:
        invoice_id = request.GET.get('print_invoice_id')
        target_invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
        action_type = "print" if request.method == "POST" else "view"
        target_printer = request.POST.get('selected_printer')

        try:
            company_settings = CompanySetting.objects.first()
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
                    return HttpResponse(f'<script>alert("تم الإرسال للطابعة!"); history.back();</script>')
            else:
                return HttpResponse(f'<script>alert("خطأ: {result_msg}"); history.back();</script>')
        except Exception as e:
            return HttpResponse(f'<script>alert("خطأ برمجي: {str(e)}"); history.back();</script>')

    search_query = request.GET.get('search_query', '').strip()
    supplier_id = request.GET.get('supplier_id', '')
    invoice_type = request.GET.get('invoice_type', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    if search_query: invoices = invoices.filter(invoice_number__icontains=search_query)
    if supplier_id: invoices = invoices.filter(supplier_id=supplier_id)
    if invoice_type: invoices = invoices.filter(invoice_type=invoice_type)
    if month: invoices = invoices.filter(invoice_month=month)
    if year: invoices = invoices.filter(invoice_year=year)

    context = {
        'page_title': 'سجل المشتريات', 'invoices': invoices, 'suppliers': Supplier.objects.all(),
        'current_search': search_query, 'current_supplier': supplier_id, 'current_type': invoice_type,
        'current_month': month, 'current_year': year, 'printers': get_available_printers()
    }
    return render(request, 'salesapp/search_purchase_invoices.html', context)


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
                    raise ValueError("❌ تاريخ الفاتورة خارج الرخصة.")
                if not items_json or items_json == '[]':
                    raise ValueError("لا يمكن حفظ فاتورة فارغة.")

                last_invoice = PurchaseInvoice.objects.order_by('invoice_number').last()
                next_number = (last_invoice.invoice_number + 1) if last_invoice else 1

                invoice = PurchaseInvoice.objects.create(
                    invoice_number=next_number, invoice_type=invoice_type,
                    supplier_id=supplier_id, invoice_month=month, invoice_year=year, branch=request.branch
                )

                for item_data in json.loads(items_json):
                    inv_item = InventoryItem.objects.get(id=item_data['id'])
                    qty = int(item_data['quantity'])
                    price = float(item_data.get('price', 0))

                    if invoice_type == 'RETURN' and qty > inv_item.quantity:
                        raise ValueError(f"⚠️ المتاح للصنف '{inv_item.name}' هو ({inv_item.quantity}) فقط.")
                    
                    PurchaseInvoiceItem.objects.create(
                        invoice=invoice, inventory_item=inv_item, quantity=qty, purchase_price=price
                    )

            messages.success(request, f"✅ تم الحفظ برقم ({next_number}).")
            return redirect('manage_purchase_invoices')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"❌ حدث خطأ غير متوقع: {str(e)}")

    context = {
        'page_title': 'فاتورة جديدة', 'suppliers': Supplier.objects.all(),
        'products': InventoryItem.objects.all(), 'current_month': def_month, 'current_year': def_year,
    }
    return render(request, 'salesapp/manage_purchase_invoices.html', context)


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
                    raise ValueError("❌ التاريخ الجديد يقع خارج الرخصة.")

                old_invoice_type = invoice.invoice_type
                for item in invoice.items.all():
                    inv_item = item.inventory_item
                    if old_invoice_type == 'PURCHASE':
                        if inv_item.quantity < item.quantity:
                            raise ValueError(f"تم بيع جزء من الصنف '{inv_item.name}' لا يمكن تعديله.")
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
                for item_data in json.loads(items_json):
                    inv_item = InventoryItem.objects.get(id=item_data['id'])
                    qty = int(item_data['quantity'])
                    price = float(item_data.get('price', 0))

                    PurchaseInvoiceItem.objects.create(
                        invoice=invoice, inventory_item=inv_item, quantity=qty, purchase_price=price
                    )

                    if new_invoice_type == 'RETURN':
                        if qty > inv_item.quantity:
                            raise ValueError(f"⚠️ المتاح للصنف '{inv_item.name}' ({inv_item.quantity}).")
                        inv_item.quantity -= qty
                    else:
                        inv_item.quantity += qty
                        inv_item.purchase_price = price
                    inv_item.save()

            messages.success(request, f"✏️ تم تعديل الفاتورة ({invoice.invoice_number}).")
            return redirect('search_purchase_invoices')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"❌ حدث خطأ: {str(e)}")

    context = {'page_title': f'تعديل فاتورة', 'invoice': invoice, 'suppliers': Supplier.objects.all(), 'products': InventoryItem.objects.all()}
    return render(request, 'salesapp/edit_purchase_invoice.html', context)


@login_required(login_url='login')
@branch_required
def delete_purchase_invoice(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    try:
        with transaction.atomic():
            items_to_update = []
            for item in invoice.items.all():
                inv_item = item.inventory_item
                if invoice.invoice_type == 'PURCHASE':
                    if inv_item.quantity < item.quantity:
                        raise ValueError(f"⚠️ لا يمكن الحذف! الصنف '{inv_item.name}' تم بيعه.")
                    inv_item.quantity -= item.quantity
                else:
                    inv_item.quantity += item.quantity
                inv_item.save()
                items_to_update.append(inv_item)

            invoice.delete()

            for inv_item in items_to_update:
                latest_purchase = PurchaseInvoiceItem.objects.filter(
                    inventory_item=inv_item, invoice__invoice_type='PURCHASE'
                ).order_by('-invoice__invoice_year', '-invoice__invoice_month', '-id').first()

                inv_item.purchase_price = latest_purchase.purchase_price if latest_purchase else getattr(inv_item, 'initial_purchase_price', 0)
                inv_item.save()

        messages.success(request, f"🗑️ تم حذف الفاتورة وتصحيح المخزون.")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"❌ خطأ غير متوقع: {str(e)}")
    return redirect('search_purchase_invoices')