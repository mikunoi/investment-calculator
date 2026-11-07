param(
    [Parameter(Mandatory=$true)][string]$InstallDir,
    [int]$InstallerPid=0,
    [switch]$StopOnly
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
$launcher=Join-Path $root 'mikunoi_Stock_Calculator.exe'
$ui=Join-Path $root 'runtime\CalculatorUI.exe'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf) -or -not (Test-Path -LiteralPath $ui -PathType Leaf)) { throw 'Invalid calculator installation' }
if ((Test-Path -LiteralPath (Join-Path $root 'ats')) -or (Test-Path -LiteralPath (Join-Path $root 'Kiwoom5814.exe'))) { throw 'Protected application directory' }
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$logDir=Join-Path $env:LOCALAPPDATA 'IndependentInvestmentCalculator'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log=Join-Path $logDir 'update-restart.log'
function Note([string]$message) { Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$message) }
function Matching {
    @(Get-Process -Name 'mikunoi_Stock_Calculator','CalculatorUI' -ErrorAction SilentlyContinue | Where-Object {
        $_.SessionId -eq $session -and ($_.Path -eq $launcher -or $_.Path -eq $ui)
    })
}
try {
    if ($InstallerPid -gt 0) {
        $installer=Get-Process -Id $InstallerPid -ErrorAction SilentlyContinue
        if ($installer -and -not $installer.WaitForExit(600000)) { throw 'Installer has not exited; restart cancelled' }
    }
    # Exact installation paths only; never taskkill by name or kill a process tree.
    foreach ($p in (Matching)) { [void]$p.CloseMainWindow() }
    $until=[DateTime]::UtcNow.AddSeconds(3)
    while ((Matching).Count -gt 0 -and [DateTime]::UtcNow -lt $until) { Start-Sleep -Milliseconds 100 }
    foreach ($p in (Matching)) {
        # Refresh identity immediately before stopping a surviving hidden process.
        $fresh=Get-Process -Id $p.Id -ErrorAction SilentlyContinue
        if ($fresh -and $fresh.StartTime -eq $p.StartTime -and $fresh.SessionId -eq $session -and ($fresh.Path -eq $launcher -or $fresh.Path -eq $ui)) {
            Stop-Process -InputObject $fresh -Force
            [void]$fresh.WaitForExit(5000)
        }
    }
    if ((Matching).Count -gt 0) { throw 'Calculator processes did not exit; restart cancelled' }
    Note 'Calculator processes stopped; single-instance owner released.'
    if ($StopOnly) { exit 0 }
    foreach ($name in @('TCL_LIBRARY','TK_LIBRARY','PYTHONHOME','PYTHONPATH')) { [Environment]::SetEnvironmentVariable($name,$null,'Process') }
    $env:PYINSTALLER_RESET_ENVIRONMENT='1'
    for ($attempt=1; $attempt -le 2; $attempt++) {
        Start-Process -FilePath $launcher -WorkingDirectory $root -WindowStyle Normal
        # Retry the first hidden start quickly; give a slow second start more time.
        $deadline=[DateTime]::UtcNow.AddSeconds($(if ($attempt -eq 1) {1.3} else {10}))
        do {
            Start-Sleep -Milliseconds 100
            $visible=@(Matching | Where-Object { $_.Path -eq $ui -and $_.MainWindowHandle -ne 0 })
            if ($visible.Count -gt 0) { Note 'Calculator window visible after update.'; exit 0 }
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($attempt -eq 2) {
            Note 'Second start has not shown a window yet; leaving the process running.'
            throw 'Calculator window did not appear within the startup wait.'
        }
        Note ('No visible window; cleaning up startup attempt '+$attempt)
        foreach ($p in (Matching | Sort-Object @{Expression={if($_.Path -eq $launcher){0}else{1}}})) {
            $fresh=Get-Process -Id $p.Id -ErrorAction SilentlyContinue
            if ($fresh -and $fresh.StartTime -eq $p.StartTime -and $fresh.SessionId -eq $session -and ($fresh.Path -eq $launcher -or $fresh.Path -eq $ui)) {
                Stop-Process -InputObject $fresh -Force
                [void]$fresh.WaitForExit(5000)
            }
        }
        if ((Matching).Count -gt 0) { throw 'Could not release calculator startup lock' }
    }
    throw 'Calculator window did not appear after retry.'
} catch {
    Note ('Restart failed: '+$_.Exception.Message)
    exit 1
}
