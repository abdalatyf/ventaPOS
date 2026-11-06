"""
Tests for Batch V1-2 in VentaPOS NextGen:
- Item 9: Enforce English whole integers in UI & Arabic-Indic whole integers in Print.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from api.models import (
    Branch,
    Salesperson,
    Receipt,
    CompanySetting,
)
from api.print_utils import to_arabic_numerals, ed2ad
from api.views.receipt_views import ReceiptViewSet


class ArabicNumeralsFormattingTests(TestCase):
    def test_to_arabic_numerals_decimal_string(self):
        self.assertEqual(to_arabic_numerals("1500.00"), "١٥٠٠")
        self.assertEqual(to_arabic_numerals("1500.49"), "١٥٠٠")
        self.assertEqual(to_arabic_numerals("1500.50"), "١٥٠١")

    def test_to_arabic_numerals_decimal_object(self):
        self.assertEqual(to_arabic_numerals(Decimal("250.60")), "٢٥١")
        self.assertEqual(to_arabic_numerals(Decimal("100.00")), "١٠٠")
        self.assertEqual(to_arabic_numerals(Decimal("0.00")), "٠")

    def test_to_arabic_numerals_float_object(self):
        self.assertEqual(to_arabic_numerals(1500.0), "١٥٠٠")
        self.assertEqual(to_arabic_numerals(250.6), "٢٥١")

    def test_to_arabic_numerals_preserves_phone_leading_zero(self):
        self.assertEqual(to_arabic_numerals("01012345678"), "٠١٠١٢٣٤٥٦٧٨")
        self.assertEqual(to_arabic_numerals("01234567890"), "٠١٢٣٤٥٦٧٨٩٠")

    def test_to_arabic_numerals_preserves_dates(self):
        self.assertEqual(to_arabic_numerals("2026/08/25"), "٢٠٢٦/٠٨/٢٥")
        self.assertEqual(to_arabic_numerals("2026-08-25"), "٢٠٢٦-٠٨-٢٥")

    def test_to_arabic_numerals_integers_and_none(self):
        self.assertEqual(to_arabic_numerals(1234), "١٢٣٤")
        self.assertEqual(to_arabic_numerals(0), "٠")
        self.assertEqual(to_arabic_numerals(None), "")
        self.assertEqual(to_arabic_numerals(""), "")

    def test_ed2ad_alias(self):
        self.assertEqual(ed2ad("1500.00"), "١٥٠٠")
        self.assertEqual(ed2ad(Decimal("250.60")), "٢٥١")
        self.assertEqual(ed2ad("01012345678"), "٠١٠١٢٣٤٥٦٧٨")

    def test_prepare_pdf_context_formatting(self):
        branch = Branch.objects.create(name="الفرع الرئيسي")
        salesperson = Salesperson.objects.create(branch=branch, name="مندوب 1")
        CompanySetting.objects.create(name="شركة التميز", phone1="01012345678")

        receipt = Receipt.objects.create(
            branch=branch,
            salesperson=salesperson,
            receipt_number=1001,
            customer_name="أحمد محمود",
            phone_number="01098765432",
            sale_month=8,
            sale_year=2026,
            total_amount=Decimal("1500.00"),
            down_payment=Decimal("300.00"),
            is_cash_sale=False,
            installment_system="200*6"
        )

        viewset = ReceiptViewSet()
        ctx = viewset._prepare_pdf_context(receipt)

        self.assertEqual(ctx['total_amount'], "١٥٠٠")
        self.assertEqual(ctx['down_payment'], "٣٠٠")
        self.assertEqual(ctx['remaining_amount'], "١٢٠٠")
        self.assertEqual(ctx['phone_number'], "٠١٠٩٨٧٦٥٤٣٢")
        self.assertNotIn(".٠٠", ctx['total_amount'])
        self.assertNotIn(".٠٠", ctx['remaining_amount'])
