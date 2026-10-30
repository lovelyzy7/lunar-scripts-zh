# jp-client/ — JP 客户端构建（自包含流水线）

> 目标：在一台干净机器上**一条命令**产出「私服补丁 + 汉化」JP 客户端 APK
> （= 现网在装 fix3c 等价物），并自动过验证门 ①-⑥ + 与 fix3c 基准等价性对照；
> 给 `--bin-e` 时**成对**产出配套汉化 bin.e（三重断言全过才落盘）。
> **硬性要求：bin.e 文件名前后不变**——输入叫什么产出就叫什么（可换目录不可改名，三处强制）。
> 主文档（依赖、故障、验证门口径）：仓库根 [`../README-JP.md`](../README-JP.md)
> 「JP 客户端构建」「成对交付 APK + bin.e」「Colab 构建」三章。

## 一条命令

```powershell
# 全部权威副本与工具就位后（MANIFEST 校验 + 客户端识别自动执行）：
C:\Python314\python.exe jp-client\build_jp_client.py --apk "resources\NieR Re[in]carnation_3.7.1_JP.apk"
# 成对交付（目标 APK + 配套汉化 bin.e）：
C:\Python314\python.exe jp-client\build_jp_client.py --apk <原版.apk> --out <目标.apk> `
    --bin-e <原版或汉化.bin.e> [--out-bin-e <同名.bin.e>] --orig-bin-e <原版.bin.e>
# 或 PowerShell 包装（推荐给交付/自测）：
pwsh -File jp-client\runbook.ps1 -Apk "resources\NieR Re[in]carnation_3.7.1_JP.apk" -Out <输出.apk>
```

出参 = 签好的 APK + **`nier-jp.apk.manifest.json`（manifest sidecar）** + `<out>-verify.json`
（①-⑥ + 等价性）+ `logs/` 构建日志与 evidence；
给 `--bin-e` 时另有配套 bin.e（**与输入同名**，如 `20240404193219.bin.e`）+ `logs\<ts>-bin-e-report.json`。
每步失败即停。

## 客户端识别与命名契约（L3a）

- **识别**：构建前调 [`../shared/detect_client.py`](../shared/detect_client.py) 按 region 三元组
  （axml 包名 + bytes + sha256）硬断言输入必须是 JP 客户端（`nierspjp` / 254,131,762B / `25b6326c…653609`）；
  未知客户端、改 1 字节、误喂 EN 包 → **fail-fast 拒建**，不产出任何文件。
- **产物命名契约**：缺省产物名 **`nier-jp.apk`**（EN 流水线出 `nier-en.apk`）；
  `--out` 语义保留（显式指定以 --out 为准）。**bin.e 文件名前后不变**（不受命名契约影响）。
- **manifest sidecar**：`nier-jp.apk.manifest.json`（[`../shared/manifest_sidecar.py`](../shared/manifest_sidecar.py)
  生成）——region 三元组 / sha256 / size / 签名证书指纹（比对 EE:C2:3B…98A2FE）/ 补丁计数 /
  验证门结果 / 构建时间 / RVA 表版本占位 / 输入 APK sha。
- **key 自动选**：region=jp → `keys/nier-jp.keystore`（alias nier / lunar-jp）；验证门证书断言。
- 共享模块 `../shared/` 已登记进 MANIFEST.json（构建前预检 sha256）。

## 布局（自包含）

| 路径 | 内容 |
|---|---|
| `build_jp_client.py` | 一条流水线：解包→私服补丁→fix3→字体→mod 菜单→重建→zipalign→签名→验证门→**bin.e 成对构建** |
| `build_bin_e.py` | bin.e 构建器：汉化 masterdata + 原版 5 项可选编辑 + 三重断言（文本格=汉化基逐字节 / AES/TOC/5 表/LZ4 / diff 只在预期表） |
| `bin-edit.default.json` | bin.e 编辑配置（缺省 = 原版 patch_masterdata.py 全量编辑面，逐项开关） |
| `runbook.ps1` | PowerShell 入口（转交 build_jp_client.py，固定 base Python） |
| `verify_jp_client.py` | 验证门 ①-⑥ + fix3c 等价性对照（可独立复跑） |
| `toolpaths.json` | 工具定位（java/apktool/SDK/UnityPy + bin.e 依赖 site-packages）；干净机器照抄改路径 |
| `MANIFEST.json` | 权威副本 + 自撰文件的来源与 sha256（构建前自动校验）；`_gen_manifest.py` 为重生成工具 |
| `colab/` | `android_lunar_zh.ipynb`（Colab 成对构建）+ `gen_android_lunar_zh.py`（生成器）+ `test_colab_functions.py`（本地 fixtures 测试）+ `make_payload_zip.ps1`（补丁包打包） |
| `fix3/` | fix3 内置串**权威表**（builtin_strings.json 67 条 / tsv）+ patch_fix3.py |
| `fonts/payload/assets/bin/Data/` | 字体 payload **权威副本**（四条目，28,026,280 B） |
| `fonts/build_fix4b_fonts.py`、`build_fix4_charset.py`、`verify_fix4b.py` | 字体可复现构建/校验脚本 |
| `patches/patch_apk_jp.py` | 私服补丁（lunar-scripts-jp\android 副本，JP 3.7.1 RVA + auth 动态） |
| `modmenu-payload/` | mod 菜单注入件（smali + libniermenu.so）——**免 Gradle/NDK** |
| `keys/nier-jp.keystore` | nier-jp 签名 key（alias nier / lunar-jp），见 `keys/README.md` |

## 基线事实（MANIFEST.json `reference_facts` 同源）

| 项 | 值 |
|---|---|
| 原版 JP APK | `resources\NieR Re[in]carnation_3.7.1_JP.apk` 254,131,762 B sha256 `25b6326c…653609`（**只读**） |
| fix3c 基准 | `zh-l10n\work\apk\nier-mod-menu-jp-font-fix3c.apk` 273,436,239 B sha256 `2f363f79…51cc8e` |
| 签名证书 | `EE:C2:3B…D3D98A2FE`（`eec23be0…d98a2fe`） |
| 验证门口径 | ①v2+v3+证书 ②fix3 62/62（TA 68+meta 7） ③stringLiteral 7 值 ④四字体 sha ⑤私服 IP 10 处 ⑥原版未动 ⑦zipalign -c ⑧fix3c 等价性对照 |
| bin.e 汉化基 | `zh-l10n\work\mt-run\fix6-text\bin_zh_fix6.bin.e` 7,685,888 B sha256 `7dba416a…8b664`（文本格=此基逐字节） |
| bin.e 原版 | `20240404193219.bin.e` 7,801,104 B sha256 `60555788…270778`（断言 C 参照；原版编辑面产物 = `0a8b8cd4…c9918`） |
