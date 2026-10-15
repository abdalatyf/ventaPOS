import os

command_code = """from django.core.management.base import BaseCommand
from api.models import InventoryItem, MonthlyInventorySnapshot
import datetime

class Command(BaseCommand):
    help = 'Backfills monthly inventory snapshots to speed up historical stock calculation.'

    def handle(self, *args, **options):
        items = InventoryItem.objects.filter(is_deleted=False)
        self.stdout.write(f"Generating snapshots for {items.count()} items...")

        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        count = 0
        for item in items:
            # Determine starting month/year
            year = item.initial_year
            month = item.initial_month

            while year < current_year or (year == current_year and month <= current_month):
                # Calculate the exact stock at that specific month/year
                stock = item.get_stock_at_date(month, year)
                price = item.get_price_at_date(month, year)

                # Use update_or_create to ensure no duplicates
                MonthlyInventorySnapshot.objects.update_or_create(
                    item=item,
                    year=year,
                    month=month,
                    defaults={
                        'closing_stock': stock,
                        'closing_value': stock * price
                    }
                )

                count += 1
                month += 1
                if month > 12:
                    month = 1
                    year += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully generated {count} monthly snapshots!"))
"""

os.makedirs(r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\management\commands", exist_ok=True)
with open(r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\management\commands\generate_snapshots.py", "w", encoding="utf-8") as f:
    f.write(command_code)

print("Created generate_snapshots.py")
