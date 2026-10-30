# -*- coding: utf-8 -*-
"""check_ko_scripts.py — ko 三载体全值脚本构成扫描（韩文/日文/拉丁），只读。"""
import sys, zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
APK = ROOT / "resources" / "NieR Re[in]carnation 3.7.1_EN.apk"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TS_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}


def classify(v):
    kana = sum(1 for c in v if "\u3040" <= c <= "\u30ff")
    hangul = sum(1 for c in v if "\uac00" <= c <= "\ud7af")
    han = sum(1 for c in v if "\u4e00" <= c <= "\u9fff")
    if hangul and not kana:
        return "KO" if not han else "KO+han"
    if kana:
        return "JA"
    if han:
        return "HAN-only"
    return "LATIN/other"


def main():
    import UnityPy
    with zipfile.ZipFile(APK) as zf:
        for entry, label in TS_KO.items():
            env = UnityPy.load(zf.read(entry))
            for obj in env.objects:
                if obj.type.name != "TextAsset":
                    continue
                s = obj.read().m_Script
                text = s.decode("utf-8") if isinstance(s, bytes) else s
                stats = {}
                ja_lines = []
                for line in text.split("\n"):
                    sep = line.find(":")
                    if sep <= 0 or line.strip().startswith("//"):
                        continue
                    k, v = line[:sep], line[sep + 1:]
                    c = classify(v)
                    stats[c] = stats.get(c, 0) + 1
                    if c == "JA":
                        ja_lines.append((k, v[:50]))
                print(label, "value-script mix:", stats)
                for k, v in ja_lines[:15]:
                    print("   JA:", k, "=", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
