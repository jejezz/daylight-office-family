# Build the editing engine (sdkjs) from source with patches\sdkjs\*.patch and copy it into the staged app tree.
# Does nothing (and prints nothing) when there is no engine patch, unless -ForceEngine (baseline build).
# Source: external\sdkjs (shallow clone of ONLYOFFICE/sdkjs, tag v<version> from upstream.txt). It is put back to a
# clean tag checkout after the build. Output lines starting with "engine" go to BUILD-INFO.txt.
# The screen code (sdk-all-min.js) and the document-core code (sdk-all.js) must be replaced TOGETHER: replacing
# only one leaves the document stuck at "Loading document". The V8 code cache sdk-all.bin is left as is (ignored when it
# does not match).
param(
  [Parameter(Mandatory)][string]$Stage,
  [Parameter(Mandatory)][string]$Root,
  [string]$Version = '10.0.0.169',
  [switch]$ForceEngine
)
$ErrorActionPreference = 'Stop'
$patches = @(Get-ChildItem (Join-Path $Root 'patches\sdkjs') -Filter *.patch -ErrorAction SilentlyContinue | Sort-Object FullName)
if ($patches.Count -eq 0 -and -not $ForceEngine) { return }

$git = (Get-Command git -ErrorAction Stop).Source
$py = (Get-Command python -ErrorAction Stop).Source
$src = Join-Path $Root 'external\sdkjs'
if (-not (Test-Path (Join-Path $src '.git'))) { throw "engine source not found: $src (git clone --depth 1 --branch v$Version https://github.com/ONLYOFFICE/sdkjs)" }
$tag = "v$Version"

function Git-Src { & $git -C $src @args; if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed in external\sdkjs" } }
Git-Src checkout -q -f $tag
Git-Src clean -q -fdx
try {
  foreach ($p in $patches) {
    & $git -C $src apply -p1 --whitespace=nowarn $p.FullName
    if ($LASTEXITCODE -ne 0) { throw "engine patch failed: patches\sdkjs\$($p.Name)" }
    Write-Host "engine patched: $($p.Name)"
  }
  $env:PYTHONUTF8 = '1'   # build.py prints non-ASCII text; the default Windows code page cannot encode it
  & $py (Join-Path $src 'build\build.py') --product word --desktop | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "sdkjs build.py failed ($LASTEXITCODE)" }
  $out = Join-Path $src 'deploy\sdkjs\word'
  $dst = Join-Path $Stage 'editors\sdkjs\word'
  foreach ($f in 'sdk-all-min.js', 'sdk-all.js') {
    if (-not (Test-Path (Join-Path $out $f))) { throw "engine build did not produce $f" }
    Copy-Item (Join-Path $out $f) (Join-Path $dst $f) -Force
  }
  Write-Host ("engine: sdkjs {0} built from source ({1} patch(es)) -> word\sdk-all-min.js + sdk-all.js" -f $tag, $patches.Count)
  "engine=sdkjs $tag patches=$($patches.Count)"
  foreach ($p in $patches) { "engine-patch=$($p.Name) sha256=$((Get-FileHash $p.FullName -Algorithm SHA256).Hash.ToLower())" }
} finally {
  Git-Src checkout -q -f $tag
  Git-Src clean -q -fdx
}
