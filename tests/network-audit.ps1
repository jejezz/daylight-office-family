# Network audit: runs build\app with a document and lists every non-local TCP connection the app's processes open.
# Usage: powershell -ExecutionPolicy Bypass -File tests\network-audit.ps1 [-Seconds 60] [-Doc <file>]
# It only observes (Get-NetTCPConnection, polled once per second); it does not block or change anything.
# Limits: short-lived connections between two polls can be missed, UDP is not covered, DNS lookups are not covered.
param(
  [int]$Seconds = 60,
  [string]$Doc = '',
  [switch]$NoDoc   # start page only, no document
)
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot 'lib\ui.ps1')
$app = Join-Path $root 'build\app'
if (-not $Doc) { $Doc = Join-Path $PSScriptRoot 'data\hello.docx' }
function Is-Local([string]$a) { $a -eq '127.0.0.1' -or $a -eq '::1' -or $a -eq '0.0.0.0' -or $a -eq '::' -or $a.StartsWith('fe80') }

Stop-App $app
$appArgs = @('--single-window-app')
if (-not $NoDoc) { $appArgs += ('"' + $Doc + '"') }
Start-App $app $appArgs
$w = Wait-AppWindow $app '*' 60
if (-not $w) { Write-Host 'FAIL: app did not start'; exit 1 }
$seen = @{}
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $Seconds) {
  $pids = @(Get-AppProcesses $app | ForEach-Object { $_.Id })
  if ($pids.Count -gt 0) {
    Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $pids -contains $_.OwningProcess -and -not (Is-Local $_.RemoteAddress) } | ForEach-Object {
      $name = (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName
      $key = "{0}  {1}:{2}  ({3})" -f $name, $_.RemoteAddress, $_.RemotePort, $_.State
      if (-not $seen.ContainsKey($key)) { $seen[$key] = [math]::Round($sw.Elapsed.TotalSeconds, 0) }
    }
  }
  Start-Sleep -Seconds 1
}
Stop-App $app
Write-Host ("Observed {0} s. Non-local TCP connections from the app's processes: {1}" -f $Seconds, $seen.Count)
$seen.GetEnumerator() | Sort-Object Value | ForEach-Object { Write-Host ("  t={0,3}s  {1}" -f $_.Value, $_.Key) }
foreach ($k in $seen.Keys) {
  $ip = ($k -split '\s+')[1] -replace ':\d+$', ''
  try { $n = [System.Net.Dns]::GetHostEntry($ip).HostName; Write-Host "  reverse DNS $ip -> $n" } catch { Write-Host "  reverse DNS $ip -> (none)" }
}
exit 0
