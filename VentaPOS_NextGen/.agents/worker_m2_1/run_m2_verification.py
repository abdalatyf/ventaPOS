import os
import sys
import json
import sqlite3
import requests

# Reconfigure stdout/stderr to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Paths & Settings
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "db", "business_data.sqlite3")
WORKER_DIR = os.path.dirname(__file__)
TEST_RESULTS_PATH = os.path.join(WORKER_DIR, "test_results.md")

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

results_log = []

def log(msg, level="INFO"):
    formatted = f"[{level}] {msg}"
    print(formatted)
    results_log.append(formatted)

def to_hex_uuid(val):
    if not val:
        return ""
    return str(val).replace("-", "")

log("=====================================================================")
log("VentaPOS NextGen - M2 POS Receipt Entry End-to-End Verification Suite")
log("=====================================================================")

# Step 1: Environment Setup & API/UI Server Verification
log("\n--- TASK 1: Environment Setup & Server Verification ---")
try:
    res = requests.get(f"{BASE_URL}/product-suggestions/", headers=HEADERS, params={"term": "كبة", "branch_id": "1", "month": "7", "year": "2026"})
    if res.status_code == 200:
        log("✅ Backend API Server is UP and processing requests at http://127.0.0.1:8000/api/v1/ (HTTP 200)")
    else:
        log(f"❌ Backend API Server returned unexpected status {res.status_code}: {res.text}", level="ERROR")
except Exception as e:
    log(f"❌ Failed to connect to Backend API Server: {e}", level="ERROR")
    sys.exit(1)

# Step 2: R1. UI & API Autocomplete / Functional Testing
log("\n--- TASK 2: R1. UI & API Autocomplete / Functional Testing ---")

# 2.1 Product Autocomplete
log("\n[R1.1] Testing Product Autocomplete (GET /api/v1/product-suggestions/)")
params_prod = {"term": "كبة", "branch_id": "1", "month": "7", "year": "2026"}
res_prod = requests.get(f"{BASE_URL}/product-suggestions/", headers=HEADERS, params=params_prod)
log(f"Request: GET /api/v1/product-suggestions/?term=كبة&branch_id=1&month=7&year=2026")
log(f"Response Status: {res_prod.status_code}")
log(f"Response Body: {json.dumps(res_prod.json(), ensure_ascii=False)}")

assert res_prod.status_code == 200, f"Expected 200, got {res_prod.status_code}"
prod_data = res_prod.json()
assert isinstance(prod_data, list), "Expected list output"
assert len(prod_data) > 0, "Expected at least 1 matching product for 'كبة'"
match_prod = next((p for p in prod_data if "كبة" in p["value"]), None)
assert match_prod is not None, "Product 'كبة' not found in suggestions"
log(f"✅ Product Autocomplete passed: Found '{match_prod['value']}' (ID: {match_prod['id']}, Max Stock: {match_prod['max']})")

# 2.2 Customer Autocomplete
log("\n[R1.2] Testing Customer Autocomplete (GET /api/v1/customer-suggestions/)")
params_cust = {"term": "أحمد", "field": "name"}
res_cust = requests.get(f"{BASE_URL}/customer-suggestions/", headers=HEADERS, params=params_cust)
log(f"Request: GET /api/v1/customer-suggestions/?term=أحمد&field=name")
log(f"Response Status: {res_cust.status_code}")
log(f"Response Body: {json.dumps(res_cust.json(), ensure_ascii=False)}")

assert res_cust.status_code == 200, f"Expected 200, got {res_cust.status_code}"
cust_data = res_cust.json()
assert isinstance(cust_data, list), "Expected list output"
log(f"✅ Customer Autocomplete passed: Returned {len(cust_data)} suggestions")

# 2.3 Cash Sale Toggle Logic Test
log("\n[R1.3] Testing Cash Sale Toggle Logic (is_cash_sale: true defaulting)")
tenant_obj = Tenant.objects.get(company_code=COMPANY_CODE)
branch_obj = Branch.objects.filter(tenant=tenant_obj).first()
salesperson_obj = Salesperson.objects.filter(tenant=tenant_obj).first()
kebba_item = InventoryItem.objects.get(tenant=tenant_obj, name="كبة")

cash_toggle_payload = {
    "branch": str(branch_obj.id),
    "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
    "customer_name": "",
    "total_amount": 150.00,
    "down_payment": 150.00,
    "is_cash_sale": True,
    "sale_year": 2026,
    "sale_month": 7,
    "sale_items": [
        {
            "inventory_item": str(kebba_item.id),
            "quantity": 1,
            "unit_price": 150.00
        }
    ]
}
res_toggle = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=cash_toggle_payload)
log(f"Response Status: {res_toggle.status_code}")
log(f"Response Body: {json.dumps(res_toggle.json(), ensure_ascii=False)}")
assert res_toggle.status_code == 201, f"Expected 201, got {res_toggle.status_code}"
toggle_data = res_toggle.json()
assert toggle_data["customer_name"] == "عميل نقدي", f"Expected 'عميل نقدي', got {toggle_data['customer_name']}"
assert float(toggle_data["down_payment"]) == float(toggle_data["total_amount"]), "Expected down_payment == total_amount for cash sale"
assert len(toggle_data.get("installment_payments", [])) == 0, "Expected empty installments for cash sale"
log("✅ Cash Sale Toggle logic verified: customer_name='عميل نقدي', down_payment=total_amount, empty installments")


# Step 3: R2. End-to-End Submission Testing
log("\n--- TASK 3: R2. End-to-End Submission Testing ---")

# 3.1 Cash Sale Flow
log("\n[R2.1] Submitting End-to-End Cash Sale Receipt")
cash_sale_payload = {
    "branch": str(branch_obj.id),
    "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
    "customer_name": "عميل نقدي",
    "total_amount": 300.00,
    "down_payment": 300.00,
    "is_cash_sale": True,
    "sale_year": 2026,
    "sale_month": 7,
    "sale_items": [
        {
            "inventory_item": str(kebba_item.id),
            "quantity": 2,
            "unit_price": 150.00
        }
    ]
}
res_cash = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=cash_sale_payload)
log(f"Request Payload: {json.dumps(cash_sale_payload, ensure_ascii=False)}")
log(f"Response Status: {res_cash.status_code}")
log(f"Response Body: {json.dumps(res_cash.json(), ensure_ascii=False)}")
assert res_cash.status_code == 201, f"Expected 201, got {res_cash.status_code}"
cash_receipt_res = res_cash.json()
cash_receipt_id = cash_receipt_res["id"]
log(f"✅ Cash Sale Receipt created successfully! ID: {cash_receipt_id}")

# 3.2 Installment Sale Flow
log("\n[R2.2] Submitting End-to-End Installment Sale Receipt")
inst_sale_payload = {
    "branch": str(branch_obj.id),
    "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
    "customer_name": "محمد السيد أحمد",
    "phone_number": "01098765432",
    "address": "شارع مصطفى النحاس",
    "area": "مدينة نصر",
    "total_amount": 600.00,
    "down_payment": 200.00,
    "is_cash_sale": False,
    "sale_year": 2026,
    "sale_month": 7,
    "sale_items": [
        {
            "inventory_item": str(kebba_item.id),
            "quantity": 4,
            "unit_price": 150.00
        }
    ],
    "installment_payments": [
        {
            "amount": 200.00,
            "payment_month": 8,
            "payment_year": 2026
        },
        {
            "amount": 200.00,
            "payment_month": 9,
            "payment_year": 2026
        }
    ]
}
res_inst = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=inst_sale_payload)
log(f"Request Payload: {json.dumps(inst_sale_payload, ensure_ascii=False)}")
log(f"Response Status: {res_inst.status_code}")
log(f"Response Body: {json.dumps(res_inst.json(), ensure_ascii=False)}")
assert res_inst.status_code == 201, f"Expected 201, got {res_inst.status_code}"
inst_receipt_res = res_inst.json()
inst_receipt_id = inst_receipt_res["id"]
log(f"✅ Installment Sale Receipt created successfully! ID: {inst_receipt_id}")

# 3.3 Verify Calculation Logic
log("\n[R2.3] Verifying Calculation Logic")

# Cash Sale Calculations
cash_subtotal = sum(item["quantity"] * float(item["unit_price"]) for item in cash_receipt_res["sale_items"])
assert cash_subtotal == float(cash_receipt_res["total_amount"]), "Cash subtotal does not match total_amount"
log(f"✅ Cash Sale Subtotal Verification: sum(items)={cash_subtotal} == total_amount={cash_receipt_res['total_amount']}")

# Installment Sale Calculations
inst_subtotal = sum(item["quantity"] * float(item["unit_price"]) for item in inst_receipt_res["sale_items"])
assert inst_subtotal == float(inst_receipt_res["total_amount"]), "Installment subtotal does not match total_amount"
log(f"✅ Installment Sale Subtotal Verification: sum(items)={inst_subtotal} == total_amount={inst_receipt_res['total_amount']}")

down_pmt = float(inst_receipt_res["down_payment"])
tot_amt = float(inst_receipt_res["total_amount"])
balance_due = tot_amt - down_pmt
installments_sum = sum(float(inst["amount"]) for inst in inst_receipt_res["installment_payments"])
assert installments_sum == balance_due, f"Installments sum ({installments_sum}) != balance due ({balance_due})"
log(f"✅ Down Payment Deduction & Installments Sum Verification: down_payment ({down_pmt}) + installments_sum ({installments_sum}) == total_amount ({tot_amt})")

# Installment Start Date Shifting Rule (sale_month + 1, 25th of month YYYY-MM-25)
first_inst = inst_receipt_res["installment_payments"][0]
first_inst_date = first_inst["payment_date"]
expected_first_date = "2026-08-25" # sale_month=7 -> 7+1=8 -> 2026-08-25
assert first_inst_date == expected_first_date, f"Expected first installment date '{expected_first_date}', got '{first_inst_date}'"
log(f"✅ Installment Date Shifting Rule Verified: sale_month=7 -> first installment date shifted to '{first_inst_date}' (25th of month YYYY-MM-25)")


# Step 4: R3. Backend Data Integrity Verification
log("\n--- TASK 4: R3. Backend Data Integrity Verification (Direct SQLite Queries) ---")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cash_hex_id = to_hex_uuid(cash_receipt_id)
inst_hex_id = to_hex_uuid(inst_receipt_id)
tenant_hex_id = to_hex_uuid(tenant_obj.id)

# 4.1 Query Receipt records directly
log("\n[R3.1] Querying SQLite table 'receipt'")
cursor.execute("SELECT * FROM receipt WHERE id IN (?, ?)", (cash_hex_id, inst_hex_id))
db_receipts = {row["id"]: row for row in cursor.fetchall()}

assert cash_hex_id in db_receipts, f"Cash Receipt ID {cash_hex_id} not found in SQLite"
assert inst_hex_id in db_receipts, f"Installment Receipt ID {inst_hex_id} not found in SQLite"

db_cash_rcpt = db_receipts[cash_hex_id]
db_inst_rcpt = db_receipts[inst_hex_id]

log(f"Direct SQLite Cash Receipt: Number={db_cash_rcpt['receipt_number']}, Total={db_cash_rcpt['total_amount']}, Hash={db_cash_rcpt['receipt_hash']}, TenantID={db_cash_rcpt['tenant_id']}")
log(f"Direct SQLite Installment Receipt: Number={db_inst_rcpt['receipt_number']}, Total={db_inst_rcpt['total_amount']}, Hash={db_inst_rcpt['receipt_hash']}, TenantID={db_inst_rcpt['tenant_id']}")

# 4.2 Query SaleItem records directly
log("\n[R3.2] Querying SQLite table 'sale_item'")
cursor.execute("SELECT * FROM sale_item WHERE receipt_id IN (?, ?) AND is_deleted=0", (cash_hex_id, inst_hex_id))
db_sale_items = cursor.fetchall()

cash_items_db = [item for item in db_sale_items if item["receipt_id"] == cash_hex_id]
inst_items_db = [item for item in db_sale_items if item["receipt_id"] == inst_hex_id]

assert len(cash_items_db) == 1, "Expected 1 sale item for cash receipt"
assert len(inst_items_db) == 1, "Expected 1 sale item for installment receipt"

# Verify exact mathematical totals
cash_item_sum = sum(item["quantity"] * float(item["unit_price"]) for item in cash_items_db)
assert cash_item_sum == float(db_cash_rcpt["total_amount"]), "Cash DB sum(items) != receipt total_amount"
log(f"✅ Direct SQLite Math Totals (Cash Receipt): sum(quantity * unit_price) = {cash_item_sum} == Receipt.total_amount ({db_cash_rcpt['total_amount']})")

inst_item_sum = sum(item["quantity"] * float(item["unit_price"]) for item in inst_items_db)
assert inst_item_sum == float(db_inst_rcpt["total_amount"]), "Installment DB sum(items) != receipt total_amount"
log(f"✅ Direct SQLite Math Totals (Installment Receipt): sum(quantity * unit_price) = {inst_item_sum} == Receipt.total_amount ({db_inst_rcpt['total_amount']})")

# 4.3 Query InstallmentPayment records directly
log("\n[R3.3] Querying SQLite table 'installment_payment'")
cursor.execute("SELECT * FROM installment_payment WHERE receipt_id=? AND is_deleted=0 ORDER BY payment_date ASC", (inst_hex_id,))
db_installments = cursor.fetchall()

assert len(db_installments) == 2, f"Expected 2 installment payments in DB, got {len(db_installments)}"
db_inst_sum = sum(float(inst["amount"]) for inst in db_installments)
db_down_pmt = float(db_inst_rcpt["down_payment"])
db_total_amt = float(db_inst_rcpt["total_amount"])

assert db_down_pmt + db_inst_sum == db_total_amt, f"DB down_payment ({db_down_pmt}) + sum(installments) ({db_inst_sum}) != total_amount ({db_total_amt})"
log(f"✅ Direct SQLite Installment Totals: down_payment ({db_down_pmt}) + sum(InstallmentPayment.amount) ({db_inst_sum}) == Receipt.total_amount ({db_total_amt})")

# 4.4 Verify receipt_hash HMAC-SHA256
log("\n[R3.4] Verifying HMAC-SHA256 receipt_hash generation")
cash_items_for_hash = [{"inventory_item": kebba_item, "quantity": item["quantity"]} for item in cash_items_db]
cash_formatted_total = f"{float(db_cash_rcpt['total_amount']):.2f}"
expected_cash_hash = generate_receipt_signature(
    db_cash_rcpt["receipt_number"],
    cash_formatted_total,
    db_cash_rcpt["sale_month"],
    db_cash_rcpt["sale_year"],
    items_data=cash_items_for_hash
)
assert db_cash_rcpt["receipt_hash"] == expected_cash_hash, f"Hash mismatch for cash receipt! Expected {expected_cash_hash}, got {db_cash_rcpt['receipt_hash']}"
log(f"✅ Direct SQLite Cash Receipt Hash Verified: HMAC-SHA256 match ({db_cash_rcpt['receipt_hash']})")

inst_items_for_hash = [{"inventory_item": kebba_item, "quantity": item["quantity"]} for item in inst_items_db]
inst_formatted_total = f"{float(db_inst_rcpt['total_amount']):.2f}"
expected_inst_hash = generate_receipt_signature(
    db_inst_rcpt["receipt_number"],
    inst_formatted_total,
    db_inst_rcpt["sale_month"],
    db_inst_rcpt["sale_year"],
    items_data=inst_items_for_hash
)
assert db_inst_rcpt["receipt_hash"] == expected_inst_hash, f"Hash mismatch for installment receipt! Expected {expected_inst_hash}, got {db_inst_rcpt['receipt_hash']}"
log(f"✅ Direct SQLite Installment Receipt Hash Verified: HMAC-SHA256 match ({db_inst_rcpt['receipt_hash']})")

# 4.5 Verify Tenant Isolation
log("\n[R3.5] Verifying Tenant Isolation")
assert str(db_cash_rcpt["tenant_id"]) == tenant_hex_id, f"Cash Receipt tenant_id mismatch: expected {tenant_hex_id}, got {db_cash_rcpt['tenant_id']}"
assert str(db_inst_rcpt["tenant_id"]) == tenant_hex_id, f"Installment Receipt tenant_id mismatch: expected {tenant_hex_id}, got {db_inst_rcpt['tenant_id']}"

for item in cash_items_db + inst_items_db:
    assert str(item["tenant_id"]) == tenant_hex_id, f"SaleItem tenant_id mismatch: expected {tenant_hex_id}, got {item['tenant_id']}"

for inst in db_installments:
    assert str(inst["tenant_id"]) == tenant_hex_id, f"InstallmentPayment tenant_id mismatch: expected {tenant_hex_id}, got {inst['tenant_id']}"

log(f"✅ Tenant Isolation Verified: All created Receipt, SaleItem, and InstallmentPayment records are strictly bound to tenant_id '{tenant_hex_id}' (Company Code '1234')")

conn.close()

log("\n=====================================================================")
log("ALL TEST CASES PASSED WITH 100% INTEGRITY AND VERIFICATION!")
log("=====================================================================")

# Write full log to test_results.md
with open(TEST_RESULTS_PATH, "w", encoding="utf-8") as f:
    f.write("# VentaPOS NextGen - POS Entry (Add Receipt) Screen Testing Report\n\n")
    f.write(f"**Execution Date**: 2026-07-04\n")
    f.write(f"**Target Host**: http://127.0.0.1:8000/api/v1/\n")
    f.write(f"**Database**: {DB_PATH}\n")
    f.write(f"**Company Code Header**: X-Company-Code: 1234\n\n")
    f.write("## Execution Summary\n\n")
    f.write("| Test Phase | Status | Details |\n")
    f.write("| --- | --- | --- |\n")
    f.write("| **Backend API Server Check** | ✅ PASSED | Server running and processing HTTP requests |\n")
    f.write("| **R1.1 Product Autocomplete** | ✅ PASSED | Returned product 'كبة' with max stock |\n")
    f.write("| **R1.2 Customer Autocomplete** | ✅ PASSED | Returned customer suggestions list |\n")
    f.write("| **R1.3 Cash Sale Toggle Logic** | ✅ PASSED | Auto-defaulted customer_name='عميل نقدي', down_payment=total_amount |\n")
    f.write("| **R2.1 Cash Sale Flow** | ✅ PASSED | Submitted receipt, HTTP 201 Created |\n")
    f.write("| **R2.2 Installment Sale Flow** | ✅ PASSED | Submitted receipt with schedule, HTTP 201 Created |\n")
    f.write("| **R2.3 Calculation Logic** | ✅ PASSED | Verified subtotal, down payment, installment sum, 25th day date shift |\n")
    f.write("| **R3.1 Direct SQLite Querying** | ✅ PASSED | Verified Receipt records in business_data.sqlite3 |\n")
    f.write("| **R3.2 Direct SQLite SaleItems** | ✅ PASSED | Verified SaleItem records and exact sum(qty * unit_price) |\n")
    f.write("| **R3.3 Direct SQLite Installments** | ✅ PASSED | Verified InstallmentPayment records and down_pmt + sum(inst) == total |\n")
    f.write("| **R3.4 HMAC-SHA256 Hash Integrity** | ✅ PASSED | Verified receipt_hash matches generate_receipt_signature |\n")
    f.write("| **R3.5 Tenant Isolation** | ✅ PASSED | Confirmed all records bound to tenant_id (Company Code '1234') |\n\n")
    f.write("## Detailed Verification Execution Logs\n\n```log\n")
    f.write("\n".join(results_log))
    f.write("\n```\n")

print(f"\nSaved test results log to: {TEST_RESULTS_PATH}")
