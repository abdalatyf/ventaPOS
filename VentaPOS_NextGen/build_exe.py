import os
import shutil
import subprocess
import sys
from pathlib import Path
import PyInstaller.__main__


def build_frontend(base_dir: Path):
    frontend_dir = base_dir / 'frontend'
    print(f"Building frontend in {frontend_dir}...")

    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'

    try:
        subprocess.run([npm_cmd, 'run', 'build'], cwd=str(frontend_dir), check=True, text=True)
        print("Frontend build completed successfully.")
    except subprocess.CalledProcessError:
        print("Error building frontend! Aborting executable build.")
        sys.exit(1)


def build():
    base_dir = Path(__file__).resolve().parent

    # Step 1: Build the frontend
    build_frontend(base_dir)

    # Step 2: Clean old dist and build directories
    for folder_name in ('dist', 'build'):
        target_dir = base_dir / folder_name
        if target_dir.exists():
            print(f"Cleaning old {folder_name} directory...")
            shutil.rmtree(target_dir, ignore_errors=True)

    backend_dir = base_dir / 'backend'
    spec_file = base_dir / 'VentaPOS.spec'
    if not spec_file.exists():
        print(f"Error: Spec file not found at {spec_file}")
        sys.exit(1)

    # Expose settings to PyInstaller's Django hook without modifying VentaPOS.spec
    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
    os.environ['PYTHONPATH'] = str(backend_dir)
    sys.path.insert(0, str(backend_dir))

    print(f"Running PyInstaller against portable spec: {spec_file}")
    PyInstaller.__main__.run([str(spec_file), '--noconfirm', '--clean'])


if __name__ == '__main__':
    build()
