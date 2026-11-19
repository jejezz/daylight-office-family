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
; LangArg is used by every shortcut and file association. The second flag turns off Chromium's automatic
; encrypted-DNS upgrade (otherwise the app talks to dns.google when the PC uses Google DNS).
#define LangArg "--lang=ko-KR --disable-features=DnsOverHttps"

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
Root: HKA; Subkey: "Software\Classes\Daylight.Document.docx"; ValueType: string; ValueData: "{#AppName} .docx"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.docx\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-108"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.docx\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.docx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.docx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.xlsx"; ValueType: string; ValueData: "{#AppName} .xlsx"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.xlsx\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-111"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.xlsx\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.xlsx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.xlsx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.pptx"; ValueType: string; ValueData: "{#AppName} .pptx"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.pptx\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-110"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.pptx\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.pptx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.pptx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odt"; ValueType: string; ValueData: "{#AppName} .odt"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odt\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-119"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odt\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.odt\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.odt"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.ods"; ValueType: string; ValueData: "{#AppName} .ods"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.ods\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-124"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.ods\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.ods\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.ods"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odp"; ValueType: string; ValueData: "{#AppName} .odp"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odp\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-104"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.odp\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.odp\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.odp"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwp"; ValueType: string; ValueData: "{#AppName} .hwp"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwp\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-164"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwp\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.hwp\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.hwp"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwpx"; ValueType: string; ValueData: "{#AppName} .hwpx"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwpx\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},-165"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\Daylight.Document.hwpx\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" {#LangArg} ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.hwpx\OpenWithProgids"; ValueType: string; ValueName: "Daylight.Document.hwpx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
; Installed for all users (C:\Program Files) the settings file is read-only for normal users, so the font chooser fails: let Users modify just this file.
; Runs on every install/upgrade, so existing installs get fixed too.
Filename: "{sys}\icacls.exe"; Parameters: """{app}\daylight-user.css"" /grant *S-1-5-32-545:M"; Flags: runhidden
; Font chooser first (checked by default). It waits until the window is closed, so the app that starts next already reads the choice.
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\set-ui-font.ps1"""; WorkingDir: "{app}"; Description: "인터페이스 글꼴 설정 (기본은 시스템 글꼴)"; Flags: postinstall skipifsilent
Filename: "{app}\{#AppExe}"; Parameters: "{#LangArg}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
