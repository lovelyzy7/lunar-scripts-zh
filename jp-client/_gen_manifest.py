#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性生成 MANIFEST.json（记录 jp-client/ 权威副本来源与 sha256）。"""
import hashlib
import json
import time
from pathlib import Path

JP = Path(__file__).resolve().parent
ROOT = Path(r"E:\NieRReincarnation")

SOURCES = {
    "fix3/patch_fix3.py": "zh-l10n/work/apk/fix3/patch_fix3.py",
    "fix3/builtin_strings.json": "zh-l10n/work/apk/fix3/builtin_strings.json",
    "fix3/builtin_strings.tsv": "zh-l10n/work/apk/fix3/builtin_strings.tsv",
    "fonts/build_fix4b_fonts.py": "zh-l10n/work/fonts-fix4/build_fix4b_fonts.py",
    "fonts/build_fix4_charset.py": "zh-l10n/work/fonts-fix4/build_fix4_charset.py",
    "fonts/verify_fix4b.py": "zh-l10n/work/fonts-fix4/verify_fix4b.py",
    "fonts/payload/assets/bin/Data/6f937efa0660c47f59d5215d276b1cbb":
        "zh-l10n/work/fonts-fix4/out2/payload2/assets/bin/Data/6f937efa0660c47f59d5215d276b1cbb",
    "fonts/payload/assets/bin/Data/7089ac60979c94824ac549baab08cfa7":
        "zh-l10n/work/fonts-fix4/out2/payload2/assets/bin/Data/7089ac60979c94824ac549baab08cfa7",
    "fonts/payload/assets/bin/Data/ad1489eb70ff840d19d7d0841bcdd3a9":
        "zh-l10n/work/fonts-fix4/out2/payload2/assets/bin/Data/ad1489eb70ff840d19d7d0841bcdd3a9",
    "fonts/payload/assets/bin/Data/550e0743a6b6344cfa3380b9a07f58b6":
        "zh-l10n/work/fonts-fix4/out2/payload2/assets/bin/Data/550e0743a6b6344cfa3380b9a07f58b6",
    "keys/nier-jp.keystore": "NieR-Re-In-Carnation-Mod_Menu/jp-client/keys/nier-jp.keystore",
    "patches/patch_apk_jp.py": "lunar-scripts-jp/android/patch_apk_jp.py",
}
for sub in ("smali", "smali_classes2"):
    src_dir = ROOT / "NieR-Re-In-Carnation-Mod_Menu" / "jp-client" / "build" / "menu_apktool" / sub
    for p in sorted(src_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(src_dir).as_posix()
            SOURCES[f"modmenu-payload/{sub}/{rel}"] = (
                f"NieR-Re-In-Carnation-Mod_Menu/jp-client/build/menu_apktool/{sub}/{rel}")
SOURCES["modmenu-payload/lib/arm64-v8a/libniermenu.so"] = (
    "NieR-Re-In-Carnation-Mod_Menu/jp-client/build/menu_apktool/lib/arm64-v8a/libniermenu.so")

# 本仓自撰/本仓演进的文件（非只读素材副本）：同样进 MANIFEST 校验 sha256，
# 权威副本 items 与 authored 条目分开标注（source = "authored"）。
AUTHORED = [
    "build_jp_client.py",
    "build_bin_e.py",
    "bin-edit.default.json",
    "verify_jp_client.py",
    "runbook.ps1",
    "toolpaths.json",
    "README.md",
    "_gen_manifest.py",
    "colab/gen_android_lunar_zh.py",
    "colab/android_lunar_zh.ipynb",
    "colab/test_colab_functions.py",
    "colab/make_payload_zip.ps1",
    # 共享模块（双前端 MANIFEST 都登记，构建前预检完整性）
    "../shared/__init__.py",
    "../shared/detect_client.py",
    "../shared/gate_defs.py",
    "../shared/manifest_sidecar.py",
    "../shared/test_detect_client.py",
    "../shared/verify_gate.py",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


items = []
for rel, src in sorted(SOURCES.items()):
    dst = JP / rel
    src_p = ROOT / src
    if not dst.is_file():
        raise SystemExit(f"missing copy: {dst}")
    items.append({
        "path": rel,
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "source": src,
        "source_sha256": sha256_file(src_p) if src_p.is_file() else None,
        "identical_to_source": src_p.is_file() and sha256_file(src_p) == sha256_file(dst),
    })

for rel in sorted(AUTHORED):
    dst = JP / rel
    if not dst.is_file():
        raise SystemExit(f"missing authored file: {dst}")
    items.append({
        "path": rel,
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "source": "authored",
        "source_sha256": None,
        "identical_to_source": None,
    })

manifest = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "description": "jp-client/ 权威副本 + 自撰文件清单（来源=本机只读素材或 authored；构建前校验 sha256）",
    "counts": {"files": len(items),
               "copies": len([i for i in items if i["source"] != "authored"]),
               "authored": len([i for i in items if i["source"] == "authored"]),
               "bytes": sum(i["bytes"] for i in items)},
    "reference_facts": {
        "original_apk": {
            "path": "resources/NieR Re[in]carnation_3.7.1_JP.apk",
            "sha256": "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609",
            "bytes": 254131762},
        "baseline_fix3c_apk": {
            "path": "zh-l10n/work/apk/nier-mod-menu-jp-font-fix3c.apk",
            "sha256": "2f363f7988b8c241028a2084ee6b2ecd1ee0a158d58dd39c31f95f29a151cc8e",
            "bytes": 273436239},
        "expected_cert_sha256": "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe",
        "fix3c_verify_expectations": {
            "fix3_entries_checked": 62,
            "fix3_entries_ok": 62,
            "fix3_textasset_hits": 68,
            "fix3_metadata_hits": 7,
            "private_ip_total_hits": 10,
            "private_ip_in_metadata": True,
            "fonts": {
                "6f937efa0660c47f59d5215d276b1cbb": "c97a431931099addbc4203606d48f03f151f4350b2bceac5a9ce72ea10026f3d",
                "7089ac60979c94824ac549baab08cfa7": "5ed20794fd7d8dacda0b05726c8a41828bb8a89330be01bde42c3d45944dee4e",
                "ad1489eb70ff840d19d7d0841bcdd3a9": "ad690f4b1a51d77a398935bf83d2bfc288f69dd7dead21f9d7904ec6160b0e34",
                "550e0743a6b6344cfa3380b9a07f58b6": "853ac67aacddd480b3a6f29f97171d431ce78fc6fa3b12e6dbb8039226ccb85b",
            },
        },
    },
    "items": items,
}
out = JP / "MANIFEST.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
copies = [i for i in items if i["source"] != "authored"]
print(f"wrote {out} files={len(items)} (copies={len(copies)} authored={len(items) - len(copies)}) "
      f"bytes={manifest['counts']['bytes']}")
print("copies identical to source:", all(i["identical_to_source"] for i in copies))
