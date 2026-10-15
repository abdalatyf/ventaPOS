# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['django', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware', 'rest_framework', 'rest_framework.authtoken', 'rest_framework.authentication', 'rest_framework.parsers', 'rest_framework.renderers', 'rest_framework.negotiation', 'rest_framework.metadata', 'corsheaders', 'corsheaders.middleware', 'whitenoise', 'whitenoise.middleware', 'api', 'api.apps', 'api.urls', 'api.middleware', 'backend.urls']
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('rest_framework')
hiddenimports += collect_submodules('corsheaders')
hiddenimports += collect_submodules('whitenoise')


a = Analysis(
    ['D:/Projects/VentaPOS/VentaPOS_NextGen/launcher.py'],
    pathex=['D:/Projects/VentaPOS/VentaPOS_NextGen/backend'],
    binaries=[],
    datas=[('D:/Projects/VentaPOS/VentaPOS_NextGen/backend', 'backend'), ('D:/Projects/VentaPOS/VentaPOS_NextGen/frontend/dist', 'frontend/dist')],
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
