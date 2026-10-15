import re
import os

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the helper functions
helpers_pattern = r"def get_date_range_filters\(request\):.*?return start_month, start_year, end_month, end_year\n"
content = re.sub(helpers_pattern, "", content, flags=re.DOTALL)

build_q_pattern = r"def build_date_range_q\(month_field, year_field, start_month, start_year, end_month, end_year\):.*?return q_objs\n"
content = re.sub(build_q_pattern, "", content, flags=re.DOTALL)


# 2. Replace the extraction
old_extraction = "start_month, start_year, end_month, end_year = get_date_range_filters(request)"
new_extraction = """
        month_str = request.query_params.get("month", "").strip()
        year_str = request.query_params.get("year", "").strip()
        from django.utils import timezone
        now = timezone.now()
        month = int(month_str) if month_str.isdigit() else now.month
        year = int(year_str) if year_str.isdigit() else now.year
"""
content = content.replace(old_extraction, new_extraction)

# 3. Replace the build_date_range_q calls
content = re.sub(
    r'\*\[build_date_range_q\("([^"]+)", "([^"]+)", start_month, start_year, end_month, end_year\)\]',
    r'\1=month, \2=year',
    content
)

# 4. In InventoryMovementReportView
content = content.replace(
    """        if start_month == 1:
            prev_month = 12
            prev_year = start_year - 1
        else:
            prev_month = start_month - 1
            prev_year = start_year""",
    """        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year"""
)
content = content.replace(
    "if item.initial_year == start_year and item.initial_month == start_month:",
    "if item.initial_year == year and item.initial_month == month:"
)
content = content.replace("c_stock = item.get_stock_at_date(end_month, end_year)", "c_stock = item.get_stock_at_date(month, year)")


# 5. In the new cache functions (if any exist)
content = content.replace("start_month", "month")
content = content.replace("start_year", "year")
content = content.replace("end_month", "month")
content = content.replace("end_year", "year")

with open(views_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Backend revert complete")
