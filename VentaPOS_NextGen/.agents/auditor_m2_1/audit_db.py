import os
import sys
import sqlite3
import json

# Set paths
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
BASE_DIR = r"d:\Projects\VentaPOS\VentaPOS_NextGen"
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "db", "business_data.sqlite3")

sys.path.append(BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.models import Receipt, SaleItem, InstallmentPayment, InventoryItem, Tenant
from api.utils.security_utils import generate_receipt_signature

def to_hex(uuid_str):
    return uuid_str.replace("-", "").lower()

receipt_ids = [
    "8ac76697-c805-4db9-a996-e2db42f37585",
    "e8137e9e-c93c-4922-b0cf-a0089390bda1"
]

print("=== FORENSIC DB AUDIT START ===")
print(f"DB Path: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for r_id in receipt_ids:
    hex_id = to_hex(r_id)
    print(f"\n--- Auditing Receipt ID: {r_id} (Hex: {hex_id}) ---")
    
    # 1. Direct SQLite query on receipt
    cursor.execute("SELECT * FROM receipt WHERE id=?", (hex_id,))
    row = cursor.fetchone()
    if not row:
        print(f"FAILED: Receipt {r_id} NOT FOUND in SQLite!")
        sys.exit(1)
        
    rcpt_dict = dict(row)
    print(f"Receipt SQLite Row: {json.dumps(rcpt_dict, default=str, ensure_ascii=False)}")
    
    # 2. Django ORM query on Receipt
    try:
        orm_receipt = Receipt.objects.get(id=r_id)
        print(f"Django ORM Receipt: ID={orm_receipt.id}, Number={orm_receipt.receipt_number}, Total={orm_receipt.total_amount}, IsCash={orm_receipt.is_cash_sale}")
    except Receipt.DoesNotExist:
        print(f"FAILED: Receipt {r_id} NOT FOUND in Django ORM!")
        sys.exit(1)

    # 3. Sale Items Audit
    cursor.execute("SELECT * FROM sale_item WHERE receipt_id=? AND is_deleted=0", (hex_id,))
    sale_item_rows = cursor.fetchall()
    print(f"SaleItems count in SQLite: {len(sale_item_rows)}")
    
    item_sum = 0.0
    items_for_hash = []
    for item in sale_item_rows:
        item_dict = dict(item)
        print(f"  SaleItem Row: {json.dumps(item_dict, default=str, ensure_ascii=False)}")
        subtotal = item["quantity"] * float(item["unit_price"])
        item_sum += subtotal
        
        # Get inventory item object for signature calculation
        inv_hex = item["inventory_item_id"]
        inv_item = InventoryItem.objects.get(id=inv_hex)
        items_for_hash.append({"inventory_item": inv_item, "quantity": item["quantity"]})
        
    print(f"Computed SaleItems Sum: {item_sum:.2f}, Receipt total_amount: {float(rcpt_dict['total_amount']):.2f}")
    if abs(item_sum - float(rcpt_dict["total_amount"])) > 0.001:
        print(f"FAILED: SaleItems sum ({item_sum}) != Receipt total ({rcpt_dict['total_amount']})")
        sys.exit(1)
    else:
        print("PASS: SaleItems total matches Receipt total_amount.")
        
    # 4. Installments Audit
    cursor.execute("SELECT * FROM installment_payment WHERE receipt_id=? AND is_deleted=0 ORDER BY payment_date ASC", (hex_id,))
    inst_rows = cursor.fetchall()
    print(f"InstallmentPayments count in SQLite: {len(inst_rows)}")
    inst_sum = 0.0
    for inst in inst_rows:
        inst_dict = dict(inst)
        print(f"  Installment Row: {json.dumps(inst_dict, default=str, ensure_ascii=False)}")
        inst_sum += float(inst["amount"])
        
    down_payment = float(rcpt_dict["down_payment"])
    total_amount = float(rcpt_dict["total_amount"])
    print(f"Down Payment: {down_payment:.2f}, Installments Sum: {inst_sum:.2f}, Total Amount: {total_amount:.2f}")
    if abs((down_payment + inst_sum) - total_amount) > 0.001:
        print(f"FAILED: down_payment + inst_sum ({down_payment + inst_sum}) != total_amount ({total_amount})")
        sys.exit(1)
    else:
        print("PASS: Down payment + installments sum matches total_amount.")

    # 5. HMAC-SHA256 Signature Verification
    formatted_total = f"{total_amount:.2f}"
    computed_hash = generate_receipt_signature(
        rcpt_dict["receipt_number"],
        formatted_total,
        rcpt_dict["sale_month"],
        rcpt_dict["sale_year"],
        items_data=items_for_hash
    )
    db_hash = rcpt_dict["receipt_hash"]
    print(f"DB Hash:       {db_hash}")
    print(f"Computed Hash: {computed_hash}")
    if db_hash != computed_hash:
        print("FAILED: HMAC-SHA256 Hash Mismatch!")
        sys.exit(1)
    else:
        print("PASS: HMAC-SHA256 Hash strictly matches computed signature!")

print("\n=== FORENSIC DB AUDIT PASSED 100% ===")
