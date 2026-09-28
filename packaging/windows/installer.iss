; Inno Setup script. The release workflow passes /DAppVersion=x.y.z
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6F1B7C1E-4D2A-4B7E-9C3A-2E5D8F0A1B77}
AppName=Document Converter
AppVersion={#AppVersion}
AppPublisher=Joe Munene
DefaultDirName={autopf}\Document Converter
DefaultGroupName=Document Converter
DisableProgramGroupPage=yes
; Installs per user when not run as admin, so no UAC prompt is needed.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\..\dist
OutputBaseFilename=DocumentConverter-Windows-Setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\DocumentConverter.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\..\dist\DocumentConverter\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Document Converter"; Filename: "{app}\DocumentConverter.exe"
Name: "{autodesktop}\Document Converter"; Filename: "{app}\DocumentConverter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DocumentConverter.exe"; Description: "Open Document Converter"; Flags: nowait postinstall skipifsilent
