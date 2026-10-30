#!/usr/bin/env python3
"""fonts-fix4/glyph_integrity.py — 对现 payload 两字体做字形级完整性验证 + 实渲染对照。

检查每个「日文载体字符」在 payload 字体里：
  1. cmap 存在
  2. 映射到的 glyph 非 .notdef、advanceWidth>0
  3. CFF charstring 非空（能画出墨迹）
并用 Pillow/FreeType 实渲染「图 17 句子」到 PNG 供目检。
输出 out/glyph_report.json + out/render_check_*.png
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(r"E:\NieRReincarnation")
WORK = ROOT / "zh-l10n" / "work"
OUT = WORK / "fonts-fix4" / "out"
INV = OUT / "inventory"
PAYLOAD_DIR = WORK / "fonts" / "out" / "payload" / "assets" / "bin" / "Data"
PAYLOAD_UI = PAYLOAD_DIR / "6f937efa0660c47f59d5215d276b1cbb"
PAYLOAD_STORY = PAYLOAD_DIR / "7089ac60979c94824ac549baab08cfa7"

SENTENCE_A = "プレイヤーが影響を受ける効果が発生する状態です。"
SENTENCE_B = "効果の範囲は、敵と味方を含む全体、または味方のみの2種類があります。"
SENTENCE_C = "『エリア負荷』とは、クエスト中、プレイヤーが影響を受ける効果が発生する状態です。"


def extract_otf(payload: Path, out_dir: Path) -> Path:
    import UnityPy  # noqa: PLC0415

    env = UnityPy.load(str(payload))
    font = next(obj for obj in env.objects if obj.type.name == "Font").read()
    data = bytes(font.m_FontData or b"")
    out = out_dir / f"{payload.name}.otf"
    out.write_bytes(data)
    return out


def glyph_stats(font_path: Path, chars: set[str]) -> dict:
    font = TTFont(str(font_path))
    cmap = font.getBestCmap() or {}
    hmtx = font["hmtx"] if "hmtx" in font else None
    cff = font["CFF "] if "CFF " in font else None
    glyf = font["glyf"] if "glyf" in font else None

    rows = []
    for ch in sorted(chars, key=ord):
        cp = ord(ch)
        gname = cmap.get(cp)
        row = {
            "char": ch,
            "codepoint": f"U+{cp:04X}",
            "name": unicodedata.name(ch, "?"),
            "in_cmap": gname is not None,
            "glyph": gname,
            "is_notdef": gname in (None, ".notdef"),
            "advance": None,
            "outline_ok": None,
            "issue": None,
        }
        if gname is not None:
            if hmtx is not None and gname in hmtx.metrics:
                row["advance"] = hmtx.metrics[gname][0]
            if cff is not None:
                try:
                    td = cff.cff[cff.cff.fontNames[0]]
                    cs = td.CharStrings[gname]
                    cs.decompile()
                    # charstring 有实际绘制算数（rmoveto/hmoveto/vmoveto 之后还有 rlineto/rrcurveto 等）
                    progs = cs.program
                    draws = sum(1 for op in progs if op in (
                        "rrcurveto", "hhcurveto", "vvcurveto", "hvcurveto", "vhcurveto",
                        "rlineto", "hlineto", "vlineto", "rlineto", "endchar"))
                    row["outline_ok"] = ("rmoveto" in progs or "hmoveto" in progs or "vmoveto" in progs) and draws > 0
                    row["cs_len"] = len(progs)
                except Exception as exc:  # noqa: BLE001
                    row["outline_ok"] = False
                    row["issue"] = f"cff:{exc}"
            elif glyf is not None and gname in glyf.glyphs:
                g = glyf.glyphs[gname]
                row["outline_ok"] = g.numberOfContours != 0
        if not row["in_cmap"]:
            row["issue"] = "missing_cmap"
        elif row["is_notdef"]:
            row["issue"] = "maps_to_notdef"
        elif row["advance"] == 0:
            row["issue"] = "zero_advance"
        elif row["outline_ok"] is False:
            row["issue"] = "empty_outline"
        rows.append(row)
    font.close()
    return {"font": str(font_path), "count": len(rows), "rows": rows}


def render_sentence(font_path: Path, text: str, out_png: Path, size: int = 48) -> None:
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    font = ImageFont.truetype(str(font_path), size=size)
    pad = 20
    lines = [text[i:i + 26] for i in range(0, len(text), 26)]
    img = Image.new("RGB", (size * 28, pad * 2 + size * len(lines) * 2), "white")
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((pad, pad + i * size * 2), line, font=font, fill="black")
    img.save(out_png)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_tmp").mkdir(exist_ok=True)
    ui_otf = extract_otf(PAYLOAD_UI, OUT / "_tmp")
    story_otf = extract_otf(PAYLOAD_STORY, OUT / "_tmp")

    # 载体字符集（上一轮盘点产物）
    inv = json.loads((INV / "inventory_summary.json").read_text(encoding="utf-8"))
    union_text = inv["carriers"]["union"]["chars_sorted"]
    union = set(union_text)
    help_text = inv["carriers"]["help_ja"]["chars_sorted"]
    help_chars = set(help_text)
    focus = set(SENTENCE_A + SENTENCE_B + SENTENCE_C) | set("け効態対象味方敵範囲⼀⽣⾏⾯−")

    report = {"generated_by": "fonts-fix4/glyph_integrity.py", "fonts": {}}
    for label, path in (("ui_medium_extA", ui_otf), ("story_regular", story_otf)):
        st_all = glyph_stats(path, union)
        st_focus = glyph_stats(path, focus)
        bad = [r for r in st_all["rows"] if r["issue"]]
        bad_focus = [r for r in st_focus["rows"] if r["issue"]]
        report["fonts"][label] = {
            "otf": str(path),
            "union_checked": st_all["count"],
            "union_issues": bad,
            "focus_checked": st_focus["count"],
            "focus_rows": st_focus["rows"],
        }
        print(f"[{label}] union={st_all['count']} issues={len(bad)}  focus_issues={len(bad_focus)}")
        for r in bad[:20]:
            print(f"    {r['codepoint']} {r['char']!r} issue={r['issue']} adv={r['advance']}")
        for r in bad_focus:
            print(f"    FOCUS {r['codepoint']} {r['char']!r} issue={r['issue']} adv={r['advance']} outline={r['outline_ok']}")

    # 实渲染
    for label, path in (("ui", ui_otf), ("story", story_otf)):
        render_sentence(path, SENTENCE_A, OUT / f"render_check_{label}_sentA.png")
        render_sentence(path, SENTENCE_B, OUT / f"render_check_{label}_sentB.png")
        render_sentence(path, SENTENCE_C, OUT / f"render_check_{label}_sentC.png")
    print("rendered ->", OUT)

    (OUT / "glyph_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("written", OUT / "glyph_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
