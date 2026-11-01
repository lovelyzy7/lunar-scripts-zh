#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fonts-fix4/verify_fix4b.py — fix4b 补换验收：四条目重读 + 全载体 0 缺字 + 渲染对照 + 体积。

验收口径（任务）：
  * out2/payload2 四个字体条目重读 OK（m_FontData 可读、容器结构保全）
  * 全载体并集（3,226 字）0 缺字，含 ー体効囲状発け態対象味方敵 等
  * 渲染对照图：fonts-fix4 渲染脚本对图 17 原句，YDHope/YDWings 各出旧/新对照
  * 体积增量记录
输出 out2/verify_report.json、out2/render_*.png。退出码 0 = PASS。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
WORK = ROOT / "zh-l10n" / "work"
FIX4 = WORK / "fonts-fix4"
OUT = FIX4 / "out"
OUT2 = FIX4 / "out2"
INV = OUT / "inventory"
PAYLOAD2 = OUT2 / "payload2" / "assets" / "bin" / "Data"
OLD_EMBED = WORK / "repack" / "fonts" / "embedded"

NAMES = {
    "ad1489eb70ff840d19d7d0841bcdd3a9": ("ydhope", "FOTK-YDHopeL"),
    "550e0743a6b6344cfa3380b9a07f58b6": ("ydwings", "FOTK-YDWingsM"),
    "6f937efa0660c47f59d5215d276b1cbb": ("ui", "FOT-RodinPro-DB SDF"),
    "7089ac60979c94824ac549baab08cfa7": ("story", "A-OTF-TalkingStd-Regular-SDF"),
}
# 任务点名必含字符 + 简体译文抽样（弹窗 fix4-help 后为中文）
REQUIRED = "ー体効囲状発け態対象味方敵−⼀⽣⾏⾯发说门们个东进这戏游"
# 图 17 原句（category_04/item_16 原文，与 verify_fix4.py 一致）
SENTENCES = {
    "tofu_fig17_a": "プレイヤーが影響を受ける効果が発生する状態です。",
    "tofu_fig17_b": "効果の範囲は、敵と味方を含む全体、または味方のみの2種類があります。",
}
OLD_INPUTS = {  # 原版容器（体积对照，sha 见 probe_ydhope_ydwings.json）
    "ydhope": ("FOTK-YDHopeL", 685362, "e16c851c0e1d53a32dea4cdc836b0b8a9ab509cb94f0ccc480405893c1463144"),
    "ydwings": ("FOTK-YDWingsM", 698938, "f128a23b0e1ca27abf0435fee733daba7e0201f6ad755e9d97cd445301a6b56a"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def payload_cmap(path: Path, tmp_dir: Path, tag: str):
    import UnityPy  # noqa: PLC0415
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    env = UnityPy.load(str(path))
    sf = next(iter(env.files.values()))
    inv = [f"{o.type.name}#{int(o.path_id)}" for o in sf.objects.values()]
    font_objs = [o for o in sf.objects.values() if o.type.name == "Font"]
    if len(font_objs) != 1:
        raise SystemExit(f"{path.name}: expect 1 Font, got {len(font_objs)}")
    data = bytes(font_objs[0].read().m_FontData or b"")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / f"{tag}_{path.name}.otf"
    tmp.write_bytes(data)
    tt = TTFont(str(tmp), lazy=True)
    cps: set[int] = set()
    for t in tt["cmap"].tables:
        cps.update(int(cp) for cp in t.cmap.keys())
    font_name = None
    for rec in tt["name"].names:
        if rec.nameID == 1 and rec.platformID == 3:
            try:
                font_name = rec.toUnicode()
            except Exception:  # noqa: BLE001
                pass
    meta = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "inventory": inv,
        "font_data_bytes": len(data),
        "font_data_sha256": sha256_bytes(data),
        "cmap_codepoints": len(cps),
        "num_glyphs": tt["maxp"].numGlyphs,
        "font_name": font_name,
    }
    tt.close()
    return cps, meta, tmp


def render(text: str, font_path: Path, out_png: Path, size: int = 44) -> None:
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    font = ImageFont.truetype(str(font_path), size=size)
    pad = 16
    lines = [text[i:i + 24] for i in range(0, len(text), 24)]
    img = Image.new("RGB", (size * 26, pad * 2 + size * 2 * len(lines)), "white")
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((pad, pad + i * size * 2), line, font=font, fill="black")
    img.save(out_png)


def main() -> int:
    import argparse  # noqa: PLC0415

    global PAYLOAD2, OUT2  # noqa: PLW0603
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload-dir", default=str(PAYLOAD2), help="四条目 payload 目录")
    ap.add_argument("--out-dir", default=str(OUT2), help="报告/渲染输出目录")
    args = ap.parse_args()
    PAYLOAD2 = Path(args.payload_dir)
    OUT2 = Path(args.out_dir)
    OUT2.mkdir(parents=True, exist_ok=True)
    return run_verify()


def run_verify() -> int:
    inv = json.loads((INV / "inventory_summary.json").read_text(encoding="utf-8"))
    union = set(inv["carriers"]["union"]["chars_sorted"])
    print(f"union={len(union)}")

    tmp = OUT2 / "_tmp"
    results = {}
    otfs = {}
    ok = True
    print("\n== 四条目重读 + 全载体覆盖 ==")
    for name, (key, label) in NAMES.items():
        cps, meta, otf = payload_cmap(PAYLOAD2 / name, tmp, "new")
        missing_union = [f"U+{ord(c):04X}({c})" for c in sorted(union, key=ord) if ord(c) not in cps]
        missing_req = [c for c in REQUIRED if ord(c) not in cps]
        meta["missing_vs_union"] = missing_union
        meta["missing_vs_required"] = missing_req
        meta["label"] = label
        results[key] = meta
        otfs[key] = otf
        if missing_union or missing_req:
            ok = False
        print(f"  {key:8s} {meta['bytes']:9,}B cmap={meta['cmap_codepoints']:6d} "
              f"missing_union={len(missing_union)} missing_required={missing_req} "
              f"inv={meta['inventory']}")

    # 渲染对照：旧字体（原版内嵌 OTF）vs 新字体（payload2 m_FontData）
    print("\n== 渲染对照（图 17 原句） ==")
    render_ok = True
    for key, old_file in (("ydhope", "FOTK-YDHopeL.otf"), ("ydwings", "FOTK-YDWingsM.otf")):
        old_otf = OLD_EMBED / old_file
        for label, text in SENTENCES.items():
            new_png = OUT2 / f"render_new_{key}_{label}.png"
            render(text, otfs[key], new_png)
            if old_otf.is_file():
                old_png = OUT2 / f"render_old_{key}_{label}.png"
                render(text, old_otf, old_png)
            else:
                render_ok = False
            print(f"  {key} {label}: new={new_png.name} old={old_file} exists={old_otf.is_file()}")
    # 简体译文抽样渲染（弹窗中文形态留证）
    zh_sample = "要结束游戏吗？游戏数据将被删除，请确认。"
    render(zh_sample, otfs["ydhope"], OUT2 / "render_new_ydhope_zh_sample.png")
    render(zh_sample, otfs["ydwings"], OUT2 / "render_new_ydwings_zh_sample.png")
    if not render_ok:
        ok = False

    # 体积增量
    print("\n== 体积增量 ==")
    size_cmp = {}
    for key, (label, old_bytes, old_sha) in OLD_INPUTS.items():
        new_bytes = results[key]["bytes"]
        size_cmp[key] = {
            "label": label,
            "old_container_bytes": old_bytes,
            "old_container_sha256": old_sha,
            "new_container_bytes": new_bytes,
            "new_container_sha256": results[key]["sha256"],
            "delta_bytes": new_bytes - old_bytes,
            "old_font_data_bytes": 678832 if key == "ydhope" else 694220,
            "new_font_data_bytes": results[key]["font_data_bytes"],
        }
        print(f"  {key:8s} {old_bytes:,} -> {new_bytes:,}  ({new_bytes - old_bytes:+,} B)")
    total_delta = sum(v["delta_bytes"] for v in size_cmp.values())
    payload2_total = sum(results[k]["bytes"] for k in results)
    print(f"  两容器合计 delta {total_delta:+,} B；payload2 四条目合计 {payload2_total:,} B")

    report = {
        "generated_by": "fonts-fix4/verify_fix4b.py",
        "union_count": len(union),
        "acceptance_pass": ok,
        "required_chars": REQUIRED,
        "entries": results,
        "size_compare": size_cmp,
        "total_delta_bytes_new_two": total_delta,
        "payload2_total_bytes": payload2_total,
    }
    (OUT2 / "verify_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nwritten {OUT2 / 'verify_report.json'}")
    print(f">>> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
