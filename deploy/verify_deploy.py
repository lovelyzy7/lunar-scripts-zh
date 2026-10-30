#!/usr/bin/env python3
"""Verify an Octo list.bin swap before/after deployment (stdlib only).

Checks performed:
  1. revision in the candidate list.bin is greater than in the baseline (deployment must
     bump it, otherwise the client keeps its cached list -- see E-deploy-cache.md);
  2. every assetbundle/resource entry added or changed between baseline and candidate
     matches the file that is actually on disk (size + md5). This is exactly what the
     lunar-tear CDN enforces before it serves a bundle
     (server/internal/service/octo.go:408-426), so this is a pre-flight for "server will
     return 404 / client will fail its md5 check";
  3. entries that did not change are untouched (count only).

Usage:
  python verify_deploy.py --old baseline/list.bin --new deployed/list.bin \
      --assets-root deployed/revision0 [--max-report 20] [--json out.json]

Exit codes: 0 pass, 1 verification failure, 2 input/parse error.
"""

import argparse
import hashlib
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_listbin import filesystem_path, parse_database  # noqa: E402


def index_entries(db):
    out = {}
    for kind, entries in (("assetbundle", db["assetBundleList"]), ("resources", db["resourceList"])):
        for e in entries:
            name = e["name"]
            if name:
                out[(kind, name)] = e
    return out


def main():
    ap = argparse.ArgumentParser(description="Verify list.bin swap + on-disk bundle hashes.")
    ap.add_argument("--old", required=True, help="baseline list.bin (backup / .bak)")
    ap.add_argument("--new", required=True, help="candidate list.bin to deploy")
    ap.add_argument("--assets-root", required=True,
                    help="directory containing assetbundle/ and resources/ (the revision-0 root)")
    ap.add_argument("--max-report", type=int, default=20)
    ap.add_argument("--no-revision-check", action="store_true",
                    help="skip the requirement that --new revision > --old (for entry-only checks)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    old_path, new_path = Path(args.old), Path(args.new)
    root = Path(args.assets_root)
    old_db = parse_database(old_path.read_bytes())
    new_db = parse_database(new_path.read_bytes())
    old_idx, new_idx = index_entries(old_db), index_entries(new_db)

    result = {
        "old_list_bin": str(old_path),
        "new_list_bin": str(new_path),
        "assets_root": str(root),
        "revision_old": old_db["revision"],
        "revision_new": new_db["revision"],
        "entries_old": len(old_idx),
        "entries_new": len(new_idx),
        "url_format_old": old_db["urlFormat"],
        "url_format_new": new_db["urlFormat"],
        "checks": {"changed": 0, "added": 0, "removed": 0, "unchanged": 0},
        "mismatches": [],
        "changed_samples": [],
    }
    problems = []

    if old_db["revision"] is None or new_db["revision"] is None:
        problems.append("revision field missing")
    elif not args.no_revision_check and new_db["revision"] <= old_db["revision"]:
        problems.append(
            "candidate revision %s is not greater than baseline %s (client would keep its cached list)"
            % (new_db["revision"], old_db["revision"])
        )
    if old_db["urlFormat"] != new_db["urlFormat"]:
        problems.append(
            "urlFormat changed; the CDN rewrites this fixed 43-byte string in memory "
            "(octo.go:441-466) -- keep it byte-identical"
        )

    changed_candidates = []
    for key, new_e in new_idx.items():
        old_e = old_idx.get(key)
        if old_e is None:
            result["checks"]["added"] += 1
            changed_candidates.append((key, old_e, new_e))
        elif (old_e["size"], old_e["md5"]) != (new_e["size"], new_e["md5"]):
            result["checks"]["changed"] += 1
            changed_candidates.append((key, old_e, new_e))
        else:
            result["checks"]["unchanged"] += 1
    for key in old_idx:
        if key not in new_idx:
            result["checks"]["removed"] += 1

    for (kind, name), old_e, new_e in changed_candidates:
        p = filesystem_path(root, kind, name)
        rec = {
            "kind": kind,
            "name": name,
            "list_size": new_e["size"],
            "list_md5": new_e["md5"],
            "path": str(p),
            "exists": p.is_file(),
        }
        if p.is_file():
            data = p.read_bytes()
            rec["disk_size"] = len(data)
            rec["disk_md5"] = hashlib.md5(data).hexdigest()
            rec["ok"] = rec["disk_size"] == new_e["size"] and rec["disk_md5"] == new_e["md5"]
        else:
            rec["ok"] = False
        if not rec["ok"]:
            result["mismatches"].append(rec)
        if len(result["changed_samples"]) < args.max_report:
            result["changed_samples"].append(rec)

    result["ok"] = not problems and not result["mismatches"]
    result["problems"] = problems

    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
