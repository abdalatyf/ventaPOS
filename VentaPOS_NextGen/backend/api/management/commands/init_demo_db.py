from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Tenant, Branch, InventoryItem, Category

class Command(BaseCommand):
    help = 'Initialize the database with Demo data if no license exists.'

    def handle(self, *args, **options):
        from api.models import ClientLicense
        if ClientLicense.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.SUCCESS("System is activated. Skipping demo init."))
            return

        with transaction.atomic():
            # Only create if the database is mostly empty
            if Tenant.objects.exists() and InventoryItem.objects.exists():
                self.stdout.write(self.style.SUCCESS("Demo data already exists."))
                return

            self.stdout.write(self.style.WARNING("Initializing Demo Data..."))
            
            # Create a Demo Tenant
            tenant, _ = Tenant.objects.get_or_create(
                company_code='DEMO123',
                defaults={'name': 'شركة تجريبية (Demo)', 'is_active': True}
            )
            
            # Create a Demo Branch
            branch, _ = Branch.objects.get_or_create(
                tenant=tenant,
                local_id=1,
                defaults={'name': 'الفرع الرئيسي'}
            )
            
            # Create some dummy categories and items
            cat_food, _ = Category.objects.get_or_create(tenant=tenant, name='مواد غذائية', defaults={'local_id': 1})
            cat_elec, _ = Category.objects.get_or_create(tenant=tenant, name='إلكترونيات', defaults={'local_id': 2})
            
            items = [
                {'name': 'شاشة سامسونج 50 بوصة', 'barcode': '10001', 'sell_price': 15000, 'buy_price': 14000, 'cat': cat_elec, 'id': 1},
                {'name': 'لابتوب ديل', 'barcode': '10002', 'sell_price': 25000, 'buy_price': 23000, 'cat': cat_elec, 'id': 2},
                {'name': 'جبنة بيضاء', 'barcode': '20001', 'sell_price': 50, 'buy_price': 40, 'cat': cat_food, 'id': 3},
                {'name': 'عصير برتقال المراعي', 'barcode': '20002', 'sell_price': 30, 'buy_price': 25, 'cat': cat_food, 'id': 4},
                {'name': 'مياه معدنية', 'barcode': '20003', 'sell_price': 10, 'buy_price': 8, 'cat': cat_food, 'id': 5},
            ]
            
            for item in items:
                InventoryItem.objects.get_or_create(
                    tenant=tenant,
                    barcode=item['barcode'],
                    defaults={
                        'name': item['name'],
                        'sell_price': item['sell_price'],
                        'buy_price': item['buy_price'],
                        'category': item['cat'],
                        'local_id': item['id'],
                        'stock_quantity': 100
                    }
                )

            self.stdout.write(self.style.SUCCESS("Demo Data Initialized Successfully."))
