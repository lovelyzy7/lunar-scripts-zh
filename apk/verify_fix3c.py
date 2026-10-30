#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix3c APK 验证（对照 build-fix3b-verify.json ①-⑥；数据源=build-fix3c-verify.json）。

检查项：
  ① apksigner verify + 证书指纹 == EE:C2:3B…（EXPECTED）+ v2/v3
  ② TextAsset 抽查 + fix3 62 串逐条命中计数（对照 builtin_strings.json 预期）
  ③ metadata stringLiteral 回读（公告/关闭/取消 + 播放影片族）
  ④ **四**字体条目 sha256 == payload2（fonts-fix4/out2/payload2，含补换 YDHopeL/YDWingsM）
  ⑤ 私服地址 192.168.2.6 仍在（10 处口径同 fix3b）
  ⑥ 原版 APK sha256 前后不变（基线 25b6326c…）

用法：C:/Python314/python.exe zh-l10n/work/apk/verify_fix3c.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
HERE = ROOT / "zh-l10n" / "work" / "apk"
FIX3 = HERE / "fix3"
sys.path.insert(0, str(FIX3))
import patch_fix3  # noqa: E402  （复用其表/metadata 解析，与 apply 同口径）

APK = HERE / "nier-mod-menu-jp-font-fix3c.apk"
OUT_JSON = HERE / "build-fix3c-verify.json"
ORIG_APK = ROOT / "resources" / "NieR Re[in]carnation_3.7.1_JP.apk"
ORIG_BASELINE = "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609"
PAYLOAD = ROOT / "zh-l10n" / "work" / "fonts-fix4" / "out2" / "payload2" / "assets" / "bin" / "Data"
FONT_ENTRIES = {
    "assets/bin/Data/6f937efa0660c47f59d5215d276b1cbb": "6f937efa0660c47f59d5215d276b1cbb",
    "assets/bin/Data/7089ac60979c94824ac549baab08cfa7": "7089ac60979c94824ac549baab08cfa7",
    "assets/bin/Data/ad1489eb70ff840d19d7d0841bcdd3a9": "ad1489eb70ff840d19d7d0841bcdd3a9",
    "assets/bin/Data/550e0743a6b6344cfa3380b9a07f58b6": "550e0743a6b6344cfa3380b9a07f58b6",
}
META_ENTRY = patch_fix3.META_ENTRY
TS_ENTRIES = patch_fix3.TS_ENTRIES
CERT_EXPECT = "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe"
PRIVATE_IP = b"192.168.2.6"

UI_SPOT = ["公告", "联系我们", "数据继承", "数据修复", "其他信息", "删除数据",
           "关闭", "取消", "下载确认",
           "结束游戏", "要结束游戏吗？"]
TITLEFLOW_SPOT = ["注册玩家名", "请输入玩家名"]
META_SPOT = ["公告", "关闭", "取消", "打开公告", "打开推特", "播放影片", "播放影片中"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def ta_text(buf: bytes) -> str:
    import UnityPy
    env = UnityPy.load(buf)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            s = getattr(d, "m_Script", None)
            if s is None:
                s = getattr(d, "script", None)
            if s is None:
                s = getattr(d, "text", None) or ""
            return s.decode("utf-8") if isinstance(s, (bytes, bytearray)) else str(s)
    return ""


def parse_kv_lines(text: str) -> list[tuple[str, str]]:
    out = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out.append((k, v))
    return out


def meta_values(data: bytes) -> list[str]:
    ents, sld_off, _ = patch_fix3.meta_entries(data)
    vals = []
    for (_i, _e_off, e_len, e_idx) in ents:
        vals.append(data[sld_off + e_idx:sld_off + e_idx + e_len].decode("utf-8", "replace"))
    return vals


def file_for_key(key: str) -> str:
    for pref, name in (("ui.", "ui"), ("titleflow.", "titleflow"), ("nt.", "nt")):
        if key.startswith(pref):
            return name
    return "?"


def main() -> int:
    res: dict = {"apk": str(APK), "ok": True}
    if not APK.is_file():
        print(f"[verify] APK 不存在: {APK}")
        return 2

    res["apk_sha256"] = sha256_file(APK)
    res["apk_bytes"] = APK.stat().st_size

    # ---- ⑥ 原版 APK 未变 ----
    orig_now = sha256_file(ORIG_APK)
    res["original_apk"] = {"sha256_now": orig_now, "baseline": ORIG_BASELINE,
                           "unchanged": orig_now == ORIG_BASELINE}
    if not res["original_apk"]["unchanged"]:
        res["ok"] = False

    with zipfile.ZipFile(APK) as zf:
        # ---- ① apksigner ----
        tools_dir = ROOT / "NieR-Re-In-Carnation-Mod_Menu" / "jp-client" / "tools"
        sys.path.insert(0, str(tools_dir))
        import _common as C  # noqa: E402
        cfg = C.load_toolpaths()
        tools = C.detect_tools(cfg)
        apksigner_jar = C.local_path(tools["apksigner_jar"])
        proc = subprocess.run([str(tools["java"]), "-jar", apksigner_jar,
                               "verify", "-v", "--print-certs", str(APK)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        text = (proc.stdout or "") + (proc.stderr or "")
        m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F:]+)", text)
        cert = m.group(1).replace(":", "").lower() if m else None
        res["apksigner"] = {
            "exit_code": proc.returncode,
            "verified_v2": "Verified using v2 scheme (APK Signature Scheme v2): true" in text,
            "verified_v3": "Verified using v3 scheme (APK Signature Scheme v3): true" in text,
            "cert_sha256": cert,
            "cert_matches_expected": cert == CERT_EXPECT,
        }
        if not (proc.returncode == 0 and res["apksigner"]["verified_v2"]
                and res["apksigner"]["verified_v3"]
                and res["apksigner"]["cert_matches_expected"]):
            res["ok"] = False

        # ---- ④ 四字体条目 ----
        res["fonts"] = {}
        for entry, name in FONT_ENTRIES.items():
            data = zf.read(entry)
            payload_sha = sha256_file(PAYLOAD / name)
            got = sha256_bytes(data)
            res["fonts"][entry] = {"sha256": got, "payload_sha256": payload_sha,
                                   "matches_payload": got == payload_sha}
            if got != payload_sha:
                res["ok"] = False

        # ---- ②③ TextAsset + metadata 解析 ----
        ts_kv: dict[str, list[tuple[str, str]]] = {}
        for entry, name in TS_ENTRIES.items():
            ts_kv[name] = parse_kv_lines(ta_text(zf.read(entry)))
        meta = zf.read(META_ENTRY)
        mvals = meta_values(meta)

        def present(name: str, needle: str) -> bool:
            return any(v == needle for (_k, v) in ts_kv[name])

        supplement_spot = {}
        for e in patch_fix3.load_table("all"):
            if e.get("tier") != "supplement":
                continue
            tgt = e.get("target_zh") or ""
            key0 = (e.get("keys") or ["?."])[0]
            fn = file_for_key(key0)
            meta_only = (int(e.get("expected_textasset") or 0) == 0
                         and int(e.get("expected_metadata") or 0) > 0)
            if meta_only or fn == "?":
                supplement_spot[e["id"]] = {
                    "needle": tgt, "file": "metadata",
                    "present": bool(tgt) and (tgt in mvals),
                }
            else:
                supplement_spot[e["id"]] = {"needle": tgt, "file": fn,
                                            "present": bool(tgt) and present(fn, tgt)}
        res["spot_checks"] = {
            "ui": {s: present("ui", s) for s in UI_SPOT},
            "titleflow": {s: present("titleflow", s) for s in TITLEFLOW_SPOT},
            "supplement": supplement_spot,
            "metadata_stringliteral": {s: (s in mvals) for s in META_SPOT},
        }
        sc = res["spot_checks"]
        if not (all(sc["ui"].values()) and all(sc["titleflow"].values())
                and all(v["present"] for v in sc["supplement"].values())
                and all(sc["metadata_stringliteral"].values())):
            res["ok"] = False

        # fix3 逐条命中计数（62 条口径）
        entries = patch_fix3.load_table("all")
        counts = []
        for e in entries:
            tgt = e.get("target_zh") or ""
            if not tgt or e["source_ja"].startswith("titleflow.dialog.termofservice"):
                continue
            per_file = {}
            for name in ("ui", "titleflow", "nt"):
                n = sum(1 for (_k, v) in ts_kv[name] if v == tgt)
                if n:
                    per_file[name] = n
            ta_n = sum(per_file.values())
            meta_n = sum(1 for v in mvals if v == tgt)
            exp_ta = int(e.get("expected_textasset") or 0)
            exp_meta = int(e.get("expected_metadata") or 0)
            ok = (ta_n == exp_ta and meta_n == exp_meta)
            counts.append({
                "id": e["id"], "tier": e["tier"], "target_zh": tgt,
                "keys": e.get("keys", []),
                "expected_textasset": exp_ta, "actual_textasset": ta_n,
                "actual_per_file": per_file,
                "expected_metadata": exp_meta, "actual_metadata": meta_n,
                "ok": ok,
            })
            if not ok:
                res["ok"] = False
        res["fix3_hit_counts"] = counts
        res["fix3_hit_summary"] = {
            "entries_checked": len(counts),
            "entries_ok": sum(1 for c in counts if c["ok"]),
            "total_textasset_hits": sum(c["actual_textasset"] for c in counts),
            "total_metadata_hits": sum(c["actual_metadata"] for c in counts),
        }
        legacy_ids = {f"T{i:02d}" for i in range(1, 16)} | {f"S{i:02d}" for i in range(1, 9)}
        legacy = [c for c in counts if c["id"] in legacy_ids]
        fresh = [c for c in counts if c["id"] not in legacy_ids]
        res["fix3_hit_split"] = {
            "legacy_fix3_23": {"entries": len(legacy),
                               "ok": sum(1 for c in legacy if c["ok"]),
                               "all_ok": all(c["ok"] for c in legacy)},
            "fix3b_new": {"entries": len(fresh),
                          "ok": sum(1 for c in fresh if c["ok"]),
                          "all_ok": all(c["ok"] for c in fresh)},
        }
        if not (res["fix3_hit_split"]["legacy_fix3_23"]["all_ok"]
                and res["fix3_hit_split"]["fix3b_new"]["all_ok"]):
            res["ok"] = False

        # ---- ⑤ 私服地址 ----
        ip_hits = {}
        if PRIVATE_IP in meta:
            ip_hits[META_ENTRY] = meta.count(PRIVATE_IP)
        for info in zf.infolist():
            if info.filename == META_ENTRY or info.file_size > (1 << 24):
                continue
            if not (info.filename.startswith("assets/bin/Data/")
                    or re.fullmatch(r"classes\d*\.dex", info.filename.split("/")[-1])
                    or info.filename.startswith("smali")):
                continue
            try:
                blob = zf.read(info.filename)
            except Exception:  # noqa: BLE001
                continue
            if PRIVATE_IP in blob:
                ip_hits[info.filename] = blob.count(PRIVATE_IP)
        res["private_server"] = {"ip": "192.168.2.6",
                                 "hits": ip_hits,
                                 "present_in_metadata": META_ENTRY in ip_hits,
                                 "total_hits": sum(ip_hits.values())}
        if not res["private_server"]["present_in_metadata"]:
            res["ok"] = False

    out = OUT_JSON
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[verify] overall {'ok' if res['ok'] else 'FAIL'} -> {out}")
    print(f"[verify] apk sha256={res['apk_sha256']}")
    print(f"[verify] cert={res['apksigner']['cert_sha256']} match={res['apksigner']['cert_matches_expected']} "
          f"v2={res['apksigner']['verified_v2']} v3={res['apksigner']['verified_v3']}")
    print(f"[verify] fonts_match={all(v['matches_payload'] for v in res['fonts'].values())} "
          f"({len(res['fonts'])} entries)")
    print(f"[verify] fix3 {res['fix3_hit_summary']['entries_ok']}/{res['fix3_hit_summary']['entries_checked']} "
          f"ta_hits={res['fix3_hit_summary']['total_textasset_hits']} "
          f"meta_hits={res['fix3_hit_summary']['total_metadata_hits']}")
    sp = res.get("fix3_hit_split", {})
    if sp:
        print(f"[verify] legacy23={sp['legacy_fix3_23']['ok']}/{sp['legacy_fix3_23']['entries']} "
              f"fix3b_new={sp['fix3b_new']['ok']}/{sp['fix3b_new']['entries']}")
    print(f"[verify] private_ip_hits={res['private_server']['total_hits']} "
          f"in_metadata={res['private_server']['present_in_metadata']}")
    print(f"[verify] original_unchanged={res['original_apk']['unchanged']}")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
