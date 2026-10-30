#!/usr/bin/env python3
# =====================================================================
# 【归档副本 ARCHIVE】2026-10-29 归档
# 来源：E:\NieRReincarnation\zh-l10n\work\deploy\patch_listbin_named.py
# 内容与来源一致（仅本头部注释为归档时添加，正文未改动）。
# EN 文本批部署用 named 版 list.bin patcher（按 staging 树文件名匹配条目；
# 与 deploy/patch_listbin_stdlib.py 的差异与用法见同目录 README-EN.md）。
# =====================================================================
"""Named-entry list.bin patcher (protobuf path; needs google.protobuf + octo_pb2).

Updates size/md5 (+crc=0, like the official patch_listbin.py) only for the entries whose
assetbundle files are present in a staged tree. Unlike scanning the whole 19.5 GiB asset
tree, it hashes only the staged files (a few MB) and rewrites list.bin once.

Usage:
  python patch_listbin_named.py --list-bin <live list.bin> \
      --staging-root <bundles_ja tree shaped assetbundle/text/ja/...> \
      --assets-root <live revisions/0> [--apply] [--json out.json]

Without --apply it reports what would change and verifies that every staged file maps to
an existing list.bin entry and that the live file currently matches the entry's old
size/md5 (baseline consistency). With --apply it writes atomically (tmp + rename) and
keeps list.bin.bak if none exists, then reloads and verifies the new values.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"E:\NieRReincarnation\lunar-base\scripts\assetbundles")
import octo_pb2  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def name_from_rel(rel: str) -> str:
    if not rel.endswith(".assetbundle"):
        raise ValueError("not an assetbundle: %s" % rel)
    stem = rel[: -len(".assetbundle")]
    if stem.startswith("assetbundle/"):
        stem = stem[len("assetbundle/"):]
    return stem.replace("/", ")")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-bin", required=True)
    ap.add_argument("--staging-root", required=True)
    ap.add_argument("--assets-root", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    list_path = Path(args.list_bin)
    staging = Path(args.staging_root)
    assets_root = Path(args.assets_root)

    db = octo_pb2.Database()
    db.ParseFromString(list_path.read_bytes())
    revision_before = db.revision
    entries = {e.name: e for e in db.assetBundleList if e.name}

    staged = sorted(p for p in staging.rglob("*") if p.is_file())
    report = {
        "list_bin": str(list_path),
        "revision_before": revision_before,
        "staged_files": len(staged),
        "matched": 0, "changed": 0, "unchanged": 0,
        "missing_entries": [], "live_baseline_mismatch": [], "errors": [],
        "apply": bool(args.apply),
        "total_old_size": 0, "total_new_size": 0,
    }
    todo = []
    for p in staged:
        rel = p.relative_to(staging).as_posix()
        try:
            name = name_from_rel(rel)
        except ValueError as exc:
            report["errors"].append({"file": rel, "error": str(exc)})
            continue
        e = entries.get(name)
        if e is None:
            report["missing_entries"].append({"file": rel, "name": name})
            continue
        report["matched"] += 1
        live = assets_root / rel
        if not live.is_file():
            report["errors"].append({"file": rel, "error": "live file missing"})
            continue
        live_md5, live_size = md5_file(live), live.stat().st_size
        report["total_old_size"] += e.size
        if live_md5 != e.md5 or live_size != e.size:
            report["live_baseline_mismatch"].append({
                "name": name, "list_md5": e.md5, "list_size": e.size,
                "live_md5": live_md5, "live_size": live_size,
            })
        new_md5, new_size = md5_file(p), p.stat().st_size
        report["total_new_size"] += new_size
        if new_md5 == e.md5 and new_size == e.size:
            report["unchanged"] += 1
            continue
        report["changed"] += 1
        todo.append((name, e, new_size, new_md5))

    report["ok_to_apply"] = (
        not report["errors"] and not report["missing_entries"]
        and not report["live_baseline_mismatch"]
    )

    if args.apply:
        if not report["ok_to_apply"]:
            report["written"] = False
            report["ok"] = False
            text = json.dumps(report, ensure_ascii=False, indent=2)
            print(text)
            if args.json:
                Path(args.json).write_text(text + "\n", encoding="utf-8")
            print("ERROR: preconditions failed; nothing written", file=sys.stderr)
            return 1
        for name, e, new_size, new_md5 in todo:
            e.size = new_size
            e.md5 = new_md5
            e.crc = 0
        bytes_before = list_path.stat().st_size
        data = db.SerializeToString()
        bak = list_path.with_suffix(list_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(list_path, bak)
        tmp = list_path.with_suffix(list_path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, list_path)
        # read-back verification
        check = octo_pb2.Database()
        check.ParseFromString(list_path.read_bytes())
        check_entries = {e.name: e for e in check.assetBundleList if e.name}
        bad = []
        for name, _e, new_size, new_md5 in todo:
            ce = check_entries.get(name)
            if ce is None or ce.size != new_size or ce.md5 != new_md5:
                bad.append(name)
        report["written"] = True
        report["size_before"] = bytes_before
        report["bytes_after"] = len(data)
        report["revision_after"] = check.revision
        report["verify_mismatches"] = bad
        report["verified"] = not bad and check.revision == revision_before
        report["ok"] = report["verified"]
    else:
        report["written"] = False
        report["errors"] += []
        report["ok"] = report["ok_to_apply"]

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
