import os
import tempfile

def license_reset():
    """
    Wipes ONLY the SalesApp licensing data.
    Business data (Inventory, Invoices, Customers) is kept completely safe.
    """
    print("=" * 50)
    print("⚠️  WARNING: LICENSE RESET ONLY ⚠️")
    print("=" * 50)
    print("This will ONLY delete:")
    print(" - Your License Activation (You will need to re-enter your code)")
    print(" - System configuration related to licensing")
    print("")
    print("✅ SAFE: All Receipts, Inventory, Customers, and Passwords will NOT be deleted.")
    print("")
    
    confirm = input("Are you sure you want to reset the license? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Reset cancelled. No files were deleted.")
        return

    # 1. Determine AppData Path
    LOCAL_APP_DATA = os.environ.get('LOCALAPPDATA')
    if not LOCAL_APP_DATA:
        LOCAL_APP_DATA = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')

    BASE_DB_FOLDER = os.path.join(LOCAL_APP_DATA, 'VentaPOS')

    # 2. Files to delete from AppData (ONLY License/System related)
    files_to_delete = [
        'system_licensing.enc',    # System/License DB (encrypted)
        'system_licensing.bin',    # System/License DB (legacy unencrypted)
        'system_licensing.bin.bak',# System/License DB (migration backup)
        'license.key'              # Saved license keys
    ]

    # 3. Temp runtime files to delete (ONLY License/System related)
    temp_dir = tempfile.gettempdir()
    temp_files_to_delete = [
        os.path.join(temp_dir, '~sys_lic_runtime.tmp'),
        os.path.join(temp_dir, '~sys_lic_runtime.tmp-wal'),
        os.path.join(temp_dir, '~sys_lic_runtime.tmp-shm'),
    ]

    deleted_count = 0

    # 4. Clean up AppData License files
    if os.path.exists(BASE_DB_FOLDER):
        print(f"\nScanning secure folder: {BASE_DB_FOLDER}...")
        
        for filename in files_to_delete:
            file_path = os.path.join(BASE_DB_FOLDER, filename)
            if os.path.exists(file_path):
                try:
                    # إزالة الحماية عن الملف قبل مسحه (إن وجدت)
                    if os.name == 'nt':
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x80)
                        
                    os.remove(file_path)
                    print(f"  [DELETED] {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  [ERROR] Failed to delete {filename}: {e}")
                    print("  -> Is the app still running? Please close it first.")
    else:
        print("\nNo secure folder found.")

    # 5. Clean up temp runtime license files
    print(f"\nScanning temp folder: {temp_dir}...")
    for file_path in temp_files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  [DELETED] {os.path.basename(file_path)}")
                deleted_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to delete {os.path.basename(file_path)}: {e}")
                print("  -> Is the app still running? Please close it first.")

    print("\n" + "=" * 50)
    if deleted_count > 0:
        print(f"✅ License Reset Successful! Deleted {deleted_count} files.")
        print("Open Venta POS to enter a new license code.")
    else:
        print("✅ Finished. No license files were found to delete.")
    print("=" * 50)

if __name__ == "__main__":
    license_reset()
    input("\nPress Enter to exit...")