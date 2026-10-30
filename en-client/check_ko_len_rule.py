# -*- coding: utf-8 -*-
"""check_ko_len_rule.py — T01 机制长度规则回读：68 键新中文字节 <= 旧 ko 原值字节。"""
import json, sys
from pathlib import Path

HERE = Path(r"E:\NieRReincarnation\zh-l10n\work\en-apk")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
rep = json.loads((HERE / "apply_report_ko.json").read_text(encoding="utf-8"))
old = rep["old_ko_values"]
keys = rep["keys"]
bad = []
rows = []
for k, zh in keys.items():
    o = old.get(k)
    if o is None:
        bad.append((k, "NO_OLD"))
        continue
    ob, nb = len(o.encode("utf-8")), len(zh.encode("utf-8"))
    rows.append((k, ob, nb, nb <= ob))
    if nb > ob:
        bad.append((k, ob, nb))
print("keys:", len(keys), "violations:", len(bad), bad)
print("override entries:")
for k, ob, nb, ok in rows:
    if k in rep.get("ko_override", {}):
        print("  ", k, "old", ob, "new", nb, "ok", ok, "->", keys[k])
print("max growth:", max((nb - ob) for _, ob, nb, _ in rows), "all_nonpositive:",
      all(nb <= ob for _, ob, nb, _ in rows))
out = {"keys": len(keys), "violations": len(bad),
       "all_within_original_bytes": not bad,
       "rows": [{"key": k, "old_bytes": ob, "new_bytes": nb, "within": ok}
                for k, ob, nb, ok in rows]}
(HERE / "ko_len_rule_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
print("-> ko_len_rule_check.json")
