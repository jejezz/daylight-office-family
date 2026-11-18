# Typing latency check: opens a document, goes to its end, starts a new line and types 30 wide letters ("W") one at a
# time (400 ms apart). For every key it polls the page area until the number of dark pixels grows, and reports the
# time from the key press to that change (includes about 10 ms of screen capture). The caret blink adds only a few
# dark pixels, so a growth of more than 12 counts as "the letter is on screen".
# Usage: powershell -ExecutionPolicy Bypass -File tests\edit-latency.ps1 [-Which build|upstream] [-Doc hello|long|big]
# Real keyboard input: do not touch keyboard or mouse while it runs. ASCII only (Windows PowerShell 5.1).
param([ValidateSet('build', 'upstream')][string]$Which = 'build', [ValidateSet('hello', 'long', 'big')][string]$Doc = 'hello', [int]$Keys = 30)
# Per-monitor DPI aware, so window and screen coordinates are real pixels on every monitor.
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class LatDpi { [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr c); }
'@
[void][LatDpi]::SetProcessDpiAwarenessContext([IntPtr]-4)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
Add-Type -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Imaging;
public static class DarkCount {
  public static int Count(int x, int y, int w, int h) {
    using (Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb)) {
      using (Graphics g = Graphics.FromImage(bmp)) { g.CopyFromScreen(x, y, 0, 0, bmp.Size); }
      BitmapData d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
      int n = 0;
      unsafe_free(d, w, h, ref n);
      bmp.UnlockBits(d);
      return n;
    }
  }
  static void unsafe_free(BitmapData d, int w, int h, ref int n) {
    byte[] row = new byte[d.Stride];
    for (int y = 0; y < h; y += 1) {
      System.Runtime.InteropServices.Marshal.Copy(new IntPtr(d.Scan0.ToInt64() + (long)y * d.Stride), row, 0, d.Stride);
      for (int x = 0; x < w; x += 1) { int i = x * 4; if (row[i] + row[i + 1] + row[i + 2] < 300) n++; }
    }
  }
}
'@ -ReferencedAssemblies System.Drawing
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class LatWin { [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int hh, uint f); }
'@
$app = Join-Path $root 'build\app'
if ($Which -eq 'upstream') { $app = (Get-ChildItem (Join-Path $root 'external') -Directory -Filter 'upstream-*' | Select-Object -First 1).FullName }
$docPath = switch ($Doc) { 'hello' { Join-Path $root 'tests\data\hello.docx' } 'long' { Join-Path $root 'tests\data\long.docx' } 'big' { Join-Path $root 'build\testdata\big.docx' } }
if (-not (Test-Path $docPath)) { Write-Host "FAIL  missing $docPath (big: python tests\make-bigdoc.py 400)"; exit 1 }
$stem = [IO.Path]::GetFileNameWithoutExtension($docPath)
function Chord([byte]$mod, [byte]$vk) {
  [DaylightUi]::keybd_event($mod, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60
  [DaylightUi]::Key($vk, 300)
  [DaylightUi]::keybd_event($mod, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200
}
Stop-App $app
Start-App $app @('--lang=ko-KR', '--single-window-app', ('"' + $docPath + '"'))
$w = Wait-AppWindow $app ("*" + $stem + "*") 90
if (-not $w) { Write-Host 'FAIL  app did not start'; exit 1 }
Start-Sleep -Seconds 4
# The app reopens where it was last (maybe on a monitor with another scale): put it on the primary screen at 1216x986.
[void][LatWin]::SetWindowPos($w.Process.MainWindowHandle, [IntPtr]::Zero, 40, 40, 1216, 986, 0x14)
Start-Sleep -Seconds 4
[void][LatWin]::SetWindowPos($w.Process.MainWindowHandle, [IntPtr]::Zero, 40, 40, 1216, 986, 0x14)
Start-Sleep -Seconds 4
Focus-AppWindow $w.Process
$sw = [Diagnostics.Stopwatch]::StartNew()
$ready = $false
while ($sw.Elapsed.TotalSeconds -lt 120) {
  $r = Get-WindowRect $w.Process
  if ([DarkCount]::Count($r.L + 330, $r.T + 300, 500, 60) -gt 30) { $ready = $true; break }
  Start-Sleep -Milliseconds 500
}
if (-not $ready) { Write-Host 'FAIL  page text never appeared'; Stop-App $app; exit 1 }
Start-Sleep -Seconds 10
$r = Get-WindowRect $w.Process
[DaylightUi]::Click($r.L + 640, $r.T + 400)
Chord 0x11 0x23           # Ctrl+End
$t = [Diagnostics.Stopwatch]::StartNew()
Start-Sleep -Seconds 4    # let the end of the document settle
[DaylightUi]::Key(0x0D, 800)   # Enter: new empty line
$x = $r.L + 120; $y = $r.T + 290; $cw = 980; $ch = 655
$lat = @()
foreach ($i in 1..$Keys) {
  $before = [DarkCount]::Count($x, $y, $cw, $ch)
  $sw2 = [Diagnostics.Stopwatch]::StartNew()
  [DaylightUi]::keybd_event(0x10, 0, 0, [UIntPtr]::Zero)   # Shift for an upper-case W
  [DaylightUi]::keybd_event(0x57, 0x11, 0, [UIntPtr]::Zero)
  [DaylightUi]::keybd_event(0x57, 0x11, 2, [UIntPtr]::Zero)
  [DaylightUi]::keybd_event(0x10, 0, 2, [UIntPtr]::Zero)
  $seen = $null
  while ($sw2.Elapsed.TotalSeconds -lt 3) {
    if (([DarkCount]::Count($x, $y, $cw, $ch) - $before) -gt 12) { $seen = $sw2.Elapsed.TotalMilliseconds; break }
  }
  $lat += $(if ($seen) { [math]::Round($seen) } else { 3000 })
  Start-Sleep -Milliseconds 400
}
$mem = [math]::Round((Get-AppProcesses $app | Measure-Object WorkingSet64 -Sum).Sum / 1MB)
Save-WindowShot $w.Process (Join-Path $root "build\shots\latency-$Which-$Doc.png")
$s = $lat | Sort-Object
$med = $s[[int]($s.Count / 2)]; $p90 = $s[[int]([math]::Floor($s.Count * 0.9)) - 1]
Write-Host ("{0,-8} {1,-5} keys={2} median={3} ms  p90={4} ms  max={5} ms  misses(>=3000)={6}  mem={7} MB" -f $Which, $Doc, $s.Count, $med, $p90, $s[-1], @($lat | Where-Object { $_ -ge 3000 }).Count, $mem)
Write-Host ("  all: " + ($lat -join ' '))
Stop-App $app
