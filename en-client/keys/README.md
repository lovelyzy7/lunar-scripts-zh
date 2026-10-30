# en-client/keys — 签名密钥

| 项 | 值 |
|---|---|
| 文件 | `nier-en.keystore`（PKCS12，2,618 B，sha256 `d02ede230d2f49bab2ec873f323233351533f20a0c0ed1ce85bc8356a6c3cbc0`） |
| **血统** | **Android 标准 debug keystore** 收编：`NieR-Re-In-carnation-Mod_Menu\en-client\keys\debug.keystore`（**复制改名收编，原文件保留勿删**） |
| 收编记录 | 2026-10-29（L3a 客户端化落地）：`Copy-Item debug.keystore → nier-en.keystore`，逐字节一致（sha256 相同）；`keys\debug.keystore` 原件只读、未删未改 |
| alias | `androiddebugkey` |
| storepass/keypass | `android`（Android 标准 debug 密码；本项目约定可公开，不用于正式发布） |
| 证书 SHA-256 | `7D:79:2C:3C:FE:FD:73:22:37:64:20:6E:DE:BD:95:26:61:86:38:FF:15:21:65:DF:5F:BE:CD:35:6A:A4:A1:73` |
| 证书 DN | `C=US, O=Android, CN=Android Debug` |

## 血统说明（勿删原文件）

- 来源文件 `NieR-Re-In-carnation-Mod_Menu\en-client\keys\debug.keystore` 是 Mod_Menu en-client
  `tools/build_all.py` 构建收尾签最终 APK 用的同一把 key（`tools/toolpaths.json` 指向它）；
- **与已安装 EN 汉化客户端同一把 key** → `adb install -r` 可直接覆盖安装、保留数据；
- **不要删除/替换原文件或本收编副本**：换 key 后无法覆盖安装（只能卸载重装）；
- 覆盖**官方** EN 安装会因签名不同失败（官方证书≠本 debug 证书），玩家需先卸载官方再安装（私服常态）。

## 双 key 分治（BUNKER-ADAPT-PLAN §8）

| 客户端 | key | alias / pass | 证书 SHA-256 |
|---|---|---|---|
| JP | `jp-client/keys/nier-jp.keystore` | `nier` / `lunar-jp` | `EE:C2:3B…98:A2:FE` |
| EN | `en-client/keys/nier-en.keystore`（本文件） | `androiddebugkey` / `android` | `7D:79:2C…A4:A1:73` |

流水线按 `shared/detect_client.py` 识别结果自动选 key（jp→nier-jp、en→nier-en、未知→fail-fast）；
验证门做证书指纹比对（JP=EE:C2:3B…98A2FE、EN=7D:79:2C…A4:A1:73）。
