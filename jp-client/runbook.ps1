# runbook.ps1 - JP client one-shot pipeline (PowerShell entry).
# Usage:
#   powershell -File jp-client\runbook.ps1 -Apk "resources\NieR Re[in]carnation_3.7.1_JP.apk"
#   powershell -File jp-client\runbook.ps1 -Apk <original-jp.apk> -Out <out.apk> -Baseline <fix3c.apk>
# L3a naming contract: -Out is optional; the default product name is nier-jp.apk
# (plus nier-jp.apk.manifest.json sidecar). bin.e output name stays "same as input".
# Paired delivery (target APK + companion hanified bin.e):
#   powershell -File jp-client\runbook.ps1 -Apk <original-jp.apk> -Out <out.apk> `
#       -BinE <original-or-hanified.bin.e> -OutBinE <target.bin.e> [-BinEdit <cfg.json>] `
#       [-TextFrom <bin_zh_fix6.bin.e>] [-OrigBinE <20240404193219.bin.e>]
# All arguments are forwarded to build_jp_client.py; every step fails fast,
# logs land in logs/ next to -Out.
# NOTE: ASCII-only on purpose - Windows PowerShell 5.1 reads BOM-less UTF-8 as ANSI.
param(
    [Parameter(Mandatory = $true)][string]$Apk,
    [string]$Out = "",
    [string]$Work = "",
    [string]$Logs = "",
    [string]$Grpc = "192.168.2.6:8003",
    [string]$Http = "192.168.2.6:8080",
    [string]$Auth = "192.168.2.6:3000",
    [string]$Mode = "patched",
    [string]$Baseline = "E:\NieRReincarnation\zh-l10n\work\apk\nier-mod-menu-jp-font-fix3c.apk",
    [string]$BinE = "",
    [string]$OutBinE = "",
    [string]$BinEdit = "",
    [string]$TextFrom = "",
    [string]$OrigBinE = "",
    [switch]$ReuseWork,
    [switch]$NoVerify
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# Build interpreter: base Python by default (C:\Python314\python.exe).
# Pitfall: do NOT use zh-l10n\.venv\Scripts\python.exe - venv python hits Windows
# ACL limits when writing the Mod_Menu tree; UnityPy is supplied through
# toolpaths.json -> unitypy_site_packages on PYTHONPATH (see README-JP.md).
$py = "C:\Python314\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

$args2 = @("$here\build_jp_client.py", "--apk", $Apk, "--mode", $Mode,
    "--grpc", $Grpc, "--http", $Http, "--auth", $Auth, "--baseline", $Baseline)
if ($Out) { $args2 += @("--out", $Out) }
if ($Work) { $args2 += @("--work", $Work) }
if ($Logs) { $args2 += @("--logs", $Logs) }
if ($BinE) { $args2 += @("--bin-e", $BinE) }
if ($OutBinE) { $args2 += @("--out-bin-e", $OutBinE) }
if ($BinEdit) { $args2 += @("--bin-edit", $BinEdit) }
if ($TextFrom) { $args2 += @("--text-from", $TextFrom) }
if ($OrigBinE) { $args2 += @("--orig-bin-e", $OrigBinE) }
if ($ReuseWork) { $args2 += "--reuse-work" }
if ($NoVerify) { $args2 += "--no-verify" }

Write-Host "[runbook] $py $($args2 -join ' ')"
& $py @args2
exit $LASTEXITCODE
