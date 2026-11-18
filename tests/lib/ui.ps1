# UI test helpers (Win32 + screenshots + keyboard). Dot-source this file: . tests\lib\ui.ps1
# ASCII only on purpose (Windows PowerShell 5.1 reads BOM-less files as ANSI).
# Do not touch the keyboard/mouse while a test that sends input is running.
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class DaylightUi {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rr, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern IntPtr GetClassLongPtr(IntPtr h, int i);
  public static void Key(byte vk, int ms) {
    keybd_event(vk, (byte)MapVirtualKey(vk, 0), 0, UIntPtr.Zero); System.Threading.Thread.Sleep(30);
    keybd_event(vk, (byte)MapVirtualKey(vk, 0), 2, UIntPtr.Zero); System.Threading.Thread.Sleep(ms);
  }
  public static void Click(int x, int y) {
    SetCursorPos(x, y); System.Threading.Thread.Sleep(250);
    mouse_event(2, 0, 0, 0, UIntPtr.Zero); mouse_event(4, 0, 0, 0, UIntPtr.Zero); System.Threading.Thread.Sleep(400);
  }
}
'@

# Processes of the app under test are matched by executable path, never by name only.
function Get-AppProcesses([string]$AppDir) {
  Get-Process editors, editors_helper, DesktopEditors -ErrorAction SilentlyContinue |
    Where-Object { $pp = $_.Path; $pp -and $pp.StartsWith($AppDir, [StringComparison]::OrdinalIgnoreCase) }
}
function Stop-App([string]$AppDir) {
  Get-AppProcesses $AppDir | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 800
}
# Graceful close (settings are written on a clean exit); falls back to killing after $TimeoutSec.
function Close-App([string]$AppDir, [int]$TimeoutSec = 10) {
  $p = Get-AppWindow $AppDir
  if ($p) { [void]$p.CloseMainWindow() }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec -and @(Get-AppProcesses $AppDir).Count -gt 0) { Start-Sleep -Milliseconds 300 }
  $left = @(Get-AppProcesses $AppDir).Count
  Stop-App $AppDir
  return ($left -eq 0)
}
function Start-App([string]$AppDir, [string[]]$AppArgs) {
  Start-Process -FilePath (Join-Path $AppDir 'DesktopEditors.exe') -ArgumentList $AppArgs | Out-Null
}
# Main window = the editors.exe process that has a window title.
function Get-AppWindow([string]$AppDir) {
  Get-Process editors -ErrorAction SilentlyContinue |
    Where-Object { $pp = $_.Path; $pp -and $pp.StartsWith($AppDir, [StringComparison]::OrdinalIgnoreCase) -and $_.MainWindowHandle -ne [IntPtr]::Zero } |
    Select-Object -First 1
}
function Wait-AppWindow([string]$AppDir, [string]$TitleLike, [int]$TimeoutSec = 60) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    $p = Get-AppWindow $AppDir
    if ($p) { $p.Refresh(); if ($p.MainWindowTitle -like $TitleLike) { return [pscustomobject]@{ Process = $p; Seconds = [math]::Round($sw.Elapsed.TotalSeconds, 1) } } }
    Start-Sleep -Milliseconds 200
  }
  return $null
}
function Focus-AppWindow($Process) {
  [void][DaylightUi]::ShowWindow($Process.MainWindowHandle, 9)
  [void][DaylightUi]::SetForegroundWindow($Process.MainWindowHandle)
  Start-Sleep -Milliseconds 500
}
function Get-WindowRect($Process) {
  $r = New-Object DaylightUi+R
  [void][DaylightUi]::GetWindowRect($Process.MainWindowHandle, [ref]$r)
  $r
}
# Captures only the app window region (never the whole screen) to a PNG file.
function Save-WindowShot($Process, [string]$Path) {
  $r = Get-WindowRect $Process
  $bmp = New-Object System.Drawing.Bitmap ($r.Rr - $r.L), ($r.B - $r.T)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  New-Item -ItemType Directory -Force (Split-Path $Path -Parent) | Out-Null
  $bmp.Save($Path)
  $g.Dispose(); $bmp.Dispose()
}
# SHA-256 of the top strip of the window (menu + ribbon); used to see whether a click changed the screen.
function Get-StripHash($Process, [int]$StripHeight = 190) {
  $r = Get-WindowRect $Process
  $bmp = New-Object System.Drawing.Bitmap ($r.Rr - $r.L), $StripHeight
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  $ms = New-Object System.IO.MemoryStream
  $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
  $h = [BitConverter]::ToString((New-Object Security.Cryptography.SHA256Managed).ComputeHash($ms.ToArray()))
  $g.Dispose(); $bmp.Dispose(); $ms.Dispose()
  $h
}
# True when the ribbon tab at window-relative x has its selection underline (a bright/accent line under the label,
# found by contrast with the toolbar background just below it).
function Test-TabSelected($Process, [int]$X) {
  $r = Get-WindowRect $Process
  $bmp = New-Object System.Drawing.Bitmap 1, 8
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  # rows 94..101 of the window: the underline (rows ~96-98) sits between the tab row and the ribbon (which starts at ~102);
  # the reference is the title-row color in the first row (it is colored per document type), not the ribbon.
  $g.CopyFromScreen($r.L + $X, $r.T + 94, 0, 0, $bmp.Size)
  $bg = $bmp.GetPixel(0, 0)
  $best = 0
  foreach ($y in 1..7) {
    $c = $bmp.GetPixel(0, $y)
    $d = [math]::Abs($c.R - $bg.R) + [math]::Abs($c.G - $bg.G) + [math]::Abs($c.B - $bg.B)
    if ($d -gt $best) { $best = $d }
  }
  $g.Dispose(); $bmp.Dispose()
  $best -gt 120
}
# Clicks a ribbon tab (window-relative x, y=82: the tab labels sit below the 40px title row) until its underline shows. It never clicks anywhere else.
function Click-Tab($Process, [int]$X, [int]$Tries = 4) {
  foreach ($i in 1..$Tries) {
    if (Test-TabSelected $Process $X) { return $true }
    $r = Get-WindowRect $Process
    Focus-AppWindow $Process
    [DaylightUi]::Click($r.L + $X, $r.T + 82)
    Start-Sleep -Seconds 2
  }
  return (Test-TabSelected $Process $X)
}
# Clicks at a window-relative position and retries (up to $Tries) until the top strip of the window changed.
function Click-Until-Changed($Process, [int]$X, [int]$Y, [int]$Tries = 3) {
  foreach ($i in 1..$Tries) {
    $before = Get-StripHash $Process
    $r = Get-WindowRect $Process
    Focus-AppWindow $Process
    [DaylightUi]::Click($r.L + $X, $r.T + $Y)
    Start-Sleep -Seconds 2
    if ((Get-StripHash $Process) -ne $before) { return $true }
  }
  return $false
}
# Waits until the top strip of the window (menu + ribbon) stops changing between two captures 1 s apart.
# Returns the seconds waited, or $null on timeout. The strip is used because the document caret blinks.
function Wait-WindowStable($Process, [int]$StripHeight = 190, [int]$TimeoutSec = 40) {
  $sw = [Diagnostics.Stopwatch]::StartNew(); $prev = $null
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    $r = Get-WindowRect $Process
    $bmp = New-Object System.Drawing.Bitmap ($r.Rr - $r.L), $StripHeight
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $hash = [BitConverter]::ToString((New-Object Security.Cryptography.SHA256Managed).ComputeHash($ms.ToArray()))
    $g.Dispose(); $bmp.Dispose(); $ms.Dispose()
    if ($prev -ne $null -and $hash -eq $prev) { return [math]::Round($sw.Elapsed.TotalSeconds, 1) }
    $prev = $hash
    Start-Sleep -Seconds 1
  }
  return $null
}
# Big window icon (WM_GETICON, ICON_BIG=1) as a 32x32 bitmap; returns the RGBA of its center pixel.
function Get-WindowIconCenter($Process) {
  $h = [DaylightUi]::SendMessage($Process.MainWindowHandle, 0x7F, [IntPtr]1, [IntPtr]::Zero)
  if ($h -eq [IntPtr]::Zero) { $h = [DaylightUi]::GetClassLongPtr($Process.MainWindowHandle, -14) }
  if ($h -eq [IntPtr]::Zero) { return $null }
  $bm = [System.Drawing.Icon]::FromHandle($h).ToBitmap()
  $c = $bm.GetPixel([int]($bm.Width / 2), [int]($bm.Height / 2))
  $bm.Dispose()
  $c
}
function Press-Keys([string]$Letters, [int]$DelayMs = 60) {
  foreach ($c in $Letters.ToCharArray()) { [DaylightUi]::Key([byte][char]::ToUpper($c), $DelayMs) }
}
