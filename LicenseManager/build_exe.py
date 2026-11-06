import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def build():
    base_dir = Path(__file__).resolve().parent
    launcher_script = base_dir / 'launcher.py'
    
    # Clean old dist directory
    dist_dir = base_dir / 'dist'
    if dist_dir.exists():
        print("Cleaning old dist directory...")
        shutil.rmtree(dist_dir, ignore_errors=True)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    os.environ['PYTHONPATH'] = str(base_dir)
    sys.path.insert(0, str(base_dir))

    args = [
        str(launcher_script),
        '--name=VentaPOS_LicenseManager',
        '--windowed',
        '--onedir',
        '--uac-admin',
        f'--paths={base_dir}',
        f'--add-data={base_dir / "core"};core',
        f'--add-data={base_dir / "licenses"};licenses',
        '--hidden-import=django',
        '--hidden-import=django.contrib.admin',
        '--hidden-import=django.contrib.auth',
        '--hidden-import=django.contrib.contenttypes',
        '--hidden-import=django.contrib.sessions',
        '--hidden-import=django.contrib.messages',
        '--hidden-import=django.contrib.staticfiles',
        '--hidden-import=django.middleware.security.SecurityMiddleware',
        '--hidden-import=django.contrib.sessions.middleware.SessionMiddleware',
        '--hidden-import=django.middleware.common.CommonMiddleware',
        '--hidden-import=django.middleware.csrf.CsrfViewMiddleware',
        '--hidden-import=django.contrib.auth.middleware.AuthenticationMiddleware',
        '--hidden-import=django.contrib.messages.middleware.MessageMiddleware',
        '--hidden-import=django.middleware.clickjacking.XFrameOptionsMiddleware',
        '--hidden-import=waitress',
        '--hidden-import=webview',
        '--hidden-import=requests',
        '--hidden-import=licenses',
        '--hidden-import=licenses.apps',
        '--hidden-import=licenses.models',
        '--hidden-import=licenses.views',
        '--hidden-import=licenses.forms',
        '--hidden-import=licenses.utils.crypto',
        '--hidden-import=core.urls',
        '--hidden-import=core.wsgi',
        '--collect-submodules=django',
        '--collect-submodules=waitress',
        '--collect-submodules=licenses',
        '--collect-submodules=core',
        '--noconfirm'
    ]

    print("Running PyInstaller for LicenseManager...")
    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    build()
