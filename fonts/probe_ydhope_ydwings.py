#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fonts-fix4/probe_ydhope_ydwings.py — 定位并体检 FOTK-YDHopeL / FOTK-YDWingsM 两字体容器。

红线体检口径（结构不符则停，不硬改）：
  * 容器 = APK assets/bin/Data/<hash> 单个 SerializedFile
  * 恰好 1 个 Font 对象、m_FontData 为 OTTO/OTF 字节
  * 其余对象逐字节可保（与 build_fix4_fonts.py swap 前提一致）
输出 out2/probe_ydhope_ydwings.json。
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
WORK = ROOT / "zh-l10n" / "work"
FIX4 = WORK / "fonts-fix4"
OUT2 = FIX4 / "out2"
APK = ROOT / "resources" / "NieR Re[in]carnation_3.7.1_JP.apk"
APK_RAW = WORK / "repack" / "fonts" / "apk_raw"
TARGETS = {
    "ad1489eb70ff840d19d7d0841bcdd3a9": "FOTK-YDHopeL",
    "550e0743a6b6344cfa3380b9a07f58b6": "FOTK-YDWingsM",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    out2_work = OUT2 / "work"
    out2_work.mkdir(parents=True, exist_ok=True)
    report: dict = {"apk": str(APK), "targets": {}}

    with zipfile.ZipFile(APK) as zf:
        names = set(zf.namelist())
        for entry_name, label in TARGETS.items():
            zip_entry = f"assets/bin/Data/{entry_name}"
            item: dict = {"label": label, "zip_entry": zip_entry, "in_apk": zip_entry in names}
            if zip_entry not in names:
                report["targets"][entry_name] = item
                continue
            data = zf.read(zip_entry)
            item["bytes"] = len(data)
            item["sha256"] = sha256_bytes(data)
            local = out2_work / f"{label}.input.bin"
            local.write_bytes(data)
            item["extracted_to"] = str(local)

            # 与 repack/fonts/apk_raw 只读拷贝交叉核对
            ref = APK_RAW / entry_name
            if ref.is_file():
                ref_sha = sha256_bytes(ref.read_bytes())
                item["apk_raw_copy_sha256"] = ref_sha
                item["apk_raw_copy_matches"] = ref_sha == item["sha256"]

            # UnityPy 结构体检
            import UnityPy  # noqa: PLC0415

            env = UnityPy.load(str(local))
            sf = next(iter(env.files.values()))
            inv = [(o.type.name, int(o.path_id)) for o in sf.objects.values()]
            item["inventory"] = [f"{t}#{p}" for t, p in inv]
            font_objs = [o for o in sf.objects.values() if o.type.name == "Font"]
            item["font_object_count"] = len(font_objs)
            if len(font_objs) == 1:
                font = font_objs[0].read()
                fd = bytes(font.m_FontData or b"")
                item["m_FontData_bytes"] = len(fd)
                item["m_FontData_sha256"] = sha256_bytes(fd)
                item["m_FontData_head"] = fd[:4].hex()
                item["m_FontData_is_otto"] = fd[:4] == b"OTTO"
                names_seen = []
                try:
                    import io  # noqa: PLC0415
                    from fontTools.ttLib import TTFont  # noqa: PLC0415

                    tt = TTFont(io.BytesIO(fd), lazy=True)
                    for rec in tt["name"].names:
                        if rec.nameID in (1, 4, 6) and rec.platformID == 3:
                            try:
                                names_seen.append({"nameID": rec.nameID, "text": rec.toUnicode()})
                            except Exception:  # noqa: BLE001
                                pass
                    cps = set()
                    for t in tt["cmap"].tables:
                        cps.update(int(cp) for cp in t.cmap.keys())
                    item["embedded_cmap_codepoints"] = len(cps)
                    item["embedded_num_glyphs"] = tt["maxp"].numGlyphs
                    tt.close()
                except Exception as exc:  # noqa: BLE001
                    item["tt_error"] = str(exc)
                item["embedded_name_records"] = names_seen
            report["targets"][entry_name] = item

    ok_all = all(
        t.get("font_object_count") == 1 and t.get("m_FontData_is_otto") and t.get("in_apk")
        for t in report["targets"].values()
    )
    report["structure_ok"] = ok_all
    out = OUT2 / "probe_ydhope_ydwings.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nstructure_ok={ok_all}  -> {out}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
