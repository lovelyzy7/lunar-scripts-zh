#!/usr/bin/env python3
"""Probe Octo list.bin with the standard library only (no protobuf dependency).

The schema comes from lunar-base/scripts/assetbundles/octo_pb2.py (generated from octo.proto):

  message Database { int32 revision = 1; repeated Data assetBundleList = 2;
                     repeated string tagname = 3; repeated Data resourceList = 4;
                     string urlFormat = 5; }
  message Data { int32 id = 1; string filepath = 2; string name = 3; int32 size = 4;
                 uint32 crc = 5; int32 priority = 6; repeated int32 tagId = 7;
                 repeated int32 dependencies = 8; State state = 9; string md5 = 10;
                 string objectName = 11; uint64 generation = 12; int32 uploadVersionId = 13; }

This script only reads. It is used by the E-deploy-cache analysis to verify:
  * the top-level revision/urlFormat embedded in the catalog,
  * that list.bin size/md5 still match the files on disk (the CDN enforces size+md5,
    see lunar-tear/server/internal/service/octo.go:409-426),
  * which text bundles exist and what object ids they map to.

Usage:
  python probe_listbin.py [--list-bin PATH] [--assets-root PATH] [--text-only]
                          [--check-md5 N] [--json OUT]
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

DEFAULT_LIST = r"E:\NieRReincarnation\lunar-tear\server\assets\revisions\0\list.bin"
DEFAULT_ROOT = r"E:\NieRReincarnation\lunar-tear\server\assets\revisions\0"


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
    raise ValueError("bad varint at offset %d" % start)


def iter_fields(buf, i, end):
    """Yield (field_number, wire_type, value, raw_start, raw_end)."""
    while i < end:
        start = i
        tag, i = read_varint(buf, i)
        field, wire = tag >> 3, tag & 7
        if wire == 0:
            value, i = read_varint(buf, i)
        elif wire == 1:
            value = buf[i:i + 8]
            i += 8
        elif wire == 2:
            ln, i = read_varint(buf, i)
            value = buf[i:i + ln]
            i += ln
        elif wire == 5:
            value = buf[i:i + 4]
            i += 4
        else:
            raise ValueError("unsupported wire type %d at %d" % (wire, start))
        yield field, wire, value, start, i


def parse_data(buf):
    d = {"id": None, "filepath": None, "name": None, "size": None, "crc": None,
         "priority": None, "tagId": [], "dependencies": [], "state": None,
         "md5": None, "objectName": None, "generation": None, "uploadVersionId": None}
    for field, wire, value, _s, _e in iter_fields(buf, 0, len(buf)):
        if field == 1 and wire == 0:
            d["id"] = value
        elif field == 2 and wire == 2:
            d["filepath"] = value.decode("utf-8", "replace")
        elif field == 3 and wire == 2:
            d["name"] = value.decode("utf-8", "replace")
        elif field == 4 and wire == 0:
            d["size"] = value
        elif field == 5 and wire == 0:
            d["crc"] = value
        elif field == 6 and wire == 0:
            d["priority"] = value
        elif field == 7 and wire == 0:
            d["tagId"].append(value)
        elif field == 8 and wire == 0:
            d["dependencies"].append(value)
        elif field == 9 and wire == 0:
            d["state"] = value
        elif field == 10 and wire == 2:
            d["md5"] = value.decode("utf-8", "replace")
        elif field == 11 and wire == 2:
            d["objectName"] = value.decode("utf-8", "replace")
        elif field == 12 and wire == 0:
            d["generation"] = value
        elif field == 13 and wire == 0:
            d["uploadVersionId"] = value
    return d


def parse_database(buf):
    db = {"revision": None, "urlFormat": None, "tagname": [],
          "assetBundleList": [], "resourceList": []}
    for field, wire, value, _s, _e in iter_fields(buf, 0, len(buf)):
        if field == 1 and wire == 0:
            db["revision"] = value
        elif field == 2 and wire == 2:
            db["assetBundleList"].append(parse_data(value))
        elif field == 3 and wire == 2:
            db["tagname"].append(value.decode("utf-8", "replace"))
        elif field == 4 and wire == 2:
            db["resourceList"].append(parse_data(value))
        elif field == 5 and wire == 2:
            db["urlFormat"] = value.decode("utf-8", "replace")
    return db


def filesystem_path(assets_root: Path, asset_type: str, name: str) -> Path:
    rel = name.replace(")", "/")
    if asset_type == "assetbundle":
        return assets_root / "assetbundle" / (rel + ".assetbundle")
    return assets_root / "resources" / rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-bin", default=DEFAULT_LIST)
    ap.add_argument("--assets-root", default=DEFAULT_ROOT)
    ap.add_argument("--text-only", action="store_true")
    ap.add_argument("--check-md5", type=int, default=20,
                    help="check the first N text bundles against disk (0 = none)")
    ap.add_argument("--bundle", action="append", default=[],
                    help="also check this exact bundle name (')' separators); repeatable")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    list_bin = Path(args.list_bin)
    root = Path(args.assets_root)
    buf = list_bin.read_bytes()
    db = parse_database(buf)

    out = {
        "list_bin": str(list_bin),
        "list_bin_size": len(buf),
        "list_bin_mtime_ns": list_bin.stat().st_mtime_ns,
        "revision": db["revision"],
        "urlFormat": db["urlFormat"],
        "tagname": db["tagname"][:10],
        "assetBundleList_count": len(db["assetBundleList"]),
        "resourceList_count": len(db["resourceList"]),
    }

    text = [e for e in db["assetBundleList"] if e["name"] and e["name"].startswith("text)")]
    out["text_bundle_count"] = len(text)

    def summarize(e):
        return {
            "name": e["name"], "size": e["size"], "md5": e["md5"], "crc": e["crc"],
            "objectName": e["objectName"], "generation": e["generation"],
            "state": e["state"], "dependencies": e["dependencies"],
        }

    out["text_bundle_samples"] = [summarize(e) for e in text[:5]]
    out["bundle_samples"] = [summarize(e) for e in db["assetBundleList"][:3]]
    out["resource_samples"] = [summarize(e) for e in db["resourceList"][:3]]

    checks = []
    by_name = {e["name"]: e for e in db["assetBundleList"] if e["name"]}
    targets = text[: args.check_md5] if args.check_md5 else []
    for name in args.bundle:
        e = by_name.get(name)
        if e is None:
            checks.append({"name": name, "error": "not found in list.bin"})
            continue
        targets.append(e)
    for e in targets:
        p = filesystem_path(root, "assetbundle", e["name"])
        rec = {"name": e["name"], "path": str(p), "exists": p.is_file(),
               "list_size": e["size"], "list_md5": e["md5"]}
        if p.is_file():
            data = p.read_bytes()
            rec["disk_size"] = len(data)
            rec["disk_md5"] = hashlib.md5(data).hexdigest()
            rec["size_match"] = rec["disk_size"] == e["size"]
            rec["md5_match"] = rec["disk_md5"] == e["md5"]
        checks.append(rec)
    out["text_bundle_disk_checks"] = checks

    text_out = json.dumps(out, ensure_ascii=False, indent=2)
    print(text_out)
    if args.json:
        Path(args.json).write_text(text_out + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
