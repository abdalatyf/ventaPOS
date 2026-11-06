from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    Receipt,
    SaleItem,
    InstallmentPayment,
    ClientLicense,
    CompanySetting,
)
from api.utils.security_utils import (
    get_machine_id,
    generate_record_signature,
    generate_receipt_signature,
)


class ReturnsWorkflowTests(TestCase):
    """
    Automated test suite for customer returns:
    1. Cash receipt returns (stock restoration, cash refund, drawer vs P&L/Card 1/Salaries timing).
    2. Partial installment receipt returns (debt rescheduling, upfront credit reserve adjustment).
    3. Over-return rejection across multiple partial returns.
    4. Invalid return date rejection.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True}
        )
        self.client.force_authenticate(user=self.admin_user)

        self.branch = Branch.objects.create(name="فرع المعادي")
        self.salesperson = Salesperson.objects.create(
            branch=self.branch, name="مندوب المبيعات التجريبي"
        )
        self.company_setting = CompanySetting.objects.create(
            name="شركة فينتابوس",
            phone1="01000000000",
            collection_commission_rate=0.10,
        )

        self.mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, self.mach_id, 1, True)
        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=self.mach_id,
            license_code_hash=sig,
        )
        self.client.credentials(HTTP_X_COMPANY_CODE="TESTRET")

    def test_cash_receipt_full_and_partial_return_flow(self):
        """
        Verify cash sale return:
        - Return receipt created with down_payment = cash refund.
        - Physical stock restored in return month.
        - Cash drawer reflects cash outflow in return month.
        - Dashboard Card 1, P&L, and salesperson commission deduct revenue, COGS, and مندبة in original sale month.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة أوتوماتيك 8ك",
            initial_quantity=10,
            initial_purchase_price=4000,
            initial_commission_amount=100,
            initial_month=1,
            initial_year=2026,
        )

        # 1. Cash sale in Month 2: 3 units sold @ 6000 = 18,000 EGP
        sale = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=201,
            customer_name="عميل كاش",
            receipt_type="SALE",
            total_amount=18000,
            down_payment=18000,
            is_cash_sale=True,
            sale_month=2,
            sale_year=2026,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=sale,
            inventory_item=item,
            quantity=3,
            unit_price=6000,
        )

        # In Month 2, available stock is 10 - 3 = 7
        self.assertEqual(item.get_stock_at_date(2, 2026), 7)

        # 2. Return 1 unit in Month 3
        res = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 3,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return_id = res.json()["return_receipt_id"]
        return_rcpt = Receipt.objects.get(id=return_id)

        # Assert return receipt properties
        self.assertEqual(return_rcpt.receipt_type, "RETURN")
        self.assertEqual(return_rcpt.total_amount, Decimal("6000.00"))
        self.assertEqual(return_rcpt.down_payment, Decimal("6000.00"))
        self.assertEqual(return_rcpt.sale_month, 3)
        self.assertEqual(return_rcpt.sale_year, 2026)
        self.assertEqual(return_rcpt.parent_receipt_id, sale.id)

        # Physical stock restored in Month 3: 7 + 1 = 8
        self.assertEqual(item.get_stock_at_date(2, 2026), 7)
        self.assertEqual(item.get_stock_at_date(3, 2026), 8)

        # Cash Drawer in Month 3 (return month): reflects cash refund outflow of 6000
        dash_res_m3 = self.client.get(
            "/api/v1/reports/dashboard/summary/",
            {"branch_id": self.branch.id, "month": 3, "year": 2026},
        )
        self.assertEqual(dash_res_m3.status_code, status.HTTP_200_OK)
        drawer_m3 = dash_res_m3.json()["cash_drawer_summary"]
        self.assertEqual(drawer_m3["sales_returns_cash"], 6000)

        # Dashboard Card 1 in Month 2 (original sale month):
        # Revenue was 18,000 - 6,000 = 12,000
        # COGS was 12,000 - 4,000 = 8,000
        # Sales Comm was 300 - 100 = 200
        dash_res_m2 = self.client.get(
            "/api/v1/reports/dashboard/summary/",
            {"branch_id": self.branch.id, "month": 2, "year": 2026},
        )
        self.assertEqual(dash_res_m2.status_code, status.HTTP_200_OK)
        kpis_m2 = dash_res_m2.json()["kpis"]
        self.assertEqual(kpis_m2["total_revenue"], 12000)
        self.assertEqual(kpis_m2["total_cogs"], 8000)
        self.assertEqual(kpis_m2["total_sales_commissions"], 200)

        # P&L Report in Month 2: matches Card 1 net calculations
        pl_res_m2 = self.client.get(
            "/api/v1/reports/sales-pl/",
            {"branch_id": self.branch.id, "month": 2, "year": 2026},
        )
        self.assertEqual(pl_res_m2.status_code, status.HTTP_200_OK)
        pl_summary_m2 = pl_res_m2.json()["summary"]
        self.assertEqual(pl_summary_m2["grand_revenue"], 12000)
        self.assertEqual(pl_summary_m2["grand_cost"], 8000)

        # Salesperson Performance Report in Month 2:
        sp_res_m2 = self.client.get(
            "/api/v1/reports/salespersons/",
            {"branch_id": self.branch.id, "month": 2, "year": 2026},
        )
        self.assertEqual(sp_res_m2.status_code, status.HTTP_200_OK)
        sp_data_m2 = sp_res_m2.json()["salespersons"][0]
        self.assertEqual(sp_data_m2["total_sales_val"], 12000)
        self.assertEqual(sp_data_m2["comm_sales"], 200)

    def test_installment_receipt_partial_return_and_debt_rescheduling(self):
        """
        Verify partial credit sale return:
        - Future installments are deleted and rescheduled to match new_debt.
        - Upfront credit reserve in original sale month drops proportionally.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة سمارت 55",
            initial_quantity=10,
            initial_purchase_price=5000,
            initial_commission_amount=150,
            initial_month=1,
            initial_year=2026,
        )

        # Credit sale in Month 1: 2 units @ 6000 = 12,000 EGP
        # Down payment 2,000 EGP, financed debt = 10,000 EGP (2 x 5000 in Months 2 & 3)
        sale = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=101,
            customer_name="عميل قسط",
            receipt_type="SALE",
            total_amount=12000,
            down_payment=2000,
            is_cash_sale=False,
            sale_month=1,
            sale_year=2026,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=sale,
            inventory_item=item,
            quantity=2,
            unit_price=6000,
        )
        p1 = InstallmentPayment.objects.create(
            receipt=sale, amount=5000, payment_date=date(2026, 2, 25)
        )
        p2 = InstallmentPayment.objects.create(
            receipt=sale, amount=5000, payment_date=date(2026, 3, 25)
        )

        # Month 1 Upfront Credit Reserve before return: 10,000 * 0.10 = 1,000 EGP
        dash_m1 = self.client.get(
            "/api/v1/reports/dashboard/summary/",
            {"branch_id": self.branch.id, "month": 1, "year": 2026},
        ).json()["kpis"]
        self.assertEqual(dash_m1["total_collection_commissions"], 1000)

        # In Month 2: return 1 unit (Value 6,000 EGP).
        # paid_so_far = down_payment (2000) + prior payments (0) = 2000.
        # new_debt = 12000 - 6000 - 2000 = 4000 EGP.
        res = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 2,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
                "new_installments": [
                    {"amount": 4000, "payment_month": 2, "payment_year": 2026}
                ],
                "new_installment_system": "قسط معدل 4000",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Old installments marked deleted
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertTrue(p1.is_deleted)
        self.assertTrue(p2.is_deleted)

        # New installment created
        active_payments = sale.payments.filter(is_deleted=False)
        self.assertEqual(active_payments.count(), 1)
        new_inst = active_payments.first()
        self.assertEqual(new_inst.amount, Decimal("4000.00"))
        self.assertEqual(new_inst.payment_date, date(2026, 2, 25))

        # Month 1 Upfront Credit Reserve after return:
        # Net financed debt = (12,000 - 2,000) - 6,000 = 4,000 EGP.
        # Reserve = 4,000 * 0.10 = 400 EGP.
        dash_m1_after = self.client.get(
            "/api/v1/reports/dashboard/summary/",
            {"branch_id": self.branch.id, "month": 1, "year": 2026},
        ).json()["kpis"]
        self.assertEqual(dash_m1_after["total_collection_commissions"], 400)

    def test_over_return_rejection(self):
        """
        Verify rejection of return quantities exceeding the original sale quantity,
        including multiple cumulative partial returns.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="مفرش سرير فاخر",
            initial_quantity=10,
            initial_purchase_price=500,
            initial_commission_amount=30,
            initial_month=1,
            initial_year=2026,
        )
        sale = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=301,
            customer_name="عميل مفروشات",
            receipt_type="SALE",
            total_amount=1600,
            down_payment=1600,
            is_cash_sale=True,
            sale_month=1,
            sale_year=2026,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=sale,
            inventory_item=item,
            quantity=2,
            unit_price=800,
        )

        # 1st partial return: 1 unit in Month 2 -> Success
        res1 = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 2,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # 2nd return attempt: try to return 2 units in Month 3 -> Rejection
        res2 = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 3,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("تتخطى الكمية المتاحة للإرجاع", res2.json().get("error", ""))

    def test_return_prior_month_rejection(self):
        """
        Verify that a return receipt cannot be dated prior to or in the same month as the original sale.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="مروحة عمود",
            initial_quantity=5,
            initial_purchase_price=800,
            initial_commission_amount=50,
            initial_month=1,
            initial_year=2026,
        )
        sale = Receipt.objects.create(
            branch=self.branch,
            salesperson=self.salesperson,
            receipt_number=401,
            customer_name="عميل مراوح",
            receipt_type="SALE",
            total_amount=1200,
            down_payment=1200,
            is_cash_sale=True,
            sale_month=3,
            sale_year=2026,
            is_confirmed=True,
        )
        SaleItem.objects.create(
            receipt=sale,
            inventory_item=item,
            quantity=1,
            unit_price=1200,
        )

        # Attempt return in same month (Month 3) -> Rejection
        res_same = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 3,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(res_same.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لا يمكن أن يكون قبل الشهر التالي", res_same.json().get("error", ""))

        # Attempt return in earlier month (Month 2) -> Rejection
        res_early = self.client.post(
            f"/api/v1/receipts/{sale.id}/return_receipt/",
            {
                "return_month": 2,
                "return_year": 2026,
                "returned_items": [{"inventory_item_id": item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(res_early.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("لا يمكن أن يكون قبل الشهر التالي", res_early.json().get("error", ""))
