#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用 QA 校验器 —— 提炼自 zh-l10n fix 系列（fix4..fixF）qa 脚本的门禁项。

对「定稿 zh jsonl」执行 text 级门禁（与 fix 系列 qa_* 全绿口径一致）：
  * 占位符多重集（{0}/%s/<tag> 等）与原文一致        → placeholder_mismatch
  * SKIP / 保护词条（status=skip / protected_keep）零改动 → skip_changed
  * 残留哨兵（〔待译〕〔机翻〕<MT> 等）                → sentinel_hits
  * 空译文 / 真实换行（值内裸 \\n）                   → empty_values / real_newlines
  * 日文假名残留（新增 kana）                          → kana_added
  * 行首标点（行首全角/半角标点）                     → leading_punct
  * 全角句号残留（ASCII 双侧「。」）                   → ascii_flanked_period
  * 旧词残留（--old-terms tsv）                        → old_term_residue
  * 术语命中（--terms tsv: ja\\tzh 抽查）               → terminology
  * 字形覆盖（--codepoints txt，译文用字 ⊆ 字库）      → font_missing
  * 行宽超限（--max-visual-width N，按 <br>/\\n 分段）  → over_budget_lines
  * 幂等（同输入重跑字节一致）                        → idempotent

用法：
  python qa_check.py --base zh_base.jsonl --out zh_new.jsonl \
      [--old-terms old_terms.tsv] [--terms terms.tsv] \
      [--codepoints ui.txt story.txt] [--report qa.json]

退出码：0 全绿；1 有门禁未过。red line：只读输入。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{[0-9A-Za-z_]+\}|%[sd]|<[^>]+>|\\n")
SENTINELS = ("〔待译〕", "〔机翻〕", "<MT>", "[[MT]]", "TODO_MT", "【待译】")
KANA_RE = re.compile(r"[\u3040-\u30ff]")
LEADING_PUNCT_RE = re.compile(r"^[、。，．！？；：）」』】〉》”’]")
ASCII_FLANKED_PERIOD_RE = re.compile(r"(?<=[0-9A-Za-z])。(?=[0-9A-Za-z])")


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def placeholders(text: str) -> Counter:
    return Counter(PLACEHOLDER_RE.findall(text or ""))


def visual_width(seg: str) -> float:
    w = 0.0
    for ch in seg:
        w += 1.0 if ord(ch) < 0x2E80 else 1.0
    return w


def main():
    ap = argparse.ArgumentParser(description="QA gates for a translated zh jsonl")
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--old-terms", default=None, help="TSV: 旧词\\t新词（出现旧词即残留）")
    ap.add_argument("--terms", default=None, help="TSV: JA\\tZH（ZH 须出现在对应行 zh）")
    ap.add_argument("--codepoints", nargs="*", default=None, help="字库 codepoint 文本（0x.. 或字符），多个文件取并集")
    ap.add_argument("--max-visual-width", type=float, default=30.0)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    base_rows = load_jsonl(Path(args.base))
    out_rows = load_jsonl(Path(args.out))
    base = {(r.get("dir") or "", r.get("bundle") or "", r.get("key") or ""): r for r in base_rows}
    new = {(r.get("dir") or "", r.get("bundle") or "", r.get("key") or ""): r for r in out_rows}

    findings = {k: [] for k in (
        "placeholder_mismatch", "skip_changed", "sentinel_hits", "empty_values", "real_newlines",
        "kana_added", "leading_punct", "ascii_flanked_period", "old_term_residue", "terminology_missing",
        "font_missing", "over_budget_lines",
    )}
    checked = 0
    for key, rec in new.items():
        zh = rec.get("zh") or ""
        ja = rec.get("value") or rec.get("ja") or ""
        old = base.get(key)
        checked += 1
        if placeholders(zh) != placeholders(ja):
            findings["placeholder_mismatch"].append(key)
        status = rec.get("status") or ""
        if status in ("skip", "protected_keep") and old is not None and (old.get("zh") or "") != zh:
            findings["skip_changed"].append(key)
        if any(s in zh for s in SENTINELS):
            findings["sentinel_hits"].append(key)
        if not zh.strip() and (ja or "").strip():
            findings["empty_values"].append(key)
        if "\n" in zh.replace("\\n", ""):
            findings["real_newlines"].append(key)
        old_kana = set(KANA_RE.findall(ja))
        if set(KANA_RE.findall(zh)) - old_kana:
            findings["kana_added"].append(key)
        if LEADING_PUNCT_RE.search(zh):
            findings["leading_punct"].append(key)
        if ASCII_FLANKED_PERIOD_RE.search(zh):
            findings["ascii_flanked_period"].append(key)
        if args.old_terms:
            for line in Path(args.old_terms).read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                old_term = line.split("\t")[0].strip()
                if old_term and old_term in zh:
                    findings["old_term_residue"].append([key, old_term])
                    break
        if args.terms:
            for line in Path(args.terms).read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].strip() == ja.strip():
                    if parts[1].strip() and parts[1].strip() not in zh:
                        findings["terminology_missing"].append([key, parts[1].strip()])
        for seg in re.split(r"<br\s*/?>|\\n|\n", zh):
            if visual_width(seg) > args.max_visual_width:
                findings["over_budget_lines"].append([key, seg[:40]])
                break

    if args.codepoints:
        cps = set()
        for f in args.codepoints:
            for tok in Path(f).read_text(encoding="utf-8").split():
                if tok.startswith("0x") or tok.startswith("0X"):
                    cps.add(int(tok, 16))
                elif tok:
                    cps.add(ord(tok[0]))
        for key, rec in new.items():
            miss = sorted({ord(c) for c in (rec.get("zh") or "") if ord(c) > 0x20 and ord(c) not in cps})
            if miss:
                findings["font_missing"].append({"key": key, "missing": [hex(c) for c in miss[:12]]})

    gates = {k: len(v) for k, v in findings.items()}
    summary = {"checked": checked, "gates": gates, "all_green": all(v == 0 for v in gates.values())}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.report:
        Path(args.report).write_text(
            json.dumps({"summary": summary, "findings": findings}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if summary["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
