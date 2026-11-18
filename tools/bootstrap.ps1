# Prepare a fresh clone so that tools\build.ps1 succeeds. Safe to run again: every step checks first and skips what is done.
#
#   powershell -ExecutionPolicy Bypass -File tools\bootstrap.ps1            # prepare everything
#   powershell -ExecutionPolicy Bypass -File tools\bootstrap.ps1 -CheckOnly # report what is missing, change nothing
#   powershell -ExecutionPolicy Bypass -File tools\bootstrap.ps1 -Build     # prepare, then run tools\build.ps1
#
# Steps:
#   1. tools:     git, python (3.9+), Pillow + numpy (pip install --user when missing), free disk space
#   2. upstream:  external\upstream-<ver>  = copy of the pinned official ONLYOFFICE Desktop Editors install tree.
#                 Source, in order: an existing copy / an installed matching version (C:\Program Files\...) /
#                 -Installer <file> / download from upstream.txt. The installer is checked (size, SHA-256, signature),
#                 installed silently into external\ (current user only, nothing in Program Files), copied, then removed.
#   3. engine:    external\sdkjs = shallow clone of tag v<ver> (core.autocrlf=false), needed by the engine patches
#   4. optional:  -WithInstaller  external\innosetup (Inno Setup 6.7.4, only tools\package.ps1 needs it)
# Everything lands in external\ (not in git). ASCII only: Windows PowerShell 5.1 reads BOM-less files as ANSI.
param(
  [string]$Installer,          # an already downloaded DesktopEditors_x64.exe of the pinned version (skips the download)
  [switch]$CheckOnly,
  [switch]$WithInstaller,
  [switch]$Build,
  [switch]$IgnoreInstalled,    # do not reuse an installed copy under Program Files; always use the installer
  [switch]$FullVerify          # hash every upstream file (about 150 s) instead of the key files
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest progress makes large downloads very slow in PS 5.1
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$ext = Join-Path $root 'external'
$problems = New-Object System.Collections.ArrayList

function Step([string]$m) { Write-Host ""; Write-Host "== $m" }
function Ok([string]$m)   { Write-Host "  ok:      $m" }
function Todo([string]$m) { Write-Host "  missing: $m"; [void]$problems.Add($m) }
function Say([string]$m)  { Write-Host "  $m" }

# ---- upstream.txt (key=value, # comments) -------------------------------------------------------------------
$pin = @{}
foreach ($line in Get-Content (Join-Path $root 'upstream.txt') -Encoding UTF8) {
  if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
  $i = $line.IndexOf('=')
  $pin[$line.Substring(0, $i).Trim()] = $line.Substring($i + 1).Trim()
}
foreach ($k in 'version', 'installer_size', 'installer_sha256', 'installer_url', 'installer_signer', 'installer_file') {
  if (-not $pin.ContainsKey($k)) { throw "upstream.txt has no '$k'" }
}
$ver = $pin['version']
$upDir = Join-Path $ext "upstream-$ver"
Write-Host "Daylight Office bootstrap  (upstream $ver)$(if ($CheckOnly) { '  [check only]' })"

# ---- 1. tools -----------------------------------------------------------------------------------------------
Step '1. tools'
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required (the pinned upstream build is x64).' }
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) { Ok ((& git --version)) } else { Todo 'git (install Git for Windows: https://git-scm.com/download/win)' }

# python must be real: the Microsoft Store "python.exe" stub prints a hint and exits non-zero
$py = Get-Command python -ErrorAction SilentlyContinue
$pyOk = $false
if ($py) {
  $pv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
  if ($LASTEXITCODE -eq 0 -and $pv) {
    $parts = $pv.Split('.')
    if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 9)) { $pyOk = $true; Ok "python $pv ($($py.Source))" }
    else { Todo "python 3.9 or newer (found $pv; 3.12 is what the engine build was verified with)" }
  }
}
if (-not $pyOk -and -not ($problems -match 'python 3.9')) { Todo 'python 3.12+ on PATH (https://www.python.org/downloads/windows/, tick "Add python.exe to PATH")' }

if ($pyOk) {
  & python -c "import PIL, numpy" 2>$null
  if ($LASTEXITCODE -eq 0) { Ok 'Pillow and numpy' }
  elseif ($CheckOnly) { Todo 'Python packages Pillow, numpy (pip install -r tools\requirements.txt)' }
  else {
    Say 'installing Pillow and numpy (pip --user) ...'
    & python -m pip install --user --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }
    & python -c "import PIL, numpy" 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Pillow/numpy still cannot be imported after pip install' }
    Ok 'Pillow and numpy installed'
  }
}

$drive = Get-PSDrive -Name ($root.Substring(0, 1)) -ErrorAction SilentlyContinue
if ($drive) {
  $freeGB = [math]::Round($drive.Free / 1GB, 1)
  # upstream copy 1.0 GB + installer 0.3 GB + temp install 1.0 GB + build\app.new/app 2 GB + sdkjs
  if ($freeGB -lt 6) { Todo "free disk space on $($drive.Name): ($freeGB GB free, about 6 GB needed)" } else { Ok "free disk space $freeGB GB" }
}
if ($problems.Count -gt 0) {
  Write-Host ""; Write-Host 'Fix the items above first, then run bootstrap again:'; $problems | ForEach-Object { Write-Host "  - $_" }
  exit 1
}

# ---- helpers for step 2 -------------------------------------------------------------------------------------
function Test-Installer([string]$File) {
  $size = (Get-Item $File).Length
  if ($size -ne [int64]$pin['installer_size']) { return "size $size, expected $($pin['installer_size'])" }
  $h = (Get-FileHash $File -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $pin['installer_sha256'].ToLower()) { return "SHA-256 $h, expected $($pin['installer_sha256'])" }
  $sig = Get-AuthenticodeSignature $File
  if ($sig.Status -ne 'Valid') { return "signature is $($sig.Status)" }
  if ($sig.SignerCertificate.Subject -notlike "*$($pin['installer_signer'])*") { return "signed by $($sig.SignerCertificate.Subject)" }
  return $null
}
function Remove-UnderExternal([string]$Path) {
  # delete only real folders inside external\ (never follow a junction: that once wiped a main checkout's external\)
  $full = [IO.Path]::GetFullPath($Path)
  if (-not $full.StartsWith($ext + '\')) { throw "refusing to delete outside external\: $full" }
  if (-not (Test-Path $full)) { return }
  if ((Get-Item $full -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($full); return }
  Remove-Item $full -Recurse -Force
}
function Find-InstalledUpstream {
  foreach ($d in @('C:\Program Files\ONLYOFFICE\DesktopEditors', (Join-Path $env:LOCALAPPDATA 'Programs\ONLYOFFICE\DesktopEditors'))) {
    $exe = Join-Path $d 'DesktopEditors.exe'
    if ((Test-Path $exe) -and ((Get-Item $exe).VersionInfo.ProductVersion -eq $ver)) { return $d }
  }
  return $null
}
function Invoke-PrepareUpstream([string]$Source) {
  $a = @{ Version = $ver }
  if ($Source) { $a['Source'] = $Source }
  if ($FullVerify) { $a['Full'] = $true }
  $global:LASTEXITCODE = 0
  & (Join-Path $PSScriptRoot 'prepare-upstream.ps1') @a
  if ($LASTEXITCODE -ne 0) { throw "prepare-upstream.ps1 verification failed (see FAIL lines above)" }
}

# ---- 2. upstream tree ---------------------------------------------------------------------------------------
Step "2. upstream install tree  external\upstream-$ver"
if (Test-Path $upDir) {
  if ($CheckOnly) { Ok 'present (not re-verified in -CheckOnly; run without it to verify hashes)' }
  else {
    Say 'present, verifying ...'
    try { Invoke-PrepareUpstream $null }
    catch { throw "$_`nThe copy is damaged or incomplete. Delete external\upstream-$ver and run bootstrap again." }
  }
} elseif ($CheckOnly) {
  Todo "external\upstream-$ver (bootstrap creates it from the official installer)"
} else {
  New-Item -ItemType Directory -Force $ext | Out-Null
  $installed = $null
  if (-not $IgnoreInstalled) { $installed = Find-InstalledUpstream }
  if ($installed) {
    Say "using the installed copy: $installed"
    Invoke-PrepareUpstream $installed
  } else {
    # obtain the installer
    $dl = Join-Path $ext '_download'
    $file = $null
    if ($Installer) {
      if (-not (Test-Path $Installer)) { throw "installer not found: $Installer" }
      $file = (Resolve-Path $Installer).Path
    } else {
      $file = Join-Path $dl $pin['installer_file']
      if (Test-Path $file) { Say "cached installer: $file" }
      else {
        New-Item -ItemType Directory -Force $dl | Out-Null
        Say ("downloading {0:N0} MB from {1} ..." -f ([int64]$pin['installer_size'] / 1MB), $pin['installer_url'])
        $tmp = "$file.part"
        (New-Object Net.WebClient).DownloadFile($pin['installer_url'], $tmp)
        Move-Item $tmp $file -Force
      }
    }
    Say 'checking size, SHA-256 and signature ...'
    $why = Test-Installer $file
    if ($why) {
      throw ("The installer is not the pinned version $ver ($why).`n" +
             "The download address always serves the newest release, so an old version must come from a saved copy:`n" +
             "  tools\bootstrap.ps1 -Installer <path to the saved DesktopEditors_x64.exe>`n" +
             "(expected SHA-256 $($pin['installer_sha256']); a downloaded file is kept at $file - delete it if it is wrong)")
    }
    Ok 'installer matches upstream.txt'
    # silent per-user install into external\ (no admin, no Program Files, no file associations kept after removal)
    $tmpInst = Join-Path $ext '_upstream-install'
    Remove-UnderExternal $tmpInst
    Say "installing silently into $tmpInst (about a minute) ..."
    $p = Start-Process -FilePath $file -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', "/DIR=`"$tmpInst`"") -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "installer exited with $($p.ExitCode)" }
    # the app may start after setup: close what we started, otherwise the copy and the uninstall hit locked files
    Get-Process DesktopEditors, editors, editors_helper -ErrorAction SilentlyContinue |
      Where-Object { $_.Path -and $_.Path.StartsWith($tmpInst + '\') } | Stop-Process -Force
    Start-Sleep -Seconds 2
    try {
      Invoke-PrepareUpstream $tmpInst
    } catch {
      Write-Host "The temporary install is left at $tmpInst for inspection."
      throw
    }
    # remove the temporary installation (uninstaller first so the per-user registry entries go away too)
    $unins = Join-Path $tmpInst 'unins000.exe'
    if (Test-Path $unins) { Start-Process -FilePath $unins -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -Wait | Out-Null }
    Remove-UnderExternal $tmpInst
    Remove-UnderExternal $dl
    Ok 'temporary installation removed'
  }
}

# ---- 3. engine source ---------------------------------------------------------------------------------------
Step "3. external\sdkjs  (editing engine source, tag v$ver)"
$sdk = Join-Path $ext 'sdkjs'
$tag = "v$ver"
if (Test-Path (Join-Path $sdk '.git')) {
  $at = (& git -C $sdk describe --tags --exact-match HEAD 2>$null)
  if ($at -and ($at -split "`n") -contains $tag) { Ok "clone present at $tag" }
  elseif ($CheckOnly) { Todo "external\sdkjs is not at $tag (build.ps1 re-checks out the tag itself; found: $at)" }
  else { Say "clone is not at $tag; build.ps1 checks out the tag itself, nothing to do" }
  if (-not $CheckOnly) { & git -C $sdk config core.autocrlf false }
} elseif ($CheckOnly) {
  Todo 'external\sdkjs (bootstrap clones it)'
} else {
  if (Test-Path $sdk) { throw "external\sdkjs exists but is not a git clone: delete it and run bootstrap again" }
  New-Item -ItemType Directory -Force $ext | Out-Null
  Say "cloning ONLYOFFICE/sdkjs $tag (shallow) ..."
  & git -c core.autocrlf=false -c core.longpaths=true clone --depth 1 --branch $tag https://github.com/ONLYOFFICE/sdkjs $sdk
  if ($LASTEXITCODE -ne 0) { throw 'git clone of sdkjs failed' }
  & git -C $sdk config core.autocrlf false
  & git -C $sdk config core.longpaths true
  Ok "cloned at $tag"
}

# ---- 4. optional: Inno Setup --------------------------------------------------------------------------------
Step 'external\innosetup  (only for tools\package.ps1)'
$iscc = Join-Path $ext 'innosetup\ISCC.exe'
if (Test-Path $iscc) { Ok 'Inno Setup present' }
elseif (-not $WithInstaller) { Say 'skipped (add -WithInstaller if you want to build the installer)' }
elseif ($CheckOnly) { Todo 'external\innosetup (bootstrap -WithInstaller installs it)' }
else {
  $isUrl = 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_4/innosetup-6.7.4.exe'
  $isSha = 'a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c'
  $dl2 = Join-Path $ext '_download'
  New-Item -ItemType Directory -Force $dl2 | Out-Null
  $isFile = Join-Path $dl2 'innosetup-6.7.4.exe'
  Say 'downloading Inno Setup 6.7.4 (10.6 MB) ...'
  (New-Object Net.WebClient).DownloadFile($isUrl, $isFile)
  if ((Get-FileHash $isFile -Algorithm SHA256).Hash.ToLower() -ne $isSha) { throw "Inno Setup SHA-256 mismatch ($isFile)" }
  $sig = Get-AuthenticodeSignature $isFile
  if ($sig.Status -ne 'Valid') { throw "Inno Setup signature is $($sig.Status)" }
  $p = Start-Process -FilePath $isFile -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/NOICONS', "/DIR=`"$(Join-Path $ext 'innosetup')`"") -Wait -PassThru
  if ($p.ExitCode -ne 0 -or -not (Test-Path $iscc)) { throw "Inno Setup install failed ($($p.ExitCode))" }
  Remove-UnderExternal $dl2
  Ok 'Inno Setup installed'
}

# ---- done ---------------------------------------------------------------------------------------------------
Write-Host ""
if ($CheckOnly) {
  if ($problems.Count -gt 0) { Write-Host 'Not ready:'; $problems | ForEach-Object { Write-Host "  - $_" }; exit 1 }
  Write-Host 'Ready: tools\build.ps1 should work.'
  exit 0
}
if ($Build) {
  Write-Host 'Running tools\build.ps1 ...'
  & (Join-Path $PSScriptRoot 'build.ps1')
} else {
  Write-Host 'Bootstrap done. Next:  tools\build.ps1'
}
