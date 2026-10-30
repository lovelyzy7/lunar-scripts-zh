# lunar-scripts-zh

**JP 客户端汉化 l10n 流**：在 [lunar-scripts-jp](../lunar-scripts-jp) 之上叠加「文本管线 + 字体步骤 + 资源包 + 部署脚本 + 汉化 APK」。

- 主文档：**[README-JP.md](README-JP.md)**（叠加关系 / 构建步骤 / 部署 runbook / 回滚 / 已知问题）
- 与 lunar-scripts-jp 的关系：**叠加，不替代**。基线管线（android/assetbundles/masterdata/local）以 lunar-scripts-jp 为准；本仓只收 l10n 侧脚本与文档。
- **providers.json（翻译供应商真实密钥）不入库**（`.gitignore` 已排除 `providers.json`/`config/providers.json`/`config/*.local.json`）；对内配置放 `zh-l10n\config\providers.json`，对外只提供 example 形态。
- **红线**：项目最最后一次性提交之前不 `git init/add/commit/push`；`resources\` 原件、现网 lunar-tear、真机设备不动。

## 目录

| 目录 | 内容 |
|---|---|
| `l10n/` | 文本管线：mt_client、dump_text、probe_bundle_repack、排除规则、术语表、fix 通用工具（apply/build/qa） |
| `fonts/` | 字体流水线：charset 子集、四容器 payload 构建/校验（Noto Sans CJK SC 2.004） |
| `resourcepack/` | `resource_dump-android-zh.7z` 构建器（7z u 增量 + list.bin 刷新 + 校验） |
| `deploy/` | 部署工具：probe/patch/bump/verify + runbook.ps1 |
| `apk/` | 汉化 APK 构建与校验（字体替换 + 同 key 重签名） |
| `docs/` | 补充文档 |

## en-client/

EN 客户端汉化管线归档（EN 客户端：`text/ko` 槽写中文，选「한국어」进中文）：`build_en_zh.py` 构建驱动、`verify_en_build.py` 独立验证、`patch_listbin_named.py`（named 版 list.bin 部署）。
- 主文档：**[README-EN.md](en-client/README-EN.md)**（ko 槽策略 / 纯度规则 / 构建步骤 / 字体 payload / 部署链 / 验证清单）
- 与 `jp-client/` 并列：EN 签名用 en-client debug key（keystore 本体不入库，路径引用）。
