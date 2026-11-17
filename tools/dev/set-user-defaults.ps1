# Dev helper: sets the per-user defaults the installer will set later (M6), e.g. the UI language.
# The app reads them from HKCU\Software\<name>\DesktopEditors (REG_SZ). Without it the UI language follows Windows.
# Usage: powershell -ExecutionPolicy Bypass -File tools\dev\set-user-defaults.ps1 [-Locale ko-KR]
param([string]$Locale = 'ko-KR')
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$name = (Get-Content (Join-Path $root 'tools\brand\brand.json') -Raw -Encoding UTF8 | ConvertFrom-Json).name
$key = "HKCU:\Software\$name\DesktopEditors"
New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name 'locale' -Value $Locale -Type String
Write-Host "set $key locale = $Locale"
