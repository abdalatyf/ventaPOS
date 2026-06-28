import os
import subprocess
import shutil

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")
    backend_dir = os.path.join(base_dir, "backend")
    
    # Force rebuild React frontend
    print("Building React frontend...")
    frontend_dir = os.path.join(base_dir, "frontend")
    # Using shell=True for npm on Windows
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, check=True)
    
    # Copy build to Django static folder
    print("Copying React build to Django...")
    react_dist = os.path.join(frontend_dir, "dist")
    django_react_build = os.path.join(backend_dir, "react_build")
    
    if os.path.exists(django_react_build):
        shutil.rmtree(django_react_build)
    shutil.copytree(react_dist, django_react_build)
    
    # Package with PyInstaller
    print("Packaging with PyInstaller...")
    pyinstaller_path = os.path.join(base_dir, "venv312", "Scripts", "pyinstaller.exe")
    
    cmd = [
        pyinstaller_path,
        "--name=VentaPOS_Django_PoC_Tabler",
        "--onefile",
        "--windowed",
        f"--paths={backend_dir}",
        f"--add-data={django_react_build};react_build",
        f"--add-data={os.path.join(backend_dir, 'db.sqlite3')};.",
        "--hidden-import=backend.settings",
        "--hidden-import=backend.urls",
        "--hidden-import=backend.wsgi",
        "--hidden-import=api",
        "--hidden-import=api.apps",
        "--hidden-import=api.models",
        "--hidden-import=api.views",
        "--hidden-import=api.urls",
        "--collect-submodules=backend",
        "--collect-all=corsheaders",
        "--collect-all=whitenoise",
        "--collect-all=rest_framework",
        "main.py"
    ]
    subprocess.run(cmd, check=True)
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    build()
