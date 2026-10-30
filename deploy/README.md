# deploy/ — 部署工具与 runbook（提炼自 zh-l10n/work/deploy + 各部署轮实操）

| 文件 | 来源 | 用途 |
|---|---|---|
| `probe_listbin.py` | work/deploy（复制） | 只读解析 list.bin（revision/urlFormat/条目/逐条 size+md5 与磁盘比对） |
| `patch_listbin_stdlib.py` | work/deploy（复制） | 无 protobuf 环境**定点** size/md5 修补（--names 名单；编码长度不变） |
| `bump_listbin_revision.py` | work/deploy（复制） | revision bump（--set N / --bump；varint 长度不变，817→16383 安全） |
| `verify_deploy.py` | work/deploy（复制） | 上线前校验：revision 增大、变更条目 size+md5 与磁盘一致、urlFormat 不变 |
| `runbook.ps1` | **脚本化**（runbook） | 预检→备份→patch→bump→verify→（显式 -ApplyLive）原子替换 |

全量条目刷新用 **protobuf 版**：`E:\NieRReincarnation\lunar-base\scripts\assetbundles\patch_listbin.py`
（缺盘文件不动；变更条目 crc 置 0——客户端/CDN 不校验 crc，只校验 size+md5）。

**要点**（详见 ../README-JP.md §2）：
1. 客户端按本地 revision 拉 `/v1/list`；**不 bump 则不换文本**（旧 md5 缓存继续用）；
2. 文本包与 bin.e 成对部署；bin.e 替换后**刷 mtime** + 重启 lunar-tear（版本号 = `20240404193219_<mtime ms>`）；
3. list.bin 落盘后重启 octo-cdn 才生效；
4. 部署副本→校验→原子替换；备份带时间戳（`work\device\deploy-<ts>\backup\`）。
