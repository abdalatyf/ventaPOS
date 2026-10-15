import random
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import (
    Branch, Salesperson, InventoryItem, Receipt, SaleItem, InstallmentPayment,
    Supplier, PurchaseInvoice, PurchaseInvoiceItem, CommissionHistory, CompanySetting, ClientLicense
)
from django.contrib.auth.models import User
from api.utils.security_utils import generate_receipt_signature

FIRST_NAMES = ["محمد", "أحمد", "علي", "محمود", "إبراهيم", "حسن", "حسين", "خالد", "يوسف", "عمر", "مصطفى", "كريم", "سيد", "طارق", "عبدالله"]
LAST_NAMES = ["السيد", "عبدالله", "علي", "محمود", "حسن", "خالد", "جمال", "صالح", "سعيد", "منصور", "الشريف", "النجار", "فتحي", "الرفاعي"]
CITIES = ["السنبلاوين", "برقين", "البلامون", "طماي الزهايرة", "ميت غراب", "ديو الوسطى", "شبرا سندي", "نوب طريف", "طوخ الأقلام"]

PRODUCTS = [
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
    if base_val < 40:
        base_val = 40
        total_months = remaining // 40
        if total_months == 0: total_months = 1; base_val = remaining
    
    if total_months <= 1:
        return [remaining], f"1*{remaining}"
        
    num_systems = random.choices([1, 2, 3], weights=[0.4, 0.5, 0.1])[0]
    num_systems = min(num_systems, total_months)
    
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
        v1 = max(40, round_to_5(v1))
        
        rem_2 = remaining - (v1 * m1)
        if rem_2 <= 0: return partition_installments(remaining, total_months)
        
        v2_base = rem_2 // m2
        v2 = max(40, round_to_5(v2_base))
        
        amounts = [v1] * m1 + [v2] * (m2 - 1)
        last_val = remaining - sum(amounts)
        if last_val <= 0: return partition_installments(remaining, total_months)
        amounts.append(last_val)
        
    else: 
        m1 = random.randint(1, total_months - 2)
        m2 = random.randint(1, total_months - m1 - 1)
        m3 = total_months - m1 - m2
        
        v1 = base_val + random.choice([20, 30])
        v1 = max(40, round_to_5(v1))
        
        rem_23 = remaining - (v1 * m1)
        if rem_23 <= 0: return partition_installments(remaining, total_months)
        
        v2 = max(40, round_to_5((rem_23 // (m2 + m3)) + random.choice([10, -10])))
        
        rem_3 = rem_23 - (v2 * m2)
        if rem_3 <= 0: return partition_installments(remaining, total_months)
        
        v3 = max(40, round_to_5(rem_3 // m3))
        
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
    help = 'Initialize the database with Rich Demo data if no license exists.'

    def handle(self, *args, **kwargs):
        if ClientLicense.objects.filter(is_active=True).exclude(machine_id="DEMO_MACHINE").exists():
            self.stdout.write(self.style.SUCCESS("System is activated. Skipping demo init."))
            return

        if CompanySetting.objects.exists():
            self.stdout.write(self.style.SUCCESS("Database already contains data. Skipping demo init."))
            return

        self.stdout.write(self.style.WARNING("Starting demo database initialization..."))

        try:
            with transaction.atomic():
                InstallmentPayment.all_objects.all().delete()
                SaleItem.all_objects.all().delete()
                Receipt.all_objects.all().delete()
                PurchaseInvoiceItem.all_objects.all().delete()
                PurchaseInvoice.all_objects.all().delete()
                CommissionHistory.all_objects.all().delete()
                InventoryItem.all_objects.all().delete()
                Supplier.all_objects.all().delete()
                Salesperson.all_objects.all().delete()
                Branch.all_objects.all().delete()
                CompanySetting.all_objects.all().delete()
                ClientLicense.objects.all().delete()

                # Demo Environment Setup
                CompanySetting.objects.create(
                    name="محلات الأمانة للبيع بالتجزئة (نسخة تجريبية)",
                    phone1="01012345678",
                    phone2="01112345678",
                    footer_text="نسخة تجريبية - جميع البيانات وهمية وسيتم حذفها عند تفعيل النظام",
                    is_cloud_viewer=False
                )
                
                # Ensure Master Admin User exists
                if not User.objects.filter(is_superuser=True).exists():
                    User.objects.create_superuser('admin', 'admin@ventapos.local', '')

                
                ClientLicense.objects.create(
                    product_id=7, # Lifetime Pro
                    start_date=timezone.now().date(),
                    expiry_date=None,
                    invoices_balance=999999,
                    is_active=True,
                    machine_id="DEMO_MACHINE",
                    license_code_hash="DEMO_HASH"
                )

                branch = Branch.objects.create(name="الفرع الرئيسي")
                
                salesperson_names = ["أحمد السيد", "محمود علي", "يوسف إبراهيم", "طارق حسن"]
                salespersons = []
                for name in salesperson_names:
                    sp = Salesperson.objects.create(name=name, branch=branch)
                    salespersons.append(sp)

                sp_areas = {}
                shuffled_cities = list(CITIES)
                random.shuffle(shuffled_cities)
                sp_areas[salespersons[0]] = shuffled_cities[0:2]
                sp_areas[salespersons[1]] = shuffled_cities[2:4]
                sp_areas[salespersons[2]] = shuffled_cities[4:6]
                sp_areas[salespersons[3]] = shuffled_cities[6:]

                ADDRESS_LANDMARKS = ["بجوار الجامع الكبير", "شارع المحطة", "أمام المدرسة", "بجوار السنترال", "شارع الجمعية الزراعية"]
                
                class CustomerProfile:
                    def __init__(self, sp, area):
                        self.salesperson = sp
                        self.area = area
                        fname = random.choice(FIRST_NAMES)
                        mname = random.choice(FIRST_NAMES)
                        lname = random.choice(LAST_NAMES)
                        self.short_name = f"{fname} {mname}"
                        self.long_name = f"{fname} {mname} {lname}"
                        self.phone = f"01{random.randint(0, 2)}{random.randint(10000000, 99999999)}"
                        landmark = random.choice(ADDRESS_LANDMARKS)
                        self.short_address = landmark
                        self.long_address = f"شارع {random.choice(FIRST_NAMES)} {landmark}".strip()
                        
                customer_pool = []
                for sp in salespersons:
                    for area in sp_areas[sp]:
                        for _ in range(15):
                            customer_pool.append(CustomerProfile(sp, area))
                
                supplier_names = [
                    "مصنع المجد للأدوات",
                    "مؤسسة التوحيد للمفروشات",
                    "شركة النور للأجهزة المنزلية",
                    "مصنع الأهرام للبلاستيك",
                    "محلات الهدى للجملة",
                    "الشركة الوطنية للإلكترونيات",
                    "مؤسسة السلام التجارية",
                    "مصنع النيل للزجاج",
                    "معارض الصفوة للموبيليا",
                    "شركة الرواد للتجارة"
                ]
                suppliers = []
                for s_name in supplier_names:
                    s = Supplier.objects.create(name=s_name)
                    suppliers.append(s)

                today = date.today()
                start_date = today - relativedelta(months=25)
                current_date = start_date.replace(day=15)
                
                inventory_items = []
                product_info_lookup = {}
                for prod_name, sale_price in PRODUCTS:
                    purchase_price = round_to_5(sale_price * 0.5)
                    commission = round_to_5(min(max(30, sale_price // 30), 120))
                    init_qty = random.randint(1, 4) * 5
                    
                    item = InventoryItem.objects.create(
                        name=prod_name,
                        branch=branch,
                        initial_quantity=init_qty,
                        initial_purchase_price=purchase_price,
                        initial_commission_amount=commission,
                        initial_month=start_date.month,
                        initial_year=start_date.year
                    )
                    CommissionHistory.objects.create(
                        item=item,
                        commission_amount=commission,
                        activation_month=start_date.month,
                        activation_year=start_date.year
                    )
                    
                    inventory_items.append(item)
                    product_info_lookup[item.id] = {
                        'installment_price': sale_price,
                        'cash_price': round_to_5(sale_price * 0.75),
                        'purchase_price': purchase_price
                    }
                    
                self.stdout.write(f"{len(inventory_items)} products created.")

                total_receipts_created = 0
                total_purchases_created = 0

                while current_date <= today:
                    target_year = current_date.year
                    target_month = current_date.month
                    
                    month_sales_total = 0
                    target_receipts = 120# Receipts
                    receipts_this_month = 0
                    monthly_sold_quantities = {}
                    while receipts_this_month < target_receipts:
                        is_cash = random.random() < 0.01 
                        num_items = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
                        selected_items = random.sample(inventory_items, num_items)
                        
                        receipt_total = 0
                        items_info = []
                        
                        for item in selected_items:
                            qty = random.choices([1, 2], weights=[80, 20])[0]
                            sale_price = product_info_lookup[item.id]['cash_price'] if is_cash else product_info_lookup[item.id]['installment_price']
                            items_info.append((item, qty, sale_price))
                            monthly_sold_quantities[item] = monthly_sold_quantities.get(item, 0) + qty
                            receipt_total += (qty * sale_price)

                        down_payment = 0
                        installment_system_str = "كاش"
                        installment_amounts = []
                        
                        if not is_cash:
                            if random.random() < 0.9:
                                down_payment = 0
                            else:
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

                        if not is_cash:
                            customer = random.choice(customer_pool)
                            cust_name = random.choice([customer.short_name, customer.long_name])
                            cust_phone = customer.phone
                            cust_area = customer.area
                            cust_address = random.choice([customer.short_address, customer.long_address])
                            sp_assigned = customer.salesperson
                        else:
                            cust_name = "عميل نقدي"
                            cust_phone = ""
                            cust_area = ""
                            cust_address = ""
                            sp_assigned = random.choice(salespersons)
                            
                        products_text_parts = []
                        for item, qty, price in items_info:
                            products_text_parts.append(f"{item.name}" if qty == 1 else f"{qty} {item.name}")
                            
                        receipt = Receipt.objects.create(
                            receipt_number=total_receipts_created + 1,
                            branch=branch,
                            salesperson=sp_assigned,
                            sale_year=target_year,
                            sale_month=target_month,
                            is_cash_sale=is_cash,
                            customer_name=cust_name,
                            phone_number=cust_phone,
                            address=cust_address,
                            area=cust_area,
                            total_amount=receipt_total,
                            down_payment=down_payment,
                            installment_system=installment_system_str,
                            products_text=" + ".join(products_text_parts)
                        )
                        
                        items_data_for_hash = []
                        for item, qty, price in items_info:
                            SaleItem.objects.create(
                                receipt=receipt,
                                inventory_item=item,
                                quantity=qty,
                                unit_price=price
                            )
                            items_data_for_hash.append({"inventory_item_id": item.id, "quantity": qty})
                            
                        receipt.receipt_hash = generate_receipt_signature(
                            receipt.receipt_number,
                            receipt.total_amount,
                            receipt.sale_month,
                            receipt.sale_year,
                            items_data_for_hash
                        )
                        receipt.save(update_fields=["receipt_hash"])
                            
                        if not is_cash and installment_amounts:
                            installs = []
                            start_d = current_date + relativedelta(months=1)
                            for idx, amt in enumerate(installment_amounts):
                                installs.append(InstallmentPayment(
                                    receipt=receipt,
                                    payment_date=start_d + relativedelta(months=idx),
                                    amount=amt
                                ))
                            InstallmentPayment.objects.bulk_create(installs)

                        month_sales_total += receipt_total
                        total_receipts_created += 1
                        receipts_this_month += 1
                        
                    self.stdout.write(f" - Month {target_year}/{target_month:02d}: {receipts_this_month} receipts created.")
                    # Replenish Stock (Buy == Sell)
                    if monthly_sold_quantities:
                        num_invoices = random.randint(2, 5)
                        items_list = list(monthly_sold_quantities.items())
                        random.shuffle(items_list)
                        
                        chunk_size = max(1, len(items_list) // num_invoices)
                        for i in range(num_invoices):
                            chunk = items_list[i*chunk_size : (i+1)*chunk_size if i < num_invoices - 1 else len(items_list)]
                            if not chunk: continue
                            
                            total_purchases_created += 1
                            supplier = random.choice(suppliers)
                            invoice = PurchaseInvoice.objects.create(
                                invoice_number=total_purchases_created,
                                invoice_type="PURCHASE",
                                supplier=supplier,
                                branch=branch,
                                invoice_month=target_month,
                                invoice_year=target_year
                            )
                            for item, sold_qty in chunk:
                                buy_qty = max(0, round_to_5(sold_qty * random.uniform(0.8, 1.1)))
                                buy_price = product_info_lookup[item.id]['purchase_price']
                                PurchaseInvoiceItem.objects.create(
                                    invoice=invoice,
                                    inventory_item=item,
                                    quantity=buy_qty,
                                    purchase_price=buy_price
                                )
                    current_date += relativedelta(months=1)
                    
            self.stdout.write(self.style.SUCCESS(f"\nProcess completed! Successfully created {total_receipts_created} receipts."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
