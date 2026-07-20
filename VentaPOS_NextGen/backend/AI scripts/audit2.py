import sqlite3

db_path = 'db/business_data.sqlite3'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("ALL TABLES:", tables)

receipt_tables = [t for t in tables if 'receipt' in t.lower()]
print("Receipt tables:", receipt_tables)

if receipt_tables:
    tbl = receipt_tables[0]
    c.execute(f"SELECT COUNT(*) FROM {tbl}")
    count = c.fetchone()[0]
    print(f"Total in {tbl}: {count}")
    
    if count > 0:
        c.execute(f"SELECT * FROM {tbl} LIMIT 3")
        cols = [desc[0] for desc in c.description]
        rows = c.fetchall()
        print("Columns:", cols)
        for r in rows:
            print(dict(zip(cols, r)))

conn.close()
print("AUDIT DONE")
