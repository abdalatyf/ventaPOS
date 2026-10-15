import os
import re

files_to_clean = [
    'src/pages/SearchReceipts.jsx',
    'src/pages/reports/ExpensesReport.jsx',
    'src/pages/reports/InstallmentsReport.jsx',
    'src/pages/reports/ProfitAndLossReport.jsx',
    'src/pages/reports/ReceiptsReport.jsx',
    'src/pages/reports/InventoryMovementReport.jsx'
]

for file_path in files_to_clean:
    if not os.path.exists(file_path): 
        print('Not found', file_path)
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Using re.DOTALL to match across newlines
    content = re.sub(r'\s*// --- Smart Scroll Interceptor ---.*?return \(', '\n\n  return (', content, flags=re.DOTALL)
    
    # Remove any stray handleWheel blocks if comment was missing
    content = re.sub(r'\s*const handleWheel = useCallback.*?return \(', '\n\n  return (', content, flags=re.DOTALL)
    
    # Remove ref={setTableRef}
    content = re.sub(r'\s*ref=\{setTableRef\}', '', content)
    
    # Fix max heights
    if 'ProfitAndLossReport.jsx' in file_path:
        content = content.replace("maxHeight: 'calc(100vh - 110px)'", "maxHeight: 'calc(100vh - 280px)'")
    elif 'SearchReceipts.jsx' in file_path:
        content = content.replace("maxHeight: 'calc(100vh - 110px)'", "maxHeight: 'calc(100vh - 250px)'")
    elif 'ReceiptsReport.jsx' in file_path:
        content = content.replace("maxHeight: 'calc(100vh - 110px)'", "maxHeight: 'calc(100vh - 180px)'")
    elif 'InventoryMovementReport.jsx' in file_path:
        content = content.replace("maxHeight: 'calc(100vh - 110px)'", "maxHeight: 'calc(100vh - 250px)'")
        content = content.replace("maxHeight: 'calc(100vh - 220px)'", "maxHeight: 'calc(100vh - 250px)'")
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Cleaned', file_path)
