# Prepare the pristine upstream tree under external\upstream-<version>.
#
# One-time step on each PC:
#   1. Install the pinned official installer (see upstream.txt: installer_sha256) normally.
#      The installer file name and size are in upstream.txt; verify its SHA-256 before running it.
#   2. Run this script. It copies the installed folder into external\ and verifies every
#      file against upstream\<version>.sha256 (use -Full), or the key files only (default).
#
# The installed copy is never modified. All later steps work on the copy.
param(
  [string]$Source = 'C:\Program Files\ONLYOFFICE\DesktopEditors',
  [string]$Version = '10.0.0.169',
  [switch]$Full
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$dst = Join-Path $root ("external\upstream-" + $Version)
$manifestPath = Join-Path $root ("upstream\" + $Version + ".sha256")
if (-not (Test-Path $manifestPath)) { throw "manifest not found: $manifestPath" }

if (-not (Test-Path $dst)) {
  $exe = Join-Path $Source 'DesktopEditors.exe'
  if (-not (Test-Path $exe)) { throw "source not found: $Source (install the pinned installer first)" }
  $installed = (Get-Item $exe).VersionInfo.ProductVersion
  if ($installed -ne $Version) { throw "installed version is $installed but $Version is required" }
  Write-Host "copying $Source -> $dst"
  robocopy $Source $dst /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
} else {
  Write-Host "already present: $dst"
}

$entries = Get-Content $manifestPath | ForEach-Object {
  $p = $_ -split '  ', 2
  [pscustomobject]@{ Hash = $p[0]; Path = $p[1] }
}
$count = (Get-ChildItem $dst -Recurse -File | Measure-Object).Count
Write-Host ("files: {0} (manifest: {1})" -f $count, $entries.Count)
$bad = @()
if ($count -ne $entries.Count) { $bad += "file count differs" }

$key = @('DesktopEditors.exe', 'editors.exe', 'ascdocumentscore.dll', 'libcef.dll', 'index.html',
         'editors/web-apps/apps/documenteditor/main/app/controller/Toolbar.js',
         'editors/web-apps/apps/common/main/lib/controller/LayoutManager.js')
$check = if ($Full) { $entries } else { $entries | Where-Object { $key -contains $_.Path } }
foreach ($e in $check) {
  $f = Join-Path $dst ($e.Path -replace '/', '\')
  if (-not (Test-Path $f)) { $bad += "missing: $($e.Path)"; continue }
  $h = (Get-FileHash $f -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $e.Hash) { $bad += "hash differs: $($e.Path)" }
}
if ($bad.Count -gt 0) { $bad | ForEach-Object { Write-Host "FAIL: $_" }; exit 1 }
Write-Host ("OK: {0} file(s) verified ({1})" -f @($check).Count, $(if ($Full) { 'full' } else { 'key files' }))
exit 0   # robocopy leaves exit code 1 (= files copied) in $LASTEXITCODE; callers must see success as 0
