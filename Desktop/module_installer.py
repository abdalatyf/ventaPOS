import os
import shutil
import subprocess
from config import *

def build_full_installer(new_version):
    print("📦 Building Full Release Installer...")
    subprocess.run([ISCC_PATH, FULL_SETUP_ISS, f"/DMyAppVersion={new_version}"])
    print(f"✅ Full Release successfully generated in the Releases folder!")

def build_patch_installer(old_version_name, old_dir, new_version, new_dir, changed_files):
    old_version_num = old_version_name.replace("Venta ", "").strip()
    print(f"📦 Preparing Patch Update... Detected {len(changed_files)} changed files.")
    
    patch_temp_dir = os.path.join(BASE_DIR, 'build', 'patch_temp')
    patch_files_dir = os.path.join(patch_temp_dir, 'files_to_patch')
    if os.path.exists(patch_temp_dir): shutil.rmtree(patch_temp_dir)
    os.makedirs(patch_files_dir)
    
    for rel_file in changed_files:
        src = os.path.join(new_dir, rel_file) 
        dst = os.path.join(patch_files_dir, rel_file)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        
    patch_iss_path = os.path.join(patch_temp_dir, 'Patch_Setup.iss')
    iss_content = f"""
[Setup]
AppId={{{{5E3B8F9A-1234-4B5C-9D8E-7F6A5B4C3D2E}}
AppName=Venta POS Update
AppVersion={new_version}
CreateAppDir=yes
DefaultDirName={{autopf}}\\Venta POS
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputDir="{RELEASES_DIR}"
OutputBaseFilename=Venta_Patch_v{old_version_num}_to_v{new_version}
Compression=lzma2/ultra
SolidCompression=yes
SetupIconFile="{os.path.join(WORKSPACE_DIR, 'venta.ico')}"
DirExistsWarning=no

[Files]
Source: "{patch_files_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{{app}}\\Venta.exe"; Description: "Updating data and starting application"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  InstalledVersion: String;
  TargetOldVersion: String;
begin
  Result := True;
  TargetOldVersion := '{old_version_num}';

  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{5E3B8F9A-1234-4B5C-9D8E-7F6A5B4C3D2E}}_is1', 'DisplayVersion', InstalledVersion) then
  begin
    if InstalledVersion <> TargetOldVersion then
    begin
      MsgBox('Error: This patch is strictly for upgrading version ' + TargetOldVersion + '.' #13#10 + 'Your currently installed version is: ' + InstalledVersion, mbError, MB_OK);
      Result := False;
    end;
  end
  else
  begin
    MsgBox('Error: Venta POS is not installed on this system. Please install the Full Release first.', mbError, MB_OK);
    Result := False;
  end;
end;
"""
    with open(patch_iss_path, 'w', encoding='utf-8-sig') as f:
        f.write(iss_content)
        
    print("⚙️ Compiling Patch Installer via Inno Setup...")
    subprocess.run([ISCC_PATH, patch_iss_path])
    print(f"✅ Patch successfully generated in Releases: Venta_Patch_v{old_version_num}_to_v{new_version}.exe")