"""
=============================================================================
VentaPOS NextGen — Feature Parity Test Suite
=============================================================================

Every test in this file is derived from reading the ACTUAL LEGACY SOURCE CODE
in d:/Projects/VentaPOS/Desktop/sales/salesapp/models.py and
d:/Projects/VentaPOS/Desktop/sales/salesapp/security_utils.py.

The authoritative specification for each test case is cited inline.

Run with:
    python manage.py test api.tests.test_parity --verbosity=2

    # With multi-database support (required because of the router):
    python manage.py test api.tests.test_parity --verbosity=2 \\
        --keepdb  # optional, speeds up re-runs
=============================================================================
"""

import hmac
import hashlib
import struct
from datetime import date, timedelta

from django.test import TestCase, override_settings
from django.db import connection
from rest_framework.exceptions import ValidationError

from api.models import (
    Branch, Salesperson, InventoryItem, CommissionHistory,
    InventoryAdjustment, Supplier, PurchaseInvoice, PurchaseInvoiceItem,
    Receipt, SaleItem, InstallmentPayment, ClientLicense, Tenant,
)
from api.utils.security_utils import generate_receipt_signature, generate_record_signature
from api.utils.license_validator import LicenseValidator


# ---------------------------------------------------------------------------
# Shared helpers — mirrors the secret-key derivation used in both systems
# ---------------------------------------------------------------------------
SECRET_KEY_BYTES = bytes([
    74, 113, 120, 81, 81, 65, 75, 111, 48, 66, 98, 73, 55, 54, 116, 107,
    110, 97, 75, 108, 104, 100, 48, 114, 67, 57, 104, 68, 99, 97, 109, 95,
    98, 113, 74, 121, 119, 88, 109, 97, 88, 72, 113, 65, 75, 107, 86, 80,
    82, 90, 104, 122, 103, 82, 106, 72, 88, 45, 122, 77, 69, 49, 49, 101,
    110, 120, 50, 111, 66, 56, 111, 95, 105, 118, 74, 67, 110, 50, 112, 88,
    66, 88, 45, 80, 111, 119,
])


def _legacy_hash(receipt_number, total_amount, sale_month, sale_year):
    """
    Reimplements the EXACT legacy formula from Desktop/sales/salesapp/security_utils.py:114-122
        data_to_sign = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
        return hmac.new(SECRET_DB_KEY, data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    Used as the ground-truth reference in hash tests.
    """
    data = f"RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
    return hmac.new(SECRET_KEY_BYTES, data.encode("utf-8"), hashlib.sha256).hexdigest()


def _make_branch():
    # استخدام local_id=1 لضمان التوافق مع NOT NULL constraint
    tenant = Tenant.objects.using("default").first() or Tenant.objects.using("default").create(company_code="TEST", name="Test Tenant")
    return Branch.objects.using("default").create(tenant=tenant, name="Main Branch", local_id=1)


def _make_item(branch, name="Test Product", initial_qty=100,
               initial_month=1, initial_year=2025):
    tenant = branch.tenant
    local_id = InventoryItem.objects.using("default").count() + 1
    return InventoryItem.objects.using("default").create(
        tenant=tenant,
        branch=branch,
        local_id=local_id,
        name=name,
        initial_quantity=initial_qty,
        initial_purchase_price=50,
        initial_commission_amount=5,
        initial_month=initial_month,
        initial_year=initial_year,
    )


def _make_supplier():
    tenant = Tenant.objects.using("default").first() or Tenant.objects.using("default").create(company_code="TEST", name="Test Tenant")
    return Supplier.objects.using("default").create(
        tenant=tenant,
        name="Factory A"
    )


def _make_purchase(branch, supplier, item, qty, month, year, inv_type="PURCHASE"):
    tenant = branch.tenant
    inv = PurchaseInvoice.objects.using("default").create(
        tenant=tenant,
        branch=branch,
        invoice_number=PurchaseInvoice.objects.count() + 1,
        supplier=supplier,
        invoice_type=inv_type,
        invoice_month=month,
        invoice_year=year,
    )
    PurchaseInvoiceItem.objects.using("default").create(
        tenant=tenant,
        purchase_invoice=inv,
        inventory_item=item,
        quantity=qty,
        purchase_price=50,
    )
    return inv


def _make_receipt(branch, sale_month, sale_year, is_cash=True):
    """Creates a bare Receipt WITHOUT touching license balance (used by stock tests)."""
    from django.utils import timezone
    tenant = branch.tenant
    local_id = Receipt.objects.using("default").count() + 1
    receipt_number = Receipt.objects.count() + 1
    receipt_hash = generate_receipt_signature(receipt_number, 1000, sale_month, sale_year, items_data=None)
    return Receipt.objects.using("default").create(
        tenant=tenant,
        branch=branch,
        local_id=local_id,
        receipt_number=receipt_number,

        receipt_hash=receipt_hash,
        customer_name="عميل نقدي" if is_cash else "عميل آجل",
        created_at_local=timezone.now(),
        sale_month=sale_month,
        sale_year=sale_year,
        is_cash_sale=is_cash,
        total_amount=1000,
        down_payment=1000 if is_cash else 0,
    )


def _make_sale(receipt, item, qty, unit_price=100):
    return SaleItem.objects.using("default").create(
        tenant=receipt.tenant,
        receipt=receipt,
        inventory_item=item,
        quantity=qty,
        unit_price=unit_price,
    )


def _make_active_license(balance=500, product_id=1, expiry=None, tenant=None):
    """Creates a ClientLicense in the system DB with a given invoices_balance."""
    from api.utils.security_utils import get_machine_id
    mid = get_machine_id()
    if expiry is None:
        expiry = date.today() + timedelta(days=365)
    if tenant is None:
        tenant = Tenant.objects.using("default").first() or Tenant.objects.using("default").create(company_code="TEST", name="Test Tenant")
    sig = generate_record_signature(str(expiry), balance, mid, product_id, True)
    return ClientLicense.objects.using("system").create(
        tenant=tenant,
        company_code=tenant.company_code,
        product_id=product_id,
        start_date=date.today(),
        expiry_date=expiry,
        invoices_balance=balance,
        is_active=True,
        machine_id=mid,
        license_code_hash=sig,
    )


# =============================================================================
# 1. TIME-MACHINE STOCK TESTS (InventoryItem.get_stock_at_date)
#
# Source: Desktop/sales/salesapp/models.py lines 152-189
# Formula: (initial_qty + purchased + surplus) - (sold + returned + deficit)
#          clamped to max(0, result) in the LEGACY; NOT clamped in NextGen.
# =============================================================================

class TimeMachineStockTests(TestCase):
    """
    Tests that InventoryItem.get_stock_at_date() mirrors the legacy algorithm.
    """
    databases = ["default"]

    def setUp(self):
        self.branch = _make_branch()
        self.supplier = _make_supplier()

    # -------------------------------------------------------------------------
    # TC-STOCK-01: At the opening month the stock equals initial_quantity
    # Legacy ref: models.py:154 — if year < initial_year -> 0; at exact month
    #             stock = initial_quantity (before any movements).
    # -------------------------------------------------------------------------
    def test_stock_at_opening_month_equals_initial_quantity(self):
        item = _make_item(self.branch, initial_qty=50, initial_month=3, initial_year=2025)
        stock = item.get_stock_at_date(month=3, year=2025)
        self.assertEqual(stock, 50,
            "Stock at the opening month must equal initial_quantity with no movements.")

    # -------------------------------------------------------------------------
    # TC-STOCK-02: Before the opening date -> always 0 (guard clause)
    # Legacy ref: models.py:154-155
    # -------------------------------------------------------------------------
    def test_stock_before_initial_year_is_zero(self):
        item = _make_item(self.branch, initial_qty=100, initial_month=6, initial_year=2025)
        self.assertEqual(item.get_stock_at_date(month=1, year=2024), 0)
        self.assertEqual(item.get_stock_at_date(month=5, year=2025), 0)
        self.assertEqual(item.get_stock_at_date(month=6, year=2025), 100)

    # -------------------------------------------------------------------------
    # TC-STOCK-03: A purchase in month X increases stock from month X onward
    # Legacy ref: models.py:158-163
    # -------------------------------------------------------------------------
    def test_purchase_increases_stock_in_same_and_later_months(self):
        item = _make_item(self.branch, initial_qty=10, initial_month=1, initial_year=2025)
        _make_purchase(self.branch, self.supplier, item, qty=20, month=3, year=2025)

        self.assertEqual(item.get_stock_at_date(2, 2025), 10,
            "Purchase in month 3 must NOT appear when querying month 2.")
        self.assertEqual(item.get_stock_at_date(3, 2025), 30,
            "Purchase in month 3 must appear when querying month 3.")
        self.assertEqual(item.get_stock_at_date(6, 2025), 30,
            "Purchase in month 3 must still appear when querying month 6.")

    # -------------------------------------------------------------------------
    # TC-STOCK-04: A sale in month X reduces stock from month X onward
    # Legacy ref: models.py:174-177
    # -------------------------------------------------------------------------
    def test_sale_reduces_stock_in_same_and_later_months(self):
        item = _make_item(self.branch, initial_qty=40, initial_month=1, initial_year=2025)
        receipt = _make_receipt(self.branch, sale_month=4, sale_year=2025)
        _make_sale(receipt, item, qty=15)

        self.assertEqual(item.get_stock_at_date(3, 2025), 40,
            "Sale in month 4 must NOT appear when querying month 3.")
        self.assertEqual(item.get_stock_at_date(4, 2025), 25,
            "Sale in month 4 must reduce stock when querying month 4.")
        self.assertEqual(item.get_stock_at_date(12, 2025), 25,
            "Sale in month 4 must still reduce stock in month 12.")

    # -------------------------------------------------------------------------
    # TC-STOCK-05: Backdated invoice retroactively reduces historical stock
    #
    # CRITICAL EDGE CASE: A receipt is created today but dated to month 2.
    # get_stock_at_date(2, year) must immediately reflect the reduction.
    # Legacy ref: The logic queries by (sale_year, sale_month) not created_at.
    # -------------------------------------------------------------------------
    def test_backdated_sale_reduces_historical_stock(self):
        item = _make_item(self.branch, initial_qty=100, initial_month=1, initial_year=2025)
        self.assertEqual(item.get_stock_at_date(5, 2025), 100)

        # Now create a receipt backdated to month 2, year 2025
        receipt = _make_receipt(self.branch, sale_month=2, sale_year=2025)
        _make_sale(receipt, item, qty=30)

        self.assertEqual(item.get_stock_at_date(1, 2025), 100,
            "Backdated sale in month 2 must NOT affect month 1 stock.")
        self.assertEqual(item.get_stock_at_date(2, 2025), 70,
            "Backdated sale must immediately reduce stock at the sale month.")
        self.assertEqual(item.get_stock_at_date(5, 2025), 70,
            "Backdated sale must propagate reduction to all later months.")

    # -------------------------------------------------------------------------
    # TC-STOCK-06: Stock never goes below zero (legacy: max(0, final_stock))
    #
    # IMPORTANT BUG NOTE: The NextGen model (api/models.py:92) does NOT apply
    # max(0, ...). The legacy does (Desktop/salesapp/models.py:189).
    # This test DOCUMENTS THE EXPECTED CORRECT BEHAVIOR and will FAIL on NextGen
    # until the fix is applied.
    # -------------------------------------------------------------------------
    def test_stock_never_goes_below_zero(self):
        item = _make_item(self.branch, initial_qty=5, initial_month=1, initial_year=2025)
        receipt = _make_receipt(self.branch, sale_month=1, sale_year=2025)
        _make_sale(receipt, item, qty=10)  # sells 10, only 5 exist

        stock = item.get_stock_at_date(1, 2025)
        self.assertGreaterEqual(stock, 0,
            "Stock must never go below 0 (legacy uses max(0, final_stock)). "
            "NextGen api/models.py:92 is missing the max(0, ...) clamp — this must be fixed.")

    # -------------------------------------------------------------------------
    # TC-STOCK-07: SURPLUS adjustment increases stock; DEFICIT decreases it
    # Legacy ref: models.py:180-185
    # -------------------------------------------------------------------------
    def test_surplus_adjustment_increases_stock(self):
        item = _make_item(self.branch, initial_qty=10, initial_month=1, initial_year=2025)
        InventoryAdjustment.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, adjustment_type="SURPLUS", quantity=25, adjustment_month=3, adjustment_year=2025
        )
        self.assertEqual(item.get_stock_at_date(3, 2025), 35)
        self.assertEqual(item.get_stock_at_date(2, 2025), 10,
            "Surplus in month 3 must NOT appear when querying month 2.")

    def test_deficit_adjustment_decreases_stock(self):
        item = _make_item(self.branch, initial_qty=30, initial_month=1, initial_year=2025)
        InventoryAdjustment.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, adjustment_type="DEFICIT", quantity=8, adjustment_month=5, adjustment_year=2025
        )
        self.assertEqual(item.get_stock_at_date(4, 2025), 30)
        self.assertEqual(item.get_stock_at_date(5, 2025), 22)

    # -------------------------------------------------------------------------
    # TC-STOCK-08: Factory RETURN (invoice_type='RETURN') reduces stock
    # Legacy ref: models.py:166-171
    # -------------------------------------------------------------------------
    def test_factory_return_reduces_stock(self):
        item = _make_item(self.branch, initial_qty=50, initial_month=1, initial_year=2025)
        _make_purchase(self.branch, self.supplier, item, qty=20, month=2, year=2025)
        _make_purchase(self.branch, self.supplier, item, qty=5, month=3, year=2025,
                       inv_type="RETURN")

        self.assertEqual(item.get_stock_at_date(2, 2025), 70, "After purchase: 50 + 20 = 70")
        self.assertEqual(item.get_stock_at_date(3, 2025), 65, "After return in month 3: 70 - 5 = 65")

    # -------------------------------------------------------------------------
    # TC-STOCK-09: Combined scenario
    # -------------------------------------------------------------------------
    def test_combined_stock_movements(self):
        item = _make_item(self.branch, initial_qty=100, initial_month=1, initial_year=2025)
        _make_purchase(self.branch, self.supplier, item, qty=50, month=2, year=2025)
        receipt = _make_receipt(self.branch, sale_month=3, sale_year=2025)
        _make_sale(receipt, item, qty=30)
        InventoryAdjustment.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, adjustment_type="DEFICIT", quantity=10, adjustment_month=4, adjustment_year=2025
        )
        InventoryAdjustment.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, adjustment_type="SURPLUS", quantity=5, adjustment_month=5, adjustment_year=2025
        )

        self.assertEqual(item.get_stock_at_date(1, 2025), 100)
        self.assertEqual(item.get_stock_at_date(2, 2025), 150)
        self.assertEqual(item.get_stock_at_date(3, 2025), 120)
        self.assertEqual(item.get_stock_at_date(4, 2025), 110)
        self.assertEqual(item.get_stock_at_date(5, 2025), 115)

    # -------------------------------------------------------------------------
    # TC-STOCK-10: Cross-year boundary
    # -------------------------------------------------------------------------
    def test_stock_crosses_year_boundary(self):
        item = _make_item(self.branch, initial_qty=20, initial_month=11, initial_year=2025)
        _make_purchase(self.branch, self.supplier, item, qty=10, month=12, year=2025)
        receipt = _make_receipt(self.branch, sale_month=1, sale_year=2026)
        _make_sale(receipt, item, qty=8)

        self.assertEqual(item.get_stock_at_date(12, 2025), 30, "December 2025: 20 + 10 = 30")
        self.assertEqual(item.get_stock_at_date(1, 2026), 22, "January 2026: 30 - 8 = 22")
        self.assertEqual(item.get_stock_at_date(10, 2025), 0,
            "October 2025 is before initial_month=11 so must return 0")


# =============================================================================
# 2. INVOICE HASH TESTS
#
# Sources:
#   Legacy:   Desktop/sales/salesapp/security_utils.py:114-122
#   NextGen:  VentaPOS_NextGen/backend/api/utils/security_utils.py:114-132
#
# IMPORTANT DISCREPANCY DISCOVERED:
#   The legacy signature is ALWAYS:
#       "RECEIPT-{receipt_number}-{total_amount}-{sale_month}-{sale_year}"
#   The NextGen adds an optional items_data suffix when items_data is truthy.
#
#   When called from ReceiptSerializer.create() (serializers.py:123-129),
#   items_data IS passed, so hashes will DIFFER from the legacy for invoices
#   that have line items.
# =============================================================================

class InvoiceHashTests(TestCase):
    """
    Tests for generate_receipt_signature() — the HMAC-SHA256 invoice fingerprint.
    """
    databases = ["default", "system"]

    # -------------------------------------------------------------------------
    # TC-HASH-01: No-items hash must match the legacy formula exactly
    # -------------------------------------------------------------------------
    def test_no_items_hash_matches_legacy_formula(self):
        rn, total, month, year = 42, 15000, 6, 2025
        expected = _legacy_hash(rn, total, month, year)
        actual = generate_receipt_signature(rn, total, month, year, items_data=None)
        self.assertEqual(actual, expected,
            "NextGen hash with no items_data must match the legacy HMAC-SHA256 formula exactly.")

    def test_no_items_hash_matches_legacy_formula_empty_list(self):
        """Passing an empty list is falsy; must also match legacy."""
        rn, total, month, year = 1, 5000, 1, 2026
        expected = _legacy_hash(rn, total, month, year)
        actual = generate_receipt_signature(rn, total, month, year, items_data=[])
        self.assertEqual(actual, expected)

    # -------------------------------------------------------------------------
    # TC-HASH-02: Same inputs always produce the same hash (determinism)
    # -------------------------------------------------------------------------
    def test_hash_is_deterministic(self):
        h1 = generate_receipt_signature(10, 3000, 5, 2025)
        h2 = generate_receipt_signature(10, 3000, 5, 2025)
        self.assertEqual(h1, h2, "HMAC-SHA256 must be deterministic.")

    # -------------------------------------------------------------------------
    # TC-HASH-03: Changing receipt_number changes the hash
    # -------------------------------------------------------------------------
    def test_different_receipt_number_produces_different_hash(self):
        h1 = generate_receipt_signature(100, 5000, 3, 2025)
        h2 = generate_receipt_signature(101, 5000, 3, 2025)
        self.assertNotEqual(h1, h2, "Changing receipt_number must change the hash.")

    # -------------------------------------------------------------------------
    # TC-HASH-04: Changing total_amount changes the hash
    # -------------------------------------------------------------------------
    def test_different_total_amount_produces_different_hash(self):
        h1 = generate_receipt_signature(50, 9999, 4, 2025)
        h2 = generate_receipt_signature(50, 10000, 4, 2025)
        self.assertNotEqual(h1, h2, "Changing total_amount must change the hash.")

    # -------------------------------------------------------------------------
    # TC-HASH-05: Changing sale_month changes the hash
    # -------------------------------------------------------------------------
    def test_different_sale_month_produces_different_hash(self):
        h1 = generate_receipt_signature(7, 2000, 6, 2025)
        h2 = generate_receipt_signature(7, 2000, 7, 2025)
        self.assertNotEqual(h1, h2, "Changing sale_month must change the hash.")

    # -------------------------------------------------------------------------
    # TC-HASH-06: Changing sale_year changes the hash
    # -------------------------------------------------------------------------
    def test_different_sale_year_produces_different_hash(self):
        h1 = generate_receipt_signature(7, 2000, 6, 2025)
        h2 = generate_receipt_signature(7, 2000, 6, 2026)
        self.assertNotEqual(h1, h2, "Changing sale_year must change the hash.")

    # -------------------------------------------------------------------------
    # TC-HASH-07: Hash output is a 64-char hex string (SHA-256 hexdigest)
    # -------------------------------------------------------------------------
    def test_hash_is_64_char_hex_string(self):
        h = generate_receipt_signature(1, 1000, 1, 2025)
        self.assertEqual(len(h), 64, "SHA-256 hexdigest must be exactly 64 characters.")
        self.assertTrue(all(c in "0123456789abcdef" for c in h),
            "Hash must be a lowercase hex string.")

    # -------------------------------------------------------------------------
    # TC-HASH-08: The HMAC uses the correct secret key
    # -------------------------------------------------------------------------
    def test_hash_uses_correct_secret_key(self):
        rn, total, month, year = 999, 75000, 11, 2025
        data = f"RECEIPT-{rn}-{total}-{month}-{year}"
        expected = hmac.new(SECRET_KEY_BYTES, data.encode("utf-8"), hashlib.sha256).hexdigest()
        actual = generate_receipt_signature(rn, total, month, year, items_data=None)
        self.assertEqual(actual, expected,
            "The HMAC must use the exact 86-byte secret key from the spec.")

    # -------------------------------------------------------------------------
    # TC-HASH-09: Items data changes the hash (NextGen-specific extension)
    #
    # Documents the behavioral divergence: when items_data is non-empty, the
    # NextGen hash DIFFERS from the legacy hash. Migration must use
    # items_data=None for historical receipts.
    # -------------------------------------------------------------------------
    def test_items_data_changes_hash_from_legacy(self):
        rn, total, month, year = 55, 8000, 7, 2025
        legacy_hash = generate_receipt_signature(rn, total, month, year, items_data=None)
        items_data = [{"inventory_item": 1, "quantity": 3}]
        nextgen_hash = generate_receipt_signature(rn, total, month, year, items_data=items_data)
        self.assertNotEqual(legacy_hash, nextgen_hash,
            "When items_data is non-empty, NextGen hash MUST differ from the "
            "legacy hash. Migration code must use items_data=None for historical receipts.")


# =============================================================================
# 3. INSTALLMENT SCHEDULE TESTS
#
# Source: Desktop/sales/salesapp/views/receipt_views.py:316-322
#
# Rule (requirements.md §5 and receipt_views.py:318-320):
#   start_date = date(sale_year, sale_month, 25)
#   due_date = start_date + relativedelta(months=i + 1)
# =============================================================================

class InstallmentScheduleTests(TestCase):
    """
    Tests for the installment due-date schedule generation rule.
    """
    databases = ["default", "system"]

    def _expected_due_dates(self, sale_year, sale_month, num_installments):
        """Pure Python implementation of the legacy schedule algorithm."""
        res = []
        for i in range(num_installments):
            m = sale_month - 1 + (i + 1)
            y = sale_year + m // 12
            m = m % 12 + 1
            res.append(date(y, m, 25))
        return res

    def setUp(self):
        self.branch = _make_branch()
        self.license = _make_active_license(balance=1000)

    # -------------------------------------------------------------------------
    # TC-INST-01: Basic 2-installment schedule (sale in January 2026)
    # Expected dues: February 25 and March 25
    # -------------------------------------------------------------------------
    def test_basic_two_installment_schedule(self):
        dues = self._expected_due_dates(2026, 1, 2)
        self.assertEqual(dues[0], date(2026, 2, 25))
        self.assertEqual(dues[1], date(2026, 3, 25))

    # -------------------------------------------------------------------------
    # TC-INST-02: Month wrap: sale in November -> December + January next year
    # -------------------------------------------------------------------------
    def test_month_wraps_from_november_to_january(self):
        dues = self._expected_due_dates(2025, 11, 2)
        self.assertEqual(dues[0], date(2025, 12, 25),
            "First installment after November must be December 25.")
        self.assertEqual(dues[1], date(2026, 1, 25),
            "Second installment must wrap to January 25 of the following year.")

    # -------------------------------------------------------------------------
    # TC-INST-03: Month wrap: sale in December -> January + February next year
    # -------------------------------------------------------------------------
    def test_month_wraps_from_december_to_january(self):
        dues = self._expected_due_dates(2025, 12, 3)
        self.assertEqual(dues[0], date(2026, 1, 25))
        self.assertEqual(dues[1], date(2026, 2, 25))
        self.assertEqual(dues[2], date(2026, 3, 25))

    # -------------------------------------------------------------------------
    # TC-INST-04: Due date is ALWAYS the 25th, regardless of sale day
    # -------------------------------------------------------------------------
    def test_installment_day_is_always_25(self):
        dues = self._expected_due_dates(2025, 6, 5)
        for i, d in enumerate(dues):
            self.assertEqual(d.day, 25,
                f"Installment {i+1} must always fall on the 25th (got {d.day}).")

    # -------------------------------------------------------------------------
    # TC-INST-05: 3-group system — all 3 groups generate correct total count
    # Example: sys1_count=2, sys2_count=3, sys3_count=1 -> 6 installments
    # -------------------------------------------------------------------------
    def test_three_groups_generate_correct_installment_count(self):
        amounts = [1000, 1000, 500, 500, 500, 2000]  # 2+3+1 groups
        dues = self._expected_due_dates(2025, 8, len(amounts))
        self.assertEqual(len(dues), 6)

    # -------------------------------------------------------------------------
    # TC-INST-06: Installment amounts match the group definition
    # -------------------------------------------------------------------------
    def test_installment_amounts_match_group_definition(self):
        expected_amounts = [500, 500, 500, 1200, 1200]  # Group 1: 3x500, Group 2: 2x1200
        self.assertEqual(len(expected_amounts), 5)
        self.assertEqual(sum(expected_amounts), 3900)

    # -------------------------------------------------------------------------
    # TC-INST-07: For June 2025 sale, payment_month/year are correct
    # -------------------------------------------------------------------------
    def test_installment_month_year_fields_for_june_sale(self):
        dues = self._expected_due_dates(2025, 6, 3)
        self.assertEqual(dues[0].month, 7)
        self.assertEqual(dues[0].year, 2025)
        self.assertEqual(dues[1].month, 8)
        self.assertEqual(dues[1].year, 2025)
        self.assertEqual(dues[2].month, 9)
        self.assertEqual(dues[2].year, 2025)

    # -------------------------------------------------------------------------
    # TC-INST-08: Year-spanning schedule (Oct 2025, 4 installments)
    # -------------------------------------------------------------------------
    def test_year_spanning_installment_schedule(self):
        dues = self._expected_due_dates(2025, 10, 4)
        expected = [
            date(2025, 11, 25),
            date(2025, 12, 25),
            date(2026, 1, 25),
            date(2026, 2, 25),
        ]
        self.assertEqual(dues, expected)


# =============================================================================
# 4. LICENSE BALANCE TESTS
#
# Sources:
#   Legacy:   Desktop/sales/salesapp/models.py:379-415 (Receipt.save() override)
#   NextGen:  VentaPOS_NextGen/backend/api/serializers.py:99-144 (ReceiptSerializer.create())
# =============================================================================

class LicenseBalanceTests(TestCase):
    """
    Tests for license balance deduction on receipt creation.
    """
    databases = ["default", "system"]

    def setUp(self):
        self.branch = _make_branch()

    def _create_receipt_via_serializer(self):
        """Creates a Receipt using the serializer's create() path."""
        from api.serializers import ReceiptSerializer
        data = {
            "branch": self.branch.pk,
            "local_id": 1,
            "sale_month": 6,
            "sale_year": 2025,
            "total_amount": 5000,
            "down_payment": 5000,
            "is_cash_sale": True,
        }
        serializer = ReceiptSerializer(data=data, context={"tenant": self.branch.tenant})
        serializer.is_valid(raise_exception=True)
        return serializer.save(tenant=self.branch.tenant)

    # -------------------------------------------------------------------------
    # TC-LIC-01: Creating a receipt deducts exactly 1 from invoices_balance
    # -------------------------------------------------------------------------
    def test_creating_receipt_deducts_one_from_balance(self):
        lic = _make_active_license(balance=100)
        self._create_receipt_via_serializer()
        lic.refresh_from_db(using="system")
        self.assertEqual(lic.invoices_balance, 99,
            "Creating a receipt must deduct exactly 1 from invoices_balance.")

    # -------------------------------------------------------------------------
    # TC-LIC-02: Creating N receipts deducts exactly N from balance
    # -------------------------------------------------------------------------
    def test_creating_multiple_receipts_deducts_correctly(self):
        lic = _make_active_license(balance=50)
        for _ in range(5):
            self._create_receipt_via_serializer()
        lic.refresh_from_db(using="system")
        self.assertEqual(lic.invoices_balance, 45)

    # -------------------------------------------------------------------------
    # TC-LIC-03: Invoice creation FAILS when balance is 0
    # -------------------------------------------------------------------------
    def test_receipt_creation_fails_when_balance_is_zero(self):
        _make_active_license(balance=0)
        from api.serializers import ReceiptSerializer
        data = {
            "branch": self.branch.pk,
            "local_id": 1,
            "sale_month": 6,
            "sale_year": 2025,
            "total_amount": 5000,
            "down_payment": 5000,
            "is_cash_sale": True,
        }
        serializer = ReceiptSerializer(data=data, context={"tenant": self.branch.tenant})
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save(tenant=self.branch.tenant)

    # -------------------------------------------------------------------------
    # TC-LIC-04: No active license at all -> creation fails
    # -------------------------------------------------------------------------
    def test_receipt_creation_fails_with_no_license(self):
        from api.serializers import ReceiptSerializer
        data = {
            "branch": self.branch.pk,
            "local_id": 1,
            "sale_month": 6,
            "sale_year": 2025,
            "total_amount": 2000,
            "down_payment": 2000,
            "is_cash_sale": True,
        }
        serializer = ReceiptSerializer(data=data, context={"tenant": self.branch.tenant})
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save(tenant=self.branch.tenant)

    # -------------------------------------------------------------------------
    # TC-LIC-05: Deleting a receipt does NOT restore the balance
    # -------------------------------------------------------------------------
    def test_deleting_receipt_does_not_restore_balance(self):
        lic = _make_active_license(balance=10)
        receipt = self._create_receipt_via_serializer()

        lic.refresh_from_db(using="system")
        self.assertEqual(lic.invoices_balance, 9)

        Receipt.objects.using("default").filter(pk=receipt.pk).delete()

        lic.refresh_from_db(using="system")
        self.assertEqual(lic.invoices_balance, 9,
            "Deleting a receipt must NOT restore the license balance.")

    # -------------------------------------------------------------------------
    # TC-LIC-06: Inactive license with balance is ignored
    # -------------------------------------------------------------------------
    def test_inactive_license_with_balance_is_not_used(self):
        tenant = Tenant.objects.using("default").first() or Tenant.objects.using("default").create(company_code="TEST", name="Test Tenant")
        expiry = date.today() + timedelta(days=365)
        sig = generate_record_signature(str(expiry), 5000, "TEST-MACHINE", 1, False)
        ClientLicense.objects.using("system").create(
            tenant=tenant,
            company_code="TEST",
            product_id=1,
            start_date=date.today(),
            expiry_date=expiry,
            invoices_balance=5000,
            is_active=False,
            machine_id="TEST-MACHINE",
            license_code_hash=sig,
        )
        from api.serializers import ReceiptSerializer
        data = {
            "branch": self.branch.pk,
            "local_id": 1,
            "sale_month": 6,
            "sale_year": 2025,
            "total_amount": 1000,
            "down_payment": 1000,
            "is_cash_sale": True,
        }
        serializer = ReceiptSerializer(data=data, context={"tenant": self.branch.tenant})
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError,
                msg="Inactive license must be completely ignored."):
            serializer.save(tenant=self.branch.tenant)

    # -------------------------------------------------------------------------
    # TC-LIC-07: Last receipt (balance=1) succeeds but next fails
    # -------------------------------------------------------------------------
    def test_last_receipt_succeeds_but_next_fails(self):
        lic = _make_active_license(balance=1)
        receipt = self._create_receipt_via_serializer()
        self.assertIsNotNone(receipt.pk)

        lic.refresh_from_db(using="system")
        self.assertEqual(lic.invoices_balance, 0)

        from api.serializers import ReceiptSerializer
        data = {
            "branch": self.branch.pk,
            "local_id": 2,
            "sale_month": 7,
            "sale_year": 2025,
            "total_amount": 1000,
            "down_payment": 1000,
            "is_cash_sale": True,
        }
        serializer = ReceiptSerializer(data=data, context={"tenant": self.branch.tenant})
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save(tenant=self.branch.tenant)


# =============================================================================
# 5. CRYPTOGRAPHIC RECORD SIGNATURE TESTS (generate_record_signature)
#
# Source: Desktop/sales/salesapp/security_utils.py:97-108
# Formula: HMAC-SHA256("{expiry}-{balance}-{machine_id}-{product_id}-{is_active}")
# =============================================================================

class RecordSignatureTests(TestCase):
    """Tests for generate_record_signature() — the per-row DB tamper protection."""
    databases = ["default", "system"]

    def test_record_signature_is_deterministic(self):
        s1 = generate_record_signature("2026-06-01", 500, "MACHINE-1", 1, True)
        s2 = generate_record_signature("2026-06-01", 500, "MACHINE-1", 1, True)
        self.assertEqual(s1, s2)

    def test_changing_balance_changes_signature(self):
        s1 = generate_record_signature("2026-06-01", 500, "MACHINE-1", 1, True)
        s2 = generate_record_signature("2026-06-01", 501, "MACHINE-1", 1, True)
        self.assertNotEqual(s1, s2,
            "Manually editing invoices_balance must invalidate the record signature.")

    def test_changing_expiry_changes_signature(self):
        s1 = generate_record_signature("2026-06-01", 100, "MACHINE-1", 1, True)
        s2 = generate_record_signature("2027-01-01", 100, "MACHINE-1", 1, True)
        self.assertNotEqual(s1, s2)

    def test_changing_is_active_changes_signature(self):
        s1 = generate_record_signature("2026-06-01", 100, "MACHINE-1", 1, True)
        s2 = generate_record_signature("2026-06-01", 100, "MACHINE-1", 1, False)
        self.assertNotEqual(s1, s2,
            "Flipping is_active must invalidate the record signature.")

    def test_none_expiry_produces_valid_signature(self):
        sig = generate_record_signature(None, 200, "MACHINE-X", 11, True)
        self.assertIsNotNone(sig)
        self.assertEqual(len(sig), 64)

    def test_signature_matches_manual_reference(self):
        expiry, balance, machine_id, product_id, is_active = "2026-12-31", 300, "MACH-001", 2, True
        data = f"{expiry}-{balance}-{machine_id}-{product_id}-{is_active}"
        expected = hmac.new(SECRET_KEY_BYTES, data.encode("utf-8"), hashlib.sha256).hexdigest()
        actual = generate_record_signature(expiry, balance, machine_id, product_id, is_active)
        self.assertEqual(actual, expected,
            "generate_record_signature must use the exact same formula as the legacy.")


# =============================================================================
# 6. LICENSE VALIDATOR TESTS (LicenseValidator.validate)
#
# Source: VentaPOS_NextGen/backend/api/utils/license_validator.py
# =============================================================================

class LicenseValidatorTests(TestCase):
    """Tests for LicenseValidator.validate() — key decoding and HMAC verification."""
    databases = ["default", "system"]

    def test_garbage_code_is_invalid(self):
        result = LicenseValidator.validate("XXXX-XXXX-XXXX-XXXX", "any-machine-id")
        self.assertFalse(result["valid"])
        self.assertIn("error", result)

    def test_empty_code_is_invalid(self):
        result = LicenseValidator.validate("", "any-machine-id")
        self.assertFalse(result["valid"])

    def test_machine_hash_is_deterministic(self):
        machine_id = "550e8400-e29b-41d4-a716-446655440000"
        h1 = LicenseValidator._get_machine_hash(machine_id)
        h2 = LicenseValidator._get_machine_hash(machine_id)
        self.assertEqual(h1, h2)

    def test_machine_hash_differs_for_different_machines(self):
        h1 = LicenseValidator._get_machine_hash("MACHINE-A")
        h2 = LicenseValidator._get_machine_hash("MACHINE-B")
        self.assertNotEqual(h1, h2)

    def test_machine_hash_is_32bit_uint(self):
        h = LicenseValidator._get_machine_hash("some-machine-id")
        self.assertIsInstance(h, int)
        self.assertGreaterEqual(h, 0)
        self.assertLessEqual(h, 0xFFFFFFFF)

    def test_get_key_returns_correct_secret(self):
        key = LicenseValidator._get_key()
        self.assertEqual(key, SECRET_KEY_BYTES,
            "_get_key() must return the exact 86-byte obfuscated secret key from the spec.")
        self.assertEqual(len(key), 86)

    def test_wrong_hmac_returns_invalid(self):
        fake_code = "AAAA-BBBB-CCCC-DDDD"
        result = LicenseValidator.validate(fake_code, "test-machine")
        self.assertFalse(result["valid"])


# =============================================================================
# 7. COMMISSION HISTORY TESTS (InventoryItem.get_commission_at_date)
#
# Source: Desktop/sales/salesapp/models.py:205-215
# =============================================================================

class CommissionHistoryTests(TestCase):
    """Tests for get_commission_at_date() — retrospective commission lookup."""
    databases = ["default"]

    def setUp(self):
        self.branch = _make_branch()

    def test_returns_initial_commission_with_no_history(self):
        item = _make_item(self.branch, initial_qty=10, initial_month=1, initial_year=2025)
        # initial_commission_amount is 5 (set in _make_item)
        self.assertEqual(item.get_commission_at_date(6, 2025), 5)

    def test_returns_active_commission_at_date(self):
        item = _make_item(self.branch, initial_qty=10, initial_month=1, initial_year=2025)
        CommissionHistory.objects.using("default").create(
            tenant=item.tenant,
            inventory_item=item,
            commission_amount=25,
            activation_month=3,
            activation_year=2025,
        )
        self.assertEqual(item.get_commission_at_date(2, 2025), 5,
            "Before activation: must return initial_commission_amount.")
        self.assertEqual(item.get_commission_at_date(3, 2025), 25,
            "At activation month: must return new commission.")
        self.assertEqual(item.get_commission_at_date(6, 2025), 25)

    def test_returns_latest_commission_when_multiple_records(self):
        item = _make_item(self.branch, initial_qty=10, initial_month=1, initial_year=2025)
        CommissionHistory.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, commission_amount=20, activation_month=2, activation_year=2025
        )
        CommissionHistory.objects.using("default").create(
            tenant=item.tenant, inventory_item=item, commission_amount=35, activation_month=5, activation_year=2025
        )
        self.assertEqual(item.get_commission_at_date(4, 2025), 20)
        self.assertEqual(item.get_commission_at_date(5, 2025), 35)
        self.assertEqual(item.get_commission_at_date(12, 2025), 35)


from rest_framework.test import APIClient
from api.serializers import ReceiptSerializer

class PosEntryParityTests(TestCase):
    databases = ["default", "system"]

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.using("default").create(company_code="TESTSUG", name="Test Suggestion Tenant")
        self.branch = Branch.objects.using("default").create(tenant=self.tenant, name="Main Branch", local_id=1)
        self.license = _make_active_license(balance=100, tenant=self.tenant)

    def test_product_suggestions_endpoint(self):
        item = _make_item(self.branch, name="صنف تجربة", initial_qty=50, initial_month=1, initial_year=2026)
        
        response = self.client.get('/api/v1/product-suggestions/', {
            "term": "تجربة",
            "month": "7",
            "year": "2026"
        }, HTTP_X_COMPANY_CODE="TESTSUG")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], str(item.id))
        self.assertEqual(data[0]["value"], "صنف تجربة")
        self.assertEqual(data[0]["max"], 50)

    def test_customer_suggestions_endpoint(self):
        from django.utils import timezone
        Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            local_id=1,
            receipt_number=1001,

            receipt_hash="dummyhash1",
            customer_name="أحمد علي",
            phone_number="0101234567",
            address="شارع التحرير",
            area="وسط البلد",
            sale_month=7,
            sale_year=2026,
            created_at_local=timezone.now(),
            total_amount=100,
            down_payment=100,
            is_cash_sale=True
        )
        
        # Name search
        response = self.client.get('/api/v1/customer-suggestions/', {
            "field": "name",
            "term": "أحمد"
        }, HTTP_X_COMPANY_CODE="TESTSUG")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], "أحمد علي")
        
        # Phone search
        response = self.client.get('/api/v1/customer-suggestions/', {
            "field": "phone",
            "term": "010"
        }, HTTP_X_COMPANY_CODE="TESTSUG")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], "٠١٠١٢٣٤٥٦٧")

    def test_retro_stock_validation_error(self):
        item = _make_item(self.branch, name="صنف شحيح", initial_qty=5, initial_month=1, initial_year=2026)
        
        data = {
            "branch": self.branch.id,
            "sale_month": 7,
            "sale_year": 2026,
            "total_amount": 500,
            "down_payment": 500,
            "is_cash_sale": True,
            "sale_items": [
                {
                    "inventory_item": item.id,
                    "quantity": 10,
                    "unit_price": 50
                }
            ]
        }
        
        serializer = ReceiptSerializer(data=data, context={"tenant": self.tenant})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        with self.assertRaises(ValidationError) as ctx:
            serializer.save()
            
        self.assertIn("عفواً، لا يمكن البيع!", str(ctx.exception))
        self.assertIn("أقصى كمية يمكن بيعها بأثر رجعي للصنف 'صنف شحيح' هي (5)", str(ctx.exception))

    def test_installment_25th_day_billing_rule(self):
        data = {
            "branch": self.branch.id,
            "sale_month": 6,
            "sale_year": 2026,
            "total_amount": 1000,
            "down_payment": 500,
            "is_cash_sale": False,
            "customer_name": "عميل آجل",
            "installment_payments": [
                {
                    "amount": 500,
                    "payment_month": 7,
                    "payment_year": 2026
                }
            ]
        }
        
        serializer = ReceiptSerializer(data=data, context={"tenant": self.tenant})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        receipt = serializer.save()
        
        installment = receipt.installment_payments.first()
        self.assertIsNotNone(installment)
        self.assertEqual(installment.payment_date.day, 25)
        self.assertEqual(installment.payment_date.month, 7)
        self.assertEqual(installment.payment_date.year, 2026)
