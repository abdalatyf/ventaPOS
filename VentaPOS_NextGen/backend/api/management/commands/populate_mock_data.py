import random
import traceback
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import date
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Max

from api.models import (
    Tenant, Branch, Salesperson, InventoryItem, Receipt, SaleItem, InstallmentPayment,
    Supplier, PurchaseInvoice, PurchaseInvoiceItem, CommissionHistory
)

FIRST_NAMES = ["محمد", "أحمد", "علي", "محمود", "إبراهيم", "حسن", "حسين", "خالد", "يوسف", "عمر", "مصطفى", "كريم", "سيد", "طارق", "عبدالله"]
LAST_NAMES = ["السيد", "عبدالله", "علي", "محمود", "حسن", "خالد", "جمال", "صالح", "سعيد", "منصور", "الشريف", "النجار", "فتحي", "الرفاعي"]
CITIES = ["السنبلاوين", "برقين", "البلامون", "طماي الزهايرة", "ميت غراب", "ديو الوسطى", "شبرا سندي", "نوب طريف", "طوخ الأقلام"]

PRODUCTS = [
    # (اسم المنتج، سعر بيع التقسيط المنطقي)
    ('حافظه ك', 1200), ('حافظه وسط', 800), ('حافظة 2*4', 1600), ('مشاية 1*4', 600), 
    ('مشاية 1*3', 450), ('مشاية 1*2', 300), ('بطانية ك', 2000), ('بطانية اطفال', 1500), 
    ('بطانية مفرد', 1200), ('دفاية ترند', 800), ('دفاية ك', 700), ('دفاية اطفال', 600), 
    ('دفاية 4ق', 1100), ('دفاية 6ق', 1400), ('لحاف ك', 2200), ('لحاف اطفال', 1800), 
    ('كوفرته ك', 900), ('كوفرته اطفال', 800), ('فوط ك 3ق', 400), ('فوط ك 4ق', 500), 
    ('فوط ك 5ق', 600), ('فوط ك 6ق', 700), ('فوط اطفال 3ق', 350), ('فوط اطفال 4ق', 450), 
    ('فوط اطفال 5ق', 550), ('كفر انتريه قطيفة 4ق', 1500), ('كفر انتريه قطيفة 5ق', 1800), 
    ('كفر انتريه جاكار 4ق', 1300), ('كفر انتريه جاكار 5ق', 1600), ('ط اركوبال', 3000), 
    ('ط سيراميك', 4500), ('ط جرانيت', 5500), ('ط الومنيوم', 2500), ('ط ملامين', 1800), 
    ('ط استالس', 4000), ('جريل', 800), ('طقم مقلاية سيراميك', 1200), ('طقم مقلاية جيرانيت', 1500), 
    ('طقم مقلاية الومنيوم', 900), ('كبة', 1200), ('خلاط', 1000), ('هاند بلندر', 800), 
    ('مضرب بيض', 700), ('كاتل', 400), ('مكوة', 900), ('مروحة سقف', 1200), 
    ('مروحة عامود', 1400), ('مروحة حائط', 1100), ('مفرش ك', 2000), ('مفرش اطفال', 1600), 
    ('مكنسة', 3500), ('دفاية 3ق', 850), ('سخان', 4500), ('حافظة 2*3', 1000), 
    ('فرن', 2800), ('ملاية ك', 500), ('ملاية اطفال', 400), ('شفاط', 700), 
    ('حافظه قطيفه', 1300), ('كفر', 600), ('مرتبه', 4000), ('حافظه بابل', 900), 
    ('طقم تيفال', 3000), ('حافظة سينا', 1100), ('بطانية 7', 2500), ('مسطح', 1500), 
    ('طحان اركوبال', 2000), ('ط صواني', 1200), ('قلايه', 2500), ('حله ضغط', 3500), 
    ('ط مصفه', 800), ('مخده', 250), ('حائط', 150), ('عجان', 6000)
]

def round_to_5(number):
    return int(round(number / 5.0) * 5)

def partition_installments(remaining, total_months):
    if remaining <= 0: return [], ""
    
    base_val = remaining // total_months
    base_val = round_to_5(base_val)
    if base_val < 5:
        base_val = 5
        total_months = remaining // 5
        if total_months == 0: total_months = 1; base_val = remaining
    
    if total_months <= 1:
        return [remaining], f"1*{remaining}"
        
    num_systems = random.choices([1, 2, 3], weights=[0.4, 0.5, 0.1])[0]
    
    amounts = []
    if num_systems == 1:
        v = base_val
        amounts = [v] * (total_months - 1)
        last_val = remaining - sum(amounts)
        if last_val <= 0:
            v -= 5
            amounts = [v] * (total_months - 1)
            last_val = remaining - sum(amounts)
        amounts.append(last_val)
        
    elif num_systems == 2:
        m1 = random.randint(1, total_months - 1)
        m2 = total_months - m1
        
        v1 = base_val + random.choice([10, 20, -10, -20])
        v1 = max(5, round_to_5(v1))
        
        rem_2 = remaining - (v1 * m1)
        if rem_2 <= 0: return partition_installments(remaining, total_months)
        
        v2_base = rem_2 // m2
        v2 = max(5, round_to_5(v2_base))
        
        amounts = [v1] * m1 + [v2] * (m2 - 1)
        last_val = remaining - sum(amounts)
        if last_val <= 0: return partition_installments(remaining, total_months)
        amounts.append(last_val)
        
    else: 
        m1 = random.randint(1, total_months - 2)
        m2 = random.randint(1, total_months - m1 - 1)
        m3 = total_months - m1 - m2
        
        v1 = base_val + random.choice([20, 30])
        v1 = max(5, round_to_5(v1))
        
        rem_23 = remaining - (v1 * m1)
        if rem_23 <= 0: return partition_installments(remaining, total_months)
        
        v2 = max(5, round_to_5((rem_23 // (m2 + m3)) + random.choice([10, -10])))
        
        rem_3 = rem_23 - (v2 * m2)
        if rem_3 <= 0: return partition_installments(remaining, total_months)
        
        v3 = max(5, round_to_5(rem_3 // m3))
        
        amounts = [v1] * m1 + [v2] * m2 + [v3] * (m3 - 1)
        last_val = remaining - sum(amounts)
        if last_val <= 0: return partition_installments(remaining, total_months)
        amounts.append(last_val)
        
    systems_str_parts = []
    current_val = amounts[0]
    count = 1
    for i in range(1, len(amounts)):
        if amounts[i] == current_val:
            count += 1
        else:
            systems_str_parts.append(f"{count}*{current_val}")
            current_val = amounts[i]
            count = 1
    systems_str_parts.append(f"{count}*{current_val}")
    
    return amounts, "+".join(systems_str_parts)


class Command(BaseCommand):
    help = 'Populates the VentaPOS_NextGen database with realistic mock data.'

    def get_next_local_id(self, tenant, ModelClass):
        max_id = ModelClass.objects.filter(tenant=tenant).aggregate(Max('local_id'))['local_id__max']
        return 1 if max_id is None else max_id + 1

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("بدء تجهيز قاعدة البيانات..."))

        # 1. Tenant
        tenant, created = Tenant.objects.get_or_create(
            company_code="1234",
            defaults={"name": "Local Dev Company", "is_active": True}
        )

        try:
            with transaction.atomic():
                # Only delete for the DEMO tenant
                InstallmentPayment.objects.filter(receipt__tenant=tenant).delete()
                SaleItem.objects.filter(receipt__tenant=tenant).delete()
                Receipt.objects.filter(tenant=tenant).delete()
                PurchaseInvoiceItem.objects.filter(purchase_invoice__tenant=tenant).delete()
                PurchaseInvoice.objects.filter(tenant=tenant).delete()
                CommissionHistory.objects.filter(inventory_item__tenant=tenant).delete()
                InventoryItem.objects.filter(tenant=tenant).delete()
                Supplier.objects.filter(tenant=tenant).delete()
                Salesperson.objects.filter(tenant=tenant).delete()
                Branch.objects.filter(tenant=tenant).delete()
            self.stdout.write(self.style.SUCCESS("تم مسح البيانات القديمة لشركة DEMO."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطأ أثناء مسح البيانات: {e}"))
            return

        # 2. Branch
        branch = Branch.objects.create(
            tenant=tenant,
            local_id=self.get_next_local_id(tenant, Branch),
            name="السنبلاوين"
        )
        
        # 3. Salespersons
        salesperson_names = ["أحمد السيد", "محمود علي", "يوسف إبراهيم", "طارق حسن"]
        salespersons = []
        for name in salesperson_names:
            sp = Salesperson.objects.create(
                tenant=tenant,
                local_id=self.get_next_local_id(tenant, Salesperson),
                name=name,
                branch=branch
            )
            salespersons.append(sp)
        
        # 4. Suppliers
        suppliers = []
        for s_name in ["مصنع المجد للأدوات", "مؤسسة التوحيد للمفروشات"]:
            s = Supplier.objects.create(
                tenant=tenant,
                name=s_name
            )
            suppliers.append(s)

        # 5. Products & Setup
        inventory_items = []
        product_info_lookup = {}
        for prod_name, sale_price in PRODUCTS:
            purchase_price = round_to_5(sale_price * 0.5)
            commission = round_to_5(min(max(30, sale_price // 30), 120))
            init_qty = random.randint(2, 10) * 5
            
            item = InventoryItem.objects.create(
                tenant=tenant,
                local_id=self.get_next_local_id(tenant, InventoryItem),
                name=prod_name,
                branch=branch,
                initial_quantity=init_qty,
                initial_purchase_price=purchase_price,
                initial_commission_amount=commission,
                initial_month=1,
                initial_year=2025
            )
            CommissionHistory.objects.create(
                tenant=tenant,
                inventory_item=item,
                commission_amount=commission,
                activation_month=1,
                activation_year=2025
            )
            
            inventory_items.append(item)
            product_info_lookup[item.id] = {
                'installment_price': sale_price,
                'cash_price': round_to_5(sale_price * 0.75),
                'purchase_price': purchase_price
            }
            
        self.stdout.write(f"تم إنشاء {len(inventory_items)} منتج.")

        # 6. Generate Sales (18 months ago to now)
        today = date.today()
        start_date = today - relativedelta(months=18)
        current_date = start_date.replace(day=15)
        
        total_receipts_created = 0
        total_purchases_created = 0
        receipt_local_id = self.get_next_local_id(tenant, Receipt)

        while current_date <= today:
            target_year = current_date.year
            target_month = current_date.month
            
            month_sales_total = 0
            target_receipts = random.randint(110, 130)
            
            # --- Replenish Stock ---
            items_to_buy = random.sample(inventory_items, 20)
            for supplier in suppliers:
                inv_num_str = f"{target_year}{target_month:02d}{random.randint(1000,9999)}"
                invoice = PurchaseInvoice.objects.create(
                    tenant=tenant,
                    invoice_number=int(inv_num_str),
                    invoice_type="PURCHASE",
                    supplier=supplier,
                    branch=branch,
                    invoice_month=target_month,
                    invoice_year=target_year
                )
                inv_total = 0
                for item in items_to_buy:
                    if random.random() > 0.5: continue
                    buy_qty = random.randint(5, 20) * 5
                    buy_price = product_info_lookup[item.id]['purchase_price']
                    PurchaseInvoiceItem.objects.create(
                        tenant=tenant,
                        purchase_invoice=invoice,
                        inventory_item=item,
                        quantity=buy_qty,
                        purchase_price=buy_price
                    )
                    inv_total += (buy_qty * buy_price)
                if inv_total > 0:
                    total_purchases_created += 1
                else:
                    invoice.delete()

            # --- Generate Receipts ---
            receipts_this_month = 0
            while receipts_this_month < target_receipts:
                with transaction.atomic():
                    is_cash = random.random() < 0.01 
                    
                    num_items = random.choices([1, 2], weights=[85, 15])[0]
                    selected_items = random.sample(inventory_items, num_items)
                    
                    receipt_total = 0
                    items_info = []
                    
                    for item in selected_items:
                        qty = random.choices([1, 2], weights=[90, 10])[0]
                        sale_price = product_info_lookup[item.id]['cash_price'] if is_cash else product_info_lookup[item.id]['installment_price']
                        items_info.append((item, qty, sale_price))
                        receipt_total += (qty * sale_price)

                    down_payment = 0
                    installment_system_str = "كاش"
                    installment_amounts = []
                    
                    if not is_cash:
                        dp_percent = random.choice([0.1, 0.15, 0.2, 0.25, 0.3])
                        down_payment = round_to_5(receipt_total * dp_percent)
                        down_payment = min(down_payment, receipt_total)
                        remaining = receipt_total - down_payment
                        
                        if remaining > 0:
                            months = 12
                            if remaining > 8000: months = random.randint(12, 15)
                            installment_amounts, installment_system_str = partition_installments(remaining, months)
                        else:
                            installment_system_str = "تم الدفع بالكامل"
                    else:
                        down_payment = receipt_total

                    cust_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if not is_cash else ""
                    cust_phone = f"01{random.randint(0, 2)}{random.randint(10000000, 99999999)}" if not is_cash else ""
                    
                    receipt = Receipt.objects.create(
                        tenant=tenant,
                        receipt_hash=f"hash_{tenant.id}_{receipt_local_id}_{random.randint(1000, 9999)}",
                        local_id=receipt_local_id,
                        receipt_number=receipt_local_id,
                        branch=branch,
                        salesperson=random.choice(salespersons),
                        sale_year=target_year,
                        sale_month=target_month,
                        is_cash_sale=is_cash,
                        customer_name=cust_name,
                        phone_number=cust_phone,
                        address=random.choice(CITIES) if not is_cash else "",
                        total_amount=receipt_total,
                        down_payment=down_payment,
                        installment_system=installment_system_str,
                        created_at_local=timezone.now()
                    )
                    receipt_local_id += 1
                    
                    for item, qty, price in items_info:
                        SaleItem.objects.create(
                            tenant=tenant,
                            receipt=receipt,
                            inventory_item=item,
                            quantity=qty,
                            unit_price=price
                        )
                        
                    if not is_cash and installment_amounts:
                        installs = []
                        start_d = current_date + relativedelta(months=1)
                        for idx, amt in enumerate(installment_amounts):
                            installs.append(InstallmentPayment(
                                tenant=tenant,
                                receipt=receipt,
                                payment_date=start_d + relativedelta(months=idx),
                                amount=amt
                            ))
                        InstallmentPayment.objects.bulk_create(installs)

                    month_sales_total += receipt_total
                    total_receipts_created += 1
                    receipts_this_month += 1
                    
            self.stdout.write(f" - شهر {target_year}/{target_month:02d}: تم إنشاء {receipts_this_month} وصل (الإجمالي {month_sales_total} ج).")
            current_date += relativedelta(months=1)
            
        self.stdout.write(self.style.SUCCESS(f"\nاكتملت العملية! تم إنشاء {total_receipts_created} وصل و {total_purchases_created} فاتورة مشتريات بنجاح."))
