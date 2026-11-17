# Korean typing check: types a Hangul word many times through the IME into the document editor, then copies the whole
# text (Ctrl+A, Ctrl+C) and compares it with what was typed. Catches dropped or garbled syllables.
# Real keyboard input and your clipboard (restored afterwards): do not touch keyboard or mouse while this runs.
# Usage: powershell -ExecutionPolicy Bypass -File tests\korean-typing.ps1 [-Repeat 40]
param([int]$Repeat = 40, [int]$KeyDelayMs = 40, [ValidateSet('build', 'upstream')][string]$Which = 'build')
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
if ($Which -eq 'upstream') { $app = (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName }
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$word = -join ([char[]](0xC548, 0xB155, 0xD558, 0xC138, 0xC694))   # annyeonghaseyo
$keys = 'dkssudgktpdy'                                              # same word on a 2-beolsik keyboard
$oldClip = $null
try { $oldClip = Get-Clipboard -Raw } catch { }
function Chord([byte]$mod, [byte]$vk) {
  [DaylightUi]::keybd_event($mod, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60
  [DaylightUi]::Key($vk, 300)
  [DaylightUi]::keybd_event($mod, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200
}
function Type-Words([int]$n) {
  for ($i = 0; $i -lt $n; $i++) { Press-Keys $keys $KeyDelayMs; [DaylightUi]::Key(0x20, 60) }
}
function Read-AllText {
  Set-Clipboard -Value 'x'
  Chord 0x11 0x41   # Ctrl+A
  Chord 0x11 0x43   # Ctrl+C
  Start-Sleep -Milliseconds 500
  Get-Clipboard -Raw
}
Stop-App $app
Start-App $app @('--lang=ko-KR', '--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
if (-not $w) { Write-Host 'FAIL  app did not start'; exit 1 }
Focus-AppWindow $w.Process
Start-Sleep -Seconds 12
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 640, $r.T + 352)
[DaylightUi]::Key(0x23, 200)   # End
[DaylightUi]::Key(0x0D, 200)   # Enter
[DaylightUi]::Key(0x15, 400)   # Hangul key: assumes the IME starts in English mode
Type-Words $Repeat
$text = Read-AllText
$count = ([regex]::Matches($text, [regex]::Escape($word))).Count
$ascii = $text.Contains('dkssud')
if ($ascii) {
  Write-Host 'NOTE  got Latin letters: the IME was already in Hangul mode, so the key toggled it off. Run again.'
}
$ok = ($count -eq $Repeat)
$other = @($text -split '\s+' | Where-Object { $_ -ne '' -and $_ -ne $word } | Select-Object -Unique | Select-Object -First 30)
$esc = $other | ForEach-Object { -join ($_.ToCharArray() | ForEach-Object { if ([int]$_ -lt 128) { [string]$_ } else { '\u{0:X4}' -f [int]$_ } }) }
Write-Host ('other tokens: ' + ($esc -join ' | '))
Write-Host ('{0}  typed {1} x word, found {2} in the document text (length {3})' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $Repeat, $count, $text.Length)
[DaylightUi]::Key(0x15, 300)   # back to the previous IME mode
Stop-App $app
if ($null -ne $oldClip) { try { Set-Clipboard -Value $oldClip } catch { } }
if (-not $ok) { exit 1 }
