#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用差异包重建器 —— 提炼自 zh-l10n fix 系列（fix4..fixF）build_bundles 脚本。

把定稿 zh jsonl 的值写回 text/<lang> 文本包，输出**整树布局、仅差异包**：
  out_root/assetbundle/text/<lang>/<服务器相对路径>.assetbundle

规则（与 fixF_build_bundles 同规）：
  * 差异包 = changes.jsonl 涉及 (dir,bundle) 全集；
  * 全状态写入：受影响包内**所有**键都按 zh jsonl 写入（保证叠加部署一致）；
  * 回读校验：改键与 zh 一致 + 未改键与源一致；
  * 打包链 = probe_bundle_repack（UnityPy + lz4 + octo 对称加密，0x31/0x32 自适配）。

用法：
  python build_bundles.py --zh zh_new.jsonl --changes merged_changes.jsonl \
      --server-root <.../revisions/0/assetbundle/text/ja> --lang ja \
      --lunar-base <lunar-base 目录> --out-root <dir> [--report report.json]

红线：server-root 只读；只写 out-root 与 report。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # l10n/
try:
    import probe_bundle_repack as pbr
except ImportError:
    print("FATAL: probe_bundle_repack.py 须与本脚本同处 l10n/ 下（或在 sys.path）", file=sys.stderr)
    raise


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def line_key(line: str):
    s = line.strip()
    if not s or s.startswith("//"):
        return None
    sep = s.find(":")
    return s[:sep] if sep > 0 else None


def replace_all_lines(text: str, set_map: dict):
    trailing = text.endswith("\n")
    lines = text.split("\n")
    if trailing and lines and lines[-1] == "":
        lines = lines[:-1]
    changed = []
    for i, line in enumerate(lines):
        k = line_key(line)
        if k is not None and k in set_map:
            new_line = f"{k}:{set_map[k]}"
            if line != new_line:
                changed.append(k)
            lines[i] = new_line
    new_text = "\n".join(lines)
    if trailing:
        new_text += "\n"
    return new_text, changed


def main():
    ap = argparse.ArgumentParser(description="rebuild changed text bundles into a tree layout")
    ap.add_argument("--zh", required=True)
    ap.add_argument("--changes", required=True)
    ap.add_argument("--server-root", required=True)
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--lunar-base", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    server_root = Path(args.server_root).resolve()
    out_root = Path(args.out_root).resolve()
    lunar = Path(args.lunar_base).resolve()
    zh_rows = load_jsonl(Path(args.zh))
    changes = load_jsonl(Path(args.changes))

    # (bundle, asset) -> {key: zh}
    edits = {}
    want = set()
    for rec in changes:
        want.add((rec.get("bundle") or "", rec.get("asset") or ""))
        edits.setdefault(rec.get("bundle") or "", {}).setdefault(rec.get("asset") or "", {})[rec.get("key") or ""] = rec.get("new", rec.get("zh", ""))
    # 全状态：受影响包所有键以 zh jsonl 为准
    full = {}
    for rec in zh_rows:
        b, a = rec.get("bundle") or "", rec.get("asset") or ""
        if (b, a) in want:
            full.setdefault(b, {}).setdefault(a, {})[rec.get("key") or ""] = rec.get("zh", "")

    index = {}
    for path in server_root.rglob("*.assetbundle"):
        index.setdefault(path.name, []).append(path)

    report = {"bundles": [], "failures": [], "keys_written": 0, "readback_ok": 0}
    for (bname, asset) in sorted(want):
        cands = index.get(bname, [])
        if len(cands) != 1:
            report["failures"].append({"bundle": bname, "asset": asset, "reason": f"candidates={len(cands)}"})
            continue
        src = cands[0]
        rel = src.relative_to(server_root)
        original = src.read_bytes()
        decrypted, mask = pbr.decrypt_file(src, lunar)
        env, bundle_file = pbr.unitypy_env(decrypted)
        names = {getattr(d, "m_Name", None): (o, d) for o, d in pbr.text_assets_of(env)}
        if asset not in names:
            report["failures"].append({"bundle": bname, "asset": asset, "reason": "asset-not-found"})
            continue
        obj, data = names[asset]
        old_text = pbr._as_text(data.m_Script)
        old_kv = pbr.parse_key_values(old_text)
        set_map = full.get(bname, {}).get(asset, {})
        new_text, changed_keys = replace_all_lines(old_text, set_map)
        if not changed_keys and old_text == new_text:
            # 无实际字节差异也写（全状态一致性要求时可删）；此处保持源文件不落盘
            report["bundles"].append({"bundle": bname, "asset": asset, "rel": str(rel), "status": "noop"})
            continue
        data.m_Script = new_text.encode("utf-8") if isinstance(new_text, str) else new_text
        try:
            import UnityPy  # noqa: F401
            raw_new = bundle_file
            # UnityPy 环境内 save
            save_name = bundle_file.name if hasattr(bundle_file, "name") else "bundle"
            out_bytes = env.file.save() if hasattr(env.file, "save") else None
            if out_bytes is None:
                raise RuntimeError("env.file.save() unavailable")
            enc = pbr.encrypt_bytes(out_bytes, mask, lunar, original[0])
        except Exception as e:  # noqa: BLE001
            report["failures"].append({"bundle": bname, "asset": asset, "reason": f"pack:{e}"})
            continue
        out_path = out_root / "assetbundle" / "text" / args.lang / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(enc)
        # 回读
        dec2, _ = pbr.decrypt_file(out_path, lunar, mask_name=mask)
        env2, _ = pbr.unitypy_env(dec2)
        names2 = {getattr(d, "m_Name", None): (o, d) for o, d in pbr.text_assets_of(env2)}
        ok = False
        if asset in names2:
            text2 = pbr._as_text(names2[asset][1].m_Script)
            kv2 = pbr.parse_key_values(text2)
            ok = all(kv2.get(k) == v for k, v in set_map.items()) and all(
                kv2.get(k) == old_kv[k] for k in old_kv if k not in set_map
            )
        if ok:
            report["readback_ok"] += 1
        else:
            report["failures"].append({"bundle": bname, "asset": asset, "reason": "readback-mismatch"})
        report["keys_written"] += len(set_map)
        report["bundles"].append({"bundle": bname, "asset": asset, "rel": str(rel), "status": "ok" if ok else "bad",
                                  "sha256": hashlib.sha256(enc).hexdigest(), "size": len(enc)})

    print(json.dumps({
        "bundles": len(report["bundles"]), "keys_written": report["keys_written"],
        "readback_ok": report["readback_ok"], "failures": len(report["failures"]),
    }, ensure_ascii=False, indent=2))
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
