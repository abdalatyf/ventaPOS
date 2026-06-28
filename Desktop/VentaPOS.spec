# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['sales\\run_app.py'], # 🔴 التوجيه لمجلد sales
    pathex=['sales'],      # 🔴 إضافة sales كمسار بحث
    datas=[
        ('sales\\salesapp\\templates', 'salesapp/templates'), 
        ('sales\\staticfiles', 'staticfiles'), 
        ('sales\\bin\\wkhtmltox', 'bin/wkhtmltox'),
        ('sales\\bin\\SumatraPDF.exe', 'bin'),
        ('sales\\bin\\SumatraPDF-settings.txt', 'bin')
    ],
    hiddenimports=[
        'webview', 
        'waitress', 
        'whitenoise', 
        'whitenoise.middleware', 
        'django.contrib.humanize.templatetags.humanize', 
        'salesapp.apps', 
        'salesapp.db_router',
        'num2words',  
        'dateutil',   
        'pandas',     
        'openpyxl',   
    ],
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
    uac_admin=True,
    icon=['venta.ico'], # 🔴 الأيقونة موجودة في المجلد الجذري الآن
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