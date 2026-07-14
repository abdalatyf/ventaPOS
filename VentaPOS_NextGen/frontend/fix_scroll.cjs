const fs = require('fs');
const path = require('path');

const filesToClean = [
    'src/pages/SearchReceipts.jsx',
    'src/pages/reports/ExpensesReport.jsx',
    'src/pages/reports/InstallmentsReport.jsx',
    'src/pages/reports/ProfitAndLossReport.jsx',
    'src/pages/reports/ReceiptsReport.jsx',
    'src/pages/reports/InventoryMovementReport.jsx'
];

filesToClean.forEach(file => {
    const fullPath = path.join(__dirname, file);
    if (!fs.existsSync(fullPath)) {
        console.log('Not found:', file);
        return;
    }
    
    let content = fs.readFileSync(fullPath, 'utf8');
    
    // Remove Smart Scroll Interceptor block
    content = content.replace(/\s*\/\/\s*---\s*Smart Scroll Interceptor\s*---[\s\S]*?(?=\s*return\s*\()/g, '\n\n  return (');
    
    // Remove handleWheel if no comment
    content = content.replace(/\s*const\s*handleWheel\s*=\s*useCallback[\s\S]*?(?=\s*return\s*\()/g, '\n\n  return (');
    
    // Remove ref={setTableRef}
    content = content.replace(/\s*ref=\{setTableRef\}/g, '');
    
    // Fix max heights
    if (file.includes('ProfitAndLossReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 110px\)'/g, "maxHeight: 'calc(100vh - 280px)'");
    } else if (file.includes('SearchReceipts.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 110px\)'/g, "maxHeight: 'calc(100vh - 250px)'");
    } else if (file.includes('ReceiptsReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 110px\)'/g, "maxHeight: 'calc(100vh - 180px)'");
    } else if (file.includes('InventoryMovementReport.jsx')) {
        content = content.replace(/maxHeight:\s*'calc\(100vh - 110px\)'/g, "maxHeight: 'calc(100vh - 250px)'");
        content = content.replace(/maxHeight:\s*'calc\(100vh - 220px\)'/g, "maxHeight: 'calc(100vh - 250px)'");
    }
    
    fs.writeFileSync(fullPath, content, 'utf8');
    console.log('Cleaned:', file);
});
