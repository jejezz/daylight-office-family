# Korean typing in table cells: types a Hangul word into each cell of a 3x3 table (Tab between cells), then copies all
# text (Ctrl+A, Ctrl+C) and compares the tokens with what was typed. Real keyboard input and your clipboard (restored).
# Do not touch keyboard or mouse while this runs.
# Usage: powershell -ExecutionPolicy Bypass -File tests\korean-table.ps1 [-Which build|upstream]
param([int]$KeyDelayMs = 40, [ValidateSet('build', 'upstream')][string]$Which = 'build')
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
if ($Which -eq 'upstream') { $app = (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName }
$doc = Join-Path $PSScriptRoot 'data\table.docx'
function U([int[]]$c) { -join ([char[]]$c) }
$w1 = U 0xC548, 0xB155, 0xD558, 0xC138, 0xC694   # annyeonghaseyo
$w2 = U 0xAC00, 0xB098, 0xB2E4, 0xB77C           # ganadara
$w3 = U 0xB300, 0xD55C, 0xBBFC, 0xAD6D           # daehanminguk
$items = @(@($w1, 'dkssudgktpdy'), @($w2, 'rkskekfk'), @($w3, 'eogksalsrnr'))
$oldClip = $null
try { $oldClip = Get-Clipboard -Raw } catch { }
function Chord([byte]$mod, [byte]$vk) {
  [DaylightUi]::keybd_event($mod, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60
  [DaylightUi]::Key($vk, 300)
  [DaylightUi]::keybd_event($mod, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200
}
Stop-App $app
Start-App $app @('--lang=ko-KR', '--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*table*' 60
if (-not $w) { Write-Host 'FAIL  app did not start'; exit 1 }
Focus-AppWindow $w.Process
Start-Sleep -Seconds 12
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 640, $r.T + 600)   # empty page area below the table: focus the document
[DaylightUi]::Key(0x24, 200)                  # Home
Chord 0x11 0x24                               # Ctrl+Home: first cell
[DaylightUi]::Key(0x15, 400)                  # Hangul key: assumes the IME starts in English mode
$expected = @()
for ($i = 0; $i -lt 9; $i++) {
  $it = $items[$i % 3]
  Press-Keys $it[1] $KeyDelayMs
  $expected += $it[0]
  if ($i -lt 8) { [DaylightUi]::Key(0x09, 150) }   # Tab: next cell
}
Start-Sleep -Milliseconds 500
Set-Clipboard -Value 'x'
Chord 0x11 0x41; Chord 0x11 0x43
Start-Sleep -Milliseconds 500
$text = Get-Clipboard -Raw
Save-WindowShot $w.Process (Join-Path $root 'build\shots\korean-table.png')
$tokens = @($text -split '\s+' | Where-Object { $_ -ne '' })
$good = 0
for ($i = 0; $i -lt 9; $i++) { if ($i -lt $tokens.Count -and $tokens[$i] -eq $expected[$i]) { $good++ } }
$esc = $tokens | ForEach-Object { -join ($_.ToCharArray() | ForEach-Object { if ([int]$_ -lt 128) { [string]$_ } else { '\u{0:X4}' -f [int]$_ } }) }
Write-Host ('tokens: ' + ($esc -join ' | '))
$ok = ($good -eq 9 -and $tokens.Count -eq 9)
Write-Host ('{0}  {1}/9 cells match, {2} tokens in the document text' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $good, $tokens.Count)
[DaylightUi]::Key(0x15, 300)
Stop-App $app
if ($null -ne $oldClip) { try { Set-Clipboard -Value $oldClip } catch { } }
if (-not $ok) { exit 1 }
