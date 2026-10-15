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
    // Search for export default function Name() {
    const fnMatch = content.match(/export default function \w+\([^)]*\) \{/);
    if (fnMatch && !content.includes('const { setTableRef } = useSmartScroll();')) {
        content = content.replace(fnMatch[0], fnMatch[0] + '\n  const { setTableRef } = useSmartScroll();');
    }
    
    // 3. Add ref={setTableRef} to the specific table wrapper
    content = content.replace(/className="table-responsive [^"]*hide-vertical-scroll"/g, 'ref={setTableRef}\n            className="table-responsive hide-vertical-scroll"');
    // Ensure we don't have duplicated hide-vertical-scroll or missing classes.
    // Actually simpler: just find className="table-responsive rounded hide-vertical-scroll"
    content = content.replace(/className="table-responsive rounded hide-vertical-scroll"/g, 'ref={setTableRef}\n            className="table-responsive rounded hide-vertical-scroll"');
    
    // Let's do a more robust replacement for the div
    // We look for className="table-responsive... hide-vertical-scroll"
    
    // Fix max heights to activate the smart scroll
    if (item.path.includes('ProfitAndLossReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 280px\)'/g, "maxHeight: 'calc(100vh - 110px)'");
    } else if (item.path.includes('SearchReceipts.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 250px\)'/g, "maxHeight: 'calc(100vh - 110px)'");
    } else if (item.path.includes('ReceiptsReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 180px\)'/g, "maxHeight: 'calc(100vh - 110px)'");
    } else if (item.path.includes('InventoryMovementReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 250px\)'/g, "maxHeight: 'calc(100vh - 110px)'");
    }
    
    fs.writeFileSync(fullPath, content, 'utf8');
    console.log('Injected:', item.path);
});
