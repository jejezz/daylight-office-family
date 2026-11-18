# Saving .xlsm (tools\formats\apply.py): static byte checks, then in build\app
#   1) open an .xlsm, type into a cell, Ctrl+S -> the same file is overwritten as .xlsm (no Save As dialog)
#   2) ask the editor for Save As with type XLSM -> the dialog accepts it and writes a new .xlsm
# Usage: powershell -ExecutionPolicy Bypass -File tests\xlsm-save.ps1
# Exit code 0 = all checks passed. Do not touch the app window while it runs (keyboard input is simulated).
# The test file also has a sheet that is never shown, with frozen panes saved while scrolled: its split must survive
# the save (engine patch sdkjs/0004; upstream wrote a negative split that Excel repairs).
# Note: the test file has no VBA part; keeping real macros is not checked here.
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
Add-Type -AssemblyName System.Windows.Forms
$app = Join-Path $root 'build\app'
$work = Join-Path $root 'build\xlsm-test'
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

# 1. static: patched bytes are in the build
Check 'dll save-format list has XLSM' ((Count-Bytes (Join-Path $app 'ascdocumentscore.dll') 'c7451005010000483b5310740dc70205010000') -eq 1)
Check 'exe dialog filter key is XLSM' ((Count-Bytes (Join-Path $app 'editors.exe') 'c7852801000005010000c7442420ffffffff4533c94c8d05') -eq 1)
Check 'exe dialog filter pattern *.xlsm' ((Count-Bytes (Join-Path $app 'editors.exe') '0020282a2e786c736d2900') -eq 1)

# 2. Ctrl+S on an opened .xlsm overwrites it as .xlsm
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force $work | Out-Null
$doc = Join-Path $work 'macro.xlsm'
& $py -I (Join-Path $PSScriptRoot 'make-xlsm.py') make $doc
$t0 = (Get-Item $doc).LastWriteTime
Stop-App $app
Start-App $app @('--single-window-app', '--remote-debugging-port=9333', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*macro.xlsm*' 60
Check 'xlsm opens' ($null -ne $w) $(if ($w) { $w.Process.MainWindowTitle } else { 'timeout' })
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
  Check 'Ctrl+S writes the same .xlsm' ((Get-Item $doc).LastWriteTime -ne $t0)
  $p.Refresh()
  Check 'title has no unsaved mark' (-not $p.MainWindowTitle.StartsWith('*')) $p.MainWindowTitle
  $out = & $py -I (Join-Path $PSScriptRoot 'make-xlsm.py') check $doc 'saved1'
  Check 'saved file is macro-enabled with the typed text' ($LASTEXITCODE -eq 0) "$out"

  # 3. Save As with type XLSM (the editor passes the type; the dialog must map it back to XLSM)
  $doc2 = Join-Path $work 'saveas.xlsm'
  [System.Windows.Forms.SendKeys]::SendWait('saved2{ENTER}'); Start-Sleep 1
  # (no double quotes in the JS: Windows PowerShell 5.1 strips them when passing arguments to python)
  $null = Eval-Editor 'var W=document.querySelector(''iframe'').contentWindow; setTimeout(function(){W.Asc.editor.asc_DownloadAs(new W.Asc.asc_CDownloadOptions(W.Asc.c_oAscFileType.XLSM));},10); 1'
  Start-Sleep 4
  [System.Windows.Forms.SendKeys]::SendWait($doc2); Start-Sleep 1
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt 20 -and -not (Test-Path $doc2)) { Start-Sleep -Milliseconds 300 }
  Start-Sleep 2
  Check 'Save As .xlsm creates the file' (Test-Path $doc2) $doc2
  if (Test-Path $doc2) {
    $out = & $py -I (Join-Path $PSScriptRoot 'make-xlsm.py') check $doc2 'saved2'
    Check 'Save As result is macro-enabled with the typed text' ($LASTEXITCODE -eq 0) "$out"
  }
  $shot = Join-Path $root ("build\shots\xlsm-save-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
  Save-WindowShot $p $shot
}
Stop-App $app
$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed" -f $results.Count, $fail)
exit $(if ($fail -eq 0) { 0 } else { 1 })
