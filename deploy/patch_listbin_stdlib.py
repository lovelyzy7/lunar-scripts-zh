#!/usr/bin/env python3
"""Patch size/md5 of selected Octo list.bin entries in place, standard library only.

Fallback for environments without `google.protobuf` (patch_listbin.py needs it). It
updates exactly the entries you name, in place, and refuses any edit that would change
the encoded length of the file:

  * `md5` (field 10, length-delimited): always 32 ASCII bytes, so it is overwritten
    byte-for-byte;
  * `size` (field 4, varint): only rewritten when the new value has the same varint
    length as the old one (translation changes are a few bytes; text bundles are
    1..4 KB = 2-byte varints). Otherwise the tool fails for that entry and tells you
    to use the protobuf path.
  * `crc` is deliberately NOT touched: the client never compares it (the public
    wrapper passes crc=0 to Unity; octo Data.crc is decorative -- see
    lunar-base/scripts/README.md:159-164 and patch_listbin.py:10-19) and the CDN
    does not use it either. It is left as the old value and reported as stale.

The file layout follows octo.proto as mirrored in
lunar-base/scripts/assetbundles/octo_pb2.py:

    message Database { int32 revision = 1; repeated Data assetBundleList = 2; ... }
    message Data { id=1 filepath=2 name=3 size=4 crc=5 priority=6 tagId=7 ...
                   md5=10 objectName=11 generation=12 uploadVersionId=13 }

Usage:
  # dry run against a list.bin copy: which entries would change / which fail
  python patch_listbin_stdlib.py --list-bin /work/list.bin --assets-root /work/revision0 \
      --names /work/changed.txt

  # apply (writes atomic tmp+replace; first run keeps list.bin.bak)
  python patch_listbin_stdlib.py ... --apply

`--names` is a UTF-8 text file with one list.bin name per line (`)` is the separator,
as in the catalog and in patch_listbin.py). Blank lines and `#` comments are skipped.
"""

import argparse
import hashlib
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
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def iter_fields(buf, start, end):
    """Yield dicts with field, wire, tag_start, value_start, value_end for one message."""
    i = start
    while i < end:
        tag_start = i
        tag, i = read_varint(buf, i)
        field, wire = tag >> 3, tag & 7
        value_start = i
        if wire == 0:
            _, i = read_varint(buf, i)
        elif wire == 1:
            i += 8
        elif wire == 2:
            length, i = read_varint(buf, i)
            value_start = i
            i += length
        elif wire == 5:
            i += 4
        else:
            raise ValueError("unsupported wire type %d at %d" % (wire, tag_start))
        yield {"field": field, "wire": wire, "tag_start": tag_start,
               "value_start": value_start, "value_end": i}


def parse_data(buf, start, end):
    """Parse one nested Octo.Data message; return dict with absolute offsets."""
    d = {"name": None, "size": None, "md5": None, "size_field": None, "md5_field": None}
    for f in iter_fields(buf, start, end):
        if f["field"] == 3 and f["wire"] == 2:
            d["name"] = bytes(buf[f["value_start"]:f["value_end"]]).decode("utf-8", "replace")
        elif f["field"] == 4 and f["wire"] == 0:
            d["size"], _ = read_varint(buf, f["value_start"])
            d["size_field"] = f
        elif f["field"] == 10 and f["wire"] == 2:
            d["md5"] = bytes(buf[f["value_start"]:f["value_end"]]).decode("ascii", "replace")
            d["md5_field"] = f
    return d


def scan_database(buf):
    """Return {name: parsed Data} for both assetBundleList and resourceList entries."""
    entries = {}
    dup = set()
    for f in iter_fields(buf, 0, len(buf)):
        if f["field"] in (2, 4) and f["wire"] == 2:
            d = parse_data(buf, f["value_start"], f["value_end"])
            if not d["name"]:
                continue
            if d["name"] in entries:
                dup.add(d["name"])
            entries[d["name"]] = d
    return entries, dup


def candidate_path(assets_root: Path, name: str) -> Path:
    rel = name.replace(")", "/")
    if ".." in rel or rel.startswith("/") or "\\" in rel:
        raise ValueError("unsafe bundle name: %r" % name)
    return assets_root / "assetbundle" / (rel + ".assetbundle")


def main():
    ap = argparse.ArgumentParser(description="In-place size/md5 patch for named Octo list.bin entries.")
    ap.add_argument("--list-bin", required=True)
    ap.add_argument("--assets-root", required=True,
                    help="revision root containing assetbundle/ (same layout as list.bin's parent)")
    ap.add_argument("--names", required=True, help="text file with one bundle name per line")
    ap.add_argument("--apply", action="store_true", help="write the file (default: dry run)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    list_path = Path(args.list_bin)
    root = Path(args.assets_root)
    buf = bytearray(list_path.read_bytes())
    entries, dup = scan_database(buf)

    wanted = []
    for line in Path(args.names).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            wanted.append(line)
    if not wanted:
        print("ERROR: no names in --names file", file=sys.stderr)
        return 2
    if len(set(wanted)) != len(wanted):
        print("ERROR: duplicate names in --names file", file=sys.stderr)
        return 2

    ops = []          # (start, end, new_bytes, name)
    report = {"list_bin": str(list_path), "assets_root": str(root),
              "requested": len(wanted), "unchanged": 0, "changed": 0,
              "apply": bool(args.apply), "entries": [], "errors": []}

    for name in wanted:
        rec = {"name": name}
        e = entries.get(name)
        if e is None:
            rec["error"] = "name not found in list.bin"
            report["errors"].append(rec)
            report["entries"].append(rec)
            continue
        if name in dup:
            rec["warning"] = "duplicate name in list.bin; all occurrences share this entry record"
        p = candidate_path(root, name)
        if not p.is_file():
            rec["error"] = "file missing on disk: %s" % p
            report["errors"].append(rec)
            report["entries"].append(rec)
            continue
        data = p.read_bytes()
        new_size, new_md5 = len(data), hashlib.md5(data).hexdigest()
        rec.update({"path": str(p), "disk_size": new_size, "disk_md5": new_md5,
                    "old_size": e["size"], "old_md5": e["md5"]})
        if e["size"] == new_size and e["md5"] == new_md5:
            rec["action"] = "unchanged"
            report["unchanged"] += 1
            report["entries"].append(rec)
            continue

        if e["md5_field"] is None or (e["md5_field"]["value_end"] - e["md5_field"]["value_start"]) != 32:
            rec["error"] = "md5 field absent or not a 32-byte string; use protobuf tool"
            report["errors"].append(rec)
            report["entries"].append(rec)
            continue
        encoded_size = encode_varint(new_size)
        if e["size_field"] is None:
            rec["error"] = "size field absent; use protobuf tool"
            report["errors"].append(rec)
            report["entries"].append(rec)
            continue
        old_size_len = e["size_field"]["value_end"] - e["size_field"]["value_start"]
        if len(encoded_size) != old_size_len:
            rec["error"] = ("size varint length would change %d -> %d bytes; use protobuf tool"
                            % (old_size_len, len(encoded_size)))
            report["errors"].append(rec)
            report["entries"].append(rec)
            continue

        rec["action"] = "patch"
        rec["crc_note"] = "crc left at old value (client and CDN never compare it)"
        report["changed"] += 1
        report["entries"].append(rec)
        ops.append((e["size_field"]["value_start"], e["size_field"]["value_end"], encoded_size, name))
        ops.append((e["md5_field"]["value_start"], e["md5_field"]["value_end"],
                    new_md5.encode("ascii"), name))

    if report["errors"]:
        report["ok"] = False
        report["written"] = False
        text = json.dumps(report, ensure_ascii=False, indent=2)
        print(text)
        if args.json:
            Path(args.json).write_text(text + "\n", encoding="utf-8")
        print("ERROR: %d entr(ies) cannot be patched in place; nothing written" % len(report["errors"]),
              file=sys.stderr)
        return 1

    if args.apply and ops:
        # all replacements have identical length, so offsets stay valid
        for start, end, new_bytes, name in ops:
            if len(new_bytes) != end - start:
                raise SystemExit("internal error: replacement length mismatch for %s" % name)
            buf[start:end] = new_bytes
        bak = list_path.with_suffix(list_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(list_path, bak)
        tmp = list_path.with_suffix(list_path.suffix + ".tmp")
        tmp.write_bytes(bytes(buf))
        os.replace(tmp, list_path)
        # read-back verification
        check_buf = bytearray(list_path.read_bytes())
        check_entries, _ = scan_database(check_buf)
        bad = []
        for rec in report["entries"]:
            if rec.get("action") != "patch":
                continue
            ce = check_entries.get(rec["name"])
            if (ce is None or ce["size"] != rec["disk_size"] or ce["md5"] != rec["disk_md5"]):
                bad.append(rec["name"])
        report["written"] = True
        report["verified"] = not bad and len(check_buf) == len(buf)
        report["verify_mismatches"] = bad
    else:
        report["written"] = False
        report["verified"] = None

    report["ok"] = not report["errors"] and (report.get("verified") is not False)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
