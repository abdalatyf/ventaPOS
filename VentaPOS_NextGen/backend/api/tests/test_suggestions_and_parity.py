from datetime import date
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Tenant, Branch, Salesperson, InventoryItem, Receipt, ClientLicense, InstallmentPayment, SaleItem
from api.serializers import InstallmentPaymentSerializer, ReceiptSerializer
from api.utils.security_utils import generate_receipt_signature, generate_record_signature, get_machine_id

class AutocompleteAndParityTests(TestCase):
    databases = ["default", "system"]

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.using("default").create(
            company_code="AUTO",
            name="Autocomplete Tenant",
            is_active=True
        )
        self.branch = Branch.objects.using("default").create(
            tenant=self.tenant,
            name="Autocomplete Branch",
            local_id=1
        )
        self.salesperson = Salesperson.objects.using("default").create(
            tenant=self.tenant,
            branch=self.branch,
            local_id=10,
            name="Mandoob"
        )
        
        # Resolve the actual machine ID for the test environment
        mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 1000, mach_id, 1, True)
        
        self.license = ClientLicense.objects.using("system").create(
            tenant=self.tenant,
            company_code="AUTO",
            product_id=1,
            start_date=date(2025, 1, 1),
            expiry_date=expiry,
            invoices_balance=1000,
            is_active=True,
            machine_id=mach_id,
            license_code_hash=sig,
        )

        # Set headers
        self.client.credentials(HTTP_X_COMPANY_CODE="AUTO")

    def test_customer_suggestions_area_field(self):
        # Create receipts with some historical data
        r1 = Receipt.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, salesperson=self.salesperson,
            local_id=1, receipt_number=1,
customer_name="Customer A",
            phone_number="012345", address="Cairo", area="Heliopolis",
            total_amount=100, down_payment=100, is_cash_sale=True,
            sale_year=2026, sale_month=6, created_at_local=timezone.now()
        )
        r2 = Receipt.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, salesperson=None,
            local_id=2, receipt_number=2,
customer_name="Customer B",
            phone_number="012346", address="Cairo", area="Helwan",
            total_amount=100, down_payment=100, is_cash_sale=True,
            sale_year=2026, sale_month=6, created_at_local=timezone.now()
        )

        # Query Heliopolis (starts with Hel) vs Helwan (starts with Hel)
        # Heliopolis has salesperson matching, so relevance Heliopolis = 50 + 20 = 70. Helwan = 50.
        # Heliopolis should be returned first
        response = self.client.get("/api/v1/customer-suggestions/", {
            "term": "Hel",
            "field": "area",
            "salesperson_id": str(self.salesperson.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["value"], "Heliopolis")
        self.assertEqual(data[1]["value"], "Helwan")

    def test_customer_suggestions_arabic_numerals(self):
        # Query using Arabic numerals term: "٠١٢" (which translates to "012")
        Receipt.objects.using("default").create(
            tenant=self.tenant, branch=self.branch,
            local_id=3, receipt_number=3,
customer_name="Ahmed",
            phone_number="012999", address="Cairo", area="Giza",
            total_amount=100, down_payment=100, is_cash_sale=True,
            sale_year=2026, sale_month=6, created_at_local=timezone.now()
        )

        response = self.client.get("/api/v1/customer-suggestions/", {
            "term": "٠١٢",
            "field": "phone"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], "٠١٢٩٩٩")

    def test_product_suggestions_stock_validation(self):
        # Create an inventory item
        item = InventoryItem.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, local_id=1,
            name="Laptop Lenovo", initial_quantity=10, initial_purchase_price=1000,
            initial_commission_amount=50, initial_month=1, initial_year=2026
        )

        # Create a sale of 3 items in month 4
        receipt = Receipt.objects.using("default").create(
            tenant=self.tenant, branch=self.branch, local_id=4, receipt_number=4,

            customer_name="Ahmed", total_amount=3000, down_payment=3000,
            is_cash_sale=True, sale_year=2026, sale_month=4, created_at_local=timezone.now()
        )
        SaleItem.objects.using("default").create(
            tenant=self.tenant, receipt=receipt, inventory_item=item, quantity=3, unit_price=1000
        )

        # The branch default date (last receipt) is month 4, year 2026.
        # We query for month 2, year 2026.
        # Between target (month 2) and default (month 4) inclusive, stock levels are:
        # month 2: 10
        # month 3: 10
        # month 4: 7
        # Minimum stock level in this range is 7.
        response = self.client.get("/api/v1/product-suggestions/", {
            "branch_id": str(self.branch.id),
            "term": "Lenovo",
            "month": "2",
            "year": "2026"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], "Laptop Lenovo")
        self.assertEqual(data[0]["max"], 7)

    def test_serializer_day_25_installment_payment(self):
        # InstallmentPaymentSerializer.to_internal_value
        data = {
            "payment_month": 5,
            "payment_year": 2026,
            "amount": 250
        }
        serializer = InstallmentPaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["payment_date"].day, 25)

        # ReceiptSerializer fallback installment date to day 25
        receipt_data = {
            "branch": self.branch.id,
            "salesperson": self.salesperson.id,
            "local_id": 100,
            "receipt_number": 100,
                        "customer_name": "Ahmed",
            "total_amount": 500,
            "down_payment": 250,
            "is_cash_sale": False,
            "sale_month": 5,
            "sale_year": 2026,
            "installment_payments": [
                {
                    "payment_month": 6,
                    "payment_year": 2026,
                    "amount": 250
                }
            ]
        }
        serializer = ReceiptSerializer(data=receipt_data, context={"tenant": self.tenant})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        receipt = serializer.save(tenant=self.tenant)
        installment = receipt.installment_payments.first()
        self.assertEqual(installment.payment_date.day, 25)
