import uuid
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from api.models import Tenant, Branch, Supplier, InventoryItem, PurchaseInvoice, PurchaseInvoiceItem

class PriceHistoryTests(TestCase):
    databases = ["default", "system"]

    def setUp(self):
        self.tenant = Tenant.objects.using("default").create(
            company_code="TESTC",
            name="Test Tenant",
            is_active=True
        )
        self.branch = Branch.objects.using("default").create(
            tenant=self.tenant,
            name="Test Branch",
            local_id=1
        )
        self.supplier = Supplier.objects.using("default").create(
            tenant=self.tenant,
            name="Test Supplier"
        )
        # Create an inventory item with initial purchase price of 100.00
        self.item = InventoryItem.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            local_id=1,
            name="Test Item",
            initial_quantity=10,
            initial_purchase_price=100,
            initial_commission_amount=5,
            initial_month=1,
            initial_year=2025
        )

    def test_fallback_no_purchase_history(self):
        # 1. Fallback to initial purchase price when there is no purchase invoice history.
        price = self.item.get_price_at_date(month=5, year=2026)
        self.assertEqual(price, 100)

    def test_fallback_purchases_after_queried_period(self):
        # 2. Fallback to initial purchase price when there are purchases, but all of them are after the queried month/year.
        invoice = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_type="PURCHASE",
            invoice_month=6,
            invoice_year=2026
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant,
            purchase_invoice=invoice,
            inventory_item=self.item,
            quantity=5,
            purchase_price=150
        )

        price = self.item.get_price_at_date(month=5, year=2026)
        self.assertEqual(price, 100)

    def test_retrieve_price_same_month_year(self):
        # 3. Retrieving the price from a purchase invoice in the same month/year.
        invoice = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_type="PURCHASE",
            invoice_month=5,
            invoice_year=2026
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant,
            purchase_invoice=invoice,
            inventory_item=self.item,
            quantity=5,
            purchase_price=150
        )

        price = self.item.get_price_at_date(month=5, year=2026)
        self.assertEqual(price, 150)

    def test_retrieve_price_prior_year(self):
        # 4. Retrieving the price from a purchase invoice in a prior year.
        invoice = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_type="PURCHASE",
            invoice_month=12,
            invoice_year=2025
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant,
            purchase_invoice=invoice,
            inventory_item=self.item,
            quantity=5,
            purchase_price=120
        )

        price = self.item.get_price_at_date(month=5, year=2026)
        self.assertEqual(price, 120)

    def test_retrieve_most_recent_price_sorting(self):
        # 5. Retrieving the most recent price when multiple purchase invoices exist in the queried period (sorting by year, month, and created_at descending).
        # We will create invoices:
        # A: 2025-10: price 110.00
        # B: 2026-03: price 130.00
        # C: 2026-05: price 140.00 (created first)
        # D: 2026-05: price 160.00 (created later)
        
        # A
        inv_a = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=1, invoice_type="PURCHASE", invoice_month=10, invoice_year=2025
        )
        item_a = PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_a, inventory_item=self.item,
            quantity=5, purchase_price=110
        )
        
        # B
        inv_b = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=2, invoice_type="PURCHASE", invoice_month=3, invoice_year=2026
        )
        item_b = PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_b, inventory_item=self.item,
            quantity=5, purchase_price=130
        )
        
        # C
        inv_c = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=3, invoice_type="PURCHASE", invoice_month=5, invoice_year=2026
        )
        item_c = PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_c, inventory_item=self.item,
            quantity=5, purchase_price=140
        )
        
        # D
        inv_d = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=4, invoice_type="PURCHASE", invoice_month=5, invoice_year=2026
        )
        item_d = PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_d, inventory_item=self.item,
            quantity=5, purchase_price=160
        )

        # Force distinct created_at timestamps to ensure exact ordering
        now = timezone.now()
        PurchaseInvoiceItem.objects.filter(id=item_a.id).update(created_at=now - timedelta(hours=3))
        PurchaseInvoiceItem.objects.filter(id=item_b.id).update(created_at=now - timedelta(hours=2))
        PurchaseInvoiceItem.objects.filter(id=item_c.id).update(created_at=now - timedelta(hours=1))
        PurchaseInvoiceItem.objects.filter(id=item_d.id).update(created_at=now)

        # Test querying at 2026-05 (should get 160.00 from item D)
        self.assertEqual(self.item.get_price_at_date(month=5, year=2026), 160)

        # Test querying at 2026-04 (should get 130.00 from item B)
        self.assertEqual(self.item.get_price_at_date(month=4, year=2026), 130)

        # Test querying at 2025-12 (should get 110.00 from item A)
        self.assertEqual(self.item.get_price_at_date(month=12, year=2025), 110)

    def test_ignore_deleted_and_returns(self):
        # 6. Correctly ignoring soft-deleted purchase invoice items or invoices of type "RETURN".
        # Invoice of type RETURN (not purchase)
        inv_return = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=1, invoice_type="RETURN", invoice_month=5, invoice_year=2026
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_return, inventory_item=self.item,
            quantity=5, purchase_price=180
        )

        # Deleted purchase invoice item
        inv_deleted_item = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=2, invoice_type="PURCHASE", invoice_month=5, invoice_year=2026
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_deleted_item, inventory_item=self.item,
            quantity=5, purchase_price=190, is_deleted=True
        )

        # Purchase invoice item under a deleted purchase invoice
        inv_deleted_header = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=3, invoice_type="PURCHASE", invoice_month=5, invoice_year=2026,
            is_deleted=True
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_deleted_header, inventory_item=self.item,
            quantity=5, purchase_price=200
        )

        # Valid purchase invoice item (so we have a non-deleted fallback)
        inv_valid = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, supplier=self.supplier,
            invoice_number=4, invoice_type="PURCHASE", invoice_month=4, invoice_year=2026
        )
        PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant, purchase_invoice=inv_valid, inventory_item=self.item,
            quantity=5, purchase_price=140
        )

        # At month 5, we should ignore 180.00 (RETURN), 190.00 (is_deleted=True), and 200.00 (invoice is_deleted=True)
        # And get 140.00 from the valid purchase in month 4.
        self.assertEqual(self.item.get_price_at_date(month=5, year=2026), 140)
