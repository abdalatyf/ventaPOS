const fs = require('fs');
const path = require('path');

const filesToInject = [
    { path: 'src/pages/SearchReceipts.jsx', hookPath: '../hooks/useSmartScroll' },
    { path: 'src/pages/reports/ExpensesReport.jsx', hookPath: '../../hooks/useSmartScroll' },
    { path: 'src/pages/reports/InstallmentsReport.jsx', hookPath: '../../hooks/useSmartScroll' },
    { path: 'src/pages/reports/ProfitAndLossReport.jsx', hookPath: '../../hooks/useSmartScroll' },
    { path: 'src/pages/reports/ReceiptsReport.jsx', hookPath: '../../hooks/useSmartScroll' },
    { path: 'src/pages/reports/InventoryMovementReport.jsx', hookPath: '../../hooks/useSmartScroll' }
];

filesToInject.forEach(item => {
    const fullPath = path.join(__dirname, item.path);
    if (!fs.existsSync(fullPath)) return;
    
    let content = fs.readFileSync(fullPath, 'utf8');
    
    // 1. Add import
    if (!content.includes('useSmartScroll')) {
        content = content.replace("import React,", "import useSmartScroll from '" + item.hookPath + "';\nimport React,");
    }
    
    // 2. Add hook call
    const fnMatch = content.match(/export default function \w+\([^)]*\) \{/);
    if (fnMatch && !content.includes('const { setTableRef } = useSmartScroll();')) {
        content = content.replace(fnMatch[0], fnMatch[0] + '\n  const { setTableRef } = useSmartScroll();');
    }
    
    // 3. Ensure ref={setTableRef} is on the wrapper. Also ensure hide-vertical-scroll class exists
    if (!content.includes('ref={setTableRef}')) {
        // Standard replacement for table-responsive
        content = content.replace(/className="table-responsive hide-vertical-scroll"/g, 'ref={setTableRef}\n            className="table-responsive hide-vertical-scroll"');
        content = content.replace(/className="table-responsive rounded hide-vertical-scroll"/g, 'ref={setTableRef}\n            className="table-responsive rounded hide-vertical-scroll"');
        
        // Specifically for SearchReceipts or others missing hide-vertical-scroll
        if (content.includes('className="table-responsive flex-grow-1 overflow-auto rounded"')) {
             content = content.replace(
                'className="table-responsive flex-grow-1 overflow-auto rounded"', 
                'ref={setTableRef}\n            className="table-responsive hide-vertical-scroll flex-grow-1 rounded"'
             );
        }
    }
    
    // 4. Clean ALL inline maxHeight from the style tag of that div
    content = content.replace(/maxHeight:\s*'calc\(100vh - \d+px\)'\s*,\s*/g, '');
    content = content.replace(/,\s*maxHeight:\s*'calc\(100vh - \d+px\)'/g, '');
    content = content.replace(/maxHeight:\s*'calc\(100vh - \d+px\)'/g, '');
    
    fs.writeFileSync(fullPath, content, 'utf8');
    console.log('Finalized:', item.path);
});
