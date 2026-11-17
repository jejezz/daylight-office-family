# Contact sheet of the file-type icons inside an exe (default build\app\DesktopEditors.exe) for visual review.
# Usage: powershell -ExecutionPolicy Bypass -File tests\icons-sheet.ps1 [-Exe <path>] [-Out <png>] [-Size 64]
param(
  [string]$Exe = '',
  [string]$Out = '',
  [int]$Size = 64
)
$root = Split-Path $PSScriptRoot -Parent
if (-not $Exe) { $Exe = Join-Path $root 'build\app\DesktopEditors.exe' }
if (-not $Out) { $Out = Join-Path $root 'build\shots\file-type-icons.png' }
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class IconX {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern uint PrivateExtractIcons(string file, int index, int cx, int cy, IntPtr[] icons, uint[] ids, uint n, uint flags);
  [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr h);
}
'@
$table = (Get-Content (Join-Path $root 'tools\brand\filetypes.json') -Raw | ConvertFrom-Json).icons
$cols = 9; $cell = $Size + 36
$rows = [math]::Ceiling(($table.Count + 1) / $cols)
$bmp = New-Object System.Drawing.Bitmap ($cols * $cell), ($rows * $cell)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(40, 44, 52))
$font = New-Object System.Drawing.Font('Segoe UI', 9)
$brush = [System.Drawing.Brushes]::White
$items = @([pscustomobject]@{ index = 0; ext = 'app' }) + @($table)
$i = 0
foreach ($e in $items) {
  $h = New-Object IntPtr[] 1; $ids = New-Object uint32[] 1
  $n = [IconX]::PrivateExtractIcons($Exe, [int]$e.index, $Size, $Size, $h, $ids, 1, 0)
  $x = ($i % $cols) * $cell + 18; $y = [math]::Floor($i / $cols) * $cell + 6
  if ($n -ge 1 -and $h[0] -ne [IntPtr]::Zero) {
    $ic = [System.Drawing.Icon]::FromHandle($h[0]); $g.DrawIcon($ic, $x, $y); [void][IconX]::DestroyIcon($h[0])
  }
  $g.DrawString(("{0} ({1})" -f $e.ext, $e.index), $font, $brush, $x - 6, $y + $Size + 4)
  $i++
}
New-Item -ItemType Directory -Force (Split-Path $Out -Parent) | Out-Null
$bmp.Save($Out); $g.Dispose(); $bmp.Dispose()
Write-Host "saved $Out ($($items.Count) icons)"
