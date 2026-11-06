"""
Tests for Deficit Loss, Date-Based Buying Price Ranges, Product Ledger Lifecycle,
and Commission History Upsert.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import (
    Branch,
    Supplier,
    Salesperson,
    InventoryItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    Receipt,
    SaleItem,
    InventoryAdjustment,
    CommissionHistory,
)


class DeficitLossAndLedgerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.client.force_authenticate(user=self.admin_user)
        self.branch = Branch.objects.create(name="فرع الهرم")
        self.supplier = Supplier.objects.create(name="مورد أجهزة")
        self.salesperson = Salesperson.objects.create(name="محمد علي", branch=self.branch)

    def test_adjustment_model_and_serializer_deficit_only(self):
        """Verify InventoryAdjustment strictly defaults to DEFICIT."""
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة توشيبا",
            initial_quantity=20,
            initial_purchase_price=5000,
            initial_commission_amount=50,
            initial_month=1,
            initial_year=2026,
        )

        # Create via model without specifying adjustment_type
        adj = InventoryAdjustment.objects.create(
            item=item,
            quantity=3,
            reason="تالف نقل",
            month=2,
            year=2026,
        )
        self.assertEqual(adj.adjustment_type, "DEFICIT")
        self.assertEqual(item.get_stock_at_date(2, 2026), 17)

        # Create via API without specifying adjustment_type
        res = self.client.post("/api/v1/inventory-adjustments/", {
            "item": item.id,
            "quantity": 2,
            "reason": "عجز فحص",
            "month": 3,
            "year": 2026,
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["adjustment_type"], "DEFICIT")
        self.assertEqual(item.get_stock_at_date(3, 2026), 15)

    def test_date_based_buying_price_ranges_and_deficit_loss(self):
        """
        Verify Deficit losses use date-based buying price ranges:
        Range 1: Initial purchase price = 1000 (Months 1-3)
        Range 2: New purchase invoice in Month 4 at price = 1500 (Months 4-12)
        Deficit in Month 2: 2 units * 1000 = 2000
        Deficit in Month 5: 3 units * 1500 = 4500
        Total Deficit Loss = 6500 (NOT 5 units * 1500 = 7500)
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة سامسونج",
            initial_quantity=10,
            initial_purchase_price=1000,
            initial_commission_amount=40,
            initial_month=1,
            initial_year=2026,
        )

        # Deficit in Month 2 (Range 1: cost 1000)
        InventoryAdjustment.objects.create(
            item=item,
            quantity=2,
            reason="كسر شاشة",
            month=2,
            year=2026,
        )

        # Purchase in Month 4 at 1500
        pinv = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_month=4,
            invoice_year=2026,
            invoice_type="PURCHASE",
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pinv,
            inventory_item=item,
            quantity=10,
            purchase_price=1500,
        )

        # Deficit in Month 5 (Range 2: cost 1500)
        InventoryAdjustment.objects.create(
            item=item,
            quantity=3,
            reason="فقدان كابلات وشاشة",
            month=5,
            year=2026,
        )

        # Verify get_price_at_date reflects ranges
        self.assertEqual(item.get_price_at_date(2, 2026), 1000)
        self.assertEqual(item.get_price_at_date(4, 2026), 1500)
        self.assertEqual(item.get_price_at_date(5, 2026), 1500)

        # Verify Dashboard Report for Month 2
        res_m2 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 2,
        })
        self.assertEqual(res_m2.status_code, 200)
        kpis_m2 = res_m2.json()["kpis"]
        self.assertEqual(kpis_m2["total_deficit_loss"], 2000)
        # estimated_net_profit should deduct deficit loss
        self.assertEqual(kpis_m2["estimated_net_profit"], -2000)

        # Verify Dashboard Report for Month 5
        res_m5 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 5,
        })
        self.assertEqual(res_m5.status_code, 200)
        kpis_m5 = res_m5.json()["kpis"]
        self.assertEqual(kpis_m5["total_deficit_loss"], 4500)
        self.assertEqual(kpis_m5["estimated_net_profit"], -4500)

        # Verify Profit & Loss Report for Month 2
        res_pl_m2 = self.client.get("/api/v1/reports/sales-pl/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 2,
        })
        self.assertEqual(res_pl_m2.status_code, 200)
        pl_m2 = res_pl_m2.json()["summary"]
        self.assertEqual(pl_m2["deficit_loss"], 2000)
        self.assertEqual(pl_m2["net_profit_final"], -2000)

        # Verify Profit & Loss Report for Month 5
        res_pl_m5 = self.client.get("/api/v1/reports/sales-pl/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 5,
        })
        self.assertEqual(res_pl_m5.status_code, 200)
        pl_m5 = res_pl_m5.json()["summary"]
        self.assertEqual(pl_m5["deficit_loss"], 4500)
        self.assertEqual(pl_m5["net_profit_final"], -4500)

    def test_product_ledger_full_lifecycle_and_metrics(self):
        """
        Verify Product Ledger endpoint returns complete lifecycle from INITIAL to last event,
        with running stock, unit costs, deficit loss, and price change indicators.
        """
        # 1. INITIAL: 10 units at 2000 in (1, 2026)
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="بوتاجاز يونيون اير",
            initial_quantity=10,
            initial_purchase_price=2000,
            initial_commission_amount=50,
            initial_month=1,
            initial_year=2026,
        )

        # 2. PURCHASE: 5 units at 2500 in (2, 2026) -> price change!
        pinv = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_month=2,
            invoice_year=2026,
            invoice_type="PURCHASE",
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pinv,
            inventory_item=item,
            quantity=5,
            purchase_price=2500,
        )

        # 3. COMMISSION CHANGE in (2, 2026)
        CommissionHistory.objects.create(
            item=item,
            commission_amount=60,
            activation_month=2,
            activation_year=2026,
        )

        # 4. SALE: 4 units at 3500 in (3, 2026)
        # Unit cost is 2500 (from Range 2). Commission is 60. Net profit per unit = 3500 - 2500 - 60 = 940.
        # Total profit for 4 units = 3760.
        rec = Receipt.objects.create(
            branch=self.branch,
            receipt_number=101,
            customer_name="أحمد محمود",
            salesperson=self.salesperson,
            sale_month=3,
            sale_year=2026,
            is_cash_sale=True,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=rec,
            inventory_item=item,
            quantity=4,
            unit_price=3500,
        )

        # 5. DEFICIT: 1 unit in (3, 2026)
        # Unit cost is 2500. Loss amount = 2500.
        InventoryAdjustment.objects.create(
            item=item,
            quantity=1,
            reason="تالف في التخزين",
            month=3,
            year=2026,
        )

        # 6. RETURN to supplier: 2 units in (4, 2026)
        pinv_ret = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=2,
            invoice_month=4,
            invoice_year=2026,
            invoice_type="RETURN",
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pinv_ret,
            inventory_item=item,
            quantity=2,
            purchase_price=2500,
        )

        # Query Ledger API
        res = self.client.get(f"/api/v1/inventory-items/{item.id}/ledger/")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check item_info
        item_info = data["item_info"]
        self.assertEqual(item_info["name"], "بوتاجاز يونيون اير")
        self.assertEqual(item_info["initial_quantity"], 10)
        self.assertEqual(item_info["initial_purchase_price"], 2000.0)
        self.assertEqual(item_info["current_purchase_price"], 2500.0)
        self.assertEqual(item_info["current_commission"], 60.0)
        # Stock: 10 (init) + 5 (purchase) - 4 (sale) - 1 (deficit) - 2 (return) = 8
        self.assertEqual(item_info["current_stock"], 8)

        # Check timeline order and event types
        timeline = data["timeline"]
        types = [e["type"] for e in timeline]
        self.assertIn("INITIAL", types)
        self.assertIn("PURCHASE", types)
        self.assertIn("COMMISSION_CHANGE", types)
        self.assertIn("SALE", types)
        self.assertIn("DEFICIT", types)
        self.assertIn("RETURN", types)

        # Check running stocks
        # 1. INITIAL (Month 1): 10
        # 2. COMMISSION_CHANGE (Month 2, priority 1): 10
        # 3. PURCHASE (Month 2, priority 2): 15
        # 4. SALE (Month 3, priority 4): 11
        # 5. DEFICIT (Month 3, priority 6): 10
        # 6. RETURN (Month 4, priority 3): 8
        running_stocks = [e["running_stock"] for e in timeline]
        self.assertEqual(running_stocks, [10, 10, 15, 11, 10, 8])

        # Check PURCHASE price change indicator
        purchase_event = [e for e in timeline if e["type"] == "PURCHASE"][0]
        self.assertTrue(purchase_event.get("is_price_change"))
        self.assertEqual(purchase_event["price"], 2500.0)

        # Check DEFICIT event details
        deficit_event = [e for e in timeline if e["type"] == "DEFICIT"][0]
        self.assertEqual(deficit_event["quantity"], 1)
        self.assertEqual(deficit_event["unit_cost"], 2500.0)
        self.assertEqual(deficit_event["loss_amount"], 2500.0)

        # Check dashboard_metrics:
        # total_profit = 3760 (from sale) - 2500 (from deficit) = 1260
        metrics = data["dashboard_metrics"]
        self.assertEqual(metrics["deficit_loss"], 2500.0)
        self.assertEqual(metrics["total_profit"], 1260.0)

    def test_commission_history_upsert(self):
        """
        Verify CommissionHistoryViewSet creates new record or updates existing record
        for the same (item, activation_month, activation_year) without database error.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="مروحة عمود",
            initial_quantity=5,
            initial_purchase_price=300,
            initial_commission_amount=15,
            initial_month=1,
            initial_year=2026,
        )

        # 1. Initial commission creation via API
        res1 = self.client.post("/api/v1/commission-history/", {
            "item": item.id,
            "commission_amount": 25,
            "activation_month": 4,
            "activation_year": 2026,
        })
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(CommissionHistory.objects.filter(item=item, activation_month=4, activation_year=2026).count(), 1)
        self.assertEqual(item.get_commission_at_date(4, 2026), 25)

        # 2. Update commission for same month/year via API (must UPSERT, not error 400/500)
        res2 = self.client.post("/api/v1/commission-history/", {
            "item": item.id,
            "commission_amount": 35,
            "activation_month": 4,
            "activation_year": 2026,
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(CommissionHistory.objects.filter(item=item, activation_month=4, activation_year=2026).count(), 1)
        self.assertEqual(item.get_commission_at_date(4, 2026), 35)
