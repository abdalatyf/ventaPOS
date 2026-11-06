"""
Tests for Batch V1-3 in VentaPOS NextGen:
- Item 2: General Print Modal & Chunked Printing.
- Item 3: Purchase & Report Print Handlers + Templates.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Branch,
    Supplier,
    InventoryItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    CompanySetting,
)


class BatchV13PurchaseDesktopPrintTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_authenticate(user=self.user)

        self.branch = Branch.objects.create(name="الفرع الرئيسي")
        self.supplier = Supplier.objects.create(name="مورد التوحيد")
        self.item1 = InventoryItem.objects.create(branch=self.branch, name="غسالة توشيبا", initial_quantity=10)
        self.company = CompanySetting.objects.create(name="معرض الأمانة", phone1="01234567890")

        self.invoice = PurchaseInvoice.objects.create(
            branch=self.branch,
            supplier=self.supplier,
            invoice_number=501,
            invoice_month=8,
            invoice_year=2026,
            invoice_type='PURCHASE'
        )
        self.invoice_item = PurchaseInvoiceItem.objects.create(
            invoice=self.invoice,
            inventory_item=self.item1,
            quantity=3,
            purchase_price=Decimal('5000.00')
        )

    @patch('api.views.purchase_views.generate_and_open_pdf')
    def test_desktop_print_view_mode(self, mock_gen_pdf):
        mock_gen_pdf.return_value = (True, "تم فتح المعاينة بنجاح")

        response = self.client.post('/api/v1/purchase-invoices/desktop_print/', {
            'invoice_ids': [self.invoice.id],
            'action': 'view'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        mock_gen_pdf.assert_called_once()
        args, kwargs = mock_gen_pdf.call_args
        self.assertEqual(kwargs.get('action'), 'view')
        self.assertEqual(kwargs.get('paper_size'), 'DL')
        # Check rendered HTML contains Arabic-Indic numerals
        html_content = args[0]
        self.assertIn('٥٠١', html_content)  # invoice_number 501
        self.assertIn('١٥٠٠٠', html_content)  # total_amount 15000
        self.assertIn('٣', html_content)  # quantity 3
        self.assertIn('٥٠٠٠', html_content)  # unit price 5000

    @patch('api.views.purchase_views.generate_and_open_pdf')
    def test_desktop_print_print_mode_with_target_printer(self, mock_gen_pdf):
        mock_gen_pdf.return_value = (True, "تم إرسال أمر الطباعة بنجاح")

        response = self.client.post('/api/v1/purchase-invoices/desktop_print/', {
            'invoice_ids': [self.invoice.id],
            'action': 'print',
            'target_printer': 'HP_LaserJet_Pro'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        mock_gen_pdf.assert_called_once()
        args, kwargs = mock_gen_pdf.call_args
        self.assertEqual(kwargs.get('action'), 'print')
        self.assertEqual(kwargs.get('target_printer'), 'HP_LaserJet_Pro')

    def test_desktop_print_missing_invoice_ids(self):
        response = self.client.post('/api/v1/purchase-invoices/desktop_print/', {
            'action': 'view'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_desktop_print_empty_invoice_ids(self):
        response = self.client.post('/api/v1/purchase-invoices/desktop_print/', {
            'invoice_ids': [],
            'action': 'view'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_desktop_print_nonexistent_invoice_ids(self):
        response = self.client.post('/api/v1/purchase-invoices/desktop_print/', {
            'invoice_ids': [99999],
            'action': 'view'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BatchV13ReportDesktopPrintTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_authenticate(user=self.user)

        self.branch = Branch.objects.create(name="فرع المعادي")
        self.company = CompanySetting.objects.create(name="شركة الفرات", phone1="01112223334")

    @patch('api.views.report_views.generate_and_open_pdf')
    def test_report_desktop_print_view_mode(self, mock_gen_pdf):
        mock_gen_pdf.return_value = (True, "تم فتح معاينة التقرير بنجاح")

        payload = {
            'title': 'تقرير المبيعات والتحصيلات',
            'branch_id': self.branch.id,
            'period_label': '2026/08',
            'filters_summary': [
                {'label': 'المندوب', 'value': 'أحمد إبراهيم'}
            ],
            'kpis': [
                {'label': 'إجمالي المبيعات', 'value': '25000', 'color': 'primary'},
                {'label': 'صافي الربح', 'value': '4500', 'color': 'success'}
            ],
            'columns': [
                {'key': 'item_name', 'label': 'الصنف', 'align': 'right'},
                {'key': 'quantity', 'label': 'الكمية', 'align': 'center'},
                {'key': 'total', 'label': 'الإجمالي', 'align': 'center'}
            ],
            'rows': [
                {'item_name': 'ثلاجة 16 قدم', 'quantity': 2, 'total': '16000'},
                {'item_name': 'مروحة سقف', 'quantity': 5, 'total': '4500'}
            ],
            'footer_row': [
                {'value': 'الإجمالي', 'align': 'center', 'colspan': 2},
                {'value': '20500', 'align': 'center'}
            ],
            'action': 'view'
        }

        response = self.client.post('/api/v1/reports/desktop_print/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        mock_gen_pdf.assert_called_once()
        args, kwargs = mock_gen_pdf.call_args
        self.assertEqual(kwargs.get('action'), 'view')
        self.assertEqual(kwargs.get('paper_size'), 'A4')

        html_content = args[0]
        # Numbers should be formatted in Arabic-Indic numerals
        self.assertIn('٢٠٢٦/٠٨', html_content)  # period_label 2026/08
        self.assertIn('٢٥٠٠٠', html_content)  # KPI 25000
        self.assertIn('٤٥٠٠', html_content)  # KPI 4500
        self.assertIn('١٦٠٠٠', html_content)  # Row total 16000
        self.assertIn('٢٠٥٠٠', html_content)  # Footer 20500
        self.assertIn('شركة الفرات', html_content)
        self.assertIn('فرع المعادي', html_content)

    @patch('api.views.report_views.generate_and_open_pdf')
    def test_report_desktop_print_print_mode(self, mock_gen_pdf):
        mock_gen_pdf.return_value = (True, "تم إرسال أمر طباعة التقرير")

        payload = {
            'title': 'تقرير حركة المخزون',
            'columns': [
                {'key': 'name', 'label': 'الصنف', 'align': 'center'}
            ],
            'rows': [
                {'name': 'بوتجاز 5 شعلة'}
            ],
            'action': 'print',
            'target_printer': 'Office_Network_Printer'
        }

        response = self.client.post('/api/v1/reports/desktop_print/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        mock_gen_pdf.assert_called_once()
        args, kwargs = mock_gen_pdf.call_args
        self.assertEqual(kwargs.get('action'), 'print')
        self.assertEqual(kwargs.get('target_printer'), 'Office_Network_Printer')

    def test_report_desktop_print_missing_title(self):
        payload = {
            'columns': [{'key': 'name', 'label': 'الصنف'}],
            'rows': [{'name': 'صنف'}]
        }
        response = self.client.post('/api/v1/reports/desktop_print/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_desktop_print_missing_columns(self):
        payload = {
            'title': 'تقرير تجريبي'
        }
        response = self.client.post('/api/v1/reports/desktop_print/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BatchV13ReceiptsPrintersEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_authenticate(user=self.user)

    @patch('subprocess.run')
    def test_printers_multiple_array_parsing(self, mock_subproc):
        mock_output = (
            '[{"Name":"HP LaserJet 1020","PrinterStatus":0,"WorkOffline":null,"IsDefault":true},'
            '{"Name":"EPSON L3150","PrinterStatus":7,"WorkOffline":false,"IsDefault":false},'
            '{"Name":"Canon G2010","PrinterStatus":0,"WorkOffline":true,"IsDefault":false}]'
        )
        mock_res = MagicMock()
        mock_res.stdout = mock_output
        mock_subproc.return_value = mock_res

        response = self.client.get('/api/v1/receipts/printers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        printers = response.data.get('printers', [])
        self.assertEqual(len(printers), 3)

        # HP: ready, default
        self.assertEqual(printers[0]['name'], "HP LaserJet 1020")
        self.assertEqual(printers[0]['status'], "ready")
        self.assertTrue(printers[0]['is_default'])

        # EPSON: offline because PrinterStatus == 7
        self.assertEqual(printers[1]['name'], "EPSON L3150")
        self.assertEqual(printers[1]['status'], "offline")
        self.assertFalse(printers[1]['is_default'])

        # Canon: offline because WorkOffline == true
        self.assertEqual(printers[2]['name'], "Canon G2010")
        self.assertEqual(printers[2]['status'], "offline")
        self.assertFalse(printers[2]['is_default'])

    @patch('subprocess.run')
    def test_printers_single_dict_parsing(self, mock_subproc):
        mock_output = '{"Name":"Microsoft Print to PDF","PrinterStatus":0,"WorkOffline":null,"IsDefault":true}'
        mock_res = MagicMock()
        mock_res.stdout = mock_output
        mock_subproc.return_value = mock_res

        response = self.client.get('/api/v1/receipts/printers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        printers = response.data.get('printers', [])
        self.assertEqual(len(printers), 1)
        self.assertEqual(printers[0]['name'], "Microsoft Print to PDF")
        self.assertEqual(printers[0]['status'], "ready")
        self.assertTrue(printers[0]['is_default'])

    @patch('subprocess.run')
    def test_printers_empty_output(self, mock_subproc):
        mock_res = MagicMock()
        mock_res.stdout = ""
        mock_subproc.return_value = mock_res

        response = self.client.get('/api/v1/receipts/printers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('printers'), [])

    @patch('subprocess.run')
    def test_printers_subprocess_failure(self, mock_subproc):
        mock_subproc.side_effect = Exception("PowerShell execution policy restricted")

        response = self.client.get('/api/v1/receipts/printers/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("فشل في جلب الطابعات", response.data.get('error'))

