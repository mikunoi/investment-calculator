[Setup]
AppId={{C23B1E36-B85D-4A97-89EC-24FA09373CD8}
AppName=mikunoi_Stock_Calculator
AppVersion=1.8.5
AppPublisher=mikunoi
DefaultDirName={localappdata}\Programs\IndependentInvestmentCalculator
DefaultGroupName=mikunoi_Stock_Calculator
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=releases
OutputBaseFilename=mikunoi_Stock_Calculator-Setup-1.8.5-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\matrix-icon.ico
UninstallDisplayName=mikunoi_Stock_Calculator
UninstallDisplayIcon={app}\mikunoi_Stock_Calculator.exe
CloseApplications=no
DisableProgramGroupPage=yes
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
[CustomMessages]
english.DesktopShortcut=Create a desktop shortcut
korean.DesktopShortcut=바탕 화면에 바로가기 만들기
english.LaunchApp=Launch mikunoi_Stock_Calculator
korean.LaunchApp=mikunoi_Stock_Calculator 실행
english.UninstallApp=Uninstall mikunoi_Stock_Calculator
korean.UninstallApp=mikunoi_Stock_Calculator 제거
[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; Flags: unchecked
[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\mikunoi_Stock_Calculator"; Filename: "{app}\mikunoi_Stock_Calculator.exe"; IconFilename: "{app}\InvestmentCalculator.ico"; AppUserModelID: "mikunoi.InvestmentCalculator"
Name: "{group}\{cm:UninstallApp}"; Filename: "{uninstallexe}"; IconFilename: "{app}\InvestmentCalculator.ico"
Name: "{userdesktop}\mikunoi_Stock_Calculator"; Filename: "{app}\mikunoi_Stock_Calculator.exe"; Tasks: desktopicon; IconFilename: "{app}\InvestmentCalculator.ico"; AppUserModelID: "mikunoi.InvestmentCalculator"
[Run]
Filename: "{app}\mikunoi_Stock_Calculator.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\mikunoi_Stock_Calculator.exe"; Flags: nowait; Check: IsAppUpdate
[UninstallDelete]
; Only empty application directories: never delete unknown/user files recursively.
Type: dirifempty; Name: "{app}\runtime\_internal\PIL"
Type: dirifempty; Name: "{app}\runtime\_internal"
Type: dirifempty; Name: "{app}\runtime"
Type: dirifempty; Name: "{app}"
[Code]
const
  ProductUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C23B1E36-B85D-4A97-89EC-24FA09373CD8}_is1';
var
  OldUninstaller: String;
  OldLocation: String;
  ReinstallFinished: Boolean;
  ActionPage: TInputOptionWizardPage;
  DeleteDataBox: TNewCheckBox;
  RemovalFinished: Boolean;
  AppUpdateMode: Boolean;

function Localize(Korean, English: String): String;
begin
  if ActiveLanguage = 'korean' then Result := Korean else Result := English;
end;

function ProtectedDirectory(Path: String): Boolean;
begin
  Result := FileExists(AddBackslash(Path) + 'Kiwoom5814.exe') or DirExists(AddBackslash(Path) + 'ats');
end;

function InitializeSetup(): Boolean;
var
  RegisteredCommand: String;
begin
  Result := True;
  AppUpdateMode := ExpandConstant('{param:APPUPDATE|0}') = '1';
  ReinstallFinished := False;
  OldUninstaller := '';
  OldLocation := '';
  if RegQueryStringValue(HKCU64, ProductUninstallKey, 'UninstallString', RegisteredCommand) then
  begin
    if WizardSilent and not AppUpdateMode then
    begin
      MsgBox(Localize('기존 mikunoi_Stock_Calculator가 있습니다. 재설치 동의가 필요하므로 설치파일을 직접 실행해 주세요.', 'An existing installation was found. Run this installer interactively to confirm reinstalling.'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    OldUninstaller := RemoveQuotes(Trim(RegisteredCommand));
    RegQueryStringValue(HKCU64, ProductUninstallKey, 'InstallLocation', OldLocation);
    if (OldLocation = '') or ProtectedDirectory(OldLocation) or
       (CompareText(RemoveBackslashUnlessRoot(ExtractFileDir(OldUninstaller)), RemoveBackslashUnlessRoot(OldLocation)) <> 0) or
       (CompareText(ExtractFileExt(OldUninstaller), '.exe') <> 0) or
       (Pos('unins', Lowercase(ExtractFileName(OldUninstaller))) <> 1) or
       not FileExists(OldUninstaller) then
    begin
      MsgBox(Localize('기존 mikunoi_Stock_Calculator의 제거 정보를 확인할 수 없습니다. Windows 설정에서 mikunoi_Stock_Calculator를 제거한 뒤 다시 설치해 주세요.', 'The existing uninstall information is invalid. Remove the app in Windows Settings and retry.'), mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure InitializeWizard();
begin
  RemovalFinished := False;
  ActionPage := CreateInputOptionPage(wpWelcome, Localize('mikunoi_Stock_Calculator 설치 또는 제거', 'Install or remove mikunoi_Stock_Calculator'),
    Localize('원하는 작업을 선택해 주세요.', 'Choose an action.'), Localize('mikunoi_Stock_Calculator 이외의 프로그램은 변경하지 않습니다.', 'Other programs will not be changed.'), True, False);
  ActionPage.Add(Localize('mikunoi_Stock_Calculator 설치 / 재설치', 'Install / reinstall'));
  ActionPage.Add(Localize('설치된 mikunoi_Stock_Calculator 제거', 'Remove mikunoi_Stock_Calculator'));
  ActionPage.SelectedValueIndex := 0;
  DeleteDataBox := TNewCheckBox.Create(WizardForm);
  DeleteDataBox.Parent := ActionPage.Surface;
  DeleteDataBox.Left := 0;
  DeleteDataBox.Top := ScaleY(135);
  DeleteDataBox.Width := ActionPage.SurfaceWidth;
  DeleteDataBox.Height := ScaleY(48);
  DeleteDataBox.Caption := Localize('제거할 때 저장한 내 자산과 목표 이력도 삭제 (복구 불가)', 'Also delete saved assets, targets and preferences (cannot be undone)');
  DeleteDataBox.Checked := False;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if RemovalFinished then
  begin
    Cancel := True;
    Confirm := False;
  end;
end;

function RemoveLocalData(): Boolean;
var
  DataDir: String;
begin
  // Delete only this application's four known files. Never recursively erase a folder.
  DataDir := AddBackslash(ExpandConstant('{localappdata}')) + 'IndependentInvestmentCalculator';
  Result := True;
  if FileExists(DataDir + '\settings.json') then
    if not DeleteFile(DataDir + '\settings.json') then Result := False;
  if FileExists(DataDir + '\settings.tmp') then
    if not DeleteFile(DataDir + '\settings.tmp') then Result := False;
  if FileExists(DataDir + '\portfolio.json') then
    if not DeleteFile(DataDir + '\portfolio.json') then Result := False;
  if FileExists(DataDir + '\portfolio.tmp') then
    if not DeleteFile(DataDir + '\portfolio.tmp') then Result := False;
  if FileExists(DataDir + '\goals.json') then
    if not DeleteFile(DataDir + '\goals.json') then Result := False;
  if FileExists(DataDir + '\goals.tmp') then
    if not DeleteFile(DataDir + '\goals.tmp') then Result := False;
  RemoveDir(DataDir);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ExitCode: Integer;
  Question: String;
begin
  Result := True;
  if (CurPageID = ActionPage.ID) and (ActionPage.SelectedValueIndex = 1) then
  begin
    Result := False;
    if OldUninstaller = '' then
    begin
      MsgBox(Localize('이 사용자 계정에 설치된 mikunoi_Stock_Calculator를 찾지 못했습니다.', 'No installation was found for this user.'), mbInformation, MB_OK);
      Exit;
    end;
    Question := Localize('mikunoi_Stock_Calculator를 제거할까요? 실행 중인 mikunoi_Stock_Calculator를 먼저 닫아 주세요.', 'Remove the app? Close mikunoi_Stock_Calculator first.');
    if DeleteDataBox.Checked then
      Question := Question + #13#10 + Localize('저장한 자산과 목표 이력도 삭제하며 복구할 수 없습니다.', 'Saved assets and target history will also be permanently deleted.')
    else
      Question := Question + #13#10 + Localize('저장한 자산과 목표 이력은 유지됩니다.', 'Saved assets and target history will be kept.');
    if MsgBox(Question, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) <> IDYES then Exit;
    if not Exec(OldUninstaller, '/SILENT /NORESTART', OldLocation, SW_SHOW, ewWaitUntilTerminated, ExitCode) then
    begin
      MsgBox(Localize('mikunoi_Stock_Calculator 제거를 시작하지 못했습니다.', 'Could not start the uninstaller.'), mbError, MB_OK);
      Exit;
    end;
    if (ExitCode <> 0) or RegKeyExists(HKCU64, ProductUninstallKey) or
       FileExists(AddBackslash(OldLocation) + 'runtime\CalculatorUI.exe') then
    begin
      MsgBox(Localize('제거가 완료되지 않았습니다. mikunoi_Stock_Calculator를 닫고 Windows 설정에서 제거 상태를 확인해 주세요.', 'Removal did not finish. Close the app and check Windows Settings.'), mbError, MB_OK);
      Exit;
    end;
    RemovalFinished := True;
    if DeleteDataBox.Checked then
    begin
      if RemoveLocalData() then
        MsgBox(Localize('mikunoi_Stock_Calculator와 저장 자료를 제거했습니다. 직접 내보낸 파일은 유지됩니다.', 'App and saved data removed. Exported files were kept.'), mbInformation, MB_OK)
      else
        MsgBox(Localize('프로그램은 제거했지만 일부 저장 자료를 삭제하지 못했습니다.', 'App removed, but some saved data could not be deleted.'), mbInformation, MB_OK);
    end
    else
      MsgBox(Localize('mikunoi_Stock_Calculator를 제거했습니다. 저장한 자산과 목표 이력은 유지됩니다.', 'App removed. Saved assets and target history were kept.'), mbInformation, MB_OK);
    WizardForm.Close;
    Exit;
  end;
  if (CurPageID = wpSelectDir) and ProtectedDirectory(ExpandConstant('{app}')) then
  begin
    MsgBox(Localize('기존 ATS 폴더에는 설치할 수 없습니다. 별도 계산기 폴더를 선택해 주세요.', 'This folder belongs to another application. Select a separate folder.'), mbError, MB_OK);
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
begin
  Result := '';
  if ActionPage.SelectedValueIndex = 1 then
  begin
    Result := Localize('제거 작업에서는 새 프로그램을 설치하지 않습니다.', 'Removal does not install a new application.');
    Exit;
  end;
  if ProtectedDirectory(ExpandConstant('{app}')) then
  begin
    Result := Localize('기존 ATS 폴더에는 설치할 수 없습니다.', 'Cannot install in a protected application folder.');
    Exit;
  end;
  if AppUpdateMode then
  begin
    if (OldLocation = '') or
       (CompareText(RemoveBackslashUnlessRoot(ExpandConstant('{app}')), RemoveBackslashUnlessRoot(OldLocation)) <> 0) then
      Result := 'Update installation path does not match the registered application.';
    // Keep the installed program until replacement; never uninstall or remove user data.
    Exit;
  end;
  if (OldUninstaller = '') or ReinstallFinished then Exit;
  if MsgBox(Localize('기존 mikunoi_Stock_Calculator를 제거한 뒤 새 버전을 설치할까요?', 'Remove the existing version and install this version?') + #13#10 + #13#10 +
    Localize('먼저 실행 중인 mikunoi_Stock_Calculator를 닫아 주세요.', 'Close mikunoi_Stock_Calculator first.') + #13#10 +
    Localize('저장한 내 자산과 목표 이력은 유지됩니다.', 'Your saved assets and target history will be kept.') + #13#10 +
    Localize('아니오를 선택하면 기존 프로그램을 그대로 두고 설치를 진행하지 않습니다.', 'Choose No to keep the existing installation and stop setup.'),
    mbConfirmation, MB_YESNO or MB_DEFBUTTON2) <> IDYES then
  begin
    Result := Localize('재설치에 동의하지 않아 기존 프로그램을 유지했습니다. 취소를 눌러 종료할 수 있습니다.', 'Reinstallation was not approved. The existing app was kept. Cancel to exit.');
    Exit;
  end;
  if not Exec(OldUninstaller, '/SILENT /NORESTART', OldLocation, SW_SHOW, ewWaitUntilTerminated, ExitCode) then
  begin
    Result := Localize('기존 mikunoi_Stock_Calculator 제거를 시작하지 못했습니다. 설치를 중단합니다.', 'Could not start the existing uninstaller. Setup stopped.');
    Exit;
  end;
  if (ExitCode <> 0) or RegKeyExists(HKCU64, ProductUninstallKey) or
     FileExists(AddBackslash(OldLocation) + 'runtime\CalculatorUI.exe') then
  begin
    Result := Localize('기존 프로그램 제거가 완료되지 않았습니다. mikunoi_Stock_Calculator를 닫고 제거 상태를 확인한 뒤 다시 설치해 주세요.', 'Removal did not finish. Close the app, verify removal and retry.');
    Exit;
  end;
  ReinstallFinished := True;
end;











function IsAppUpdate(): Boolean;
begin
  Result := AppUpdateMode;
end;
