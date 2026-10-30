# lunar-scripts-zh · README-JP（JP 客户端汉化 l10n 流）

> **定位**：在 **lunar-scripts-jp**（JP 客户端基线管线）**之上叠加 l10n 流**：文本管线 → 字体步骤 → 资源包 → 部署脚本 → 汉化 APK。
> 本仓**只收脚本与文档**（work 大产物不入库）；基线工具仍以 lunar-scripts-jp 为准，本仓不复制其 android/assetbundles/masterdata 管线本体，只在需要处置的位点做 l10n 侧封装。
> **红线**：不 `git init/add/commit/push`（项目最最后一次性提交）；`resources\` 原件、`D:\Downloads\20240404193219.bin.e` 基线、现网 lunar-tear 服务、真机设备不动；**providers.json（翻译供应商真实密钥）绝不入库**（`.gitignore` 已按 zh-l10n 约定排除 `providers.json` / `config/providers.json` / `config/*.local.json`；对外只提供 `config/providers.example.json` 形态）。

---

## 0. 与 lunar-scripts-jp 的叠加关系

```
lunar-scripts-jp（基线，不动）                 lunar-scripts-zh（本仓，l10n 叠加）
├─ android/      build_apk.py, patch_apk_jp.py   ├─ apk/           build_jp_zh.py + verify_fix3c.py（字体替换+重签名）
├─ assetbundles/ crypt/encrypt/patch_listbin     ├─ deploy/        patch_listbin/bump/probe/verify + runbook.ps1
├─ masterdata/   dump/patch/msgpack              ├─ resourcepack/  build_resource_pack.py（resource_dump-android-zh.7z）
├─ local/, colab/, docs/                         ├─ fonts/         charset 子集 + 四容器 payload 构建/校验
└─ keys/nier-jp.keystore（同 key 签名）           ├─ l10n/          mt_client/排除规则/术语表/fix 通用工具
                                                 └─ docs/, README-JP.md
```

- **同 key 升级**：汉化 APK 沿用 lunar-scripts-jp `keys/nier-jp.keystore`（= bunker-modmenu mod 菜单 key），同 key 覆盖安装保留数据；换 key 才需卸载重装。
- **加密对称化补丁**：octo v1(0x31) `encrypt_assetbundle.py` 掩 255 内容字节的修复，**lunar-base 已改**；lunar-scripts(-jp) 两份旧脚本副本仍是旧 2 行（见「已知问题」）。
- 消费侧：**lunar-tear server**（在线/现网）与 **bunker**（离线启动器，导入 resource_dump 的 `revisions/0`）共用同一套替换件。

---

## 1. 构建步骤（自上而下一次跑通）

### 1.1 文本管线（`l10n/`）
1. **抽取**：`dump_text.py --lang ja`（只读，三语键值 → jsonl）。
2. **排除/保护**：`build_exclusions.py` → `l10n/exclusions/rules.json`（R01–R20 排除规则）+ `protect_terms.tsv`（保护词/不译）+ `names.json`（名字词典源）。
3. **术语表**：`l10n/glossary/ui_glossary.tsv`（UI 统一词）+ `help_TERMS.md`（帮助域锁定词）；批次裁定（fix10 用户裁定/fix12 名字还原/fix13 尾巴）以 changes.jsonl 形式叠加。
4. **批量翻译**：`mt_client.py translate --providers azure_s0,...`（三家供应商/占位符保护/缓存 `mt-cache.json`/降级；密钥在 `zh-l10n/config/providers.json`，**不入库**）。
5. **fix 批次合成（通用工具，提炼自 fix4..fixF）**：
   ```powershell
   $py l10n\fix\apply_changes.py --base zh_base.jsonl --changes a_changes.jsonl b_changes.jsonl `
       --out zh_new.jsonl --out-changes merged_changes.jsonl --name-dictionary name_dictionary.json
   $py l10n\fix\build_bundles.py --zh zh_new.jsonl --changes merged_changes.jsonl `
       --server-root <lunar-tear\server\assets\revisions\0\assetbundle\text\ja> --lang ja `
       --lunar-base E:\NieRReincarnation\lunar-base --out-root <bundles_ja> --report build.json
   $py l10n\fix\qa_check.py --base zh_base.jsonl --out zh_new.jsonl `
       --old-terms old_terms.tsv --terms terms.tsv --codepoints <ui.codepoints> <story.codepoints> --report qa.json
   ```
   - `apply_changes.py`：L1 精确/L2 基线全行/L3 强置 三层命中 + 批次优先级 + 名字词典回填 + 规则终扫；幂等。
   - `build_bundles.py`：差异包整树布局、受影响包**全状态写入**、回读校验（改键一致 + 未改键不变）；打包链 = `probe_bundle_repack.py`（UnityPy+lz4+octo 对称加密）。
   - `qa_check.py`：占位符/SKIP 改动/哨兵/空值/真换行/假名残留/行首标点/全角句号/旧词残留/术语命中/字库缺字/行宽 全门禁；exit 0=全绿。
6. **终态**（2026-10-28 fixF）：`zh_ja_fixF.jsonl` 145,701 行 / 692 差异包 / QA 全绿 / Go 607 表 OK（详见 `zh-l10n\work\mt-run\fixF-final\FIXF-REPORT.md`）。

### 1.2 字体流水线（`fonts/`）
1. **字库盘点**：`glyph_integrity.py`（现网 4 个 TMP_FontAsset 全 Dynamic；RodinPro GB2312 一级仅 75.5% → 必须换字体）。
2. **charset 子集**：`build_fix4_charset.py` → `fix4_subset`（剧情 Regular 6.04MB）/ `fix4_subset_extA`（UI Medium+ExtA 7.95MB）；fix4 补 5 缺字（`− ⼀ ⽣ ⾏ ⾯`）后 3,226 字 100%。
3. **四容器 payload**：`build_fix4b_fonts.py` → `payload2/`（**UI=RodinPro→Medium+ExtA 子集、剧情=TalkingStd→Regular 子集、FOTK-YDHopeL/YDWingsM 两符号容器补换**）；字体源 = Noto Sans CJK SC 2.004（SIL OFL 1.1，CTAN 镜像 Regular/Medium/Bold OTF）。
4. **校验**：`verify_fix4b.py`（替换后读回 sha 一致、对象清单不变、字形 0 缺）+ `probe_ydhope_ydwings.py`（图17 □ 豆腐定位）。
5. **EN/JP 通用**：同一 payload 双端通用（JP/EN 的 4 个 Font 资源逐字节一致；替换后输出 sha 相同），只需维护一份。

### 1.3 资源包（`resourcepack/`）
```powershell
$py resourcepack\build_resource_pack.py `
    --original E:\NieRReincarnation\resources\resource_dump_android.7z `
    --out      E:\NieRReincarnation\zh-l10n\work\release-jp\resource_dump-android-zh.7z `
    --text-ja  E:\NieRReincarnation\lunar-tear\server\assets\revisions\0\assetbundle\text\ja `
    --bin-e    E:\NieRReincarnation\zh-l10n\work\mt-run\final2\bin_zh_final2.bin.e `
    --help-ja  <原版/回滚态 help/ja 树> `
    --patch-tool E:\NieRReincarnation\lunar-base\scripts\assetbundles\patch_listbin.py `
    --seven-zip  <7-Zip 22+ 的 7z.exe> --revision 829 --work-dir <staging> --apply
```
- **包内容**（服务器资源树汉化件）：`revisions/0/assetbundle/text/ja/**`（7,012 包终态）+ `revisions/0/assetbundle/ui/help/ja/**`（原版 310 本轮回滚态）+ `revisions/0/list.bin`（原版基 + text/ja 条目刷新 + revision bump）+ `release/20240404193219.bin.e`（汉化 bin.e）。
- **7-Zip 版本要求（重要）**：**必须 7-Zip 22+**。32 位 7-Zip 9.x 对 14.9GB solid 包执行 `u` 会 `Unknown Error`（实测）；本仓构建脚本对7z仅做子进程调用，把路径用 `--seven-zip` 指定。
- 原版 dump **一字节不动**：先整文件 copy 成工作副本（sha256 双端核对）再 `7z u`。

### 1.4 汉化 APK（`apk/`）
```powershell
$py apk\build_jp_zh.py    # 解包 APK → 替换 4 个字体容器 payload2 → 重打包 → zipalign → 同 key 签名
$py apk\verify_fix3c.py   # 62 串抽查/证书指纹/私服 10 处/字体容器 sha 校验
```
- 产物形态：`nier-mod-menu-jp-font-fix3c.apk`（fix3c=四容器 payload2 + 43 处漏译弹窗族；fix3b=弹窗族；fix3=基础字体替换）。
- 签名 = `keys/nier-jp.keystore`（与 mod 菜单同 key，覆盖安装保留数据）。
- **推荐路径**：手工多步已被 `jp-client/` 一条流水线取代，见下章「JP 客户端构建」。

---

## JP 客户端构建（`jp-client/` 一条流水线）

> 目标：干净机器上**一条命令**产出「私服补丁 + 汉化」JP 客户端 APK（= 现网 fix3c 等价物）。
> 布局/基线事实见 [`jp-client/README.md`](jp-client/README.md)；构建脚本、fix3 表、字体 payload 权威副本、
> 验证脚本、keystore 全部自包含在 `jp-client/`（`MANIFEST.json` 构建前自动校验 sha256）。

### 前置依赖（干净机器）

| 依赖 | 版本 / 定位 | 说明与坑 |
|---|---|---|
| Python | 3.11+；本机 `C:\Python314\python.exe` | **用 base Python 跑构建**，不要用 `zh-l10n\.venv\Scripts\python.exe`（见「常见故障」①） |
| UnityPy（+ lz4） | 1.25.x | base Python 缺 UnityPy 时由 `jp-client\toolpaths.json` 的 `unitypy_site_packages`（`zh-l10n\.venv\Lib\site-packages`）挂 PYTHONPATH；干净机器直接 `pip install UnityPy lz4` 即可（TextAsset 重写用） |
| JDK | 21（本机 Adoptium `jdk-21.0.11.10-hotspot`） | `toolpaths.json` → `java_home` |
| Android SDK build-tools | 34+（`zipalign`、`lib/apksigner.jar`） | `toolpaths.json` → `android_home`，自动选最新 build-tools |
| apktool | `apktool.jar`（本机 `E:\NieRReincarnation\jp\apktool.jar`，3.0.2） | `toolpaths.json` → `apktool_jar` |
| 7-Zip 22+ | 仅**资源包**步骤（§1.3）需要 | **坑**：从 `resources\APK Easy Tool v1.60 Portable.zip` 解出 `Resources/7z.exe`（22.00）用；系统 32 位 7-Zip 9.x 对 14.9GB solid 包 `u` 报 `Unknown Error`（实测）。**APK 构建流水线本身不调用 7z** |
| Gradle / NDK | **不需要** | mod 菜单注入件（smali + libniermenu.so）已内置 `jp-client\modmenu-payload\`；只有改菜单源码才回 mod-menu 仓库 `gradlew assembleDebug` 再 `apktool d` 刷新注入件 |
| 原版 JP APK | `resources\NieR Re[in]carnation_3.7.1_JP.apk`，254,131,762 B，sha256 `25b6326c…653609` | **只读引用**；流水线首尾各校验一次 sha256（⑥），改动即失败 |

### 一条命令

```powershell
# 入参=原版 JP APK；出参=签好的汉化客户端 APK + verify 报告 + logs/（每步失败即停、日志落盘）
C:\Python314\python.exe jp-client\build_jp_client.py --apk "resources\NieR Re[in]carnation_3.7.1_JP.apk" --out <输出.apk>
# 等价 PowerShell 入口（runbook）：
pwsh -File jp-client\runbook.ps1 -Apk "resources\NieR Re[in]carnation_3.7.1_JP.apk" -Out <输出.apk>
```

流水线步骤（build_jp_client.py 0-7）：MANIFEST/工具/UnityPy 预检 → apktool d → 私服补丁
（`patches\patch_apk_jp.py`，JP 3.7.1 RVA + auth 动态）→ fix3 内置串（`fix3\patch_fix3.py apply --tier all`）
→ 字体 payload 四条目 → mod 菜单注入 → apktool b → zipalign → apksigner（nier-jp key）→ 验证门。
默认私服地址 `--grpc 192.168.2.6:8003 --http 192.168.2.6:8080 --auth 192.168.2.6:3000`（同 fix3c）。

### 客户端识别与命名契约（L3a）

> 双前端共用模块 [`shared/detect_client.py`](shared/detect_client.py) +
> [`shared/manifest_sidecar.py`](shared/manifest_sidecar.py)；口径 = BUNKER-ADAPT-PLAN §3/§8/§9。

**① 客户端自动识别（region 三元组硬断言，fail-fast）**：输入 APK 按三元组判定，
被 `build_jp_client.py`（jp 流水线）与 `build_en_zh.py`（en 流水线）调用——
识别 → 自动选 key / 补丁集 / 产物名；未知客户端、三元组不符（**含改 1 字节**）、
region 矛盾（EN 包喂 jp 流水线等）一律 `SystemExit` 拒建，不产出任何文件。

| region | 包名（APK 内 axml 解析） | bytes | sha256 | 证据面 |
|---|---|---|---|---|
| **jp** | `com.square_enix.android_googleplay.nierspjp` | 254,131,762 | `25b6326c…653609` | metadata 特征 `api.app.nierreincarnation.jp` 佐证 |
| **en** | `com.square_enix.android_googleplay.nierspww` | 263,571,029 | `9ded0797…c9209` | metadata 特征 `api.app.nierreincarnation.com` 佐证 |

**② 产物命名契约**：APK 产物按客户端自动命名——
**jp 流水线出 `nier-jp.apk`、en 流水线出 `nier-en.apk`**（缺省 `--out` 产物名）。
`--out` 语义保留：显式指定时以 `--out` 为准（sidecar 仍按契约登记产物名）。
Colab notebook 输出同契约（`MyDrive/nier-jp.apk`）。**bin.e 仍「文件名前后不变」**
（输出名==输入名，如 `20240404193219.bin.e`，三处强制不变）。

**③ manifest sidecar**：每产物附 `<产物名>.manifest.json`（如 `nier-jp.apk.manifest.json`），
字段：region 三元组 / 产物 sha256 / 产物 size / 签名证书指纹（含比对结果）/ 补丁计数 /
验证门结果 / 构建时间 / **RVA 表版本占位** / 输入 APK sha（+ bin.e sha256 成对交付时）。
生成器 [`shared/manifest_sidecar.py`](shared/manifest_sidecar.py)（schema `nier-product-manifest/v1`，
落盘后自检 sha/size/证书/验证门）。

**④ 签名 key 分治 + 验证门证书断言**：按识别结果自动选 key——
jp→`jp-client/keys/nier-jp.keystore`（证书 `EE:C2:3B…98A2FE`）、
en→`en-client/keys/nier-en.keystore`（证书 `7D:79:2C…A4:A1:73`，= debug.keystore 收编）；
验证门对签名证书做指纹比对，不符即失败。


### 验证门（build 后自动跑；`verify_jp_client.py` 可独立复跑）

| # | 检查项 | fix3c 基准口径 |
|---|---|---|
| ① | apksigner v2+v3 且证书 `EE:C2:3B…D3D98A2FE` | cert `eec23be0…d98a2fe` |
| ② | fix3 **62/62 串**逐条命中（TA 68 + metadata 7 = 75 处；legacy 23 + 新 39） | entries_ok 62/62 |
| ③ | metadata stringLiteral 回读（公告/关闭/取消 + 播放影片族共 7 值） | 7/7 |
| ④ | **四**字体条目 sha256 = payload | `c97a4319…`/`5ed20794…`/`ad690f4b…`/`853ac67a…` |
| ⑤ | 私服 IP `192.168.2.6` **10 处**（metadata 7 + classes.dex 2 + network_config 1） | total_hits 10 |
| ⑥ | 原版 APK sha256 前后不变 | `25b6326c…653609` |
| ⑦ | `zipalign -c -p 4` 对齐校验 | exit 0 |
| ⑧ | **与 fix3c 基准 APK 等价性对照**：先试整文件逐字节；否则逐 zip 条目 | 见下 |
| ⑨ | **显示 RVA 表按客户端选对**（display_patch.c 区服一致性识别）：包名 / 清单 `org.veritr1x.bunker.REGION` meta / region.py 三元组 与 libil2cpp.so 大小交叉核对，矛盾/未知 fail-fast 拒补丁；同一套 JP/EN 事实表（`shared/detect_client.py` REGIONS `libil2cpp_size`）无漂移 | 离线证据：`zh-l10n\work\diag-rva-display\l3b-test\test_display_rva.py` + `verify_en_source.py` + `bunker\android\tools\test_display.py` 全绿。**协同点**：任务 C L6 将本门脚本化并入 `verify_jp_client.py` / build.py 产物验证门时按本行口径调用（本行=清单依据+离线证据，暂不在 verify_jp_client.py 内自动跑） |

等价性对照方法：整文件 sha256 相同 → 「逐字节一致」（最优）；否则按 zip 条目逐项比
（条目名集合、每条目解压内容 sha256、zip 时间戳分列）+ ①-⑤ 事实逐项比对。
**实测（2026-10-28 自测）**：4,317/4,317 条目内容逐字节一致（含 META-INF 内容），仅
4,317 条 zip 时间戳与 v2/v3 签名块（APK Signing Block）不同 → 「除构建时间戳外逐项一致」，
verdict=`identical except META-INF signature / zip timestamps`，facts_identical=True。

### 常见故障

1. **venv python 写 Mod_Menu 受限 / ACL**：`zh-l10n\.venv\Scripts\python.exe` 对
   `NieR-Re-In-Carnation-Mod_Menu\` 子树偶发写入拒绝（Windows ACL，见 work\acl-recovery\）。
   **构建一律用 base `C:\Python314\python.exe`**；UnityPy 走 `toolpaths.json → unitypy_site_packages`
   挂 PYTHONPATH（与 build-fix3b/3c 既定口径一致）。本流水线产物写 `--out`/`--logs`/`--work` 指定目录，
   不再写 Mod_Menu 子树。
2. **签名覆盖官方需卸载重装**：原版 Google Play 版用官方证书，本流水线用 nier-jp key
   （证书不同）→ **覆盖安装会报签名冲突，必须先卸载再装**；此后 fix3c↔新构建之间是同 key
   （`keys/nier-jp.keystore`，alias nier），覆盖安装保留数据。换 key 才需清数据。
3. **fix3「同值不同译」按键替换原因**：fix3 是**值级**替换（TextAsset `key:value` 行只换 value，
   metadata stringLiteral 原地替换）——同一日文原值出现在多个 key 时必然共享同一译文；
   若业务上要求「同值不同译」，值级机制做不到，`patch_fix3.py` 会以「表冲突」拒绝
   （`repl_map`：同 source 两个不同 target 即 SystemExit）。处理口径：统一译文，
   或把该 key 从表中拆出单独处置（表内 `keys` 列记录共享该值的键位）。
   metadata 侧另有限制：**只许变短**（NUL 填充回写 length），译文长于原文会 SKIP_TOO_LONG。
4. **auth-host 长度 WARN**：`--auth 192.168.2.6:3000`（16B）> `facebook.com`（12B）时 metadata 的
   facebook 替换跳过（smali/AuthHost 动态仍生效），日志 `[!] WARN: auth-host … longer …` 属已知，
   不是失败。
5. **fix3 自检失败拒打包**：TextAsset/metadata 抽查未命中即 SystemExit，看 `logs/` 里 apply_report
   与自检 JSON；多为表被改动（MANIFEST 校验会先拦）或 APK 版本不符。

### 自测记录

2026-10-28 完整流水线自测：产出 `zh-l10n\work\apk\jp-client-build-test\nier-mod-menu-jp-font-fix3c-buildtest.apk`
（273,436,239 B，与 fix3c 同体积），验证门 ①-⑦ 全过 + ⑧ 等价性「除时间戳外逐项一致」；
报告见 [`zh-l10n\work\release-jp\JP-CLIENT-BUILD.md`](../zh-l10n/work/release-jp/JP-CLIENT-BUILD.md)。
2026-10-28 成对交付（APK+bin.e）自测见下章「成对交付」与 `JP-CLIENT-BIN-COLAB.md`。

---

## 成对交付 APK + bin.e（`jp-client/` 流水线第 8 步）

> 目标：**一次命令**产出「目标 APK + 配套汉化 bin.e」两个文件（"就像原 lunar-scripts 一样，
> 可以编辑 apk 和 bin.e，最后得到目标 apk 和配套 bin.e"）。bin.e 侧可选编辑项**逐项对应**
> 原版 lunar-scripts `patch_masterdata.py`（= notebook「Patch Master Data」cell 的实际编辑面），
> 编辑器语义遵守 bunker 核实结论（**格子不冲文件会冲、文本格字节照搬、只动 date 列**）。
>
> **硬性要求：bin.e 文件名前后不变**——输入 bin.e 叫什么（如 `20240404193219.bin.e`），
> 产出就叫什么；可换目录，不可改文件名。`build_jp_client.py` / `build_bin_e.py` / Colab
> notebook 三处均强制（名字不符即拒绝/自动纠正）。

### 一条命令（成对）

```powershell
C:\Python314\python.exe jp-client\build_jp_client.py `
  --apk  "resources\NieR Re[in]carnation_3.7.1_JP.apk" `
  --out  <输出.apk> `
  --bin-e     "zh-l10n\work\mt-run\fix6-text\bin_zh_fix6.bin.e" `
  --out-bin-e <输出\bin_zh_fix6.bin.e> `
  --bin-edit  jp-client\bin-edit.default.json `
  --orig-bin-e "zh-l10n\work\masterdata\00-baseline.bin.e"
# 等价 runbook（-OutBinE 省略则自动取 -BinE 同名；文件名前后不变）：
pwsh -File jp-client\runbook.ps1 -Apk <原版.apk> -Out <输出.apk> `
  -BinE <原版或汉化.bin.e> -OutBinE <同名.bin.e> -OrigBinE <原版20240404193219.bin.e>
# bin.e 也可以单独构建（一条 runbook 串起两者时用上面的组合形态）：
C:\Python314\python.exe jp-client\build_bin_e.py --bin-e <原版或汉化bin.e> `
  --out-bin-e <同名.bin.e> [--bin-edit <编辑配置>] [--text-from <汉化基>] [--orig-bin-e <原版>]
```

### bin.e 侧内容与编辑项（对齐原版）

* **内容基 = 汉化 masterdata**：权威汉化基 `zh-l10n\work\mt-run\fix6-text\bin_zh_fix6.bin.e`
  （sha256 `7dba416a…b664`）。两种喂法等价（实测产出逐字节一致）：
  1. `--bin-e bin_zh_fix6.bin.e`（直接以汉化基为输入）；
  2. `--bin-e <原版20240404193219.bin.e> --text-from bin_zh_fix6.bin.e`
     （原版输入 + 5 张文本表**逐字节移植**，"文本格字节照搬"）。
* **可选编辑项**（`--bin-edit` JSON，逐项 true/false；缺省 = 原版全量编辑面）：

  | 编辑项 | 对应原版 patch_masterdata.py | 作用 |
  |---|---|---|
  | `extend_end_dates` | `PATCH_COLUMNS`（33 表 date 列） | 活动/商店/卡池等 EndDatetime 2020-2029 → **2030-12-31**（含 gimmick 档期 cutoff 过滤） |
  | `empty_maintenance` | `EMPTY_TABLES` | `m_maintenance` 清空（不再弹维护横幅） |
  | `add_labyrinth_unlock` | `TABLE_ROW_ADDITIONS` | `m_event_quest_unlock_condition` 补 `[12,0,0,1,21,0]`（迷宫进支线菜单；幂等） |
  | `window_labyrinth_seasons` | `patch_labyrinth_seasons` | `m_event_quest_labyrinth_season` 每章恰 1 个赛季开窗 |
  | `dedup_gimmick_schedules` | `patch_gimmick_sequence_schedules` | `m_gimmick_sequence_schedule` 每 FirstGimmickSequenceId 1 条活跃（黑鸟可见） |

  （`m_omikuji` 恒跳过 = 原版 `SKIP_TABLES`；只对 `0xd3` int64 **date 列**原地写、
  字符串列 walker 跳过、未改表字节照搬 → 文本格永不落刀。）
* **编辑器语义**（bunker 核实结论）：格子不冲（未改表照搬 + 表内只动 date 列）、文件会冲
  （输出整体新文件；**别拿未汉化 bin 当重建基线**）、只动 date 列的坑（不改非日期列编码宽度）。

### 输出 bin.e 三重断言（不过即失败，不落盘）

| # | 断言 | 口径 |
|---|---|---|
| A | **文本格 = 汉化基逐字节** | 5 张文本表（m_dokan_text/m_gift_text/m_navi_cut_in_text/m_webview_mission_title_text/m_webview_panel_mission_complete_flavor_text）raw blob 全等 |
| B | **结构校验（AES/TOC/5 表/LZ4 全过）** | 体积 (1MB,32MB)、AES-256-CBC 解密、TOC 越界检查、m_costume/m_weapon/m_event_quest_chapter/m_shop/m_mom_banner 齐全、逐表 LZ4 可解、表块连续（= bunker `validate_master` 口径 + 布局检查） |
| C | **与原版 bin.e 的 diff 只在预期表** | 变化表 = {汉化基⊕原版 差异表（4 张文本表）} ∪ {编辑项动到的表（31 张）}；逐表格子级复核只出现「date 列变化 / 尾部补行 / 指定表清空」三种白名单操作 |

**对齐原版的硬证据**：对原版 `20240404193219.bin.e`（`60555788…f270778`）跑全量编辑项，
产出 sha256 = `0a8b8cd4…c9918`，与原版 lunar-scripts 仓捆绑的 `20240404193219.bin.e`
**逐字节一致**——本编辑面与原版 `patch_masterdata.py` 完全等价。

### 产出物落盘位置

| 文件 | 位置 |
|---|---|
| 目标 APK | `--out`（同流水线） |
| 配套 bin.e | `--out-bin-e`（**文件名前后不变**：必须与输入 `--bin-e` 同名，如 `20240404193219.bin.e`） |
| bin.e 报告 | `--out` 同级 `logs\<ts>-bin-e-report.json`（三重断言 + 逐表 diff + 格子级分类） |
| evidence | `logs\<ts>-evidence-jpclient.json`（含 `bin_e` 节） |

### 常见故障（bin.e 侧）

1. **bin.e 依赖缺失**：`pip install pycryptodome msgpack lz4`；本机走
   `toolpaths.json → bin_e_site_packages`（缺省兜底 `lunar-base\.venv`）挂 PYTHONPATH。
2. **断言 A 失败**＝文本格被动过——检查输入是否给了非汉化基、或误用了会重打包文本表的工具；
   本工具对未改表**字节照搬**，正常路径不可能触发。
3. **断言 C 失败**＝diff 出现预期外的表——看报告 `diff_vs_orig.unexpected_tables`，
   多为 `--orig-bin-e` 给错参照（应给原版 `60555788…`）。
4. **重复跑幂等**：编辑项第二次跑全部 0 变化（date 值已在 2030-12-31 窗口外/行已存在）。

---

## Colab 构建（`jp-client\colab\android_lunar_zh.ipynb`）

> 在 Google Colab 上产出**成对两个目标文件**（目标 APK + 配套汉化 bin.e）。
> **操作流程与原版 android_lunar 系列 notebook 一字不变**：上传 COLAB → 配置原 APK、bin.e 在
> Google Drive 的路径 → 填写局域网 IP → 产出两个目标文件。改编点只有输出带汉化。

### 操作步骤（截图式文字版）

1. **本机打包补丁包**（一次性）：
   `pwsh -File jp-client\colab\make_payload_zip.ps1 -OutZip <本机>\jp-client-payload.zip`
   （含脚本/fix3 表/字体 payload 28MB/modmenu/keystore/编辑配置；构建产物不进包）。
2. **上传 Google Drive**，建议目录：
   ```
   MyDrive/NieR-JP-zh/
   ├─ NieR Re[in]carnation_3.7.1_JP.apk     （原版 APK，只读）
   ├─ bin_zh_fix6.bin.e                     （汉化基 masterdata）
   ├─ 20240404193219.bin.e                  （原版 bin.e，断言 C 参照，可选）
   ├─ jp-client-payload.zip                 （第 1 步产物）
   └─ out/                                  （产出目录）
   ```
3. **上传 notebook**：Colab → Upload → `jp-client\colab\android_lunar_zh.ipynb`。
4. **Configuration cell**（第 1 个代码格）填参数：
   * `apk_source` = `MyDrive/NieR-JP-zh/NieR Re[in]carnation_3.7.1_JP.apk`
   * `masterdata_source` = `MyDrive/NieR-JP-zh/bin_zh_fix6.bin.e`
   * `payload_zip` = `MyDrive/NieR-JP-zh/jp-client-payload.zip`
   * `orig_bin_e_source` = `MyDrive/NieR-JP-zh/20240404193219.bin.e`（可选）
   * **填写局域网 IP**：`grpc_addr`/`http_addr`/`auth_host`（如 `192.168.2.6:8003` / `:8080` / `:3000`）
   * 输出路径：`output_apk_drive_path` = `MyDrive/NieR-JP-zh/out/target-zh.apk`、
     `output_bin_drive_path` = `MyDrive/NieR-JP-zh/out/<输入 bin.e 同名>`
     （**文件名前后不变**：只可改目录；文件名会被自动纠正为 `masterdata_source` 的同名，
     如输入 `bin_zh_fix6.bin.e` → 产出 `bin_zh_fix6.bin.e`）
   * bin.e 可选编辑项 5 个 true/false 开关（缺省全开 = 原版编辑面）。
5. **Runtime → Run all**；弹出授权时允许 Drive 挂载。依赖安装（pip/apt/wget）全自动。
6. **产出**：`out/target-zh.apk`（目标 APK）+ `out/<输入 bin.e 同名>`（配套汉化 bin.e，
   文件名前后不变）自动存回 Drive，并触发浏览器下载一份。APK 侧=fixed 私服补丁+fix3+字体+mod menu（nier-jp key）；
   bin.e 侧=汉化 masterdata+编辑项（三重断言在 Colab 内同样全过才落盘）。

### payload 装载方案（为什么不是 base64 内嵌）

* 补丁脚本/表/字体/modmenu/keystore **全部从 Drive 的 `jp-client-payload.zip` 装载**——
  对应原版 notebook 的 `git clone` 依赖装载（本仓不提交/不外发，git 路线不可用）；
* 大件（**字体 28MB / modmenu 1.5MB**）不进 notebook：base64 内嵌会把 ipynb 膨胀到 40MB+，
  Colab 上传慢、编辑器卡顿、易截断；zip 走 Drive 既稳又快（实测解包 <5s）；
* zip 缺件会在 `Load patch payload` cell **fail-fast**（`_REQUIRED` 15 项清单），不会半路才发现。

### notebook cell 清单（7 格，与原版结构对应）

| # | id | 类型 | 对应原版 cell | 内容 |
|---|---|---|---|---|
| 0 | md-intro | markdown | 原版 md intro | 中文使用说明 + payload 装载方案 + 输出表 |
| 1 | cfg-config | code | Configuration | 参数（Drive 路径/编辑项/IP/输出）+ `load_config/check_config` + Drive 挂载 |
| 2 | cfg-deps | code | Install dependencies | pip pycryptodome/msgpack/lz4/UnityPy + apktool/zipalign/apksigner |
| 3 | cfg-payload | code | （新增，对应 git clone 的依赖装载） | `load_payload`：Drive zip → `/content/jp-client` + `_REQUIRED` fail-fast |
| 4 | patch-apk | code | Patch APK | `patch_apk_flow`：解包→私服→fix3→字体→mod menu→重建→对齐→nier-jp 签名 |
| 5 | patch-bine | code | Patch Master Data | `patch_bin_e_flow`：汉化基+编辑项+三重断言 → `20240404193219.bin.e` |
| 6 | save-outputs | code | Save to Google Drive | `save_outputs`：两个目标文件落 Drive + 浏览器下载 |

### 本地校验（不真上 Colab）

```powershell
C:\Python314\python.exe jp-client\colab\test_colab_functions.py
```
= nbformat 结构校验（可上传）+ 关键函数对 fixtures 全跑：T1 配置校验、T2 payload zip 打包/解包、
**T3 APK 补丁对原版 APK**（私服+fix3+字体+mod menu 抽查全命中）、**T4 bin.e 编辑对汉化基**
（三重断言全过）、T5 双文件落盘。报告：
`zh-l10n\work\release-jp\staging\colab-test\colab-test-report.json`（详见 `JP-CLIENT-BIN-COLAB.md`）。

---

## 2. 部署 runbook（现网 lunar-tear；`deploy/runbook.ps1` 已脚本化）

> 完整脚本：`pwsh -File deploy\runbook.ps1 -StageRoot <staging\revisions\0> -ListBin <staging\list.bin> -WhatIf`
> 脚本默认**只动暂存副本**；`-ApplyLive` 才原子替换现网（人工确认后用）。

1. **预检**：`probe_listbin.py` 记录 revision 与基线 hash；sha256 备份 `list.bin`、被替换 bundle、`bin.e`（带时间戳，放 `work\device\deploy-<ts>\backup\`）。
2. **暂存**：把交付的 `revisions/0/assetbundle/**` 复制到暂存树（text/ja + help/ja + …）。
3. **patch 条目**：`lunar-base\scripts\assetbundles\patch_listbin.py <staging\list.bin>`（protobuf 全量刷新在盘差异；缺盘文件不动）。定点小批可用 `deploy\patch_listbin_stdlib.py --names changed.txt`（无 protobuf 兜底）。
4. **bump revision**：`deploy\bump_listbin_revision.py --set <N>`（**N 必须大于客户端见过的任何 revision**；817→16383 内 2 字节 varint 安全）。客户端按本地 revision 拉 `/v1/list`，不 bump 则继续用旧缓存（旧 md5）不换文本。
5. **verify**：`deploy\verify_deploy.py --old <backup\list.bin> --new <staging\list.bin> --assets-root <staging>`（changed 条目 size+md5 与磁盘一致、urlFormat 不变、revision 增大）。
6. **原子替换**：暂存树 robocopy 覆盖 `lunar-tear\server\assets\revisions\0\assetbundle\`，list.bin 原子替换；**替换 bin.e**（`assets\release\20240404193219.bin.e`，文件名不可改）并**刷新 mtime**。
7. **生效**：重启 octo-cdn（list/bin 校验）；lunar-tear 重启（masterdata 内存重载；bin.e 版本号 = `20240404193219_<mtime ms>`，mtime 变 → 客户端自动重下）。
8. **真机复验**：启动→自动更新→中文 UI/剧情/帮助→战斗→商店/抽蛋→Deck；logcat 无 FATAL/ANR。

**文本包与 bin.e 必须成对部署**；只换其一会“半中半日/英”。

---

## 3. 回滚

| 层 | 回滚动作 | 依据 |
|---|---|---|
| text/ja、ui/help/ja | 恢复部署备份的三语树（`work\device\deploy-<ts>\backup\assetbundle-text-ja`、`assetbundle-ui-help\ja`）→ 重新 patch_listbin + bump + 重启 octo | 交付件 `SHA256SUMS` 可验完整性 |
| list.bin | 恢复备份 `list.bin`（注意 revision 可能回退，客户端需 bump 后才会换回） | runbook 第 1 步备份 |
| bin.e | 恢复 `20240404193219.bin.e.bak-<ts>` → **刷 mtime** → 重启 lunar-tear | §2 第 6 步 |
| 字体 APK | 卸载汉化 APK → 装原版/fix3 前版本（**同 key 覆盖安装保留数据**；换 key 才需清数据） | §9.7 数据/登录态 |
| 服务端机制 | lunar-tear 二进制 `.bak-before-bport`（B 方案机制移植前）3 分钟回滚 | 交接纪要 §7 |

一键回滚脚本：`deploy\runbook.ps1` 的 `-BackupDir` 复用即回滚源（恢复 + patch + bump 一轮）。

---

## 4. 已知问题（截至 2026-10-28，留后续）

1. **帮助中文包闪退（已回滚原版）**：octo v1(0x31) 加密比解密多掩 1 字节 → TypeTree 损坏 → Unity SIGTRAP。`encrypt_assetbundle.py` 上游已修（lunar-base）；**lunar-scripts / lunar-scripts-jp 两份旧脚本副本仍待套同款 2 行补丁**。本轮交付 help=原版 310 回滚态；fix5-help 中文版（310 包 9,340,795B）已在现网 10-26 部署，是否纳入下一版资源包待用户点头。
2. **bin.e 版本差异**：任务基准= `bin_zh_final2`（`a8c962aa`，含 md 微修 8 格）；现网实测= `bin_zh_fix6`（`7dba416a` = final2 + 2 键 LT1/LT3 4 格：`m_dokan_text#1923` 销售→出售 等，10-27 19:13 写入）。**不要换 `bin_zh_fix4f`**（`ddb260b7`，缺 md 微修会回退）。
3. **词面小尾巴**（fixF 已知局限）：`ui.Outgame.Quest.DeckPower.Lock`「最大战斗力 {0}」→ 建议「最高战力{0}」小批；名字域外词典机翻名 5,636 处（shop.item.name 等）留后续；mission 名字丢失 4 行需句式级重写；「分数等级」连写 470011-30 等未统一「分数评级」；剧情族「报酬/回报」独立语义 18 行按裁定保留。
4. **机制缺口**（与汉化无关但影响体验）：月票时间门控（MissionPass 12 期档期已结束；方案 A bin.e 延展 / B bunker 日历移植）；扭蛋档期借期（gacha.go 已修，复活 158 档期）；18 个客户端可调未实现 RPC（任务领奖×2/好友×8/SkipQuestBulk 等）；unknown 页签 2 键已补（「收集任务」/「特别」暂定名待正名）。
5. **EN 线**（离线交付未部署）：ko 槽 6,585 包 + EN APK；**APK 内置表 ko 段→中文**待做；18 键 ko 缺行；263 KO 独有键保韩文。
6. **字体渲染**：SC 与 JP face 区域变体 851/1,709 字按简中字形渲染（可读、不影响功能）；TMP 预烘 843 字满则 □ 需扩容（图 17 类）。

---

## 5. 基线与产物索引

| 项 | 值 |
|---|---|
| 客户端 | NieR Re[in]carnation 3.7.1 JP（原版 APK `resources\NieR Re[in]carnation_3.7.1_JP.apk` 254,131,762B） |
| 原版 dump | `resources\resource_dump_android.7z` 14,928,186,871B，sha256 `06de0ba5…80e6`（12 solid blocks，仅含 `revisions/0`：assetbundle+resources+info.json+list.bin；**不含 bin.e**） |
| text/ja 终态 | 7,012 包 / 13,202,271B（fixF；zh_ja_fixF.jsonl 145,701 行） |
| help | 原版 310 包 / 9,351,677B（本轮回滚态）；fix5-help 中文 310 包 / 9,340,795B（现网） |
| bin.e | `bin_zh_final2` 7,685,904B sha256 `a8c962aa…cb47`（= 原版+补行 138+3,494 格 LT1/LT3+md 微修）；现网 `bin_zh_fix6` `7dba416a…b664` |
| list.bin | 原版 26,721,218B（rev 817）→ 刷新 text/ja 6,583 条目 + rev 829（现网 rev 828） |
| 字体 payload | `work\fonts-fix4\out2\payload2\`（UI c97a4319… / STORY 5ed20794… + YDHopeL/YDWingsM） |
| 汉化 APK | fix3c `2f363f79…`（273MB；fix3b 48c62868…/fix3 基础） |
| 资源包 | `zh-l10n\work\release-jp\resource_dump-android-zh.7z`（本仓 `resourcepack\build_resource_pack.py` 产物） |
