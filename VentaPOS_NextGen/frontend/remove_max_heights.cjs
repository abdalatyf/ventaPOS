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
  
  // Replace style={{ maxHeight: 'calc(...)', overflowY: 'auto' }} with style={{ overflowY: 'auto' }}
  // Or handle cases with spaces
  content = content.replace(/maxHeight:\s*'calc\(100vh - \d+px\)'\s*,\s*/g, '');
  content = content.replace(/,\s*maxHeight:\s*'calc\(100vh - \d+px\)'/g, '');
  content = content.replace(/maxHeight:\s*'calc\(100vh - \d+px\)'/g, '');
  
  fs.writeFileSync(f, content, 'utf8');
  console.log(f.split('/').pop(), 'cleaned maxHeight');
});
