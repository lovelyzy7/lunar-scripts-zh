#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_colab_functions.py — 本地把 android_lunar_zh.ipynb 的关键函数抽出来对 fixtures 跑一遍。

不做真 Colab，只证明 notebook 代码路径正确：
  T0  nbformat 结构校验（可上传）+ 全 cell 可 exec（无语法错误、无 Colab 侧副作用）
  T1  load_config/check_config：正常通过 + 三种缺配置正确报错
  T2  load_payload：make_payload_zip.ps1 产物 zip 解包 + _REQUIRED 清单 fail-fast
  T3  patch_apk_flow：对**原版 JP APK** 跑 APK 侧补丁（私服+fix3+字体+mod 菜单→重签名）
  T4  patch_bin_e_flow：对**汉化基 bin_zh_fix6.bin.e** 跑 bin.e 编辑（三重断言全过）
  T5  save_outputs：本地模式落盘两个目标文件

用法：
  C:\\Python314\\python.exe jp-client\\colab\\test_colab_functions.py [--skip-apk]
报告：--out（缺省 = zh-l10n\\work\\release-jp\\staging\\colab-test\\colab-test-report.json）
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
JP = HERE.parent
NOTEBOOK = HERE / "android_lunar_zh.ipynb"
ROOT = Path(r"E:\NieRReincarnation")
FIX6 = ROOT / "zh-l10n/work/mt-run/fix6-text/bin_zh_fix6.bin.e"
ORIG_BIN = ROOT / "zh-l10n/work/masterdata/00-baseline.bin.e"
ORIG_APK = ROOT / "resources/NieR Re[in]carnation_3.7.1_JP.apk"
WORK = ROOT / "zh-l10n/work/apk/jp-client-colab-test"
STAGE = ROOT / "zh-l10n/work/release-jp/staging/colab-test"
NBPYKGS = ROOT / "tmp_u_heuristics/pypkgs"

sys.path.insert(0, str(NBPYKGS))
# bin.e 依赖（pycryptodome/msgpack/lz4）= lunar-base venv；UnityPy = zh-l10n venv。
# 口径同 build_jp_client.ensure_unitypy/ensure_bin_deps；Colab 上两者都是 pip install。
_LB = r"E:\NieRReincarnation\lunar-base\.venv\Lib\site-packages"
_ZH = r"E:\NieRReincarnation\zh-l10n\.venv\Lib\site-packages"
sys.path.insert(0, _LB)
sys.path.insert(0, _ZH)
os.environ["PYTHONPATH"] = os.pathsep.join([_LB, _ZH, os.environ.get("PYTHONPATH", "")])


def sha256_file(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


# --------------------------------------------------------------------------
def t0_notebook_structure(report: dict) -> dict:
    import nbformat
    nb = nbformat.read(str(NOTEBOOK), as_version=4)
    nbformat.validate(nb)
    # 全 cell 逐个 compile（语法门），再整体 exec（无 Colab 侧副作用门）
    ns: dict = {"__name__": "colab_cells"}
    compiled = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            compiled.append({"index": i, "type": "markdown", "chars": len(cell.source)})
            continue
        code = compile(cell.source, f"<cell{i}>", "exec")
        exec(code, ns)
        compiled.append({"index": i, "type": "code", "chars": len(cell.source),
                         "defines": [n for n in ("drive_path", "load_config", "check_config",
                                                 "install_dependencies", "load_payload",
                                                 "patch_apk_flow", "patch_bin_e_flow",
                                                 "save_outputs", "_run", "_fetch_source")
                                     if n in ns]})
    fns = sorted(n for n in ns if callable(ns[n]) and not n.startswith("__"))
    return {"nbformat": f"{nb.nbformat}.{nb.nbformat_minor}",
            "cells": [{"index": c["index"], "type": c["type"], "chars": c["chars"]} for c in compiled],
            "cell_count": len(nb.cells),
            "functions": fns,
            "namespace_keys": sorted(k for k in ns if not k.startswith("__")),
            "ns": ns}


def t1_config(ns: dict) -> dict:
    cfg = ns["load_config"]()
    cfg["use_gdrive"] = False
    cfg["apk_source"] = str(ORIG_APK)
    cfg["masterdata_source"] = str(FIX6)
    cfg["payload_zip"] = str(WORK / "jp-client-payload.zip")
    cfg["orig_bin_e_source"] = str(ORIG_BIN)
    cfg["work"] = str(WORK)
    cfg["jp_root"] = str(WORK / "jp-client")
    ns["check_config"](cfg)
    cases = []
    for field in ("apk_source", "masterdata_source", "payload_zip", "grpc_addr"):
        bad = dict(cfg)
        bad[field] = ""
        try:
            ns["check_config"](bad)
            cases.append({"field": field, "raised": False})
        except RuntimeError as exc:
            cases.append({"field": field, "raised": True, "message": str(exc).splitlines()[0]})
    ok = all(c["raised"] for c in cases)
    return {"config_ok": True, "negative_cases": cases, "ok": ok}


def t2_payload(ns: dict, cfg: dict, report: dict) -> dict:
    zip_path = WORK / "jp-client-payload.zip"
    if zip_path.is_file():
        zip_path.unlink()
    shell = (shutil.which("pwsh") or shutil.which("powershell")
             or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
    r = run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(HERE / "make_payload_zip.ps1"), "-OutZip", str(zip_path)])
    if r.returncode != 0:
        raise RuntimeError(f"make_payload_zip.ps1 failed: {r.stdout}\n{r.stderr}")
    root = ns["load_payload"](cfg)
    required = ns["_REQUIRED"]
    missing = [f for f in required if not (Path(root) / f).is_file()]
    return {"zip": str(zip_path), "zip_bytes": zip_path.stat().st_size,
            "zip_sha256": sha256_file(zip_path), "extract_root": root,
            "required_checked": len(required), "missing": missing,
            "ok": not missing}


def t3_patch_apk(ns: dict, cfg: dict) -> dict:
    tools = json.loads((JP / "toolpaths.json").read_text(encoding="utf-8-sig"))
    java = tools.get("java") or str(Path(tools["java_home"]) / "bin" / "java.exe")
    bt = Path(tools["android_home"]) / "build-tools"
    bt_ver = sorted([d for d in bt.iterdir() if d.is_dir()])[-1]
    tools_cfg = {
        "apktool": [java, "-jar", tools["apktool_jar"]],
        "zipalign": str(bt_ver / "zipalign.exe"),
        "apksigner": [java, "-jar", str(bt_ver / "lib" / "apksigner.jar")],
        "python": sys.executable,
    }
    t0 = time.time()
    out_apk = ns["patch_apk_flow"](cfg, tools=tools_cfg)
    out = Path(out_apk)
    facts = {"path": str(out), "bytes": out.stat().st_size, "sha256": sha256_file(out),
             "elapsed_sec": round(time.time() - t0, 1)}
    # 抽查：私服 IP / fix3 中文串 / 字体条目存在
    import zipfile
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        meta = zf.read("assets/bin/Data/Managed/Metadata/global-metadata.dat")
        facts["font_entries"] = {
            n: ("assets/bin/Data/" + n) in names
            for n in ("6f937efa0660c47f59d5215d276b1cbb",
                      "7089ac60979c94824ac549baab08cfa7",
                      "ad1489eb70ff840d19d7d0841bcdd3a9",
                      "550e0743a6b6344cfa3380b9a07f58b6")}
        payload_dir = JP / "fonts" / "payload" / "assets" / "bin" / "Data"
        facts["font_sha_match"] = {
            n: sha256_bytes(zf.read("assets/bin/Data/" + n)) == sha256_file(payload_dir / n)
            for n in facts["font_entries"]}
        facts["fix3_spot"] = {s: (s.encode("utf-8") in meta) for s in ("公告", "取消", "播放影片")}
        facts["private_ip"] = meta.count(b"192.168.2.6")
        facts["has_libniermenu"] = "lib/arm64-v8a/libniermenu.so" in names
    facts["ok"] = bool(
        all(facts["font_entries"].values()) and all(facts["font_sha_match"].values())
        and all(facts["fix3_spot"].values())
        and facts["private_ip"] > 0 and facts["has_libniermenu"])
    return facts


def t4_patch_bin_e(ns: dict, cfg: dict) -> dict:
    t0 = time.time()
    out_bin, rep = ns["patch_bin_e_flow"](cfg)
    out = Path(out_bin)
    return {"path": str(out), "bytes": out.stat().st_size, "sha256": sha256_file(out),
            "elapsed_sec": round(time.time() - t0, 1),
            "assert_text_cells": rep["text_cells"]["identical"],
            "assert_structure": rep["structure"]["ok"],
            "assert_diff_expected": rep.get("diff_vs_orig", {}).get("ok"),
            "diff_tables": len(rep.get("diff_vs_orig", {}).get("changed_tables", [])),
            "cell_level_ok": rep.get("cell_level_ok"),
            "ok": bool(rep.get("ok"))}


def t5_save(ns: dict, cfg: dict, apk_path: str, bin_path: str) -> dict:
    a, b = ns["save_outputs"](cfg, apk_path=apk_path, bin_path=bin_path)
    return {"apk_saved": os.path.isfile(a), "bin_saved": os.path.isfile(b),
            "apk": a, "bin": b, "ok": os.path.isfile(a) and os.path.isfile(b)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-apk", action="store_true", help="跳过 T3 重活（APK 全流程）")
    ap.add_argument("--out", default=str(STAGE / "colab-test-report.json"))
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    WORK.mkdir(parents=True, exist_ok=True)
    STAGE.mkdir(parents=True, exist_ok=True)
    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "notebook": str(NOTEBOOK), "tests": {}}
    t0 = time.time()
    ok = True

    try:
        r0 = t0_notebook_structure(report)
        ns = r0.pop("ns")
        report["tests"]["T0_notebook"] = dict(r0, ok=True)
        print(f"[T0] notebook OK: {r0['cell_count']} cells, functions={r0['functions']}")
    except BaseException as exc:  # noqa: BLE001
        report["tests"]["T0_notebook"] = {"ok": False, "error": str(exc),
                                          "trace": traceback.format_exc()}
        _write(report, args.out, t0)
        return 2

    r1 = t1_config(ns)
    report["tests"]["T1_config"] = r1
    ok &= r1["ok"]
    print(f"[T1] config ok={r1['ok']} negatives={r1['negative_cases']}")

    cfg = ns["load_config"]()
    cfg["use_gdrive"] = False
    cfg["apk_source"] = str(ORIG_APK)
    cfg["masterdata_source"] = str(FIX6)
    cfg["payload_zip"] = str(WORK / "jp-client-payload.zip")
    cfg["orig_bin_e_source"] = str(ORIG_BIN)
    cfg["work"] = str(WORK)
    cfg["jp_root"] = str(WORK / "jp-client")
    cfg["out_apk_drive"] = ""
    cfg["out_bin_drive"] = ""

    try:
        r2 = t2_payload(ns, cfg, report)
        report["tests"]["T2_payload"] = r2
        ok &= r2["ok"]
        print(f"[T2] payload ok={r2['ok']} zip={r2['zip_bytes']}B required={r2['required_checked']}")
    except BaseException as exc:  # noqa: BLE001
        report["tests"]["T2_payload"] = {"ok": False, "error": str(exc),
                                         "trace": traceback.format_exc()}
        ok = False

    apk_path = bin_path = None
    if not args.skip_apk:
        try:
            r3 = t3_patch_apk(ns, cfg)
            report["tests"]["T3_patch_apk"] = r3
            ok &= r3["ok"]
            apk_path = r3["path"]
            print(f"[T3] patch_apk ok={r3['ok']} sha={r3['sha256'][:16]}… {r3['elapsed_sec']}s")
        except BaseException as exc:  # noqa: BLE001
            report["tests"]["T3_patch_apk"] = {"ok": False, "error": str(exc),
                                               "trace": traceback.format_exc()}
            ok = False
    else:
        report["tests"]["T3_patch_apk"] = {"ok": None, "skipped": True}

    try:
        r4 = t4_patch_bin_e(ns, cfg)
        report["tests"]["T4_patch_bin_e"] = r4
        ok &= r4["ok"]
        bin_path = r4["path"]
        print(f"[T4] patch_bin_e ok={r4['ok']} diff_tables={r4['diff_tables']} "
              f"sha={r4['sha256'][:16]}…")
    except BaseException as exc:  # noqa: BLE001
        report["tests"]["T4_patch_bin_e"] = {"ok": False, "error": str(exc),
                                             "trace": traceback.format_exc()}
        ok = False

    if apk_path and bin_path:
        try:
            r5 = t5_save(ns, cfg, apk_path, bin_path)
            report["tests"]["T5_save_outputs"] = r5
            ok &= r5["ok"]
            print(f"[T5] save_outputs ok={r5['ok']}")
        except BaseException as exc:  # noqa: BLE001
            report["tests"]["T5_save_outputs"] = {"ok": False, "error": str(exc),
                                                  "trace": traceback.format_exc()}
            ok = False
    else:
        report["tests"]["T5_save_outputs"] = {"ok": None, "skipped": True}

    report["ok"] = bool(ok)
    _write(report, args.out, t0)
    print(f"=== COLAB TEST {'OK' if ok else 'FAIL'} -> {args.out} ===")
    return 0 if ok else 2


def _write(report: dict, out: str, t0: float):
    report["elapsed_sec"] = round(time.time() - t0, 1)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out}")


if __name__ == "__main__":
    sys.exit(main())
