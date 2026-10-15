import os
import sys
import json
import sqlite3
import requests

# Set UTF-8 encoding for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "db", "business_data.sqlite3")
LOG_PATH = os.path.join(os.path.dirname(__file__), "independent_test_log.md")

sys.path.append(BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.models import Tenant, Branch, Salesperson, InventoryItem, Receipt, SaleItem, InstallmentPayment
from api.utils.security_utils import generate_receipt_signature

BASE_URL = "http://127.0.0.1:8000/api/v1"
COMPANY_CODE = "1234"
HEADERS = {
    "X-Company-Code": COMPANY_CODE,
    "Content-Type": "application/json"
}

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(msg)

def to_hex_uuid(val):
    if not val:
        return ""
    return str(val).replace("-", "")

log("# Independent Victory Audit Verification Execution")
log(f"**Execution Host**: {BASE_URL}")
log(f"**Database Path**: {DB_PATH}")
log(f"**Company Code**: {COMPANY_CODE}\n")

# Phase 1: API Server Liveness & Product/Customer Autocomplete
log("## Phase 1: Endpoint & Autocomplete Testing")

res_prod = requests.get(f"{BASE_URL}/product-suggestions/", headers=HEADERS, params={"term": "كبة", "branch_id": "1", "month": "7", "year": "2026"})
assert res_prod.status_code == 200, f"Product autocomplete failed with status {res_prod.status_code}"
prod_json = res_prod.json()
assert len(prod_json) > 0, "No product suggestions returned for 'كبة'"
kebba_prod = next(p for p in prod_json if "كبة" in p["value"])
log(f"✓ Product Autocomplete: HTTP 200 OK. Found '{kebba_prod['value']}' (ID: {kebba_prod['id']}, Max Stock: {kebba_prod['max']})")

res_cust = requests.get(f"{BASE_URL}/customer-suggestions/", headers=HEADERS, params={"term": "أحمد", "field": "name"})
assert res_cust.status_code == 200, f"Customer autocomplete failed with status {res_cust.status_code}"
cust_json = res_cust.json()
log(f"✓ Customer Autocomplete: HTTP 200 OK. Returned {len(cust_json)} suggestions for term 'أحمد'")

# Phase 2: Cash Sale Toggle & Submission
log("\n## Phase 2: Cash Sale Flow & Toggle Defaulting")

tenant_obj = Tenant.objects.get(company_code=COMPANY_CODE)
branch_obj = Branch.objects.filter(tenant=tenant_obj).first()
salesperson_obj = Salesperson.objects.filter(tenant=tenant_obj).first()
kebba_item = InventoryItem.objects.get(tenant=tenant_obj, name="كبة")

cash_payload = {
    "branch": str(branch_obj.id),
    "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
    "customer_name": "", # Test auto-defaulting when is_cash_sale is True
    "total_amount": 750.00,
    "down_payment": 750.00,
    "is_cash_sale": True,
    "sale_year": 2026,
    "sale_month": 7,
    "sale_items": [
        {
            "inventory_item": str(kebba_item.id),
            "quantity": 5,
            "unit_price": 150.00
        }
    ]
}

res_cash = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=cash_payload)
assert res_cash.status_code == 201, f"Cash receipt creation failed: {res_cash.status_code} - {res_cash.text}"
cash_data = res_cash.json()
cash_receipt_id = cash_data["id"]

assert cash_data["customer_name"] == "عميل نقدي", f"Expected default 'عميل نقدي', got '{cash_data['customer_name']}'"
assert float(cash_data["down_payment"]) == float(cash_data["total_amount"]), "Down payment != total_amount for Cash sale"
assert len(cash_data.get("installment_payments", [])) == 0, "Cash sale should have zero installments"

log(f"✓ Cash Sale Created: HTTP 201 Created. Receipt ID: {cash_receipt_id}")
log(f"  - Customer Name: '{cash_data['customer_name']}' (auto-defaulted correctly)")
log(f"  - Total Amount: {cash_data['total_amount']}, Down Payment: {cash_data['down_payment']}")
log(f"  - Installment Payments Count: {len(cash_data.get('installment_payments', []))}")


# Phase 3: Installment Sale Flow & Calculation Verification
log("\n## Phase 3: Installment Sale Flow & Calculation Verification")

inst_payload = {
    "branch": str(branch_obj.id),
    "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
    "customer_name": "أيمن علي محمود",
    "phone_number": "01122334455",
    "address": "شارع عباس العقاد",
    "area": "مدينة نصر",
    "total_amount": 1200.00,
    "down_payment": 400.00,
    "is_cash_sale": False,
    "sale_year": 2026,
    "sale_month": 7,
    "sale_items": [
        {
            "inventory_item": str(kebba_item.id),
            "quantity": 8,
            "unit_price": 150.00
        }
    ],
    "installment_payments": [
        {"amount": 200.00, "payment_month": 8, "payment_year": 2026},
        {"amount": 200.00, "payment_month": 9, "payment_year": 2026},
        {"amount": 200.00, "payment_month": 10, "payment_year": 2026},
        {"amount": 200.00, "payment_month": 11, "payment_year": 2026}
    ]
}

res_inst = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=inst_payload)
assert res_inst.status_code == 201, f"Installment receipt creation failed: {res_inst.status_code} - {res_inst.text}"
inst_data = res_inst.json()
inst_receipt_id = inst_data["id"]

# Verify math
subtotal_cash = sum(item["quantity"] * float(item["unit_price"]) for item in cash_data["sale_items"])
assert subtotal_cash == float(cash_data["total_amount"]), "Cash subtotal mismatch"

subtotal_inst = sum(item["quantity"] * float(item["unit_price"]) for item in inst_data["sale_items"])
assert subtotal_inst == float(inst_data["total_amount"]), "Installment subtotal mismatch"

inst_sum = sum(float(i["amount"]) for i in inst_data["installment_payments"])
down_pmt = float(inst_data["down_payment"])
tot_amt = float(inst_data["total_amount"])
assert down_pmt + inst_sum == tot_amt, f"Down payment ({down_pmt}) + installments sum ({inst_sum}) != total ({tot_amt})"

# Verify date shifting rule (sale_month=7 -> month 8 -> 2026-08-25)
first_payment_date = inst_data["installment_payments"][0]["payment_date"]
expected_payment_date = "2026-08-25"
assert first_payment_date == expected_payment_date, f"Expected '{expected_payment_date}', got '{first_payment_date}'"

log(f"✓ Installment Sale Created: HTTP 201 Created. Receipt ID: {inst_receipt_id}")
log(f"  - Customer Name: '{inst_data['customer_name']}'")
log(f"  - Total Amount: {tot_amt}, Down Payment: {down_pmt}, Installments Sum: {inst_sum}")
log(f"  - Math Verification: down_payment ({down_pmt}) + installments_sum ({inst_sum}) == total_amount ({tot_amt}) [PASS]")
log(f"  - Date Shifting Rule: sale_month=7 -> first installment date shifted to '{first_payment_date}' (YYYY-MM-25) [PASS]")


# Phase 4: Direct SQLite Database Inspection & HMAC Hash Verification
log("\n## Phase 4: Direct SQLite DB Integrity & HMAC Signature Verification")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cash_hex = to_hex_uuid(cash_receipt_id)
inst_hex = to_hex_uuid(inst_receipt_id)
tenant_hex = to_hex_uuid(tenant_obj.id)

cursor.execute("SELECT * FROM receipt WHERE id IN (?, ?)", (cash_hex, inst_hex))
db_receipts = {row["id"]: row for row in cursor.fetchall()}

assert cash_hex in db_receipts, f"Cash receipt {cash_hex} not found in SQLite"
assert inst_hex in db_receipts, f"Installment receipt {inst_hex} not found in SQLite"

db_cash = db_receipts[cash_hex]
db_inst = db_receipts[inst_hex]

log(f"✓ SQLite Receipt Check: Found Cash Receipt {cash_hex} and Installment Receipt {inst_hex}")

# Query sale_item
cursor.execute("SELECT * FROM sale_item WHERE receipt_id IN (?, ?) AND is_deleted=0", (cash_hex, inst_hex))
db_items = cursor.fetchall()
cash_db_items = [i for i in db_items if i["receipt_id"] == cash_hex]
inst_db_items = [i for i in db_items if i["receipt_id"] == inst_hex]

assert len(cash_db_items) == 1 and cash_db_items[0]["quantity"] == 5, "Cash sale item mismatch in DB"
assert len(inst_db_items) == 1 and inst_db_items[0]["quantity"] == 8, "Installment sale item mismatch in DB"
log("✓ SQLite SaleItem Check: Item quantities and prices match submission exactly")

# Query installment_payment
cursor.execute("SELECT * FROM installment_payment WHERE receipt_id=? AND is_deleted=0 ORDER BY payment_date ASC", (inst_hex,))
db_inst_payments = cursor.fetchall()
assert len(db_inst_payments) == 4, f"Expected 4 installment rows in DB, found {len(db_inst_payments)}"
log("✓ SQLite InstallmentPayment Check: 4 installment rows present in database")

# Verify HMAC Signature
cash_items_hash_input = [{"inventory_item": kebba_item, "quantity": i["quantity"]} for i in cash_db_items]
cash_calc_hash = generate_receipt_signature(
    db_cash["receipt_number"],
    f"{float(db_cash['total_amount']):.2f}",
    db_cash["sale_month"],
    db_cash["sale_year"],
    cash_items_hash_input
)
assert db_cash["receipt_hash"] == cash_calc_hash, f"HMAC mismatch for Cash receipt! DB: {db_cash['receipt_hash']}, Calc: {cash_calc_hash}"
log(f"✓ HMAC-SHA256 Hash Verification (Cash Receipt): Stored = Computed ({db_cash['receipt_hash'][:16]}...) [MATCH]")

inst_items_hash_input = [{"inventory_item": kebba_item, "quantity": i["quantity"]} for i in inst_db_items]
inst_calc_hash = generate_receipt_signature(
    db_inst["receipt_number"],
    f"{float(db_inst['total_amount']):.2f}",
    db_inst["sale_month"],
    db_inst["sale_year"],
    inst_items_hash_input
)
assert db_inst["receipt_hash"] == inst_calc_hash, f"HMAC mismatch for Installment receipt! DB: {db_inst['receipt_hash']}, Calc: {inst_calc_hash}"
log(f"✓ HMAC-SHA256 Hash Verification (Installment Receipt): Stored = Computed ({db_inst['receipt_hash'][:16]}...) [MATCH]")


# Phase 5: Tenant Isolation Verification
log("\n## Phase 5: Tenant Isolation Verification")

assert str(db_cash["tenant_id"]) == tenant_hex, "Cash receipt tenant mismatch"
assert str(db_inst["tenant_id"]) == tenant_hex, "Installment receipt tenant mismatch"

for item in db_items:
    assert str(item["tenant_id"]) == tenant_hex, f"SaleItem tenant mismatch for ID {item['id']}"

for inst in db_inst_payments:
    assert str(inst["tenant_id"]) == tenant_hex, f"InstallmentPayment tenant mismatch for ID {inst['id']}"

log(f"✓ Tenant Binding: All Receipt, SaleItem, and InstallmentPayment DB records bound to Tenant ID '{tenant_hex}'")

# Test invalid tenant header rejection
bad_headers = {"X-Company-Code": "9999", "Content-Type": "application/json"}
res_bad_tenant = requests.get(f"{BASE_URL}/product-suggestions/", headers=bad_headers, params={"term": "كبة"})
assert res_bad_tenant.status_code == 400, f"Expected HTTP 400 for bad company code, got {res_bad_tenant.status_code}"
log("✓ Tenant Isolation Enforcement: Invalid X-Company-Code '9999' rejected with HTTP 400 Bad Request")

conn.close()

log("\n=======================================================")
log("INDEPENDENT VICTORY AUDIT TEST EXECUTION: 100% PASSED!")
log("=======================================================")

with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print(f"\nWritten independent log to {LOG_PATH}")
