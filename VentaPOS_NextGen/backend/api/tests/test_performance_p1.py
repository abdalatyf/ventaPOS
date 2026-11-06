from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from api.models import (
    Branch, Supplier, InventoryItem, PurchaseInvoice, PurchaseInvoiceItem,
    Salesperson, Receipt, SaleItem, InventoryAdjustment, ClientLicense
)
from api.utils.security_utils import get_machine_id, generate_record_signature


class PerformanceP1Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.client.force_authenticate(user=self.admin_user)

        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 10000, mach_id, 1, True)

        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=10000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig
        )

        self.branch = Branch.objects.create(name="Performance Branch")
        self.supplier = Supplier.objects.create(name="Performance Supplier")
        self.salesperson = Salesperson.objects.create(name="Performance Rep", branch=self.branch)

        # Create 25 inventory items
        self.items = []
        for i in range(1, 26):
            item = InventoryItem.objects.create(
                branch=self.branch,
                name=f"Performance Item {i:02d}",
                initial_quantity=50,
                initial_purchase_price=100.0,
                initial_commission_amount=10.0,
                initial_month=1,
                initial_year=2025
            )
            self.items.append(item)

        # Inbound purchases in month 1 and 2
        p_inv1 = PurchaseInvoice.objects.create(
            branch=self.branch, supplier=self.supplier, invoice_number=101,
            invoice_type="PURCHASE", invoice_month=1, invoice_year=2025
        )
        p_inv2 = PurchaseInvoice.objects.create(
            branch=self.branch, supplier=self.supplier, invoice_number=102,
            invoice_type="PURCHASE", invoice_month=2, invoice_year=2025
        )
        for item in self.items:
            PurchaseInvoiceItem.objects.create(invoice=p_inv1, inventory_item=item, quantity=10, purchase_price=105.0)
            PurchaseInvoiceItem.objects.create(invoice=p_inv2, inventory_item=item, quantity=5, purchase_price=110.0)

        # Sales in month 2 and 3
        rcpt1 = Receipt.objects.create(
            branch=self.branch, salesperson=self.salesperson, receipt_number=1,
            receipt_type="SALE", sale_month=2, sale_year=2025, total_amount=1000.0,
            is_cash_sale=True, is_confirmed=True
        )
        rcpt2 = Receipt.objects.create(
            branch=self.branch, salesperson=self.salesperson, receipt_number=2,
            receipt_type="SALE", sale_month=3, sale_year=2025, total_amount=1500.0,
            is_cash_sale=True, is_confirmed=True
        )
        for item in self.items[:15]:
            SaleItem.objects.create(receipt=rcpt1, inventory_item=item, quantity=2, unit_price=150.0)
            SaleItem.objects.create(receipt=rcpt2, inventory_item=item, quantity=3, unit_price=160.0)

        # Returns in month 3
        rcpt_ret = Receipt.objects.create(
            branch=self.branch, parent_receipt=rcpt1, salesperson=self.salesperson, receipt_number=3,
            receipt_type="RETURN", sale_month=3, sale_year=2025, total_amount=150.0,
            is_cash_sale=True, is_confirmed=True
        )
        for item in self.items[:5]:
            SaleItem.objects.create(receipt=rcpt_ret, inventory_item=item, quantity=1, unit_price=150.0)

        # Deficits in month 3
        for item in self.items[15:]:
            InventoryAdjustment.objects.create(
                item=item, adjustment_type="DEFICIT", quantity=1, month=3, year=2025
            )

    def test_product_suggestions_query_count(self):
        """Verify ProductSuggestionsView runs in <= 8 queries for 25 items."""
        url = f"/api/v1/product-suggestions/?term=Performance&month=3&year=2025&branch_id={self.branch.id}"
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 25)
        # 1 DefaultDate, 1 items_qs, 3 grouped stock queries = 5 queries total
        self.assertLessEqual(
            len(queries), 8,
            f"Expected <= 8 queries for ProductSuggestionsView, got {len(queries)}"
        )

    def test_inventory_movement_report_query_count(self):
        """Verify InventoryMovementReportView runs in <= 10 total queries (<= 7 report queries + 3 license middleware) for 25 items."""
        url = f"/api/v1/reports/inventory-movement/?branch_id={self.branch.id}&year=2025&month=3"
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("items", [])), 25)
        self.assertLessEqual(
            len(queries), 10,
            f"Expected <= 10 queries for InventoryMovementReportView, got {len(queries)}"
        )

    def test_inventory_items_list_query_count(self):
        """Verify GET /api/v1/inventory-items/ runs in <= 8 total queries (<= 4 list queries + 3 license middleware) with precomputed stock."""
        url = f"/api/v1/inventory-items/?branch_id={self.branch.id}"
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(queries), 8,
            f"Expected <= 8 queries for InventoryItemViewSet list, got {len(queries)}"
        )

    def test_receipts_list_has_returns_query_count(self):
        """Verify GET /api/v1/receipts/ runs in <= 12 total queries (O(1) constant queries, 0 per-receipt queries)."""
        url = f"/api/v1/receipts/?branch_id={self.branch.id}"
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(queries), 12,
            f"Expected <= 12 queries for ReceiptViewSet list, got {len(queries)}"
        )
