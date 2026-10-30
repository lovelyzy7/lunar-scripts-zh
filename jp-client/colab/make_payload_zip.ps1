# make_payload_zip.ps1 - pack jp-client/ + en-client/ + shared/ into the Colab payload zip (upload to Google Drive).
# Usage:
#   powershell -File jp-client\colab\make_payload_zip.ps1 -OutZip <dir>\jp-client-payload.zip
# Content = full jp-client/ (scripts, fix3 tables, fonts payload, modmenu, keystore, edit config)
# + en-client/ (fix3-EN/ko/fix3l scripts, EN fonts payload, en keystore) + shared/ (L3a shared
#   modules detect_client.py / manifest_sidecar.py, sibling of jp-client/;
#   build_jp_client.py imports ../shared and MANIFEST.json ../shared/* entries resolve the same way).
# The zip root contains one jp-client/ folder + one shared/ folder (load_payload accepts both layouts);
# en-client/ rides along for the EN build face and is ignored by the JP loader.
# Big payloads (fonts 28MB / modmenu 1.5MB) travel via Drive zip, not notebook base64
# (see android_lunar_zh.ipynb cell 0).
# Before compressing, the pack step asserts the offline payload families are inside:
# fix3 authoritative table, font payload 4 entries (per client), modmenu payload.
# NOTE: ASCII-only on purpose - Windows PowerShell 5.1 reads BOM-less UTF-8 as ANSI.
param(
    [Parameter(Mandatory = $true)][string]$OutZip
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$jp = Resolve-Path (Join-Path $here "..")
$shared = Resolve-Path (Join-Path $here "..\..\shared")
$en = Resolve-Path (Join-Path $here "..\..\en-client")
$OutZip = [System.IO.Path]::GetFullPath($OutZip)

if (Test-Path $OutZip) { throw "Output exists, refusing to overwrite: $OutZip" }
$outDir = Split-Path -Parent $OutZip
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("jp-payload-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path (Join-Path $stage "jp-client") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "shared") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "en-client") | Out-Null
# Build artifacts / caches stay out of the package.
$exclude = @("build", "out", "__pycache__", "logs", "work")
foreach ($item in Get-ChildItem -Force $jp) {
    if ($exclude -contains $item.Name) { continue }
    $dest = Join-Path (Join-Path $stage "jp-client") $item.Name
    if ($item.PSIsContainer) {
        Copy-Item -Recurse -Force $item.FullName $dest
        foreach ($ex in $exclude) {
            $p = Join-Path $dest $ex
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
    } else {
        Copy-Item -Force $item.FullName $dest
    }
}
# en-client/ face (fix3-EN/ko/fix3l scripts + EN fonts payload + en keystore)
foreach ($item in Get-ChildItem -Force $en) {
    if ($exclude -contains $item.Name) { continue }
    $dest = Join-Path (Join-Path $stage "en-client") $item.Name
    if ($item.PSIsContainer) {
        Copy-Item -Recurse -Force $item.FullName $dest
        foreach ($ex in $exclude) {
            $p = Join-Path $dest $ex
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
    } else {
        Copy-Item -Force $item.FullName $dest
    }
}
# shared/ module files (detect_client.py / manifest_sidecar.py / __init__.py)
foreach ($item in Get-ChildItem -Force $shared) {
    if ($exclude -contains $item.Name) { continue }
    $dest = Join-Path (Join-Path $stage "shared") $item.Name
    if ($item.PSIsContainer) {
        Copy-Item -Recurse -Force $item.FullName $dest
        foreach ($ex in $exclude) {
            $p = Join-Path $dest $ex
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
    } else {
        Copy-Item -Force $item.FullName $dest
    }
}
# Offline payload families: fix3 table + font payload 4 entries (per client) + modmenu.
$fontNames = @("6f937efa0660c47f59d5215d276b1cbb", "7089ac60979c94824ac549baab08cfa7",
               "ad1489eb70ff840d19d7d0841bcdd3a9", "550e0743a6b6344cfa3380b9a07f58b6")
$required = @("jp-client\fix3\builtin_strings.json", "jp-client\modmenu-payload\lib\arm64-v8a\libniermenu.so")
foreach ($n in $fontNames) {
    $required += "jp-client\fonts\payload\assets\bin\Data\$n"
    $required += "en-client\fonts\payload\assets\bin\Data\$n"
}
$missing = @()
foreach ($rel in $required) {
    if (-not (Test-Path (Join-Path $stage $rel))) { $missing += $rel }
}
if ($missing.Count -gt 0) {
    Remove-Item -Recurse -Force $stage
    throw ("payload incomplete, missing: " + ($missing -join ", "))
}
Write-Host ("[make_payload_zip] payload families ok: fix3 table + {0} font entries x 2 clients + modmenu" -f $fontNames.Count)
Compress-Archive -Path (Join-Path $stage "jp-client"), (Join-Path $stage "en-client"), (Join-Path $stage "shared") -DestinationPath $OutZip -CompressionLevel Optimal
Remove-Item -Recurse -Force $stage

$zip = Get-Item $OutZip
Write-Host ("[make_payload_zip] {0}  {1:N0} B" -f $zip.FullName, $zip.Length)
Write-Host "Upload it to Google Drive, then set payload_zip in android_lunar_zh.ipynb."
