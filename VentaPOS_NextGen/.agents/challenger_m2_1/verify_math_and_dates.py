import os
import sys
import re
import sqlite3
from decimal import Decimal, ROUND_HALF_UP

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Setup paths & Django environment for HMAC hashing function
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.path.join(BACKEND_DIR, "db", "business_data.sqlite3")

sys.path.append(BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.models import Receipt, SaleItem, InstallmentPayment, InventoryItem
from api.utils.security_utils import generate_receipt_signature

def to_hex_uuid(val):
    if not val:
        return ""
    return str(val).replace("-", "")

def run_challenger_verification():
    print("=====================================================================")
    print("Challenger 1: Financial Math & Date Calculations Verification Harness")
    print("=====================================================================")
    print(f"Target SQLite Database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query all active (non-deleted) receipts
    cursor.execute("SELECT * FROM receipt WHERE is_deleted = 0")
    receipts = cursor.fetchall()
    print(f"Found {len(receipts)} total non-deleted receipts in database.\n")

    failures = []
    successes = 0

    date_regex = re.compile(r"^\d{4}-\d{2}-25$")

    for rcpt in receipts:
        rcpt_id_hex = rcpt["id"]
        rcpt_num = rcpt["receipt_number"]
        is_cash = bool(rcpt["is_cash_sale"])
        sale_month = rcpt["sale_month"]
        sale_year = rcpt["sale_year"]
        
        # 1. Total Amount vs SaleItems sum
        cursor.execute("SELECT * FROM sale_item WHERE receipt_id = ? AND is_deleted = 0", (rcpt_id_hex,))
        items = cursor.fetchall()
        
        calculated_total = Decimal("0.00")
        items_for_hash = []

        for item in items:
            qty = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            item_total = (qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            calculated_total += item_total

            # Fetch inventory item OR dummy wrapper for hash generation
            try:
                inv_obj = InventoryItem.objects.get(id=item["inventory_item_id"])
            except Exception:
                inv_obj = None

            items_for_hash.append({
                "inventory_item": inv_obj if inv_obj else item["inventory_item_id"],
                "quantity": item["quantity"]
            })

        db_total = Decimal(str(rcpt["total_amount"])).quantize(Decimal("0.01"))

        if calculated_total != db_total:
            msg = f"Receipt #{rcpt_num} ({rcpt_id_hex}): SaleItem sum ({calculated_total}) != Receipt.total_amount ({db_total})"
            failures.append(msg)
            print(f"❌ [MATH FAIL] {msg}")
        else:
            print(f"✅ [MATH PASS] Receipt #{rcpt_num}: sum(SaleItem) = {calculated_total} == Receipt.total_amount ({db_total})")

        # 2. Down Payment + Installments sum
        db_down_pmt = Decimal(str(rcpt["down_payment"])).quantize(Decimal("0.01"))
        
        cursor.execute("SELECT * FROM installment_payment WHERE receipt_id = ? AND is_deleted = 0 ORDER BY payment_date ASC", (rcpt_id_hex,))
        installments = cursor.fetchall()

        if is_cash:
            if db_down_pmt != db_total:
                msg = f"Receipt #{rcpt_num} (Cash Sale): down_payment ({db_down_pmt}) != total_amount ({db_total})"
                failures.append(msg)
                print(f"❌ [CASH FAIL] {msg}")
            if len(installments) > 0:
                msg = f"Receipt #{rcpt_num} (Cash Sale): has {len(installments)} installment payments, expected 0"
                failures.append(msg)
                print(f"❌ [CASH FAIL] {msg}")
        else:
            inst_sum = sum(Decimal(str(inst["amount"])).quantize(Decimal("0.01")) for inst in installments)
            if db_down_pmt + inst_sum != db_total:
                msg = f"Receipt #{rcpt_num} (Installment Sale): down_payment ({db_down_pmt}) + installment_sum ({inst_sum}) = {db_down_pmt + inst_sum} != total_amount ({db_total})"
                failures.append(msg)
                print(f"❌ [INST MATH FAIL] {msg}")
            else:
                print(f"✅ [INST MATH PASS] Receipt #{rcpt_num}: down_payment ({db_down_pmt}) + sum(installments) ({inst_sum}) == total_amount ({db_total})")

            # 3. Check Installment payment dates: strict YYYY-MM-25 format and starting month (sale_month + 1)
            expected_m = sale_month + 1
            expected_y = sale_year
            if expected_m > 12:
                expected_m = 1
                expected_y += 1

            for idx, inst in enumerate(installments):
                pdate = inst["payment_date"]
                if not date_regex.match(pdate):
                    msg = f"Receipt #{rcpt_num} Installment #{idx+1}: payment_date '{pdate}' does not match strict YYYY-MM-25 format"
                    failures.append(msg)
                    print(f"❌ [DATE FORMAT FAIL] {msg}")
                else:
                    exp_date_str = f"{expected_y:04d}-{expected_m:02d}-25"
                    if pdate != exp_date_str:
                        msg = f"Receipt #{rcpt_num} Installment #{idx+1}: payment_date '{pdate}' != expected date '{exp_date_str}'"
                        failures.append(msg)
                        print(f"❌ [DATE SEQUENCE FAIL] {msg}")
                    else:
                        print(f"✅ [DATE PASS] Receipt #{rcpt_num} Installment #{idx+1}: payment_date = '{pdate}' (matches {exp_date_str})")

                # Advance expected month for next installment
                expected_m += 1
                if expected_m > 12:
                    expected_m = 1
                    expected_y += 1

        # 4. Re-compute HMAC-SHA256 receipt_hash and compare
        formatted_total_str = f"{db_total:.2f}"
        
        # Call generate_receipt_signature
        expected_hash = generate_receipt_signature(
            rcpt["receipt_number"],
            formatted_total_str,
            sale_month,
            sale_year,
            items_data=items_for_hash
        )

        db_hash = rcpt["receipt_hash"]
        if db_hash != expected_hash:
            msg = f"Receipt #{rcpt_num}: stored receipt_hash '{db_hash}' != re-computed hash '{expected_hash}'"
            failures.append(msg)
            print(f"❌ [HASH FAIL] {msg}")
        else:
            print(f"✅ [HASH PASS] Receipt #{rcpt_num}: stored hash matches HMAC-SHA256 signature ({db_hash})")

        successes += 1

    conn.close()

    print("\n---------------------------------------------------------------------")
    print(f"Audit Summary: {successes} receipts audited. Failures found: {len(failures)}")
    if failures:
        print("FAILURES LIST:")
        for f in failures:
            print(f" - {f}")
        return False
    else:
        print("ALL DATABASE RECORDS PASSED EMPIRICAL AUDIT WITH ZERO ERRORS!")
        return True

if __name__ == "__main__":
    success = run_challenger_verification()
    if not success:
        sys.exit(1)
