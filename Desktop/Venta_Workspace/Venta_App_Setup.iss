; =========================================================
; Venta POS - APP INSTALLER (FULL SETUP WITH AUTO-UNINSTALL)
; =========================================================

#ifndef MyAppVersion
  #define MyAppVersion "2.1.1" 
#endif

#define MyAppName "Venta POS"
#define MyAppPublisher "Abdalatyf Ahmed"
#define MyAppExeName "Venta.exe"
#define MyWorkspacePath "D:\exe\venta_pos\Venta_Workspace"

[Setup]
AppId={{5E3B8F9A-1234-4B5C-9D8E-7F6A5B4C3D2E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#MyWorkspacePath}\Releases
OutputBaseFilename=Venta_App_Setup_v{#MyAppVersion}
SetupIconFile={#MyWorkspacePath}\venta.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DirExistsWarning=no 

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\VentaPOS\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\VentaPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[UninstallDelete]
; مسح الفولدر بالكامل عند الإزالة لضمان النظافة
Type: filesandordirs; Name: "{app}"

; =========================================================
; 🔴 السحر البرمجي المحدث: كود الإزالة + التنظيف الإجباري
; =========================================================
[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  // التعديل الأول: استخدام قوس واحد فقط { داخل النص
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{5E3B8F9A-1234-4B5C-9D8E-7F6A5B4C3D2E}_is1';
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    // 1. محاولة الإزالة الرسمية للنسخة القديمة من الويندوز
    if IsUpgrade() then
    begin
      UnInstallOldVersion();
    end;
    
    // 2. التعديل الجذري: مسح الفولدر بالقوة (DelTree) لضمان عدم بقاء أي ملفات قديمة (مثل dll أو exe)
    // العوامل (True, True, True) تعني: مسح الملفات، مسح المجلدات الفرعية، مسح المجلد الرئيسي
    DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;