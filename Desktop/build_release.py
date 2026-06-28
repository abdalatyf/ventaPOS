import os
import shutil
from config import *
import module_builder as builder
import module_installer as installer
import module_git as git
import module_cloud as cloud

def task_build_version():
    print("\n--- TASK 1: BUILD & ARCHIVE ---")
    current_ver = builder.get_current_version()
    new_ver = input(f"Enter NEW version number [Current: {current_ver}]: ").strip()
    if not new_ver: new_ver = current_ver
    
    builder.update_version(new_ver)
    builder.run_pyinstaller()
    builder.archive_current_build(new_ver)

def task_create_installer():
    print("\n--- TASK 2: CREATE INSTALLER ---")
    current_ver = builder.get_current_version()
    
    target_ver = input(f"Enter TARGET version to build installer for [Default: {current_ver}]: ").strip()
    if not target_ver: 
        target_ver = current_ver
        
    archive_path = os.path.join(ARCHIVE_DIR, f"Venta {target_ver}")
    
    if not os.path.exists(archive_path):
        print(f"❌ Cannot find Archive for TARGET version {target_ver}. Run Task 1 first.")
        return

    print("\nSelect Installer Type:")
    print("1) Full Release (For new customers)")
    print("2) Patch Update (For existing customers)")
    choice = input("Choice (1 or 2): ").strip()

    if choice == '1':
        print(f"📦 Building Full Release Installer for v{target_ver}...")
        if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
        shutil.copytree(archive_path, DIST_DIR)
        installer.build_full_installer(target_ver)

    elif choice == '2':
        archived_versions = builder.get_archived_versions()
        
        if f"Venta {target_ver}" in archived_versions:
            archived_versions.remove(f"Venta {target_ver}")
            
        if not archived_versions:
            print("❌ No previous versions found in Archive to compare against!")
            return
            
        print("\n📁 Found the following OLD versions in Archive:")
        for idx, ver in enumerate(archived_versions, 1):
            print(f"   {idx}) {ver}")
            
        ver_choice = input(f"\n🔸 Select the installed OLD version to upgrade to v{target_ver}: ").strip()
        try:
            selected_old_version = archived_versions[int(ver_choice) - 1]
            old_dir = os.path.join(ARCHIVE_DIR, selected_old_version)
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
            return
            
        # 🔴 استدعاء دالة التحليل وطباعة التقرير
        changed = builder.analyze_differences(old_dir, archive_path)
        
        if not changed:
            print("⚠️ No file changes detected between the two versions!")
            return
            
        # 🔴 التعديل الجديد: خطوة التأكيد قبل البناء
        confirm = input("\n❓ Proceed with building the patch update based on these changes? (y/n): ").strip().lower()
        if confirm == 'y':
            installer.build_patch_installer(selected_old_version, old_dir, target_ver, archive_path, changed)
        else:
            print("🚫 Patch build cancelled by user.")
def task_git_operations():
    print("\n--- TASK 3: GIT DOCUMENTATION ---")
    current_ver = builder.get_current_version()
    git.commit_and_tag(current_ver)

def task_cloud_upload():
    print("\n--- TASK 4: CLOUD UPLOAD ---")
    cloud.upload_to_mediafire()

def main_menu():
    while True:
        print("\n" + "="*50)
        print(" 🛠️ VentaPOS - Release Engineering Automation 🛠️")
        print("="*50)
        print(f"🔹 Current Version in System: {builder.get_current_version()}")
        print("\nSelect a task to execute:")
        print("  1) Build Version & Archive (PyInstaller)")
        print("  2) Create Installer (Inno Setup - Full/Patch)")
        print("  3) Push to Git (Commit & Tag)")
        print("  4) Upload to Cloud (MediaFire)")
        print("  0) Exit")
        
        choice = input("\nEnter Task Number: ").strip()
        
        if choice == '1': task_build_version()
        elif choice == '2': task_create_installer()
        elif choice == '3': task_git_operations()
        elif choice == '4': task_cloud_upload()
        elif choice == '0':
            print("👋 Exiting... Have a great day!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    main_menu()