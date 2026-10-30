#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_fix3_ko.py — EN 客户端内置弹窗串补丁（fix3 **ko 段** 版）。

背景（EN-APK-REPORT §四遗留）：EN 客户端选「한국어」时内置 TextAsset 表按 ko 槽取值；
上一轮只把 EN 段（a1e9ec10/6c88814b/1dc4624c）改成了中文，ko 段仍是韩文原文。
本工具把 **ko 段** 同键值替换为中文（与 EN 段现值同译文），使选韩国语时弹窗/按钮全中文。

载体（builtin_strings.json layers.textasset.not_touched 中的 ko 三件套）：
    assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486  TextAsset "ui"        (ko)
    assets/bin/Data/3286caf719be04314bd3208e16bc0e0e  TextAsset "titleflow" (ko)
    assets/bin/Data/d3f332a247d3c418d94d377ae81104c7  TextAsset "nt"        (ko)

机制：
  A. TextAsset **按键名单** 做 ko 值→中文 值替换（键名单同 EN 版 builtin_strings.json，
     同值不同译 T02/S21 Contact、S24/S26 Continue 由键驱动天然消歧）。
  B. **长度 ≤ 原字节** 硬约束（同 T01 metadata stringLiteral 机制的 len(new)<=len(old)）：
     逐条核对 ko 原值字节数；超长译文用更短译文（KO_OVERRIDE，见下）或 SKIP_TOO_LONG
     记录跳过原因。EN 段现值存在 2 条超长（ko 原文比 EN 短）：
       T02 ui.Outgame.Menu.Contact            ko「문의」6B  < 联系我们 12B → 短译「联系」6B
       S23 titleflow.dialog.maintenance.to.twitter  ko「Twitter로」10B < 前往推特 12B → 短译「去推特」9B
     其余 66 条 EN 段现值中文字节均 ≤ ko 原值字节，直接同 EN。
  C. metadata stringLiteral 单值不分段、上一轮已改中文 —— 本工具**不动 metadata**。

用法（UnityPy 走 zh-l10n\\.venv site-packages，同 patch_fix3_en.py）：
  python patch_fix3_ko.py apply  --work DIR [--dry-run]   # 就地打补丁（apktool 解包目录）
  python patch_fix3_ko.py verify --work DIR               # 回读校验（含旧值残留 0）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent                       # zh-l10n/work/en-apk 或 en-client/
ROOT = next((p for p in [HERE, *HERE.parents]
             if (p / "zh-l10n" / "work" / "apk" / "fix3").is_dir()), HERE.parents[2])  # E:\NieRReincarnation（锚点查找）
TABLE = ROOT / "zh-l10n" / "work" / "apk" / "fix3" / "builtin_strings.json"

TS_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}

# 超长条目短译对照（键 -> (短译, EN 段现值, 短译理由)）。约束：len(短译 utf-8) <= len(ko 原值 utf-8)。
KO_OVERRIDE = {
    "ui.Outgame.Menu.Contact": {
        "zh": "联系",
        "en_value": "联系我们",
        "reason": "ko 原值「문의」6B < EN 段现值「联系我们」12B；T01 机制 len(new)<=len(old)，取同义短译「联系」6B",
    },
    "titleflow.dialog.maintenance.to.twitter": {
        "zh": "去推特",
        "en_value": "前往推特",
        "reason": "ko 原值「Twitter로」10B < EN 段现值「前往推特」12B；T01 机制 len(new)<=len(old)，取同义短译「去推特」9B",
    },
}

APPLY_REPORT = HERE / "apply_report_ko.json"
VERIFY_REPORT = HERE / "verify_report_ko.json"


# ---------------------------------------------------------------- utilities

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_entries(tier: str = "all") -> list[dict]:
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    want = {"apply", "supplement"} if tier == "all" else {"apply"}
    return [e for e in t["entries"] if e["tier"] in want]


def key_map(entries: list[dict]) -> dict[str, str]:
    """TextAsset key -> 中文（键名单驱动；metadata.* 伪键跳过；KO_OVERRIDE 短译覆盖）。"""
    m: dict[str, str] = {}
    for e in entries:
        for k in e.get("keys", []):
            if k.startswith("metadata."):
                continue
            if not e.get("target_zh"):
                continue
            if k in KO_OVERRIDE:
                m[k] = KO_OVERRIDE[k]["zh"]
            else:
                m[k] = e["target_zh"]
    return m


# ---------------------------------------------------------------- textasset

def _ta_text(d) -> str:
    s = getattr(d, "m_Script", None)
    return s.decode("utf-8") if isinstance(s, bytes) else s


def patch_textasset_keyed(buf: bytes, kmap: dict[str, str]) -> tuple[bytes, list[dict]]:
    """按 key 列表替换 ko 值 -> 中文；**len(new) <= len(old) 硬约束**（T01 机制口径），
    超长记 SKIP_TOO_LONG 跳过（正常情况下 KO_OVERRIDE 已消化超长条目）。"""
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
        skipped = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            sep = line.find(":")
            if sep <= 0:
                continue
            key, value = line[:sep], line[sep + 1:]
            if key not in kmap:
                continue
            new_val = kmap[key]
            if new_val == value:
                continue
            ob = value.encode("utf-8")
            nb = new_val.encode("utf-8")
            if len(nb) > len(ob):
                skipped.append({
                    "key": key, "old": value, "new": new_val, "status": "SKIP_TOO_LONG",
                    "old_bytes": len(ob), "new_bytes": len(nb),
                    "reason": "T01 机制 len(new)<=len(old) 未满足且无 KO_OVERRIDE 短译",
                })
                continue
            new_line = f"{key}:{new_val}"
            lines[i] = new_line
            changed.append({
                "key": key, "old": value, "new": new_val,
                "old_bytes": len(ob), "new_bytes": len(nb),
                "shortened": key in KO_OVERRIDE,
            })
        if changed:
            any_change = True
            new_text = "\n".join(lines) + ("\n" if trailing else "")
            d.m_Script = new_text
            d.save()
        log.append({"asset": name, "changed": changed, "skipped": skipped,
                    "changed_count": len(changed), "skipped_count": len(skipped)})
    if not any_change:
        return buf, log
    fobj = list(env.files.values())[0]
    return fobj.save(), log


def verify_textasset_ko(new: bytes, kmap: dict[str, str], old_vals: dict[str, str]) -> dict:
    """回读：目标键值 == 中文；旧 ko 值行残留 == 0；非目标行结构不变（行数一致）。"""
    import UnityPy

    env = UnityPy.load(new)
    res: dict = {"ok": True, "checks": {}}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", None) or getattr(d, "name", None)
        text = _ta_text(d)
        lines = text.split("\n")
        kv = {}
        for line in lines:
            sep = line.find(":")
            if sep > 0:
                kv[line[:sep]] = line[sep + 1:]
        per = {}
        old_residual = []
        bad = []
        for k, zh in kmap.items():
            if k not in kv:
                continue
            is_zh = kv[k] == zh
            old_v = old_vals.get(k)
            old_left = (old_v is not None and kv[k] == old_v)
            per[k] = {"value": kv[k], "is_zh": is_zh, "old_value_residual": old_left}
            if not is_zh:
                bad.append(k)
            if old_left:
                old_residual.append(k)
        res["checks"][name] = {
            "keys_found": len(per), "zh_hits": sum(1 for v in per.values() if v["is_zh"]),
            "bad": bad, "old_value_residual_keys": old_residual,
            "old_value_residual_total": len(old_residual),
            "line_count": len(lines), "keys": per,
        }
        if bad or old_residual:
            res["ok"] = False
    return res


# ---------------------------------------------------------------- commands

def cmd_apply(work: Path, tier: str, dry_run: bool) -> int:
    entries = load_entries(tier)
    kmap = key_map(entries)
    print(f"[fix3-ko] tier={tier} keys={len(kmap)} overrides={len(KO_OVERRIDE)}")
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": "patch_fix3_ko.py",
        "tier": tier, "dry_run": dry_run, "keys": kmap,
        "ko_override": KO_OVERRIDE,
        "length_rule": "T01 机制：len(new utf-8) <= len(old utf-8)，超长用 KO_OVERRIDE 短译或 SKIP_TOO_LONG",
        "files": {}, "ok": True,
    }
    old_vals_all: dict[str, str] = {}
    for entry, label in TS_KO.items():
        p = work / entry
        if not p.is_file():
            report["files"][entry] = {"missing": True}
            report["ok"] = False
            print(f"[fix3-ko] MISSING {entry}")
            continue
        raw = p.read_bytes()
        # 记录旧 ko 值（verify 旧值残留用）
        import UnityPy
        env = UnityPy.load(raw)
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            text = _ta_text(obj.read())
            for line in text.split("\n"):
                sep = line.find(":")
                if sep > 0 and line[:sep] in kmap:
                    old_vals_all[line[:sep]] = line[sep + 1:]
        out, log = patch_textasset_keyed(raw, kmap)
        n = sum(x["changed_count"] for x in log)
        n_skip = sum(x["skipped_count"] for x in log)
        if n_skip:
            report["ok"] = False
        report["files"][entry] = {
            "label": label, "sha256_before": sha256(raw), "sha256_after": sha256(out),
            "changed": raw != out, "changed_count": n, "skipped_count": n_skip, "log": log,
        }
        print(f"[fix3-ko] {label} changed_lines={n} skipped={n_skip}")
        if not dry_run and raw != out:
            p.write_bytes(out)
    report["old_ko_values"] = old_vals_all
    report["changed_total"] = sum(v.get("changed_count", 0)
                                  for v in report["files"].values() if isinstance(v, dict))
    APPLY_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fix3-ko] report -> {APPLY_REPORT}")
    return 0 if report["ok"] else 1


def cmd_verify(work: Path, tier: str) -> int:
    entries = load_entries(tier)
    kmap = key_map(entries)
    old_vals = {}
    if APPLY_REPORT.is_file():
        old_vals = json.loads(APPLY_REPORT.read_text(encoding="utf-8")).get("old_ko_values", {})
    ok_all = True
    vreport = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "tool": "patch_fix3_ko.py verify", "files": {}}
    for entry, label in TS_KO.items():
        p = work / entry
        if not p.is_file():
            vreport["files"][label] = {"missing": True}
            ok_all = False
            print(f"[verify-ko] MISSING {label}")
            continue
        res = verify_textasset_ko(p.read_bytes(), kmap, old_vals)
        chk = res["checks"]
        vreport["files"][label] = res
        for name, c in chk.items():
            print(f"[verify-ko] {name}: keys={c['keys_found']} zh={c['zh_hits']} "
                  f"bad={len(c['bad'])} old_residual={c['old_value_residual_total']}")
        if not res["ok"]:
            ok_all = False
    vreport["ok"] = ok_all
    VERIFY_REPORT.write_text(json.dumps(vreport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify-ko] ok={ok_all} report -> {VERIFY_REPORT}")
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
