# -*- coding: utf-8 -*-
"""check_ko_en_consistency.py — 最终 APK 内 ko 段 vs EN 段同键值一致性对照（只读）。"""
import json, sys, zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
HERE = ROOT / "zh-l10n" / "work" / "en-apk"
APK = HERE / "nier-mod-menu-en-font-fix3k.apk"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TS_EN = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
    "assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb": "nt(en)",
}
TS_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}


def load_kv(buf):
    import UnityPy
    env = UnityPy.load(buf)
    kv = {}
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            s = obj.read().m_Script
            text = s.decode("utf-8") if isinstance(s, bytes) else s
            for line in text.split("\n"):
                sep = line.find(":")
                if sep > 0:
                    kv[line[:sep]] = line[sep + 1:]
    return kv


def main():
    sys.path.insert(0, str(HERE))
    import patch_fix3_ko as K
    kmap = K.key_map(K.load_entries("all"))
    with zipfile.ZipFile(APK) as zf:
        en_kv, ko_kv = {}, {}
        for e, l in TS_EN.items():
            en_kv.update(load_kv(zf.read(e)))
        for e, l in TS_KO.items():
            ko_kv.update(load_kv(zf.read(e)))
    rows, same, diff = [], 0, []
    has_ko_char = []
    for k, zh in kmap.items():
        ev, kv_ = en_kv.get(k), ko_kv.get(k)
        r = {"key": k, "en": ev, "ko": kv_, "same": ev == kv_,
             "ko_bytes": len(kv_.encode("utf-8")) if kv_ else None,
             "override": k in K.KO_OVERRIDE}
        rows.append(r)
        if r["same"]:
            same += 1
        else:
            diff.append(r)
        if kv_ and any("\uac00" <= c <= "\ud7af" for c in kv_):
            has_ko_char.append(k)
    out = {
        "apk": str(APK), "keys": len(kmap),
        "en_ko_identical": same, "en_ko_diff": len(diff),
        "diff_rows": diff, "ko_chars_remaining_in_targets": has_ko_char,
        "ok": same == len(kmap) - len(K.KO_OVERRIDE) and not has_ko_char
              and all(r["override"] for r in diff),
    }
    (HERE / "ko_en_consistency.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("keys:", out["keys"], "identical:", same, "diff:", len(diff))
    for r in diff:
        print("  DIFF", r["key"], "en=", r["en"], "ko=", r["ko"], "override=", r["override"],
              "ko_bytes=", r["ko_bytes"])
    print("ko chars remaining in target keys:", has_ko_char)
    print("OK" if out["ok"] else "FAILED")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
