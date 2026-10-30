#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_untranslated.py — EN APK 内置表（ui/titleflow/nt × EN/ko 段）全表漏译扫描。

列出仍为英文/韩文/日文的弹窗与按钮键（排除已译 68 键与 keep 项），
并按任务点名的目标串（Skip/Age/3D菜单/확인/광고 等）做关键词命中分类。

用法：
  set PYTHONPATH=E:\\NieRReincarnation\\zh-l10n\\.venv\\Lib\\site-packages
  C:\\Python314\\python.exe scan_untranslated.py
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APK = ROOT / "resources" / "NieR Re[in]carnation 3.7.1_EN.apk"
TABLE = ROOT / "zh-l10n" / "work" / "apk" / "fix3" / "builtin_strings.json"
OUT = HERE / "scan_untranslated.json"

# EN APK 内置表 6 载体（3 表 × 2 语言槽）
TS_ALL = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
    "assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb": "nt(en)",
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}

# 已译 68 键（builtin_strings.json apply+supplement 的 TextAsset 键）
# 以及 keep 项 K01-K05
def load_known_keys() -> tuple[set[str], set[str]]:
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    translated: set[str] = set()
    keep: set[str] = set()
    for e in t["entries"]:
        for k in e.get("keys", []):
            if k.startswith("metadata."):
                continue
            if e["tier"] == "keep":
                keep.add(k)
            elif e.get("target_zh"):
                translated.add(k)
    return translated, keep


def classify_value(v: str) -> str:
    """粗分类：值的主要脚本。"""
    if not v or not v.strip():
        return "empty"
    # 去掉 TMP/富文本标签和占位符后再分类
    clean = re.sub(r"<[^>]+>", "", v)
    clean = re.sub(r"\{[^}]*\}", "", clean)
    clean = re.sub(r"\\n", "", clean)
    clean = re.sub(r"#[A-Za-z0-9/]+", "", clean)
    has_hangul = bool(re.search(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]", clean))
    has_kana = bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF]", clean))
    has_cjk = bool(re.search(r"[\u4E00-\u9FFF\u3400-\u4DBF]", clean))
    has_han_ext = bool(re.search(r"[\U00020000-\U0002A6DF]", clean))
    has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", clean))
    # 中文判定：CJK 但无假名（且无韩文）
    if has_hangul:
        return "hangul"
    if has_kana:
        return "kana"  # 日文（含汉字混排）
    if has_cjk or has_han_ext:
        return "cjk_no_kana"  # 中文（或纯汉字）
    # 纯拉丁/数字/标点
    latin_letters = len(re.findall(r"[A-Za-z]", clean))
    if latin_letters >= 2:
        return "latin"
    if re.search(r"[А-Яа-я]", clean):
        return "cyrillic"
    return "other"


# 任务点名目标关键词（命中分类用）
TARGET_PATTERNS = {
    "skip_confirm": [r"skip this story", r"confirm skip", r"スキップ", r"건너뛰"],
    "return_title_confirm": [r"return to the title", r"Are you sure you want to return",
                             r"タイトル画面に戻りますか", r"タイトルへ戻りますか"],
    "age_confirm": [r"Is your age 16", r"Confirm Age", r"16 years or over",
                    r"年齢", r"16歳以上"],
    "menu_3d": [r"^Profile$", r"^Help$", r"^Settings$", r"^Official Twitter$",
                r"^Download Data$", r"^Credits$", r"^Title Screen$",
                r"プロフィール", r"ヘルプ", r"設定", r"公式ツイッター",
                r"ダウンロードデータ", r"クレジット"],
    "confirm_button": [r"^확인$", r"^确认$", r"^OK$", r"^Confirm$",
                       r"^はい$", r"^Yes$", r"^확인합니다"],
    "watch_ad": [r"광고 영상 보기", r"watch ad", r"watch advertisement",
                 r"広告", r"動画広告"],
}


def match_targets(key: str, value: str) -> list[str]:
    hits = []
    blob = f"{key}\n{value}"
    for cat, pats in TARGET_PATTERNS.items():
        for p in pats:
            if re.search(p, blob, re.IGNORECASE | re.MULTILINE):
                hits.append(cat)
                break
    return hits


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import UnityPy

    translated, keep = load_known_keys()
    print(f"已译键 {len(translated)} 个 / keep 键 {len(keep)} 个")

    result: dict = {
        "apk": str(APK),
        "translated_keys_count": len(translated),
        "keep_keys_count": len(keep),
        "segments": {},
        "untranslated_summary": {},
        "target_hits": {},
    }

    # 目标命中总表
    target_hits: dict[str, list[dict]] = {k: [] for k in TARGET_PATTERNS}

    for entry, label in TS_ALL.items():
        with zipfile.ZipFile(APK) as zf:
            buf = zf.read(entry)
        env = UnityPy.load(buf)
        kv: dict[str, str] = {}
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            d = obj.read()
            s = getattr(d, "m_Script", None)
            text = s.decode("utf-8") if isinstance(s, bytes) else s
            for line in text.split("\n"):
                sep = line.find(":")
                if sep > 0:
                    kv[line[:sep]] = line[sep + 1:]

        untranslated = []
        for k, v in kv.items():
            if k in translated or k in keep:
                continue
            cls = classify_value(v)
            if cls in ("empty", "other"):
                continue
            # 拉丁短串（OK/TAP TO START 等）单列
            entry_info = {"key": k, "value": v[:120], "class": cls,
                          "bytes": len(v.encode("utf-8"))}
            cats = match_targets(k, v)
            if cats:
                entry_info["target_categories"] = cats
                for c in cats:
                    target_hits[c].append({"segment": label, "key": k, "value": v[:120]})
            if cls in ("latin",):
                entry_info["note"] = "拉丁短串（可能是 OK/TAP 等通用按钮）"
            untranslated.append(entry_info)

        result["segments"][label] = {
            "total_keys": len(kv),
            "untranslated_count": len(untranslated),
            "by_class": {},
            "untranslated": untranslated,
        }
        for e in untranslated:
            result["segments"][label]["by_class"][e["class"]] = \
                result["segments"][label]["by_class"].get(e["class"], 0) + 1
        print(f"{label}: total={len(kv)} untranslated={len(untranslated)} "
              f"by_class={result['segments'][label]['by_class']}")

    result["target_hits"] = target_hits
    for cat, hits in target_hits.items():
        result["untranslated_summary"][cat] = len(hits)
        if hits:
            print(f"\n=== 目标命中 [{cat}] × {len(hits)} ===")
            for h in hits[:20]:
                print(f"  {h['segment']:16s} {h['key']:60s} {h['value'][:60]}")

    # 同键在 EN/ko 段都未译的汇总（按键去重）
    all_un_keys: dict[str, dict] = {}
    for label, seg in result["segments"].items():
        for e in seg["untranslated"]:
            k = e["key"]
            if k not in all_un_keys:
                all_un_keys[k] = {"key": k, "en_value": None, "ko_value": None,
                                  "class": e["class"], "segments": []}
            all_un_keys[k]["segments"].append(label)
            if "(en)" in label:
                all_un_keys[k]["en_value"] = e["value"]
            else:
                all_un_keys[k]["ko_value"] = e["value"]
    result["untranslated_unique_keys"] = sorted(all_un_keys.values(), key=lambda x: x["key"])
    result["untranslated_unique_count"] = len(all_un_keys)
    print(f"\n未译去重键总数: {len(all_un_keys)}")

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"report -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
