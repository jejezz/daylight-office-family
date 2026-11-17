# Brand test for build\app: icons, separate settings/data locations, static string checks, start-screen and About screenshots.
# Usage: powershell -ExecutionPolicy Bypass -File tests\brand.ps1
# It clicks inside the app window (start screen, About). Do not touch the mouse/keyboard while it runs.
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$cfg = Get-Content (Join-Path $root 'tools\brand\brand.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}
function Near($c, [int]$r, [int]$g, [int]$b, [int]$tol = 14) {
  $c -and ([math]::Abs($c.R - $r) -le $tol) -and ([math]::Abs($c.G - $g) -le $tol) -and ([math]::Abs($c.B - $b) -le $tol)
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$shots = Join-Path $root 'build\shots'

# --- static checks on the assembled tree
Check 'updatesvc.exe removed' (-not (Test-Path (Join-Path $app 'updatesvc.exe')))
$gone = @('9DC93CDB-B576-4F0C-B55E-FCC9C48DD007', '38E022EA-AD92-45FC-B22B-49DF39746DB4', '7327FC95-16DA-41D9-9AF2-0E7F449F6800', 'AA2EA9B6-9EC2-415F-9762-634EE8D9A95E')
Check 'online plugins removed' (@($gone | Where-Object { Test-Path (Join-Path $app ("editors\sdkjs-plugins\{" + $_ + "}")) }).Count -eq 0)
$html = [IO.File]::ReadAllText((Join-Path $app 'index.html'), [Text.Encoding]::UTF8)
$noticeStart = $cfg.notice.Substring(0, 20)
Check 'About notice present in index.html' ($html.Contains($noticeStart))
Check 'no "ONLYOFFICE Desktop Editors" left in index.html' (-not $html.Contains('ONLYOFFICE Desktop Editors'))
$ed = [IO.File]::ReadAllBytes((Join-Path $app 'editors.exe'))
$u16 = [Text.Encoding]::Unicode.GetString($ed)
Check 'update URL no longer points at the vendor' (-not $u16.Contains('download.onlyoffice.com/install/desktop'))
Check 'brand name present in editors.exe' ($u16.Contains($cfg.name))

# --- exe file icons (Explorer)
foreach ($e in 'editors.exe', 'DesktopEditors.exe') {
  $bm = [System.Drawing.Icon]::ExtractAssociatedIcon((Join-Path $app $e)).ToBitmap()
  $c = $bm.GetPixel(16, 16); $bm.Dispose()
  Check "file icon of $e is the new icon" (Near $c 245 184 46) ("center=({0},{1},{2})" -f $c.R, $c.G, $c.B)
}

# --- file-type icons inside DesktopEditors.exe: sample the colored band of two of them (index 7 = docx, 10 = xlsx)
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class IconProbe {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern uint PrivateExtractIcons(string file, int index, int cx, int cy, IntPtr[] icons, uint[] ids, uint n, uint flags);
  [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr h);
}
'@
function Get-TypeIconBand([string]$Exe, [int]$Index) {
  $h = New-Object IntPtr[] 1; $ids = New-Object uint32[] 1
  $n = [IconProbe]::PrivateExtractIcons($Exe, $Index, 64, 64, $h, $ids, 1, 0)
  if ($n -lt 1 -or $h[0] -eq [IntPtr]::Zero) { return $null }
  $bm = [System.Drawing.Icon]::FromHandle($h[0]).ToBitmap()
  $c = $bm.GetPixel(32, 34)   # colored band just above the lettering (band spans y = 32..51 of 64)
  $bm.Dispose(); [void][IconProbe]::DestroyIcon($h[0])
  $c
}
$de = Join-Path $app 'DesktopEditors.exe'
$c7 = Get-TypeIconBand $de 7
Check 'file-type icon docx (index 7) is blue' (Near $c7 59 125 221 20) $(if ($c7) { "band=({0},{1},{2})" -f $c7.R, $c7.G, $c7.B } else { 'no icon' })
$c10 = Get-TypeIconBand $de 10
Check 'file-type icon xlsx (index 10) is green' (Near $c10 46 158 91 20) $(if ($c10) { "band=({0},{1},{2})" -f $c10.R, $c10.G, $c10.B } else { 'no icon' })

# --- run the app: settings/data separation, window icon, screenshots
$legacy = Join-Path $env:LOCALAPPDATA 'ONLYOFFICE\DesktopEditors'
$legacyBefore = if (Test-Path $legacy) { (Get-Item $legacy).LastWriteTime } else { $null }
Stop-App $app
Start-App $app @('--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
Check 'app starts' ($null -ne $w)
if ($w) {
  Focus-AppWindow $w.Process
  [void](Wait-WindowStable $w.Process)
  Check "title ends with '$($cfg.name)'" ($w.Process.MainWindowTitle -like ('*' + $cfg.name)) $w.Process.MainWindowTitle
  $ic = Get-WindowIconCenter $w.Process
  Check 'window/taskbar icon is the new icon' (Near $ic 245 184 46) $(if ($ic) { "center=({0},{1},{2})" -f $ic.R, $ic.G, $ic.B } else { 'no icon' })
  Save-WindowShot $w.Process (Join-Path $shots "brand-$stamp-editor.png")
  # start screen: first tab, then About (bottom of the left rail)
  $r = Get-WindowRect $w.Process
  [DaylightUi]::Click($r.L + 65, $r.T + 17); Start-Sleep -Seconds 2
  Save-WindowShot $w.Process (Join-Path $shots "brand-$stamp-start.png")
  [DaylightUi]::Click($r.L + 47, $r.B - 48); Start-Sleep -Seconds 2
  Save-WindowShot $w.Process (Join-Path $shots "brand-$stamp-about.png")
}
$clean = Close-App $app
Check 'app exits cleanly when asked to close' $clean
Start-Sleep -Seconds 1
# the app only writes the DesktopEditors sub-key when a setting changes; the updater group is written on every start
Check 'settings key HKCU\Software\<name> exists (not the vendor key)' (Test-Path ("HKCU:\Software\" + $cfg.name))
Check 'data folder %LOCALAPPDATA%\<dataDir>\DesktopEditors exists' (Test-Path (Join-Path $env:LOCALAPPDATA ($cfg.dataDir + '\DesktopEditors')))
$legacyAfter = if (Test-Path $legacy) { (Get-Item $legacy).LastWriteTime } else { $null }
Check 'original ONLYOFFICE data folder untouched' ($legacyBefore -eq $legacyAfter)

$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed. Screenshots: build\shots\brand-{2}-*.png" -f $results.Count, $fail, $stamp)
exit $(if ($fail -eq 0) { 0 } else { 1 })
