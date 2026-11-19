# Frozen panes survive a save (engine patch sdkjs/0004), in build\app:
#   open an .xlsx, type into a cell, Ctrl+S -> the same file is overwritten and the never-shown sheet keeps its split
# Usage: powershell -ExecutionPolicy Bypass -File tests\frozen-pane.ps1
# Exit code 0 = all checks passed. Do not touch the app window while it runs (keyboard input is simulated).
# The test file also has a sheet that is never shown, with frozen panes saved while scrolled: its split must survive
# the save (engine patch sdkjs/0004; upstream wrote a negative split that Excel repairs).
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
Add-Type -AssemblyName System.Windows.Forms
$app = Join-Path $root 'build\app'
$work = Join-Path $root 'build\frozen-test'
$py = (Get-Command python -ErrorAction Stop).Source
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}
function Count-Bytes([string]$Path, [string]$Hex) {
  [int](& $py -I -c "import sys; print(open(sys.argv[1],'rb').read().count(bytes.fromhex(sys.argv[2])))" $Path $Hex)
}
function Eval-Editor([string]$Js) {
  # runs JS in the editor frame through the DevTools port (tests\lib\cdp.py)
  $code = "import sys; sys.path.insert(0, r'" + (Join-Path $PSScriptRoot 'lib') + "'); import cdp; s = cdp.connect(9333); print(cdp.ev(s, sys.argv[1]))"
  & $py -I -c $code $Js
}

# Ctrl+S on an opened .xlsx overwrites it
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force $work | Out-Null
$doc = Join-Path $work 'frozen.xlsx'
& $py -I (Join-Path $PSScriptRoot 'make-frozen-xlsx.py') make $doc
$t0 = (Get-Item $doc).LastWriteTime
Stop-App $app
Start-App $app @('--single-window-app', '--remote-debugging-port=9333', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*frozen.xlsx*' 60
Check 'xlsx opens' ($null -ne $w) $(if ($w) { $w.Process.MainWindowTitle } else { 'timeout' })
if ($w) {
  $p = $w.Process
  Focus-AppWindow $p
  $null = Wait-WindowStable $p
  Start-Sleep 2
  $r = Get-WindowRect $p
  Focus-AppWindow $p; Start-Sleep -Milliseconds 500
  # type into a grid cell until the title shows the unsaved mark (the first keys can be lost while the editor settles)
  for ($try = 0; $try -lt 3; $try++) {
    Focus-AppWindow $p; Start-Sleep -Milliseconds 500
    [DaylightUi]::Click([int](($r.L + $r.R) / 2), [int]($r.T + ($r.B - $r.T) * 0.6)); Start-Sleep 1
    [System.Windows.Forms.SendKeys]::SendWait('saved1{ENTER}'); Start-Sleep 2
    $p.Refresh()
    if ($p.MainWindowTitle.StartsWith('*')) { break }
  }
  Check 'typing marks the document modified' ($p.MainWindowTitle.StartsWith('*')) $p.MainWindowTitle
  [System.Windows.Forms.SendKeys]::SendWait('^s')
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt 20 -and (Get-Item $doc).LastWriteTime -eq $t0) { Start-Sleep -Milliseconds 300 }
  Start-Sleep 1
  Check 'Ctrl+S writes the same .xlsx' ((Get-Item $doc).LastWriteTime -ne $t0)
  $p.Refresh()
  Check 'title has no unsaved mark' (-not $p.MainWindowTitle.StartsWith('*')) $p.MainWindowTitle
  $out = & $py -I (Join-Path $PSScriptRoot 'make-frozen-xlsx.py') check $doc 'saved1'
  Check 'saved file keeps the typed text and frozen split' ($LASTEXITCODE -eq 0) "$out"

  $shot = Join-Path $root ("build\shots\frozen-pane-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
  Save-WindowShot $p $shot
}
Stop-App $app
$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed" -f $results.Count, $fail)
exit $(if ($fail -eq 0) { 0 } else { 1 })
