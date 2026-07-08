import uuid
from datetime import date
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Tenant, Branch, Salesperson, Receipt, ClientLicense
from api.utils.security_utils import generate_record_signature, get_machine_id


class SearchReceiptsTests(TestCase):
    databases = ["default", "system"]

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.using("default").create(
            company_code="SEARCH",
            name="Search Tenant",
            is_active=True
        )
        self.branch1 = Branch.objects.using("default").create(
            tenant=self.tenant,
            name="Branch 1",
            local_id=1
        )
        self.branch2 = Branch.objects.using("default").create(
            tenant=self.tenant,
            name="Branch 2",
            local_id=2
        )
        self.salesperson1 = Salesperson.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch1,
            local_id=10,
            name="Mandoob 1"
        )
        self.salesperson2 = Salesperson.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch2,
            local_id=20,
            name="Mandoob 2"
        )

        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, mach_id, 1, True)

        self.license = ClientLicense.objects.using("system").create(
            tenant=self.tenant,
            company_code="SEARCH",
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig,
        )

        self.client.credentials(HTTP_X_COMPANY_CODE="SEARCH")

        # Create sample receipts for testing filter combinations
        self.r1 = Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch1,
            salesperson=self.salesperson1,
            local_id=1,
            receipt_number=101,
            client_uuid=uuid.uuid4(),
            receipt_hash=uuid.uuid4().hex,
            customer_name="احمد علي",
            phone_number="01012345678",
            address="شارع النصر",
            area="مدينة نصر",
            total_amount=500,
            down_payment=500,
            is_cash_sale=True,
            sale_year=2026,
            sale_month=5,
            created_at_local=timezone.now()
        )

        self.r2 = Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch2,
            salesperson=self.salesperson2,
            local_id=2,
            receipt_number=102,
            client_uuid=uuid.uuid4(),
            receipt_hash=uuid.uuid4().hex,
            customer_name="محمود حسن",
            phone_number="01198765432",
            address="شارع التحرير",
            area="الدقي",
            total_amount=1200,
            down_payment=200,
            is_cash_sale=False,
            sale_year=2026,
            sale_month=6,
            created_at_local=timezone.now()
        )

        self.r3 = Receipt.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch1,
            salesperson=self.salesperson1,
            local_id=3,
            receipt_number=103,
            client_uuid=uuid.uuid4(),
            receipt_hash=uuid.uuid4().hex,
            customer_name="احمد مصطفى",
            phone_number="01234567890",
            address="شارع الأهرام",
            area="الجيزة",
            total_amount=750,
            down_payment=750,
            is_cash_sale=True,
            sale_year=2025,
            sale_month=12,
            created_at_local=timezone.now()
        )

    def test_filter_customer_name_and_year(self):
        # GET /api/v1/receipts/?customer_name=احمد&year=2026
        response = self.client.get("/api/v1/receipts/", {
            "customer_name": "احمد",
            "year": "2026"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r1.id))

    def test_filter_branch_id_by_local_id_and_uuid(self):
        # By local_id integer
        response = self.client.get("/api/v1/receipts/", {"branch_id": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r2.id))

        # By UUID
        response = self.client.get("/api/v1/receipts/", {"branch_id": str(self.branch1.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

    def test_filter_salesperson_by_local_id_and_uuid(self):
        # By local_id using salesperson_id
        response = self.client.get("/api/v1/receipts/", {"salesperson_id": "20"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r2.id))

        # By alias salesperson parameter with UUID
        response = self.client.get("/api/v1/receipts/", {"salesperson": str(self.salesperson1.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

    def test_filter_arabic_numerals_year_month_receipt_range(self):
        # Filter with Arabic numerals for year, month, and receipt range
        # year=٢٠٢٦ (2026), month=٦ (6), receipt_from=١٠١ (101), receipt_to=١٠٥ (105)
        response = self.client.get("/api/v1/receipts/", {
            "year": "٢٠٢٦",
            "month": "٦",
            "receipt_from": "١٠١",
            "receipt_to": "١٠٥"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r2.id))

    def test_filter_phone_address_area(self):
        # Filter by phone (using phone_number param with Arabic numerals), address, area
        response = self.client.get("/api/v1/receipts/", {
            "phone_number": "٠١١٩٨٧",
            "address": "التحرير",
            "area": "الدقي"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r2.id))

    def test_filter_is_cash_sale(self):
        # Cash sale true
        response = self.client.get("/api/v1/receipts/", {"is_cash_sale": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

        # Cash sale false
        response = self.client.get("/api/v1/receipts/", {"is_cash_sale": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.r2.id))
