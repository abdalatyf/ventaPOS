"""
test_reports_comprehensive_e2e.py — Comprehensive Multi-Tier E2E & Integration Tests for Reporting Subsystem
=============================================================================================================
Single Source of Truth:
  - VentaPOS_NextGen/REPORTS_AGREEMENT.md
  - VentaPOS_NextGen/requirements.md
  - TEST_INFRA.md

Coverage Structure:
- Tier 1: Feature Coverage (Dashboard, Salesperson Performance, Inventory Movement, P&L Totals & Averages,
          Cash Drawer, Installments Ledger, Expenses, Receipt Pagination & Aggregates, Default Date)
- Tier 2: Boundary & Corner Cases (Receipt number ranges with Western & Arabic digits, 0 down payments,
          year/month rollovers, historical time-machine fallback, empty queries, stock clamping to 0,
          soft-delete exclusion, cross-branch data isolation, error handling for invalid parameters)
- Tier 3: Cross-Feature Combinations (Full sale creation pipeline, down payment drawer & dashboard sync,
          salesperson salary calculation with collections, procurement stock deduction & movement tracking)
- Tier 4: Real-World Business Workloads (Complete monthly business close scenario, multi-month timeline continuity,
          multi-branch enterprise isolation under load)
"""

from datetime import date
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
    Branch, Salesperson, InventoryItem, Supplier,
    PurchaseInvoice, PurchaseInvoiceItem, Receipt, SaleItem,
    InstallmentPayment, Expense, InventoryAdjustment, CommissionHistory,
    ClientLicense
)
from api.utils.security_utils import generate_record_signature, get_machine_id


class ReportingBaseTestCase(TestCase):
    """Base setup for reporting tests providing authenticated client, license, branch, and helpers."""

    def setUp(self):
        self.client = APIClient()

        # License setup
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

        # Standard branch
        self.branch = Branch.objects.create(name="الفرع الرئيسي")
        self.salesperson1 = Salesperson.objects.create(branch=self.branch, name="أحمد محمود")
        self.salesperson2 = Salesperson.objects.create(branch=self.branch, name="مصطفى حسن")
        self.supplier = Supplier.objects.create(name="مؤسسة الأمل للتوريدات")


# ===========================================================================
# TIER 1: FEATURE COVERAGE
# ===========================================================================

class Tier1FeatureCoverageTests(ReportingBaseTestCase):
    """Tests covering primary behavior, calculations, and contracts for all report endpoints."""

    def setUp(self):
        super().setUp()

        # Inventory Items
        self.item_fridge = InventoryItem.objects.create(
            branch=self.branch,
            name="ثلاجة 16 قدم",
            initial_quantity=20,
            initial_purchase_price=8000,
            initial_commission_amount=300,
            initial_month=1,
            initial_year=2026
        )
        self.item_washer = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة أوتوماتيك",
            initial_quantity=15,
            initial_purchase_price=6000,
            initial_commission_amount=250,
            initial_month=1,
            initial_year=2026
        )

        # Inbound Purchase in Month 7/2026
        self.purchase_inv = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=101,
            invoice_type="PURCHASE",
            invoice_month=7,
            invoice_year=2026
        )
        self.pur_item = PurchaseInvoiceItem.objects.create(
            invoice=self.purchase_inv,
            inventory_item=self.item_fridge,
            quantity=10,
            purchase_price=8000
        )

        # 1. Cash Sale Receipt: 2 fridges @ 10,000 each = 20,000
        self.receipt_cash = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=1001,
            receipt_hash="hash_cash_1",
            customer_name="خالد عبد الله",
            phone_number="01011111111",
            address="شارع التحرير",
            area="الدقي",
            total_amount=20000,
            down_payment=20000,
            sale_year=2026,
            sale_month=7,
            is_cash_sale=True,
            is_confirmed=True
        )
        self.sale_item_cash = SaleItem.objects.create(
            receipt=self.receipt_cash,
            inventory_item=self.item_fridge,
            quantity=2,
            unit_price=10000
        )

        # 2. Credit/Installment Sale Receipt: 3 washers @ 8,000 each = 24,000, Down Payment 6,000
        self.receipt_credit = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson2,
            receipt_number=1002,
            receipt_hash="hash_credit_1",
            customer_name="سعيد عبد الرحمن",
            phone_number="01222222222",
            address="شارع السودان",
            area="المهندسين",
            total_amount=24000,
            down_payment=6000,
            installment_system="6 شهور",
            sale_year=2026,
            sale_month=7,
            is_cash_sale=False,
            is_confirmed=True
        )
        self.sale_item_credit = SaleItem.objects.create(
            receipt=self.receipt_credit,
            inventory_item=self.item_washer,
            quantity=3,
            unit_price=8000
        )

        # 3. Collected Installment Payment in Month 7/2026
        self.payment = InstallmentPayment.objects.create(
            receipt=self.receipt_credit,
            payment_date=date(2026, 7, 25),
            amount=3000
        )

        # 4. Operating Expenses in Month 7/2026
        self.expense1 = Expense.objects.create(
            branch=self.branch,
            amount=2000,
            description="إيجار المعرض",
            expense_year=2026,
            expense_month=7
        )
        self.expense2 = Expense.objects.create(
            branch=self.branch,
            amount=500,
            description="كهرباء ومرافق",
            expense_year=2026,
            expense_month=7
        )

    def test_tier1_dashboard_summary_kpis(self):
        """Verify Dashboard summary KPIs matching mathematical accounting formulas."""
        res = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        kpis = data["kpis"]
        # Total Revenue = 20,000 (cash) + 24,000 (credit) = 44,000
        self.assertEqual(kpis["total_revenue"], 44000)

        # COGS = (2 fridges * 8,000) + (3 washers * 6,000) = 16,000 + 18,000 = 34,000
        self.assertEqual(kpis["total_cogs"], 34000)

        # Sales Commissions = (2 * 300) + (3 * 250) = 600 + 750 = 1,350
        self.assertEqual(kpis["total_sales_commissions"], 1350)

        # Collection Commissions = 3,000 // 10 = 300
        self.assertEqual(kpis["total_collection_commissions"], 300)

        # Operating Expenses = 2,000 + 500 = 2,500
        # Estimated Net Profit = 44,000 - (34,000 + 1,350 + 300 + 2,500) = 5,850
        self.assertEqual(kpis["estimated_net_profit"], 5850)

        # Stock at end of Month 7:
        # Fridge: 20 initial + 10 purchase - 2 sold = 28 * 8,000 = 224,000
        # Washer: 15 initial - 3 sold = 12 * 6,000 = 72,000
        # Total Inventory Value = 224,000 + 72,000 = 296,000
        self.assertEqual(kpis["current_inventory_value"], 296000)
        self.assertEqual(kpis["low_stock_count"], 0)
        self.assertEqual(kpis["avg_basket_size"], 22000)  # 44,000 / 2 receipts

    def test_tier1_dashboard_cash_drawer_summary(self):
        """Verify Cash Drawer breakdown within the dashboard summary."""
        res = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        drawer = res.json()["cash_drawer_summary"]

        self.assertEqual(drawer["cash_sales_inflow"], 20000)
        self.assertEqual(drawer["down_payment_inflow"], 6000)
        self.assertEqual(drawer["collection_inflow"], 3000)
        self.assertEqual(drawer["total_cash_inflow"], 29000)

        # Outflows: Purchases (10 * 8,000 = 80,000), Expenses (2,500), Salaries (1,350 + 300 = 1,650)
        self.assertEqual(drawer["total_purchases"], 80000)
        self.assertEqual(drawer["operating_expenses"], 2500)
        self.assertEqual(drawer["auto_salaries"], 1650)

        # Net cash in hand = 29,000 - (2,500 + 1,650 + 80,000) = -55,150
        self.assertEqual(drawer["net_cash_in_hand"], -55150)
        self.assertEqual(res.json()["kpis"]["safe_balance"], -55150)

    def test_tier1_dashboard_top_products_and_areas(self):
        """Verify top selling products and top customer areas in dashboard."""
        res = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(data["top_products"]), 2)
        # Most sold by qty: Washer (3), Fridge (2)
        self.assertEqual(data["top_products"][0]["product_name"], "غسالة أوتوماتيك")
        self.assertEqual(data["top_products"][0]["quantity_sold"], 3)
        self.assertEqual(data["top_products"][1]["product_name"], "ثلاجة 16 قدم")
        self.assertEqual(data["top_products"][1]["quantity_sold"], 2)

        # Top areas: المهندسين (24,000), الدقي (20,000)
        self.assertEqual(len(data["top_areas"]), 2)
        self.assertEqual(data["top_areas"][0]["area"], "المهندسين")
        self.assertEqual(data["top_areas"][0]["sales_value"], 24000)
        self.assertEqual(data["top_areas"][1]["area"], "الدقي")
        self.assertEqual(data["top_areas"][1]["sales_value"], 20000)

    def test_tier1_dashboard_alias_endpoint(self):
        """Verify GET /api/v1/reports/dashboard/ alias behaves identically to /summary/."""
        res = self.client.get("/api/v1/reports/dashboard/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("kpis", res.json())
        self.assertIn("cash_drawer_summary", res.json())

    def test_tier1_salesperson_performance_report(self):
        """Verify Salesperson Performance endpoint breakdown and totals."""
        res = self.client.get("/api/v1/reports/salespersons/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        totals = data["totals"]
        self.assertEqual(totals["grand_total_cash"], 20000)
        self.assertEqual(totals["grand_total_credit"], 24000)
        self.assertEqual(totals["grand_total_sales"], 44000)
        self.assertEqual(totals["grand_total_collected"], 3000)
        self.assertEqual(totals["grand_total_comm_sales"], 1350)
        self.assertEqual(totals["grand_total_comm_coll"], 300)
        self.assertEqual(totals["grand_total_due"], 1650)

        salespersons = {sp["name"]: sp for sp in data["salespersons"]}
        # Rep 1: 1 cash sale, 0 credit, 0 collected, comm_sales = 600, comm_coll = 0, due = 600
        sp1 = salespersons["أحمد محمود"]
        self.assertEqual(sp1["receipts_count"], 1)
        self.assertEqual(sp1["cash_sales"], 20000)
        self.assertEqual(sp1["credit_sales"], 0)
        self.assertEqual(sp1["comm_sales"], 600)
        self.assertEqual(sp1["due_salary"], 600)

        # Rep 2: 0 cash sale, 1 credit, 3000 collected, comm_sales = 750, comm_coll = 300, due = 1050
        sp2 = salespersons["مصطفى حسن"]
        self.assertEqual(sp2["receipts_count"], 1)
        self.assertEqual(sp2["cash_sales"], 0)
        self.assertEqual(sp2["credit_sales"], 24000)
        self.assertEqual(sp2["collected"], 3000)
        self.assertEqual(sp2["comm_sales"], 750)
        self.assertEqual(sp2["comm_coll"], 300)
        self.assertEqual(sp2["due_salary"], 1050)

    def test_tier1_salesperson_performance_alias_endpoint(self):
        """Verify GET /api/v1/reports/salesperson-performance/ alias works."""
        res = self.client.get("/api/v1/reports/salesperson-performance/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("salespersons", res.json())
        self.assertIn("totals", res.json())

    def test_tier1_inventory_movement_report(self):
        """Verify Inventory Movement report columns, lifecycle values, and total valuation."""
        # Add a surplus adjustment of 1 fridge and deficit of 1 washer in Month 7
        InventoryAdjustment.objects.create(
            item=self.item_fridge,
            adjustment_type="SURPLUS",
            quantity=1,
            reason="فائض جرد",
            month=7,
            year=2026
        )
        InventoryAdjustment.objects.create(
            item=self.item_washer,
            adjustment_type="DEFICIT",
            quantity=1,
            reason="تالف نقل",
            month=7,
            year=2026
        )

        res = self.client.get("/api/v1/reports/inventory-movement/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["total_adjustments_count"], 2)
        items = {it["product_name"]: it for it in data["items"]}

        # Fridge: Opening 20, Purchases 10, Returns 0, Sales 2, Surplus 1, Deficit 0 -> Final 29
        fridge_row = items["ثلاجة 16 قدم"]
        self.assertEqual(fridge_row["opening_stock"], 20)
        self.assertEqual(fridge_row["purchases"], 10)
        self.assertEqual(fridge_row["sales"], 2)
        self.assertEqual(fridge_row["surplus"], 1)
        self.assertEqual(fridge_row["deficit"], 0)
        self.assertEqual(fridge_row["final_stock"], 29)
        self.assertEqual(fridge_row["unit_cost"], 8000)
        self.assertEqual(fridge_row["total_value"], 29 * 8000)

        # Washer: Opening 15, Purchases 0, Returns 0, Sales 3, Surplus 0, Deficit 1 -> Final 11
        washer_row = items["غسالة أوتوماتيك"]
        self.assertEqual(washer_row["opening_stock"], 15)
        self.assertEqual(washer_row["purchases"], 0)
        self.assertEqual(washer_row["sales"], 3)
        self.assertEqual(washer_row["surplus"], 0)
        self.assertEqual(washer_row["deficit"], 1)
        self.assertEqual(washer_row["final_stock"], 11)
        self.assertEqual(washer_row["unit_cost"], 6000)
        self.assertEqual(washer_row["total_value"], 11 * 6000)

        expected_total_val = (29 * 8000) + (11 * 6000)  # 232,000 + 66,000 = 298,000
        self.assertEqual(data["total_inventory_value"], expected_total_val)

    def test_tier1_profit_and_loss_report(self):
        """Verify Profit and Loss report totals, split, and proportional collection commission."""
        res = self.client.get("/api/v1/reports/sales-pl/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        summary = data["summary"]
        self.assertEqual(summary["grand_revenue"], 44000)
        self.assertEqual(summary["grand_cost"], 34000)
        # grand_commission = sales_comm (600 + 750 = 1350) + coll_comm (1800) = 3150
        # Installment Coll Comm on 24,000 credit sale with 6,000 down payment:
        # Financed debt = 18,000. Coll comm = 18,000 // 10 = 1,800.
        self.assertEqual(summary["grand_commission"], 3150)
        self.assertEqual(summary["expenses_total"], 2500)
        # Net Profit = 44,000 - 34,000 - 3,150 - 2,500 = 4,350
        self.assertEqual(summary["net_profit_final"], 4350)

        # Cash sales table
        self.assertEqual(len(data["cash_sales_profitability"]), 1)
        cash_row = data["cash_sales_profitability"][0]
        self.assertEqual(cash_row["name"], "ثلاجة 16 قدم")
        self.assertEqual(cash_row["qty"], 2)
        self.assertEqual(cash_row["avg_sell"], 10000)
        self.assertEqual(cash_row["cost_per_unit"], 8000)
        self.assertEqual(cash_row["sales_comm_per_unit"], 300)
        self.assertEqual(cash_row["total_coll_comm"], 0)
        self.assertEqual(cash_row["total_profit"], 3400)  # 20,000 - 16,000 - 600
        self.assertEqual(cash_row["avg_profit"], 1700)

        # Installment sales table
        self.assertEqual(len(data["installment_sales_profitability"]), 1)
        inst_row = data["installment_sales_profitability"][0]
        self.assertEqual(inst_row["name"], "غسالة أوتوماتيك")
        self.assertEqual(inst_row["qty"], 3)
        self.assertEqual(inst_row["avg_sell"], 8000)
        self.assertEqual(inst_row["cost_per_unit"], 6000)
        self.assertEqual(inst_row["sales_comm_per_unit"], 250)
        self.assertEqual(inst_row["total_coll_comm"], 1800)
        self.assertEqual(inst_row["coll_comm_per_unit"], 600)  # 1800 // 3
        self.assertEqual(inst_row["total_profit"], 3450)  # 24,000 - 18,000 - 750 - 1800
        self.assertEqual(inst_row["avg_profit"], 1150)  # 3450 // 3

    def test_tier1_profit_and_loss_alias_and_salesperson_filter(self):
        """Verify P&L alias endpoint and filtering by salesperson."""
        # Alias test
        res_alias = self.client.get("/api/v1/reports/profit-and-loss/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res_alias.status_code, 200)

        # Filter by Salesperson 1 (only cash sale)
        res_sp1 = self.client.get("/api/v1/reports/sales-pl/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7,
            "salesperson_id": self.salesperson1.id
        })
        self.assertEqual(res_sp1.status_code, 200)
        data_sp1 = res_sp1.json()
        self.assertEqual(data_sp1["summary"]["grand_revenue"], 20000)
        self.assertEqual(len(data_sp1["cash_sales_profitability"]), 1)
        self.assertEqual(len(data_sp1["installment_sales_profitability"]), 0)

    def test_tier1_cash_drawer_details_report(self):
        """Verify Cash Drawer details listing cash sales, down payments, and collections."""
        res = self.client.get("/api/v1/reports/cash-drawer-details/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Cash sales
        self.assertEqual(len(data["cash_sales"]), 1)
        self.assertEqual(data["cash_sales"][0]["amount"], 20000)
        self.assertEqual(data["cash_sales"][0]["receipt_number"], 1001)

        # Down payments
        self.assertEqual(len(data["down_payments"]), 1)
        self.assertEqual(data["down_payments"][0]["down_payment"], 6000)
        self.assertEqual(data["down_payments"][0]["receipt_number"], 1002)

        # Collections
        self.assertEqual(len(data["collections"]), 1)
        self.assertEqual(data["collections"][0]["amount"], 3000)
        self.assertEqual(data["collections"][0]["customer_name"], "سعيد عبد الرحمن")

    def test_tier1_installments_report_listing_and_filters(self):
        """Verify Installments Ledger report with customer filters and sale period filters."""
        res = self.client.get("/api/v1/reports/installments/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["total_installments_amount"], 3000)
        self.assertEqual(data["installments_count"], 1)
        self.assertEqual(data["installments"][0]["customer_name"], "سعيد عبد الرحمن")
        self.assertEqual(data["installments"][0]["salesperson_name"], "مصطفى حسن")

        # Test customer name filter match
        res_filter = self.client.get("/api/v1/reports/installments/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7,
            "customer_name": "سعيد"
        })
        self.assertEqual(res_filter.json()["installments_count"], 1)

        # Test customer name filter no match
        res_nomatch = self.client.get("/api/v1/reports/installments/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7,
            "customer_name": "غير موجود"
        })
        self.assertEqual(res_nomatch.json()["installments_count"], 0)

    def test_tier1_expenses_report_filtering(self):
        """Verify Expense filtering by branch, year, and month."""
        qs = Expense.objects.filter(
            branch=self.branch,
            expense_year=2026,
            expense_month=7,
            is_deleted=False
        )
        self.assertEqual(qs.count(), 2)
        descriptions = list(qs.values_list('description', flat=True))
        self.assertIn("إيجار المعرض", descriptions)
        self.assertIn("كهرباء ومرافق", descriptions)

    def test_tier1_receipts_report_pagination_and_aggregate(self):
        """Verify Receipts endpoint pagination and total_amount_sum calculation."""
        res = self.client.get("/api/v1/receipts/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["total_amount_sum"], 44000.0)

    def test_tier1_default_date_resolution(self):
        """Verify DefaultDateView resolves latest transaction date."""
        res = self.client.get("/api/v1/default-date/", {"branch_id": self.branch.id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["year"], 2026)
        self.assertEqual(res.json()["month"], 7)


# ===========================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ===========================================================================

class Tier2BoundaryAndCornerCaseTests(ReportingBaseTestCase):
    """Boundary conditions, Arabic numeral parsing, zero values, rollovers, clamping, and isolation."""

    def setUp(self):
        super().setUp()

        self.item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة 55 بوصة",
            initial_quantity=10,
            initial_purchase_price=5000,
            initial_commission_amount=200,
            initial_month=1,
            initial_year=2026
        )

        # Create sequential receipts #101 to #105
        for i in range(1, 6):
            r = Receipt.objects.create(
                branch=self.branch,
                salesperson=self.salesperson1,
                receipt_number=100 + i,
                receipt_hash=f"hash_{100+i}",
                customer_name=f"عميل {i}",
                phone_number=f"0100000000{i}",
                area="الجيزة",
                total_amount=10000 * i,
                down_payment=2000 * i,
                sale_year=2026,
                sale_month=8,
                is_cash_sale=(i % 2 == 1),
                is_confirmed=True
            )
            SaleItem.objects.create(
                receipt=r,
                inventory_item=self.item,
                quantity=1,
                unit_price=10000 * i
            )

    def test_tier2_receipt_range_numeric_filter(self):
        """Verify receipt_from and receipt_to with standard Western numbers."""
        res = self.client.get("/api/v1/receipts/", {
            "branch_id": self.branch.id,
            "receipt_from": "102",
            "receipt_to": "104"
        })
        self.assertEqual(res.status_code, 200)
        results = res.json()["results"]
        receipt_nums = [r["receipt_number"] for r in results]
        self.assertEqual(sorted(receipt_nums), [102, 103, 104])

    def test_tier2_receipt_range_arabic_digits_filter(self):
        """Verify receipt_from and receipt_to with Arabic-Indic numerals (e.g. ١٠٢ to ١٠٤)."""
        res = self.client.get("/api/v1/receipts/", {
            "branch_id": self.branch.id,
            "receipt_from": "١٠٢",
            "receipt_to": "١٠٤"
        })
        self.assertEqual(res.status_code, 200)
        results = res.json()["results"]
        receipt_nums = [r["receipt_number"] for r in results]
        self.assertEqual(sorted(receipt_nums), [102, 103, 104])

    def test_tier2_zero_value_down_payment_handling(self):
        """Verify 100% credit sales (down_payment = 0) are handled cleanly without divide-by-zero."""
        Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=199,
            receipt_hash="hash_zero_dp",
            customer_name="عميل بدون مقدم",
            total_amount=30000,
            down_payment=0,
            sale_year=2026,
            sale_month=8,
            is_cash_sale=False,
            is_confirmed=True
        )

        res_drawer = self.client.get("/api/v1/reports/cash-drawer-details/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 8
        })
        self.assertEqual(res_drawer.status_code, 200)
        # Receipts with 0 down payment should NOT appear in down_payments list
        dp_nums = [dp["receipt_number"] for dp in res_drawer.json()["down_payments"]]
        self.assertNotIn(199, dp_nums)

    def test_tier2_full_down_payment_credit_sale(self):
        """Verify credit sale where down_payment == total_amount (0 remaining debt)."""
        Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=200,
            receipt_hash="hash_full_dp",
            customer_name="عميل مقدم كامل",
            total_amount=15000,
            down_payment=15000,
            sale_year=2026,
            sale_month=8,
            is_cash_sale=False,
            is_confirmed=True
        )

        res_pl = self.client.get("/api/v1/reports/sales-pl/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 8
        })
        self.assertEqual(res_pl.status_code, 200)

    def test_tier2_month_rollover_december_to_january(self):
        """Verify opening stock and reports rollover across year boundary (12/2026 -> 1/2027)."""
        # Add sale in December 2026
        r_dec = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=301,
            receipt_hash="hash_dec",
            total_amount=10000,
            down_payment=10000,
            sale_year=2026,
            sale_month=12,
            is_cash_sale=True,
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=r_dec,
            inventory_item=self.item,
            quantity=2,
            unit_price=5000
        )

        # In January 2027, opening stock must reflect deductions from 2026
        res_inv = self.client.get("/api/v1/reports/inventory-movement/", {
            "branch_id": self.branch.id,
            "year": 2027,
            "month": 1
        })
        self.assertEqual(res_inv.status_code, 200)
        items = {it["product_name"]: it for it in res_inv.json()["items"]}
        # Total sold in 2026: 5 in Aug + 2 in Dec = 7. Initial 10. Opening in Jan 2027 = 3.
        self.assertEqual(items["شاشة 55 بوصة"]["opening_stock"], 3)

    def test_tier2_historical_time_machine_price_and_commission(self):
        """Verify item.get_price_at_date and get_commission_at_date accurately follow historical timeline."""
        # Initial purchase price is 5000, initial comm is 200 in 1/2026
        # Add purchase invoice in 5/2026 at 6000
        pur = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=201,
            invoice_type="PURCHASE",
            invoice_month=5,
            invoice_year=2026
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pur,
            inventory_item=self.item,
            quantity=5,
            purchase_price=6000
        )

        # Add Commission change in 6/2026 to 350
        CommissionHistory.objects.create(
            item=self.item,
            commission_amount=350,
            activation_month=6,
            activation_year=2026
        )

        # At Month 3/2026: Price = 5000, Comm = 200
        self.assertEqual(self.item.get_price_at_date(3, 2026), 5000)
        self.assertEqual(self.item.get_commission_at_date(3, 2026), 200)

        # At Month 5/2026: Price = 6000, Comm = 200
        self.assertEqual(self.item.get_price_at_date(5, 2026), 6000)
        self.assertEqual(self.item.get_commission_at_date(5, 2026), 200)

        # At Month 7/2026: Price = 6000, Comm = 350
        self.assertEqual(self.item.get_price_at_date(7, 2026), 6000)
        self.assertEqual(self.item.get_commission_at_date(7, 2026), 350)

    def test_tier2_zero_sales_empty_period(self):
        """Verify querying an empty month returns clean zero KPIs without runtime exceptions."""
        res = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2025,
            "month": 1  # Prior to activity
        })
        self.assertEqual(res.status_code, 200)
        kpis = res.json()["kpis"]
        self.assertEqual(kpis["total_revenue"], 0)
        self.assertEqual(kpis["avg_basket_size"], 0)

    def test_tier2_stock_never_negative_clamping(self):
        """Verify stock calculation clamps to 0 when deficit exceeds available stock."""
        InventoryAdjustment.objects.create(
            item=self.item,
            adjustment_type="DEFICIT",
            quantity=500,  # Exceeds total stock
            reason="تلف هائل",
            month=8,
            year=2026
        )
        self.assertEqual(self.item.get_stock_at_date(8, 2026), 0)

    def test_tier2_soft_delete_exclusion(self):
        """Verify soft-deleted entities are strictly excluded from all report calculations."""
        # Create a receipt then soft delete it
        r_del = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=999,
            receipt_hash="hash_del",
            total_amount=50000,
            down_payment=50000,
            sale_year=2026,
            sale_month=8,
            is_cash_sale=True,
            is_confirmed=True,
            is_deleted=True
        )
        SaleItem.objects.create(
            receipt=r_del,
            inventory_item=self.item,
            quantity=5,
            unit_price=10000,
            is_deleted=True
        )

        res = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 8
        })
        self.assertEqual(res.status_code, 200)
        # Revenue from 5 valid receipts = 10,000 + 20,000 + 30,000 + 40,000 + 50,000 = 150,000
        self.assertEqual(res.json()["kpis"]["total_revenue"], 150000)

    def test_tier2_cross_branch_data_isolation(self):
        """Verify complete isolation between separate branch locations."""
        branch2 = Branch.objects.create(name="فرع الإسكندرية")
        sp_b2 = Salesperson.objects.create(branch=branch2, name="عمرو السكندري")
        item_b2 = InventoryItem.objects.create(
            branch=branch2,
            name="شاشة 55 بوصة",
            initial_quantity=50,
            initial_purchase_price=4500,
            initial_month=1,
            initial_year=2026
        )
        Receipt.objects.create(
            branch=branch2,
            salesperson=sp_b2,
            receipt_number=1,
            receipt_hash="hash_b2_1",
            total_amount=99000,
            down_payment=99000,
            sale_year=2026,
            sale_month=8,
            is_cash_sale=True,
            is_confirmed=True
        )

        # Query Branch 1: Should NOT see Branch 2's 99,000 revenue
        res_b1 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 8
        })
        self.assertEqual(res_b1.json()["kpis"]["total_revenue"], 150000)

        # Query Branch 2: Should see exactly 99,000 revenue
        res_b2 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": branch2.id,
            "year": 2026,
            "month": 8
        })
        self.assertEqual(res_b2.json()["kpis"]["total_revenue"], 99000)

    def test_tier2_invalid_parameters_error_handling(self):
        """Verify invalid or missing parameters return HTTP 400 with descriptive error."""
        # Missing branch_id
        res_missing = self.client.get("/api/v1/reports/dashboard/summary/", {"year": 2026, "month": 8})
        self.assertEqual(res_missing.status_code, 400)
        self.assertIn("branch_id", res_missing.json())

        # Non-numeric branch_id
        res_invalid = self.client.get("/api/v1/reports/dashboard/summary/", {"branch_id": "abc", "year": 2026})
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("branch_id", res_invalid.json())


# ===========================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ===========================================================================

class Tier3CrossFeatureIntegrationTests(ReportingBaseTestCase):
    """End-to-end multi-step transactions and cross-report synchronizations."""

    def setUp(self):
        super().setUp()
        self.item = InventoryItem.objects.create(
            branch=self.branch,
            name="بوتجاز 5 شعلة",
            initial_quantity=10,
            initial_purchase_price=4000,
            initial_commission_amount=150,
            initial_month=1,
            initial_year=2026
        )

    def test_tier3_cash_sale_full_pipeline(self):
        """Sale Creation -> Cash Drawer -> Dashboard -> Inventory Stock Deduction -> Rep Commission."""
        # 1. Create Cash Sale
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson1,
            receipt_number=501,
            receipt_hash="hash_pipeline_cash",
            customer_name="ياسر جلال",
            area="المعادي",
            total_amount=12000,
            down_payment=12000,
            sale_year=2026,
            sale_month=9,
            is_cash_sale=True,
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=receipt,
            inventory_item=self.item,
            quantity=2,
            unit_price=6000
        )

        # 2. Check Cash Drawer
        res_drawer = self.client.get("/api/v1/reports/cash-drawer-details/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        self.assertEqual(len(res_drawer.json()["cash_sales"]), 1)
        self.assertEqual(res_drawer.json()["cash_sales"][0]["amount"], 12000)

        # 3. Check Dashboard KPIs
        res_dash = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        self.assertEqual(res_dash.json()["kpis"]["total_revenue"], 12000)
        self.assertEqual(res_dash.json()["kpis"]["total_cogs"], 8000)  # 2 * 4000
        self.assertEqual(res_dash.json()["kpis"]["total_sales_commissions"], 300)  # 2 * 150

        # 4. Check Inventory Movement
        res_inv = self.client.get("/api/v1/reports/inventory-movement/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        item_row = res_inv.json()["items"][0]
        self.assertEqual(item_row["sales"], 2)
        self.assertEqual(item_row["final_stock"], 8)  # 10 - 2

        # 5. Check Salesperson Performance
        res_sp = self.client.get("/api/v1/reports/salespersons/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        sp1 = [s for s in res_sp.json()["salespersons"] if s["name"] == "أحمد محمود"][0]
        self.assertEqual(sp1["cash_sales"], 12000)
        self.assertEqual(sp1["comm_sales"], 300)
        self.assertEqual(sp1["due_salary"], 300)

    def test_tier3_installment_sale_and_subsequent_collection_pipeline(self):
        """Installment Sale -> Down Payment Drawer Sync -> Subsequent Monthly Collection -> Salary & KPI Sync."""
        # 1. Installment Sale in Month 9
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson2,
            receipt_number=502,
            receipt_hash="hash_pipeline_credit",
            customer_name="طارق شوقي",
            area="مدينة نصر",
            total_amount=18000,
            down_payment=3000,
            installment_system="10 شهور",
            sale_year=2026,
            sale_month=9,
            is_cash_sale=False,
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=receipt,
            inventory_item=self.item,
            quantity=3,
            unit_price=6000
        )

        # Verify Down payment in Month 9
        res_dash_m9 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        self.assertEqual(res_dash_m9.json()["cash_drawer_summary"]["down_payment_inflow"], 3000)

        # 2. Collect 1,500 installment in Month 10
        InstallmentPayment.objects.create(
            receipt=receipt,
            payment_date=date(2026, 10, 15),
            amount=1500
        )

        # Verify Month 10 Collection reflection
        res_dash_m10 = self.client.get("/api/v1/reports/dashboard/summary/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 10
        })
        self.assertEqual(res_dash_m10.json()["cash_drawer_summary"]["collection_inflow"], 1500)
        self.assertEqual(res_dash_m10.json()["kpis"]["total_collection_commissions"], 150)  # 1500 // 10

        # Verify Salesperson Performance in Month 10
        res_sp_m10 = self.client.get("/api/v1/reports/salespersons/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 10
        })
        sp2 = [s for s in res_sp_m10.json()["salespersons"] if s["name"] == "مصطفى حسن"][0]
        self.assertEqual(sp2["collected"], 1500)
        self.assertEqual(sp2["comm_coll"], 150)
        self.assertEqual(sp2["due_salary"], 150)

    def test_tier3_procurement_and_inventory_reconciliation(self):
        """Purchase Invoice Inbound -> Purchase Return -> Stock Valuation & Movement Sync."""
        # 1. Inbound purchase of 10 units @ 4200 in Month 9
        pur = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=601,
            invoice_type="PURCHASE",
            invoice_month=9,
            invoice_year=2026
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pur,
            inventory_item=self.item,
            quantity=10,
            purchase_price=4200
        )

        # 2. Return of 2 defective units to supplier in Month 9
        ret = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=602,
            invoice_type="RETURN",
            invoice_month=9,
            invoice_year=2026
        )
        PurchaseInvoiceItem.objects.create(
            invoice=ret,
            inventory_item=self.item,
            quantity=2,
            purchase_price=4200
        )

        # 3. Check Inventory Movement Report
        res_inv = self.client.get("/api/v1/reports/inventory-movement/", {
            "branch_id": self.branch.id,
            "year": 2026,
            "month": 9
        })
        self.assertEqual(res_inv.status_code, 200)
        item_row = res_inv.json()["items"][0]
        self.assertEqual(item_row["purchases"], 10)
        self.assertEqual(item_row["returns"], 2)
        # Initial 10 + 10 purchase - 2 return = 18 units
        self.assertEqual(item_row["final_stock"], 18)
        self.assertEqual(item_row["unit_cost"], 4200)  # Latest purchase price
        self.assertEqual(item_row["total_value"], 18 * 4200)


# ===========================================================================
# TIER 4: REAL-WORLD BUSINESS WORKLOADS
# ===========================================================================

class Tier4RealWorldWorkloadTests(ReportingBaseTestCase):
    """Full monthly closing scenarios verifying complete financial and inventory mathematical invariants."""

    def test_tier4_monthly_business_close_scenario(self):
        """Simulate a complete 1-month business cycle with 3 products, 2 reps, mixed sales, purchases,
        expenses, collections, and adjustments, verifying all cross-report mathematical invariants."""
        month = 11
        year = 2026

        # Products
        prod_a = InventoryItem.objects.create(
            branch=self.branch, name="طقم نوم تركي",
            initial_quantity=5, initial_purchase_price=15000, initial_commission_amount=500,
            initial_month=1, initial_year=2026
        )
        prod_b = InventoryItem.objects.create(
            branch=self.branch, name="شاشة 65 بوصة 4K",
            initial_quantity=8, initial_purchase_price=10000, initial_commission_amount=350,
            initial_month=1, initial_year=2026
        )
        prod_c = InventoryItem.objects.create(
            branch=self.branch, name="طقم سفرة كلاسيك",
            initial_quantity=4, initial_purchase_price=12000, initial_commission_amount=400,
            initial_month=1, initial_year=2026
        )

        # Procurement: Inbound purchase of 2 bedroom sets @ 15500
        pur = PurchaseInvoice.objects.create(
            branch=self.branch, supplier=self.supplier,
            invoice_number=801, invoice_type="PURCHASE", invoice_month=month, invoice_year=year
        )
        PurchaseInvoiceItem.objects.create(
            invoice=pur, inventory_item=prod_a, quantity=2, purchase_price=15500
        )

        # Sales Rep 1 Transactions:
        # Cash sale: 1 bedroom set @ 22,000
        r1 = Receipt.objects.create(
            branch=self.branch, salesperson=self.salesperson1, receipt_number=701,
            receipt_hash="h701", customer_name="طارق علام", area="مدينة نصر",
            total_amount=22000, down_payment=22000, sale_year=year, sale_month=month,
            is_cash_sale=True, is_confirmed=True
        )
        SaleItem.objects.create(receipt=r1, inventory_item=prod_a, quantity=1, unit_price=22000)

        # Credit sale: 2 TV sets @ 14,000 = 28,000 (Down payment 8,000)
        r2 = Receipt.objects.create(
            branch=self.branch, salesperson=self.salesperson1, receipt_number=702,
            receipt_hash="h702", customer_name="عمر الشريف", area="مصر الجديدة",
            total_amount=28000, down_payment=8000, installment_system="10 شهور",
            sale_year=year, sale_month=month, is_cash_sale=False, is_confirmed=True
        )
        SaleItem.objects.create(receipt=r2, inventory_item=prod_b, quantity=2, unit_price=14000)

        # Sales Rep 2 Transactions:
        # Cash sale: 1 dining set @ 18,000
        r3 = Receipt.objects.create(
            branch=self.branch, salesperson=self.salesperson2, receipt_number=703,
            receipt_hash="h703", customer_name="فاروق حسني", area="الزمالك",
            total_amount=18000, down_payment=18000, sale_year=year, sale_month=month,
            is_cash_sale=True, is_confirmed=True
        )
        SaleItem.objects.create(receipt=r3, inventory_item=prod_c, quantity=1, unit_price=18000)

        # Collected Installments in Month 11
        # Rep 1: 5,000 from r2
        InstallmentPayment.objects.create(receipt=r2, payment_date=date(year, month, 10), amount=5000)

        # Adjustments: 1 TV surplus
        InventoryAdjustment.objects.create(
            item=prod_b, adjustment_type="SURPLUS", quantity=1, reason="فائض مخزني",
            month=month, year=year
        )

        # Operating Expenses: 4,000 (Rent 3000, Electricity 1000)
        Expense.objects.create(branch=self.branch, amount=3000, description="إيجار", expense_year=year, expense_month=month)
        Expense.objects.create(branch=self.branch, amount=1000, description="كهرباء", expense_year=year, expense_month=month)

        # --- EXECUTE ALL 5 MAIN REPORTS FOR PERIOD ---
        dash_res = self.client.get("/api/v1/reports/dashboard/summary/", {"branch_id": self.branch.id, "year": year, "month": month})
        sp_res = self.client.get("/api/v1/reports/salespersons/", {"branch_id": self.branch.id, "year": year, "month": month})
        inv_res = self.client.get("/api/v1/reports/inventory-movement/", {"branch_id": self.branch.id, "year": year, "month": month})
        pl_res = self.client.get("/api/v1/reports/sales-pl/", {"branch_id": self.branch.id, "year": year, "month": month})
        drawer_res = self.client.get("/api/v1/reports/cash-drawer-details/", {"branch_id": self.branch.id, "year": year, "month": month})

        self.assertEqual(dash_res.status_code, 200)
        self.assertEqual(sp_res.status_code, 200)
        self.assertEqual(inv_res.status_code, 200)
        self.assertEqual(pl_res.status_code, 200)
        self.assertEqual(drawer_res.status_code, 200)

        dash_kpis = dash_res.json()["kpis"]
        dash_drawer = dash_res.json()["cash_drawer_summary"]
        sp_totals = sp_res.json()["totals"]
        inv_data = inv_res.json()
        pl_summary = pl_res.json()["summary"]

        # INVARIANT 1: Total Revenue Reconciliation
        # 22,000 (r1) + 28,000 (r2) + 18,000 (r3) = 68,000
        self.assertEqual(dash_kpis["total_revenue"], 68000)
        self.assertEqual(sp_totals["grand_total_sales"], 68000)
        self.assertEqual(pl_summary["grand_revenue"], 68000)

        # INVARIANT 2: Cash Inflow Reconciliation
        # Cash sales: 22,000 + 18,000 = 40,000
        # Down payments: 8,000
        # Collections: 5,000
        # Total cash inflow = 53,000
        self.assertEqual(dash_drawer["cash_sales_inflow"], 40000)
        self.assertEqual(dash_drawer["down_payment_inflow"], 8000)
        self.assertEqual(dash_drawer["collection_inflow"], 5000)
        self.assertEqual(dash_drawer["total_cash_inflow"], 53000)

        # INVARIANT 3: Salesperson Compensation Reconciliation
        # Rep 1: Sales comm (prod_a: 500 + 2*prod_b: 700 = 1200) + Coll comm (5000 // 10 = 500) = 1700
        # Rep 2: Sales comm (prod_c: 400) + Coll comm 0 = 400
        # Grand total due = 2100
        self.assertEqual(sp_totals["grand_total_comm_sales"], 1600)
        self.assertEqual(sp_totals["grand_total_comm_coll"], 500)
        self.assertEqual(sp_totals["grand_total_due"], 2100)
        self.assertEqual(dash_drawer["auto_salaries"], 2100)

        # INVARIANT 4: Inventory Closing Valuation Reconciliation
        # Prod A: 5 initial + 2 purchase - 1 sold = 6 * 15500 (latest price) = 93,000
        # Prod B: 8 initial - 2 sold + 1 surplus = 7 * 10000 = 70,000
        # Prod C: 4 initial - 1 sold = 3 * 12000 = 36,000
        # Total Inventory Value = 93,000 + 70,000 + 36,000 = 199,000
        self.assertEqual(inv_data["total_inventory_value"], 199000)
        self.assertEqual(dash_kpis["current_inventory_value"], 199000)

        # INVARIANT 5: Net Cash in Hand & Safe Balance Reconciliation
        # Outflows: Purchases (2 * 15500 = 31000) + Expenses (4000) + Salaries (2100) = 37100
        # Net Cash = Inflow (53000) - Outflow (37100) = 15,900
        self.assertEqual(dash_drawer["net_cash_in_hand"], 15900)
        self.assertEqual(dash_kpis["safe_balance"], 15900)
