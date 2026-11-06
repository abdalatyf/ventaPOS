import io
import os
import sqlite3
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Branch,
    Salesperson,
    InventoryItem,
    Receipt,
    SaleItem,
    ClientLicense,
    CompanySetting,
)
from api.utils.security_utils import (
    get_machine_id,
    generate_record_signature,
)


class BackupsAndSyncTests(TestCase):
    """
    Automated test suite for Backup and USB Sync subsystems:
    1. BackupDownloadView returns a valid SQLite binary stream.
    2. BackupUploadView validates extensions, integrity, required schema tables,
       creates pre-restore safety backups, and restores cleanly in isolation.
    3. Offline USB Sync lifecycle: export item catalog, import unconfirmed receipts
       (verifying zero stock deduction while pending), list pending receipts, and approve
       pending receipts (verifying sequential receipt numbering, HMAC signature, and stock deduction).
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"is_superuser": True}
        )
        self.client.force_authenticate(user=self.admin_user)

        self.branch = Branch.objects.create(name="الفرع التجريبي للمزامنة")
        self.salesperson = Salesperson.objects.create(
            branch=self.branch, name="مندوب الرحلات الميدانية"
        )
        self.company_setting = CompanySetting.objects.create(
            name="شركة المزامنة",
            phone1="01000000000",
            collection_commission_rate=0.10,
        )

        self.mach_id = get_machine_id()
        expiry = date.today() + timezone.timedelta(days=365)
        sig = generate_record_signature(str(expiry), 500, self.mach_id, 1, True)
        self.license = ClientLicense.objects.create(
            company_code=1001,
            product_id=1,
            start_date=date(2026, 1, 1),
            expiry_date=expiry,
            invoices_balance=500,
            is_active=True,
            machine_id=self.mach_id,
            license_code_hash=sig,
        )
        self.client.credentials(HTTP_X_COMPANY_CODE="TESTSYNC")

    def _create_sqlite_db_file(self, file_path, include_schema=True):
        """Helper to create a standalone SQLite database file."""
        conn = sqlite3.connect(file_path)
        cur = conn.cursor()
        if include_schema:
            cur.execute("CREATE TABLE salesapp_branch (id INTEGER PRIMARY KEY, name TEXT);")
            cur.execute("CREATE TABLE salesapp_inventoryitem (id INTEGER PRIMARY KEY, name TEXT);")
            cur.execute("CREATE TABLE salesapp_receipt (id INTEGER PRIMARY KEY, total_amount REAL);")
            cur.execute("CREATE TABLE salesapp_saleitem (id INTEGER PRIMARY KEY, quantity INTEGER);")
            cur.execute("CREATE TABLE salesapp_purchaseinvoice (id INTEGER PRIMARY KEY, invoice_number TEXT);")
            cur.execute("CREATE TABLE salesapp_purchaseinvoiceitem (id INTEGER PRIMARY KEY, quantity INTEGER);")
            cur.execute("CREATE TABLE salesapp_salesperson (id INTEGER PRIMARY KEY, name TEXT);")
            cur.execute("CREATE TABLE salesapp_companysetting (id INTEGER PRIMARY KEY, name TEXT);")
            cur.execute("CREATE TABLE salesapp_clientlicense (id INTEGER PRIMARY KEY, is_active INTEGER);")
        else:
            cur.execute("CREATE TABLE irrelevant_table (id INTEGER PRIMARY KEY, data TEXT);")
        conn.commit()
        conn.close()

    def test_backup_download_returns_valid_sqlite_stream(self):
        """
        Verify that BackupDownloadView creates a valid SQLite backup and returns
        a streaming FileResponse containing SQLite magic bytes.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db = Path(temp_dir) / "test_active.sqlite3"
            self._create_sqlite_db_file(temp_db, include_schema=True)

            with unittest.mock.patch.dict(settings.DATABASES["default"], {"NAME": str(temp_db)}):
                res = self.client.get("/api/v1/tools/backup/download/")
                self.assertEqual(res.status_code, status.HTTP_200_OK)

                content = b"".join(res.streaming_content) if res.streaming else res.content
                # First 16 bytes of any valid SQLite database must be 'SQLite format 3\x00'
                self.assertTrue(content.startswith(b"SQLite format 3\x00"))

    def test_backup_upload_validation_and_isolated_restore(self):
        """
        Verify that BackupUploadView:
        - Rejects files with invalid extensions.
        - Rejects corrupted/non-SQLite files.
        - Rejects SQLite files missing mandatory salesapp_* tables.
        - Creates a pre_restore safety backup in the backups/ folder.
        - Safely completes the restore without mutating test environment state.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db = Path(temp_dir) / "live_db.sqlite3"
            self._create_sqlite_db_file(temp_db, include_schema=True)

            with unittest.mock.patch.dict(settings.DATABASES["default"], {"NAME": str(temp_db)}), \
                 unittest.mock.patch("django.db.connections.close_all"), \
                 unittest.mock.patch("django.core.management.call_command"):

                # 1. Invalid file extension (.txt)
                invalid_ext_file = SimpleUploadedFile("backup.txt", b"plain text", content_type="text/plain")
                res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": invalid_ext_file})
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("امتداد الملف غير مدعوم", res.json()["error"])

                # 2. Corrupted file (invalid SQLite binary)
                corrupt_file = SimpleUploadedFile("corrupt.sqlite3", b"this is not sqlite", content_type="application/octet-stream")
                res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": corrupt_file})
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(any(k in res.json()["error"] for k in ["تالف", "غير صالح", "فحص النسخة"]))

                # 3. SQLite missing required salesapp_* tables
                missing_tables_path = Path(temp_dir) / "missing_tables.sqlite3"
                self._create_sqlite_db_file(missing_tables_path, include_schema=False)
                with open(missing_tables_path, "rb") as f:
                    missing_file = SimpleUploadedFile("missing.sqlite3", f.read(), content_type="application/octet-stream")
                res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": missing_file})
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("جداول مفقودة", res.json()["error"])

                # 4. Valid backup file
                valid_backup_path = Path(temp_dir) / "valid_incoming.sqlite3"
                self._create_sqlite_db_file(valid_backup_path, include_schema=True)
                with open(valid_backup_path, "rb") as f:
                    valid_file = SimpleUploadedFile("valid_incoming.sqlite3", f.read(), content_type="application/octet-stream")

                res = self.client.post("/api/v1/tools/backup/upload/", {"backup_file": valid_file})
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                self.assertEqual(res.json()["status"], "success")

                # Verify that pre-restore snapshot was generated in backups directory
                backups_dir = temp_db.parent / "backups"
                self.assertTrue(backups_dir.exists())
                snapshots = list(backups_dir.glob("pre_restore_*.sqlite3"))
                self.assertGreaterEqual(len(snapshots), 1)

    @unittest.skip("USB Sync disabled for now (P2-4.1)")
    def test_usb_sync_full_lifecycle(self):
        """
        Verify USB Sync workflow:
        1. OfflineExportItemsView returns branch catalog.
        2. OfflineImportReceiptsView accepts unconfirmed receipts (is_confirmed=False).
        3. Physical stock is NOT deducted while receipts remain unconfirmed.
        4. PendingReceiptsListView returns the unconfirmed receipts.
        5. ApprovePendingReceiptView validates limits, assigns receipt_number,
           generates receipt_hash, and deducts physical inventory and license balance.
        6. Re-approving the same receipt returns 400 Bad Request.
        """
        item = InventoryItem.objects.create(
            branch=self.branch,
            name="شاشة 43 بوصة سمارت",
            initial_quantity=10,
            initial_purchase_price=3000,
            initial_commission_amount=80,
            initial_month=1,
            initial_year=2026,
        )

        # 1. Export catalog for salesperson
        exp_res = self.client.get(
            f"/api/v1/tools/sync/export-items/?salesperson_id={self.salesperson.id}",
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(exp_res.status_code, status.HTTP_200_OK)
        catalog = exp_res.json()
        self.assertEqual(catalog["branch_id"], self.branch.id)
        self.assertEqual(catalog["salesperson_id"], self.salesperson.id)
        self.assertEqual(len(catalog["items"]), 1)
        self.assertEqual(catalog["items"][0]["id"], item.id)

        # Initial stock is 10
        self.assertEqual(item.get_stock_at_date(1, 2026), 10)

        # 2. Import offline receipts via USB sync payload
        import_payload = [
            {
                "branch": self.branch.id,
                "salesperson": self.salesperson.id,
                "customer_name": "عميل متجول",
                "sale_month": 1,
                "sale_year": 2026,
                "is_cash_sale": True,
                "total_amount": 4000,
                "down_payment": 4000,
                "items": [
                    {
                        "inventory_item_id": item.id,
                        "quantity": 2,
                        "unit_price": 2000,
                    }
                ],
            }
        ]

        imp_res = self.client.post(
            "/api/v1/tools/sync/import-receipts/",
            import_payload,
            format="json",
        )
        self.assertEqual(imp_res.status_code, status.HTTP_200_OK)

        # Find the newly imported receipt
        imported_receipt = Receipt.objects.filter(customer_name="عميل متجول").first()
        self.assertIsNotNone(imported_receipt)
        self.assertFalse(imported_receipt.is_confirmed)
        self.assertIsNone(imported_receipt.receipt_number)

        # 3. CRITICAL: Unconfirmed receipt MUST NOT deduct physical stock!
        self.assertEqual(item.get_stock_at_date(1, 2026), 10)

        # 4. Check PendingReceiptsListView
        pending_res = self.client.get(
            "/api/v1/tools/sync/pending-receipts/",
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(pending_res.status_code, status.HTTP_200_OK)
        pending_list = pending_res.json()
        self.assertTrue(any(p["id"] == imported_receipt.id for p in pending_list))

        # Check initial license balance
        self.license.refresh_from_db()
        initial_balance = self.license.invoices_balance

        # 5. Approve pending receipt
        approve_res = self.client.post(
            f"/api/v1/tools/sync/approve-pending/{imported_receipt.id}/",
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)

        # Verify receipt after approval
        imported_receipt.refresh_from_db()
        self.assertTrue(imported_receipt.is_confirmed)
        self.assertIsNotNone(imported_receipt.receipt_number)
        self.assertTrue(len(imported_receipt.receipt_hash) > 0)

        # Physical stock is now deducted: 10 - 2 = 8
        self.assertEqual(item.get_stock_at_date(1, 2026), 8)

        # License balance is decremented
        self.license.refresh_from_db()
        self.assertEqual(self.license.invoices_balance, initial_balance - 1)

        # 6. Re-approval attempt must be rejected with 400
        dup_approve_res = self.client.post(
            f"/api/v1/tools/sync/approve-pending/{imported_receipt.id}/",
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(dup_approve_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("تم اعتماد هذه الفاتورة مسبقاً", dup_approve_res.json()["error"])
