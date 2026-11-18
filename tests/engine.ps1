# Engine (sdkjs) check on build\app: the document must really be drawn by the editing engine.
# tests\smoke.ps1 cannot tell (it passed even with the engine file removed), so this one looks at pixels.
# Usage: powershell -ExecutionPolicy Bypass -File tests\engine.ps1 [-ExpectEngine]
#   -ExpectEngine : also require the "engine=" line in BUILD-INFO.txt (build made with patches\sdkjs or -ForceEngine)
# English UI and the default window size are assumed (coordinates below). Do not touch the app window while it runs.
param([switch]$ExpectEngine)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
Add-Type -AssemblyName System.Drawing
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
$results = @()
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }
  Write-Host ("{0}  {1}  {2}" -f $(if ($Ok) { 'PASS' } else { 'FAIL' }), $Name, $Detail)
}
function Lum($c) { 0.299 * $c.R + 0.587 * $c.G + 0.114 * $c.B }

$info = Join-Path $app 'BUILD-INFO.txt'
$eng = if (Test-Path $info) { @(Get-Content $info | Where-Object { $_ -like 'engine=*' }) } else { @() }
if ($ExpectEngine) { Check 'BUILD-INFO has an engine line' ($eng.Count -eq 1) ($eng -join ' ') }
foreach ($f in 'sdk-all-min.js', 'sdk-all.js') {
  $p = Join-Path $app "editors\sdkjs\word\$f"
  Check "engine file present: $f" (Test-Path $p) $(if (Test-Path $p) { '{0:N1} MB' -f ((Get-Item $p).Length / 1MB) } else { '' })
}

Stop-App $app
Start-App $app @('--single-window-app', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
Check 'window with document title appears' ($null -ne $w)
if ($w) {
  Focus-AppWindow $w.Process
  # poll up to 60 s: take a shot every 2 s until the text and the ruler are both drawn (a cold start can be slow)
  $sw = [Diagnostics.Stopwatch]::StartNew()
  do {
    Start-Sleep -Seconds 2
    $shot = Join-Path $root ("build\shots\engine-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png")
    Save-WindowShot $w.Process $shot
    $bmp = New-Object System.Drawing.Bitmap $shot
    # (a) the loading box ("Loading document", dark, centered on the page) must be gone: two points inside where it was
    $a1 = Lum ($bmp.GetPixel(480, 400)); $a2 = Lum ($bmp.GetPixel(700, 385))
    # (b) the document text is drawn: dark glyph pixels in the first lines of the page
    $dark = 0
    for ($y = 338; $y -lt 390; $y++) { for ($x = 320; $x -lt 680; $x++) { if ((Lum ($bmp.GetPixel($x, $y))) -lt 110) { $dark++ } } }
    # (c) the horizontal ruler is drawn: many light/dark changes along the ruler band
    $changes = 0; $prev = $null
    for ($x = 215; $x -lt 1005; $x++) { $l = [int](Lum ($bmp.GetPixel($x, 228)) / 40); if ($null -ne $prev -and $l -ne $prev) { $changes++ }; $prev = $l }
    $bmp.Dispose()
    $done = ($dark -gt 200) -and ($changes -gt 60)
  } while (-not $done -and $sw.Elapsed.TotalSeconds -lt 60)
  Check 'no "Loading document" box over the page' (($a1 -gt 200) -and ($a2 -gt 200)) ("lum {0:N0}, {1:N0}" -f $a1, $a2)
  Check 'document text drawn on the page' (($dark -gt 200) -and ($dark -lt 6000)) "dark pixels=$dark after $([math]::Round($sw.Elapsed.TotalSeconds)) s"
  Check 'horizontal ruler drawn' ($changes -gt 60) "changes=$changes"
  Check 'screenshot saved' (Test-Path $shot) $shot
}
Stop-App $app
$fail = @($results | Where-Object { -not $_.Ok }).Count
Write-Host ("`n{0} checks, {1} failed" -f $results.Count, $fail)
exit $(if ($fail -eq 0) { 0 } else { 1 })
