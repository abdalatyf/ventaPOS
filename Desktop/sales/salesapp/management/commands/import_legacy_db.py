import os
import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from salesapp.models import (
    Branch, Salesperson, Supplier, InventoryItem, CommissionHistory,
    PurchaseInvoice, PurchaseInvoiceItem, Receipt, SaleItem,
    InstallmentPayment, Expense, InventoryAdjustment
)

class Command(BaseCommand):
    help = 'استيراد البيانات من ملف نسخة احتياطية قديم إلى الهيكل الجديد للبرنامج'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='مسار ملف الـ sqlite3 القديم')

    def handle(self, *args, **kwargs):
        backup_file = kwargs['backup_file']

        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f"❌ لم يتم العثور على الملف: {backup_file}"))
            return

        self.stdout.write(self.style.WARNING(f"🔗 جاري الاتصال بقاعدة البيانات القديمة..."))
        conn = sqlite3.connect(backup_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            with transaction.atomic():
                # 1. استيراد الفروع
                self.stdout.write("📦 استيراد الفروع...")
                cur.execute("SELECT * FROM salesapp_branch")
                for _row in cur.fetchall():
                    row = dict(_row)
                    Branch.objects.get_or_create(id=row['id'], defaults={'name': row['name']})

                # 2. استيراد الموردين
                self.stdout.write("📦 استيراد الموردين...")
                try:
                    cur.execute("SELECT * FROM salesapp_supplier")
                    for _row in cur.fetchall():
                        row = dict(_row)
                        # حماية إضافية لأسماء الموردين المكررة
                        base_sup_name = str(row['name']).strip()
                        final_sup_name = base_sup_name
                        c = 1
                        while Supplier.objects.filter(name=final_sup_name).exclude(id=row['id']).exists():
                            final_sup_name = f"{base_sup_name} (مكرر {c})"
                            c += 1
                        Supplier.objects.get_or_create(id=row['id'], defaults={'name': final_sup_name})
                except sqlite3.OperationalError:
                    pass

                # 3. استيراد الموظفين
                self.stdout.write("📦 استيراد المناديب...")
                cur.execute("SELECT * FROM salesapp_salesperson")
                for _row in cur.fetchall():
                    row = dict(_row)
                    Salesperson.objects.get_or_create(
                        id=row['id'],
                        defaults={'name': row['name'], 'branch_id': row['branch_id']}
                    )

                # 4. استيراد المنتجات (مع حل سحري للأسماء المكررة)
                self.stdout.write("📦 استيراد الأصناف وتأمين الأسماء المكررة...")
                cur.execute("SELECT * FROM salesapp_inventoryitem")
                old_items_qty = {}
                
                for _row in cur.fetchall():
                    row = dict(_row)
                    try:
                        created_dt = datetime.strptime(row['created_at'][:19], '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        created_dt = datetime.now()

                    old_items_qty[row['id']] = row['quantity']

                    # 🟢 الخوارزمية الذكية لاكتشاف وتعديل الأسماء المكررة
                    base_name = str(row['name']).strip()
                    final_name = base_name
                    counter = 1
                    
                    # طالما الاسم موجود لمنتج آخر (يحمل ID مختلف) في نفس الفرع، قم بتغيير الاسم
                    while InventoryItem.objects.filter(name=final_name, branch_id=row['branch_id']).exclude(id=row['id']).exists():
                        final_name = f"{base_name} (مكرر {counter})"
                        counter += 1

                    item, _ = InventoryItem.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'name': final_name,
                            'branch_id': row['branch_id'],
                            'initial_quantity': 1000, 
                            'initial_purchase_price': row['purchase_price'],
                            'initial_commission_amount': row.get('salesperson_commission_amount', 0),
                            'initial_month': created_dt.month,
                            'initial_year': created_dt.year,
                        }
                    )

                    CommissionHistory.objects.get_or_create(
                        item=item,
                        activation_month=created_dt.month,
                        activation_year=created_dt.year,
                        defaults={'commission_amount': row.get('salesperson_commission_amount', 0)}
                    )

                # 5. استيراد فواتير الشراء
                self.stdout.write("📦 استيراد فواتير المشتريات والمرتجعات...")
                try:
                    cur.execute("SELECT * FROM salesapp_purchaseinvoice")
                    for _row in cur.fetchall():
                        row = dict(_row)
                        PurchaseInvoice.objects.get_or_create(
                            id=row['id'],
                            defaults={
                                'invoice_number': row['invoice_number'],
                                'branch_id': row['branch_id'],
                                'supplier_id': row['supplier_id'],
                                'invoice_type': row['invoice_type'],
                                'invoice_month': row['invoice_month'],
                                'invoice_year': row['invoice_year'],
                            }
                        )

                    cur.execute("SELECT * FROM salesapp_purchaseinvoiceitem")
                    for _row in cur.fetchall():
                        row = dict(_row)
                        PurchaseInvoiceItem.objects.get_or_create(
                            id=row['id'],
                            defaults={
                                'invoice_id': row['invoice_id'],
                                'inventory_item_id': row['inventory_item_id'],
                                'quantity': row['quantity'],
                                'purchase_price': row['purchase_price'] if row['purchase_price'] else 0,
                            }
                        )
                except sqlite3.OperationalError:
                    pass

                # 6. استيراد المبيعات (الوصلات)
                self.stdout.write("📦 استيراد الفواتير والوصلات...")
                cur.execute("SELECT * FROM salesapp_receipt")
                for _row in cur.fetchall():
                    row = dict(_row)
                    Receipt.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'source': row.get('source', 'DESKTOP'),
                            'receipt_number': row['receipt_number'],
                            'branch_id': row['branch_id'],
                            'customer_name': row['customer_name'],
                            'products_text': row['products_text'],
                            'phone_number': row['phone_number'],
                            'address': row['address'],
                            'area': row['area'],
                            'total_amount': row['total_amount'],
                            'down_payment': row['down_payment'],
                            'installment_system': row['installment_system'],
                            'salesperson_id': row['salesperson_id'],
                            'sale_year': row['sale_year'],
                            'sale_month': row['sale_month'],
                            'is_cash_sale': bool(row['is_cash_sale']),
                        }
                    )

                # 7. استيراد تفاصيل الفواتير
                self.stdout.write("📦 استيراد الأصناف المباعة...")
                cur.execute("SELECT * FROM salesapp_saleitem")
                for _row in cur.fetchall():
                    row = dict(_row)
                    SaleItem.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'receipt_id': row['receipt_id'],
                            'inventory_item_id': row['inventory_item_id'],
                            'quantity': row['quantity'],
                            'unit_price': row['unit_price'],
                        }
                    )

                # 8. استيراد الأقساط
                self.stdout.write("📦 استيراد سجل الأقساط...")
                cur.execute("SELECT * FROM salesapp_installmentpayment")
                for _row in cur.fetchall():
                    row = dict(_row)
                    InstallmentPayment.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'receipt_id': row['receipt_id'],
                            'payment_date': row['payment_date'],
                            'amount': row['amount'],
                        }
                    )

                # 9. استيراد المصروفات
                self.stdout.write("📦 استيراد المصروفات...")
                cur.execute("SELECT * FROM salesapp_expense")
                for _row in cur.fetchall():
                    row = dict(_row)
                    Expense.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'branch_id': row['branch_id'],
                            'amount': row['amount'],
                            'description': row['description'],
                            'expense_year': row['expense_year'],
                            'expense_month': row['expense_month'],
                        }
                    )

                # 10. المعايرة الزمنية للرصيد
                self.stdout.write(self.style.WARNING("⚙️ جاري معايرة أرصدة المخزن وضبط التسويات..."))
                for item_id, old_current_qty in old_items_qty.items():
                    item = InventoryItem.objects.get(id=item_id)
                    calculated_qty = item.get_stock_at_date(12, 2099) 
                    diff = old_current_qty - calculated_qty

                    if diff > 0:
                        InventoryAdjustment.objects.create(
                            item=item, adjustment_type='SURPLUS', quantity=diff,
                            reason='ترحيل فرق الرصيد اليدوي من النسخة القديمة',
                            month=item.initial_month, year=item.initial_year
                        )
                    elif diff < 0:
                        InventoryAdjustment.objects.create(
                            item=item, adjustment_type='DEFICIT', quantity=abs(diff),
                            reason='ترحيل فرق الرصيد اليدوي من النسخة القديمة',
                            month=item.initial_month, year=item.initial_year
                        )

            conn.close()
            self.stdout.write(self.style.SUCCESS("✅ تمت عملية الترحيل بنجاح! قاعدة البيانات الجديدة جاهزة الآن."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ حدث خطأ أثناء الترحيل: {str(e)}"))