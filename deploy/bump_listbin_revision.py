#!/usr/bin/env python3
"""Bump the revision stored at field 1 of an Octo list.bin, in place (stdlib only).

Why this exists
---------------
The client keeps a local asset-list database ("pdb") and compares its stored revision
with the revision embedded in the list.bin it downloads at startup. The JP client asks
`GET /v1/list/<gameId>/<localRevision>` and the lunar-tear CDN always answers with
`assets/revisions/0/list.bin` unchanged, whatever revision was asked. If the revision in
that file is not changed, the client keeps its old list (old md5 values) and keeps
serving already-cached bundles, so a translated bundle does not replace the old text on
screen. Bumping this revision makes the client replace its list database and then fetch
the bundles whose md5 changed.

Wire format (from lunar-base/scripts/assetbundles/octo_pb2.py, octo.proto)
--------------------------------------------------------------------------
    message Database { int32 revision = 1; repeated Data assetBundleList = 2; ... }
A revision below 16384 is a two-byte varint, so the current baseline (817 = `b1 06`)
can be rewritten to 818 (`b2 06`) without changing the file length or any offset.
This script refuses any change whose varint length would differ: use protobuf
(patch_listbin.py's octo_pb2) for that case.

Usage
-----
    # dry run: show current revision and what would be written
    python bump_listbin_revision.py --list-bin path/to/list.bin

    # write 818 (keeps a .bak of the first run, atomic tmp+replace)
    python bump_listbin_revision.py --list-bin path/to/list.bin --set 818

    # convenience: current + 1
    python bump_listbin_revision.py --list-bin path/to/list.bin --bump

Exit codes: 0 ok, 1 error (nothing written on error).
"""

import argparse
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from pathlib import Path


def read_varint(buf, i):
    value = 0
    shift = 0
    start = i
    while i < len(buf) and i - start < 10:
        b = buf[i]
        value |= (b & 0x7F) << shift
        i += 1
        if not (b & 0x80):
            return value, i
        shift += 7
    raise ValueError("bad varint at %d" % start)


def encode_varint(value):
    if value < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def find_revision(buf):
    """Return (value, value_start, value_end) for top-level field 1 (varint)."""
    i = 0
    while i < len(buf):
        tag_start = i
        tag, i = read_varint(buf, i)
        field, wire = tag >> 3, tag & 7
        if wire == 0:
            value_start = i
            value, i = read_varint(buf, i)
            if field == 1:
                return value, value_start, i
        elif wire == 1:
            i += 8
        elif wire == 2:
            length, i = read_varint(buf, i)
            i += length
        elif wire == 5:
            i += 4
        else:
            raise ValueError("unsupported wire type %d at %d" % (wire, tag_start))
    raise ValueError("top-level field 1 (revision) not found")


def main():
    ap = argparse.ArgumentParser(description="Bump the revision field of an Octo list.bin in place.")
    ap.add_argument("--list-bin", required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--set", type=int, help="new revision value")
    g.add_argument("--bump", action="store_true", help="current revision + 1")
    ap.add_argument("--dry-run", action="store_true", help="do not write (default when --set/--bump absent)")
    args = ap.parse_args()

    path = Path(args.list_bin)
    buf = bytearray(path.read_bytes())
    current, start, end = find_revision(buf)
    old_len = end - start

    if args.set is not None:
        target = args.set
    elif args.bump:
        target = current + 1
    else:
        target = None

    result = {
        "list_bin": str(path),
        "size_before": len(buf),
        "revision_current": current,
        "revision_bytes": buf[start:end].hex(),
        "revision_target": target,
    }
    if target is None:
        result["written"] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if target <= current:
        print("ERROR: target revision %d must be greater than current %d" % (target, current), file=sys.stderr)
        return 1
    encoded = encode_varint(target)
    if len(encoded) != old_len:
        print(
            "ERROR: varint length would change %d -> %d bytes (current=%d target=%d); "
            "rewrite with protobuf (octo_pb2) instead" % (old_len, len(encoded), current, target),
            file=sys.stderr,
        )
        return 1
    result["revision_encoded"] = encoded.hex()
    result["size_after"] = len(buf)

    if args.dry_run:
        result["written"] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    buf[start:end] = encoded
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(bytes(buf))
    os.replace(tmp, path)

    # verify the write by re-reading through the same parser
    check, cstart, cend = find_revision(bytearray(path.read_bytes()))
    result["revision_after"] = check
    result["verified"] = check == target and (cend - cstart) == old_len
    result["written"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
