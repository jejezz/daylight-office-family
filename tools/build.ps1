# Assemble build\app = pristine upstream + patches\**\*.patch + overlay\ (+ optional tools\brand\apply.ps1).
# The upstream tree itself is never modified.
param(
  [string]$Version = '10.0.0.169'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$up = Join-Path $root ("external\upstream-" + $Version)
$app = Join-Path $root 'build\app'
if (-not (Test-Path $up)) { throw "upstream tree not found: $up (run tools\prepare-upstream.ps1)" }
$git = (Get-Command git -ErrorAction Stop).Source
Set-Location $root

# 1. fresh copy of the upstream tree
if (Test-Path $app) {
  Get-Process editors, editors_helper, DesktopEditors -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like ($app + '\*') } | Stop-Process -Force
  Start-Sleep -Milliseconds 500
  Remove-Item $app -Recurse -Force
}
New-Item -ItemType Directory -Force $app | Out-Null
Write-Host "copy upstream -> build\app"
robocopy $up $app /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }

# 2. patches (git apply works on plain directories; --directory is relative to the repo root)
$patches = @(Get-ChildItem (Join-Path $root 'patches') -Recurse -Filter *.patch -ErrorAction SilentlyContinue | Sort-Object FullName)
foreach ($p in $patches) {
  $rel = $p.FullName.Substring($root.Length + 1)
  & $git apply -p1 --directory=build/app --whitespace=nowarn $p.FullName
  if ($LASTEXITCODE -ne 0) { throw "patch failed: $rel" }
  Write-Host "patched: $rel"
}

# 3. overlay (files copied over the tree as they are)
$ov = Join-Path $root 'overlay'
if (Test-Path $ov) {
  $n = (Get-ChildItem $ov -Recurse -File | Where-Object { $_.Name -ne '.gitkeep' } | Measure-Object).Count
  if ($n -gt 0) {
    robocopy $ov $app /E /XF .gitkeep /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "overlay copy failed ($LASTEXITCODE)" }
    Write-Host "overlay: $n file(s)"
  }
}

# 4. binary / identity step (added in M1)
$brand = Join-Path $PSScriptRoot 'brand\apply.ps1'
if (Test-Path $brand) { & $brand -App $app }

# 5. build record
$lines = @("upstream_version=$Version", ("built_at=" + (Get-Date -Format 's')))
if (Test-Path (Join-Path $root '.git')) {
  $head = & $git rev-parse --verify -q --short HEAD
  if ($LASTEXITCODE -eq 0) { $lines += "repo_commit=$head" }
}
foreach ($p in $patches) {
  $lines += ("patch={0} sha256={1}" -f $p.Name, (Get-FileHash $p.FullName -Algorithm SHA256).Hash.ToLower())
}
[IO.File]::WriteAllLines((Join-Path $app 'BUILD-INFO.txt'), $lines)
Write-Host ("OK: build\app ready ({0} patch(es))" -f $patches.Count)
