# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

spec_root = Path(SPECPATH).resolve()
backend_dir = spec_root / 'backend'
frontend_dist = spec_root / 'frontend' / 'dist'
bin_dir = backend_dir / 'bin'

hiddenimports = [
    'django', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 'rest_framework', 'rest_framework.authtoken',
    'rest_framework.authentication', 'rest_framework.parsers', 'rest_framework.renderers',
    'rest_framework.negotiation', 'rest_framework.metadata', 'corsheaders', 'corsheaders.middleware',
    'whitenoise', 'whitenoise.middleware', 'api', 'api.apps', 'api.urls', 'api.middleware', 'backend.urls'
]
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('rest_framework')
hiddenimports += collect_submodules('corsheaders')
hiddenimports += collect_submodules('whitenoise')
hiddenimports += collect_submodules('api')
hiddenimports += collect_submodules('api.views')
hiddenimports += collect_submodules('api.services')
hiddenimports += collect_submodules('api.utils')

datas = [
    (str(backend_dir), 'backend'),
    (str(frontend_dist), 'frontend/dist'),
]
if bin_dir.exists():
    datas.append((str(bin_dir), 'bin'))

a = Analysis(
    [str(spec_root / 'launcher.py')],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
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
