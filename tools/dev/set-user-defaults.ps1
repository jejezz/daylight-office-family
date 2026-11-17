# Dev helper: writes the per-user setting the app stores in HKCU\Software\<name>\DesktopEditors (REG_SZ).
# NOTE (checked 2026-11-17): on this PC the UI stayed English with locale=ko-KR in the registry; the UI language follows
# the Windows display language, and --lang=ko-KR (this run) / --keeplang=ko-KR (kept) forces it. The registry value is
# kept here only because the original app stores it; do not rely on it for the family installer (use the command line).
# Usage: powershell -ExecutionPolicy Bypass -File tools\dev\set-user-defaults.ps1 [-Locale ko-KR]
param([string]$Locale = 'ko-KR')
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$name = (Get-Content (Join-Path $root 'tools\brand\brand.json') -Raw -Encoding UTF8 | ConvertFrom-Json).name
$key = "HKCU:\Software\$name\DesktopEditors"
New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name 'locale' -Value $Locale -Type String
Write-Host "set $key locale = $Locale"
