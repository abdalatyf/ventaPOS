"""
Tests for Batch V1-5 in VentaPOS NextGen:
- Item 13: uac_admin and packaging configurations.
- Item 14: Release version 1.0.0 and SPA catch-all exclusions.
- Items 15 & 16: Auto-Updater endpoints (check-update and apply-update).
"""
import io
import json
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status


class BatchV15SystemUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @override_settings(APP_VERSION="1.0.0", RELEASES_MANIFEST_URL="https://raw.githubusercontent.com/venta-pos/releases/main/version.json")
    @patch('urllib.request.urlopen')
    def test_check_update_newer_version_available(self, mock_urlopen):
        remote_manifest = {
            "version": "1.0.1",
            "release_date": "2026-11-10",
            "release_notes": "تحسينات جديدة وسرعة أعلى.",
            "download_url": "https://github.com/venta-pos/releases/releases/download/v1.0.1/VentaPOS_Setup_v1.0.1.exe",
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(remote_manifest).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        response = self.client.get('/api/v1/system/check-update/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["current_version"], "1.0.0")
        self.assertEqual(data["latest_version"], "1.0.1")
        self.assertTrue(data["has_update"])
        self.assertFalse(data["offline"])
        self.assertEqual(data["download_url"], remote_manifest["download_url"])

    @override_settings(APP_VERSION="1.0.0", RELEASES_MANIFEST_URL="https://raw.githubusercontent.com/venta-pos/releases/main/version.json")
    @patch('urllib.request.urlopen')
    def test_check_update_already_up_to_date(self, mock_urlopen):
        remote_manifest = {
            "version": "1.0.0",
            "release_date": "2026-11-06",
            "release_notes": "الإصدار الحالي v1.0.0",
            "download_url": "https://github.com/venta-pos/releases/releases/download/v1.0.0/VentaPOS_Setup_v1.0.0.exe",
            "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(remote_manifest).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        response = self.client.get('/api/v1/system/check-update/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["current_version"], "1.0.0")
        self.assertEqual(data["latest_version"], "1.0.0")
        self.assertFalse(data["has_update"])
        self.assertFalse(data["offline"])

    @override_settings(APP_VERSION="1.0.0")
    @patch('urllib.request.urlopen')
    def test_check_update_offline_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("DNS Resolution Failure")

        response = self.client.get('/api/v1/system/check-update/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["current_version"], "1.0.0")
        self.assertFalse(data["has_update"])
        self.assertTrue(data["offline"])

    def test_apply_update_missing_required_fields(self):
        # Missing download_url
        res1 = self.client.post('/api/v1/system/apply-update/', {
            "sha256": "abcdef"
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res1.data["error"], "missing_url")

        # Missing sha256
        res2 = self.client.post('/api/v1/system/apply-update/', {
            "download_url": "https://github.com/venta-pos/releases/releases/download/v1.0.1/setup.exe"
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res2.data["error"], "missing_sha256")

    def test_apply_update_untrusted_url_rejected(self):
        res = self.client.post('/api/v1/system/apply-update/', {
            "download_url": "https://malicious-site.com/payload.exe",
            "sha256": "abcdef123456"
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["error"], "untrusted_download_url")

    @patch('subprocess.Popen')
    @patch('urllib.request.urlopen')
    def test_apply_update_checksum_mismatch(self, mock_urlopen, mock_popen):
        fake_binary_bytes = b"MZ\x90\x00Dummy binary content"
        mock_resp = MagicMock()
        mock_resp.read.side_effect = [fake_binary_bytes, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        payload = {
            "download_url": "https://github.com/venta-pos/releases/releases/download/v1.0.1/VentaPOS_Setup_v1.0.1.exe",
            "sha256": "wrong_expected_checksum_00000000000000000000000000000000000000000000000",
            "version": "1.0.1"
        }
        res = self.client.post('/api/v1/system/apply-update/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["error"], "checksum_mismatch")
        mock_popen.assert_not_called()

    @patch('subprocess.Popen')
    @patch('urllib.request.urlopen')
    def test_apply_update_successful_execution(self, mock_urlopen, mock_popen):
        fake_binary_bytes = b"MZ\x90\x00Valid executable file data"
        valid_checksum = hashlib.sha256(fake_binary_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.read.side_effect = [fake_binary_bytes, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        payload = {
            "download_url": "https://github.com/venta-pos/releases/releases/download/v1.0.1/VentaPOS_Setup_v1.0.1.exe",
            "sha256": valid_checksum,
            "version": "1.0.1"
        }
        res = self.client.post('/api/v1/system/apply-update/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "success")
        mock_popen.assert_called_once()


class BatchV15SPACatchAllExclusionsTests(TestCase):
    def setUp(self):
        self.django_client = Client()

    def test_static_and_media_routes_not_swallowed_by_spa_catch_all(self):
        # A request to missing /static/ file should return 404 (not match SPA TemplateView 200)
        res_static = self.django_client.get('/static/assets/non_existent_bundle.js')
        self.assertEqual(res_static.status_code, 404)

        # A request to missing /media/ file should return 404
        res_media = self.django_client.get('/media/non_existent_image.png')
        self.assertEqual(res_media.status_code, 404)

        # A request to unknown /api/ route should return 404, not match SPA TemplateView 200
        res_api = self.django_client.get('/api/v1/non_existent_endpoint/')
        self.assertEqual(res_api.status_code, 404)

        # A standard SPA client route like /dimensions should match TemplateView and return 200
        res_spa = self.django_client.get('/dimensions')
        self.assertEqual(res_spa.status_code, 200)


class BatchV15FrontendLogsAndMiddlewareTests(TestCase):
    def setUp(self):
        self.django_client = Client()

    def test_frontend_logs_endpoint_list(self):
        payload = {
            "logs": [
                {"level": "INFO", "message": "User navigated to /pos", "url": "/pos"},
                {"level": "WARN", "message": "Slow network response", "details": "500ms", "url": "/pos"},
            ]
        }
        res = self.django_client.post('/api/v1/frontend-logs/', payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "success")

    def test_frontend_logs_endpoint_single_object(self):
        payload = {
            "level": "ERROR",
            "message": "Uncaught Error: Test error",
            "details": "Error at main.jsx:10",
            "url": "/receipts"
        }
        res = self.django_client.post('/api/v1/frontend-logs/', payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "success")

    def test_frontend_logs_endpoint_empty_payload(self):
        res = self.django_client.post('/api/v1/frontend-logs/', {}, content_type='application/json')
        self.assertEqual(res.status_code, 400)
