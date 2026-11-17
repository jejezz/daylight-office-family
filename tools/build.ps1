# Assemble build\app = pristine upstream + patches\**\*.patch + overlay\ + brand step (tools\brand\apply.ps1).
# The upstream tree itself is never modified.
# The tree is built in build\app.new and swapped in only when every step succeeded, so a failed build never
# leaves a half-built build\app behind (a half-built tree makes the app fail with "kernel.dll" errors).
param(
  [string]$Version = '10.0.0.169'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$up = Join-Path $root ("external\upstream-" + $Version)
$app = Join-Path $root 'build\app'
$stage = Join-Path $root 'build\app.new'
$old = Join-Path $root 'build\app.old'
if (-not (Test-Path $up)) { throw "upstream tree not found: $up (run tools\prepare-upstream.ps1)" }
$git = (Get-Command git -ErrorAction Stop).Source
Set-Location $root

function Remove-Tree([string]$Path) {
  # a few retries: a freshly written tree can be locked for a moment by a virus scanner
  foreach ($try in 1..5) {
    if (-not (Test-Path $Path)) { return $true }
    Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $Path)) { return $true }
    Start-Sleep -Seconds 2
  }
  return (-not (Test-Path $Path))
}

# running copies of the app would lock files
Get-Process editors, editors_helper, DesktopEditors -ErrorAction SilentlyContinue |
  Where-Object { $pp = $_.Path; $pp -and ($pp.StartsWith($app + '\') -or $pp.StartsWith($stage + '\')) } | Stop-Process -Force
Start-Sleep -Milliseconds 500
if (-not (Remove-Tree $stage)) { throw "cannot remove $stage (something holds it; close programs that use it)" }
if (-not (Remove-Tree $old)) { throw "cannot remove $old (something holds it)" }

# 1. fresh copy of the upstream tree
New-Item -ItemType Directory -Force $stage | Out-Null
Write-Host "copy upstream -> build\app.new"
robocopy $up $stage /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }

# 2. patches (git apply works on plain directories; --directory is relative to the repo root)
$patches = @(Get-ChildItem (Join-Path $root 'patches') -Recurse -Filter *.patch -ErrorAction SilentlyContinue | Sort-Object FullName)
foreach ($p in $patches) {
  $rel = $p.FullName.Substring($root.Length + 1)
  & $git apply -p1 --directory=build/app.new --whitespace=nowarn $p.FullName
  if ($LASTEXITCODE -ne 0) { throw "patch failed: $rel" }
  Write-Host "patched: $rel"
}

# 3. overlay (files copied over the tree as they are)
$ov = Join-Path $root 'overlay'
if (Test-Path $ov) {
  $n = (Get-ChildItem $ov -Recurse -File | Where-Object { $_.Name -ne '.gitkeep' } | Measure-Object).Count
  if ($n -gt 0) {
    robocopy $ov $stage /E /XF .gitkeep /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "overlay copy failed ($LASTEXITCODE)" }
    Write-Host "overlay: $n file(s)"
  }
}

# 4. binary / identity step
$brand = Join-Path $PSScriptRoot 'brand\apply.ps1'
if (Test-Path $brand) { & $brand -App $stage }

# 4b. appearance: the Saturn palette written over the two built-in themes (tools\theme\palette.json)
$py = Get-Command python -ErrorAction Stop
$env:PYTHONIOENCODING = 'utf-8'
& $py.Source (Join-Path $PSScriptRoot 'theme\apply.py') --app $stage
if ($LASTEXITCODE -ne 0) { throw "theme\apply.py failed ($LASTEXITCODE)" }

# 4c. icons: Phosphor Duotone painted into the modern icon sheets (tools\icons\mapping.json)
& $py.Source (Join-Path $PSScriptRoot 'icons\apply.py') --app $stage
if ($LASTEXITCODE -ne 0) { throw "icons\apply.py failed ($LASTEXITCODE)" }

# 5. build record
$lines = @("upstream_version=$Version", ("built_at=" + (Get-Date -Format 's')))
if (Test-Path (Join-Path $root '.git')) {
  $head = & $git rev-parse --verify -q --short HEAD
  if ($LASTEXITCODE -eq 0) { $lines += "repo_commit=$head" }
}
foreach ($p in $patches) {
  $lines += ("patch={0} sha256={1}" -f $p.Name, (Get-FileHash $p.FullName -Algorithm SHA256).Hash.ToLower())
}
[IO.File]::WriteAllLines((Join-Path $stage 'BUILD-INFO.txt'), $lines)

# 6. swap: rename the old tree away first (a rename fails cleanly if something holds it, leaving build\app intact)
if (Test-Path $app) {
  try { Rename-Item $app 'app.old' -ErrorAction Stop }
  catch { throw "cannot replace build\app (something holds it); the new build stays in build\app.new" }
}
Rename-Item $stage 'app'
[void](Remove-Tree $old)
Write-Host ("OK: build\app ready ({0} patch(es))" -f $patches.Count)
