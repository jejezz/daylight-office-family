# Icon test for build\app: static check of every replaced sprite cell, then a real screenshot of the Home tab where the
# bold / italic / underline / strikethrough buttons are compared with the expected Phosphor glyph (pixel correlation).
# Usage: powershell -ExecutionPolicy Bypass -File tests\icons.ps1
# Button positions are fixed offsets for the default window size and English UI (same assumption as tests\theme.ps1).
# Do not touch the mouse/keyboard while it runs.
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$py = (Get-Command python -ErrorAction Stop).Source
$verify = Join-Path $root 'tools\icons\verify.py'
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}

$out = & $py $verify --app $app 2>&1
Check 'every replaced sprite cell is correct (static)' ($LASTEXITCODE -eq 0) (($out | Select-Object -Last 1) -join '')

Stop-App $app
Start-App $app @('--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
Check 'app starts' ($null -ne $w)
if (-not $w) { exit 1 }
Focus-AppWindow $w.Process
Start-Sleep -Seconds 14
[void](Click-Tab $w.Process 98)                                   # Home tab (checked by its underline)
$osLight = (Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize' -ErrorAction SilentlyContinue).AppsUseLightTheme
$darkArg = @()
if ($osLight -eq 0) { $darkArg = @('--dark') }
$shot = Join-Path $root ("build\shots\icons-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
Save-WindowShot $w.Process $shot
$cases = @(@('bold', 135, 'text-b'), @('italic', 163, 'text-italic'), @('underline', 191, 'text-underline'), @('strikethrough', 219, 'text-strikethrough'))
foreach ($c in $cases) {
  $o = & $py $verify --shot $shot --at ("{0},151" -f $c[1]) --icon $c[2] --box 20 @darkArg 2>&1
  Check ("Home tab shows the Phosphor '" + $c[0] + "' icon") ($LASTEXITCODE -eq 0) (($o | Select-Object -Last 1) -join '')
}
# big icons (Insert tab, 28 px cells with a 24 px glyph)
if (Click-Tab $w.Process 156) {
  Start-Sleep -Seconds 1
  $shot2 = Join-Path $root ("build\shots\icons-insert-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
  Save-WindowShot $w.Process $shot2
  foreach ($c in @(@('table', 234, 'table'), @('image', 286, 'image'))) {
    $o = & $py $verify --shot $shot2 --at ("{0},119" -f $c[1]) --icon $c[2] --box 24 2>&1
    Check ("Insert tab shows the Phosphor '" + $c[0] + "' (big) icon") ($LASTEXITCODE -eq 0) (($o | Select-Object -Last 1) -join '')
  }
} else { Check 'Insert tab opens' $false }
[void](Close-App $app)
$fail =@($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed. Screenshot: {2}" -f $results.Count, $fail, $shot)
exit $(if ($fail -eq 0) { 0 } else { 1 })
