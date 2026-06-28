import os
import sys
import shutil
import filecmp
import subprocess
from config import *

def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return "1.0.0"

def update_version(new_version):
    with open(VERSION_FILE, 'w') as f:
        f.write(new_version)
    print(f"✅ Version file updated to {new_version}")

def run_pyinstaller():
    print("🚀 Building executable with PyInstaller...")
    if os.path.exists(os.path.join(BASE_DIR, 'build')): shutil.rmtree(os.path.join(BASE_DIR, 'build'))
    if os.path.exists(os.path.join(BASE_DIR, 'dist')): shutil.rmtree(os.path.join(BASE_DIR, 'dist'))
    
    result = subprocess.run(["pyinstaller", SPEC_FILE, "--noconfirm", "--clean"], cwd=BASE_DIR)
    if result.returncode != 0:
        print("❌ PyInstaller build failed.")
        sys.exit(1)
        
    old_exe = os.path.join(DIST_DIR, 'VentaPOS.exe')
    new_exe = os.path.join(DIST_DIR, 'Venta.exe')
    if os.path.exists(old_exe):
        os.rename(old_exe, new_exe)

def archive_current_build(new_version):
    archive_path = os.path.join(ARCHIVE_DIR, f"Venta {new_version}")
    if os.path.exists(archive_path): shutil.rmtree(archive_path)
    shutil.copytree(DIST_DIR, archive_path)
    print(f"📁 Build successful and archived at: {archive_path}")

def get_archived_versions():
    if not os.path.exists(ARCHIVE_DIR): return []
    dirs = [d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))]
    versions = [d for d in dirs if d.startswith("Venta ")]
    versions.sort(reverse=True)
    return versions

def analyze_differences(old_dir, new_dir):
    print("\n🔍 Analyzing differences between the two versions...")
    added_files = []
    modified_files = []
    deleted_files = []

    # 1. البحث عن الملفات المضافة والمعدلة (بالمرور على النسخة الجديدة)
    for root, dirs, files in os.walk(new_dir):
        rel_path = os.path.relpath(root, new_dir)
        old_root = os.path.join(old_dir, rel_path) if rel_path != '.' else old_dir
        
        for file in files:
            new_file_path = os.path.join(root, file)
            old_file_path = os.path.join(old_root, file)
            rel_file_path = os.path.relpath(new_file_path, new_dir)
            
            if not os.path.exists(old_file_path):
                added_files.append(rel_file_path)
            elif not filecmp.cmp(old_file_path, new_file_path, shallow=False):
                modified_files.append(rel_file_path)

    # 2. البحث عن الملفات المحذوفة (بالمرور على النسخة القديمة)
    for root, dirs, files in os.walk(old_dir):
        rel_path = os.path.relpath(root, old_dir)
        new_root = os.path.join(new_dir, rel_path) if rel_path != '.' else new_dir
        
        for file in files:
            old_file_path = os.path.join(root, file)
            new_file_path = os.path.join(new_root, file)
            rel_file_path = os.path.relpath(old_file_path, old_dir)
            
            if not os.path.exists(new_file_path):
                deleted_files.append(rel_file_path)

    # طباعة التقارير بشكل منظم
    if added_files:
        print(f"\n✨ New Files Added ({len(added_files)}):")
        for f in added_files[:10]: print(f"   ➕ {f}")
        if len(added_files) > 10: print(f"   ... and {len(added_files) - 10} more.")

    if modified_files:
        print(f"\n📝 Existing Files Modified ({len(modified_files)}):")
        for f in modified_files[:10]: print(f"   🔄 {f}")
        if len(modified_files) > 10: print(f"   ... and {len(modified_files) - 10} more.")

    if deleted_files:
        print(f"\n🗑️ Files Deleted ({len(deleted_files)}):")
        for f in deleted_files[:10]: print(f"   ❌ {f}")
        if len(deleted_files) > 10: print(f"   ... and {len(deleted_files) - 10} more.")
        
    # ⚠️ ملحوظة هامة برمجياً: 
    # نحن نُرجع الملفات المضافة والمعدلة فقط لكي يقوم السكريبت بنسخها ووضعها في الباتش.
    # لا يمكننا إرجاع الملفات المحذوفة في هذه القائمة لأن السكريبت سيحاول نسخها ولن يجدها وسيعطي خطأ.
    return added_files + modified_files