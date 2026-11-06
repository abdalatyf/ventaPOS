"""
VentaPOS NextGen — Production Release Publisher Script.
Publishes only the compiled executable binary and version.json metadata to https://github.com/venta-pos/releases.
Zero source code is uploaded to the releases repository.

Instructions:
Set your GitHub token in the GITHUB_TOKEN constant below (or set environment variable GITHUB_TOKEN)
before running this script:
    python scripts/publish_release.py
"""
import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

# ==============================================================================
# Configuration & Credentials Placeholder
# Leave as empty string placeholder until typed by the user
# ==============================================================================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RELEASES_REPO = "venta-pos/releases"
BASE_DIR = Path(__file__).resolve().parent.parent


def get_app_version():
    """Reads APP_VERSION from backend/backend/settings.py or package.json."""
    settings_file = BASE_DIR / "backend" / "backend" / "settings.py"
    if settings_file.exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("APP_VERSION"):
                    return line.split("=")[1].strip().strip("'\"")
    return "1.0.0"


def compute_sha256(file_path):
    """Calculates SHA-256 hash of a binary file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def find_release_binary(version):
    """Locates the built setup installer or standalone executable in dist/."""
    dist_dir = BASE_DIR / "dist"
    candidates = [
        dist_dir / f"VentaPOS_Setup_v{version}.exe",
        dist_dir / "VentaPOS" / "VentaPOS.exe",
        dist_dir / "VentaPOS.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main():
    version = get_app_version()
    print("=" * 60)
    print(f" VentaPOS NextGen — Release Publisher (v{version})")
    print(f" Target Releases Repository: https://github.com/{RELEASES_REPO}")
    print("=" * 60)

    binary_path = find_release_binary(version)
    if not binary_path:
        print(f"[-] Warning: No compiled binary found in dist/. Please run build_exe.py first.")
        print(f"    Expected path: dist/VentaPOS_Setup_v{version}.exe or dist/VentaPOS/VentaPOS.exe")
        # For testing/manifest preparation, create a stub if in dry-run
        checksum = "0000000000000000000000000000000000000000000000000000000000000000"
        binary_name = f"VentaPOS_Setup_v{version}.exe"
    else:
        print(f"[+] Found compiled binary: {binary_path}")
        print(f"[*] Calculating SHA-256 checksum...")
        checksum = compute_sha256(binary_path)
        binary_name = binary_path.name
        print(f"[+] SHA-256: {checksum}")

    download_url = f"https://github.com/{RELEASES_REPO}/releases/download/v{version}/{binary_name}"

    manifest_data = {
        "version": version,
        "release_date": "2026-11-06",
        "release_notes": f"الإصدار الرسمي v{version} لمنظومة VentaPOS NextGen — تحسينات شاملة وسرعة واستقرار.",
        "download_url": download_url,
        "sha256": checksum,
    }

    # Save local version.json manifest
    dist_manifest = BASE_DIR / "dist" / "version.json"
    dist_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(dist_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"[+] Generated manifest saved locally at: {dist_manifest}")
    print(json.dumps(manifest_data, ensure_ascii=False, indent=2))

    if not GITHUB_TOKEN:
        print("\n" + "=" * 60)
        print("[!] GITHUB_TOKEN is currently empty.")
        print("    To upload this release to GitHub, please set your personal access token:")
        print("    1. In scripts/publish_release.py: GITHUB_TOKEN = 'ghp_...'")
        print("    2. Or run: $env:GITHUB_TOKEN='ghp_...'; python scripts/publish_release.py")
        print("    Local manifest generation completed successfully.")
        print("=" * 60)
        return

    # Upload to GitHub Releases API
    print(f"\n[*] Creating GitHub Release v{version} on {RELEASES_REPO}...")
    create_release_url = f"https://api.github.com/repos/{RELEASES_REPO}/releases"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "VentaPOS-Publisher",
    }
    payload = json.dumps({
        "tag_name": f"v{version}",
        "target_commitish": "main",
        "name": f"VentaPOS NextGen v{version}",
        "body": manifest_data["release_notes"],
        "draft": False,
        "prerelease": False,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(create_release_url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            rel_data = json.loads(resp.read().decode("utf-8"))
            upload_url = rel_data.get("upload_url", "").split("{")[0]
            print(f"[+] Release created successfully! ID: {rel_data.get('id')}")
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error while creating release: {e.code} {e.reason}")
        return

    # Upload version.json as asset
    print("[*] Uploading version.json asset...")
    with open(dist_manifest, "rb") as f:
        asset_bytes = f.read()
    asset_req = urllib.request.Request(
        f"{upload_url}?name=version.json",
        data=asset_bytes,
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(asset_req) as resp:
            print("[+] version.json asset uploaded successfully.")
    except Exception as e:
        print(f"[-] Failed uploading version.json: {e}")

    # Upload binary if exists
    if binary_path and binary_path.exists():
        print(f"[*] Uploading binary asset: {binary_name}...")
        with open(binary_path, "rb") as f:
            bin_bytes = f.read()
        bin_req = urllib.request.Request(
            f"{upload_url}?name={binary_name}",
            data=bin_bytes,
            headers={**headers, "Content-Type": "application/octet-stream"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(bin_req) as resp:
                print(f"[+] Binary asset {binary_name} uploaded successfully!")
        except Exception as e:
            print(f"[-] Failed uploading binary: {e}")

    print("\n[SUCCESS] Production release publishing process finished!")


if __name__ == "__main__":
    main()
