#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resource_dump-android-zh.7z 构建器 —— 2026-10-28 JP 最终打包所用流程的脚本化。

流程（原版 dump 一字节不动）：
  1) copy  原版 resource_dump_android.7z → 工作副本（sha256 双端核对）；
  2) stage 汉化件到 staging/upd/（镜像包内路径）：
       revisions/0/assetbundle/text/ja/**   ← 现网 text/ja 整树（--text-ja）
       revisions/0/assetbundle/ui/help/ja/**← 可选 help 树（--help-ja，原版/回滚态则与包内一致）
       revisions/0/list.bin                 ← 原版 list.bin 起步（从工作副本解出）→ 刷新条目
       release/20240404193219.bin.e         ← 汉化 bin.e（--bin-e）
  3) patch list.bin：lunar-base patch_listbin.py（protobuf，缺盘文件不动）→ bump --set --revision；
  4) 7z u 工作副本（**需要 7-Zip 22+**：32 位 7-Zip 9.x 对 14.9GB solid 包 update 会 Unknown Error）；
  5) verify：7z 列表条目 CRC32/size ↔ staging 文件逐一核对。

用法（工作目录任意，全部 IO 落 --work-dir）：
  python build_resource_pack.py \
    --original <resources/resource_dump_android.7z> \
    --out resource_dump-android-zh.7z \
    --text-ja <lunar-tear/.../assetbundle/text/ja> \
    --bin-e <bin_zh_final2.bin.e> \
    --help-ja <可选：原版 help/ja 树> \
    --patch-tool <lunar-base/scripts/assetbundles/patch_listbin.py> \
    --python <python 解释器（需 protobuf）> \
    --seven-zip <7z.exe 绝对路径（22+）> \
    --revision 829 --work-dir <staging> [--apply]
缺 --apply 时全程 dry-run（只演练、不写工作副本）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, cwd=None):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, errors="replace")
    if r.stdout:
        print(r.stdout[-2000:])
    if r.stderr:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def stage_tree(src: Path, dst: Path):
    n = 0
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="build resource_dump-android-zh.7z")
    ap.add_argument("--original", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text-ja", required=True)
    ap.add_argument("--bin-e", required=True)
    ap.add_argument("--help-ja", default=None)
    ap.add_argument("--patch-tool", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--seven-zip", required=True)
    ap.add_argument("--revision", type=int, default=None)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    original, out = Path(args.original).resolve(), Path(args.out).resolve()
    work = Path(args.work_dir).resolve()
    upd = work / "upd"
    report = {"steps": []}

    def step(name, **kw):
        report["steps"].append({"step": name, **kw})
        print(f"== {name} ==")

    if not args.apply:
        print("DRY-RUN（不写工作副本；加 --apply 落盘）")

    # 1) copy
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, out)
    h_orig, h_out = sha256_file(original), sha256_file(out)
    step("copy", original_sha256=h_orig, out_sha256=h_out, identical=h_orig == h_out)
    if h_orig != h_out:
        print("FATAL: 工作副本与原版不一致", file=sys.stderr)
        return 1

    # 2) stage
    if upd.exists():
        shutil.rmtree(upd)
    (upd / "revisions" / "0").mkdir(parents=True)
    n_text = stage_tree(Path(args.text_ja), upd / "revisions" / "0" / "assetbundle" / "text" / "ja")
    n_help = 0
    if args.help_ja:
        n_help = stage_tree(Path(args.help_ja), upd / "revisions" / "0" / "assetbundle" / "ui" / "help" / "ja")
    (upd / "release").mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.bin_e, upd / "release" / "20240404193219.bin.e")
    step("stage", text_ja_files=n_text, help_ja_files=n_help, bin_e_sha256=sha256_file(Path(args.bin_e)))

    # 3) list.bin：从工作副本解出原版 → patch → bump
    list_bin = upd / "revisions" / "0" / "list.bin"
    if not list_bin.exists():
        if run([args.seven_zip, "x", str(out), f"-o{upd}", "revisions\\0\\list.bin", "-y"]) != 0:
            return 1
    if args.apply:
        if run([args.python, args.patch_tool, str(list_bin)]) != 0:
            return 1
        if args.revision is not None:
            bump = work.parent / "deploy" / "bump_listbin_revision.py"
            if bump.exists():
                run([args.python, bump, "--list-bin", str(list_bin), "--set", str(args.revision)])
    step("list-bin", revision_target=args.revision, size=list_bin.stat().st_size)

    # 4) 7z u
    if args.apply:
        if run([args.seven_zip, "u", str(out), "revisions", "release", "-m0=LZMA2", "-mmt=on"], cwd=upd) != 0:
            return 1
    step("update", out=str(out), size=out.stat().st_size)

    # 5) verify（列表 CRC ↔ staging）
    proc = subprocess.run([args.seven_zip, "l", "-slt", str(out)], capture_output=True, text=True, errors="replace")
    entries, cur = {}, None
    for ln in proc.stdout.splitlines():
        if ln.startswith("Path = ") and ln[7:] != str(out):
            cur = ln[7:]
            entries[cur] = {}
        elif cur and ln.startswith("Size = "):
            entries[cur]["size"] = int(ln[7:])
        elif cur and ln.startswith("CRC = "):
            entries[cur]["crc"] = ln[6:].upper()
    import binascii

    def crc32(p: Path):
        with p.open("rb") as f:
            return f.read()

    mism = []
    checked = 0
    for base, prefix in ((upd / "revisions" / "0" / "assetbundle" / "text" / "ja", "revisions\\0\\assetbundle\\text\\ja"),
                         (upd / "revisions" / "0" / "assetbundle" / "ui" / "help" / "ja", "revisions\\0\\assetbundle\\ui\\help\\ja"),
                         (upd / "release", "release")):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = str(p.relative_to(base)).replace("/", "\\")
            key = f"{prefix}\\{rel}"
            data = crc32(p)
            e = entries.get(key)
            checked += 1
            if not e or e.get("size") != len(data) or e.get("crc") != f"{binascii.crc32(data) & 0xFFFFFFFF:08X}":
                mism.append(key)
    step("verify", entries_checked=checked, mismatches=mism[:20], ok=not mism)

    (work / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2)[:4000])
    return 0 if not mism else 1


if __name__ == "__main__":
    sys.exit(main())
