#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix3 —— il2cpp/APK 内置 UI 串补丁工具（标题菜单 / ダウンロード確認 族 / 玩家名注册 / 全局按钮）

载体（已彻查定位，见 FIX3-REPORT.md）：
  A. APK 内置 ja TextAsset 表（key:value 行）：
       assets/bin/Data/35005335013ad4314b0ac8afbfe27b9c  TextAsset "ui"
       assets/bin/Data/5296ae89c03c14825a9f664b0c355ccc  TextAsset "titleflow"
       assets/bin/Data/ed79b6250ad8541b1ba6f2a229fcc9bf  TextAsset "nt"
  B. global-metadata.dat stringLiteral 表项（お知らせ/閉じる/キャンセル/OK 等）。

替换机制：
  A. TextAsset —— 值级精确替换（key:value 行的 value == 原文才换），UnityPy 重写
     SerializedFile（与文本包/fix1 help 相同机制，长度任意）；
  B. metadata  —— stringLiteral 表项原地替换（同 lunar-scripts-jp patch_metadata_strings）：
     仅允许 len(new)<=len(old)，写新值+尾部 NUL 填充并回写 length 字段，
     不移动字节、不改节偏移；变长只能变短。

用法（TextAsset 相关子命令需 UnityPy venv：zh-l10n\\.venv\\Scripts\\python.exe）：
  python patch_fix3.py extract              # 从原版 APK 解出 3 个载体 -> fix3/orig/
  python patch_fix3.py patch [--tier apply|all]
  python patch_fix3.py verify               # 回读验证 -> fix3/verify_report.json
  python patch_fix3.py apply --work DIR [--dry-run]   # 集成：就地打补丁到 apktool 解包目录
  python patch_fix3.py all [--tier apply|all]         # extract+patch+verify
  python patch_fix3.py tsv                  # 由 builtin_strings.json 生成 TSV

设计要点：
  * 只读原版 APK；所有产物都是副本（orig/patched/），apply 对 work 目录就地改
    （就地改保证 lunar-scripts-jp 已写入 metadata 的服务器地址不被覆盖）；
  * 幂等：已替换的表项/行自动跳过（old 消失且 new 命中预期次数）；
  * 值级精确匹配：不会误伤长句子串（如 网络错误文案里含「お問い合わせ」的句子）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # zh-l10n/work/apk/fix3
ROOT = HERE.parents[3]                          # E:\NieRReincarnation
APK = ROOT / "resources" / "NieR Re[in]carnation_3.7.1_JP.apk"
TABLE = HERE / "builtin_strings.json"
ORIG = HERE / "orig"
PATCHED = HERE / "patched"

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
TS_ENTRIES = {
    "assets/bin/Data/35005335013ad4314b0ac8afbfe27b9c": "ui",
    "assets/bin/Data/5296ae89c03c14825a9f664b0c355ccc": "titleflow",
    "assets/bin/Data/ed79b6250ad8541b1ba6f2a229fcc9bf": "nt",
}
ALL_TARGETS = {META_ENTRY: "metadata", **TS_ENTRIES}

METADATA_MAGIC = 0xFAB11BAF
HDR_STRING_LITERAL_OFF = 8          # v24: (offset,size) 对
HDR_STRING_LITERAL_DATA_OFF = 16


# ---------------------------------------------------------------- utilities

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_table(tier: str) -> list[dict]:
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    if tier == "all":
        want = {"apply", "supplement"}
    else:
        want = {"apply"}
    return [e for e in t["entries"] if e["tier"] in want]


def repl_map(entries: list[dict]) -> dict[str, str]:
    """source -> target（值级精确匹配；同 source 后者覆盖前者仅当 target 不同时报错）"""
    m: dict[str, str] = {}
    for e in entries:
        s, z = e["source_ja"], e["target_zh"]
        if s.startswith("titleflow.dialog.termofservice"):
            continue
        if not z:
            continue
        if s in m and m[s] != z:
            raise SystemExit(f"表冲突: {s!r} 有两个不同译文")
        m[s] = z
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
    """stringLiteral 表项原地替换（同 lunar 机制：只许变短，NUL 填充）。"""
    buf = bytearray(data)
    magic, version, sl_off, sl_size, sld_off, sld_size = meta_header(buf)
    if magic != METADATA_MAGIC:
        raise ValueError(f"bad magic 0x{magic:08X}")
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
        # 数据槽（可能多表项共享 dataIndex）写一次；每个表项回写 length
        slots = {}
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


def verify_metadata(orig: bytes, new: bytes, repl: dict[str, str],
                    expected_meta: dict[str, int] | None = None) -> dict:
    expected_meta = expected_meta or {}
    res = {"ok": True, "checks": {}}
    o_magic, o_ver, o_sl, o_sls, o_sld, o_slds = meta_header(orig)
    n_magic, n_ver, n_sl, n_sls, n_sld, n_slds = meta_header(new)
    res["checks"]["header_unchanged"] = {
        "ok": (o_magic, o_ver, o_sl, o_sls, o_sld, o_slds) == (n_magic, n_ver, n_sl, n_sls, n_sld, n_slds),
        "orig": [hex(o_magic), o_ver, hex(o_sl), o_sls, hex(o_sld), o_slds],
        "new": [hex(n_magic), n_ver, hex(n_sl), n_sls, hex(n_sld), n_slds],
    }
    res["checks"]["size_unchanged"] = {"ok": len(orig) == len(new), "orig": len(orig), "new": len(new)}

    # 变化字节必须全部落在 stringLiteral 表 ∪ stringLiteralData 内
    changed_outside = []
    for i, (a, b) in enumerate(zip(orig, new)):
        if a != b:
            in_sl = o_sl <= i < o_sl + o_sls
            in_sld = o_sld <= i < o_sld + o_slds
            if not (in_sl or in_sld):
                changed_outside.append(i)
                if len(changed_outside) > 8:
                    break
    res["checks"]["diff_confined"] = {"ok": not changed_outside,
                                      "outside_offsets": changed_outside}

    # 逐表项复查：目标值命中数 == 预期；旧值 0；非目标表项逐字节不变
    o_ents, o_sld_off, o_sld_size = meta_entries(orig)
    n_ents, n_sld_off, n_sld_size = meta_entries(new)
    res["checks"]["entry_count"] = {"ok": len(o_ents) == len(n_ents),
                                    "orig": len(o_ents), "new": len(n_ents)}
    value_hits = {}
    unchanged_ok = True
    changed_entries = []
    for (i, oe_off, oe_len, oe_idx), (j, ne_off, ne_len, ne_idx) in zip(o_ents, n_ents):
        osl = orig[o_sld_off + oe_idx:o_sld_off + oe_idx + oe_len]
        nsl = new[n_sld_off + ne_idx:n_sld_off + ne_idx + ne_len]
        key = (oe_idx, oe_len)
        if osl != nsl or oe_len != ne_len:
            changed_entries.append(i)
        else:
            # 非目标槽应当完全一致（含 length 字段）
            if oe_off != ne_off or struct.unpack_from("<I", orig, oe_off)[0] != struct.unpack_from("<I", new, ne_off)[0]:
                unchanged_ok = False
        value_hits.setdefault(nsl.split(b"\x00")[0].decode("utf-8", "replace"), 0)
        value_hits[nsl.split(b"\x00")[0].decode("utf-8", "replace")] += 1

    res["checks"]["non_target_entries_byte_identical"] = {"ok": unchanged_ok}
    per_src = {}
    for old, exp_target in repl.items():
        ob, nb = old.encode("utf-8"), exp_target.encode("utf-8")
        old_n = sum(1 for (i, e_off, e_len, e_idx) in n_ents
                    if e_len == len(ob) and new[n_sld_off + e_idx:n_sld_off + e_idx + e_len] == ob)
        new_n = sum(1 for (i, e_off, e_len, e_idx) in n_ents
                    if e_len == len(nb) and new[n_sld_off + e_idx:n_sld_off + e_idx + e_len] == nb)
        exp = expected_meta.get(old, 0)
        per_src[old] = {"old_remaining": old_n, "new_hits": new_n,
                        "expected_new": exp, "ok": old_n == 0 and (new_n == exp or (exp == 0 and new_n == 0))}
    res["checks"]["values"] = per_src
    res["checks"]["changed_entry_indices"] = changed_entries
    for k, v in res["checks"].items():
        if isinstance(v, dict) and "ok" in v and not v["ok"]:
            res["ok"] = False
    for v in per_src.values():
        if not v["ok"]:
            res["ok"] = False
    return res


# ---------------------------------------------------------------- textasset

def _ta_text(d) -> str:
    s = getattr(d, "m_Script", None)
    return s.decode("utf-8") if isinstance(s, bytes) else s


def patch_textasset(buf: bytes, repl: dict[str, str]) -> tuple[bytes, list[dict]]:
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
            if value in repl:
                new_line = f"{key}:{repl[value]}"
                if new_line != line:
                    lines[i] = new_line
                    changed.append({"key": key, "old": value, "new": repl[value]})
        if changed:
            any_change = True
            new_text = "\n".join(lines) + ("\n" if trailing else "")
            d.m_Script = new_text
            d.save()
        log.append({"asset": name, "changed": changed,
                    "changed_count": len(changed)})
    if not any_change:
        return buf, log          # 无改动不重写（保持原始字节）
    fobj = list(env.files.values())[0]
    return fobj.save(), log


def verify_textasset(orig: bytes, new: bytes, repl: dict[str, str]) -> dict:
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
    res = {"ok": True, "checks": {}}
    res["checks"]["name_unchanged"] = {"ok": on == nn, "orig": on, "new": nn}
    o_lines, n_lines = ot.split("\n"), nt.split("\n")
    res["checks"]["line_count"] = {"ok": len(o_lines) == len(n_lines),
                                   "orig": len(o_lines), "new": len(n_lines)}
    changed_keys, bad = [], []
    for i, (ol, nl) in enumerate(zip(o_lines, n_lines)):
        if ol == nl:
            continue
        o_sep, n_sep = ol.find(":"), nl.find(":")
        o_key, o_val = ol[:o_sep], ol[o_sep + 1:]
        n_key, n_val = nl[:n_sep], nl[n_sep + 1:]
        if o_key != n_key or o_val not in repl or repl[o_val] != n_val:
            bad.append({"line": i + 1, "orig": ol[:80], "new": nl[:80]})
        else:
            changed_keys.append(o_key)
    res["checks"]["only_expected_lines_changed"] = {"ok": not bad, "unexpected": bad[:10]}
    res["checks"]["changed_keys"] = changed_keys
    # 旧值残留 / 新值计数
    per = {}
    for old, newv in repl.items():
        per[old] = {"old_remaining_in_lines": sum(1 for l in n_lines if l.find(":") >= 0 and l[l.find(":") + 1:] == old),
                    "new_hits": sum(1 for l in n_lines if l.find(":") >= 0 and l[l.find(":") + 1:] == newv)}
    res["checks"]["values"] = per
    for k, v in res["checks"].items():
        if isinstance(v, dict) and "ok" in v and not v["ok"]:
            res["ok"] = False
    return res


# ---------------------------------------------------------------- subcommands

def cmd_extract() -> int:
    ORIG.mkdir(parents=True, exist_ok=True)
    manifest = {"apk": str(APK), "apk_sha256": sha256(APK.read_bytes()), "files": {}}
    with zipfile.ZipFile(APK) as zf:
        for entry in ALL_TARGETS:
            buf = zf.read(entry)
            flat = entry.replace("/", "__")
            (ORIG / flat).write_bytes(buf)
            manifest["files"][entry] = {"flat": flat, "bytes": len(buf), "sha256": sha256(buf)}
            print(f"[extract] {entry} -> orig/{flat} ({len(buf)} bytes)")
    (HERE / "orig_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def cmd_patch(tier: str) -> int:
    entries = load_table(tier)
    repl = repl_map(entries)
    print(f"[patch] tier={tier} entries={len(entries)} values={len(repl)}")
    PATCHED.mkdir(parents=True, exist_ok=True)
    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tier": tier, "files": {}}
    for entry, kind in ALL_TARGETS.items():
        flat = entry.replace("/", "__")
        src = ORIG / flat
        if not src.is_file():
            print(f"[!] 缺少 orig/{flat}，先运行 extract", file=sys.stderr)
            return 2
        raw = src.read_bytes()
        if kind == "metadata":
            out, log = patch_metadata(raw, repl)
        else:
            out, log = patch_textasset(raw, repl)
        (PATCHED / flat).write_bytes(out)
        report["files"][entry] = {
            "kind": kind, "orig_sha256": sha256(raw), "out_sha256": sha256(out),
            "orig_bytes": len(raw), "out_bytes": len(out), "log": log,
        }
        print(f"[patch] {entry} -> patched/{flat} ({len(raw)} -> {len(out)} bytes)")
        for item in log:
            st = item.get("status") or f"{item.get('changed_count')} lines"
            print(f"        {st}: {(item.get('old') or item.get('asset') or '')!r}")
    (HERE / "patch_log.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def cmd_verify(tier: str) -> int:
    entries = load_table(tier)
    repl = repl_map(entries)
    # 每条 source 的预期命中数（来自表）
    expected = {}
    for e in entries:
        if not e["target_zh"]:
            continue
        s = e["source_ja"]
        if s.startswith("titleflow.dialog.termofservice"):
            continue
        exp = expected.setdefault(s, {"textasset": 0, "metadata": 0, "target": e["target_zh"]})
        exp["textasset"] += e["expected_textasset"]
        exp["metadata"] += e["expected_metadata"]
    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tier": tier,
              "ok": True, "files": {}}
    for entry, kind in ALL_TARGETS.items():
        flat = entry.replace("/", "__")
        o = (ORIG / flat).read_bytes()
        n = (PATCHED / flat).read_bytes()
        if kind == "metadata":
            r = verify_metadata(o, n, repl,
                                {s: v["metadata"] for s, v in expected.items()})
        else:
            r = verify_textasset(o, n, repl)
        report["files"][entry] = r
        status = "ok" if r["ok"] else "FAIL"
        print(f"[verify] {status} {entry}")
        if not r["ok"]:
            report["ok"] = False
            print(json.dumps(r["checks"], ensure_ascii=False)[:1200])
    # 出现计数总表（译文命中数与预期一致）
    counts = {}
    for old, newv in repl.items():
        counts[old] = {"target": newv, "textasset": 0, "metadata": 0}
    for entry, kind in ALL_TARGETS.items():
        flat = entry.replace("/", "__")
        n = (PATCHED / flat).read_bytes()
        if kind == "metadata":
            ents, sld_off, sld_size = meta_entries(n)
            for old, newv in repl.items():
                nb = newv.encode("utf-8")
                counts[old]["metadata"] += sum(
                    1 for (i, e_off, e_len, e_idx) in ents
                    if e_len == len(nb) and n[sld_off + e_idx:sld_off + e_idx + e_len] == nb)
        else:
            import UnityPy
            env = UnityPy.load(n)
            for obj in env.objects:
                if obj.type.name != "TextAsset":
                    continue
                text = _ta_text(obj.read())
                for line in text.split("\n"):
                    sep = line.find(":")
                    if sep > 0:
                        val = line[sep + 1:]
                        for old, newv in repl.items():
                            if val == newv:
                                counts[old]["textasset"] += 1
    report["translation_hit_counts"] = counts
    all_match = True
    for old, c in counts.items():
        exp = expected.get(old, {"textasset": 0, "metadata": 0})
        match = (c["textasset"] == exp["textasset"] and c["metadata"] == exp["metadata"])
        c["expected_textasset"] = exp["textasset"]
        c["expected_metadata"] = exp["metadata"]
        c["matches_expectation"] = match
        if not match:
            all_match = False
        flag = "ok" if match else "MISMATCH"
        print(f"  [count] {flag} {old!r} -> {c['target']!r}: "
              f"textasset={c['textasset']}/{exp['textasset']} metadata={c['metadata']}/{exp['metadata']}")
    report["hit_counts_match_expectation"] = all_match
    if not all_match:
        report["ok"] = False
    (HERE / "verify_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify] overall {'ok' if report['ok'] else 'FAIL'} -> verify_report.json")
    return 0 if report["ok"] else 1


def cmd_apply(work: Path, tier: str, dry_run: bool) -> int:
    """集成点：对 apktool 解包目录就地打补丁（metadata 在 lunar 私服补丁之后执行）。
    就地打补丁 = 不覆盖 lunar 已写入的服务器地址。"""
    entries = load_table(tier)
    repl = repl_map(entries)
    if not work.is_dir():
        print(f"[!] work 目录不存在: {work}", file=sys.stderr)
        return 2
    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "work": str(work),
              "tier": tier, "dry_run": dry_run, "files": {}}
    for entry, kind in ALL_TARGETS.items():
        path = work / entry
        if not path.is_file():
            print(f"[!] work 中缺少 {entry}", file=sys.stderr)
            report["files"][entry] = {"status": "MISSING"}
            report["ok"] = False
            continue
        raw = path.read_bytes()
        if kind == "metadata":
            out, log = patch_metadata(raw, repl)
        else:
            out, log = patch_textasset(raw, repl)
        report["files"][entry] = {
            "status": "DRY_RUN" if dry_run else "APPLIED",
            "orig_sha256": sha256(raw), "out_sha256": sha256(out),
            "changed": raw != out, "log": log,
        }
        print(f"[apply] {entry} changed={raw != out}")
        for item in log:
            st = item.get("status") or f"{item.get('changed_count')} lines"
            print(f"        {st}: {(item.get('old') or item.get('asset') or '')!r}")
        if not dry_run and raw != out:
            path.write_bytes(out)
    (HERE / "apply_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def cmd_tsv() -> int:
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    out = HERE / "builtin_strings.tsv"
    lines = ["id\ttier\tfamily\tsource_ja\ttarget_zh\texpected_textasset\texpected_metadata\texpected_total\tkeys\tnote"]
    for e in t["entries"]:
        lines.append("\t".join([
            e["id"], e["tier"], e["family"], e["source_ja"].replace("\t", " "),
            e["target_zh"].replace("\t", " "), str(e["expected_textasset"]),
            str(e["expected_metadata"]), str(e["expected_total"]),
            "|".join(e.get("keys", [])), e.get("note", "").replace("\t", " "),
        ]))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[tsv] {out} rows={len(t['entries'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="fix3 il2cpp/APK 内置 UI 串补丁")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("extract")
    p_patch = sub.add_parser("patch")
    p_patch.add_argument("--tier", choices=["apply", "all"], default="apply")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--tier", choices=["apply", "all"], default="apply")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--work", required=True)
    p_apply.add_argument("--tier", choices=["apply", "all"], default="apply")
    p_apply.add_argument("--dry-run", action="store_true")
    p_all = sub.add_parser("all")
    p_all.add_argument("--tier", choices=["apply", "all"], default="apply")
    sub.add_parser("tsv")
    args = ap.parse_args()

    if args.cmd == "extract":
        return cmd_extract()
    if args.cmd == "patch":
        return cmd_patch(args.tier)
    if args.cmd == "verify":
        return cmd_verify(args.tier)
    if args.cmd == "apply":
        return cmd_apply(Path(args.work).resolve(), args.tier, args.dry_run)
    if args.cmd == "all":
        rc = cmd_extract()
        if rc:
            return rc
        rc = cmd_patch(args.tier)
        if rc:
            return rc
        return cmd_verify(args.tier)
    if args.cmd == "tsv":
        return cmd_tsv()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
