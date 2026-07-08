import sqlite3
import traceback

try:
    conn = sqlite3.connect('db/business_data.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    with open('db_test_output.txt', 'w') as f:
        f.write(f"Tables: {tables}\n")
        
        # Check receipts
        if ('pos_receipt',) in tables:
            cursor.execute("SELECT count(*) FROM pos_receipt")
            count = cursor.fetchone()[0]
            f.write(f"Receipt count in pos_receipt: {count}\n")
        
        # Check invoices or other tables
        if ('api_receipt',) in tables:
            cursor.execute("SELECT count(*) FROM api_receipt")
            count = cursor.fetchone()[0]
            f.write(f"Receipt count in api_receipt: {count}\n")
except Exception as e:
    with open('db_test_error.txt', 'w') as f:
        f.write(traceback.format_exc())
