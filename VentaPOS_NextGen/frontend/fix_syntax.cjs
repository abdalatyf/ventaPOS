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
    if (!fs.existsSync(fullPath)) return;
    
    let content = fs.readFileSync(fullPath, 'utf8');
    content = content.replace(/return \(\s*return \(/g, 'return (');
    fs.writeFileSync(fullPath, content, 'utf8');
});
