import os
import re

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"

with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix DashboardReportView
# c_stock = item.get_stock_at_date(month, year) -> (end_month, end_year)
content = content.replace(
    "c_stock = item.get_stock_at_date(month, year)",
    "c_stock = item.get_stock_at_date(end_month, end_year)"
)
content = content.replace(
    "c_price = item.get_price_at_date(month, year)",
    "c_price = item.get_price_at_date(end_month, end_year)"
)
content = content.replace(
    '"period": { "year": year, "month": month }',
    '"period": { "start_year": start_year, "start_month": start_month, "end_year": end_year, "end_month": end_month }'
)

# 2. Fix InventoryMovementReportView
content = content.replace(
    "if month == 1:",
    "if start_month == 1:"
)
content = content.replace(
    "prev_year = year - 1",
    "prev_year = start_year - 1"
)
content = content.replace(
    "prev_month = month - 1",
    "prev_month = start_month - 1"
)
content = content.replace(
    "prev_year = year",
    "prev_year = start_year"
)
content = content.replace(
    "if item.initial_year == year and item.initial_month == month:",
    "if item.initial_year == start_year and item.initial_month == start_month:"
)
content = content.replace(
    "final_stock = item.get_stock_at_date(month, year)",
    "final_stock = item.get_stock_at_date(end_month, end_year)"
)
content = content.replace(
    "unit_cost = item.get_price_at_date(month, year)",
    "unit_cost = item.get_price_at_date(end_month, end_year)"
)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed missing months in views.py successfully!")
