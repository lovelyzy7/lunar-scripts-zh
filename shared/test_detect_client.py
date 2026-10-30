#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_detect_client.py — 客户端自动识别正反例自测（L3a）。

正例：JP APK → region=jp；EN APK → region=en（三元组全对、key/产物名分派对）。
反例（全部必须 fail-fast，不产出任何文件）：
  N1  改 1 字节（文件中部任意资产）→ sha256 变 → 三元组断言拒建；
  N2  改 1 字节（AndroidManifest.xml 字符串池内）→ 包名判定失败/三元组拒建；
  N3  EN 包喂 jp 流水线（--expect jp）→ region 矛盾即拒；
  N4  JP 包喂 en 流水线（--expect en）→ region 矛盾即拒；
  N5  未知客户端（非 NieR APK / 空文件）→ 未知包名拒建。

用法：
  python shared/test_detect_client.py --jp <JP.apk> --en <EN.apk> --work <tmp目录> [--out report.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import detect_client as D  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def tamper_copy(src: Path, dst: Path, offset: int, xor: int = 0x01) -> dict:
    """复制 src 到 dst 并在 offset 处翻转 1 个字节（返回篡改事实）。"""
    data = bytearray(src.read_bytes())
    before = data[offset]
    data[offset] = before ^ xor
    dst.write_bytes(bytes(data))
    return {"path": str(dst), "offset": offset,
            "byte_before": before, "byte_after": data[offset]}


def expect_fail(name: str, fn) -> dict:
    try:
        fn()
    except SystemExit as exc:
        msg = str(exc)
        return {"case": name, "expect": "fail-fast", "got": "SystemExit",
                "message": msg[:300], "ok": True}
    return {"case": name, "expect": "fail-fast", "got": "NO-EXIT", "ok": False}


def expect_ok(name: str, fn, check) -> dict:
    try:
        info = fn()
    except SystemExit as exc:
        return {"case": name, "expect": "detect-ok", "got": f"SystemExit: {exc}",
                "ok": False}
    problems = check(info)
    return {"case": name, "expect": "detect-ok", "got": {
        "region": info["region"], "package": info["detected"]["package"],
        "product_name": info["product_name"], "keystore": info["keystore"],
    }, "ok": not problems, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jp", required=True, help="原版 JP APK")
    ap.add_argument("--en", required=True, help="原版 EN APK")
    ap.add_argument("--work", required=True, help="篡改副本工作目录（一次性）")
    ap.add_argument("--out", default=str(HERE / "test_detect_client_report.json"))
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    jp, en = Path(args.jp).resolve(), Path(args.en).resolve()
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)

    cases: list[dict] = []

    # ---------- 正例 ----------
    cases.append(expect_ok(
        "P1 JP APK → jp",
        lambda: D.detect_client(jp, expect="jp"),
        lambda i: ([] if (i["region"] == "jp"
                          and i["product_name"] == "nier-jp.apk"
                          and i["ks_alias"] == "nier"
                          and i["cert_sha256"].startswith("eec23be0")
                          and i["detected"]["triple_ok"]) else
                   [f"分派不符: {i['region']}/{i['product_name']}/{i['ks_alias']}"])))
    cases.append(expect_ok(
        "P2 EN APK → en",
        lambda: D.detect_client(en, expect="en"),
        lambda i: ([] if (i["region"] == "en"
                          and i["product_name"] == "nier-en.apk"
                          and i["ks_alias"] == "androiddebugkey"
                          and i["cert_sha256"].startswith("7d792c3c")
                          and i["detected"]["triple_ok"]) else
                   [f"分派不符: {i['region']}/{i['product_name']}/{i['ks_alias']}"])))

    # ---------- 反例 ----------
    # N1 改 1 字节（文件中部资产区）
    n1 = work / "jp-tampered-mid.apk"
    t1 = tamper_copy(jp, n1, jp.stat().st_size // 2)
    cases.append(expect_fail("N1 JP 改 1 字节(中部) → 拒建",
                             lambda: D.detect_client(n1, expect="jp")) | {"tamper": t1})

    # N2 改 1 字节（AndroidManifest.xml 字符串池内）：zip 条目级重写
    n2 = work / "jp-tampered-manifest.apk"
    with zipfile.ZipFile(jp) as zin:
        names = zin.namelist()
        manifest = zin.read("AndroidManifest.xml")
    man = bytearray(manifest)
    # 翻转字符串池中部一字节（破坏包名串 → 包名判定失败或三元组拒建）
    man[len(man) // 2] ^= 0x01
    with zipfile.ZipFile(n2, "w", zipfile.ZIP_STORED) as zout:
        with zipfile.ZipFile(jp) as zin:
            for n in names:
                if n == "AndroidManifest.xml":
                    zout.writestr(n, bytes(man))
                else:
                    zout.writestr(n, zin.read(n))
    cases.append(expect_fail("N2 JP AndroidManifest 改 1 字节 → 拒建",
                             lambda: D.detect_client(n2, expect="jp"))
                 | {"tamper": {"path": str(n2), "entry": "AndroidManifest.xml",
                               "offset": len(man) // 2}})

    # N3/N4 region 矛盾即拒
    cases.append(expect_fail("N3 EN 包喂 jp 流水线 → 拒建",
                             lambda: D.detect_client(en, expect="jp")))
    cases.append(expect_fail("N4 JP 包喂 en 流水线 → 拒建",
                             lambda: D.detect_client(jp, expect="en")))

    # N5 未知客户端（空文件 + 伪 APK）
    n5a = work / "empty.apk"
    n5a.write_bytes(b"")
    cases.append(expect_fail("N5a 空文件 → 未知客户端拒建",
                             lambda: D.detect_client(n5a)))
    n5b = work / "fake.apk"
    n5b.write_bytes(b"PK\x03\x04 not an android apk")
    cases.append(expect_fail("N5b 伪 APK → 未知客户端拒建",
                             lambda: D.detect_client(n5b)))

    ok = all(c["ok"] for c in cases)
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": "shared/detect_client.py",
        "inputs": {"jp": str(jp), "jp_sha256": sha256_file(jp),
                   "en": str(en), "en_sha256": sha256_file(en)},
        "cases": cases,
        "summary": {"total": len(cases),
                    "passed": sum(1 for c in cases if c["ok"]),
                    "failed": sum(1 for c in cases if not c["ok"])},
        "ok": ok,
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    for c in cases:
        print(f"  [{'ok' if c['ok'] else 'FAIL'}] {c['case']}")
    print(f"[detect selftest] {'OK' if ok else 'FAILED'} -> {args.out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
