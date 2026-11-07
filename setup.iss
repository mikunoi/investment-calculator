[Setup]
AppId={{C23B1E36-B85D-4A97-89EC-24FA09373CD8}
AppName=투자계산기
AppVersion=1.7.0
AppPublisher=mikunoi
DefaultDirName={localappdata}\Programs\IndependentInvestmentCalculator
DefaultGroupName=투자계산기
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=releases
OutputBaseFilename=InvestmentCalculator-Setup-1.7.0-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\matrix-icon.ico
UninstallDisplayName=투자계산기
UninstallDisplayIcon={app}\InvestmentCalculator.exe
CloseApplications=no
DisableProgramGroupPage=yes
[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
[Tasks]
Name: "desktopicon"; Description: "바탕 화면에 바로가기 만들기"; Flags: unchecked
[Files]
Source: "package\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\투자계산기"; Filename: "{app}\InvestmentCalculator.exe"; IconFilename: "{app}\InvestmentCalculator.ico"; AppUserModelID: "mikunoi.InvestmentCalculator"
Name: "{group}\투자계산기 제거"; Filename: "{uninstallexe}"; IconFilename: "{app}\InvestmentCalculator.ico"
Name: "{userdesktop}\투자계산기"; Filename: "{app}\InvestmentCalculator.exe"; Tasks: desktopicon; IconFilename: "{app}\InvestmentCalculator.ico"; AppUserModelID: "mikunoi.InvestmentCalculator"
[Run]
Filename: "{app}\InvestmentCalculator.exe"; Description: "투자계산기 실행"; Flags: nowait postinstall skipifsilent
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

function ProtectedDirectory(Path: String): Boolean;
begin
  Result := FileExists(AddBackslash(Path) + 'Kiwoom5814.exe') or DirExists(AddBackslash(Path) + 'ats');
end;

function InitializeSetup(): Boolean;
var
  RegisteredCommand: String;
begin
  Result := True;
  ReinstallFinished := False;
  OldUninstaller := '';
  OldLocation := '';
  if RegQueryStringValue(HKCU64, ProductUninstallKey, 'UninstallString', RegisteredCommand) then
  begin
    if WizardSilent then
    begin
      MsgBox('기존 투자계산기가 있습니다. 재설치 동의가 필요하므로 설치파일을 직접 실행해 주세요.', mbError, MB_OK);
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
      MsgBox('기존 투자계산기의 제거 정보를 확인할 수 없습니다. Windows 설정에서 투자계산기를 제거한 뒤 다시 설치해 주세요.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure InitializeWizard();
begin
  RemovalFinished := False;
  ActionPage := CreateInputOptionPage(wpWelcome, '투자계산기 설치 또는 제거',
    '원하는 작업을 선택해 주세요.', '투자계산기 이외의 프로그램은 변경하지 않습니다.', True, False);
  ActionPage.Add('투자계산기 설치 / 재설치');
  ActionPage.Add('설치된 투자계산기 제거');
  ActionPage.SelectedValueIndex := 0;
  DeleteDataBox := TNewCheckBox.Create(WizardForm);
  DeleteDataBox.Parent := ActionPage.Surface;
  DeleteDataBox.Left := 0;
  DeleteDataBox.Top := ScaleY(135);
  DeleteDataBox.Width := ActionPage.SurfaceWidth;
  DeleteDataBox.Height := ScaleY(48);
  DeleteDataBox.Caption := '제거할 때 저장한 내 자산과 목표 이력도 삭제 (복구 불가)';
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
      MsgBox('이 사용자 계정에 설치된 투자계산기를 찾지 못했습니다.', mbInformation, MB_OK);
      Exit;
    end;
    Question := '투자계산기를 제거할까요? 실행 중인 투자계산기를 먼저 닫아 주세요.';
    if DeleteDataBox.Checked then
      Question := Question + #13#10 + '저장한 자산과 목표 이력도 삭제하며 복구할 수 없습니다.'
    else
      Question := Question + #13#10 + '저장한 자산과 목표 이력은 유지됩니다.';
    if MsgBox(Question, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) <> IDYES then Exit;
    if not Exec(OldUninstaller, '/SILENT /NORESTART', OldLocation, SW_SHOW, ewWaitUntilTerminated, ExitCode) then
    begin
      MsgBox('투자계산기 제거를 시작하지 못했습니다.', mbError, MB_OK);
      Exit;
    end;
    if (ExitCode <> 0) or RegKeyExists(HKCU64, ProductUninstallKey) or
       FileExists(AddBackslash(OldLocation) + 'runtime\CalculatorUI.exe') then
    begin
      MsgBox('제거가 완료되지 않았습니다. 투자계산기를 닫고 Windows 설정에서 제거 상태를 확인해 주세요.', mbError, MB_OK);
      Exit;
    end;
    RemovalFinished := True;
    if DeleteDataBox.Checked then
    begin
      if RemoveLocalData() then
        MsgBox('투자계산기와 저장 자료를 제거했습니다. 직접 내보낸 파일은 유지됩니다.', mbInformation, MB_OK)
      else
        MsgBox('프로그램은 제거했지만 일부 저장 자료를 삭제하지 못했습니다.', mbInformation, MB_OK);
    end
    else
      MsgBox('투자계산기를 제거했습니다. 저장한 자산과 목표 이력은 유지됩니다.', mbInformation, MB_OK);
    WizardForm.Close;
    Exit;
  end;
  if (CurPageID = wpSelectDir) and ProtectedDirectory(ExpandConstant('{app}')) then
  begin
    MsgBox('기존 ATS 폴더에는 설치할 수 없습니다. 별도 계산기 폴더를 선택해 주세요.', mbError, MB_OK);
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
    Result := '제거 작업에서는 새 프로그램을 설치하지 않습니다.';
    Exit;
  end;
  if ProtectedDirectory(ExpandConstant('{app}')) then
  begin
    Result := '기존 ATS 폴더에는 설치할 수 없습니다.';
    Exit;
  end;
  if (OldUninstaller = '') or ReinstallFinished then Exit;
  if MsgBox('기존 투자계산기를 제거한 뒤 새 버전을 설치할까요?' + #13#10 + #13#10 +
    '먼저 실행 중인 투자계산기를 닫아 주세요.' + #13#10 +
    '저장한 내 자산과 목표 이력은 유지됩니다.' + #13#10 +
    '아니오를 선택하면 기존 프로그램을 그대로 두고 설치를 진행하지 않습니다.',
    mbConfirmation, MB_YESNO or MB_DEFBUTTON2) <> IDYES then
  begin
    Result := '재설치에 동의하지 않아 기존 프로그램을 유지했습니다. 취소를 눌러 종료할 수 있습니다.';
    Exit;
  end;
  if not Exec(OldUninstaller, '/SILENT /NORESTART', OldLocation, SW_SHOW, ewWaitUntilTerminated, ExitCode) then
  begin
    Result := '기존 투자계산기 제거를 시작하지 못했습니다. 설치를 중단합니다.';
    Exit;
  end;
  if (ExitCode <> 0) or RegKeyExists(HKCU64, ProductUninstallKey) or
     FileExists(AddBackslash(OldLocation) + 'runtime\CalculatorUI.exe') then
  begin
    Result := '기존 프로그램 제거가 완료되지 않았습니다. 투자계산기를 닫고 제거 상태를 확인한 뒤 다시 설치해 주세요.';
    Exit;
  end;
  ReinstallFinished := True;
end;










