# Daylight Office - interface font chooser.
# Lists every installed font and writes the choice to daylight-user.css next to this script
# (read by the editors and the start screen when the app starts). Keep this file ASCII only (Windows PowerShell 5.1).
#   set-ui-font.ps1            open the chooser window
#   set-ui-font.ps1 -Set NAME  write NAME and exit (no window)
#   set-ui-font.ps1 -Reset     back to the default font and exit
param([string]$Set = '', [switch]$Reset)
$ErrorActionPreference = 'Stop'
function U([string]$s) { [regex]::Unescape($s) }
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$css = Join-Path $dir 'daylight-user.css'
$stack = '"SeoulNamsan", sans-serif'

function Write-FontFile([string]$name) {
  $head = '/* Daylight Office - personal appearance settings. Written by set-ui-font.ps1; you may also edit it by hand. */'
  if ($name) { $rule = ':root { --dl-font: "' + ($name -replace '"', '') + '", ' + $stack + '; }' }
  else { $rule = '/* :root { --dl-font: "Malgun Gothic", "SeoulNamsan", sans-serif; } */' }
  [IO.File]::WriteAllText($css, $head + "`r`n" + $rule + "`r`n", (New-Object Text.UTF8Encoding($false)))
}
function Read-FontName {
  if (-not (Test-Path $css)) { return '' }
  $m = [regex]::Match((Get-Content $css -Raw), '(?m)^\s*:root\s*\{\s*--dl-font:\s*"([^"]+)"')
  if ($m.Success) { return $m.Groups[1].Value } else { return '' }
}

if ($Reset) { Write-FontFile ''; exit 0 }
if ($Set) { Write-FontFile $Set; exit 0 }

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$defaultLabel = U '\uAE30\uBCF8 (\uC11C\uC6B8\uB0A8\uC0B0\uCCB4)'
$fonts = @((New-Object System.Drawing.Text.InstalledFontCollection).Families | ForEach-Object { $_.Name } | Sort-Object)
$form = New-Object Windows.Forms.Form
$form.Text = U 'Daylight Office - \uC778\uD130\uD398\uC774\uC2A4 \uAE00\uAF34'
$form.ClientSize = New-Object Drawing.Size(460, 210)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object Drawing.Font('Malgun Gothic', 9)
$lbl = New-Object Windows.Forms.Label
$lbl.Text = U '\uC778\uD130\uD398\uC774\uC2A4 \uAE00\uAF34'
$lbl.Location = New-Object Drawing.Point(16, 16); $lbl.AutoSize = $true
$combo = New-Object Windows.Forms.ComboBox
$combo.DropDownStyle = 'DropDownList'
$combo.Location = New-Object Drawing.Point(16, 40); $combo.Width = 428
[void]$combo.Items.Add($defaultLabel)
foreach ($f in $fonts) { [void]$combo.Items.Add($f) }
$cur = Read-FontName
$idx = if ($cur) { $combo.Items.IndexOf($cur) } else { 0 }
$prev = New-Object Windows.Forms.Label
$prev.Text = U 'Daylight \uD55C\uAE00 \uAC00\uB098\uB2E4\uB77C ABC abc 123'
$prev.Location = New-Object Drawing.Point(16, 80); $prev.Size = New-Object Drawing.Size(428, 44)
$prev.BorderStyle = 'FixedSingle'; $prev.TextAlign = 'MiddleLeft'
$note = New-Object Windows.Forms.Label
$note.Text = U '\uD0ED \uC81C\uBAA9\uC740 \uC774 \uC124\uC815\uC744 \uB530\uB974\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.'; $note.ForeColor = [Drawing.Color]::Gray
$note.Location = New-Object Drawing.Point(16, 132); $note.AutoSize = $true
$status = New-Object Windows.Forms.Label
$status.Location = New-Object Drawing.Point(16, 156); $status.AutoSize = $true
$ok = New-Object Windows.Forms.Button
$ok.Text = U '\uC801\uC6A9'; $ok.Location = New-Object Drawing.Point(268, 170); $ok.Size = New-Object Drawing.Size(84, 30)
$cl = New-Object Windows.Forms.Button
$cl.Text = U '\uB2EB\uAE30'; $cl.Location = New-Object Drawing.Point(360, 170); $cl.Size = New-Object Drawing.Size(84, 30)
$combo.Add_SelectedIndexChanged({
  $n = [string]$combo.SelectedItem
  if ($combo.SelectedIndex -le 0) { $prev.Font = New-Object Drawing.Font('Malgun Gothic', 14) }
  else { try { $prev.Font = New-Object Drawing.Font($n, 14) } catch { } }
})
$ok.Add_Click({
  if ($combo.SelectedIndex -le 0) { Write-FontFile '' } else { Write-FontFile ([string]$combo.SelectedItem) }
  $status.Text = U '\uC801\uC6A9\uD588\uC2B5\uB2C8\uB2E4. \uC571\uC744 \uB2E4\uC2DC \uC2DC\uC791\uD558\uBA74 \uBC14\uB01D\uB2C8\uB2E4.'
})
$cl.Add_Click({ $form.Close() })
$form.Controls.AddRange(@($lbl, $combo, $prev, $note, $status, $ok, $cl))
$combo.SelectedIndex = [Math]::Max(0, $idx)
[void]$form.ShowDialog()
