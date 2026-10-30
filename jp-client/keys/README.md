# jp-client/keys — 签名密钥

| 项 | 值 |
|---|---|
| 文件 | `nier-jp.keystore`（JKS，2,246 B，sha256 `4C5CF2D4BAB5F8791CECD418169A29E04A69340A155D109C33E6651AF16346F8`） |
| 来源 | `NieR-Re-In-Carnation-Mod_Menu\jp-client\keys\nier-jp.keystore`（与 `lunar-scripts-jp\keys\nier-jp.keystore` 同物） |
| alias | `nier` |
| storepass/keypass | `lunar-jp`（本项目约定可公开；同 bunker-modmenu mod 菜单 key） |
| 证书 SHA-256 | `EE:C2:3B:E0:CB:20:5C:40:17:91:BE:3D:4B:82:E8:85:15:60:F5:C2:AE:D3:EC:64:41:66:09:3D:3D:98:A2:FE` |

- **同 key 升级**：汉化 APK 与历史 fix3c、mod 菜单同 key → 覆盖安装保留数据；
  只有换 key 才需卸载重装（清数据）。
- `.gitignore` 沿用 `!keys/*.keystore` 例外（本目录另加 `!jp-client/keys/*.keystore`），
  其余 `*.keystore` 一律不入库。
