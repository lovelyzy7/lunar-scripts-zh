#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用 fix 批次应用器 —— 提炼自 zh-l10n fix 系列（fix5..fix15 / fixA / fixF）apply 脚本。

把「翻译定稿 jsonl」+「若干批 changes.jsonl」合成为新的定稿 jsonl：
  * 匹配层级（与 fixF_apply 同规）：
      L1 current[(dir,bundle,key)].zh == old          精确命中
      L2 基线行中按键 + old 全行命中（old 指向基线原值）
      L3 按 (dir,bundle,key) 强置（冲突处置按 --priority，日志单列）
  * 冲突处置：同键多批改动按命令行顺序后写覆盖，或用 --priority b,c,a 指定批次优先；
  * 可选名字词典回填（--name-dictionary dict.json）：longest-first 单遍替换、
    预算 = JA 出现次数、不回扫已输出区（fix12_apply 层1 同规）；
  * 可选规则终扫（--sweep rule.json：[{pattern,replacement}]，正则）。
  * 幂等：对同一 base+changes 重跑字节一致。

用法：
  python apply_changes.py --base zh_base.jsonl \
      --changes a_changes.jsonl b_changes.jsonl \
      --out zh_new.jsonl --out-changes merged_changes.jsonl \
      [--name-dictionary name_dictionary.json] [--sweep sweep_rules.json] [--priority b,a]

行尾 CRLF（与 fix11+ 代际一致）。red line：只读输入、只写 out*。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MISSION_RE = re.compile(r"^(?:mission|report\.mission)\.name\.")


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def dump_jsonl(p: Path, rows) -> str:
    data = "".join(json.dumps(r, ensure_ascii=False) + "\r\n" for r in rows).encode("utf-8")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def k3(rec) -> tuple:
    return (rec.get("dir") or "", rec.get("bundle") or "", rec.get("key") or "")


def name_backfill(key: str, ja: str, zh: str, by_ja) -> tuple[str, list]:
    """名字词典回填（fix12 层1）：JA 名前提、zh 已含则跳过、单遍最长优先、预算=JA 次数。"""
    if not MISSION_RE.match(key) or not zh:
        return zh, []
    applied = []
    budgets = {}
    for ja_name, lst in by_ja.items():
        if ja_name not in ja or ja_name in zh:
            continue
        budgets[ja_name] = ja.count(ja_name)
    out = []
    i = 0
    while i < len(zh):
        hit = None
        for mt_name, ja_name, src in by_ja_flat:
            if mt_name and zh.startswith(mt_name, i) and budgets.get(ja_name, 0) > 0:
                if hit is None or len(mt_name) > len(hit[0]):
                    hit = (mt_name, ja_name, src)
        if hit:
            mt_name, ja_name, src = hit
            out.append(ja_name)
            budgets[ja_name] -= 1
            applied.append({"mt": mt_name, "ja": ja_name, "source": src})
            i += len(mt_name)
        else:
            out.append(zh[i])
            i += 1
    return "".join(out), applied


by_ja_flat: list = []  # 由 build_name_pairs 填充


def build_name_pairs(dict_path: Path):
    global by_ja_flat
    doc = json.loads(dict_path.read_text(encoding="utf-8"))
    pairs = [(p["ja_name"], p["mt_name"], p.get("source", "")) for p in doc.get("backfill_pairs", [])]
    # flat (mt, ja, source) 最长 mt 优先
    by_ja_flat = sorted(((mt, ja, src) for ja, mt, src in pairs), key=lambda t: (-len(t[0]), t[0]))
    by_ja = defaultdict(list)
    for ja, mt, src in pairs:
        by_ja[ja].append((mt, src))
    return by_ja


def apply_batches(base_rows, batches, priority, name_dict_path, sweep_rules):
    """batches: list of (name, [change rows])。返回 (out_rows, merged_changes, stats)。"""
    idx = {k3(r): r for r in base_rows}
    base_by_key = defaultdict(list)
    for r in base_rows:
        base_by_key[(r.get("key") or "")].append(r)

    order = {name: i for i, name in enumerate(reversed(priority))} if priority else {}
    # 收集同键多批：按 priority（后写覆盖），无 priority 时按命令行顺序后写优先
    pending = defaultdict(list)  # k3 -> [(batch_name, change)]
    for name, rows in batches:
        for ch in rows:
            pending[k3(ch)].append((name, ch))

    by_ja = build_name_pairs(name_dict_path) if name_dict_path else None

    stats = {"L1": 0, "L2": 0, "L3": 0, "name_backfill_rows": 0, "name_subs": 0, "sweep": 0}
    merged = []
    out_rows = [dict(r) for r in base_rows]
    out_idx = {k3(r): r for r in out_rows}

    for key, cand in pending.items():
        if priority:
            cand = sorted(cand, key=lambda t: order.get(t[0], 0))
        batch_name, ch = cand[-1]  # 后写/高优先胜出
        old, new = ch.get("old"), ch.get("new")
        cur = out_idx.get(key)
        level = None
        if cur is not None and cur.get("zh") == old:
            level = "L1"
        else:
            for r in base_by_key.get((key[2] or ""), []):
                if (r.get("zh") == old) and cur is None:
                    level = "L2"
                    cur = r
                    break
            if level is None and key in out_idx:
                level = "L3"
                cur = out_idx[key]
        if level is None or cur is None:
            continue
        stats[level] += 1
        cur["zh"] = new
        if "status" in ch:
            cur["status"] = ch["status"]
        if "provider" in ch:
            cur["provider"] = ch["provider"]
        subs = []
        if by_ja is not None:
            before = cur["zh"]
            cur["zh"], subs = name_backfill(key, cur.get("value") or cur.get("ja") or "", cur["zh"], by_ja)
            if subs:
                stats["name_backfill_rows"] += 1
                stats["name_subs"] += len(subs)
        merged.append({
            "dir": key[0], "bundle": key[1], "key": key[2],
            "old": old, "new": cur["zh"], "via_batch": batch_name, "level": level,
            "name_subs": subs,
        })

    if sweep_rules:
        rules = json.loads(Path(sweep_rules).read_text(encoding="utf-8"))
        for r in out_rows:
            zh = r.get("zh") or ""
            new = zh
            for rule in rules:
                new = re.sub(rule["pattern"], rule["replacement"], new)
            if new != zh:
                r["zh"] = new
                stats["sweep"] += 1
                merged.append({
                    "dir": r.get("dir") or "", "bundle": r.get("bundle") or "",
                    "key": r.get("key") or "", "old": zh, "new": new,
                    "via_batch": "sweep", "level": "sweep", "name_subs": [],
                })
    return out_rows, merged, stats


def main():
    ap = argparse.ArgumentParser(description="apply translation fix batches onto a zh jsonl")
    ap.add_argument("--base", required=True)
    ap.add_argument("--changes", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-changes", default=None)
    ap.add_argument("--name-dictionary", default=None)
    ap.add_argument("--sweep", default=None)
    ap.add_argument("--priority", default=None, help="逗号分隔批次名优先级（高→低）；缺省按命令行顺序后写优先")
    args = ap.parse_args()

    base_rows = load_jsonl(Path(args.base))
    batches = [(Path(c).stem, load_jsonl(Path(c))) for c in args.changes]
    priority = [x.strip() for x in args.priority.split(",")] if args.priority else None
    name_dict = Path(args.name_dictionary) if args.name_dictionary else None

    out_rows, merged, stats = apply_batches(base_rows, batches, priority, name_dict, args.sweep)
    h_rows = dump_jsonl(Path(args.out), out_rows)
    h_chg = dump_jsonl(Path(args.out_changes), merged) if args.out_changes else None
    summary = {
        "base_rows": len(base_rows), "out_rows": len(out_rows), "merged_changes": len(merged),
        "levels": {k: stats[k] for k in ("L1", "L2", "L3")},
        "name_backfill_rows": stats["name_backfill_rows"], "name_subs": stats["name_subs"],
        "sweep_rows": stats["sweep"],
        "out_sha256": h_rows, "out_changes_sha256": h_chg,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
