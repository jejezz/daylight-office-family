; Daylight Office installer. Built by tools\package.ps1 (passes AppVersion, SourceDir, OutDir).
; Per-user install by default (no administrator rights needed); user settings live in %LOCALAPPDATA%\Daylight and
; HKCU\Software\Daylight and are never touched by install, upgrade or uninstall.
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\build\app"
#endif
#ifndef OutDir
  #define OutDir "..\..\dist"
#endif
#define AppName "Daylight Office"
#define AppExe "DesktopEditors.exe"
#define LangArg "--lang=ko-KR"

[Setup]
AppId={{7B1E2C3A-5D4F-4E8A-9C21-D41F6A0B3E77}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Daylight family edition
DefaultDirName={autopf}\Daylight
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutDir}
OutputBaseFilename=Daylight-Setup-{#AppVersion}
Compression=lzma2/normal
SolidCompression=yes
SetupIconFile={#SourceDir}\app.ico
UninstallDisplayIcon={app}\{#AppExe}
LicenseFile={#SourceDir}\LICENSE.txt
InfoBeforeFile=NOTICE.txt
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "assoc"; Description: "docx, xlsx, pptx, hwp ... 열기 프로그램에 {#AppName} 를 추가 (Windows 에서 기본 프로그램은 직접 고릅니다)"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Excludes: "unins000.*,daylight-user.css"; Flags: recursesubdirs createallsubdirs ignoreversion
; personal settings (interface font): created once, never overwritten by upgrades, kept on uninstall
Source: "{#SourceDir}\daylight-user.css"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "..\icons\LICENSE-phosphor.txt"; DestDir: "{app}\licenses"; DestName: "phosphor-LICENSE.txt"; Flags: ignoreversion
Source: "NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "{#LangArg}"
Name: "{group}\{#AppName} 글꼴 설정"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\set-ui-font.ps1"""; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "{#LangArg}"; Tasks: desktopicon

[Registry]
; ProgID and "Open with" entries only; the default program stays the user's choice.
Root: HKA; Subkey: "Software\Classes\Daylight.Document"; ValueType: string; ValueData: "{#AppName} document"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.docx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.xlsx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.pptx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.odt\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ods\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.odp\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.hwp\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.hwpx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "{#LangArg}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
