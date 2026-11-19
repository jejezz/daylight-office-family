# Start screen test: single page (toolbar + recent files), settings as a modal, single/clear-all removal.
# Usage: powershell -ExecutionPolicy Bypass -File tests\start-screen.ps1
# Starts build\app with a DevTools port, opens 3 temporary documents (they end up in the recent list, then the list is
# cleared by the test: this CHANGES the recent-files list of the app's settings). Do not touch the app while it runs.
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
$tmp = Join-Path $root 'build\start-screen-test'
$shots = Join-Path $root 'build\shots'
New-Item -ItemType Directory -Force $tmp, $shots | Out-Null
foreach ($n in 'a', 'b', 'c') { Copy-Item (Join-Path $PSScriptRoot 'data\hello.docx') (Join-Path $tmp "doc-$n.docx") -Force }
Stop-App $app
Start-App $app @('--single-window-app', '--remote-debugging-port=9333')
Start-Sleep -Seconds 9
foreach ($n in 'a', 'b', 'c') {
  Start-App $app @('--single-window-app', ('"' + (Join-Path $tmp "doc-$n.docx") + '"'))
  Start-Sleep -Seconds 5
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
& python -I (Join-Path $PSScriptRoot 'start-screen-check.py') (Join-Path $shots "start-$stamp")
$code = $LASTEXITCODE
[void](Close-App $app)
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit $code
