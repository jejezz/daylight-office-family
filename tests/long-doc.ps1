# Long document check: opens tests\data\long.docx (about 100 pages), reports time to open, memory, and screenshots
# the first page and the last page (Ctrl+End). Look at the screenshots: the status bar should show the page count.
# Real keyboard input: do not touch keyboard or mouse while this runs.
# Usage: powershell -ExecutionPolicy Bypass -File tests\long-doc.ps1 [-Which build|upstream]
param([ValidateSet('build', 'upstream')][string]$Which = 'build')
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
if ($Which -eq 'upstream') { $app = (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName }
$doc = Join-Path $PSScriptRoot 'data\long.docx'
function Chord([byte]$mod, [byte]$vk) {
  [DaylightUi]::keybd_event($mod, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60
  [DaylightUi]::Key($vk, 300)
  [DaylightUi]::keybd_event($mod, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200
}
function Mem-MB { [math]::Round((Get-AppProcesses $app | Measure-Object WorkingSet64 -Sum).Sum / 1MB) }
Stop-App $app
$sw = [Diagnostics.Stopwatch]::StartNew()
Start-App $app @('--lang=ko-KR', '--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*long*' 90
if (-not $w) { Write-Host 'FAIL  app did not start'; exit 1 }
$tTitle = [math]::Round($sw.Elapsed.TotalSeconds, 1)
Focus-AppWindow $w.Process
$tStable = Wait-WindowStable $w.Process 190 60
$tOpen = [math]::Round($sw.Elapsed.TotalSeconds, 1)
Start-Sleep -Seconds 10
Write-Host ('title after {0}s, ribbon stable after {1}s total, memory {2} MB' -f $tTitle, $tOpen, (Mem-MB))
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 640, $r.T + 400)
Save-WindowShot $w.Process (Join-Path $root "build\shots\long-$Which-first.png")
$s2 = [Diagnostics.Stopwatch]::StartNew()
Chord 0x11 0x23   # Ctrl+End
Start-Sleep -Seconds 3
Write-Host ('Ctrl+End then 3 s wait, memory {0} MB' -f (Mem-MB))
Save-WindowShot $w.Process (Join-Path $root "build\shots\long-$Which-last.png")
$alive = [bool](Get-AppWindow $app)
Write-Host ('{0}  app still running: {1}' -f $(if ($alive) { 'PASS' } else { 'FAIL' }), $alive)
Stop-App $app
if (-not $alive) { exit 1 }
