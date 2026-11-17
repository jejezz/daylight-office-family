# Smoke test for build\app: launch, open a document, check window title / processes / patch markers, save a screenshot.
# Usage: powershell -ExecutionPolicy Bypass -File tests\smoke.ps1 [-TitleSuffix ONLYOFFICE] [-MaxStartSec 45]
# Exit code 0 = all checks passed, 1 = at least one failed. Screenshot: build\shots\smoke-<time>.png
# Do not touch the app window while it runs.
param(
  [string]$TitleSuffix = 'ONLYOFFICE',   # M1 changes this to the product name
  [int]$MaxStartSec = 45
)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}

# 1. build output and patch markers
Check 'build\app exists' (Test-Path (Join-Path $app 'DesktopEditors.exe')) $app
Check 'test document exists' (Test-Path $doc) $doc
$info = Join-Path $app 'BUILD-INFO.txt'
$applied = 0
if (Test-Path $info) { $applied = @(Get-Content $info | Where-Object { $_ -like 'patch=*' }).Count }
$expected = @(Get-ChildItem (Join-Path $root 'patches') -Recurse -Filter *.patch -ErrorAction SilentlyContinue).Count
Check 'all patches recorded in BUILD-INFO' ($applied -eq $expected) ("applied=$applied expected=$expected")
$lm = Join-Path $app 'editors\web-apps\apps\common\main\lib\controller\LayoutManager.js'
Check 'patch marker: hidden-elements list' ((Test-Path $lm) -and ((Get-Content $lm -Raw) -match '_daylightHidden')) 'LayoutManager.js'
if (-not (Test-Path (Join-Path $app 'DesktopEditors.exe')) -or -not (Test-Path $doc)) { exit 1 }

# 2. launch and open the document
Stop-App $app
Start-App $app @('--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
Check 'window with document title appears' ($null -ne $w) $(if ($w) { "$($w.Seconds)s: $($w.Process.MainWindowTitle)" } else { 'timeout' })
if ($w) {
  Check ("window appears within {0}s" -f $MaxStartSec) ($w.Seconds -le $MaxStartSec) "$($w.Seconds)s"
  Check ("title ends with '{0}'" -f $TitleSuffix) ($w.Process.MainWindowTitle -like ('*' + $TitleSuffix)) $w.Process.MainWindowTitle
  Start-Sleep -Seconds 5
  $still = Get-AppWindow $app
  Check 'app still running after 5 s' ($null -ne $still)
  $helpers = @(Get-Process editors_helper -ErrorAction SilentlyContinue | Where-Object { $pp = $_.Path; $pp -and $pp.StartsWith($app, [StringComparison]::OrdinalIgnoreCase) }).Count
  Check 'renderer helper processes present' ($helpers -ge 2) "count=$helpers"
  if ($still) {
    Focus-AppWindow $still
    $stable = Wait-WindowStable $still
    Check 'UI finished loading (ribbon stable)' ($null -ne $stable) $(if ($stable) { "$stable s" } else { 'timeout' })
    $shot = Join-Path $root ("build\shots\smoke-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
    Save-WindowShot $still $shot
    Check 'screenshot saved' (Test-Path $shot) $shot
  }
}
Stop-App $app
$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed" -f $results.Count, $fail)
exit $(if ($fail -eq 0) { 0 } else { 1 })
