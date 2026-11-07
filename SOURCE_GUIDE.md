# mikunoi_Stock_Calculator 개발 / Development

Rust stdlib launcher + Python 3.12 Tkinter UI. No broker or order engine.

## Run from source (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe build_source.py
.venv/Scripts/python.exe ui/main.py
```

## Build the installer
Install Rust stable MSVC, Visual Studio C++ Build Tools, Windows SDK and Inno Setup.
Set the RC environment variable to rc.exe if the SDK resource compiler path differs.
```powershell
./build.ps1 -Compiler 'C:/Program Files (x86)/Inno Setup 7/ISCC.exe'
```
Outputs are in releases/. End users do not need developer tools.

## Check changes
```powershell
.venv/Scripts/python.exe release_checks.py
```
Tests isolate LOCALAPPDATA using a temporary folder; they do not read personal assets.

## Modules
- main.py: app, asset editor and preference persistence
- quantity.py / portfolio_data.py: Decimal shares (up to 8 places), validation and currency conversion
- average_cost.py / allocation_tool.py: calculations and tool views
- i18n.py / translations.json: explicit Korean-to-English UI catalog; user data is not translated
- asset_files.py: bilingual Excel/CSV interchange and JSON
- allocation_export.py: image export; goal_history.py: five saved scenarios
- source_export.py: explicit user-approved source TXT export

## 유지 사항 / Compatibility
설치 ID와 LocalAppData/IndependentInvestmentCalculator 경로를 유지하여 업그레이드 시 개인 자료를 보존합니다.
Keep the installation AppId and data path stable. Do not bundle personal portfolio, goals or settings files.
US selects English text; the reporting currency stays KRW. No automatic FX or order execution.
Do not truncate fractional shares. Persist quantities as decimal strings; calculations use Decimal.

## Source TXT recovery
Save each BEGIN FILE / END FILE section to its specified relative path.
Decode the BASE64 icon section into assets/matrix-icon.ico.
Do not recursively include generated source bundles.

## License
MIT License, Copyright (c) 2026 mikunoi. Keep LICENSE and third-party notices.
