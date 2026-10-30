#!/usr/bin/env python3
"""fonts-fix4/build_fix4_charset.py — 全载体日文字符盘点 + 修正子集字符集生成（fix4）。

载体（会以日文形态上屏）:
  text_ja          work/text_ja.jsonl value（不译项+未译残留 的日文原文母集）
  help_ja          device backup assetbundle-ui-help/ja/**（207 文本包）解密 TextAsset 全文
  masterdata_all   lunar-base/data/masterdata/*.json 全部字符串字段（含 JA 行，超集）
  preserved_names  exclusion/names.json ja_values（不译专有名词）
  apk_builtin_ja   APK 内置 ja TextAsset 表(ui/titleflow/nt) + fix3 keep 残留原文

输出:
  out/charset_fix4/union.codepoints.txt        全载体并集（子集输入）
  out/charset_fix4/fix4_subset.codepoints.txt  修正后子集 = old recommended_subset_extA ∪ 并集 ∪ 康熙部首/常用符号缓冲
  out/inventory/inventory_summary.json         盘点 + 与现 payload 差分
  out/inventory/missing.json                   缺字清单（码位+载体+样例）

只读 work/fonts 原产物。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
WORK = ROOT / "zh-l10n" / "work"
LUNAR_BASE = ROOT / "lunar-base"
HELP_ROOT = WORK / "device" / "deploy-20261025-210555" / "backup" / "assetbundle-ui-help" / "ja"
TEXT_JA = WORK / "text_ja.jsonl"
MASTERDATA_DIR = LUNAR_BASE / "data" / "masterdata"
NAMES_JSON = WORK / "exclusion" / "names.json"
APK_BUILTIN = WORK / "apk" / "fix3"
FONTS = WORK / "fonts"
PAYLOAD_DIR = FONTS / "out" / "payload" / "assets" / "bin" / "Data"
PAYLOAD_UI = PAYLOAD_DIR / "6f937efa0660c47f59d5215d276b1cbb"
PAYLOAD_STORY = PAYLOAD_DIR / "7089ac60979c94824ac549baab08cfa7"

# fix3 报告 layers.textasset.files：只有这三个是 ja 表
APK_BUILTIN_JA_FILES = [
    "textasset__assets_bin_Data_35005335013ad4314b0ac8afbfe27b9c__ui.txt",
    "textasset__assets_bin_Data_5296ae89c03c14825a9f664b0c355ccc__titleflow.txt",
    "textasset__assets_bin_Data_ed79b6250ad8541b1ba6f2a229fcc9bf__nt.txt",
]
TAG_RE = re.compile(r"<[^>]{1,60}>")
UNRENDERABLE_CATS = {"Cc", "Cf", "Cs", "Zl", "Zp"}


def renderable(ch: str) -> bool:
    return unicodedata.category(ch) not in UNRENDERABLE_CATS


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CharSet:
    def __init__(self, name: str, max_samples: int = 6) -> None:
        self.name = name
        self.chars: set[str] = set()
        self.samples: dict[str, list[str]] = {}
        self.max_samples = max_samples
        self.failures: list[str] = []

    def add(self, text: str, origin: str) -> None:
        for ch in text:
            if not renderable(ch):
                continue
            self.chars.add(ch)
            bucket = self.samples.setdefault(ch, [])
            if len(bucket) < self.max_samples and origin not in bucket:
                bucket.append(origin)


def strip_tags(value: str) -> str:
    return TAG_RE.sub("", value)


# ----------------------------------------------------------------- carriers
def carrier_text_ja() -> CharSet:
    cs = CharSet("text_ja")
    with TEXT_JA.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cs.add(strip_tags(rec.get("value") or ""),
                   f"text_ja:{rec.get('dir','')}/{rec.get('bundle','')}#{rec.get('key','')}")
    return cs


def carrier_help_ja() -> CharSet:
    sys.path.insert(0, str(LUNAR_BASE / "tools"))
    import extract_names as xn  # noqa: E402

    cs = CharSet("help_ja")
    files = [p for p in sorted(HELP_ROOT.rglob("*.assetbundle")) if "image_" not in p.name]
    for path in files:
        rel = path.relative_to(HELP_ROOT).as_posix()
        rel_noext = rel[: -len(".assetbundle")] if rel.endswith(".assetbundle") else rel
        mask = "ui)help)ja)" + rel_noext.replace("/", ")")
        try:
            decrypted = xn.decrypt_text_bundle(path.read_bytes(), mask)
            if not decrypted.startswith(b"UnityFS"):
                raise ValueError(f"decrypt failed head={decrypted[:8]!r}")
            assets: list[tuple[str, str]] = []
            for stream in xn.extract_bundle_streams(decrypted):
                assets.extend(xn.extract_text_assets(stream))
            if not assets:
                raise ValueError("no TextAsset")
            for asset_name, text in assets:
                for line_no, raw in enumerate(text.replace("\r\n", "\n").split("\n")):
                    line = raw.strip()
                    if not line or line.startswith("//"):
                        continue
                    sep = line.find(":")
                    value = line[sep + 1:] if sep > 0 else line
                    cs.add(strip_tags(value), f"help_ja:{rel}#{asset_name}:L{line_no}")
        except Exception as exc:  # noqa: BLE001
            cs.failures.append(f"{rel}: {exc}")
    return cs


def carrier_masterdata_all() -> CharSet:
    """全部 masterdata 表的所有字符串字段（含 LT1 日文行；超集，体积无碍）。
    只统计含 CJK/假名/标点的字段，纯 ASCII 标识符（表名/枚举）跳过以减少噪声。"""
    cs = CharSet("masterdata_all")
    ja_marker = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\u3400-\u4dbf]")
    for path in sorted(MASTERDATA_DIR.glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            cs.failures.append(f"{path.name}: {exc}")
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for col, value in row.items():
                if not isinstance(value, str) or not ja_marker.search(value):
                    continue
                cs.add(strip_tags(value), f"masterdata:{path.stem}.{col}")
    return cs


def carrier_preserved_names() -> CharSet:
    cs = CharSet("preserved_names")
    data = json.loads(NAMES_JSON.read_text(encoding="utf-8"))
    for cat_name, category in data["categories"].items():
        for value in category.get("ja_values") or []:
            cs.add(value, f"names:{cat_name}")
    return cs


def carrier_apk_builtin_ja() -> CharSet:
    cs = CharSet("apk_builtin_ja")
    for name in APK_BUILTIN_JA_FILES:
        path = APK_BUILTIN / name
        if not path.exists():
            cs.failures.append(f"missing {name}")
            continue
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            sep = line.find(":")
            value = line[sep + 1:] if sep > 0 else line
            cs.add(strip_tags(value), f"apk_builtin:{name}:L{line_no}")
    builtin = json.loads((APK_BUILTIN / "builtin_strings.json").read_text(encoding="utf-8"))
    for entry in builtin.get("entries", []):
        cs.add(strip_tags(entry.get("source_ja") or ""), f"builtin:{entry.get('id')}:{entry.get('tier')}")
    return cs


# ----------------------------------------------------------------- payload cmap
def payload_cmap(path: Path, tmp_dir: Path) -> tuple[set[int], dict]:
    import UnityPy  # noqa: PLC0415
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    env = UnityPy.load(str(path))
    font_objs = [obj for obj in env.objects if obj.type.name == "Font"]
    if len(font_objs) != 1:
        raise SystemExit(f"{path}: expect 1 Font object, got {len(font_objs)}")
    data = bytes(font_objs[0].read().m_FontData or b"")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / f"_fix4_readback_{path.name}.otf"
    tmp.write_bytes(data)
    tt = TTFont(str(tmp), lazy=True)
    cps: set[int] = set()
    for table in tt["cmap"].tables:
        cps.update(int(cp) for cp in table.cmap.keys())
    meta = {
        "payload_path": str(path),
        "payload_bytes": path.stat().st_size,
        "payload_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "font_data_bytes": len(data),
        "font_data_sha256": hashlib.sha256(data).hexdigest(),
        "num_glyphs": tt["maxp"].numGlyphs,
        "cmap_codepoints": len(cps),
        "font_name": None,
    }
    for rec in tt["name"].names:
        if rec.nameID == 1 and rec.platformID == 3:
            try:
                meta["font_name"] = rec.toUnicode()
            except Exception:  # noqa: BLE001
                pass
    tt.close()
    return cps, meta


def load_codepoints(path: Path) -> set[int]:
    out: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("U+"):
            out.add(int(line[2:], 16))
    return out


def font_cmap(path: Path) -> set[int]:
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    tt = TTFont(str(path), lazy=True)
    cps: set[int] = set()
    for t in tt["cmap"].tables:
        cps.update(int(cp) for cp in t.cmap.keys())
    tt.close()
    return cps


# ----------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent / "out"))
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    inv_dir = out_dir / "inventory"
    cs_dir = out_dir / "charset_fix4"
    inv_dir.mkdir(parents=True, exist_ok=True)
    cs_dir.mkdir(parents=True, exist_ok=True)

    carriers = {
        "text_ja": carrier_text_ja(),
        "help_ja": carrier_help_ja(),
        "masterdata_all": carrier_masterdata_all(),
        "preserved_names": carrier_preserved_names(),
        "apk_builtin_ja": carrier_apk_builtin_ja(),
    }

    print("== carrier sizes ==")
    carrier_json = {}
    for name, cs in carriers.items():
        text = "".join(sorted(cs.chars))
        carrier_json[name] = {
            "count": len(cs.chars),
            "sha256_utf8_sorted": sha256_text(text),
            "chars_sorted": text,
            "failures": cs.failures,
        }
        print(f"  {name:18s} {len(cs.chars):6d}  fail={len(cs.failures)}")
        for f in cs.failures[:5]:
            print(f"      FAIL {f}")

    union: set[str] = set()
    for cs in carriers.values():
        union |= cs.chars
    print(f"  {'UNION':18s} {len(union):6d}")
    union_text = "".join(sorted(union))
    carrier_json["union"] = {"count": len(union), "sha256_utf8_sorted": sha256_text(union_text),
                             "chars_sorted": union_text}
    (cs_dir / "union.codepoints.txt").write_text(
        "\n".join(f"U+{ord(c):04X}" for c in sorted(union, key=ord)), encoding="utf-8"
    )
    (cs_dir / "union.txt").write_text(union_text, encoding="utf-8")

    # payload cmaps
    ui_cmap, ui_meta = payload_cmap(PAYLOAD_UI, out_dir / "_tmp")
    story_cmap, story_meta = payload_cmap(PAYLOAD_STORY, out_dir / "_tmp")
    print(f"\npayload UI    cmap={len(ui_cmap)}  {ui_meta['font_name']}  {ui_meta['payload_bytes']}B")
    print(f"payload STORY cmap={len(story_cmap)}  {story_meta['font_name']}  {story_meta['payload_bytes']}B")

    def missing_against(cps: set[int]) -> list[dict]:
        rows = []
        for ch in sorted(union, key=ord):
            if ord(ch) in cps:
                continue
            rows.append({
                "char": ch,
                "codepoint": f"U+{ord(ch):04X}",
                "name": unicodedata.name(ch, "?"),
                "category": unicodedata.category(ch),
                "carriers": sorted(n for n, cs in carriers.items() if ch in cs.chars),
                "samples": [s for n in sorted(carriers) for s in carriers[n].samples.get(ch, [])][:6],
            })
        return rows

    missing_ui = missing_against(ui_cmap)
    missing_story = missing_against(story_cmap)
    print(f"\n== missing from current payload ==")
    print(f"  UI(Medium/extA)  missing {len(missing_ui)}")
    print(f"  STORY(Regular)   missing {len(missing_story)}")

    per_carrier_missing = {}
    for name, cs in carriers.items():
        miss = sorted((ch for ch in cs.chars if ord(ch) not in ui_cmap), key=ord)
        per_carrier_missing[name] = {
            "count": len(miss),
            "chars": "".join(miss),
            "codepoints": [f"U+{ord(c):04X}" for c in miss],
        }
        print(f"  carrier {name:18s} missing_in_UI={len(miss)}  " +
              " ".join(f"U+{ord(c):04X}" for c in miss[:30]))

    # ---------------- 修正子集字符集
    old_extA = load_codepoints(FONTS / "charsets" / "recommended_subset_extA.codepoints.txt")
    old_rec = load_codepoints(FONTS / "charsets" / "recommended_subset.codepoints.txt")
    print(f"\nold charset: recommended_subset={len(old_rec)}  +extA={len(old_extA)}")

    # 源字体（Noto Sans CJK SC）cmap
    src_cmap = font_cmap(FONTS / "vendor" / "ctan" / "NotoSansCJKsc-Medium.otf")
    src_reg_cmap = font_cmap(FONTS / "vendor" / "ctan" / "NotoSansCJKsc-Regular.otf")
    src_common = src_cmap & src_reg_cmap
    print(f"Noto Medium cmap={len(src_cmap)} Regular cmap={len(src_reg_cmap)} common={len(src_common)}")

    # 缓冲：CJK 康熙部首/兼容表意 U+2E80..U+2FDF（help 文本实测用到 ⼀⽣⾏⾯）
    #       + 常用数学/标点补集（−±×÷≤≥≠∞°′″℃‰′ 等）
    radical_block = set(range(0x2E80, 0x2FE0))
    mathish = set("−±×÷≤≥≠∞°′″℃‰※〒→←↑↓〜～…‥‘’“”•–—＀")
    buffer_extra = {cp for cp in (radical_block | {ord(c) for c in mathish}) if cp in src_common}

    union_cps = {ord(c) for c in union}
    fix4_extA = (old_extA | union_cps | buffer_extra) & src_common
    fix4_rec = (old_rec | union_cps | buffer_extra) & src_common

    def write_cs(name: str, cps: set[int], desc: str) -> None:
        (cs_dir / f"{name}.codepoints.txt").write_text(
            "\n".join(f"U+{cp:04X}" for cp in sorted(cps)), encoding="utf-8"
        )
        (cs_dir / f"{name}.txt").write_text(
            "".join(chr(cp) for cp in sorted(cps)), encoding="utf-8"
        )
        print(f"  charset {name:22s} {len(cps):6d}  ({desc})")

    print("\n== fix4 charsets ==")
    write_cs("fix4_subset_extA", fix4_extA, "UI Medium：old extA ∪ 全载体 ∪ 部首/符号缓冲 ∩ 源字体")
    write_cs("fix4_subset", fix4_rec, "story Regular：old rec ∪ 全载体 ∪ 部首/符号缓冲 ∩ 源字体")

    added_extA = sorted(fix4_extA - old_extA)
    added_rec = sorted(fix4_rec - old_rec)
    print(f"\nadded vs old: UI +{len(added_extA)}  STORY +{len(added_rec)}")
    print("  UI added: " + " ".join(f"U+{cp:04X}" for cp in added_extA[:60]))
    print("  ST added: " + " ".join(f"U+{cp:04X}" for cp in added_rec[:60]))

    result = {
        "generated_by": "fonts-fix4/build_fix4_charset.py",
        "carriers": carrier_json,
        "payload": {"ui": ui_meta, "story": story_meta},
        "missing": {"ui": missing_ui, "story": missing_story},
        "per_carrier_missing_vs_ui": per_carrier_missing,
        "charset": {
            "old_recommended_subset": len(old_rec),
            "old_recommended_subset_extA": len(old_extA),
            "fix4_subset": len(fix4_rec),
            "fix4_subset_extA": len(fix4_extA),
            "added_extA": [f"U+{cp:04X}" for cp in added_extA],
            "added_rec": [f"U+{cp:04X}" for cp in added_rec],
            "buffer_note": "CJK Radicals Supplement U+2E80..U+2FDF + 常用数学/标点补集 ∩ Noto SC 源字体",
        },
    }
    (inv_dir / "inventory_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (inv_dir / "missing.json").write_text(
        json.dumps({"ui": missing_ui, "story": missing_story}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nwritten {inv_dir} and {cs_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
