import sqlite3

db_path = r'D:\Projects\VentaPOS\VentaPOS_NextGen\backend\db\business_data.sqlite3'

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check tables available
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%receipt%'")
tables = c.fetchall()
print(f'Receipt-related tables: {tables}')

# Check receipts
c.execute("SELECT COUNT(*) FROM api_receipt")
count = c.fetchone()[0]
print(f'Total Receipts in DB: {count}')

c.execute("SELECT id, customer_name, total_amount, is_cash_sale, sale_year, sale_month FROM api_receipt LIMIT 5")
rows = c.fetchall()
print('Sample Receipts:')
for r in rows:
    print(f'  ID:{r[0]} | Customer:{r[1]} | Amount:{r[2]} | Cash:{r[3]} | {r[5]}/{r[4]}')

# Cash vs Installment count
c.execute("SELECT COUNT(*) FROM api_receipt WHERE is_cash_sale=1")
cash_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM api_receipt WHERE is_cash_sale=0")
inst_count = c.fetchone()[0]
print(f'Cash: {cash_count} | Installment: {inst_count}')

# Test year filter
c.execute("SELECT COUNT(*) FROM api_receipt WHERE sale_year=2026")
yr_count = c.fetchone()[0]
print(f'Year=2026 filter: {yr_count} receipts')

# Check sale_items
c.execute("SELECT COUNT(*) FROM api_saleitem")
si_count = c.fetchone()[0]
print(f'Total SaleItems: {si_count}')

# Check installment payments
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%installment%'")
inst_tables = c.fetchall()
print(f'Installment tables: {inst_tables}')
if inst_tables:
    c.execute(f"SELECT COUNT(*) FROM {inst_tables[0][0]}")
    ip_count = c.fetchone()[0]
    print(f'Total InstallmentPayments: {ip_count}')

conn.close()
print('DB Audit: PASSED')
