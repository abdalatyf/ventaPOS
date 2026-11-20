# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

spec_root = Path(SPECPATH).resolve()
backend_dir = spec_root / 'backend'
frontend_dist = spec_root / 'frontend' / 'dist'
bin_dir = backend_dir / 'bin'
icon_path = spec_root / 'assets' / 'venta.ico'


def collect_backend_datas(root_dir: Path):
    """Collect clean backend source and templates without runtime DB/logs/backups/tests/bin."""
    excluded_top_dirs = {'bin', 'backups', 'logs', 'media', 'db', '__pycache__', 'staticfiles'}
    excluded_any_dirs = {'__pycache__', 'tests'}
    excluded_suffixes = ('.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.sqlite3-journal', '.log', '.pyc', '.pyo')
    excluded_names = {'restore_pending.bin'}

    collected = []
    for current_root, dirs, files in os.walk(root_dir):
        current_path = Path(current_root)
        rel_dir = current_path.relative_to(root_dir)
        is_top = rel_dir == Path('.')

        dirs[:] = [
            d for d in dirs
            if d not in excluded_any_dirs and not (is_top and d in excluded_top_dirs)
        ]

        dest_dir = 'backend' if is_top else f"backend/{rel_dir.as_posix()}"
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
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 'rest_framework', 'rest_framework.authtoken',
    'rest_framework.authentication', 'rest_framework.parsers', 'rest_framework.renderers',
    'rest_framework.negotiation', 'rest_framework.metadata', 'corsheaders', 'corsheaders.middleware',
    'whitenoise', 'whitenoise.middleware', 'api', 'api.apps', 'api.urls', 'api.middleware', 'backend.urls',
    'tzdata', 'zoneinfo', 'certifi', 'num2words', 'pdfkit', 'waitress', 'webview',
    'dateutil', 'dateutil.relativedelta',
]
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('rest_framework')
hiddenimports += collect_submodules('corsheaders')
hiddenimports += collect_submodules('whitenoise')
hiddenimports += collect_submodules('api', filter=lambda name: not name.startswith('api.tests'))
hiddenimports += collect_submodules('api.views')
hiddenimports += collect_submodules('api.services')
hiddenimports += collect_submodules('api.utils')

datas = collect_backend_datas(backend_dir)
datas.append((str(frontend_dist), 'frontend/dist'))
if bin_dir.exists():
    datas.append((str(bin_dir), 'bin'))
datas += collect_data_files('tzdata')
datas += collect_data_files('certifi')

excludes = ['numpy', 'scipy', 'pandas', 'matplotlib', 'tkinter', '_tkinter', 'pytest']

a = Analysis(
    [str(spec_root / 'launcher.py')],
    pathex=[str(backend_dir)],
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
    name='VentaPOS',
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
    name='VentaPOS',
)
