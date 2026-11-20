# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

spec_root = Path(SPECPATH).resolve()
icon_path = spec_root / 'assets' / 'venta.ico'


def collect_app_datas(app_dir: Path, bundle_prefix: str):
    """Collect clean Django app files without caches, local SQLite DBs, logs, or tests."""
    excluded_dirs = {'__pycache__'}
    excluded_suffixes = ('.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.sqlite3-journal', '.log', '.pyc', '.pyo')
    excluded_names = {'tests.py'}

    collected = []
    for current_root, dirs, files in os.walk(app_dir):
        current_path = Path(current_root)
        rel_dir = current_path.relative_to(app_dir)
        is_top = rel_dir == Path('.')

        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        dest_dir = bundle_prefix if is_top else f"{bundle_prefix}/{rel_dir.as_posix()}"

        for filename in files:
            lower_name = filename.lower()
            if (
                lower_name in excluded_names
                or lower_name.startswith('db.sqlite3')
                or lower_name.endswith(excluded_suffixes)
            ):
                continue
            collected.append((str(current_path / filename), dest_dir))
    return collected


hiddenimports = [
    'django', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'waitress', 'webview', 'requests', 'certifi', 'tzdata', 'zoneinfo',
    'licenses', 'licenses.apps', 'licenses.models', 'licenses.views',
    'licenses.forms', 'licenses.middleware', 'licenses.utils.crypto',
    'core.urls', 'core.wsgi',
]
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('waitress')
hiddenimports += collect_submodules('licenses', filter=lambda name: name != 'licenses.tests')
hiddenimports += collect_submodules('core')

datas = []
datas += collect_app_datas(spec_root / 'core', 'core')
datas += collect_app_datas(spec_root / 'licenses', 'licenses')
datas += collect_data_files('tzdata')
datas += collect_data_files('certifi')

excludes = ['numpy', 'scipy', 'pandas', 'matplotlib', 'tkinter', '_tkinter', 'pytest']

a = Analysis(
    [str(spec_root / 'launcher.py')],
    pathex=[str(spec_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)


def _is_forbidden_data(entry):
    dest_name = Path(entry[0]).name.lower()
    src_lower = entry[1].lower()
    dest_lower = entry[0].lower()
    return (
        dest_name.startswith('db.sqlite3')
        or src_lower.endswith(('.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.sqlite3-journal', '.db', '.log'))
        or dest_lower.endswith(('.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.sqlite3-journal', '.db', '.log'))
    )


a.datas = [entry for entry in a.datas if not _is_forbidden_data(entry)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VentaPOS_LicenseManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VentaPOS_LicenseManager',
)
