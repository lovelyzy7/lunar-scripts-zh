#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_fix3_en.py — EN 客户端内置弹窗串补丁（fix3 EN 版）。

与 JP 版 patch_fix3.py 的差异：
  A. TextAsset 载体是 **EN 表**（键同名、值为 EN）：
       assets/bin/Data/a1e9ec10c664743ac927859dda597701  TextAsset "ui"    (en)
       assets/bin/Data/6c88814b67ea44496a219083a723a1e5  TextAsset "titleflow" (en)
       assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb  TextAsset "nt"     (en)
     替换按 **builtin_strings.json 键名单** 做 EN→中 值替换（同义表口径同 JP target_zh，
     如 ゲーム終了/Quit Game → 结束游戏）；注意 EN 里 T02/S21 同值 "Contact"、
     S24/S26 同值 "Continue" 译文不同，**只能按键替换，不能按值全局替换**。
  B. metadata stringLiteral —— EN 包内同簇仍是 **JP 源串**（实测 EN metadata
     #20948-20962 = JP #20410-20424：キャンセル/閉じる/ムービー再生/…），故
     直接复用 JP 源串→中文（≤原字节、NUL 填充，机制同 lunar-scripts patch_metadata_strings）。

用法（UnityPy 走 zh-l10n\\.venv site-packages）：
  python patch_fix3_en.py apply  --work DIR [--dry-run]   # 就地打补丁（apktool 解包目录）
  python patch_fix3_en.py verify --work DIR               # 回读校验
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent                       # zh-l10n/work/en-apk 或 en-client/
ROOT = next((p for p in [HERE, *HERE.parents]
             if (p / "zh-l10n" / "work" / "apk" / "fix3").is_dir()), HERE.parents[2])  # E:\NieRReincarnation（锚点查找）
TABLE = ROOT / "zh-l10n" / "work" / "apk" / "fix3" / "builtin_strings.json"

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
TS_EN = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
    "assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb": "nt(en)",
}
METADATA_MAGIC = 0xFAB11BAF
HDR_STRING_LITERAL_OFF = 8
HDR_STRING_LITERAL_DATA_OFF = 16


# ---------------------------------------------------------------- utilities

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_entries(tier: str = "all") -> list[dict]:
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    want = {"apply", "supplement"} if tier == "all" else {"apply"}
    return [e for e in t["entries"] if e["tier"] in want]


def key_map(entries: list[dict]) -> dict[str, str]:
    """TextAsset key -> 中文（键名单驱动；metadata.* 伪键跳过）。"""
    m: dict[str, str] = {}
    for e in entries:
        for k in e.get("keys", []):
            if k.startswith("metadata."):
                continue
            if not e.get("target_zh"):
                continue
            m[k] = e["target_zh"]
    return m


def meta_repl(entries: list[dict]) -> dict[str, str]:
    """metadata 同 JP：源串（JP 内置串）-> 中文（仅 expected_metadata>0 的条目）。"""
    m: dict[str, str] = {}
    for e in entries:
        if e.get("expected_metadata") and e.get("target_zh"):
            s = e["source_ja"]
            if s.startswith("titleflow.dialog.termofservice"):
                continue
            m[s] = e["target_zh"]
    return m


# ---------------------------------------------------------------- metadata

def meta_header(data: bytes):
    magic, version = struct.unpack_from("<Ii", data, 0)
    sl_off, sl_size = struct.unpack_from("<II", data, HDR_STRING_LITERAL_OFF)
    sld_off, sld_size = struct.unpack_from("<II", data, HDR_STRING_LITERAL_DATA_OFF)
    return magic, version, sl_off, sl_size, sld_off, sld_size


def meta_entries(data: bytes):
    _, _, sl_off, sl_size, sld_off, sld_size = meta_header(data)
    out = []
    for i in range(sl_size // 8):
        e_off = sl_off + i * 8
        e_len, e_idx = struct.unpack_from("<II", data, e_off)
        out.append((i, e_off, e_len, e_idx))
    return out, sld_off, sld_size


def patch_metadata(data: bytes, repl: dict[str, str]) -> tuple[bytes, list[dict]]:
    """stringLiteral 表项原地替换（同 lunar/JP fix3 机制：只许变短，NUL 填充）。"""
    buf = bytearray(data)
    magic, version, sl_off, sl_size, sld_off, sld_size = meta_header(buf)
    if magic != METADATA_MAGIC:
        raise ValueError(f"bad metadata magic 0x{magic:08X}")
    ents, _, _ = meta_entries(buf)
    log: list[dict] = []
    for old, new in repl.items():
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        if len(nb) > len(ob):
            log.append({"old": old, "new": new, "status": "SKIP_TOO_LONG",
                        "old_bytes": len(ob), "new_bytes": len(nb)})
            continue
        hits = [(i, e_off, e_len, e_idx) for (i, e_off, e_len, e_idx) in ents
                if e_len == len(ob) and buf[sld_off + e_idx:sld_off + e_idx + e_len] == ob]
        already = [(i, e_off, e_len, e_idx) for (i, e_off, e_len, e_idx) in ents
                   if e_len == len(nb) and buf[sld_off + e_idx:sld_off + e_idx + e_len] == nb
                   and e_len <= len(ob)]
        if not hits and already:
            log.append({"old": old, "new": new, "status": "ALREADY",
                        "entries": [i for i, *_ in already]})
            continue
        if not hits:
            log.append({"old": old, "new": new, "status": "NOT_FOUND"})
            continue
        slots: dict[int, list] = {}
        for (i, e_off, e_len, e_idx) in hits:
            slots.setdefault(e_idx, []).append((i, e_off, e_len))
        for e_idx, items in slots.items():
            pos = sld_off + e_idx
            e_len = items[0][2]
            buf[pos:pos + e_len] = nb + b"\x00" * (e_len - len(nb))
            for (i, e_off, _l) in items:
                struct.pack_into("<I", buf, e_off, len(nb))
        log.append({"old": old, "new": new, "status": "PATCHED",
                    "entries": [i for i, *_ in hits],
                    "entry_offsets": [hex(e) for _, e, *_ in hits],
                    "data_indexes": [hex(x) for x in slots]})
    return bytes(buf), log


# ---------------------------------------------------------------- textasset

def _ta_text(d) -> str:
    s = getattr(d, "m_Script", None)
    return s.decode("utf-8") if isinstance(s, bytes) else s


def patch_textasset_keyed(buf: bytes, kmap: dict[str, str]) -> tuple[bytes, list[dict]]:
    """按 key 列表替换 EN 值 -> 中文（值内 \n 为字面两字符，不动结构）。"""
    import UnityPy

    env = UnityPy.load(buf)
    log: list[dict] = []
    any_change = False
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", None) or getattr(d, "name", None)
        text = _ta_text(d)
        trailing = text.endswith("\n")
        lines = text.split("\n")
        if trailing and lines and lines[-1] == "":
            lines = lines[:-1]
        changed = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            sep = line.find(":")
            if sep <= 0:
                continue
            key, value = line[:sep], line[sep + 1:]
            if key in kmap:
                new_line = f"{key}:{kmap[key]}"
                if new_line != line:
                    lines[i] = new_line
                    changed.append({"key": key, "old": value, "new": kmap[key]})
        if changed:
            any_change = True
            new_text = "\n".join(lines) + ("\n" if trailing else "")
            d.m_Script = new_text
            d.save()
        log.append({"asset": name, "changed": changed, "changed_count": len(changed)})
    if not any_change:
        return buf, log
    fobj = list(env.files.values())[0]
    return fobj.save(), log


def verify_textasset_keyed(orig: bytes, new: bytes, kmap: dict[str, str]) -> dict:
    import UnityPy

    def load(buf):
        env = UnityPy.load(buf)
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                d = obj.read()
                return (getattr(d, "m_Name", None) or getattr(d, "name", None)), _ta_text(d)
        return None, None

    on, ot = load(orig)
    nn, nt = load(new)
    res: dict = {"ok": True, "checks": {}}
    res["checks"]["name_unchanged"] = {"ok": on == nn, "orig": on, "new": nn}
    o_lines, n_lines = ot.split("\n"), nt.split("\n")
    res["checks"]["line_count"] = {"ok": len(o_lines) == len(n_lines),
                                   "orig": len(o_lines), "new": len(n_lines)}
    bad = []
    changed_keys = []
    for i, (ol, nl) in enumerate(zip(o_lines, n_lines)):
        if ol == nl:
            continue
        o_sep, n_sep = ol.find(":"), nl.find(":")
        o_key = ol[:o_sep]
        n_val = nl[n_sep + 1:]
        if o_key not in kmap or kmap[o_key] != n_val or ol[:o_sep] != nl[:n_sep]:
            bad.append({"line": i + 1, "orig": ol[:80], "new": nl[:80]})
        else:
            changed_keys.append(o_key)
    res["checks"]["only_keyed_lines_changed"] = {"ok": not bad, "unexpected": bad[:10]}
    res["checks"]["changed_keys"] = changed_keys
    per = {}
    for k, zh in kmap.items():
        old_n = sum(1 for l in n_lines if l.find(":") > 0 and l[:l.find(":")] == k and l[l.find(":") + 1:] != zh)
        new_n = sum(1 for l in n_lines if l.find(":") > 0 and l[:l.find(":")] == k and l[l.find(":") + 1:] == zh)
        per[k] = {"not_target_remaining": old_n, "target_hits": new_n}
    res["checks"]["keys"] = per
    for k, v in res["checks"].items():
        if isinstance(v, dict) and "ok" in v and not v["ok"]:
            res["ok"] = False
    return res


def verify_metadata(orig: bytes, new: bytes, repl: dict[str, str]) -> dict:
    res = {"ok": True, "checks": {}}
    o_h, n_h = meta_header(orig), meta_header(new)
    res["checks"]["header_unchanged"] = {"ok": o_h == n_h}
    res["checks"]["size_unchanged"] = {"ok": len(orig) == len(new),
                                       "orig": len(orig), "new": len(new)}
    o_ents, o_sld, _ = meta_entries(orig)
    n_ents, n_sld, _ = meta_entries(new)
    res["checks"]["entry_count"] = {"ok": len(o_ents) == len(n_ents)}
    unchanged_ok = True
    for (i, oe_off, oe_len, oe_idx), (j, ne_off, ne_len, ne_idx) in zip(o_ents, n_ents):
        osl = orig[o_sld + oe_idx:o_sld + oe_idx + oe_len]
        nsl = new[n_sld + ne_idx:n_sld + ne_idx + ne_len]
        if osl == nsl and oe_len == ne_len:
            if oe_off != ne_off or struct.unpack_from("<I", orig, oe_off)[0] != struct.unpack_from("<I", new, ne_off)[0]:
                unchanged_ok = False
    res["checks"]["non_target_entries_byte_identical"] = {"ok": unchanged_ok}
    per_src = {}
    for old, exp_target in repl.items():
        ob, nb = old.encode("utf-8"), exp_target.encode("utf-8")
        old_n = sum(1 for (i, e_off, e_len, e_idx) in n_ents
                    if e_len == len(ob) and new[n_sld + e_idx:n_sld + e_idx + e_len] == ob)
        new_n = sum(1 for (i, e_off, e_len, e_idx) in n_ents
                    if e_len == len(nb) and new[n_sld + e_idx:n_sld + e_idx + e_len] == nb)
        per_src[old] = {"old_remaining": old_n, "new_hits": new_n}
    res["checks"]["values"] = per_src
    for k, v in res["checks"].items():
        if isinstance(v, dict) and "ok" in v and not v["ok"]:
            res["ok"] = False
    return res


# ---------------------------------------------------------------- commands

def cmd_apply(work: Path, tier: str, dry_run: bool) -> int:
    entries = load_entries(tier)
    kmap = key_map(entries)
    mrep = meta_repl(entries)
    print(f"[fix3-en] tier={tier} keys={len(kmap)} meta_repl={len(mrep)}")
    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": "patch_fix3_en.py",
              "tier": tier, "dry_run": dry_run, "keys": kmap, "meta_repl": mrep,
              "files": {}, "ok": True}
    for entry, label in TS_EN.items():
        p = work / entry
        if not p.is_file():
            report["files"][entry] = {"missing": True}
            report["ok"] = False
            print(f"[fix3-en] MISSING {entry}")
            continue
        raw = p.read_bytes()
        out, log = patch_textasset_keyed(raw, kmap)
        n = sum(x["changed_count"] for x in log)
        report["files"][entry] = {"label": label, "sha256_before": sha256(raw),
                                  "sha256_after": sha256(out), "changed": raw != out,
                                  "changed_count": n, "log": log}
        print(f"[fix3-en] {label} changed_lines={n}")
        if not dry_run and raw != out:
            p.write_bytes(out)
    mp = work / META_ENTRY
    if not mp.is_file():
        report["files"][META_ENTRY] = {"missing": True}
        report["ok"] = False
    else:
        raw = mp.read_bytes()
        out, mlog = patch_metadata(raw, mrep)
        report["files"][META_ENTRY] = {"sha256_before": sha256(raw), "sha256_after": sha256(out),
                                       "changed": raw != out, "log": mlog}
        print(f"[fix3-en] metadata: " + json.dumps(
            {x["old"]: x["status"] for x in mlog}, ensure_ascii=False))
        if not dry_run and raw != out:
            mp.write_bytes(out)
    (HERE / "apply_report_en.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fix3-en] report -> {HERE / 'apply_report_en.json'}")
    return 0 if report["ok"] else 1


def cmd_verify(work: Path, tier: str) -> int:
    entries = load_entries(tier)
    kmap = key_map(entries)
    mrep = meta_repl(entries)
    ok_all = True
    vreport = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": {}}
    for entry, label in TS_EN.items():
        p = work / entry
        raw = p.read_bytes() if p.is_file() else b""
        # 回读：目标键值 == 中文
        import UnityPy
        hits = {}
        if p.is_file():
            env = UnityPy.load(raw)
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = _ta_text(obj.read())
                    kv = {}
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
                    for k, zh in kmap.items():
                        if k in kv:
                            hits[k] = {"value": kv[k], "is_zh": kv[k] == zh}
        missing = [k for k in kmap if k not in hits]
        bad = [k for k, v in hits.items() if not v["is_zh"]]
        vreport["files"][label] = {"hits": len(hits), "bad": bad, "missing_keys_count": len(missing)}
        print(f"[verify] {label}: hits={len(hits)} bad={len(bad)}")
        if bad:
            ok_all = False
    mp = work / META_ENTRY
    if mp.is_file():
        new = mp.read_bytes()
        per = {}
        for old, zh in mrep.items():
            ob, nb = old.encode("utf-8"), zh.encode("utf-8")
            ents, sld, _ = meta_entries(new)
            old_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(ob) and new[sld + e_idx:sld + e_idx + e_len] == ob)
            new_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(nb) and new[sld + e_idx:sld + e_idx + e_len] == nb)
            per[old] = {"old_remaining": old_n, "new_hits": new_n, "ok": old_n == 0 and new_n >= 1}
            if not per[old]["ok"]:
                ok_all = False
        vreport["metadata"] = per
        print("[verify] metadata: " + json.dumps({k: v for k, v in per.items()}, ensure_ascii=False))
    vreport["ok"] = ok_all
    (HERE / "verify_report_en.json").write_text(
        json.dumps(vreport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify] ok={ok_all}")
    return 0 if ok_all else 1


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--work", required=True)
    p_apply.add_argument("--tier", choices=["apply", "all"], default="all")
    p_apply.add_argument("--dry-run", action="store_true")
    p_ver = sub.add_parser("verify")
    p_ver.add_argument("--work", required=True)
    p_ver.add_argument("--tier", choices=["apply", "all"], default="all")
    args = ap.parse_args()
    if args.cmd == "apply":
        return cmd_apply(Path(args.work).resolve(), args.tier, args.dry_run)
    return cmd_verify(Path(args.work).resolve(), args.tier)


if __name__ == "__main__":
    raise SystemExit(main())
