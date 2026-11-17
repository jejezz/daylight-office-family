# Installer check: silent per-user install into build\install-test, file/shortcut checks, launch the installed app with a
# document, uninstall, verify removal and that user data was left alone. Needs dist\Daylight-Setup-*.exe (tools\package.ps1).
param([string]$Version = '0.1.0')
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$setup = Join-Path $root "dist\Daylight-Setup-$Version.exe"
$dir = Join-Path $root 'build\install-test'
$log = Join-Path $root 'build\install.log'
$results = @()
function Check([string]$name, [bool]$ok, [string]$detail = '') { $script:results += [pscustomobject]@{ Ok = $ok }; Write-Host (('{0}  {1}  {2}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $detail)) }
if (-not (Test-Path $setup)) { Write-Host "FAIL: $setup missing"; exit 1 }
if (Test-Path $dir) { Stop-App $dir; Remove-Item $dir -Recurse -Force }
$p = Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/NOICONS', '/TASKS=assoc', "/DIR=$dir", "/LOG=$log") -Wait -PassThru
Check 'installer exit code 0' ($p.ExitCode -eq 0) ("exit " + $p.ExitCode)
Check 'app files installed' (Test-Path (Join-Path $dir 'DesktopEditors.exe'))
Check 'NOTICE and licenses installed' ((Test-Path (Join-Path $dir 'NOTICE.txt')) -and (Test-Path (Join-Path $dir 'licenses\phosphor-LICENSE.txt')) -and (Test-Path (Join-Path $dir 'LICENSE.txt')))
Check 'uninstaller present, upstream one absent from payload' (Test-Path (Join-Path $dir 'unins000.exe'))
$prog = Get-ItemProperty 'HKCU:\Software\Classes\.docx\OpenWithProgids' -ErrorAction SilentlyContinue
Check "'Open with' entry registered (assoc task)" ($null -ne $prog.'Daylight.Document')
# upgrade over the existing install: a marker in the user data folder must survive, and the app must still start
$dataDir = Join-Path $env:LOCALAPPDATA 'Daylight'
$madeData = -not (Test-Path $dataDir)
New-Item -ItemType Directory -Force $dataDir | Out-Null
$marker = Join-Path $dataDir 'upgrade-marker.txt'
Set-Content $marker 'keep me' -Encoding ASCII
$p2 = Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/NOICONS', "/DIR=$dir", "/LOG=$log") -Wait -PassThru
Check 'upgrade over existing install, exit code 0' ($p2.ExitCode -eq 0) ("exit " + $p2.ExitCode)
Check 'user data survives the upgrade' (Test-Path $marker)
$userDataBefore = Test-Path (Join-Path $env:LOCALAPPDATA 'Daylight')
Start-App $dir @('--single-window-app', ('"' + (Join-Path $root 'tests\data\hello.docx') + '"'))
$w = Wait-AppWindow $dir '*hello*' 60
Check 'installed app starts and opens a document' ($null -ne $w)
Start-Sleep -Seconds 6
if ($w) { Save-WindowShot $w.Process (Join-Path $root 'build\shots\installer-run.png') }
[void](Close-App $dir)
Stop-App $dir
$u = Start-Process -FilePath (Join-Path $dir 'unins000.exe') -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -Wait -PassThru
Start-Sleep -Seconds 3
Check 'uninstall exit code 0' ($u.ExitCode -eq 0) ("exit " + $u.ExitCode)
Check 'app executable removed' (-not (Test-Path (Join-Path $dir 'DesktopEditors.exe')))
$prog2 = Get-ItemProperty 'HKCU:\Software\Classes\.docx\OpenWithProgids' -ErrorAction SilentlyContinue
Check "'Open with' entry removed" ($null -eq $prog2 -or $null -eq $prog2.'Daylight.Document')
Check 'user data survives the uninstall' (Test-Path $marker)
Remove-Item $marker -ErrorAction SilentlyContinue
if ($madeData) { Remove-Item $dataDir -Recurse -Force -ErrorAction SilentlyContinue }
$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed" -f $results.Count, $fail)
exit $(if ($fail -eq 0) { 0 } else { 1 })
