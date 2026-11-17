# Hanja reconversion comparison: original upstream copy vs the Daylight build, same keys, same document.
# Types Korean via the IME, selects the word and presses the Hanja key, then captures the WHOLE screen (the candidate
# window is a separate top-level window). Real keyboard input: do not touch keyboard or mouse while this runs.
# Usage: powershell -ExecutionPolicy Bypass -File tests\hanja.ps1 [-Which upstream|build|both] [-SwitchKey hangul|none]
param([ValidateSet('upstream', 'build', 'both')][string]$Which = 'both', [ValidateSet('hangul', 'none')][string]$SwitchKey = 'hangul')
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
$doc = Join-Path $root 'tests\data\hello.docx'
$targets = @()
if ($Which -ne 'build') { $targets += , @('upstream', (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName) }
if ($Which -ne 'upstream') { $targets += , @('build', (Join-Path $root 'build\app')) }
function Shot-Screen([string]$path) {
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $bm = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bm)
  $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bm.Size)
  $bm.Save($path, [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bm.Dispose()
}
foreach ($t in $targets) {
  $name = $t[0]; $app = $t[1]
  Stop-App $app
  Start-App $app @('--single-window-app', ('"' + $doc + '"'))
  $w = Wait-AppWindow $app '*hello*' 60
  if (-not $w) { Write-Host "FAIL: $name did not start"; continue }
  Focus-AppWindow $w.Process
  Start-Sleep -Seconds 14
  $r = Get-WindowRect $w.Process
  [DaylightUi]::Click($r.L + 640, $r.T + 352)          # end of the third text line
  [DaylightUi]::Key(0x23, 200)                         # End
  [DaylightUi]::Key(0x0D, 200)                         # Enter: new empty line
  if ($SwitchKey -eq 'hangul') { [DaylightUi]::Key(0x15, 400) }
  Press-Keys 'gksrmf' 120                              # Korean 'han-geul' when the IME is in Hangul mode
  [DaylightUi]::Key(0x20, 400)                         # space commits the syllables
  Shot-Screen (Join-Path $root "build\shots\hanja-$name-1-typed.png")
  # select the typed word with a double click (arrow keys need the extended-key flag, so avoid them)
  $cx = $r.L + 333; $cy = $r.T + 366
  [void][DaylightUi]::SetCursorPos($cx, $cy); Start-Sleep -Milliseconds 300
  foreach ($i in 1, 2) { [DaylightUi]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); [DaylightUi]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 80 }
  Shot-Screen (Join-Path $root "build\shots\hanja-$name-1b-selected.png")
  Start-Sleep -Milliseconds 400
  [DaylightUi]::Key(0x19, 1200)                        # Hanja key on the selected word
  Shot-Screen (Join-Path $root "build\shots\hanja-$name-2-hanja.png")
  Stop-App $app
  Write-Host "$name done"
}
