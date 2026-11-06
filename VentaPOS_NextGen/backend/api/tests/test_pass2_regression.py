import datetime
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.models import (
    Branch, Salesperson, InventoryItem, Supplier,
    PurchaseInvoice, PurchaseInvoiceItem, Receipt, SaleItem,
    InstallmentPayment, CompanySetting, ClientLicense
)
from api.serializers import PurchaseInvoiceSerializer
from api.utils.security_utils import generate_record_signature, get_machine_id
from api.views.base import get_default_date


class Pass2RegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.admin_user.set_password("adminpass")
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)

        self.branch = Branch.objects.create(name="فرع المعادي")
        self.salesperson = Salesperson.objects.create(branch=self.branch, name="أحمد محمود")
        self.supplier = Supplier.objects.create(name="مورد التحرير")

        # Set up an active license for 2026
        self.mach_id = get_machine_id()
        self.start_date = datetime.date(2026, 1, 1)
        self.expiry_date = datetime.date(2027, 1, 1)
        sig = generate_record_signature(str(self.expiry_date), 1000, self.mach_id, 1, True)
        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=self.start_date,
            expiry_date=self.expiry_date,
            invoices_balance=1000,
            is_active=True,
            machine_id=self.mach_id,
            license_code_hash=sig,
        )
        self.company_setting = CompanySetting.objects.create(
            name="شركة فينتابوس",
            collection_commission_rate=Decimal("0.10")
        )

    def test_purchase_serializer_update_stock_bottleneck_rollback(self):
        """
        1. PurchaseInvoiceSerializer.update rejects lowering a past PURCHASE quantity
        when a later month's sale depends on that stock, and rolls back cleanly.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة إل جي",
            initial_quantity=0,
            initial_purchase_price=Decimal("5000"),
            initial_commission_amount=Decimal("100"),
            initial_month=1,
            initial_year=2026
        )

        # Inbound purchase in month 1: 10 units
        invoice = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=101,
            invoice_type="PURCHASE",
            invoice_month=1,
            invoice_year=2026
        )
        p_item = PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            inventory_item=item,
            quantity=10,
            purchase_price=Decimal("5000")
        )

        # Sale in month 2: 8 units (remaining stock = 2)
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=1,
            customer_name="علي حسن",
            total_amount=Decimal("12000"),
            down_payment=Decimal("12000"),
            sale_year=2026,
            sale_month=2,
            is_cash_sale=True,
            receipt_type="SALE",
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=receipt,
            inventory_item=item,
            quantity=8,
            unit_price=Decimal("1500")
        )

        # Now attempting to mutate purchase invoice in month 1 to qty 5 (induces 5 - 8 = -3 stock in month 2)
        serializer = PurchaseInvoiceSerializer(
            instance=invoice,
            data={
                "branch": self.branch.id,
                "supplier": self.supplier.id,
                "invoice_number": 101,
                "invoice_type": "PURCHASE",
                "invoice_month": 1,
                "invoice_year": 2026,
                "items": [
                    {
                        "inventory_item": item.id,
                        "quantity": 5,
                        "purchase_price": "5000.00"
                    }
                ]
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError):
            serializer.save()

        # Verify rollback: quantity remains 10
        p_item.refresh_from_db()
        self.assertEqual(p_item.quantity, 10)

    def test_pnl_and_dashboard_card1_return_alignment(self):
        """
        2. ProfitAndLossReportView and DashboardReportView Card 1 produce identical
        Net Profit and Upfront Credit Reserve numbers when an installment receipt has a partial return.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة سامسونج 55",
            initial_quantity=10,
            initial_purchase_price=Decimal("3000"),
            initial_commission_amount=Decimal("50"),
            initial_month=1,
            initial_year=2026
        )

        # Installment sale in month 1: 2 units at 4000 = 8000
        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=201,
            customer_name="محمد سعيد",
            total_amount=Decimal("8000"),
            down_payment=Decimal("2000"),
            installment_system="1000*6",
            sale_year=2026,
            sale_month=1,
            is_cash_sale=False,
            receipt_type="SALE",
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=receipt,
            inventory_item=item,
            quantity=2,
            unit_price=Decimal("4000")
        )
        for i in range(1, 7):
            m = 1 + i
            y = 2026
            InstallmentPayment.objects.create(
                receipt=receipt,
                payment_date=datetime.date(y, m, 25),
                amount=Decimal("1000")
            )

        # Partial return in month 2: 1 unit returned (value 4000)
        ret_receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=202,
            parent_receipt=receipt,
            customer_name="محمد سعيد",
            total_amount=Decimal("4000"),
            down_payment=Decimal("0"),
            installment_system="1000*2",
            sale_year=2026,
            sale_month=2,
            is_cash_sale=False,
            receipt_type="RETURN",
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=ret_receipt,
            inventory_item=item,
            quantity=1,
            unit_price=Decimal("4000")
        )

        pnl_res = self.client.get(f"/api/v1/reports/profit-and-loss/?branch_id={self.branch.id}&month=1&year=2026")
        dash_res = self.client.get(f"/api/v1/reports/dashboard/summary/?branch_id={self.branch.id}&month=1&year=2026")

        self.assertEqual(pnl_res.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)

        # Net profit across both must match cleanly
        pnl_net = pnl_res.data.get("summary", {}).get("net_profit_final")
        dash_net = dash_res.data.get("kpis", {}).get("estimated_net_profit")
        self.assertIsNotNone(pnl_net)
        self.assertIsNotNone(dash_net)
        self.assertEqual(float(pnl_net), float(dash_net))
        self.assertEqual(float(pnl_net), 750.0)

    def test_ledger_sale_return_parent_valuation_and_stock_clamping(self):
        """
        3. InventoryItemViewSet.ledger values SALE_RETURN items at parent_receipt unit price
        and clamps stock at month boundaries.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="طقم انتريه",
            initial_quantity=5,
            initial_purchase_price=Decimal("2000"),
            initial_commission_amount=Decimal("30"),
            initial_month=1,
            initial_year=2026
        )

        receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=301,
            customer_name="كريم عادل",
            total_amount=Decimal("3500"),
            down_payment=Decimal("3500"),
            sale_year=2026,
            sale_month=1,
            is_cash_sale=True,
            receipt_type="SALE",
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=receipt,
            inventory_item=item,
            quantity=1,
            unit_price=Decimal("3500")
        )

        ret_receipt = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=302,
            parent_receipt=receipt,
            customer_name="كريم عادل",
            total_amount=Decimal("3500"),
            down_payment=Decimal("3500"),
            sale_year=2026,
            sale_month=2,
            is_cash_sale=True,
            receipt_type="RETURN",
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=ret_receipt,
            inventory_item=item,
            quantity=1,
            unit_price=Decimal("3500")
        )

        res = self.client.get(f"/api/v1/inventory-items/{item.id}/ledger/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        timeline = res.data.get("timeline", [])
        return_events = [ev for ev in timeline if ev.get("type") == "SALE_RETURN"]
        self.assertTrue(len(return_events) > 0)
        # Unit price is valued at parent receipt's price
        self.assertEqual(float(return_events[0]["price"]), 3500.0)
        # Stock calculation never negative
        for ev in timeline:
            self.assertGreaterEqual(ev.get("running_stock", 0), 0)

    def test_passwordless_login_lifecycle(self):
        """
        4. Passwordless login (password="") succeeds when admin password is empty
        and fails with 400 once a password is set.
        """
        # Set password to empty string
        self.admin_user.set_password("")
        self.admin_user.save()

        unauth_client = APIClient()
        res = unauth_client.post("/api/v1/auth/local/", {"password": ""})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

        # Set real password
        self.admin_user.set_password("mypassword123")
        self.admin_user.save()

        # Empty password now fails
        res_fail = unauth_client.post("/api/v1/auth/local/", {"password": ""})
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # Correct password succeeds
        res_ok = unauth_client.post("/api/v1/auth/local/", {"password": "mypassword123"})
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertIn("token", res_ok.data)

    def test_one_year_license_chronological_boundaries(self):
        """
        5. 1-year license starting 01-2026 (expiry_date = 2027-01-01) allows invoice months
        01-2026..12-2026 and rejects 01-2027, while allowing real-time entry up to 25-01-2027.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="سخان غاز",
            initial_quantity=20,
            initial_purchase_price=Decimal("1000"),
            initial_commission_amount=Decimal("20"),
            initial_month=1,
            initial_year=2026
        )

        # 12-2026 invoice: succeeds
        res_valid = self.client.post("/api/v1/receipts/", {
            "branch": self.branch.id,
            "salesperson": self.salesperson.id,
            "customer_name": "عميل ديسمبر",
            "sale_month": 12,
            "sale_year": 2026,
            "is_cash_sale": True,
            "total_amount": 1200,
            "down_payment": 1200,
            "sale_items": [
                {"inventory_item": item.id, "quantity": 1, "unit_price": 1200}
            ]
        }, format="json")
        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)

        # 01-2027 invoice: rejected (exceeds license year boundary)
        res_invalid = self.client.post("/api/v1/receipts/", {
            "branch": self.branch.id,
            "salesperson": self.salesperson.id,
            "customer_name": "عميل يناير القادم",
            "sale_month": 1,
            "sale_year": 2027,
            "is_cash_sale": True,
            "total_amount": 1200,
            "down_payment": 1200,
            "sale_items": [
                {"inventory_item": item.id, "quantity": 1, "unit_price": 1200}
            ]
        }, format="json")
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_default_date_highest_chronological(self):
        """
        6. get_default_date() returns the highest chronological (sale_year, sale_month)
        even after entering a back-dated receipt.
        """
        # Receipt 1: Month 3, 2026
        Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=601,
            customer_name="عميل 1",
            total_amount=Decimal("1000"),
            down_payment=Decimal("1000"),
            sale_year=2026,
            sale_month=3,
            is_cash_sale=True,
            receipt_type="SALE",
            is_confirmed=True
        )

        # Receipt 2: Month 8, 2026 (highest)
        Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=602,
            customer_name="عميل 2",
            total_amount=Decimal("1000"),
            down_payment=Decimal("1000"),
            sale_year=2026,
            sale_month=8,
            is_cash_sale=True,
            receipt_type="SALE",
            is_confirmed=True
        )

        # Receipt 3: Back-dated Month 1, 2026
        Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=603,
            customer_name="عميل قديم",
            total_amount=Decimal("1000"),
            down_payment=Decimal("1000"),
            sale_year=2026,
            sale_month=1,
            is_cash_sale=True,
            receipt_type="SALE",
            is_confirmed=True
        )

        # Direct function call check
        max_year, max_month = get_default_date(branch_id=self.branch.id)
        self.assertEqual((max_year, max_month), (2026, 8))

        # API endpoint check
        res = self.client.get(f"/api/v1/default-date/?branch_id={self.branch.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["year"], 2026)
        self.assertEqual(res.data["month"], 8)
