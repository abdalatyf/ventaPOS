"""
Tests for Batch V1-4 in VentaPOS NextGen:
- Item 8: Standalone AI Agent Skill & Script for Raw Data -> .sqlite3 Backup Generator.
"""
import json
import os
import sqlite3
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

# Import the standalone backup builder script
SKILL_SCRIPT_PATH = Path("C:/Users/Abdo/.gemini/config/skills/ventapos-backup-generator/scripts").resolve()
if str(SKILL_SCRIPT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPT_PATH))

from build_sqlite_backup import build_backup, generate_receipt_signature, to_ascii_digits


class BatchV14BackupGeneratorTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_authenticate(user=self.user)

        self.temp_dir = tempfile.mkdtemp()
        self.sample_json_path = os.path.join(self.temp_dir, "sample_receipts.json")
        self.sample_csv_path = os.path.join(self.temp_dir, "sample_receipts.csv")
        self.output_db_path = os.path.join(self.temp_dir, "test_generated_backup.sqlite3")

        # 1. Sample Raw JSON Data (Legacy paper contracts)
        self.sample_receipts = [
            {
                "receipt_number": "101",
                "customer_name": "محمد حسن علي",
                "phone_number": "01012345678",
                "address": "بجوار المسجد الكبير",
                "area": "السنبلاوين",
                "salesperson_name": "أحمد السيد",
                "products_text": "غرفة نوم + غسالة توشيبا",
                "total_amount": "15000",
                "down_payment": "3000",
                "installment_system": "1000*12",
                "sale_date": "2025/11/15",
                "is_cash_sale": False
            },
            {
                "receipt_number": "102",
                "customer_name": "محمود إبراهيم",
                "phone_number": "01198765432",
                "address": "شارع المحطة",
                "area": "برقين",
                "salesperson_name": "طارق حسن",
                "products_text": "طقم انتريه قطيفة",
                "total_amount": "8000",
                "down_payment": "8000",
                "installment_system": "",
                "sale_date": "2026/01/10",
                "is_cash_sale": True
            },
            {
                "receipt_number": "103",
                "customer_name": "علي مصطفى",
                "phone_number": "01233445566",
                "address": "أمام الجمعية الزراعية",
                "area": "البلامون",
                "salesperson_name": "أحمد السيد",
                "products_text": "شاشة سامسونج 55 + ثلاجة",
                "total_amount": "22000",
                "down_payment": "4000",
                "installment_system": "1000*10 + 800*10",
                "sale_date": "2026/03/20",
                "is_cash_sale": False
            }
        ]

        with open(self.sample_json_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_receipts, f, ensure_ascii=False)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_sqlite_backup_from_json(self):
        """
        Verify that build_sqlite_backup creates a valid SQLite database with all required tables,
        correct cryptographic signatures, and 25th convention installment schedules.
        """
        out_path = build_backup(
            input_path=self.sample_json_path,
            output_path=self.output_db_path,
            branch_name="الفرع الرئيسي",
            lic_start="2026/08"
        )

        self.assertTrue(os.path.exists(out_path))

        conn = sqlite3.connect(out_path)
        cursor = conn.cursor()

        # 1. Integrity Check
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        self.assertEqual(res[0], "ok")

        # 2. Required 8 Core Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        required = {
            'salesapp_receipt', 'salesapp_saleitem', 'salesapp_inventoryitem',
            'salesapp_purchaseinvoice', 'salesapp_branch', 'salesapp_salesperson',
            'salesapp_companysetting', 'salesapp_clientlicense'
        }
        self.assertTrue(required.issubset(tables))

        # 3. Check Demo License uses DEMO_MACHINE
        cursor.execute("SELECT machine_id, invoices_balance FROM salesapp_clientlicense")
        lic_row = cursor.fetchone()
        self.assertIsNotNone(lic_row)
        self.assertEqual(lic_row[0], "DEMO_MACHINE")
        self.assertGreater(lic_row[1], 1000)

        # 4. Check Receipts Count and Cryptographic Signatures
        cursor.execute("SELECT id, receipt_number, total_amount, sale_month, sale_year, receipt_hash, is_cash_sale FROM salesapp_receipt ORDER BY receipt_number")
        receipt_rows = cursor.fetchall()
        self.assertEqual(len(receipt_rows), 3)

        for r_id, r_num, tot_amt, m, y, r_hash, is_cash in receipt_rows:
            # Deterministically verify signature
            expected_hash = generate_receipt_signature(r_num, int(float(tot_amt)), m, y, items_data=None)
            self.assertEqual(r_hash, expected_hash, f"Receipt #{r_num} signature mismatch")

        # 5. Check Installments (Receipt 101: 15000 total - 3000 down = 12000 remaining, 1000*12)
        r101_id = receipt_rows[0][0]
        cursor.execute("SELECT payment_date, amount FROM salesapp_installmentpayment WHERE receipt_id = ? ORDER BY payment_date", (r101_id,))
        inst_rows = cursor.fetchall()
        self.assertEqual(len(inst_rows), 12)
        # Verify 25th convention
        for p_date, amt in inst_rows:
            self.assertTrue(p_date.endswith("-25"), f"Installment date {p_date} must end with -25")
            self.assertEqual(int(float(amt)), 1000)

        # Receipt 102: Cash sale, 0 installments
        r102_id = receipt_rows[1][0]
        cursor.execute("SELECT COUNT(*) FROM salesapp_installmentpayment WHERE receipt_id = ?", (r102_id,))
        self.assertEqual(cursor.fetchone()[0], 0)

        # Receipt 103: Multi-system (1000*10 + 800*10 = 18000 remaining)
        r103_id = receipt_rows[2][0]
        cursor.execute("SELECT payment_date, amount FROM salesapp_installmentpayment WHERE receipt_id = ? ORDER BY payment_date", (r103_id,))
        inst103_rows = cursor.fetchall()
        self.assertEqual(len(inst103_rows), 20)
        self.assertEqual(int(float(inst103_rows[0][1])), 1000)
        self.assertEqual(int(float(inst103_rows[10][1])), 800)

        conn.close()

    def test_build_sqlite_backup_from_csv(self):
        """
        Verify CSV parsing with Arabic column headers.
        """
        csv_content = """رقم الوصل,اسم العميل,الهاتف,العنوان,المنطقة,المندوب,الأصناف,الإجمالي,المقدم,نظام القسط,التاريخ
501,سعد عبد المنعم,01055566677,الشارع التجاري,برقين,محمود علي,بطانية ترند + لحاف,4500,500,400*10,2026/02/01
502,فاطمة السيد,01122334455,طريق المحطة,البلامون,أحمد السيد,طقم صواني جرانيت,3000,3000,,2026/02/15
"""
        with open(self.sample_csv_path, "w", encoding="utf-8-sig") as f:
            f.write(csv_content)

        csv_out_path = os.path.join(self.temp_dir, "csv_output.sqlite3")
        build_backup(
            input_path=self.sample_csv_path,
            output_path=csv_out_path,
            branch_name="الفرع الرئيسي"
        )

        conn = sqlite3.connect(csv_out_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM salesapp_receipt")
        self.assertEqual(cursor.fetchone()[0], 2)

        cursor.execute("SELECT COUNT(*) FROM salesapp_installmentpayment")
        self.assertEqual(cursor.fetchone()[0], 10)  # 10 installments for receipt 501
        conn.close()

    def test_upload_generated_backup_to_backend(self):
        """
        Verify that the generated .sqlite3 backup file cleanly uploads and restores through
        BackupUploadView (POST /api/v1/tools/backup/upload/) with zero schema or migration errors.
        """
        build_backup(
            input_path=self.sample_json_path,
            output_path=self.output_db_path,
            branch_name="الفرع الرئيسي"
        )

        with open(self.output_db_path, "rb") as f:
            uploaded_file = SimpleUploadedFile("test_restore.sqlite3", f.read(), content_type="application/x-sqlite3")

        response = self.client.post("/api/v1/tools/backup/upload/", {
            "backup_file": uploaded_file
        }, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be either 'success' or 'pending_restart'
        self.assertIn(response.data.get("status"), ["success", "pending_restart"])
