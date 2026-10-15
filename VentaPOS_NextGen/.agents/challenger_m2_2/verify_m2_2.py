"""
Verification Script for Challenger 2: Tenant Isolation & Stock Limits
"""
import os
import sys
import django
import uuid
import datetime
import random
from django.utils import timezone

# Ensure UTF-8 output encoding for Windows terminal
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.test import Client
from rest_framework import status
from api.models import (
    Tenant, Branch, Salesperson, InventoryItem, Receipt, SaleItem,
    InstallmentPayment, ClientLicense, CompanySetting
)
from api.views import calculate_safe_stock_limit, get_default_date_for_tenant
from api.utils.security_utils import generate_record_signature, get_machine_id

def run_tests():
    print("=" * 60)
    print("RUNNING EMPIRICAL VERIFICATION TESTS FOR M2-CHALLENGER 2")
    print("=" * 60)
    
    machine_id = get_machine_id()
    start_date = datetime.date(2026, 1, 1)
    exp_date = datetime.date(2030, 12, 31)
    
    # Tenant 1: "1234"
    tenant1, _ = Tenant.objects.get_or_create(
        company_code="1234",
        defaults={"name": "Company 1234", "is_active": True}
    )
    sig1 = generate_record_signature(exp_date, 10000, machine_id, 1, True)
    ClientLicense.objects.update_or_create(
        tenant=tenant1,
        defaults={
            "product_id": 1,
            "license_code_hash": sig1,
            "start_date": start_date,
            "expiry_date": exp_date,
            "invoices_balance": 10000,
            "is_active": True,
            "is_deleted": False
        }
    )
    
    # Tenant 2: "5678"
    tenant2, _ = Tenant.objects.get_or_create(
        company_code="5678",
        defaults={"name": "Company 5678", "is_active": True}
    )
    sig2 = generate_record_signature(exp_date, 10000, machine_id, 1, True)
    ClientLicense.objects.update_or_create(
        tenant=tenant2,
        defaults={
            "product_id": 1,
            "license_code_hash": sig2,
            "start_date": start_date,
            "expiry_date": exp_date,
            "invoices_balance": 10000,
            "is_active": True,
            "is_deleted": False
        }
    )
    
    # Tenant 3: "999000" (inactive)
    tenant_inactive, _ = Tenant.objects.get_or_create(
        company_code="999000",
        defaults={"name": "Inactive Corp", "is_active": False}
    )

    branch1, _ = Branch.objects.get_or_create(tenant=tenant1, local_id=1, defaults={"name": "Branch 1234"})
    branch2, _ = Branch.objects.get_or_create(tenant=tenant2, local_id=1, defaults={"name": "Branch 5678"})

    sp1, _ = Salesperson.objects.update_or_create(tenant=tenant1, branch=branch1, local_id=888, defaults={"name": "Seller 1234", "is_deleted": False})
    sp2, _ = Salesperson.objects.update_or_create(tenant=tenant2, branch=branch2, local_id=889, defaults={"name": "Seller 5678", "is_deleted": False})

    # Clean previous test Receipts & SaleItems for clean empirical execution
    SaleItem.all_objects.filter(tenant=tenant1).delete()
    SaleItem.all_objects.filter(tenant=tenant2).delete()
    Receipt.all_objects.filter(tenant=tenant1).delete()
    Receipt.all_objects.filter(tenant=tenant2).delete()

    print("[SETUP] Created/Confirmed Test Tenants 1234, 5678, and inactive 999000")

    client = Client()

    # ==================================================================
    # TASK 1: MULTI-TENANT ISOLATION TESTS
    # ==================================================================
    print("\n--- TASK 1: Multi-Tenant Isolation Tests ---")
    
    # 1A. Valid Tenant "1234"
    resp = client.get("/api/v1/salespersons/", HTTP_X_COMPANY_CODE="1234")
    print(f"1A. Request with X-Company-Code '1234': HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    sellers = [item["name"] for item in data]
    print(f"    Returned sellers for 1234: {sellers}")
    assert "Seller 1234" in sellers and "Seller 5678" not in sellers, "Tenant 1234 leaked data from Tenant 5678!"

    # 1B. Valid Tenant "5678"
    resp = client.get("/api/v1/salespersons/", HTTP_X_COMPANY_CODE="5678")
    print(f"1B. Request with X-Company-Code '5678': HTTP {resp.status_code}")
    assert resp.status_code == 200
    data = resp.json()
    sellers = [item["name"] for item in data]
    print(f"    Returned sellers for 5678: {sellers}")
    assert "Seller 5678" in sellers and "Seller 1234" not in sellers, "Tenant 5678 leaked data from Tenant 1234!"

    # 1C. Invalid Tenant "INVALID_CODE_999"
    resp = client.get("/api/v1/salespersons/", HTTP_X_COMPANY_CODE="INVALID_CODE_999")
    print(f"1C. Request with invalid X-Company-Code 'INVALID_CODE_999': HTTP {resp.status_code}")
    print(f"    Response body: {resp.json()}")
    assert resp.status_code in [400, 403, 404], f"Invalid company code should be rejected! Got {resp.status_code}"
    assert "company_code" in resp.json() or "detail" in resp.json(), "Invalid company code error missing from response!"

    # 1D. Inactive Tenant "999000"
    resp = client.get("/api/v1/salespersons/", HTTP_X_COMPANY_CODE="999000")
    print(f"1D. Request with inactive tenant '999000': HTTP {resp.status_code}")
    print(f"    Response body: {resp.json()}")
    assert resp.status_code in [400, 403], f"Inactive tenant should be rejected! Got {resp.status_code}"

    # 1E. MISSING X-Company-Code Header
    resp = client.get("/api/v1/salespersons/")
    print(f"1E. Request WITHOUT X-Company-Code header: HTTP {resp.status_code}")
    if resp.status_code == 200:
        returned_names = [x["name"] for x in resp.json()]
        print(f"    BEHAVIOR OBSERVED: Accepted! Returned data from default tenant: {returned_names}")
    else:
        print(f"    Response body: {resp.json()}")

    # ==================================================================
    # TASK 2: CREATION & TENANT BINDING IN DB
    # ==================================================================
    print("\n--- TASK 2: Receipt, SaleItem & InstallmentPayment Tenant Binding ---")

    # Create an InventoryItem for Tenant 1234
    item1234, _ = InventoryItem.objects.update_or_create(
        tenant=tenant1,
        branch=branch1,
        local_id=101,
        defaults={
            "name": "Widget A",
            "initial_quantity": 100,
            "initial_year": 2026,
            "initial_month": 1,
            "initial_purchase_price": "30.00",
            "is_deleted": False
        }
    )

    # Post a new receipt via API using X-Company-Code: 1234
    receipt_payload = {
        "branch": str(branch1.id),
        "salesperson": str(sp1.id),
        "customer_name": "Test Customer 1234",
        "customer_phone": "01012345678",
        "customer_address": "Cairo, Egypt",
        "customer_area": "Downtown",
        "total_amount": 100.0,
        "down_payment": 20.0,
        "installment_system": "MONTHLY",
        "sale_year": 2026,
        "sale_month": 7,
        "is_cash_sale": False,
        "sale_items": [
            {
                "inventory_item": str(item1234.id),
                "item_name": "Widget A",
                "quantity": 2,
                "unit_price": 50.0,
                "total_price": 100.0,
                "cost_price": 30.0
            }
        ],
        "installment_payments": [
            {
                "installment_number": 1,
                "amount": 40.0,
                "payment_month": 8,
                "payment_year": 2026,
                "is_paid": False
            },
            {
                "installment_number": 2,
                "amount": 40.0,
                "payment_month": 9,
                "payment_year": 2026,
                "is_paid": False
            }
        ]
    }

    resp = client.post(
        "/api/v1/receipts/",
        data=receipt_payload,
        content_type="application/json",
        HTTP_X_COMPANY_CODE="1234"
    )
    print(f"2A. POST /api/v1/receipts/ for Tenant 1234: HTTP {resp.status_code}")
    if resp.status_code != 201:
        print(f"    Error response: {resp.json()}")
    assert resp.status_code == 201, f"Receipt creation failed with {resp.status_code}"
    created_receipt_data = resp.json()
    receipt_id = created_receipt_data["id"]

    # Direct DB inspection of business_data.sqlite3 records
    db_receipt = Receipt.objects.get(id=receipt_id)
    print(f"2B. DB Receipt ID: {db_receipt.id}, tenant_id: {db_receipt.tenant_id}")
    assert db_receipt.tenant_id == tenant1.id, f"Receipt tenant mismatch! Expected {tenant1.id}, got {db_receipt.tenant_id}"

    db_sale_items = list(SaleItem.objects.filter(receipt=db_receipt))
    print(f"2C. DB SaleItems count: {len(db_sale_items)}")
    assert len(db_sale_items) == 1
    for si in db_sale_items:
        print(f"    SaleItem ID: {si.id}, tenant_id: {si.tenant_id}")
        assert si.tenant_id == tenant1.id, f"SaleItem tenant mismatch! Expected {tenant1.id}, got {si.tenant_id}"

    db_installments = list(InstallmentPayment.objects.filter(receipt=db_receipt))
    print(f"2D. DB InstallmentPayments count: {len(db_installments)}")
    assert len(db_installments) == 2
    for inst in db_installments:
        print(f"    Installment ID: {inst.id}, tenant_id: {inst.tenant_id}")
        assert inst.tenant_id == tenant1.id, f"Installment tenant mismatch! Expected {tenant1.id}, got {inst.tenant_id}"

    # Verify cross-tenant isolation: querying receipts with X-Company-Code: 5678 must NOT return this receipt
    resp = client.get("/api/v1/receipts/", HTTP_X_COMPANY_CODE="5678")
    returned_ids = [r["id"] for r in resp.json()]
    assert receipt_id not in returned_ids, "Tenant 5678 returned Receipt belonging to Tenant 1234!"
    print("2E. Multi-tenant database isolation verified for Receipt, SaleItem, and InstallmentPayment.")

    # ==================================================================
    # TASK 3: RETROACTIVE STOCK LIMIT LOGIC (calculate_safe_stock_limit)
    # ==================================================================
    print("\n--- TASK 3: Retroactive Stock Limit Verification ---")

    # Setup Item B with initial stock = 100 in Month 1/2026
    item_b, _ = InventoryItem.objects.update_or_create(
        tenant=tenant1,
        branch=branch1,
        local_id=202,
        defaults={
            "name": "Widget Stock Test",
            "initial_quantity": 100,
            "initial_year": 2026,
            "initial_month": 1,
            "initial_purchase_price": "5.00",
            "is_deleted": False
        }
    )
    # Reset sales on item_b
    SaleItem.all_objects.filter(inventory_item=item_b).delete()

    # Helper function to get next local_id & receipt_number
    def create_test_receipt(month, year, cust_name, total):
        last_rec = Receipt.all_objects.filter(tenant=tenant1).order_by("-receipt_number").first()
        loc_id = (last_rec.local_id + 1) if last_rec else 2000
        rec_num = (last_rec.receipt_number + 1) if last_rec else 2000
        rec_hash = generate_record_signature(datetime.date.today(), total, machine_id, 1, True) + str(uuid.uuid4())[:8]
        return Receipt.objects.create(
            tenant=tenant1, branch=branch1, salesperson=sp1,
            local_id=loc_id, receipt_number=rec_num, client_uuid=uuid.uuid4(),
            customer_name=cust_name, total_amount=total, down_payment=total,
            sale_year=year, sale_month=month, is_cash_sale=True, created_at_local=timezone.now(),
            receipt_hash=rec_hash
        )

    # Current/Default Date is 2026-07 (July 2026)
    # Add a sale of 60 items in March 2026 (Month 3)
    r_march = create_test_receipt(3, 2026, "March Buyer", 600.0)
    SaleItem.objects.create(
        tenant=tenant1, receipt=r_march, inventory_item=item_b,
        quantity=60, unit_price=10.0
    )

    # Add a sale of 30 items in May 2026 (Month 5)
    r_may = create_test_receipt(5, 2026, "May Buyer", 300.0)
    SaleItem.objects.create(
        tenant=tenant1, receipt=r_may, inventory_item=item_b,
        quantity=30, unit_price=10.0
    )

    # 3A. Test calculate_safe_stock_limit for a retroactive sale in February 2026 (Month 2)
    # Range evaluated: Feb, Mar, Apr, May, Jun, Jul
    # Stocks in range: [100, 40, 40, 10, 10, 10] -> min is 10!
    safe_limit_feb = calculate_safe_stock_limit(item_b, default_year=2026, default_month=7, target_year=2026, target_month=2)
    print(f"3A. Safe stock limit for Month 2 (Feb) with default Month 7 (Jul): {safe_limit_feb}")
    assert safe_limit_feb == 10, f"Expected safe stock limit 10, got {safe_limit_feb}"

    # 3B. Test API rejection when attempting to sell MORE than safe limit (e.g. 15 items in Month 2)
    over_limit_payload = {
        "branch": str(branch1.id),
        "salesperson": str(sp1.id),
        "customer_name": "Over Limit Buyer",
        "total_amount": 150.0,
        "down_payment": 150.0,
        "sale_year": 2026,
        "sale_month": 2,
        "is_cash_sale": True,
        "sale_items": [
            {
                "inventory_item": str(item_b.id),
                "item_name": "Widget Stock Test",
                "quantity": 15,
                "unit_price": 10.0,
                "total_price": 150.0,
                "cost_price": 5.0
            }
        ]
    }
    resp = client.post(
        "/api/v1/receipts/",
        data=over_limit_payload,
        content_type="application/json",
        HTTP_X_COMPANY_CODE="1234"
    )
    print(f"3B. POST sale exceeding safe limit (15 > 10 in Feb 2026): HTTP {resp.status_code}")
    print(f"    Response body: {resp.json()}")
    assert resp.status_code == 400, f"Over-limit sale should be rejected! Got {resp.status_code}"
    err_msg = str(resp.json())
    assert "أقصى كمية يمكن بيعها بأثر رجعي" in err_msg or "error" in resp.json(), "Safe stock limit error message expected!"

    # 3C. Test POST sale AT or UNDER safe limit (e.g. 8 items in Month 2)
    valid_limit_payload = {
        "branch": str(branch1.id),
        "salesperson": str(sp1.id),
        "customer_name": "Valid Limit Buyer",
        "total_amount": 80.0,
        "down_payment": 80.0,
        "sale_year": 2026,
        "sale_month": 2,
        "is_cash_sale": True,
        "sale_items": [
            {
                "inventory_item": str(item_b.id),
                "item_name": "Widget Stock Test",
                "quantity": 8,
                "unit_price": 10.0,
                "total_price": 80.0,
                "cost_price": 5.0
            }
        ]
    }
    resp = client.post(
        "/api/v1/receipts/",
        data=valid_limit_payload,
        content_type="application/json",
        HTTP_X_COMPANY_CODE="1234"
    )
    print(f"3C. POST sale within safe limit (8 <= 10 in Feb 2026): HTTP {resp.status_code}")
    assert resp.status_code == 201, f"Valid retroactive sale failed! HTTP {resp.status_code}"

    # After selling 8 items in Feb:
    # Stocks now: Feb=92, Mar=32, Apr=32, May=2, Jun=2, Jul=2
    new_safe_limit = calculate_safe_stock_limit(item_b, default_year=2026, default_month=7, target_year=2026, target_month=2)
    print(f"3D. New safe stock limit after 8 sold: {new_safe_limit}")
    assert new_safe_limit == 2, f"Expected new safe stock limit 2, got {new_safe_limit}"

    # 3E. Edge Case: Retroactive sale before item's initial_month (Dec 2025 vs Initial Jan 2026)
    limit_before_init = calculate_safe_stock_limit(item_b, default_year=2026, default_month=7, target_year=2025, target_month=12)
    print(f"3E. Safe stock limit for month BEFORE initial_month (Dec 2025): {limit_before_init}")
    assert limit_before_init == 0, f"Expected 0 stock before initial date, got {limit_before_init}"

    # 3F. Edge Case: Future sale (Target Month Sept 2026, Default July 2026)
    limit_future = calculate_safe_stock_limit(item_b, default_year=2026, default_month=7, target_year=2026, target_month=9)
    print(f"3F. Safe stock limit for future month (Sept 2026): {limit_future}")
    assert limit_future == 2, f"Expected 2 for future month, got {limit_future}"

    print("\n" + "=" * 60)
    print("ALL EMPIRICAL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
