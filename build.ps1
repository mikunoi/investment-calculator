param([string]$Python = "$PSScriptRoot/.venv/Scripts/python.exe", [string]$Compiler = "$PSScriptRoot/tools/inno/ISCC.exe")
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    & $Python build_source.py
    if ($LASTEXITCODE -ne 0) { throw 'Source bundle failed' }
    & cargo build --release --manifest-path launcher/Cargo.toml
    if ($LASTEXITCODE -ne 0) { throw 'Rust build failed' }
    & $Python -m PyInstaller --noconfirm --windowed --onedir --name CalculatorUI --distpath dist --workpath build --specpath . --paths ui --icon assets/matrix-icon.ico --add-data "assets/matrix-icon.ico;assets" --add-data "ui/translations.json;." --add-data "generated/InvestmentCalculator-source.txt;source" ui/main.py
    if ($LASTEXITCODE -ne 0) { throw 'UI build failed' }
    # Some Python distributions patch ssl.py to load an adjacent certificate file.
    # Bundle that public CA resource when present; standard Python needs no extra file.
    $sslResource = & $Python -c "import pathlib,ssl; p=pathlib.Path(ssl.__file__).with_name('codex-rejected-cas.pem'); print(str(p) if p.is_file() else '')"
    if ($sslResource) { Copy-Item -LiteralPath $sslResource -Destination 'dist/CalculatorUI/_internal/codex-rejected-cas.pem' -Force }
    New-Item -ItemType Directory -Force package/runtime,package/licenses | Out-Null
    # Rebuild only our staging runtime; removed dependencies must not linger in releases.
    $runtimeStage=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'package/runtime'))
    $packageRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'package'))
    if ($runtimeStage -ne (Join-Path $packageRoot 'runtime')) { throw 'Unexpected runtime staging path' }
    Remove-Item -LiteralPath $runtimeStage -Recurse -Force
    New-Item -ItemType Directory -Path $runtimeStage | Out-Null
    Copy-Item dist/CalculatorUI/* package/runtime -Recurse -Force
    if (Test-Path -LiteralPath 'package/InvestmentCalculator.exe') { Remove-Item -LiteralPath 'package/InvestmentCalculator.exe' -Force }
    Copy-Item launcher/target/release/investment-calculator.exe package/mikunoi_Stock_Calculator.exe -Force
    Copy-Item assets/matrix-icon.ico package/InvestmentCalculator.ico -Force
    Copy-Item README.md package/README.md -Force
    Copy-Item LICENSE,THIRD_PARTY.md package -Force
    Copy-Item licenses/* package/licenses -Recurse -Force
    New-Item -ItemType Directory -Force package/docs | Out-Null
    Copy-Item docs/*.md package/docs -Force

    & $Compiler /Q setup.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
} finally { Pop-Location }

