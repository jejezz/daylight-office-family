# Brand step of tools\build.ps1: string/logo/icon patches (apply.py) + PE icon resources (Windows API).
param([Parameter(Mandatory)][string]$App)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$py = Get-Command python -ErrorAction Stop
$env:PYTHONIOENCODING = 'utf-8'

& $py.Source (Join-Path $PSScriptRoot 'apply.py') --app $App
if ($LASTEXITCODE -ne 0) { throw "brand\apply.py failed ($LASTEXITCODE)" }

# Explorer / window icon of the executables: only the application icon group (101); the file-type icons are left alone.
$ico = Join-Path $root 'build\brand\app.ico'
$tool = Join-Path $root 'tools\win\replace-exe-icon.ps1'
foreach ($exe in 'editors.exe', 'DesktopEditors.exe') {
  # a freshly written exe can be locked for a moment (antivirus scan), so retry a few times
  $ok = $false
  foreach ($try in 1..4) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $tool -Exe (Join-Path $App $exe) -Ico $ico -OnlyGroup 101
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Write-Host "icon step for $exe failed (try $try), retrying"
    Start-Sleep -Seconds 3
  }
  if (-not $ok) { throw "icon replacement failed for $exe" }
}
# File-type icons (the 72 other icon groups of DesktopEditors.exe): one generated icon per document type.
$types = Join-Path $root 'build\brand\types'
& $py.Source (Join-Path $PSScriptRoot 'make_type_icons.py') --out $types
if ($LASTEXITCODE -ne 0) { throw "make_type_icons.py failed ($LASTEXITCODE)" }
$ok = $false
foreach ($try in 1..4) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tool -Exe (Join-Path $App 'DesktopEditors.exe') -MapFile (Join-Path $types 'map.json')
  if ($LASTEXITCODE -eq 0) { $ok = $true; break }
  Write-Host "file-type icon step failed (try $try), retrying"
  Start-Sleep -Seconds 3
}
if (-not $ok) { throw "file-type icon replacement failed" }
Write-Host "brand step done"
