# Build the editing engine (sdkjs) from source with patches\sdkjs\*.patch and copy it into the staged app tree.
# Does nothing (and prints nothing) when there is no engine patch, unless -ForceEngine (baseline build).
# Source: external\sdkjs (shallow clone of ONLYOFFICE/sdkjs, tag v<version> from upstream.txt). It is put back to a
# clean tag checkout after the build. Output lines starting with "engine" go to BUILD-INFO.txt.
# The screen code (sdk-all-min.js) and the document-core code (sdk-all.js) must be replaced TOGETHER: replacing
# only one leaves the document stuck at "Loading document". The V8 snapshot sdk-all.bin of each rebuilt product is
# deleted (the converter would otherwise save with the unpatched upstream engine).
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
Git-Src config core.autocrlf false   # sources are LF; patches carry LF, so no end-of-line conversion
Git-Src checkout -q -f $tag
Git-Src clean -q -fdx
try {
  foreach ($p in $patches) {
    & $git -C $src apply -p1 --whitespace=nowarn $p.FullName
    if ($LASTEXITCODE -ne 0) { throw "engine patch failed: patches\sdkjs\$($p.Name)" }
    Write-Host "engine patched: $($p.Name)"
  }
  # products to build = top folders the patches touch (word = documents, cell = spreadsheets, slide = presentations);
  # a patch in common\ goes into every product. -ForceEngine alone builds word (baseline check).
  $tops = @(foreach ($p in $patches) {
    Get-Content $p.FullName | Where-Object { $_ -like 'diff --git a/*' } | ForEach-Object { ($_ -split ' ')[2].Substring(2).Split('/')[0] }
  }) | Sort-Object -Unique
  $products = @('word', 'cell', 'slide') | Where-Object { ($tops -contains $_) -or ($tops -contains 'common') }
  if ($products.Count -eq 0) { $products = @('word') }
  $env:PYTHONUTF8 = '1'   # build.py prints non-ASCII text; the default Windows code page cannot encode it
  foreach ($prod in $products) {
    & $py (Join-Path $src 'build\build.py') --product $prod --desktop | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "sdkjs build.py --product $prod failed ($LASTEXITCODE)" }
    $out = Join-Path $src "deploy\sdkjs\$prod"
    $dst = Join-Path $Stage "editors\sdkjs\$prod"
    foreach ($f in 'sdk-all-min.js', 'sdk-all.js') {
      if (-not (Test-Path (Join-Path $out $f))) { throw "engine build did not produce $prod\$f" }
      Copy-Item (Join-Path $out $f) (Join-Path $dst $f) -Force
    }
    # sdk-all.bin is a V8 startup snapshot of the UPSTREAM sdk-all.js. The converter's JS runtime (x2t/doctrenderer,
    # which applies the edits when a file is saved) loads it instead of sdk-all.js whenever it exists, so a patched
    # engine would be ignored on save. Without it doctrenderer reads sdk-all.js (measured: no noticeable slowdown).
    $bin = Join-Path $dst 'sdk-all.bin'
    if (Test-Path $bin) { Remove-Item $bin -Force }
    Write-Host ("engine: sdkjs {0} built from source ({1} patch(es)) -> {2}\sdk-all-min.js + sdk-all.js" -f $tag, $patches.Count, $prod)
  }
  "engine=sdkjs $tag patches=$($patches.Count)"
  foreach ($p in $patches) { "engine-patch=$($p.Name) sha256=$((Get-FileHash $p.FullName -Algorithm SHA256).Hash.ToLower())" }
} finally {
  Git-Src checkout -q -f $tag
  Git-Src clean -q -fdx
}
