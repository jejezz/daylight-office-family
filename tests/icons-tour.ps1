# Review tool (not a pass/fail test): opens a new document of one kind, visits every ribbon tab and stacks the ribbon
# strips of all tabs into one PNG, so icon changes can be reviewed on one picture.
# Usage: powershell -ExecutionPolicy Bypass -File tests\icons-tour.ps1 -Kind word|cell|slide [-Out <png>]
# Tab positions are fixed pixel offsets (default window size, English UI). Clicks go only to the ribbon tab row and are
# checked by the tab underline (Click-Tab), so nothing in the document can be hit by accident.
param(
  [ValidateSet('word', 'cell', 'slide')][string]$Kind = 'word',
  [string]$Out = ''
)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$tabs = @{
  word  = @(@('Home', 98), @('Insert', 156), @('Layout', 215), @('References', 290), @('Collaboration', 383), @('Protection', 475), @('View', 543))
  cell  = @(@('Home', 98), @('Insert', 156), @('Layout', 215), @('Formula', 281), @('Data', 343), @('Collaboration', 419), @('Protection', 511), @('View', 579))
  slide = @(@('Home', 98), @('Insert', 156), @('Design', 216), @('Transitions', 290), @('Animation', 363), @('Collaboration', 467), @('View', 626))
}
$flag = @{ word = '--new:word'; cell = '--new:cell'; slide = '--new:slide' }
$title = @{ word = '*docx*'; cell = '*xlsx*'; slide = '*pptx*' }
if (-not $Out) { $Out = Join-Path $root ("build\shots\tour-" + $Kind + ".png") }
Add-Type -AssemblyName System.Drawing
Stop-App $app
Start-App $app @('--single-window-app', $flag[$Kind])
$w = Wait-AppWindow $app $title[$Kind] 60
if (-not $w) { Write-Host 'FAIL: app did not start'; exit 1 }
Focus-AppWindow $w.Process
Start-Sleep -Seconds 14
$strips = @()
foreach ($t in $tabs[$Kind]) {
  if (-not (Click-Tab $w.Process $t[1])) { Write-Host ("tab '{0}' could not be selected, skipped" -f $t[0]); continue }
  Start-Sleep -Milliseconds 600
  $tmp = Join-Path $root ("build\shots\tour-tmp.png")
  Save-WindowShot $w.Process $tmp
  $bm = [System.Drawing.Bitmap]::FromFile($tmp)
  $strip = $bm.Clone([System.Drawing.Rectangle]::new(0, 64, [math]::Min(1216, $bm.Width), 122), $bm.PixelFormat)
  $bm.Dispose()
  $g = [System.Drawing.Graphics]::FromImage($strip)
  $g.DrawString($t[0], (New-Object System.Drawing.Font('Segoe UI', 8)), [System.Drawing.Brushes]::Yellow, 2, 106)
  $g.Dispose()
  $strips += $strip
}
[void](Close-App $app)
$sheet = New-Object System.Drawing.Bitmap 1216, ($strips.Count * 124)
$g = [System.Drawing.Graphics]::FromImage($sheet)
$y = 0
foreach ($s in $strips) { $g.DrawImage($s, 0, $y); $y += 124; $s.Dispose() }
$g.Dispose()
New-Item -ItemType Directory -Force (Split-Path $Out -Parent) | Out-Null
$sheet.Save($Out); $sheet.Dispose()
Remove-Item (Join-Path $root 'build\shots\tour-tmp.png') -Force -ErrorAction SilentlyContinue
Write-Host ("saved {0} ({1} tabs)" -f $Out, $strips.Count)
