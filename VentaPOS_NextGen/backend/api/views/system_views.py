"""
System & Auto-Update Views for VentaPOS NextGen.
Handles update checking against GitHub releases manifest and downloading/installing verified update binaries.
"""
import os
import sys
import json
import hashlib
import tempfile
import urllib.request
import subprocess
import time
import threading
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


def parse_semver(ver_str):
    """
    Parses a version string (e.g. '1.0.0', 'v1.2.3') into a tuple of ints for semantic comparison.
    """
    clean = str(ver_str).strip().lstrip('v')
    parts = []
    for token in clean.split('.'):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


class SystemCheckUpdateView(APIView):
    """
    GET /api/v1/system/check-update/
    Fetches the latest version.json from the public releases repo and checks for updates.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        current_version = getattr(settings, 'APP_VERSION', '1.0.0')
        manifest_url = getattr(
            settings,
            'RELEASES_MANIFEST_URL',
            'https://raw.githubusercontent.com/venta-pos/releases/main/version.json'
        )

        try:
            req = urllib.request.Request(
                manifest_url,
                headers={'User-Agent': f'VentaPOS-Desktop/{current_version}'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get('version', current_version)
                    has_update = parse_semver(latest_version) > parse_semver(current_version)

                    return Response({
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "has_update": has_update,
                        "release_notes": data.get('release_notes', ''),
                        "download_url": data.get('download_url', ''),
                        "sha256": data.get('sha256', ''),
                        "release_date": data.get('release_date', ''),
                        "offline": False
                    }, status=status.HTTP_200_OK)
        except Exception:
            # Gracefully handle network outage or unreachable manifest
            pass

        return Response({
            "current_version": current_version,
            "latest_version": current_version,
            "has_update": False,
            "release_notes": "",
            "download_url": "",
            "sha256": "",
            "release_date": "",
            "offline": True
        }, status=status.HTTP_200_OK)


class SystemApplyUpdateView(APIView):
    """
    POST /api/v1/system/apply-update/
    Validates, downloads, verifies SHA-256 checksum, and launches the update installer package.
    """
    permission_classes = [AllowAny]

    ALLOWED_PREFIXES = (
        'https://github.com/venta-pos/releases/',
        'https://raw.githubusercontent.com/venta-pos/releases/',
    )

    def post(self, request):
        download_url = request.data.get('download_url', '').strip()
        expected_sha256 = request.data.get('sha256', '').strip().lower()
        version_label = request.data.get('version', 'latest').strip().lstrip('v')

        if not download_url:
            return Response(
                {"error": "missing_url", "message": "رابط التحميل مطلوب."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not expected_sha256:
            return Response(
                {"error": "missing_sha256", "message": "بصمة التحقق SHA-256 مطلوبة."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Security check: must originate from trusted repository
        if not any(download_url.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
            return Response(
                {"error": "untrusted_download_url", "message": "رابط التحميل غير موثوق. يجب أن يكون من مستودع التحديثات الرسمي."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_dir = Path(tempfile.gettempdir()) / "VentaPOS_Update"
        target_dir.mkdir(parents=True, exist_ok=True)
        installer_file = target_dir / f"VentaPOS_Setup_v{version_label}.exe"

        # Download and compute checksum
        hasher = hashlib.sha256()
        try:
            req = urllib.request.Request(
                download_url,
                headers={'User-Agent': 'VentaPOS-AutoUpdater'}
            )
            with urllib.request.urlopen(req, timeout=60) as resp, open(installer_file, 'wb') as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    f.write(chunk)
        except Exception as e:
            if installer_file.exists():
                try: installer_file.unlink()
                except Exception: pass
            return Response(
                {"error": "download_failed", "message": f"فشل تحميل ملف التحديث: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Checksum verification
        computed_sha256 = hasher.hexdigest().lower()
        if computed_sha256 != expected_sha256:
            if installer_file.exists():
                try: installer_file.unlink()
                except Exception: pass
            return Response(
                {"error": "checksum_mismatch", "message": "فشل التحقق الأمني من سلامة ملف التحديث (SHA-256 Mismatch). تم إلغاء التثبيت."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Launch the installer executable
        try:
            subprocess.Popen([str(installer_file)])
        except Exception as e:
            return Response(
                {"error": "launch_failed", "message": f"فشل تشغيل برنامج التثبيت: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # If running inside PyInstaller bundle, schedule application exit
        if getattr(sys, 'frozen', False):
            def _delayed_exit():
                time.sleep(1.0)
                os._exit(0)
            threading.Thread(target=_delayed_exit, daemon=True).start()

        return Response({
            "status": "success",
            "message": "تم تحميل وتأكيد ملف التحديث بنجاح، وجاري بدء التثبيت الآن.",
            "installer_path": str(installer_file)
        }, status=status.HTTP_200_OK)
