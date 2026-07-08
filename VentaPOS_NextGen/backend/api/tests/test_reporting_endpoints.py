import uuid
from django.test import TestCase
from django.utils import timezone
from datetime import date
from rest_framework.test import APIClient
from api.models import (
    Tenant, Branch, Salesperson, InventoryItem, Supplier,
    PurchaseInvoice, PurchaseInvoiceItem, Receipt, SaleItem,
    InstallmentPayment, Expense, ClientLicense
)
from api.utils.security_utils import generate_record_signature, get_machine_id

class ReportingEndpointsTests(TestCase):
    databases = ["default", "system"]

    def setUp(self):
        self.client = APIClient()
        
        # Create Tenant
        self.tenant = Tenant.objects.using("default").create(
            company_code="TESTC",
            name="Test Tenant",
            is_active=True
        )
        
        # Create a valid license in the system database
        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, mach_id, 1, True)

        self.license = ClientLicense.objects.using("system").create(
            tenant=self.tenant,
            company_code="TESTC",
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig,
        )
        
        # Set default credentials/headers for tenant resolution
        self.client.credentials(HTTP_X_COMPANY_CODE="TESTC")
        
        # Create Branch
        self.branch = Branch.objects.using("default").create(
            tenant=self.tenant,
            name="Test Branch",
            local_id=1
        )
        
        # Create Salesperson
        self.salesperson = Salesperson.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            name="أحمد محمود",
            local_id=1
        )
        
        # Create Supplier
        self.supplier = Supplier.objects.using("default").create(
            tenant=self.tenant,
            name="Test Supplier"
        )
        
        # Create Inventory Item
        self.item = InventoryItem.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            local_id=1,
            name="Test Item",
            initial_quantity=20,
            initial_purchase_price=4000,
            initial_commission_amount=200,
            initial_month=1,
            initial_year=2026
        )

        # Create Purchase Invoice (to verify get_price_at_date fallback is overridden/tested)
        self.purchase_invoice = PurchaseInvoice.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=1,
            invoice_type="PURCHASE",
            invoice_month=7,
            invoice_year=2026
        )
        self.purchase_item = PurchaseInvoiceItem.objects.using("default").create(
            tenant=self.tenant,
            purchase_invoice=self.purchase_invoice,
            inventory_item=self.item,
            quantity=10,
            purchase_price=4000
        )
        
        # Create a Cash Sale Receipt
        self.receipt_cash = Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            salesperson=self.salesperson,
            local_id=1,
            receipt_number=1001,
            client_uuid=uuid.uuid4(),
            receipt_hash="hash_cash",
            customer_name="محمد علي",
            area="الدقي",
            total_amount=25000,
            down_payment=25000,
            sale_year=2026,
            sale_month=7,
            is_cash_sale=True,
            is_confirmed=True,
            created_at_local=timezone.now()
        )
        self.sale_item_cash = SaleItem.objects.using("default").create(
            tenant=self.tenant,
            receipt=self.receipt_cash,
            inventory_item=self.item,
            quantity=5,
            unit_price=5000
        )
        
        # Create a Credit/Installment Sale Receipt
        self.receipt_credit = Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            salesperson=self.salesperson,
            local_id=2,
            receipt_number=1002,
            client_uuid=uuid.uuid4(),
            receipt_hash="hash_credit",
            customer_name="إبراهيم حسن",
            area="الدقي",
            total_amount=55000,
            down_payment=15000,
            sale_year=2026,
            sale_month=7,
            is_cash_sale=False,
            is_confirmed=True,
            created_at_local=timezone.now()
        )
        self.sale_item_credit = SaleItem.objects.using("default").create(
            tenant=self.tenant,
            receipt=self.receipt_credit,
            inventory_item=self.item,
            quantity=10,
            unit_price=5500
        )
        
        # Create an Installment Payment
        self.payment = InstallmentPayment.objects.using("default").create(
            tenant=self.tenant,
            receipt=self.receipt_credit,
            payment_date=date(2026, 7, 5),
            amount=25000
        )
        
        # Create an Expense
        self.expense = Expense.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            amount=10000,
            description="Monthly Rent",
            expense_year=2026,
            expense_month=7,
            created_at_local=timezone.now()
        )

    def test_dashboard_summary(self):
        url = "/api/v1/reports/dashboard/summary/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Period assertion
        self.assertEqual(data["period"]["year"], 2026)
        self.assertEqual(data["period"]["month"], 7)
        
        # KPI assertions
        kpis = data["kpis"]
        self.assertEqual(kpis["total_revenue"], 80000) # 25000 (cash) + 55000 (credit)
        self.assertEqual(kpis["total_cogs"], 60000) # (5 + 10) * 4000.00
        
        # sales comm: (5 + 10) * 200.00 = 3000.00
        # reserve deduction: (55000 - 15000) * 10% = 4000.00
        # operating expenses: 10000.00
        # estimated_net_profit = 80000.00 - (60000.00 + 3000.00 + 4000.00 + 10000.00) = 3000.00
        self.assertEqual(kpis["estimated_net_profit"], 3000)
        
        # stock: 20 (initial) + 10 (purchase) - 15 (sales) = 15.
        # current inventory value: 15 * 4000.00 = 60000.00
        self.assertEqual(kpis["current_inventory_value"], 60000)
        self.assertEqual(kpis["low_stock_count"], 0)
        self.assertEqual(kpis["avg_basket_size"], 40000) # 80000 / 2
        
        # Cash drawer assertions
        summary = data["cash_drawer_summary"]
        self.assertEqual(summary["cash_sales_inflow"], 25000)
        self.assertEqual(summary["down_payment_inflow"], 15000)
        self.assertEqual(summary["collection_inflow"], 25000)
        self.assertEqual(summary["total_cash_inflow"], 65000)
        self.assertEqual(summary["operating_expenses"], 10000)
        
        # sp commission: 3000.00. collection commission: 25000.00 * 10% = 2500.00. total: 5500.00
        self.assertEqual(summary["auto_salaries"], 5500)
        self.assertEqual(summary["net_cash_in_hand"], 49500) # 65000.00 - 10000.00 - 5500.00
        self.assertEqual(kpis["safe_balance"], 49500)
        
        # Top products
        self.assertEqual(len(data["top_products"]), 1)
        self.assertEqual(data["top_products"][0]["product_name"], "Test Item")
        self.assertEqual(data["top_products"][0]["quantity_sold"], 15)

        # Top areas
        self.assertEqual(len(data["top_areas"]), 1)
        self.assertEqual(data["top_areas"][0]["area"], "الدقي")
        self.assertEqual(data["top_areas"][0]["sales_value"], 80000)
        self.assertEqual(data["top_areas"][0]["invoice_count"], 2)

    def test_salesperson_performance(self):
        url = "/api/v1/reports/salespersons/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["totals"]["grand_total_cash"], 25000)
        self.assertEqual(data["totals"]["grand_total_credit"], 55000)
        self.assertEqual(data["totals"]["grand_total_sales"], 80000)
        self.assertEqual(data["totals"]["grand_total_collected"], 25000)
        self.assertEqual(data["totals"]["grand_total_comm_sales"], 3000)
        self.assertEqual(data["totals"]["grand_total_comm_coll"], 2500)
        self.assertEqual(data["totals"]["grand_total_due"], 5500)
        
        self.assertEqual(len(data["salespersons"]), 1)
        sp = data["salespersons"][0]
        self.assertEqual(sp["name"], "أحمد محمود")
        self.assertEqual(sp["receipts_count"], 2)
        self.assertEqual(sp["due_salary"], 5500)

    def test_inventory_movement(self):
        url = "/api/v1/reports/inventory-movement/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["total_inventory_value"], 60000)
        self.assertEqual(data["total_adjustments_count"], 0)
        
        self.assertEqual(len(data["items"]), 1)
        item_row = data["items"][0]
        self.assertEqual(item_row["product_name"], "Test Item")
        self.assertEqual(item_row["opening_stock"], 20)
        self.assertEqual(item_row["purchases"], 10)
        self.assertEqual(item_row["returns"], 0)
        self.assertEqual(item_row["sales"], 15)
        self.assertEqual(item_row["final_stock"], 15)
        self.assertEqual(item_row["unit_cost"], 4000)
        self.assertEqual(item_row["total_value"], 60000)

    def test_profit_and_loss(self):
        url = "/api/v1/reports/sales-pl/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        summary = data["summary"]
        self.assertEqual(summary["grand_revenue"], 80000)
        self.assertEqual(summary["grand_cost"], 60000)
        self.assertEqual(summary["grand_commission"], 7000)
        self.assertEqual(summary["expenses_total"], 10000)
        self.assertEqual(summary["net_profit_final"], 3000)
        
        # Cash sales details
        self.assertEqual(len(data["cash_sales_profitability"]), 1)
        cash_row = data["cash_sales_profitability"][0]
        self.assertEqual(cash_row["name"], "Test Item")
        self.assertEqual(cash_row["qty"], 5)
        self.assertEqual(cash_row["total_rev"], 25000)
        self.assertEqual(cash_row["total_cost"], 20000)
        self.assertEqual(cash_row["total_sales_comm"], 1000)
        self.assertEqual(cash_row["total_coll_comm"], 0)
        self.assertEqual(cash_row["total_profit"], 4000)
        
        # Installment sales details
        self.assertEqual(len(data["installment_sales_profitability"]), 1)
        inst_row = data["installment_sales_profitability"][0]
        self.assertEqual(inst_row["name"], "Test Item")
        self.assertEqual(inst_row["qty"], 10)
        self.assertEqual(inst_row["total_rev"], 55000)
        self.assertEqual(inst_row["total_cost"], 40000)
        self.assertEqual(inst_row["total_sales_comm"], 2000)
        self.assertEqual(inst_row["total_coll_comm"], 4000)
        self.assertEqual(inst_row["total_profit"], 9000)

    def test_profit_and_loss_with_salesperson(self):
        url = "/api/v1/reports/sales-pl/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7,
            "salesperson_id": str(self.salesperson.id)
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["grand_revenue"], 80000)

        # Query with non-existent salesperson UUID
        params["salesperson_id"] = str(uuid.uuid4())
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["grand_revenue"], 0)

    def test_cash_drawer_details(self):
        url = "/api/v1/reports/cash-drawer-details/"
        params = {
            "branch_id": str(self.branch.id),
            "year": 2026,
            "month": 7
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["cash_sales"]), 1)
        self.assertEqual(data["cash_sales"][0]["amount"], 25000)
        
        self.assertEqual(len(data["down_payments"]), 1)
        self.assertEqual(data["down_payments"][0]["down_payment"], 15000)
        
        self.assertEqual(len(data["collections"]), 1)
        self.assertEqual(data["collections"][0]["amount"], 25000)

    def test_error_handling_missing_branch_id(self):
        url = "/api/v1/reports/dashboard/summary/"
        # missing branch_id
        response = self.client.get(url, {"year": 2026, "month": 7})
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch_id", response.json())
        
        # invalid branch_id format
        response = self.client.get(url, {"branch_id": "not-a-uuid", "year": 2026, "month": 7})
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch_id", response.json())
        
        # non-existent branch_id
        response = self.client.get(url, {"branch_id": str(uuid.uuid4()), "year": 2026, "month": 7})
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch_id", response.json())
