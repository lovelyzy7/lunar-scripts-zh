#!/usr/bin/env python3
"""把 octo 文本资源包（assetbundle/text/<lang>/**）导出成 JSONL。

输出每行一个条目：
    {"lang": "ja", "dir": "ui", "bundle": "ui_0130310.assetbundle",
     "asset": "<TextAsset 名>", "line": 12, "key": "...", "value": "..."}

- 保留原始行号（line，0 基），便于回填时按行定位；
- key 按"首个冒号"切分；无冒号行（续行）、注释、空行不产出记录，
  但 line 字段来自原始文本行序，供回填器参考；
- 用 lunar-base 的读取器（extract_names.py）解密 + 解包 + 解析 UnityFS/SerializedFile。

用法（Windows）:
    E:\\NieRReincarnation\\lunar-base\\.venv\\Scripts\\python.exe dump_text.py --lang ja --out work/text_ja.jsonl
    ... --lang en --out work/text_en.jsonl
    ... --lang ko --out work/text_ko.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LUNAR_BASE = Path(r"E:\NieRReincarnation\lunar-base")
DEFAULT_TEXT_ROOT = Path(
    r"E:\NieRReincarnation\lunar-tear\server\assets\revisions\0\assetbundle\text"
)

sys.path.insert(0, str(LUNAR_BASE / "tools"))
import extract_names as xn  # noqa: E402


def mask_for(lang: str, relative: Path) -> str:
    """与 lunar-base/scripts/assetbundles/assetbundle_crypt.py 的 derive_mask_name 等价。"""
    rel = relative.as_posix()
    if rel.endswith(".assetbundle"):
        rel = rel[: -len(".assetbundle")]
    parts = ["text", lang, *rel.split("/")]
    return ")".join(parts)


def iter_entries(text: str):
    """按原始行序产出 (line_no, key, value)；跳过注释/空行/无冒号行。"""
    for line_no, raw in enumerate(text.replace("\r\n", "\n").split("\n")):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        sep = line.find(":")
        if sep <= 0:
            continue
        yield line_no, line[:sep], line[sep + 1 :]


def main() -> int:
    ap = argparse.ArgumentParser(description="Dump octo text bundles to JSONL")
    ap.add_argument("--lang", required=True, choices=["ja", "en", "ko"])
    ap.add_argument("--text-root", type=Path, default=DEFAULT_TEXT_ROOT)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个包（调试用）")
    args = ap.parse_args()

    root = args.text_root / args.lang
    if not root.is_dir():
        raise SystemExit(f"text root not found: {root}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(root.rglob("*.assetbundle"))
    if args.limit:
        files = files[: args.limit]

    total_entries = 0
    failed: list[str] = []
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        for i, path in enumerate(files, 1):
            rel = path.relative_to(root)
            lang = args.lang
            try:
                data = path.read_bytes()
                decrypted = xn.decrypt_text_bundle(data, mask_for(lang, rel))
                if not decrypted.startswith(b"UnityFS"):
                    raise ValueError("not a UnityFS bundle after decrypt")
                streams = xn.extract_bundle_streams(decrypted)
                assets = []
                for stream in streams:
                    assets.extend(xn.extract_text_assets(stream))
                if not assets:
                    raise ValueError("no TextAsset found")
                for asset_name, text in assets:
                    for line_no, key, value in iter_entries(text):
                        record = {
                            "lang": lang,
                            "dir": rel.parts[0] if len(rel.parts) > 1 else "",
                            "bundle": rel.name,
                            "asset": asset_name,
                            "line": line_no,
                            "key": key,
                            "value": value,
                        }
                        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                        total_entries += 1
            except Exception as exc:  # noqa: BLE001 - 记录失败包后继续
                failed.append(f"{rel.as_posix()}: {exc}")

            if i % 500 == 0 or i == len(files):
                print(
                    f"[{lang}] {i}/{len(files)} bundles, {total_entries} entries, "
                    f"{len(failed)} failed",
                    flush=True,
                )

    if failed:
        fail_path = args.out.with_suffix(".failed.txt")
        fail_path.write_text("\n".join(failed) + "\n", encoding="utf-8")
        print(f"failed bundles written to {fail_path}", flush=True)
    print(f"done: {total_entries} entries -> {args.out}", flush=True)
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
