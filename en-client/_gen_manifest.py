#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_gen_manifest.py — 生成 en-client/MANIFEST.json（记录 en-client/ 权威副本 + 自撰文件 sha256）。

镜像 jp-client/_gen_manifest.py 口径：
  * 权威副本（copies）= 别处原件的逐字节副本，登记来源路径 + 来源 sha256 + identical_to_source；
  * 自撰（authored）= 本仓演进/归档文件，同样进 MANIFEST 校验 sha256；
  * 共享模块 shared/detect_client.py + shared/manifest_sidecar.py 以 ../shared/ 相对路径
    登记进两客户端 MANIFEST（双前端都预检共享模块完整性）。

重生成：python en-client/_gen_manifest.py     （构建前 check_manifest() 会校验本表）
"""
import hashlib
import json
import time
from pathlib import Path

EN = Path(__file__).resolve().parent
ROOT = Path(r"E:\NieRReincarnation")
ZH = EN.parent

# 权威副本：路径 → 来源（相对 E:\NieRReincarnation）
SOURCES = {
    "keys/nier-en.keystore":
        "NieR-Re-In-carnation-Mod_Menu/en-client/keys/debug.keystore",
    "patches/patch_apk_en.py":
        "lunar-scripts/android/patch_apk.py",
    "patches/patch_auth_dynamic_en.py":
        "NieR-Re-In-carnation-Mod_Menu/en-client/tools/patch_auth_dynamic_en.py",
    "fix4_orig_en_values.json":
        "zh-l10n/work/en-apk/fix4_orig_en_values.json",
}

# 自撰/归档演进文件（含共享模块）
AUTHORED = [
    "build_en_zh.py",
    "verify_en_build.py",
    "patch_fix3_en.py",
    "patch_fix3_ko.py",
    "patch_fix3l.py",
    "patch_fix4.py",
    "patch_listbin_named.py",
    "check_ko_en_consistency.py",
    "check_ko_len_rule.py",
    "check_ko_scripts.py",
    "scan_untranslated.py",
    "README-EN.md",
    "keys/README.md",
    "_gen_manifest.py",
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
    dst = EN / rel
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
    dst = EN / rel
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
    "description": "en-client/ 权威副本 + 自撰文件清单（来源=本机只读素材或 authored；"
                   "构建前校验 sha256；镜像 jp-client/MANIFEST.json 口径）",
    "counts": {"files": len(items),
               "copies": len([i for i in items if i["source"] != "authored"]),
               "authored": len([i for i in items if i["source"] == "authored"]),
               "bytes": sum(i["bytes"] for i in items)},
    "reference_facts": {
        "original_apk": {
            "path": "resources/NieR Re[in]carnation 3.7.1_EN.apk",
            "sha256": "9ded0797ee607b6892b531ba3a02f4c4510774f5fe098ccada78ccff881c9209",
            "bytes": 263571029},
        "expected_cert_sha256":
            "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173",
        "product_name_contract": "nier-en.apk",
        "keystore": {"file": "keys/nier-en.keystore", "alias": "androiddebugkey",
                     "pass": "android",
                     "lineage": "NieR-Re-In-carnation-Mod_Menu/en-client/keys/debug.keystore"
                                "（复制收编，原件保留）"},
    },
    "items": items,
}
out = EN / "MANIFEST.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
copies = [i for i in items if i["source"] != "authored"]
print(f"wrote {out} files={len(items)} (copies={len(copies)} authored={len(items) - len(copies)}) "
      f"bytes={manifest['counts']['bytes']}")
print("copies identical to source:", all(i["identical_to_source"] for i in copies))
