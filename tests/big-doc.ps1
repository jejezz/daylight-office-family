# Big document speed check: generates build\testdata\big.docx (about 400 pages, 40 noisy PNG images, 31 MB) with
# tests\make-bigdoc.py, opens it and reports: time until the first page text is visible, memory, time for Ctrl+End to
# reach the last page, 10 typed letters at the end (screenshot), and how long copying everything (Ctrl+A, Ctrl+C) takes. Needs Python with Pillow. Real keyboard input and your clipboard (restored): do not touch them.
# Usage: powershell -ExecutionPolicy Bypass -File tests\big-doc.ps1 [-Which build|upstream] [-Pages 400]
param([ValidateSet('build', 'upstream')][string]$Which = 'build', [int]$Pages = 400)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
if ($Which -eq 'upstream') { $app = (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName }
$doc = Join-Path $root 'build\testdata\big.docx'
if (-not (Test-Path $doc)) { python (Join-Path $PSScriptRoot 'make-bigdoc.py') $Pages }
$oldClip = $null
try { $oldClip = Get-Clipboard -Raw } catch { }
function Chord([byte]$mod, [byte]$vk) {
  [DaylightUi]::keybd_event($mod, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60
  [DaylightUi]::Key($vk, 300)
  [DaylightUi]::keybd_event($mod, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200
}
function Mem-MB { [math]::Round((Get-AppProcesses $app | Measure-Object WorkingSet64 -Sum).Sum / 1MB) }
# Region hash of the window (window-relative x,y,w,h).
function Region-Hash($p, [int]$x, [int]$y, [int]$w, [int]$h) {
  $r = Get-WindowRect $p
  $bmp = New-Object System.Drawing.Bitmap $w, $h
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L + $x, $r.T + $y, 0, 0, $bmp.Size)
  $ms = New-Object System.IO.MemoryStream
  $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
  $hh = [BitConverter]::ToString((New-Object Security.Cryptography.SHA256Managed).ComputeHash($ms.ToArray()))
  $g.Dispose(); $bmp.Dispose(); $ms.Dispose()
  $hh
}
# Number of dark pixels in the page text area (page is white in every theme): >30 means text is drawn.
function Dark-Pixels($p) {
  $r = Get-WindowRect $p
  $bmp = New-Object System.Drawing.Bitmap 500, 60
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L + 330, $r.T + 300, 0, 0, $bmp.Size)
  $n = 0
  for ($y = 0; $y -lt 60; $y += 2) { for ($x = 0; $x -lt 500; $x += 2) { $c = $bmp.GetPixel($x, $y); if (($c.R + $c.G + $c.B) -lt 200) { $n++ } } }
  $g.Dispose(); $bmp.Dispose()
  $n
}
Stop-App $app
$sw = [Diagnostics.Stopwatch]::StartNew()
Start-App $app @('--lang=ko-KR', '--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*big*' 90
if (-not $w) { Write-Host 'FAIL  app did not start'; exit 1 }
$tTitle = [math]::Round($sw.Elapsed.TotalSeconds, 1)
Focus-AppWindow $w.Process
$tText = $null
while ($sw.Elapsed.TotalSeconds -lt 240) { if ((Dark-Pixels $w.Process) -gt 30) { $tText = [math]::Round($sw.Elapsed.TotalSeconds, 1); break }; Start-Sleep -Milliseconds 500 }
Write-Host ('window title after {0} s, first page text visible after {1} s, memory {2} MB' -f $tTitle, $tText, (Mem-MB))
if (-not $tText) { Save-WindowShot $w.Process (Join-Path $root "build\shots\big-$Which-notext.png"); Write-Host 'FAIL  no text within 240 s'; Stop-App $app; exit 1 }
Start-Sleep -Seconds 10
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 640, $r.T + 400)
# Ctrl+End: time until the status bar page indicator stops changing (bottom-left strip).
$h0 = Region-Hash $w.Process 0 712 130 30
$s2 = [Diagnostics.Stopwatch]::StartNew()
Chord 0x11 0x23
$changed = $null; $prev = $null; $stable = $null
while ($s2.Elapsed.TotalSeconds -lt 60) {
  $h = Region-Hash $w.Process 0 712 130 30
  if ($null -eq $changed -and $h -ne $h0) { $changed = [math]::Round($s2.Elapsed.TotalSeconds, 1) }
  if ($null -ne $changed -and $h -eq $prev) { $stable = [math]::Round($s2.Elapsed.TotalSeconds, 1); break }
  $prev = $h; Start-Sleep -Milliseconds 400
}
Write-Host ('Ctrl+End: page indicator changed after {0} s, settled after {1} s, memory {2} MB' -f $changed, $stable, (Mem-MB))
Save-WindowShot $w.Process (Join-Path $root "build\shots\big-$Which-last.png")
# Type 10 letters at the end (English mode assumed); the screenshot shows them (look at it).
$s3 = [Diagnostics.Stopwatch]::StartNew()
Press-Keys 'zzzzzzzzzz' 40
Start-Sleep -Milliseconds 800
Save-WindowShot $w.Process (Join-Path $root ("build\shots\big-" + $Which + "-typed.png"))
Write-Host ('typed 10 letters, screen updated; memory {0} MB' -f (Mem-MB))
# Copy everything (Ctrl+A, Ctrl+C) of the whole 400-page document: informational, 90 s limit.
Set-Clipboard -Value 'x'
$s4 = [Diagnostics.Stopwatch]::StartNew()
Chord 0x11 0x41; Chord 0x11 0x43
$text = $null
while ($s4.Elapsed.TotalSeconds -lt 90) { $t = Get-Clipboard -Raw; if ($t -and $t.Length -gt 10) { $text = $t; break }; Start-Sleep -Milliseconds 500 }
if ($text) { Write-Host ('Ctrl+A, Ctrl+C: {0} s, {1} characters, tail has the typed letters: {2}' -f [math]::Round($s4.Elapsed.TotalSeconds, 1), $text.Length, $text.TrimEnd().EndsWith('zzzzzzzzzz')) }
else { Write-Host 'Ctrl+A, Ctrl+C: nothing on the clipboard within 90 s' }
$alive = [bool](Get-AppWindow $app)
Write-Host ('{0}  app running: {1}, memory now {2} MB' -f $(if ($alive) { 'PASS' } else { 'FAIL' }), $alive, (Mem-MB))
$ok = $alive
Stop-App $app
if ($null -ne $oldClip) { try { Set-Clipboard -Value $oldClip } catch { } }
if (-not $ok) { exit 1 }
