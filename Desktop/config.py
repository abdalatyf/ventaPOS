import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, 'version.txt')
SPEC_FILE = os.path.join(BASE_DIR, 'VentaPOS.spec')
DIST_DIR = os.path.join(BASE_DIR, 'dist', 'VentaPOS')

WORKSPACE_DIR = os.path.join(BASE_DIR, 'Venta_Workspace')
RELEASES_DIR = os.path.join(WORKSPACE_DIR, 'Releases')
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, 'Archive')
FULL_SETUP_ISS = os.path.join(WORKSPACE_DIR, 'Venta_App_Setup.iss')

ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"