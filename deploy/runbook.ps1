# deploy/runbook.ps1 — JP 侧部署 runbook 脚本化（patch_listbin / bump / verify）
# 提炼自 zh-l10n\work\deploy\README.md 与 fix 系列部署轮实操（deploy-20261025..20261028）。
# 红线：本脚本默认只做「预检→备份→副本上 patch/bump→verify」，**不写现网**；
#       最后一步原子替换是显式 -ApplyLive 开关（本交付任务内禁止使用）。
#
# 用法（工作目录 = lunar-scripts-zh 之外任选，全部 IO 在 E:）：
#   pwsh -File deploy\runbook.ps1 -StageRoot <staging\revisions\0> -ListBin <staging\list.bin> `
#        -LiveRoot E:\NieRReincarnation\lunar-tear\server\assets\revisions\0 -WhatIf
#   pwsh -File deploy\runbook.ps1 ... -Names changed.txt -NewRevision 822        # 副本 patch+bump+verify
#   pwsh -File deploy\runbook.ps1 ... -ApplyLive                                  # 显式原子替换（需人工确认）

param(
  [Parameter(Mandatory = $true)][string]$StageRoot,        # 暂存的 revisions\0 树（含 assetbundle/）
  [Parameter(Mandatory = $true)][string]$ListBin,          # 暂存 list.bin（会被原地 patch）
  [string]$LiveRoot = "E:\NieRReincarnation\lunar-tear\server\assets\revisions\0",
  [string]$NamesFile,                                     # patch 名单（缺省 = 全部在盘差异，走 patch_listbin.py 语义）
  [int]$NewRevision = 0,
  [string]$Py = "E:\NieRReincarnation\zh-l10n\.venv\Scripts\python.exe",
  [string]$DeployTools = "E:\NieRReincarnation\zh-l10n\work\deploy",
  [string]$LunarBasePatch = "E:\NieRReincarnation\lunar-base\scripts\assetbundles\patch_listbin.py",
  [string]$BackupDir,                                      # 缺省 = <StageRoot>\..\backup-<时间戳>
  [switch]$ApplyLive,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $BackupDir) { $BackupDir = Join-Path (Split-Path $StageRoot -Parent) "backup-$ts" }

function Step($n) { Write-Host "==== $n ====" -ForegroundColor Cyan }

# ---------- 0) 预检 ----------
Step "0 precheck"
if (-not (Test-Path $StageRoot)) { throw "StageRoot 不存在: $StageRoot" }
if (-not (Test-Path $ListBin)) { throw "ListBin 不存在: $ListBin" }
& $Py (Join-Path $DeployTools "probe_listbin.py") --list-bin $ListBin --json (Join-Path $PSScriptRoot "precheck.json") | Out-Null
Write-Host "list.bin 预检 OK（precheck.json）"

# ---------- 1) 备份现网（只读复制） ----------
Step "1 backup live"
New-Item -ItemType Directory -Force $BackupDir | Out-Null
Copy-Item (Join-Path $LiveRoot "list.bin") (Join-Path $BackupDir "list.bin") -Force
Write-Host "已备份 live list.bin → $BackupDir\list.bin"

# ---------- 2) patch 条目（只写暂存副本） ----------
Step "2 patch list.bin (stage)"
$patchArgs = @($LunarBasePatch, $ListBin)
if ($WhatIf) { $patchArgs += "--dry-run" }
& $Py @patchArgs
if ($LASTEXITCODE -ne 0) { throw "patch_listbin 失败" }

# ---------- 3) bump revision ----------
if ($NewRevision -gt 0) {
  Step "3 bump revision → $NewRevision"
  $bumpArgs = @((Join-Path $DeployTools "bump_listbin_revision.py"), "--list-bin", $ListBin, "--set", "$NewRevision")
  if ($WhatIf) { Write-Host "WhatIf: $bumpArgs" } else { & $Py @bumpArgs }
}

# ---------- 4) verify（old=live 备份, new=暂存, assets=暂存树） ----------
Step "4 verify_deploy"
$verArgs = @((Join-Path $DeployTools "verify_deploy.py"),
  "--old", (Join-Path $BackupDir "list.bin"),
  "--new", $ListBin,
  "--assets-root", $StageRoot,
  "--json", (Join-Path $PSScriptRoot "verify.json"))
if ($NewRevision -le 0) { $verArgs += "--no-revision-check" }
& $Py @verArgs
if ($LASTEXITCODE -ne 0) { throw "verify_deploy 失败（verify.json）" }

# ---------- 5) 原子替换（显式开关；红线下本任务禁用） ----------
if ($ApplyLive -and -not $WhatIf) {
  Step "5 apply live（原子替换）"
  Write-Host "将把暂存树与 list.bin 覆盖到 $LiveRoot" -ForegroundColor Yellow
  Copy-Item $ListBin (Join-Path $LiveRoot "list.bin") -Force
  robocopy $StageRoot (Join-Path $LiveRoot "assetbundle") /E /COPY:DAT /R:2 /W:2 | Out-Null
  Write-Host "替换完成。随后需重启 octo-cdn（或 admin reload）使 list.bin 生效；"
  Write-Host "bin.e 另行替换 assets\release\20240404193219.bin.e 并刷 mtime（见 README-JP.md runbook）。"
} else {
  Step "5 apply live（跳过）"
  Write-Host "未替换现网。验证通过后加 -ApplyLive 执行（或手工按 README-JP.md runbook）。"
}

Write-Host "runbook 完成。产物：precheck.json / verify.json / 备份 $BackupDir"
