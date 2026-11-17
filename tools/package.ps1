# Packages build\app into dist\: Daylight-Setup-<ver>.exe (Inno Setup) and Daylight-<ver>-portable.zip, plus SHA-256 sums.
# Usage (repo root): powershell -ExecutionPolicy Bypass -File tools\package.ps1 [-Version 0.1.0] [-NoZip]
param([string]$Version = '0.1.0', [switch]$NoZip)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$app = Join-Path $root 'build\app'
$dist = Join-Path $root 'dist'
$iscc = Join-Path $root 'external\innosetup\ISCC.exe'
if (-not (Test-Path (Join-Path $app 'DesktopEditors.exe'))) { throw 'build\app missing: run tools\build.ps1 first' }
if (-not (Test-Path $iscc)) { throw 'external\innosetup\ISCC.exe missing (Inno Setup 6, see docs/PROGRESS.md M6)' }
New-Item -ItemType Directory -Force $dist | Out-Null
& $iscc "/DAppVersion=$Version" "/DSourceDir=$app" "/DOutDir=$dist" (Join-Path $PSScriptRoot 'installer\daylight.iss')
if ($LASTEXITCODE -ne 0) { throw "ISCC failed ($LASTEXITCODE)" }
if (-not $NoZip) {
  $zip = Join-Path $dist "Daylight-$Version-portable.zip"
  if (Test-Path $zip) { Remove-Item $zip }
  Compress-Archive -Path (Join-Path $app '*') -DestinationPath $zip -CompressionLevel Optimal
}
Get-ChildItem $dist -File | ForEach-Object { '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name } | Set-Content (Join-Path $dist 'SHA256SUMS.txt') -Encoding ASCII
Get-ChildItem $dist | Select-Object Name, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } }
