import re
import os

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"

with open(views_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Optimize DashboardReportView
# We'll inject the cache dicts right before "# 3. COGS and Sales Commission"
injection_point_1 = "        # 3. COGS and Sales Commission"
memoization_code = """
        # --- N+1 OPTIMIZATION CACHE ---
        price_cache = {}
        def get_cached_price(item, month, year):
            key = (item.id, month, year)
            if key not in price_cache:
                price_cache[key] = item.get_price_at_date(month, year)
            return price_cache[key]

        comm_cache = {}
        def get_cached_comm(item, month, year):
            key = (item.id, month, year)
            if key not in comm_cache:
                comm_cache[key] = item.get_commission_at_date(month, year)
            return comm_cache[key]
        
        # 3. COGS and Sales Commission"""

content = content.replace(injection_point_1, memoization_code)

# Now replace the calls in DashboardReportView
content = content.replace(
    "cost_unit = item.inventory_item.get_price_at_date(item.receipt.sale_month, item.receipt.sale_year)",
    "cost_unit = get_cached_price(item.inventory_item, item.receipt.sale_month, item.receipt.sale_year)"
)
content = content.replace(
    "comm_unit = item.inventory_item.get_commission_at_date(item.receipt.sale_month, item.receipt.sale_year)",
    "comm_unit = get_cached_comm(item.inventory_item, item.receipt.sale_month, item.receipt.sale_year)"
)

# Now let's inject into SalespersonPerformanceReportView
injection_point_2 = "    def get(self, request):"
# Need to find the specific get method of SalespersonPerformanceReportView
# It's better to just search for `class SalespersonPerformanceReportView` and then the next `def get`
class_str = "class SalespersonPerformanceReportView(views.APIView):\n    def get(self, request):"
memoization_code_2 = """class SalespersonPerformanceReportView(views.APIView):
    def get(self, request):
        # --- N+1 OPTIMIZATION CACHE ---
        comm_cache = {}
        def get_cached_comm(item, month, year):
            key = (item.id, month, year)
            if key not in comm_cache:
                comm_cache[key] = item.get_commission_at_date(month, year)
            return comm_cache[key]
"""

content = content.replace(class_str, memoization_code_2)

with open(views_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied in-memory cache to views.py")
