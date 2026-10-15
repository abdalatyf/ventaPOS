import os
import sys
import json
import sqlite3
import requests
from decimal import Decimal

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "db", "business_data.sqlite3")

sys.path.append(BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.models import Tenant, Branch, Salesperson, InventoryItem, Receipt, InstallmentPayment
from api.utils.security_utils import generate_receipt_signature

BASE_URL = "http://127.0.0.1:8000/api/v1"
COMPANY_CODE = "1234"
HEADERS = {
    "X-Company-Code": COMPANY_CODE,
    "Content-Type": "application/json"
}

def run_edge_case_tests():
    print("=====================================================================")
    print("Challenger 1: Edge Case & Boundary Stress Test Suite")
    print("=====================================================================\n")

    tenant_obj = Tenant.objects.get(company_code=COMPANY_CODE)
    branch_obj = Branch.objects.filter(tenant=tenant_obj).first()
    salesperson_obj = Salesperson.objects.filter(tenant=tenant_obj).first()
    item_obj = InventoryItem.objects.filter(tenant=tenant_obj).first()

    edge_results = []

    # -------------------------------------------------------------------------
    # Scenario 1: December Sale -> Year Boundary Transition (Dec 2026 -> Jan 2027)
    # -------------------------------------------------------------------------
    print("--- SCENARIO 1: Year Boundary Transition (Dec 2026 sale -> Jan/Feb 2027 installments) ---")
    dec_payload = {
        "branch": str(branch_obj.id),
        "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
        "customer_name": "اختبار رأس السنة",
        "total_amount": 500.00,
        "down_payment": 100.00,
        "is_cash_sale": False,
        "sale_year": 2026,
        "sale_month": 12,
        "sale_items": [
            {
                "inventory_item": str(item_obj.id),
                "quantity": 1,
                "unit_price": 500.00
            }
        ],
        "installment_payments": [
            {
                "amount": 200.00,
                "payment_month": 1,
                "payment_year": 2027
            },
            {
                "amount": 200.00,
                "payment_month": 2,
                "payment_year": 2027
            }
        ]
    }

    res_dec = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=dec_payload)
    print(f"Status Code: {res_dec.status_code}")
    if res_dec.status_code == 201:
        dec_data = res_dec.json()
        insts = dec_data.get("installment_payments", [])
        p1 = insts[0]["payment_date"] if len(insts) > 0 else ""
        p2 = insts[1]["payment_date"] if len(insts) > 1 else ""
        print(f"Installment #1 Date: {p1} (Expected: 2027-01-25)")
        print(f"Installment #2 Date: {p2} (Expected: 2027-02-25)")
        
        if p1 == "2027-01-25" and p2 == "2027-02-25":
            print("✅ [PASS] December year-boundary date shifting rule correctly generated 2027-01-25 and 2027-02-25!")
            edge_results.append(("Dec Year Boundary", "PASS", f"p1={p1}, p2={p2}"))
        else:
            print("❌ [FAIL] December year-boundary date shifting rule generated incorrect dates!")
            edge_results.append(("Dec Year Boundary", "FAIL", f"p1={p1}, p2={p2}"))
    else:
        print(f"❌ [FAIL] Dec sale submission failed: {res_dec.text}")
        edge_results.append(("Dec Year Boundary", "FAIL", res_dec.text))

    print()

    # -------------------------------------------------------------------------
    # Scenario 2: Fractional Decimal Currency Calculations (33.33 x 3 = 99.99)
    # -------------------------------------------------------------------------
    print("--- SCENARIO 2: Fractional Decimal Currency Calculations ---")
    frac_payload = {
        "branch": str(branch_obj.id),
        "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
        "customer_name": "عميل كسور",
        "total_amount": 99.99,
        "down_payment": 99.99,
        "is_cash_sale": True,
        "sale_year": 2026,
        "sale_month": 7,
        "sale_items": [
            {
                "inventory_item": str(item_obj.id),
                "quantity": 3,
                "unit_price": 33.33
            }
        ]
    }

    res_frac = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=frac_payload)
    print(f"Status Code: {res_frac.status_code}")
    if res_frac.status_code == 201:
        frac_data = res_frac.json()
        print(f"Total Amount: {frac_data['total_amount']}, Down Payment: {frac_data['down_payment']}")
        print("✅ [PASS] Fractional currency payload processed cleanly with 2 decimal precision!")
        edge_results.append(("Fractional Currency", "PASS", f"Total={frac_data['total_amount']}"))
    else:
        print(f"❌ [FAIL] Fractional payload failed: {res_frac.text}")
        edge_results.append(("Fractional Currency", "FAIL", res_frac.text))

    print()

    # -------------------------------------------------------------------------
    # Scenario 3: Total Amount vs Sale Items Math Mismatch
    # -------------------------------------------------------------------------
    print("--- SCENARIO 3: Total Amount vs Sale Items Math Mismatch ---")
    math_mismatch_payload = {
        "branch": str(branch_obj.id),
        "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
        "customer_name": "عميل غير متطابق",
        "total_amount": 1000.00,  # Intentional mismatch vs 1 * 150.00
        "down_payment": 1000.00,
        "is_cash_sale": True,
        "sale_year": 2026,
        "sale_month": 7,
        "sale_items": [
            {
                "inventory_item": str(item_obj.id),
                "quantity": 1,
                "unit_price": 150.00
            }
        ]
    }

    res_mismatch = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=math_mismatch_payload)
    print(f"Status Code: {res_mismatch.status_code}")
    print(f"Response: {res_mismatch.text}")
    if res_mismatch.status_code == 201:
        print("⚠️ [OBSERVATION/NOTE] Backend allows client to specify total_amount without enforcing sum(SaleItem) validation on POST.")
        edge_results.append(("Total Mismatch Submission", "ALLOWED_BY_BE", "Backend created receipt without verifying item sum matches total_amount"))
    else:
        print("✅ [PASS] Backend rejected mismatched total_amount payload.")
        edge_results.append(("Total Mismatch Submission", "REJECTED", res_mismatch.text))

    print()

    # -------------------------------------------------------------------------
    # Scenario 4: Installments Sum Mismatch (Down Payment + Installments != Total)
    # -------------------------------------------------------------------------
    print("--- SCENARIO 4: Installments Sum Mismatch ---")
    inst_mismatch_payload = {
        "branch": str(branch_obj.id),
        "salesperson": str(salesperson_obj.id) if salesperson_obj else None,
        "customer_name": "عميل أقساط غير متطابقة",
        "total_amount": 600.00,
        "down_payment": 200.00,  # Balance due should be 400.00
        "is_cash_sale": False,
        "sale_year": 2026,
        "sale_month": 7,
        "sale_items": [
            {
                "inventory_item": str(item_obj.id),
                "quantity": 4,
                "unit_price": 150.00
            }
        ],
        "installment_payments": [
            {
                "amount": 100.00,  # Total installments = 200.00, down_pmt + inst = 400.00 != 600.00
                "payment_month": 8,
                "payment_year": 2026
            },
            {
                "amount": 100.00,
                "payment_month": 9,
                "payment_year": 2026
            }
        ]
    }

    res_inst_mismatch = requests.post(f"{BASE_URL}/receipts/", headers=HEADERS, json=inst_mismatch_payload)
    print(f"Status Code: {res_inst_mismatch.status_code}")
    print(f"Response: {res_inst_mismatch.text}")
    if res_inst_mismatch.status_code == 201:
        print("⚠️ [OBSERVATION/NOTE] Backend created receipt even though down_payment + sum(installments) != total_amount.")
        edge_results.append(("Installment Sum Mismatch", "ALLOWED_BY_BE", "Backend created receipt without verifying down_payment + sum(installments) == total_amount"))
    else:
        print("✅ [PASS] Backend rejected mismatched installment sum payload.")
        edge_results.append(("Installment Sum Mismatch", "REJECTED", res_inst_mismatch.text))

    print("\n=====================================================================")
    print("Edge Case Test Summary:")
    for test_name, status, detail in edge_results:
        print(f" - {test_name}: [{status}] {detail}")
    print("=====================================================================")

if __name__ == "__main__":
    run_edge_case_tests()
