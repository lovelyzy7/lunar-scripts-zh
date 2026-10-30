# en-client — EN 客户端汉化管线（脚本+文档归档）

> 归档时间：2026-10-29　来源：`zh-l10n\work\en-apk\`、`zh-l10n\work\deploy\`、`zh-l10n\work\fonts-fix4\`
> 与 `jp-client/`（JP 管线）并列：本目录收 **EN 客户端** 汉化管线的脚本归档与说明；
> **L3a 起** `keys/nier-en.keystore`（=debug.keystore 复制收编）与 `patches/` 私服补丁权威副本**入库**（MANIFEST 登记 sha256）。
> 相关记录报告（不复制，保留在原处）：`zh-l10n\work\en-apk\EN-APK-REPORT.md`、`EN-APK-KO-REPORT.md`、`EN-APK-FIX3L-REPORT.md`、`EN-APK-FIX4-REPORT.md`、`SHA256SUMS`。

---

## 0. 客户端识别与命名契约（L3a，与 jp-client 同步）

> 共享模块 [`../shared/detect_client.py`](../shared/detect_client.py) + [`../shared/manifest_sidecar.py`](../shared/manifest_sidecar.py)；
> 口径 = BUNKER-ADAPT-PLAN §3/§8/§9；README-JP.md「客户端识别与命名契约（L3a）」为总纲。

- **识别（fail-fast）**：`build_en_zh.py` 构建前按 region 三元组（axml 包名
  `com.square_enix.android_googleplay.nierspww` + 263,571,029B + sha `9ded0797…c9209`）
  硬断言输入必须是 EN 客户端；未知客户端、改 1 字节、误喂 JP 包 → **拒建**，不产出任何文件。
- **产物命名契约**：缺省产物名 **`nier-en.apk`**（jp 流水线出 `nier-jp.apk`）；
  `--out` 语义保留（显式指定以 --out 为准）。
- **manifest sidecar**：`nier-en.apk.manifest.json`——region 三元组 / sha256 / size /
  签名证书指纹（比对 **7D:79:2C…A4:A1:73**）/ 补丁计数 / 验证门结果 / 构建时间 /
  RVA 表版本占位 / 输入 APK sha。
- **key 自动选**：region=en → `keys/nier-en.keystore`（alias `androiddebugkey` / pass `android`，
  = Mod_Menu `en-client\keys\debug.keystore` **复制收编、原件保留勿删**，血统见 [`keys/README.md`](keys/README.md)）；
  验证门做证书指纹断言。
- **MANIFEST 预检**：`MANIFEST.json` + `_gen_manifest.py`（镜像 jp-client 口径；
  权威副本 = `patches/patch_apk_en.py`、`patches/patch_auth_dynamic_en.py`、`keys/nier-en.keystore`）。

---

## 1. EN 汉化策略

### 1.1 槽位策略（ko 槽写中文）

| 资源 | 处置 |
|---|---|
| `text/en` | **不动**（保留英文） |
| `text/ko` | **写中文**（EN 源译文；玩家在语言设置选 **「한국어」** 标签即见中文，「한국어」标签本身保留） |
| masterdata LT1 | zh（实测 LT1 全 CJK：dokan 1304/1304、gift 216/216、navi 211/211、flavor 16/16） |
| masterdata LT2 | **不动**（英文） |
| masterdata LT3 | **zh**（EN 客户端选韩语槽时读 **LT3**） |

- EN 端选韩语读 **LT3**：`LanguageType` 枚举 0=UNKNOWN/1=JA/2=EN/3=KO（`dump.cs:762284-762292`，查找 API `FindByDokanTextIdAndLanguageType((Id,LanguageType))`；`Dark.Kernel.Language.GetLanguageType()` + `KoreanPath` 佐证）。
- masterdata `bin.e` **无需补丁**：现网 `20240404193219.bin.e`（sha `7DBA416A…`）LT3 已是中文、LT2 英文未动（核对见 `zh-l10n\work\en-mt\EN-PIPELINE-REPORT.md` §1.1）。MD01 挿話 8 标题（`m_webview_mission_title_text`）LT1 日文原样 / LT2 英文 / LT3 韩文原样——豁免正确。缺口仅 dokan 114 + gift 22 个 id 无 LT3 行（上游原版即缺，客户端走原回退）。
- ja 段仍为日文（选日本語时内置弹窗非中文，已知遗留）。

### 1.2 builtin 内置表纯度规则（无中英混排）

**规则：切槽前（EN 段）纯英文、切槽后（ko 段）纯中文**——任何段内不允许中英混排。

| 段 | 处置 | 键数 |
|---|---|---|
| EN 段（ui/titleflow/nt × en） | **还原原版英文**（fix4 逐键从原版 EN APK 提取还原） | **81**（ui 37 + titleflow 43 + nt 1；= fix3 68 + fix3l 13） |
| ko 段（ui/titleflow/nt × ko） | **写中文** | **148**（fix3 68 + fix3l 13 + fix4 nt 新译 67） |
| metadata stringLiteral | 保持中文 7 串（il2cpp stringLiteral 不分 EN/ko 槽位，切槽前后均显中文） | 7 |

- **KO_OVERRIDE 短译**（ko 段 ≤ 原字节硬约束下 2 条短译）：`ui.Outgame.Menu.Contact`→「联系」(6B)、`titleflow.dialog.maintenance.to.twitter`→「去推特」(9B)；fix3l 另 2 条短译「是否满16岁？/加载中」。EN 段同键仍为对应英文/全译，两态验证中 2 条与 EN 段译文不一致是**预期行为**。
- 3D 菜单 6 按钮（Profile/Help/Settings/Official Twitter/Download Data/Credits）**不在内置表也不在 metadata**（仅 key 名），归 text 侧管线；内置弹窗/按钮已由 EN 段+ko 段+metadata 覆盖。
- 术语表对齐 **zh_ja_fix7**（JP 侧中文终台账 `zh-l10n\work\mt-run\fix7-text\zh_ja_fix7.jsonl`，sha `4c1b1293…`）：如「盟友→队友」等体例逐键对照 JA 源 + JP 中文统一（各 fix 批 QA 含 JP 对照 0 偏差项）。
- **2026-10-29 用户终裁定术语**（fix11/12/13 执行，全库作用域）：Karma=**天命**（JA 源即「天命」）、Karma Flux=**天命流转**、Force=**战力**、Memory=**回忆**、Companion=**同伴**、deck=**编队**、Footer.Top=**主页**、主手→**主武器**、次级→**副武器**、安置→**交换**；专名重译：Karma:Ⅰ 罗马数字体例（「我」→「Ⅰ」）、お試し=试用（非审判）。后续批次术语以本条为准（覆盖旧「因果」等历史译法）。
- MT 供应商（2026-10-29）：**azure_s0 作废**（额度归零），仅 **f0 + 有道** 可用。

### 1.3 文本管线三仓（工作区记录）

| 工作区 | 内容 | 规模 |
|---|---|---|
| `zh-l10n\work\en-mt\` | ko 槽翻译主线 + **fix 差异批**（工作目录 fix1–fix5、fix8–fix13；报告双编号 en-fixN / fixM，如 fix2 目录 = EN-FIX4） | 基线 `bundles_ko` 6,585 包已部署；EN 151,971 元组 / KO 151,696 / 共有 151,433；SKIP 15,237 行、可译 137,464 行、去重 64,591 单元；MT 137,464 成功 / 0 失败；终态批 fix8-13 共 **415 键 / 148 差异包**（fix8 40 / fix9 15 / fix10 56 / fix11 145 / fix12 94 / fix13 65），已部署 rev 835；QA PASS（`EN-PIPELINE-REPORT.md`、各 `EN-FIX*-REPORT.md`） |
| `zh-l10n\work\en-help\` | help/ko 帮助页汉化（逐页审校） | **209 文本包**（22 contents + 187 page）/ 999 键 / 韩文原文 56,742 字；11 批修复（`fixes/batch01-11.json`）；重打包 209 文本包 + 109 图包原样（out 树 318=209+109）；T01-T08 双回读 + S01-S22 octo 结构逐字节一致（`qa_en_help.py`） |
| `zh-l10n\work\en-audit\` | 审计台账（只出清单不修复） | **5,370 条**（`EN-AUDIT-LEDGER.md` / `ledger.json`；数据源 zh_en_ko.jsonl 152,701 行 + ko_write_ledger 143,614 行 + builtin_strings 67 条 + JP 参照 143,359 键）；text-ko 5,190 条 + builtin 各段 |

---

## 2. APK 构建（build_en_zh.py）

`build_en_zh.py` = EN 汉化客户端离线构建驱动（7 步流水），抄 `build_jp_zh.py` 改（EN 侧）：

| 步 | 内容 | 工具 |
|---|---|---|
| 1/7 | EN 菜单编译/extract（复用） | `NieR-Re-In-carnation-Mod_Menu\en-client\tools`（inject_modmenu 管线） |
| 2/7 | 解包原版 APK | 原版 `resources\NieR Re[in]carnation 3.7.1_EN.apk`（sha `9ded0797…c9209`，只读） |
| 3/7 | 私服补丁 + auth 动态化 | `patches/patch_apk_en.py` + `patches/patch_auth_dynamic_en.py`（L3a 权威副本收编；原 lunar-scripts `patch_apk.py` + `en-client\tools\patch_auth_dynamic_en.py`） |
| 4/7 | fix3-EN 内置串（68 键 + metadata 7） | `zh-l10n\work\en-apk\patch_fix3_en.py` |
| 4b/7 | fix3-ko（68 键，≤原字节） | `zh-l10n\work\en-apk\patch_fix3_ko.py` |
| 4c/7 | fix3l 扩展键（13 键，EN+ko 双段） | `zh-l10n\work\en-apk\patch_fix3l.py` |
| 4d/7 | fix4 纯净化（EN 81 键还原 + ko 67 nt 翻译） | `zh-l10n\work\en-apk\patch_fix4.py` |
| 5/7 | 字体 payload3 四条目注入 | `zh-l10n\work\fonts-fix4\out3\payload3\assets\bin\Data`（按名+sha 对号入座，全程校验） |
| 6/7 | EN mod 菜单注入 | `en-client\tools\inject_modmenu`（smali/manifest/start-call） |
| 7/7 | apktool b → zipalign（`-p 4`）→ apksigner | `keys/nier-en.keystore` 签名（L3a 收编 = debug.keystore；alias androiddebugkey / android） |

### 2.1 Python 构建环境

- **受限**：`zh-l10n\.venv` 的 python **不能写 Mod_Menu 子树**，故构建用不受限解释器 + venv site-packages 挂 `PYTHONPATH` 取 UnityPy：

```bat
set PYTHONPATH=E:\NieRReincarnation\zh-l10n\.venv\Lib\site-packages
C:\Python314\python.exe build_en_zh.py --mode patched ^
    --apk "resources\NieR Re[in]carnation 3.7.1_EN.apk" ^
    --out "zh-l10n\work\en-apk\nier-mod-menu-en-font-fix4.apk" ^
    --work "NieR-Re-In-carnation-Mod_Menu\en-client\build\work_en_zh_fix4" --fresh ^
    --grpc 192.168.2.6:8003 --http 192.168.2.6:8080 --auth 192.168.2.6:3000
```

- 打包工具链依赖 **`lunar-base\.venv`**（`patch_listbin_named.py` 经 `sys.path` 引 `lunar-base\scripts\assetbundles\octo_pb2`，需 google.protobuf）。
- 产物：APK + 构建日志 + evidence JSON（`--out` 所在目录 `\logs`）+ `SHA256SUMS`。

### 2.2 签名（keystore 路径引用，本体不入库）

| 端 | keystore | alias / pass | 证书 SHA-256 |
|---|---|---|---|
| **EN** | `NieR-Re-In-carnation-Mod_Menu\en-client\keys\debug.keystore` | `androiddebugkey` / `android` | `7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173`（**7D:79:2C…**） |
| JP | `lunar-scripts-zh\jp-client\keys\nier-jp.keystore` | nier / lunar-jp | —（JP 侧统一） |

- 签名方案 **v2 + v3**；覆盖官方 EN 安装会因签名不符失败，**玩家需先卸载官方再安装**（私服常态）。

---

## 3. 字体 payload（Noto Sans CJK SC 子集 + Hangul 11,172 字形）

- 字体流水线共用 `fonts/`（jp 侧已有 `build_fix4_charset.py`、`build_fix4b_fonts.py`、`verify_fix4b.py`、`glyph_integrity.py`）；EN 侧差异只在 payload 产物。
- **EN 侧 Hangul payload**：`zh-l10n\work\fonts-fix4\`
  - `out2\payload2\`：CJK 子集四条目一包齐（前身）；
  - `out3\payload3\`：**+ Hangul 11,172 全音节字形**，`build_en_zh.py` 5/7 步实际注入源（四条目直接拷入，sha 全程校验）。
- 四条目角色表（EN=JP 原版容器逐字节一致，按名+sha 对号入座，不一致按 Font 角色回退重建）：

| 条目 | 角色 | 替换为 |
|---|---|---|
| `6f937efa0660c47f59d5215d276b1cbb` | UI（FOT-Rodin Pro DB） | Noto Sans CJK SC **Medium** 子集+Hangul |
| `7089ac60979c94824ac549baab08cfa7` | Story（A-OTF Talking Std R） | Noto Sans CJK SC **Regular** 子集+Hangul |
| `ad1489eb70ff840d19d7d0841bcdd3a9` | YDHopeL（Applibot-YDHope M） | Noto Sans CJK SC **Regular** 子集+Hangul |
| `550e0743a6b6344cfa3380b9a07f58b6` | YDWingsM（Applibot-YDWings M） | Noto Sans CJK SC **Medium** 子集+Hangul |

- 核销（EN-APK-FIX4-REPORT §三）：`en-help\hangul_needed` 209 码点（155 非 ASCII、60 Hangul 音节）→ 四字体 cmap **100% 覆盖 0 缺**；fix3l 已含 11,172 全音节 Hangul，无需补入 payload3。

---

## 4. 部署链（ko 文本批 → list.bin → octo）

```
ko 差异包 bundles_ko_fixN\assetbundle\text\ko\…（octo encrypt_fixed 语义，0x32）
  → patch_listbin_named.py  （按 staging 名匹配 list.bin 条目，更新 size/md5 + crc=0）
  → bump_listbin_revision.py（升 revision，编码长度不变）      [lunar-scripts-zh/deploy/]
  → verify_deploy.py         （上线前校验：revision 递增 / 条目与磁盘一致 / urlFormat 不变）
  → 部署服务端 revisions/0
```

### patch_listbin_named.py（本目录归档）用法

```powershell
C:\Python314\python.exe patch_listbin_named.py `
    --list-bin <live list.bin> `
    --staging-root <bundles_ko_fixN 树：assetbundle/text/ko/…> `
    --assets-root <live revisions/0> [--apply] [--json out.json]
```

- 默认 **dry-run**（只报告将变更项 + 基线一致性校验：live 文件须匹配条目旧 size/md5）；`--apply` 原子写（tmp+rename、保留 `list.bin.bak`）并回读校验。
- **与 `deploy/patch_listbin_stdlib.py` 的差异**：
  - **named 版（本目录，EN 批使用）**：走 `google.protobuf + octo_pb2`（`lunar-base\scripts\assetbundles`），**按 staging 树文件名匹配条目**（`assetbundle/text/ko/…` 路径 → 条目名），只哈希 staged 文件（几 MB）而不扫全量 19.5 GiB 资产树，`crc=0`（同官方 `patch_listbin.py` 语义）。
  - stdlib 版（`deploy/`）：纯标准库手写 protobuf wire 解析（无 protobuf 环境兜底），以 `--names` 名单为**定点**修补，crc 保持旧值。
- **多批连续部署（实操教训，2026-10-29）**：必须**逐批 patch→robocopy 交替**（fixN 的 patch 通过后立即铺它的包，再做 fixN+1）；若先把全部批 patch 完再统一铺文件，重叠包会让后续批的 precondition（live 须匹配条目旧 md5）失败且整批拒写。铺完所有批后 bump 一次 revision、落盘 list.bin、**重启 octo-cdn**（list 索引缓存无失效机制，见 lunar-base `E-deploy-cache.md`）。

---

## 5. 验证清单

| # | 项 | 方法 / 判据 |
|---|---|---|
| 1 | **字形零豆腐** | `fonts-fix4\verify_fix4.py` / `verify_fix4b.py` + `glyph_integrity.py`：glyph_report cmap 缺口 0；`render_check_*.png`（UI/Story × 句样 × 豆腐/部首/减号对照）目检 |
| 2 | **Hangul 覆盖** | 11,172 全音节入 payload3；`hangul_needed` 209 码点在 4 字体 cmap 全命中（0 缺） |
| 3 | **APK 签名 sha** | `apksigner verify -v --print-certs`：v2+v3，证书 sha256 = `7d792c3c…`（EXPECTED_CERT_SHA256 校验） |
| 4 | 构建独立验证 | `verify_en_build.py` ①-⑥：① 签名/证书 ② 字体四条目 sha256 = payload3（容器 + m_FontData 双校验）③ 私服 IP 192.168.2.6 命中（metadata×4 + dex×1）④ fix3 EN 回读 / ④b ko 段回读 / ④c fix3l 回读 ⑤ 原版 APK sha 未动（`9ded0797…c9209`）⑥ zip testzip + `zipalign -c` |
| 5 | 两态纯度验证 | `fix4_two_state_verify.json`：EN 段 81/81 = 原版英文、metadata 7/7 = 中文、ko 段 148 = 中文、旧值残留 0（KO_OVERRIDE 2 条短译除外，见 §1.2） |
| 6 | **显示 RVA 表按客户端选对**（display_patch.c 区服一致性识别） | 包名 / 清单 `org.veritr1x.bunker.REGION` meta / region.py 三元组 与 libil2cpp.so 大小交叉核对，矛盾/未知 fail-fast 拒补丁；EN so+EN 表过、EN so+JP 表拒。离线证据：`zh-l10n\work\diag-rva-display\l3b-test\test_display_rva.py` + `verify_en_source.py`（EN 源码级反汇编语义核对）+ `bunker\android\tools\test_display.py` 全绿。**协同点**：任务 C L6 将本门脚本化并入 `verify_en_build.py` / build.py 产物验证门时按本行口径调用 |

---

## 6. 本目录文件清单

| 文件 | 说明 | 来源（2026-10-29 归档） |
|---|---|---|
| `build_en_zh.py` | EN APK 离线构建驱动（7 步流水，见 §2） | `zh-l10n\work\en-apk\build_en_zh.py`（内容原样+头部注释） |
| `verify_en_build.py` | EN 构建产物独立验证 ①-⑥（见 §5） | `zh-l10n\work\en-apk\verify_en_build.py`（内容原样+头部注释） |
| `patch_listbin_named.py` | named 版 list.bin patcher（部署链，见 §4） | `zh-l10n\work\deploy\patch_listbin_named.py`（内容原样+头部注释） |
| `patch_fix3_en.py` / `patch_fix3_ko.py` | fix3 内置串补丁（EN 段 68 键+metadata 7 / ko 段同键 ≤原字节） | `zh-l10n\work\en-apk\`（逐字节原样） |
| `patch_fix3l.py` | fix3l 扩展 13 键（EN+ko 双段） | `zh-l10n\work\en-apk\`（逐字节原样） |
| `patch_fix4.py` | fix4 纯净化（EN 81 键还原 + ko 67 nt 翻译） | `zh-l10n\work\en-apk\`（逐字节原样） |
| `check_ko_en_consistency.py` / `check_ko_len_rule.py` / `check_ko_scripts.py` | ko 段 QA 三件（一致性/长度/脚本残留） | `zh-l10n\work\en-apk\`（逐字节原样） |
| `scan_untranslated.py` | 全表残余未译扫描 | `zh-l10n\work\en-apk\`（逐字节原样） |
| `README-EN.md` | 本文档 | — |

## 7. 相关脚本引用关系

**已归档（本目录，2026-10-29 补全）**——`build_en_zh.py` 绝对路径引用的 EN 专属工具，副本与 `zh-l10n\work\en-apk\` 原件逐字节一致：

| 本目录 | 角色 | 原路径 |
|---|---|---|
| `patch_fix3_en.py` | fix3 EN 段 68 键 → 中文 + metadata 7 串 | `zh-l10n\work\en-apk\patch_fix3_en.py` |
| `patch_fix3_ko.py` | fix3 ko 段同键 → 中文（≤原字节；KO_OVERRIDE 2 条短译） | `zh-l10n\work\en-apk\patch_fix3_ko.py` |
| `patch_fix3l.py` | fix3l 扩展 13 键（EN+ko 双段） | `zh-l10n\work\en-apk\patch_fix3l.py` |
| `patch_fix4.py` | fix4 纯净化（EN 81 键还原 + ko 67 nt 翻译；`fix4_orig_en_values.json` 为 81 键原版英文值，随原路径引用） | `zh-l10n\work\en-apk\patch_fix4.py` |
| `check_ko_en_consistency.py` / `check_ko_len_rule.py` / `check_ko_scripts.py` | ko 段一致性 / ≤原字节长度 / 脚本残留 QA | `zh-l10n\work\en-apk\` |
| `scan_untranslated.py` | 全表残余未译扫描（A-builtin-untranslated） | `zh-l10n\work\en-apk\scan_untranslated.py` |

**仍按原路径引用（未复制）**：

| 路径 | 角色 |
|---|---|
| `zh-l10n\work\en-apk\selftest_fix3en.py` / `selftest_fix3ko.py` / `selftest_fix3l.py` | 各补丁自检 |
| `zh-l10n\work\fonts-fix4\build_fix5_fonts.py` / `build_fix5_hangul_charset.py` | 字体 payload 构建 + Hangul charset（out2/out3 产物） |
| `zh-l10n\work\fonts-fix4\verify_fix4.py` / `verify_fix4b.py` / `glyph_integrity.py` | 字体校验（零豆腐/覆盖） |
| `lunar-scripts-zh\deploy\patch_listbin_stdlib.py` / `bump_listbin_revision.py` / `verify_deploy.py` / `probe_listbin.py` | 部署工具（stdlib patcher 兜底 + revision/校验） |
| `NieR-Re-In-carnation-Mod_Menu\en-client\tools\` | EN 菜单/注入管线（inject_modmenu、patch_auth_dynamic_en 等） |
| `NieR-Re-In-carnation-Mod_Menu\en-client\keys\debug.keystore` | EN 签名 key（**不入库**，路径引用，见 §2.2） |
| `lunar-scripts\android\patch_apk.py` | EN 3.7.1 RVA 私服补丁 |
