import re

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"

with open(views_path, "r", encoding="utf-8") as f:
    content = f.read()

# Locate the start of InventoryMovementReportView get method
injection_point = """
        inventory_items = InventoryItem.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )

        items_list = []
"""

optimized_code = """
        inventory_items = InventoryItem.objects.filter(
            branch_id=branch_id,
            is_deleted=False
        )

        # --- SNAPSHOT OPTIMIZATION CACHE ---
        from api.models import MonthlyInventorySnapshot
        snapshots = MonthlyInventorySnapshot.objects.filter(year=prev_year, month=prev_month, item__branch_id=branch_id)
        snapshot_dict = {s.item_id: s.closing_stock for s in snapshots}

        items_list = []
"""

content = content.replace(injection_point, optimized_code)

old_opening = """        for item in inventory_items:
            opening_stock = item.get_stock_at_date(prev_month, prev_year)
            if item.initial_year == start_year and item.initial_month == start_month:"""

new_opening = """        for item in inventory_items:
            if item.id in snapshot_dict:
                opening_stock = snapshot_dict[item.id]
            else:
                opening_stock = item.get_stock_at_date(prev_month, prev_year)
                
            if item.initial_year == start_year and item.initial_month == start_month:"""

content = content.replace(old_opening, new_opening)

with open(views_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied snapshot optimization to InventoryMovementReportView")
