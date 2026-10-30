# fonts/ — 字体流水线（fonts-fix4 系列，四容器 payload2）

字体源：**Noto Sans CJK SC 2.004**（SIL OFL 1.1；CTAN 镜像 Regular/Medium/Bold 单字重 OTF）。
结论：游戏原字体（RodinPro/TalkingStd）GB2312 一级覆盖仅 75.5%/73.0%，**必须替换**；一套 payload JP/EN 通用。

| 文件 | 来源 | 用途 |
|---|---|---|
| `build_fix4_charset.py` | fonts-fix4（复制） | 译文用字 + ExtA 增补 → 子集 codepoints（`fix4_subset` / `fix4_subset_extA`） |
| `build_fix4b_fonts.py` | fonts-fix4（复制） | **四容器构建**：UI(RodinPro)→Medium+ExtA 子集 7.95MB、STORY(TalkingStd)→Regular 子集 6.04MB、FOTK-YDHopeL / FOTK-YDWingsM 补换 → `payload2/` |
| `verify_fix4b.py` | fonts-fix4（复制） | 替换后读回 sha/对象清单/字形 0 缺 |
| `glyph_integrity.py` | fonts-fix4（复制） | 现网字体字形盘点/覆盖率 |
| `probe_ydhope_ydwings.py` | fonts-fix4（复制） | 图 17 □ 豆腐（YDHopeM 对照）定位 |

产物（work 不入库）：`zh-l10n\work\fonts-fix4\out\payload\`（UI c97a4319… / STORY 5ed20794…）与 `out2\payload2\`（四容器终版，fix3c APK 用）。
fix4 子集补 5 缺字（`− ⼀ ⽣ ⾏ ⾯`，全在 help 载体）后 3,226 字 100% 覆盖。
