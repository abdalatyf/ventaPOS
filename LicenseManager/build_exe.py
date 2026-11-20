import os
import shutil
import sys
from pathlib import Path
import PyInstaller.__main__


def build():
    base_dir = Path(__file__).resolve().parent
    spec_file = base_dir / 'VentaPOS_LicenseManager.spec'
    if not spec_file.exists():
        print(f"Error: Spec file not found at {spec_file}")
        sys.exit(1)

    # Clean old dist and build directories
    for folder_name in ('dist', 'build'):
        target_dir = base_dir / folder_name
        if target_dir.exists():
            print(f"Cleaning old {folder_name} directory...")
            shutil.rmtree(target_dir, ignore_errors=True)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    os.environ['PYTHONPATH'] = str(base_dir)
    sys.path.insert(0, str(base_dir))

    print(f"Running PyInstaller for LicenseManager using {spec_file}...")
    PyInstaller.__main__.run([str(spec_file), '--noconfirm', '--clean'])


if __name__ == '__main__':
    build()
