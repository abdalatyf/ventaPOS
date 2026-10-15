import os
import re

reports_dir = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports"
files = [f for f in os.listdir(reports_dir) if f.endswith('Report.jsx') and f != 'DashboardReport.jsx']

for filename in files:
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update Context Destructuring
    content = re.sub(
        r'const\s*{\s*year,\s*month,\s*branchId\s*}\s*=\s*useContext\s*\(\s*ReportsContext\s*\);',
        r'const { startYear, startMonth, endYear, endMonth, branchId } = useContext(ReportsContext);',
        content
    )
    
    # 2. Update params in API calls
    old_params = r'params:\s*\{\s*month:\s*month,\s*year:\s*year\s*\}'
    new_params = r'params: { start_year: startYear, start_month: startMonth, end_year: endYear, end_month: endMonth }'
    content = re.sub(old_params, new_params, content)
    
    # Also handle the reversed order case
    old_params_rev = r'params:\s*\{\s*year:\s*year,\s*month:\s*month\s*\}'
    content = re.sub(old_params_rev, new_params, content)
    
    # Update [year, month, branchId] in useEffect dependencies
    content = content.replace('[year, month, branchId]', '[startYear, startMonth, endYear, endMonth, branchId]')
    
    # Also in condition `if (!year || !month || !branchId) return;`
    content = content.replace(
        'if (!year || !month || !branchId) return;',
        'if (!startYear || !startMonth || !endYear || !endMonth || !branchId) return;'
    )
    
    # 3. Update the imports to use formatUtils
    # Wait, they might already have fmtNum or toArabic.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Refactored {filename}")
