import sqlite3

db_path = r'D:\exe\venta_pos\Backup_SalesApp_2026-05-24.sqlite3'
out_path = r'D:\exe\venta_pos\db_analysis_output.txt'

try:
    with open(out_path, 'w', encoding='utf-8') as f:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        f.write('--- Branch ---\n')
        cur.execute("SELECT * FROM salesapp_branch;")
        f.write(str(cur.fetchall()) + '\n')
        
        f.write('\n--- Products (InventoryItem) ---\n')
        # Use PRAGMA to get columns
        cur.execute("PRAGMA table_info(salesapp_inventoryitem);")
        columns = [col[1] for col in cur.fetchall()]
        f.write("Columns: " + str(columns) + '\n')
        
        if 'purchase_price' in columns:
            cur.execute("SELECT name, quantity, purchase_price, salesperson_commission_amount FROM salesapp_inventoryitem;")
        elif 'initial_purchase_price' in columns:
            cur.execute("SELECT name, initial_quantity, initial_purchase_price, initial_commission_amount FROM salesapp_inventoryitem;")
        f.write(str(cur.fetchall()) + '\n')
        
        f.write('\n--- Receipts count by month ---\n')
        cur.execute("SELECT sale_year, sale_month, COUNT(*) FROM salesapp_receipt GROUP BY sale_year, sale_month ORDER BY sale_year, sale_month;")
        f.write(str(cur.fetchall()) + '\n')
        
        f.write('\n--- Cash vs Installment ---\n')
        cur.execute("SELECT is_cash_sale, COUNT(*) FROM salesapp_receipt GROUP BY is_cash_sale;")
        f.write(str(cur.fetchall()) + '\n')
        
        conn.close()
except Exception as e:
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(f"\nError: {e}\n")
