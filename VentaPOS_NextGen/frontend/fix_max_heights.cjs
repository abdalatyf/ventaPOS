const fs = require('fs');
const files = [
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/SearchReceipts.jsx',
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/reports/ExpensesReport.jsx',
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/reports/InstallmentsReport.jsx',
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/reports/ProfitAndLossReport.jsx',
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/reports/ReceiptsReport.jsx',
  'd:/Projects/VentaPOS/VentaPOS_NextGen/frontend/src/pages/reports/InventoryMovementReport.jsx'
];

files.forEach(f => {
  let content = fs.readFileSync(f, 'utf8');
  const hasSticky = content.includes('sticky-toolbar');
  
  const expectedHeight = hasSticky ? "maxHeight: 'calc(100vh - 110px)'" : "maxHeight: 'calc(100vh - 65px)'";
  
  // Replace any existing maxHeight calc(100vh - ...)
  content = content.replace(/maxHeight:\s*'calc\(100vh - \d+px\)'/g, expectedHeight);
  
  fs.writeFileSync(f, content, 'utf8');
  console.log(f.split('/').pop(), '-> updated to', expectedHeight);
});
