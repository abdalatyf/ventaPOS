import os
import django
import random
from datetime import date
from dateutil.relativedelta import relativedelta

# 1. تهيئة بيئة جانجو (تأكد أن 'sales.settings' هو اسم مشروعك)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings') 
django.setup()

from django.db import transaction
from salesapp.models import (
    Branch, Salesperson, InventoryItem, Supplier, PurchaseInvoice, 
    PurchaseInvoiceItem, Receipt, SaleItem, InstallmentPayment, 
    Expense, CommissionHistory, InventoryAdjustment
)

# =======================================================
# دوال مساعدة للتوليد العشوائي والتقريب
# =======================================================
def round_to_5(num):
    return 5 * round(num / 5)

def generate_arabic_name():
    first = ["محمد", "أحمد", "محمود", "مصطفى", "علي", "كريم", "عمر", "حسين", "طارق", "ياسين"]
    second = ["السيد", "عبدالله", "إبراهيم", "حسن", "عادل", "فاروق", "توفيق", "سامي", "سعد", "منصور"]
    third = ["النجار", "الحداد", "المصري", "الهواري", "سالم", "عثمان", "رضوان", "الشناوي", "علام", "جاد"]
    return f"{random.choice(first)} {random.choice(second)} {random.choice(third)}"

def generate_phone():
    prefixes = ["010", "011", "012", "015"]
    return f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"

def generate_area():
    areas = ["الدقي", "المهندسين", "مدينة نصر", "الهرم", "المعادي", "التجمع الخامس", "فيصل", "شبرا", "حلوان", "زايد"]
    return random.choice(areas)

def calculate_installments_system(total_remaining, months=12):
    if total_remaining <= 0:
        return [], ""
    avg_inst = total_remaining / months
    base_inst = round_to_5(avg_inst)
    if base_inst == 0: base_inst = 5
    amounts = [base_inst] * (months - 1)
    last_inst = total_remaining - sum(amounts)
    amounts.append(last_inst)
    counts = {}
    for a in amounts:
        counts[a] = counts.get(a, 0) + 1
    sys_parts = [f"{amt}*{count}" for amt, count in counts.items()]
    return amounts, " + ".join(sys_parts)

# =======================================================
# الدالة الرئيسية للإنفجار العظيم (Data Seeding)
# =======================================================
def seed_database():
    print("🗑️ جاري مسح قاعدة البيانات القديمة (تجاهل التراخيص)...")
    with transaction.atomic():
        InstallmentPayment.objects.all().delete()
        SaleItem.objects.all().delete()
        Receipt.objects.all().delete()
        PurchaseInvoiceItem.objects.all().delete()
        PurchaseInvoice.objects.all().delete()
        InventoryAdjustment.objects.all().delete()
        CommissionHistory.objects.all().delete()
        InventoryItem.objects.all().delete()
        Expense.objects.all().delete()
        Salesperson.objects.all().delete()
        Supplier.objects.all().delete()
        Branch.objects.all().delete()

    print("✅ تم المسح! جاري زراعة البيانات الجديدة بذكاء محاكي للسوق...")
    
    with transaction.atomic():
        branch = Branch.objects.create(name="الفرع الرئيسي")
        suppliers = [Supplier.objects.create(name=f"مورد/مصنع {n}") for n in ["توشيبا", "فريش", "النساجون", "النور للأدوات المنزلية", "كينوود", "براون", "تورنيدو"]]
        salespersons = [Salesperson.objects.create(name=n, branch=branch) for n in ["أحمد الشناوي", "محمود الهواري", "كريم عادل", "مصطفى السيد"]]

        # 2. خطة المنتجات (الأسعار هنا هي سعر البيع قسط من 400 لـ 4000)
        product_plan = [
            # الدفعة الأولى - شهر 11/2024
            {"name": "شاشة تورنيدو 32ب", "base_price": 4000, "m": 11, "y": 2024},
            {"name": "شاشة ATA 32ب", "base_price": 3200, "m": 11, "y": 2024},
            {"name": "خلاط مولينكس 400و", "base_price": 800, "m": 11, "y": 2024},
            {"name": "خلاط كينوود 500و", "base_price": 1100, "m": 11, "y": 2024},
            {"name": "خلاط تورنيدو 300و", "base_price": 600, "m": 11, "y": 2024},
            {"name": "غسالة فريش 10ك هاف", "base_price": 3500, "m": 11, "y": 2024},
            {"name": "غسالة توشيبا 7ك هاف", "base_price": 2800, "m": 11, "y": 2024},
            {"name": "مكواة تيفال بخار 2000و", "base_price": 1200, "m": 11, "y": 2024},
            {"name": "مكواة باناسونيك جاف", "base_price": 750, "m": 11, "y": 2024},
            {"name": "مكواة فيليبس بخار 1800و", "base_price": 1000, "m": 11, "y": 2024},
            {"name": "مكنسة توشيبا 1600و", "base_price": 3500, "m": 11, "y": 2024},
            {"name": "مكنسة كينوود 1800و", "base_price": 4000, "m": 11, "y": 2024},
            {"name": "دفاية هالوجين 3ش", "base_price": 600, "m": 11, "y": 2024},
            {"name": "دفاية زيت تورنيدو 9ر", "base_price": 2500, "m": 11, "y": 2024},
            {"name": "دفاية فريش 2ش", "base_price": 450, "m": 11, "y": 2024},
            {"name": "غلاية تورنيدو 1.7ل", "base_price": 650, "m": 11, "y": 2024},
            {"name": "غلاية كينوود 1.5ل", "base_price": 900, "m": 11, "y": 2024},
            {"name": "غلاية فريش بلاستيك", "base_price": 400, "m": 11, "y": 2024},
            {"name": "حلل تيفال زهران 8ق", "base_price": 3800, "m": 11, "y": 2024},
            {"name": "طقم كاسات كريستال 6ق", "base_price": 800, "m": 11, "y": 2024},
            {"name": "طقم كاسات تركي 6ق", "base_price": 450, "m": 11, "y": 2024},
            {"name": "مجات شاي بايركس 6ق", "base_price": 400, "m": 11, "y": 2024},
            {"name": "طقم عشاء لومينارك 46ق", "base_price": 3500, "m": 11, "y": 2024},
            {"name": "طقم عشاء أركوبال 18ق", "base_price": 1500, "m": 11, "y": 2024},
            {"name": "ملايات قطن العامرية 4ق", "base_price": 650, "m": 11, "y": 2024},
            {"name": "ملايات 3D اطفال 3ق", "base_price": 500, "m": 11, "y": 2024},
            {"name": "ملايات مطرز تركي 5ق", "base_price": 1200, "m": 11, "y": 2024},
            {"name": "بطانية مورا حفر 1ط", "base_price": 1800, "m": 11, "y": 2024},
            {"name": "بطانية الدب 2ط", "base_price": 2500, "m": 11, "y": 2024},
            {"name": "بطانية ماك 1ط", "base_price": 1100, "m": 11, "y": 2024},
            {"name": "كوفرتة قطن صيفي 2ق", "base_price": 700, "m": 11, "y": 2024},
            {"name": "كوفرتة المجد قطيفة", "base_price": 950, "m": 11, "y": 2024},
            {"name": "لحاف المجد 1ط", "base_price": 1400, "m": 11, "y": 2024},
            {"name": "سشوار براون 2000و", "base_price": 1200, "m": 11, "y": 2024},
            {"name": "سشوار فيليبس 1800و", "base_price": 950, "m": 11, "y": 2024},
            {"name": "ماكينة حلاقة براون", "base_price": 1500, "m": 11, "y": 2024},
            {"name": "كبة براون 400و", "base_price": 1800, "m": 11, "y": 2024},
            {"name": "كبة تورنيدو 400و", "base_price": 1300, "m": 11, "y": 2024},
            {"name": "مضرب بيض فريش", "base_price": 750, "m": 11, "y": 2024},
            {"name": "مروحة سقف تورنيدو 56ب", "base_price": 1100, "m": 11, "y": 2024},
            # متفرقات 2025
            {"name": "ميكروويف فريش 20ل", "base_price": 3800, "m": 1, "y": 2025},
            {"name": "فرن تورنيدو 45ل", "base_price": 2900, "m": 3, "y": 2025},
            {"name": "مرتبة يانسن 120سم", "base_price": 3500, "m": 5, "y": 2025},
            {"name": "مروحة ستاند توشيبا", "base_price": 1600, "m": 7, "y": 2025},
            {"name": "محضر طعام تورنيدو", "base_price": 2200, "m": 9, "y": 2025},
        ]

        # 3. متغيرات تتبع المبيعات لتحديد مشتريات الشهر القادم
        product_sales_tracker = {}

        # 4. الدوران على الشهور من 11/2024 إلى 4/2026 (18 شهر)
        start_date = date(2024, 11, 1)
        end_date = date(2026, 4, 1)
        current_date = start_date
        
        receipt_counter = 1

        while current_date <= end_date:
            curr_y = current_date.year
            curr_m = current_date.month
            print(f"⏳ جاري معالجة شهر {curr_m}/{curr_y} ...")

            # أ) تفعيل المنتجات الجديدة
            for p in product_plan:
                if p['y'] == curr_y and p['m'] == curr_m:
                    cost = round_to_5(p['base_price'] / 2) # التكلفة = السعر / 2
                    comm = round_to_5(cost * 0.10)
                    item = InventoryItem.objects.create(
                        name=p['name'], branch=branch, initial_quantity=0,
                        initial_purchase_price=cost, initial_commission_amount=comm,
                        initial_month=curr_m, initial_year=curr_y
                    )
                    CommissionHistory.objects.create(
                        item=item, commission_amount=comm, activation_month=curr_m, activation_year=curr_y
                    )

            active_products = list(InventoryItem.objects.filter(branch=branch, initial_year__lte=curr_y).exclude(initial_year=curr_y, initial_month__gt=curr_m))
            if not active_products:
                current_date += relativedelta(months=1)
                continue

            # ب) المشتريات (ذكية بناءً على مبيعات الشهر السابق)
            inv_purch = PurchaseInvoice.objects.create(
                invoice_number=receipt_counter*100, invoice_type='PURCHASE',
                supplier=random.choice(suppliers), branch=branch, invoice_month=curr_m, invoice_year=curr_y
            )
            for prod in active_products:
                cost = round_to_5([p['base_price'] for p in product_plan if p['name']==prod.name][0] / 2)
                
                if prod.name not in product_sales_tracker:
                    # منتج جديد: نشتري كمية افتتاحية
                    qty_to_buy = random.randint(80, 120)
                    product_sales_tracker[prod.name] = 0
                else:
                    # منتج قديم: نشتري اللي اتباع الشهر اللي فات + بافر صغير
                    last_month_sales = product_sales_tracker[prod.name]
                    if last_month_sales > 0:
                        qty_to_buy = last_month_sales + random.randint(5, 15)
                    else:
                        qty_to_buy = random.randint(10, 20) # تنشيط رصيد

                PurchaseInvoiceItem.objects.create(invoice=inv_purch, inventory_item=prod, quantity=qty_to_buy, purchase_price=cost)

            # تصفير عداد المبيعات للشهر الحالي
            current_month_sales = {prod.name: 0 for prod in active_products}

            # ج) المصروفات
            Expense.objects.create(branch=branch, amount=random.randint(2000, 5000), description="مصروفات تشغيل ومستلزمات", expense_year=curr_y, expense_month=curr_m)

            # د) المبيعات (120 فاتورة)
            # تجهيز الأوزان (المنتج الرخيص وزنه أكبر = فرصة اختياره أعلى)
            weights = [10000 / [p['base_price'] for p in product_plan if p['name']==prod.name][0] for prod in active_products]

            for _ in range(120):
                is_cash = random.random() < 0.05
                salesperson = random.choice(salespersons)
                
                receipt = Receipt.objects.create(
                    receipt_number=receipt_counter, branch=branch, salesperson=salesperson,
                    customer_name=generate_arabic_name(), phone_number=generate_phone(),
                    address=f"شارع {random.randint(1, 99)}", area=generate_area(),
                    sale_year=curr_y, sale_month=curr_m, is_cash_sale=is_cash
                )
                
                # اختيار منتجات بدون تكرار في نفس الفاتورة بناءً على الوزن (الرخيص يظهر أكثر)
                temp_prods = list(active_products)
                temp_weights = list(weights)
                selected_prods = []
                num_items = random.randint(1, min(3, len(temp_prods)))
                
                for _ in range(num_items):
                    choice = random.choices(temp_prods, weights=temp_weights, k=1)[0]
                    selected_prods.append(choice)
                    idx = temp_prods.index(choice)
                    temp_prods.pop(idx)
                    temp_weights.pop(idx)

                total_receipt_amount = 0
                prod_strings = []

                for prod in selected_prods:
                    qty = random.randint(1, 2)
                    base_inst_price = [p['base_price'] for p in product_plan if p['name']==prod.name][0]
                    
                    fluctuation = random.uniform(0.97, 1.03)
                    final_inst_price = round_to_5(base_inst_price * fluctuation)
                    
                    if is_cash:
                        final_price = round_to_5(final_inst_price * 0.75)
                    else:
                        final_price = final_inst_price

                    SaleItem.objects.create(receipt=receipt, inventory_item=prod, quantity=qty, unit_price=final_price)
                    total_receipt_amount += (qty * final_price)
                    prod_strings.append(f"{qty} {prod.name}" if qty > 1 else prod.name)
                    
                    # تسجيل المبيعات لهذا المنتج عشان الشراء الشهر الجاي
                    current_month_sales[prod.name] += qty

                receipt.products_text = " + ".join(prod_strings)
                receipt.total_amount = total_receipt_amount

                if is_cash:
                    receipt.down_payment = total_receipt_amount
                    receipt.installment_system = ""
                else:
                    has_down_payment = random.choice([True, False])
                    dp = round_to_5(total_receipt_amount * 0.10) if has_down_payment else 0
                    receipt.down_payment = dp
                    remaining = total_receipt_amount - dp
                    
                    amounts, sys_str = calculate_installments_system(remaining, random.choice([6, 10, 12]))
                    receipt.installment_system = sys_str
                    
                    inst_date = date(curr_y, curr_m, 15)
                    for idx, amt in enumerate(amounts):
                        due_date = inst_date + relativedelta(months=idx + 1)
                        InstallmentPayment.objects.create(receipt=receipt, payment_date=due_date, amount=amt)

                receipt.save()
                receipt_counter += 1

            # تحديث متتبع المبيعات للشهر القادم
            product_sales_tracker = current_month_sales
            current_date += relativedelta(months=1)

    print(f"🎉 تمت العملية بنجاح! تم إنشاء {receipt_counter - 1} فاتورة، بنظام الشراء الذكي ومراعاة المنتجات الشعبية.")

if __name__ == '__main__':
    seed_database()