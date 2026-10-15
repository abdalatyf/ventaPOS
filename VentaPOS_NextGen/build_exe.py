import os
import sys
import subprocess
import shutil
import PyInstaller.__main__
from pathlib import Path

def build_frontend(base_dir):
    frontend_dir = os.path.join(base_dir, 'frontend')
    print(f"Building frontend in {frontend_dir}...")
    
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    
    try:
        result = subprocess.run([npm_cmd, 'run', 'build'], cwd=frontend_dir, check=True, text=True)
        print("Frontend build completed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error building frontend! Aborting executable build.")
        sys.exit(1)

def build():
    base_dir = Path(__file__).resolve().parent
    
    # Step 1: Build the frontend
    build_frontend(base_dir)

    # Step 2: Clean old build
    dist_dir = base_dir / 'dist'
    if dist_dir.exists():
        print("Cleaning old dist directory...")
        shutil.rmtree(dist_dir, ignore_errors=True)

    backend_dir = base_dir / 'backend'
    launcher_script = base_dir / 'launcher.py'
    
    # Expose settings to PyInstaller's Django hook
    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
    os.environ['PYTHONPATH'] = str(backend_dir)
    sys.path.insert(0, str(backend_dir))
    
    PyInstaller.__main__.run([
        str(launcher_script),
        '--name=VentaPOS',
        '--windowed',
        '--onedir',
        f'--paths={backend_dir}',
        f'--add-data={backend_dir};backend',
        f'--add-data={base_dir / "frontend" / "dist"};frontend/dist',
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
        '--hidden-import=rest_framework',
        '--hidden-import=rest_framework.authtoken',
        '--hidden-import=rest_framework.authentication',
        '--hidden-import=rest_framework.parsers',
        '--hidden-import=rest_framework.renderers',
        '--hidden-import=rest_framework.negotiation',
        '--hidden-import=rest_framework.metadata',
        '--hidden-import=corsheaders',
        '--hidden-import=corsheaders.middleware',
        '--hidden-import=whitenoise',
        '--hidden-import=whitenoise.middleware',
        '--hidden-import=api',
        '--hidden-import=api.apps',
        '--hidden-import=api.urls',
        '--hidden-import=api.middleware',
        '--hidden-import=backend.urls',
        '--collect-submodules=django',
        '--collect-submodules=rest_framework',
        '--collect-submodules=corsheaders',
        '--collect-submodules=whitenoise',
        '--noconfirm'
    ])

if __name__ == '__main__':
    build()
