import os
import re

views_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend\api\views.py"

with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. DashboardReportView
# Replace month/year parsing
dashboard_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        try:
            year = int(year_str) if year_str else now.year
        except ValueError:
            raise ValidationError({"year": ["Invalid year format."]})
            
        try:
            month = int(month_str) if month_str else now.month
        except ValueError:
            raise ValidationError({"month": ["Invalid month format."]})"""
dashboard_new_parse = """        start_month, start_year, end_month, end_year = get_date_range_filters(request)"""
content = content.replace(dashboard_old_parse, dashboard_new_parse)

# Replace filter logic for Receipt
content = re.sub(
    r'sale_year=year,\s*sale_month=month,',
    r'*[build_date_range_q("sale_month", "sale_year", start_month, start_year, end_month, end_year)],',
    content
)

# Replace filter logic for InstallmentPayment
content = re.sub(
    r'payment_date__year=year,\s*payment_date__month=month,',
    r'*[build_date_range_q("payment_date__month", "payment_date__year", start_month, start_year, end_month, end_year)],',
    content
)

# Replace filter logic for Expense
content = re.sub(
    r'expense_year=year,\s*expense_month=month,',
    r'*[build_date_range_q("expense_month", "expense_year", start_month, start_year, end_month, end_year)],',
    content
)

# Replace filter logic for PurchaseInvoice
content = re.sub(
    r'invoice__invoice_year=year,\s*invoice__invoice_month=month,',
    r'*[build_date_range_q("invoice__invoice_month", "invoice__invoice_year", start_month, start_year, end_month, end_year)],',
    content
)

# Replace filter logic for SaleItem
content = re.sub(
    r'receipt__sale_year=year,\s*receipt__sale_month=month,',
    r'*[build_date_range_q("receipt__sale_month", "receipt__sale_year", start_month, start_year, end_month, end_year)],',
    content
)

# Replace filter logic for InventoryAdjustment
content = re.sub(
    r'year=year,\s*month=month,',
    r'*[build_date_range_q("month", "year", start_month, start_year, end_month, end_year)],',
    content
)

# DashboardReportView: cost_unit = item.inventory_item.get_price_at_date(month, year)
content = content.replace(
    "cost_unit = item.inventory_item.get_price_at_date(month, year)",
    "cost_unit = item.inventory_item.get_price_at_date(item.receipt.sale_month, item.receipt.sale_year)"
)
content = content.replace(
    "comm_unit = item.inventory_item.get_commission_at_date(month, year)",
    "comm_unit = item.inventory_item.get_commission_at_date(item.receipt.sale_month, item.receipt.sale_year)"
)

# ProfitAndLossReportView also has its own month/year parsing
pnl_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        
        now = timezone.now()
        year = int(year_str) if year_str else now.year
        month = int(month_str) if month_str else now.month"""
content = content.replace(pnl_old_parse, dashboard_new_parse)

# SalespersonPerformanceReportView parse
sp_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        now = timezone.now()
        year = int(year_str) if year_str else now.year
        month = int(month_str) if month_str else now.month"""
content = content.replace(sp_old_parse, dashboard_new_parse)

# InventoryMovementReportView parse
inv_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        now = timezone.now()
        year = int(year_str) if year_str else now.year
        month = int(month_str) if month_str else now.month"""
content = content.replace(inv_old_parse, dashboard_new_parse)

# CashDrawerReportView parse
cd_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        now = timezone.now()
        year = int(year_str) if year_str else now.year
        month = int(month_str) if month_str else now.month"""
content = content.replace(cd_old_parse, dashboard_new_parse)

# InstallmentsReportView parse
inst_old_parse = """        year_str = request.query_params.get("year")
        month_str = request.query_params.get("month")
        now = timezone.now()
        year = int(year_str) if year_str else now.year
        month = int(month_str) if month_str else now.month"""
content = content.replace(inst_old_parse, dashboard_new_parse)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactored views.py successfully!")
