# make_payload_zip.ps1 - pack jp-client/ + shared/ into the Colab payload zip (upload to Google Drive).
# Usage:
#   powershell -File jp-client\colab\make_payload_zip.ps1 -OutZip <dir>\jp-client-payload.zip
# Content = full jp-client/ (scripts, fix3 tables, fonts payload, modmenu, keystore, edit config)
# + shared/ (L3a shared modules detect_client.py / manifest_sidecar.py, sibling of jp-client/;
#   build_jp_client.py imports ../shared and MANIFEST.json ../shared/* entries resolve the same way).
# The zip root contains one jp-client/ folder + one shared/ folder (load_payload accepts both layouts).
# Big payloads (fonts 28MB / modmenu 1.5MB) travel via Drive zip, not notebook base64
# (see android_lunar_zh.ipynb cell 0).
# NOTE: ASCII-only on purpose - Windows PowerShell 5.1 reads BOM-less UTF-8 as ANSI.
param(
    [Parameter(Mandatory = $true)][string]$OutZip
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$jp = Resolve-Path (Join-Path $here "..")
$shared = Resolve-Path (Join-Path $here "..\..\shared")
$OutZip = [System.IO.Path]::GetFullPath($OutZip)

if (Test-Path $OutZip) { throw "Output exists, refusing to overwrite: $OutZip" }
$outDir = Split-Path -Parent $OutZip
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("jp-payload-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path (Join-Path $stage "jp-client") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "shared") | Out-Null
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
Compress-Archive -Path (Join-Path $stage "jp-client"), (Join-Path $stage "shared") -DestinationPath $OutZip -CompressionLevel Optimal
Remove-Item -Recurse -Force $stage

$zip = Get-Item $OutZip
Write-Host ("[make_payload_zip] {0}  {1:N0} B" -f $zip.FullName, $zip.Length)
Write-Host "Upload it to Google Drive, then set payload_zip in android_lunar_zh.ipynb."
