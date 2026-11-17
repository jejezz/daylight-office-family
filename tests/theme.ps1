# Theme test for build\app: static checks, then dark and light colors sampled from real screenshots, theme menu, start screen.
# Usage: powershell -ExecutionPolicy Bypass -File tests\theme.ps1 [-KeepData]
# It RESETS this product's user state first (registry key HKCU\Software\<name> and %LOCALAPPDATA%\<dataDir>, names from
# tools\brand\brand.json) so the first-run default theme is tested; -KeepData skips that.
# The window must be the default size and the UI language English (menu positions are fixed pixel offsets).
# It clicks inside the app window: do not touch the mouse/keyboard while it runs.
param([switch]$KeepData)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$brand = Get-Content (Join-Path $root 'tools\brand\brand.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pal = Get-Content (Join-Path $root 'tools\theme\palette.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}
function Hex($c) { '#{0:X2}{1:X2}{2:X2}' -f $c.R, $c.G, $c.B }
function Near($c, [string]$hex, [int]$tol = 3) {
  $e = [Convert]::ToInt32($hex.TrimStart('#'), 16)
  $r = ($e -shr 16) -band 255; $g = ($e -shr 8) -band 255; $b = $e -band 255
  ([math]::Abs($c.R - $r) -le $tol) -and ([math]::Abs($c.G - $g) -le $tol) -and ([math]::Abs($c.B - $b) -le $tol)
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$shots = Join-Path $root 'build\shots'
Add-Type -AssemblyName System.Drawing

# --- static checks
$pages = @('documenteditor', 'spreadsheeteditor', 'presentationeditor', 'pdfeditor', 'visioeditor') |
  ForEach-Object { Join-Path $app ("editors\web-apps\apps\" + $_ + "\main\index.html") }
$missing = @($pages | Where-Object { -not ((Get-Content $_ -Raw) -match 'id="daylight-theme"') })
Check 'theme CSS injected in every editor page' ($missing.Count -eq 0) ("pages=" + $pages.Count)
Check 'theme CSS injected in the start screen' ((Get-Content (Join-Path $app 'index.html') -Raw -Encoding UTF8) -match 'id="daylight-theme"')
$themesJs = Get-Content (Join-Path $app 'editors\web-apps\apps\common\main\lib\controller\Themes.js') -Raw
Check 'theme choices reduced to system/light/dark' ($themesJs -match "delete themes_map\['theme-gray'\]")

# --- run: first start with fresh user state (dark = the system mode on this PC; check the OS mode below)
Stop-App $app
if (-not $KeepData) {
  Remove-Item ("HKCU:\Software\" + $brand.name) -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item (Join-Path $env:LOCALAPPDATA $brand.dataDir) -Recurse -Force -ErrorAction SilentlyContinue
}
$osLight = (Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize' -ErrorAction SilentlyContinue).AppsUseLightTheme
$sysIsDark = ($osLight -eq 0)
Start-App $app @('--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
Check 'app starts' ($null -ne $w)
if (-not $w) { exit 1 }
Focus-AppWindow $w.Process
function Shot-Pixels($name) {
  Save-WindowShot $w.Process (Join-Path $shots ("theme-$stamp-$name.png"))
  [System.Drawing.Bitmap]::FromFile((Join-Path $shots ("theme-$stamp-$name.png")))
}
# wait until the toolbar pixel is no longer the loading skeleton / vendor gray (editor finished loading)
$expect = if ($sysIsDark) { $pal.dark } else { $pal.light }
$ok = $false
foreach ($i in 1..40) {
  $bm = Shot-Pixels 'poll'; $c = $bm.GetPixel(760, 100); $bm.Dispose()
  if (Near $c $expect.surface) { $ok = $true; break }
  Start-Sleep -Seconds 1
}
$mode = if ($sysIsDark) { 'dark' } else { 'light' }
$bm = Shot-Pixels "default-$mode"
Check "default theme follows the system ($mode)" $ok ("toolbar=" + (Hex $bm.GetPixel(760, 100)) + " expected " + $expect.surface)
Check 'canvas around the page' (Near $bm.GetPixel(120, 450) $expect.canvas) ((Hex $bm.GetPixel(120, 450)) + " expected " + $expect.canvas)
Check 'title strip inside the editor' (Near $bm.GetPixel(400, 48) $expect.bar) ((Hex $bm.GetPixel(400, 48)) + " expected " + $expect.bar)
Check 'native window background (editors.exe theme JSON)' (Near $bm.GetPixel(700, 14) $expect.surface) ((Hex $bm.GetPixel(700, 14)) + " expected " + $expect.surface)
$bm.Dispose()

# --- switch the theme through View > Interface Theme: menu = Same as system / Light / Dark
$viewOk = Click-Tab $w.Process 543                                         # View tab (checked by its underline)
Check 'View tab opens' $viewOk
$switched = $false
if ($viewOk) {
  # the Interface Theme button only exists on the View tab, so this click cannot hit a document command
  $r = Get-WindowRect $w.Process
  [DaylightUi]::Click($r.L + 517, $r.T + 148); Start-Sleep -Seconds 1
  Save-WindowShot $w.Process (Join-Path $shots "theme-$stamp-menu.png")
  $other = if ($sysIsDark) { 'light' } else { 'dark' }
  $otherY = if ($sysIsDark) { 211 } else { 237 }                          # Light / Dark entries of the menu
  [DaylightUi]::Click($r.L + 530, $r.T + $otherY); Start-Sleep -Seconds 3
  [void](Click-Tab $w.Process 98)                                         # back to Home
  $exp2 = if ($sysIsDark) { $pal.light } else { $pal.dark }
  $switched = $true
  $bm = Shot-Pixels "switched-$other"
  Check "switching to $other applies its palette" ((Near $bm.GetPixel(760, 100) $exp2.surface) -and (Near $bm.GetPixel(120, 450) $exp2.canvas)) ("toolbar=" + (Hex $bm.GetPixel(760, 100)) + " canvas=" + (Hex $bm.GetPixel(120, 450)))
  Check "native window follows the $other theme" (Near $bm.GetPixel(700, 14) $exp2.surface) ((Hex $bm.GetPixel(700, 14)) + " expected " + $exp2.surface)
  $bm.Dispose()
}

# --- start screen (first tab) in the current theme: the left rail uses the palette canvas color
$cur = if ($switched) { $exp2 } else { $expect }
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 65, $r.T + 17); Start-Sleep -Seconds 3
$bm = Shot-Pixels 'start'
$c = $bm.GetPixel(47, 400)
Check 'start screen left rail uses the palette canvas color' (Near $c $cur.canvas) ((Hex $c) + " expected " + $cur.canvas)
$bm.Dispose()
[void](Close-App $app)
Get-ChildItem $shots -Filter "theme-$stamp-poll.png" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed. Screenshots: build\shots\theme-{2}-*.png" -f $results.Count, $fail, $stamp)
exit $(if ($fail -eq 0) { 0 } else { 1 })
