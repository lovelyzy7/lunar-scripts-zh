# l10n/ — 文本管线（提炼自 zh-l10n tools/ + work/mt-run fix 系列）

| 文件 | 来源 | 用途 |
|---|---|---|
| `dump_text.py` | zh-l10n/tools/（复制） | 三语文本抽取（只读）→ jsonl |
| `mt_client.py` | zh-l10n/tools/（复制） | 翻译客户端：三家供应商/占位符保护/缓存/降级；密钥见 `zh-l10n/config/providers.json`（**不入库**） |
| `probe_providers.py` | zh-l10n/tools/（复制） | 供应商连通性 |
| `probe_bundle_repack.py` | zh-l10n/tools/（复制） | 文本包解包/改值/回写/校验（UnityPy+lz4+octo 对称加密） |
| `build_exclusions.py` | zh-l10n/work/exclusion/（复制） | R01–R20 排除规则重建 |
| `exclusions/` | zh-l10n/work/exclusion/（复制） | rules.json、protect_terms.tsv、english_terms*.tsv、names.json 等机器可读产物 |
| `glossary/` | zh-l10n/work/mt-run/（复制） | ui_glossary.tsv（UI 统一词）、help_TERMS.md（帮助域锁定词） |
| `fix/apply_changes.py` | **提炼通用化**（fix4..fixF apply） | 批次合成：L1/L2/L3 命中 + 优先级 + 名字词典回填 + 终扫；幂等 |
| `fix/build_bundles.py` | **提炼通用化**（fix4..fixF build_bundles） | 差异包整树重建 + 全状态写入 + 回读校验 |
| `fix/qa_check.py` | **提炼通用化**（fix4..fixF qa） | QA 门禁：占位符/SKIP/哨兵/空值/换行/假名/标点/旧词/术语/字库/行宽 |

**约定**：输入只读；输出 jsonl 行尾 CRLF（fix11+ 代际一致）；每条译文带 `status`/`provider` 元字段便于回查。
批次历史（fix1..fix15、fixA、fixF）与各自 QA 报告在 `zh-l10n\work\mt-run\`（work 不入库），合成终态 = `zh_ja_fixF.jsonl`。
