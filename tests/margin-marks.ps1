# Margin boundary marks: engine patch patches\sdkjs\0001 + the "Text boundaries" checkbox in the View tab.
# Starts build\app with a DevTools port (9333), asks the page through tests\lib\cdp.py, and takes a screenshot with the
# marks on. English UI assumed. Do not touch the app window while it runs.
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$doc = Join-Path $PSScriptRoot 'data\hello.docx'
Stop-App $app
Start-App $app @('--single-window-app', '--remote-debugging-port=9333', ('"' + $doc + '"'))
$w = Wait-AppWindow $app '*hello*' 60
if (-not $w) { Write-Host 'FAIL  window did not appear'; exit 1 }
Start-Sleep -Seconds 10   # document and editor finish loading
$env:PYTHONIOENCODING = 'utf-8'
& python (Join-Path $PSScriptRoot 'margin-marks-check.py')
$code = $LASTEXITCODE
# screenshot with the marks on (look at it: corner marks at the four corners of the text area)
$cdp = Join-Path $PSScriptRoot 'lib\cdp.py'
function Set-Marks([string]$On) {
  & python $cdp "(function(){var a=document.querySelector('iframe').contentWindow.Asc.editor;a.put_ShowMarginBoundaries($On);return 1})()" | Out-Null
}
Set-Marks 'true'
Start-Sleep -Seconds 1
Focus-AppWindow $w.Process
Save-WindowShot $w.Process (Join-Path $root 'build\shots\margin-marks.png')
Set-Marks 'false'
Stop-App $app
exit $code
