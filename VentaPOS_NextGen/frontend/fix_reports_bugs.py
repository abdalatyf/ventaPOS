import os
import re

reports_dir = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports"

# 1. ReceiptsReport.jsx
with open(os.path.join(reports_dir, "ReceiptsReport.jsx"), 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "if (month) params.append('month', month);",
    "if (startMonth) params.append('start_month', startMonth);\n      if (endMonth) params.append('end_month', endMonth);"
)
content = content.replace(
    "if (year) params.append('year', year);",
    "if (startYear) params.append('start_year', startYear);\n      if (endYear) params.append('end_year', endYear);"
)

with open(os.path.join(reports_dir, "ReceiptsReport.jsx"), 'w', encoding='utf-8') as f:
    f.write(content)

# 2. InstallmentsReport.jsx
with open(os.path.join(reports_dir, "InstallmentsReport.jsx"), 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "if (year && month && branchId) {",
    "if (startYear && startMonth && endYear && endMonth && branchId) {"
)
content = content.replace(
    "}, [year, month, saleFromYear, saleFromMonth, saleToYear, saleToMonth, salespersonId, branchId]);",
    "}, [startYear, startMonth, endYear, endMonth, saleFromYear, saleFromMonth, saleToYear, saleToMonth, salespersonId, branchId]);"
)
content = content.replace(
    "year: year || undefined,",
    "start_year: startYear || undefined,\n          end_year: endYear || undefined,"
)
content = content.replace(
    "month: month || undefined,",
    "start_month: startMonth || undefined,\n          end_month: endMonth || undefined,"
)

with open(os.path.join(reports_dir, "InstallmentsReport.jsx"), 'w', encoding='utf-8') as f:
    f.write(content)


# 3. SalespersonPerformanceReport.jsx
with open(os.path.join(reports_dir, "SalespersonPerformanceReport.jsx"), 'r', encoding='utf-8') as f:
    content = f.read()

# Fix params API call
content = content.replace("year: year,", "start_year: startYear,\n          end_year: endYear,")
content = content.replace("month: month", "start_month: startMonth,\n          end_month: endMonth")

# Fix Links
content = content.replace("year=${year}&month=${month}", "start_year=${startYear}&start_month=${startMonth}&end_year=${endYear}&end_month=${endMonth}")
# Fix the title rendering
content = content.replace("{month}/{year}", "{startMonth}/{startYear} - {endMonth}/{endYear}")

with open(os.path.join(reports_dir, "SalespersonPerformanceReport.jsx"), 'w', encoding='utf-8') as f:
    f.write(content)


# 4. CashDrawerReport.jsx
with open(os.path.join(reports_dir, "CashDrawerReport.jsx"), 'r', encoding='utf-8') as f:
    content = f.read()

# Remove local states for year/month and replace with context
content = re.sub(r'const \[year, setYear\] = useState[^;]+;', '', content)
content = re.sub(r'const \[month, setMonth\] = useState[^;]+;', '', content)

content = content.replace(
    "const { branchId } = useContext(ReportsContext);",
    "const { startYear, startMonth, endYear, endMonth, branchId } = useContext(ReportsContext);"
)
content = content.replace(
    "year: year,",
    "start_year: startYear,\n          end_year: endYear,"
)
content = content.replace(
    "month: month",
    "start_month: startMonth,\n          end_month: endMonth"
)
content = content.replace(
    "setYear(searchParams.get('year') || defaultYear);",
    ""
)
content = content.replace(
    "setMonth(searchParams.get('month') || defaultMonth);",
    ""
)
content = content.replace(
    "if(year && month) {",
    "if(startYear && startMonth && endYear && endMonth) {"
)
content = content.replace(
    "}, [year, month]);",
    "}, [startYear, startMonth, endYear, endMonth]);"
)
content = content.replace(
    "value={year}",
    "value={startYear}"
)
content = content.replace(
    "value={month}",
    "value={startMonth}"
)

with open(os.path.join(reports_dir, "CashDrawerReport.jsx"), 'w', encoding='utf-8') as f:
    f.write(content)

# 5. InventoryMovementReport.jsx
with open(os.path.join(reports_dir, "InventoryMovementReport.jsx"), 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'const \[year, setYear\] = useState[^;]+;', '', content)
content = re.sub(r'const \[month, setMonth\] = useState[^;]+;', '', content)

content = content.replace(
    "const { branchId } = useContext(ReportsContext);",
    "const { startYear, startMonth, endYear, endMonth, branchId } = useContext(ReportsContext);"
)
content = content.replace(
    "year: year,",
    "start_year: startYear,\n          end_year: endYear,"
)
content = content.replace(
    "month: month,",
    "start_month: startMonth,\n          end_month: endMonth,"
)
content = content.replace(
    "}, [year, month, salespersonId, dateLoading]);",
    "}, [startYear, startMonth, endYear, endMonth, salespersonId, dateLoading]);"
)
content = content.replace(
    "value={year}",
    "value={startYear}"
)
content = content.replace(
    "value={month}",
    "value={startMonth}"
)
content = content.replace(
    "if (!year || !month || !branchId) return;",
    "if (!startYear || !startMonth || !endYear || !endMonth || !branchId) return;"
)

with open(os.path.join(reports_dir, "InventoryMovementReport.jsx"), 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed frontend reports!")
