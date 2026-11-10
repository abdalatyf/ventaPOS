"""
Comprehensive Tests for AreasReportView, Redesigned PurchasesReportView (Product x Supplier Matrix),
and Cross-Report Salesperson & Area Filtering in VentaPOS NextGen.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date
from rest_framework.test import APIClient
from api.models import (
    Branch, Salesperson, InventoryItem, Supplier,
    PurchaseInvoice, PurchaseInvoiceItem, Receipt, SaleItem,
    InstallmentPayment, Expense, ClientLicense
)
from api.utils.security_utils import generate_record_signature, get_machine_id


class AreasAndPurchasesReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.admin_user, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True})
        self.client.force_authenticate(user=self.admin_user)

        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, mach_id, 1, True)

        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig
        )

        self.branch = Branch.objects.create(name="الفرع الرئيسي")
        self.branch2 = Branch.objects.create(name="فرع الإسكندرية")

        self.sp1 = Salesperson.objects.create(branch=self.branch, name="علي حسن")
        self.sp2 = Salesperson.objects.create(branch=self.branch, name="محمد سمير")

        self.supp1 = Supplier.objects.create(branch=self.branch, name="مورد الأجهزة الحديثة")
        self.supp2 = Supplier.objects.create(branch=self.branch, name="مورد المفروشات الفاخرة")

        self.item1 = InventoryItem.objects.create(
            branch=self.branch,
            name="غسالة توشيبا 10 كيلو",
            initial_quantity=10,
            initial_purchase_price=5000,
            initial_commission_amount=100
        )
        self.item2 = InventoryItem.objects.create(
            branch=self.branch,
            name="طقم انتريه قطيفة",
            initial_quantity=5,
            initial_purchase_price=8000,
            initial_commission_amount=200
        )

    def test_areas_report_aggregation_and_kpis(self):
        """
        Verify AreasReportView aggregates receipts by area and calculates all KPIs properly.
        """
        # Sale 1 in المعادي by sp1: Cash sale 6000
        Receipt.objects.create(
            branch=self.branch,
            receipt_number=101,
            sale_year=2026,
            sale_month=8,
            salesperson=self.sp1,
            customer_name="محمود سعيد",
            area="المعادي",
            total_amount=6000,
            is_cash_sale=True,
            is_confirmed=True
        )

        # Sale 2 in المعادي by sp2: Installment sale 12000 with down payment 2000
        r2 = Receipt.objects.create(
            branch=self.branch,
            receipt_number=102,
            sale_year=2026,
            sale_month=8,
            salesperson=self.sp2,
            customer_name="خالد إبراهيم",
            area="المعادي",
            total_amount=12000,
            down_payment=2000,
            is_cash_sale=False,
            is_confirmed=True
        )
        # Add scheduled installment payment due in 2026/08
        InstallmentPayment.objects.create(
            receipt=r2,
            payment_date=date(2026, 8, 25),
            amount=1000
        )

        # Sale 3 in مدينة نصر by sp1: Installment sale 15000 with down payment 3000
        r3 = Receipt.objects.create(
            branch=self.branch,
            receipt_number=103,
            sale_year=2026,
            sale_month=8,
            salesperson=self.sp1,
            customer_name="طارق يوسف",
            area="مدينة نصر",
            total_amount=15000,
            down_payment=3000,
            is_cash_sale=False,
            is_confirmed=True
        )
        InstallmentPayment.objects.create(
            receipt=r3,
            payment_date=date(2026, 8, 25),
            amount=1200
        )

        # Return in المعادي: 2000 returned
        Receipt.objects.create(
            branch=self.branch,
            receipt_number=104,
            receipt_type="RETURN",
            sale_year=2026,
            sale_month=8,
            salesperson=self.sp1,
            customer_name="محمود سعيد",
            area="المعادي",
            total_amount=2000,
            is_cash_sale=True,
            is_confirmed=True
        )

        # Query endpoint
        res = self.client.get(f"/api/v1/reports/areas/?branch_id={self.branch.id}&year=2026&month=8")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("summary", data)
        self.assertIn("areas", data)
        summary = data["summary"]

        # Gross sales: (6000 + 12000 + 15000) = 33000
        self.assertEqual(summary["total_sales"], 33000)
        # Returns: 2000
        self.assertEqual(summary["total_returns_amount"], 2000)
        # Net sales: 33000 - 2000 = 31000
        self.assertEqual(summary["net_sales"], 31000)
        # Down payments: 2000 + 3000 = 5000
        self.assertEqual(summary["total_down_payments"], 5000)
        # Due installments: 1000 + 1200 = 2200
        self.assertEqual(summary["total_due_installments"], 2200)
        # Areas count: 2 (المعادي, مدينة نصر)
        self.assertEqual(summary["areas_count"], 2)

        # Verify area rows
        areas = data["areas"]
        maadi = next((a for a in areas if a["area"] == "المعادي"), None)
        self.assertIsNotNone(maadi)
        self.assertEqual(maadi["cash_sales"], 6000)
        self.assertEqual(maadi["installment_sales"], 12000)
        self.assertEqual(maadi["gross_sales"], 18000)
        self.assertEqual(maadi["returns_amount"], 2000)
        self.assertEqual(maadi["net_sales"], 16000)
        self.assertEqual(maadi["due_installments_month"], 1000)
        self.assertIn("علي حسن", maadi["salespersons_display"])
        self.assertIn("محمد سمير", maadi["salespersons_display"])

    def test_areas_report_filtering_by_salesperson_and_area(self):
        """
        Verify filtering AreasReportView by salesperson_id and area query param.
        """
        Receipt.objects.create(
            branch=self.branch,
            receipt_number=201,
            sale_year=2026,
            sale_month=9,
            salesperson=self.sp1,
            customer_name="عميل 1",
            area="الدقي",
            total_amount=5000,
            is_cash_sale=True,
            is_confirmed=True
        )
        Receipt.objects.create(
            branch=self.branch,
            receipt_number=202,
            sale_year=2026,
            sale_month=9,
            salesperson=self.sp2,
            customer_name="عميل 2",
            area="المهندسين",
            total_amount=9000,
            is_cash_sale=True,
            is_confirmed=True
        )

        # Filter by salesperson 1
        res_sp1 = self.client.get(f"/api/v1/reports/areas/?branch_id={self.branch.id}&year=2026&month=9&salesperson_id={self.sp1.id}")
        self.assertEqual(res_sp1.status_code, 200)
        data_sp1 = res_sp1.json()
        self.assertEqual(data_sp1["summary"]["total_sales"], 5000)
        self.assertEqual(len(data_sp1["areas"]), 1)
        self.assertEqual(data_sp1["areas"][0]["area"], "الدقي")

        # Filter by area substring
        res_area = self.client.get(f"/api/v1/reports/areas/?branch_id={self.branch.id}&year=2026&month=9&area=المهندسين")
        self.assertEqual(res_area.status_code, 200)
        data_area = res_area.json()
        self.assertEqual(data_area["summary"]["total_sales"], 9000)
        self.assertEqual(len(data_area["areas"]), 1)
        self.assertEqual(data_area["areas"][0]["area"], "المهندسين")

    def test_purchases_report_product_supplier_matrix(self):
        """
        Verify redesigned PurchasesReportView groups by (inventory_item_id, supplier_id)
        and computes net quantities, returns deduction, and weighted unit costs.
        """
        # Purchase Invoice 1: 5 units of item1 from supp1 @ 4000
        inv1 = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supp1,
            invoice_number=1,
            invoice_year=2026,
            invoice_month=8,
            invoice_type="PURCHASE"
        )
        PurchaseInvoiceItem.objects.create(
            invoice=inv1,
            inventory_item=self.item1,
            quantity=5,
            purchase_price=4000
        )

        # Purchase Invoice 2: 3 units of item1 from supp2 @ 4200
        inv2 = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supp2,
            invoice_number=2,
            invoice_year=2026,
            invoice_month=8,
            invoice_type="PURCHASE"
        )
        PurchaseInvoiceItem.objects.create(
            invoice=inv2,
            inventory_item=self.item1,
            quantity=3,
            purchase_price=4200
        )

        # Purchase Return Invoice 3: Return 1 unit of item1 to supp1 @ 4000
        inv3 = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supp1,
            invoice_number=3,
            invoice_year=2026,
            invoice_month=8,
            invoice_type="RETURN"
        )
        PurchaseInvoiceItem.objects.create(
            invoice=inv3,
            inventory_item=self.item1,
            quantity=1,
            purchase_price=4000
        )

        # Query Purchases Report
        res = self.client.get(f"/api/v1/reports/purchases/?branch_id={self.branch.id}&year=2026&month=8")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("summary", data)
        self.assertIn("items", data)
        self.assertIn("invoices", data)

        summary = data["summary"]
        # Gross purchases: (5*4000) + (3*4200) = 20000 + 12600 = 32600
        self.assertEqual(summary["gross_purchases_amount"], 32600.0)
        # Total returns: 1*4000 = 4000
        self.assertEqual(summary["total_returns_amount"], 4000.0)
        # Net purchases: 32600 - 4000 = 28600
        self.assertEqual(summary["total_purchases_amount"], 28600.0)
        # Total units net: 5 + 3 - 1 = 7
        self.assertEqual(summary["total_items_quantity"], 7)
        self.assertEqual(summary["suppliers_count"], 2)
        self.assertEqual(summary["distinct_products_count"], 1)

        # Verify grouped matrix items
        items = data["items"]
        # There should be 2 matrix rows: (item1, supp1) and (item1, supp2)
        self.assertEqual(len(items), 2)

        item1_supp1 = next((it for it in items if it["supplier_id"] == self.supp1.id), None)
        self.assertIsNotNone(item1_supp1)
        self.assertEqual(item1_supp1["purchased_qty"], 5)
        self.assertEqual(item1_supp1["returned_qty"], 1)
        self.assertEqual(item1_supp1["net_qty"], 4)
        self.assertEqual(item1_supp1["gross_purchases"], 20000.0)
        self.assertEqual(item1_supp1["returns_amount"], 4000.0)
        self.assertEqual(item1_supp1["net_purchases"], 16000.0)
        # Weighted cost: 16000 / 4 = 4000.0
        self.assertEqual(item1_supp1["avg_unit_cost"], 4000.0)

        # Verify supplier filter
        res_supp1 = self.client.get(f"/api/v1/reports/purchases/?branch_id={self.branch.id}&year=2026&month=8&supplier_id={self.supp1.id}")
        self.assertEqual(res_supp1.status_code, 200)
        data_supp1 = res_supp1.json()
        self.assertEqual(len(data_supp1["items"]), 1)
        self.assertEqual(data_supp1["items"][0]["supplier_name"], self.supp1.name)

    def test_salesperson_and_area_filters_across_all_reports(self):
        """
        Verify that passing salesperson_id and area filters to Dashboard, InventoryMovement,
        ProfitAndLoss, and SalespersonPerformance reports works consistently without error.
        """
        # Create a sale with items
        r = Receipt.objects.create(
            branch=self.branch,
            receipt_number=301,
            sale_year=2026,
            sale_month=10,
            salesperson=self.sp1,
            customer_name="عميل فلتر",
            area="شبرا",
            total_amount=10000,
            is_cash_sale=True,
            is_confirmed=True
        )
        SaleItem.objects.create(
            receipt=r,
            inventory_item=self.item1,
            quantity=2,
            unit_price=5000
        )

        endpoints = [
            f"/api/v1/reports/dashboard/?branch_id={self.branch.id}&year=2026&month=10&salesperson_id={self.sp1.id}&area=شبرا",
            f"/api/v1/reports/inventory-movement/?branch_id={self.branch.id}&year=2026&month=10&salesperson_id={self.sp1.id}&area=شبرا",
            f"/api/v1/reports/profit-and-loss/?branch_id={self.branch.id}&year=2026&month=10&salesperson_id={self.sp1.id}&area=شبرا",
            f"/api/v1/reports/salesperson-performance/?branch_id={self.branch.id}&year=2026&month=10&salesperson_id={self.sp1.id}&area=شبرا",
            f"/api/v1/reports/cash-drawer-details/?branch_id={self.branch.id}&year=2026&month=10&salesperson_id={self.sp1.id}&area=شبرا",
        ]

        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"Failed at endpoint {url}")

    def test_desktop_print_areas_and_purchases_html_headers(self):
        """
        Verify that ReportDesktopPrintView handles report_type='areas' and report_type='purchases',
        maps them to the respective analytical report data, and renders HTML containing the expected
        Arabic table headers and data.
        """
        from unittest.mock import patch

        # 1. Test Areas Desktop Print HTML
        with patch("api.views.report_views.generate_and_open_pdf") as mock_pdf:
            mock_pdf.return_value = (True, "PDF generated")
            res_areas = self.client.post("/api/v1/reports/desktop_print/", {
                "report_type": "areas",
                "branch_id": self.branch.id,
                "year": 2026,
                "month": 8,
                "action": "view"
            }, format="json")

            self.assertEqual(res_areas.status_code, 200)
            mock_pdf.assert_called()
            html_areas = mock_pdf.call_args[0][0]

            expected_areas_headers = [
                "المنطقة", "عدد الفواتير", "مبيعات نقدي", "مبيعات تقسيط",
                "إجمالي المبيعات", "إجمالي المقدمات", "الأقساط المستحقة",
                "المرتجعات", "صافي المبيعات", "المناديب"
            ]
            for header in expected_areas_headers:
                self.assertIn(header, html_areas, f"Missing areas header: {header}")

        # 2. Test Purchases Desktop Print HTML (Product x Supplier Matrix)
        with patch("api.views.report_views.generate_and_open_pdf") as mock_pdf:
            mock_pdf.return_value = (True, "PDF generated")
            res_purch = self.client.post("/api/v1/reports/desktop_print/", {
                "report_type": "purchases",
                "branch_id": self.branch.id,
                "year": 2026,
                "month": 8,
                "action": "view"
            }, format="json")

            self.assertEqual(res_purch.status_code, 200)
            mock_pdf.assert_called()
            html_purch = mock_pdf.call_args[0][0]

            expected_purch_headers = [
                "اسم الصنف", "اسم المورد", "عدد الفواتير", "كمية الشراء",
                "كمية المرتجع", "صافي الكمية", "متوسط سعر الشراء",
                "إجمالي الشراء", "إجمالي المرتجع", "صافي المشتريات"
            ]
            for header in expected_purch_headers:
                self.assertIn(header, html_purch, f"Missing purchases header: {header}")

