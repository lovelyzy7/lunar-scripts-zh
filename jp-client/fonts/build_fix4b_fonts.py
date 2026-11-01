#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fonts-fix4/build_fix4b_fonts.py — 补换 FOTK-YDHopeL / FOTK-YDWingsM 两字体容器（fix4b）。

背景：fix4 已换 UI(6f937efa…) / STORY(7089ac60…)；图 17 豆腐形态与未替换的
FOTK-YDHopeL(ad1489eb…) / FOTK-YDWingsM(550e0743…) 缺字集吻合 → 本次补换这两容器。

子集参数（与 build_fix4_fonts.py 对 6f937efa 的处理完全一致）：
  YDHopeL（细/黑体风格）= NotoSansCJKsc-Regular  ∩ fix4_subset
  YDWingsM（M 字重）    = NotoSansCJKsc-Medium   ∩ fix4_subset_extA
字符集用 fix4_subset(_extA)（= 旧 recommended ∪ 全载体并集3,226 ∪ 部首/符号缓冲，
⊇ 任务点名的「全载体 3,226 并集」，另覆盖简体译文字形——弹窗 fix4-help 后显示中文，
只取 3,226 并集会让 游/戏/发/说… 等简体字缺字，故取超集；验收仍按全载体并集 0 缺字）。

容器写回：m_FontData 替换（build_fix4_fonts.py.swap_font_container 同款），
Font 之外对象逐字节不变；输入容器来自原版 APK assets/bin/Data/<hash>（只读）。

产物（四个字体条目一包齐）：
  out2/payload2/assets/bin/Data/{ad1489eb…, 550e0743…}   本次新建
  out2/payload2/assets/bin/Data/{6f937efa…, 7089ac60…}   复制 fonts-fix4 新子集版
                                                          （c97a4319… / 5ed20794…）

红线：只写 fonts-fix4/out2/**，不写 work/fonts/**、不动原版 APK。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
WORK = ROOT / "zh-l10n" / "work"
FONTS = WORK / "fonts"
FIX4 = WORK / "fonts-fix4"
OUT = FIX4 / "out"
OUT2 = FIX4 / "out2"
CHARSET_DIR = OUT / "charset_fix4"
VENDOR = FONTS / "vendor" / "ctan"
# 原始容器（probe_ydhope_ydwings.py 已从原版 APK 抽出，sha 与 apk_raw 拷贝一致）
INPUT_YDHOPE = OUT2 / "work" / "FOTK-YDHopeL.input.bin"
INPUT_YDWINGS = OUT2 / "work" / "FOTK-YDWingsM.input.bin"
PAYLOAD_YDHOPE_NAME = "ad1489eb70ff840d19d7d0841bcdd3a9"   # FOTK-YDHopeL
PAYLOAD_YDWINGS_NAME = "550e0743a6b6344cfa3380b9a07f58b6"  # FOTK-YDWingsM
PAYLOAD_UI_NAME = "6f937efa0660c47f59d5215d276b1cbb"       # UI，复制 fix4 新版
PAYLOAD_STORY_NAME = "7089ac60979c94824ac549baab08cfa7"    # STORY，复制 fix4 新版
FIX4_PAYLOAD = OUT / "payload" / "assets" / "bin" / "Data"
EXPECT_UI_SHA = "c97a431931099addbc4203606d48f03f151f4350b2bceac5a9ce72ea10026f3d"
EXPECT_STORY_SHA = "5ed20794fd7d8dacda0b05726c8a41828bb8a89330be01bde42c3d45944dee4e"

# 与 build_fix4_fonts.py 完全一致的 fontTools.subset 参数
SUBSET_OPTS = dict(
    hinting=True, desubroutinize=False, name_IDs=["*"], name_languages=["*"],
    notdef_glyph=True, notdef_outline=True, recalc_bounds=False,
    prune_unicode_ranges=True, recalc_timestamp=False, canonical_order=True,
    layout_features=[], drop_tables=["vhea", "vmtx", "VORG", "GSUB", "GPOS", "GDEF", "BASE"],
)

# 子集可丢的控制符码位（U+0000-001F / U+007F-009F）；其余源字形全保。
CONTROL_CODEPOINTS = set(range(0x00, 0x20)) | set(range(0x7F, 0xA0))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_codepoints(path: Path) -> set[int]:
    out: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("U+"):
            out.add(int(line[2:], 16))
    return out


def build_subset(source: Path, codepoints: set[int], out: Path) -> dict:
    from fontTools import subset  # noqa: PLC0415
    from fontTools.ttLib import TTFont  # noqa: PLC0415

    src_font = TTFont(str(source), lazy=True)
    src_cmap: set[int] = set()
    for t in src_font["cmap"].tables:
        src_cmap.update(int(cp) for cp in t.cmap.keys())
    src_font.close()
    # 恢复原样口径：子集码位集 = 源字体完整 cmap ∪ 请求集（一个字形不丢、只增不减）；
    # 仅丢控制符 U+0000-001F/007F-009F，其余全保（含韩文）。
    available = (src_cmap | codepoints) - CONTROL_CODEPOINTS

    font = TTFont(str(source))
    options = subset.Options()
    options.hinting = SUBSET_OPTS["hinting"]
    options.desubroutinize = SUBSET_OPTS["desubroutinize"]
    options.name_IDs = SUBSET_OPTS["name_IDs"]
    options.name_languages = SUBSET_OPTS["name_languages"]
    options.notdef_glyph = SUBSET_OPTS["notdef_glyph"]
    options.notdef_outline = SUBSET_OPTS["notdef_outline"]
    options.recalc_bounds = SUBSET_OPTS["recalc_bounds"]
    options.prune_unicode_ranges = SUBSET_OPTS["prune_unicode_ranges"]
    options.recalc_timestamp = SUBSET_OPTS["recalc_timestamp"]
    options.canonical_order = SUBSET_OPTS["canonical_order"]
    options.layout_features = SUBSET_OPTS["layout_features"]
    options.drop_tables += SUBSET_OPTS["drop_tables"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=available)
    subsetter.subset(font)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(out))
    font.close()

    chk = TTFont(str(out), lazy=True)
    out_cmap: set[int] = set()
    for t in chk["cmap"].tables:
        out_cmap.update(int(cp) for cp in t.cmap.keys())
    meta = {
        "source": str(source),
        "out": str(out),
        "out_bytes": out.stat().st_size,
        "out_sha256": sha256_file(out),
        "requested": len(codepoints),
        "available_in_source": len(available),
        "missing_from_source": sorted(codepoints - src_cmap),
        "cmap_codepoints": len(out_cmap),
        "num_glyphs": chk["maxp"].numGlyphs,
        "tables": sorted(chk.keys()),
        "missing_in_subset": sorted(available - out_cmap),
    }
    chk.close()
    return meta


def swap_font_container(input_bin: Path, new_font: bytes, out_path: Path, work_dir: Path,
                        label: str) -> dict:
    import UnityPy  # noqa: PLC0415

    work_dir.mkdir(parents=True, exist_ok=True)
    src_copy = work_dir / f"{label}.input.bin"
    src_copy.write_bytes(input_bin.read_bytes())
    env = UnityPy.load(str(src_copy))
    sf = next(iter(env.files.values()))
    inv_before = [(obj.type.name, int(obj.path_id)) for obj in sf.objects.values()]
    raw_before = {f"{o.type.name}#{int(o.path_id)}": sha256_bytes(bytes(o.get_raw_data()))
                  for o in sf.objects.values()}
    font_objs = [obj for obj in sf.objects.values() if obj.type.name == "Font"]
    if len(font_objs) != 1:
        raise SystemExit(f"{label}: expect 1 Font, got {len(font_objs)}")
    font = font_objs[0].read()
    original_data = bytes(font.m_FontData or b"")
    font.m_FontData = new_font
    font.save()
    out_bytes = sf.save()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)

    env2 = UnityPy.load(str(out_path))
    sf2 = next(iter(env2.files.values()))
    inv_after = [(obj.type.name, int(obj.path_id)) for obj in sf2.objects.values()]
    raw_after = {f"{o.type.name}#{int(o.path_id)}": sha256_bytes(bytes(o.get_raw_data()))
                 for o in sf2.objects.values()}
    font2 = next(obj.read() for obj in sf2.objects.values() if obj.type.name == "Font")
    readback = bytes(font2.m_FontData or b"")
    others_same = all(raw_before[k] == raw_after.get(k) for k in raw_before if not k.startswith("Font#"))
    return {
        "label": label,
        "input_bin": str(input_bin),
        "input_bytes": input_bin.stat().st_size,
        "input_sha256": sha256_file(input_bin),
        "original_font_data_bytes": len(original_data),
        "original_font_data_sha256": sha256_bytes(original_data),
        "new_font_bytes": len(new_font),
        "new_font_sha256": sha256_bytes(new_font),
        "out_path": str(out_path),
        "out_bytes": len(out_bytes),
        "out_sha256": sha256_bytes(out_bytes),
        "size_overhead": len(out_bytes) - len(new_font),
        "size_delta_vs_input": len(out_bytes) - input_bin.stat().st_size,
        "readback_sha256": sha256_bytes(readback),
        "readback_matches_new_font": sha256_bytes(readback) == sha256_bytes(new_font),
        "inventory_preserved": inv_before == inv_after,
        "inventory": [f"{t}#{p}" for t, p in inv_after],
        "other_objects_raw_unchanged": others_same,
    }


def main() -> int:
    out2_subset = OUT2 / "subset"
    payload2 = OUT2 / "payload2" / "assets" / "bin" / "Data"
    work_dir = OUT2 / "work"
    out2_subset.mkdir(parents=True, exist_ok=True)
    payload2.mkdir(parents=True, exist_ok=True)

    for p in (INPUT_YDHOPE, INPUT_YDWINGS):
        if not p.is_file():
            raise SystemExit(f"缺输入容器（先跑 probe_ydhope_ydwings.py）: {p}")

    cps_extA = load_codepoints(CHARSET_DIR / "fix4_subset_extA.codepoints.txt")
    cps_rec = load_codepoints(CHARSET_DIR / "fix4_subset.codepoints.txt")

    print("== build subsets (fix4b：YDHope=Regular∩fix4_subset，YDWings=Medium∩fix4_subset_extA) ==")
    t0 = time.time()
    hope_meta = build_subset(VENDOR / "NotoSansCJKsc-Regular.otf", cps_rec,
                             out2_subset / "NotoSansCJKsc-Regular.subset-fix4_subset-nolayout-ydhope.otf")
    print(f"  YDHope(Regular)   {hope_meta['out_bytes']:,}B cmap={hope_meta['cmap_codepoints']} "
          f"glyphs={hope_meta['num_glyphs']} missing_in_subset={len(hope_meta['missing_in_subset'])} "
          f"missing_from_source={len(hope_meta['missing_from_source'])}")
    wings_meta = build_subset(VENDOR / "NotoSansCJKsc-Medium.otf", cps_extA,
                              out2_subset / "NotoSansCJKsc-Medium.subset-fix4_subset_extA-nolayout-ydwings.otf")
    print(f"  YDWings(Medium)   {wings_meta['out_bytes']:,}B cmap={wings_meta['cmap_codepoints']} "
          f"glyphs={wings_meta['num_glyphs']} missing_in_subset={len(wings_meta['missing_in_subset'])} "
          f"missing_from_source={len(wings_meta['missing_from_source'])}")
    print(f"  build {time.time() - t0:.0f}s")

    # 与 fix4 既有子集字节一致性对照（同源同参数应完全一致）
    ref_story_otf = OUT / "subset" / "NotoSansCJKsc-Regular.subset-fix4_subset-nolayout.otf"
    ref_ui_otf = OUT / "subset" / "NotoSansCJKsc-Medium.subset-fix4_subset_extA-nolayout.otf"
    hope_meta["same_bytes_as_fix4_story_subset"] = (
        ref_story_otf.is_file() and sha256_file(ref_story_otf) == hope_meta["out_sha256"])
    wings_meta["same_bytes_as_fix4_ui_subset"] = (
        ref_ui_otf.is_file() and sha256_file(ref_ui_otf) == wings_meta["out_sha256"])
    print(f"  与 fix4 子集字节一致: YDHope={hope_meta['same_bytes_as_fix4_story_subset']} "
          f"YDWings={wings_meta['same_bytes_as_fix4_ui_subset']}")

    print("\n== swap into APK Font containers ==")
    hope_swap = swap_font_container(
        INPUT_YDHOPE, Path(hope_meta["out"]).read_bytes(),
        payload2 / PAYLOAD_YDHOPE_NAME, work_dir, "ydhope_regular",
    )
    wings_swap = swap_font_container(
        INPUT_YDWINGS, Path(wings_meta["out"]).read_bytes(),
        payload2 / PAYLOAD_YDWINGS_NAME, work_dir, "ydwings_medium",
    )
    for s in (hope_swap, wings_swap):
        print(f"  {s['label']:15s} payload={s['out_bytes']:,}B "
              f"delta_vs_input={s['size_delta_vs_input']:+,} readback_ok={s['readback_matches_new_font']} "
              f"inv_ok={s['inventory_preserved']} others_ok={s['other_objects_raw_unchanged']}")

    print("\n== copy fix4 new UI/STORY payloads (四条目一包齐) ==")
    copied = {}
    for name, expect in ((PAYLOAD_UI_NAME, EXPECT_UI_SHA), (PAYLOAD_STORY_NAME, EXPECT_STORY_SHA)):
        src = FIX4_PAYLOAD / name
        if not src.is_file():
            raise SystemExit(f"fix4 payload 缺失: {src}")
        got = sha256_file(src)
        if got != expect:
            raise SystemExit(f"fix4 payload sha 不符: {name} got={got} expect={expect}")
        dst = payload2 / name
        shutil.copy2(src, dst)
        copied[name] = {"src": str(src), "dst": str(dst), "bytes": dst.stat().st_size,
                        "sha256": sha256_file(dst), "matches_fix4_new_payload": True}
        print(f"  {name} {dst.stat().st_size:,}B {got[:16]}…")

    report = {
        "generated_by": "fonts-fix4/build_fix4b_fonts.py",
        "subset_options": SUBSET_OPTS,
        "charset_note": ("fix4_subset(_extA) ⊇ 全载体并集(3,226) ∪ 旧 recommended ∪ 部首/符号缓冲；"
                         "覆盖简体译文（弹窗 fix4-help 后为中文）"),
        "charsets": {
            "fix4_subset_extA": {"count": len(cps_extA), "file": str(CHARSET_DIR / "fix4_subset_extA.codepoints.txt")},
            "fix4_subset": {"count": len(cps_rec), "file": str(CHARSET_DIR / "fix4_subset.codepoints.txt")},
        },
        "subsets": {"ydhope_regular": hope_meta, "ydwings_medium": wings_meta},
        "payload": {"ydhope": hope_swap, "ydwings": wings_swap, "copied_fix4": copied},
    }
    (OUT2 / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nwritten {OUT2 / 'build_report.json'}")
    ok = (hope_swap["readback_matches_new_font"] and hope_swap["inventory_preserved"]
          and hope_swap["other_objects_raw_unchanged"]
          and wings_swap["readback_matches_new_font"] and wings_swap["inventory_preserved"]
          and wings_swap["other_objects_raw_unchanged"]
          and all(c["matches_fix4_new_payload"] for c in copied.values()))
    print(f"BUILD {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
