#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_jp_client.py — JP 客户端验证门（①-⑥）+ 与 fix3c 基准 APK 等价性对照。

检查项（口径与 work\\apk\\verify_fix3c.py / build-fix3c-verify.json 一致）：
  ① apksigner verify + 证书指纹 == EE:C2:3B…（eec23be0…d98a2fe）+ v2/v3
  ② fix3 62 串逐条命中计数（TextAsset 3 载体 + metadata，对照 builtin_strings.json 预期）
  ③ metadata stringLiteral 回读（公告/关闭/取消 + 播放影片族共 7 值）
  ④ 四字体条目 sha256 == 字体 payload（fonts/payload/assets/bin/Data）
  ⑤ 私服 IP 192.168.2.6 仍在（fix3c 口径 10 处：metadata 7 + classes.dex 2 + network_config 1）
  ⑥ 原版 APK sha256 前后不变（基线 25b6326c…653609）
  ⑦ zipalign -c -p 4 对齐校验
  ⑧ 与 fix3c 基准 APK 等价性对照：先试整文件逐字节；否则逐 zip 条目
     （除 zip 时间戳/META-INF 签名外逐项一致），并逐项比对 ①-⑤ 事实。

用法（build_jp_client.py 会自动调用；也可独立复跑）：
  python verify_jp_client.py --apk <新APK> [--baseline <fix3c.apk>] [--out-json report.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

JP = Path(__file__).resolve().parent
DEFAULT_FIX3 = JP / "fix3"
DEFAULT_PAYLOAD = JP / "fonts" / "payload" / "assets" / "bin" / "Data"
DEFAULT_ORIG = Path(r"E:\NieRReincarnation\resources\NieR Re[in]carnation_3.7.1_JP.apk")
DEFAULT_BASELINE = Path(r"E:\NieRReincarnation\zh-l10n\work\apk\nier-mod-menu-jp-font-fix3c.apk")
ORIG_BASELINE_SHA256 = "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609"
CERT_EXPECT = "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe"
FIX3C_EXPECT = {
    "fix3_entries_checked": 62,
    "fix3_entries_ok": 62,
    "fix3_textasset_hits": 68,
    "fix3_metadata_hits": 7,
    "private_ip_total_hits": 10,
    "fonts": {
        "6f937efa0660c47f59d5215d276b1cbb": "c97a431931099addbc4203606d48f03f151f4350b2bceac5a9ce72ea10026f3d",
        "7089ac60979c94824ac549baab08cfa7": "5ed20794fd7d8dacda0b05726c8a41828bb8a89330be01bde42c3d45944dee4e",
        "ad1489eb70ff840d19d7d0841bcdd3a9": "ad690f4b1a51d77a398935bf83d2bfc288f69dd7dead21f9d7904ec6160b0e34",
        "550e0743a6b6344cfa3380b9a07f58b6": "853ac67aacddd480b3a6f29f97171d431ce78fc6fa3b12e6dbb8039226ccb85b",
    },
}
FONT_ENTRIES = {
    "assets/bin/Data/6f937efa0660c47f59d5215d276b1cbb": "6f937efa0660c47f59d5215d276b1cbb",
    "assets/bin/Data/7089ac60979c94824ac549baab08cfa7": "7089ac60979c94824ac549baab08cfa7",
    "assets/bin/Data/ad1489eb70ff840d19d7d0841bcdd3a9": "ad1489eb70ff840d19d7d0841bcdd3a9",
    "assets/bin/Data/550e0743a6b6344cfa3380b9a07f58b6": "550e0743a6b6344cfa3380b9a07f58b6",
}
PRIVATE_IP = b"192.168.2.6"
UI_SPOT = ["公告", "联系我们", "数据继承", "数据修复", "其他信息", "删除数据",
           "关闭", "取消", "下载确认", "结束游戏", "要结束游戏吗？"]
TITLEFLOW_SPOT = ["注册玩家名", "请输入玩家名"]
META_SPOT = ["公告", "关闭", "取消", "打开公告", "打开推特", "播放影片", "播放影片中"]


# ------------------------------------------------------------------ helpers
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_unitypy(venv_site: str | None) -> None:
    """UnityPy 可用化：优先现解释器；否则挂 zh-l10n venv site-packages（PYTHONPATH 同源）。"""
    try:
        import UnityPy  # noqa: F401
        return
    except ImportError:
        pass
    cands = []
    if venv_site:
        cands.append(Path(venv_site))
    cands.append(Path(r"E:\NieRReincarnation\zh-l10n\.venv\Lib\site-packages"))
    for c in cands:
        if c.is_dir() and (c / "UnityPy").is_dir():
            sys.path.insert(0, str(c))
            import UnityPy  # noqa: F401
            return
    raise SystemExit("UnityPy 不可用：请安装 UnityPy 或在 toolpaths.json 配置 unitypy_site_packages")


def ta_text(buf: bytes) -> str:
    import UnityPy
    env = UnityPy.load(buf)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            s = getattr(d, "m_Script", None)
            if s is None:
                s = getattr(d, "script", None)
            if s is None:
                s = getattr(d, "text", None) or ""
            return s.decode("utf-8") if isinstance(s, (bytes, bytearray)) else str(s)
    return ""


def parse_kv_lines(text: str) -> list[tuple[str, str]]:
    out = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out.append((k, v))
    return out


def file_for_key(key: str) -> str:
    for pref, name in (("ui.", "ui"), ("titleflow.", "titleflow"), ("nt.", "nt")):
        if key.startswith(pref):
            return name
    return "?"


# ------------------------------------------------------------------ core
def analyze_apk(apk: Path, payload_dir: Path, fix3_dir: Path,
                orig_apk: Path, expect_input_sha: str | None,
                java: str, apksigner_jar: str, zipalign: str | None = None) -> dict:
    """对单个 APK 跑 ①-⑥ 事实集（不裁决），返回事实 dict。"""
    sys.path.insert(0, str(fix3_dir))
    import patch_fix3  # noqa: E402

    res: dict = {
        "apk": str(apk),
        "apk_sha256": sha256_file(apk),
        "apk_bytes": apk.stat().st_size,
    }

    # ⑥ 原版 APK 未变
    if orig_apk.is_file():
        orig_now = sha256_file(orig_apk)
        res["original_apk"] = {
            "path": str(orig_apk), "sha256_now": orig_now,
            "baseline": ORIG_BASELINE_SHA256,
            "matches_documented_baseline": orig_now == ORIG_BASELINE_SHA256,
            "unchanged_since_build": (orig_now == expect_input_sha) if expect_input_sha else None,
        }
    else:
        res["original_apk"] = {"path": str(orig_apk), "missing": True}

    with zipfile.ZipFile(apk) as zf:
        res["zip_ok"] = zf.testzip() is None
        res["zip_entries"] = len(zf.namelist())

        # ① apksigner
        proc = subprocess.run([java, "-jar", apksigner_jar,
                               "verify", "-v", "--print-certs", str(apk)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        text = (proc.stdout or "") + (proc.stderr or "")
        m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F:]+)", text)
        cert = m.group(1).replace(":", "").lower() if m else None
        res["apksigner"] = {
            "exit_code": proc.returncode,
            "verified_v2": "Verified using v2 scheme (APK Signature Scheme v2): true" in text,
            "verified_v3": "Verified using v3 scheme (APK Signature Scheme v3): true" in text,
            "cert_sha256": cert,
            "cert_matches_expected": cert == CERT_EXPECT,
        }

        # ⑦ zipalign -c
        if zipalign:
            proc2 = subprocess.run([zipalign, "-c", "-p", "4", str(apk)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
            res["zipalign"] = {"exit_code": proc2.returncode, "ok": proc2.returncode == 0,
                               "output_tail": ((proc2.stdout or "") + (proc2.stderr or "")).splitlines()[-5:]}
        else:
            res["zipalign"] = {"skipped": "zipalign binary not configured"}

        # ④ 四字体条目
        res["fonts"] = {}
        for entry, name in FONT_ENTRIES.items():
            data = zf.read(entry)
            payload_sha = sha256_file(payload_dir / name)
            got = sha256_bytes(data)
            res["fonts"][entry] = {"sha256": got, "payload_sha256": payload_sha,
                                   "matches_payload": got == payload_sha}

        # ②③ TextAsset + metadata
        ts_kv = {name: parse_kv_lines(ta_text(zf.read(entry)))
                 for entry, name in patch_fix3.TS_ENTRIES.items()}
        meta = zf.read(patch_fix3.META_ENTRY)

        def meta_values(data: bytes) -> list[str]:
            ents, sld_off, _ = patch_fix3.meta_entries(data)
            return [data[sld_off + e_idx:sld_off + e_idx + e_len].decode("utf-8", "replace")
                    for (_i, _e_off, e_len, e_idx) in ents]

        mvals = meta_values(meta)

        def present(name: str, needle: str) -> bool:
            return any(v == needle for (_k, v) in ts_kv[name])

        supplement_spot = {}
        for e in patch_fix3.load_table("all"):
            if e.get("tier") != "supplement":
                continue
            tgt = e.get("target_zh") or ""
            key0 = (e.get("keys") or ["?."])[0]
            fn = file_for_key(key0)
            meta_only = (int(e.get("expected_textasset") or 0) == 0
                         and int(e.get("expected_metadata") or 0) > 0)
            if meta_only or fn == "?":
                supplement_spot[e["id"]] = {"needle": tgt, "file": "metadata",
                                            "present": bool(tgt) and (tgt in mvals)}
            else:
                supplement_spot[e["id"]] = {"needle": tgt, "file": fn,
                                            "present": bool(tgt) and present(fn, tgt)}
        res["spot_checks"] = {
            "ui": {s: present("ui", s) for s in UI_SPOT},
            "titleflow": {s: present("titleflow", s) for s in TITLEFLOW_SPOT},
            "supplement": supplement_spot,
            "metadata_stringliteral": {s: (s in mvals) for s in META_SPOT},
        }

        counts = []
        for e in patch_fix3.load_table("all"):
            tgt = e.get("target_zh") or ""
            if not tgt or e["source_ja"].startswith("titleflow.dialog.termofservice"):
                continue
            per_file = {}
            for name in ("ui", "titleflow", "nt"):
                n = sum(1 for (_k, v) in ts_kv[name] if v == tgt)
                if n:
                    per_file[name] = n
            ta_n = sum(per_file.values())
            meta_n = sum(1 for v in mvals if v == tgt)
            exp_ta = int(e.get("expected_textasset") or 0)
            exp_meta = int(e.get("expected_metadata") or 0)
            counts.append({
                "id": e["id"], "tier": e["tier"], "target_zh": tgt,
                "expected_textasset": exp_ta, "actual_textasset": ta_n,
                "actual_per_file": per_file,
                "expected_metadata": exp_meta, "actual_metadata": meta_n,
                "ok": (ta_n == exp_ta and meta_n == exp_meta),
            })
        res["fix3_hit_counts"] = counts
        res["fix3_hit_summary"] = {
            "entries_checked": len(counts),
            "entries_ok": sum(1 for c in counts if c["ok"]),
            "total_textasset_hits": sum(c["actual_textasset"] for c in counts),
            "total_metadata_hits": sum(c["actual_metadata"] for c in counts),
        }

        # ⑤ 私服地址
        ip_hits = {}
        if PRIVATE_IP in meta:
            ip_hits[patch_fix3.META_ENTRY] = meta.count(PRIVATE_IP)
        for info in zf.infolist():
            if info.filename == patch_fix3.META_ENTRY or info.file_size > (1 << 24):
                continue
            if not (info.filename.startswith("assets/bin/Data/")
                    or re.fullmatch(r"classes\d*\.dex", info.filename.split("/")[-1])
                    or info.filename.startswith("smali")):
                continue
            try:
                blob = zf.read(info.filename)
            except Exception:  # noqa: BLE001
                continue
            if PRIVATE_IP in blob:
                ip_hits[info.filename] = blob.count(PRIVATE_IP)
        res["private_server"] = {"ip": "192.168.2.6", "hits": ip_hits,
                                 "present_in_metadata": patch_fix3.META_ENTRY in ip_hits,
                                 "total_hits": sum(ip_hits.values())}

        # zip 条目清单（等价性用）
        res["entries"] = {info.filename: {"size": info.file_size,
                                          "sha256": sha256_bytes(zf.read(info.filename)),
                                          "date_time": list(info.date_time)}
                          for info in zf.infolist()}
    return res


def judge(res: dict, expect_input_sha: str | None) -> dict:
    """①-⑥ 裁决。"""
    gates = {}

    a = res["apksigner"]
    gates["1_signature"] = bool(a["exit_code"] == 0 and a["verified_v2"] and a["verified_v3"]
                                and a["cert_matches_expected"])
    sc = res["spot_checks"]
    fhs = res["fix3_hit_summary"]
    gates["2_fix3_strings"] = bool(
        all(sc["ui"].values()) and all(sc["titleflow"].values())
        and all(v["present"] for v in sc["supplement"].values())
        and fhs["entries_checked"] == FIX3C_EXPECT["fix3_entries_checked"]
        and fhs["entries_ok"] == FIX3C_EXPECT["fix3_entries_ok"]
        and fhs["total_textasset_hits"] == FIX3C_EXPECT["fix3_textasset_hits"]
        and fhs["total_metadata_hits"] == FIX3C_EXPECT["fix3_metadata_hits"])
    gates["3_metadata_stringliteral"] = all(sc["metadata_stringliteral"].values())
    gates["4_fonts"] = (all(v["matches_payload"] for v in res["fonts"].values())
                        and len(res["fonts"]) == 4
                        and {k.split("/")[-1]: v["sha256"] for k, v in res["fonts"].items()}
                        == FIX3C_EXPECT["fonts"])
    ps = res["private_server"]
    gates["5_private_ip"] = bool(ps["present_in_metadata"]
                                 and ps["total_hits"] == FIX3C_EXPECT["private_ip_total_hits"])
    orig = res.get("original_apk", {})
    if orig.get("missing"):
        gates["6_original_untouched"] = False
    else:
        ok = orig["matches_documented_baseline"]
        if expect_input_sha and orig["unchanged_since_build"] is not None:
            ok = ok and orig["unchanged_since_build"]
        gates["6_original_untouched"] = bool(ok)
    gates["zip_integrity"] = bool(res["zip_ok"])
    gates["7_zipalign"] = bool(res.get("zipalign", {}).get("ok"))
    return gates


def compare_with_baseline(new: dict, base: dict) -> dict:
    """⑦ 等价性对照：整文件 → 逐 zip 条目 → 事实逐项。"""
    out: dict = {
        "baseline_apk": base["apk"],
        "new_apk": new["apk"],
        "whole_file_identical": new["apk_sha256"] == base["apk_sha256"],
    }
    ne, be = new["entries"], base["entries"]
    only_new = sorted(set(ne) - set(be))
    only_base = sorted(set(be) - set(ne))
    common = sorted(set(ne) & set(be))
    diff = [n for n in common if ne[n]["sha256"] != be[n]["sha256"]]
    same = [n for n in common if ne[n]["sha256"] == be[n]["sha256"]]
    ts_diff = [n for n in common if ne[n]["date_time"] != be[n]["date_time"]]
    sig_prefix = "META-INF/"
    diff_nonsig = [n for n in diff if not n.startswith(sig_prefix)]
    out["entries"] = {
        "baseline_count": len(be), "new_count": len(ne),
        "identical": len(same), "content_differs": len(diff),
        "content_differs_non_meta_inf": diff_nonsig,
        "content_differs_meta_inf": [n for n in diff if n.startswith(sig_prefix)],
        "only_in_new": only_new, "only_in_baseline": only_base,
        "timestamp_differs": len(ts_diff),
    }
    facts_new = {
        "cert": new["apksigner"]["cert_sha256"],
        "fonts": {k.split("/")[-1]: v["sha256"] for k, v in new["fonts"].items()},
        "fix3": new["fix3_hit_summary"],
        "private_ip": {"total_hits": new["private_server"]["total_hits"],
                       "hits": new["private_server"]["hits"]},
    }
    facts_base = {
        "cert": base["apksigner"]["cert_sha256"],
        "fonts": {k.split("/")[-1]: v["sha256"] for k, v in base["fonts"].items()},
        "fix3": base["fix3_hit_summary"],
        "private_ip": {"total_hits": base["private_server"]["total_hits"],
                       "hits": base["private_server"]["hits"]},
    }
    out["facts_new"] = facts_new
    out["facts_baseline"] = facts_base
    out["facts_identical"] = facts_new == facts_base
    out["equivalent"] = bool(
        not only_new and not only_base and not diff_nonsig and out["facts_identical"])
    out["verdict"] = (
        "whole-file identical" if out["whole_file_identical"]
        else ("identical except META-INF signature / zip timestamps"
              if out["equivalent"] else "DIFFERENT"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="JP 客户端验证门 ①-⑥ + fix3c 等价性对照")
    ap.add_argument("--apk", required=True, help="待验证 APK")
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE),
                    help="fix3c 基准 APK（默认 zh-l10n/work/apk/nier-mod-menu-jp-font-fix3c.apk；传空字符串跳过）")
    ap.add_argument("--orig-apk", default=str(DEFAULT_ORIG), help="原版 JP APK（⑥）")
    ap.add_argument("--payload", default=str(DEFAULT_PAYLOAD), help="字体 payload 目录")
    ap.add_argument("--fix3-dir", default=str(DEFAULT_FIX3), help="fix3 工具/表目录")
    ap.add_argument("--expect-input-sha", default=None,
                    help="构建开始时记录的原版 sha256（⑥ 附加项）")
    ap.add_argument("--out-json", default=None, help="报告 JSON 输出路径")
    ap.add_argument("--toolpaths", default=str(JP / "toolpaths.json"))
    ap.add_argument("--bin-e", default=None,
                    help="配套 bin.e（统一门 A3 文件名不变量；缺省跳过）")
    ap.add_argument("--expect-bin-e-name", default=None,
                    help="bin.e 期望文件名（默认 20240404193219.bin.e）")
    ap.add_argument("--sidecar", default=None,
                    help="manifest sidecar 路径（统一门 A4 rva_table_version 槽位）")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    tp = {}
    tp_path = Path(args.toolpaths)
    if tp_path.is_file():
        tp = json.loads(tp_path.read_text(encoding="utf-8-sig"))
    ensure_unitypy(tp.get("unitypy_site_packages"))

    # 工具定位（java / apksigner）
    java = tp.get("java") or ""
    if not java:
        jh = tp.get("java_home") or os.environ.get("JAVA_HOME") or ""
        java = str(Path(jh) / "bin" / "java.exe") if jh else "java"
    bt = tp.get("android_home") or os.environ.get("ANDROID_HOME") or ""
    apksigner_jar = tp.get("apksigner_jar") or ""
    zipalign = tp.get("zipalign") or ""
    if (not apksigner_jar or not zipalign) and bt:
        for c in (Path(bt) / "build-tools",):
            if c.is_dir():
                vers = sorted([d for d in c.iterdir() if d.is_dir()], reverse=True)
                for v in vers:
                    if not apksigner_jar:
                        for cand in (v / "lib" / "apksigner.jar", v / "apksigner.jar"):
                            if cand.is_file():
                                apksigner_jar = str(cand)
                                break
                    if not zipalign:
                        for cand in (v / "zipalign.exe", v / "zipalign"):
                            if cand.is_file():
                                zipalign = str(cand)
                                break
                    if apksigner_jar and zipalign:
                        break
    if not apksigner_jar or not Path(apksigner_jar).is_file():
        raise SystemExit(f"未找到 apksigner.jar（android_home={bt}）")
    if zipalign and not Path(zipalign).is_file():
        zipalign = ""

    apk = Path(args.apk).resolve()
    if not apk.is_file():
        raise SystemExit(f"APK 不存在: {apk}")
    payload_dir = Path(args.payload).resolve()
    fix3_dir = Path(args.fix3_dir).resolve()
    orig_apk = Path(args.orig_apk).resolve()

    res = analyze_apk(apk, payload_dir, fix3_dir, orig_apk, args.expect_input_sha,
                      java, apksigner_jar, zipalign or None)
    res["gates"] = judge(res, args.expect_input_sha)
    res["ok"] = all(res["gates"].values())

    base_arg = (args.baseline or "").strip()
    if base_arg:
        base_path = Path(base_arg).resolve()
        if base_path.is_file():
            print(f"[verify] 基准 APK 等价性对照: {base_path}")
            base_res = analyze_apk(base_path, payload_dir, fix3_dir, orig_apk, None,
                                  java, apksigner_jar, zipalign or None)
            res["baseline"] = compare_with_baseline(res, base_res)
            if not res["baseline"]["equivalent"]:
                res["ok"] = False
        else:
            res["baseline"] = {"skipped": f"baseline not found: {base_path}"}
            res["ok"] = False
    else:
        res["baseline"] = {"skipped": "baseline disabled"}

    # ---- L6 统一验证门四项（MANIFEST 预检 / 证书断言 / bin.e 文件名不变 /
    # RVA 表版本位）：断言定义 shared/gate_defs.py，执行器 shared/verify_gate.py，
    # 与 bunker 侧 verify_gate_zh.py 同 schema（nier-verify-gate/v1）。
    sys.path.insert(0, str(JP.parent / "shared"))
    import verify_gate as VG
    ug: list[dict] = []

    def _ug(cid, s, d, expected=None, actual=None):
        row = {"id": cid, "status": s, "detail": d}
        if expected is not None:
            row["expected"] = expected
        if actual is not None:
            row["actual"] = actual
        ug.append(row)

    s, d, det = VG.check_manifest_precheck(JP)
    _ug("manifest_precheck", s, d, actual=det)
    s, d, det = VG.check_cert_assertion(apk, "jp")
    _ug("cert_assertion", s, d, expected=VG.G.CLIENTS["jp"]["cert_sha256"],
        actual=det.get("actual"))
    bin_e = Path(args.bin_e).resolve() if args.bin_e else None
    if bin_e and bin_e.is_file():
        s, d, det = VG.check_bin_e_filename(
            bin_e, args.expect_bin_e_name or "20240404193219.bin.e")
        _ug("bin_e_filename", s, d, actual=det.get("name"))
    else:
        _ug("bin_e_filename", "skip", "未给 --bin-e（或文件不存在）", None)
    sidecar = (Path(args.sidecar).resolve() if args.sidecar
               else Path(str(apk) + ".manifest.json"))
    s, d, det = VG.check_rva_table_version(
        sidecar if sidecar.is_file() else None, "jp")
    _ug("rva_table_version", s, d,
        expected=VG.G.CLIENTS["jp"]["rva_table_version"], actual=det.get("slot"))
    res["unified_gate"] = {"schema": "nier-verify-gate/v1", "checks": ug,
                           "ok": all(c["status"] != "fail" for c in ug)}
    if not res["unified_gate"]["ok"]:
        res["ok"] = False

    out = Path(args.out_json).resolve() if args.out_json else apk.parent / (apk.stem + "-verify.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[verify] overall {'ok' if res['ok'] else 'FAIL'} -> {out}")
    print(f"[verify] apk sha256={res['apk_sha256']} bytes={res['apk_bytes']}")
    print(f"[verify] gates: " + " ".join(f"{k}={'Y' if v else 'N'}" for k, v in res["gates"].items()))
    print(f"[verify] cert={res['apksigner']['cert_sha256']} match={res['apksigner']['cert_matches_expected']} "
          f"v2={res['apksigner']['verified_v2']} v3={res['apksigner']['verified_v3']}")
    print(f"[verify] fonts_match={all(v['matches_payload'] for v in res['fonts'].values())} (4 entries)")
    print(f"[verify] fix3 {res['fix3_hit_summary']['entries_ok']}/{res['fix3_hit_summary']['entries_checked']} "
          f"ta_hits={res['fix3_hit_summary']['total_textasset_hits']} "
          f"meta_hits={res['fix3_hit_summary']['total_metadata_hits']}")
    print(f"[verify] private_ip_hits={res['private_server']['total_hits']} "
          f"in_metadata={res['private_server']['present_in_metadata']}")
    print(f"[verify] original_unchanged={res['gates']['6_original_untouched']}")
    print(f"[verify] zipalign={res.get('zipalign', {})}")
    print("[verify] unified_gate: " + " ".join(
        f"{c['id']}={'Y' if c['status'] == 'pass' else ('-' if c['status'] == 'skip' else 'N')}"
        for c in res["unified_gate"]["checks"]))
    if "equivalent" in res.get("baseline", {}):
        b = res["baseline"]
        print(f"[verify] baseline equivalence: {b['verdict']} "
              f"(identical={b['entries']['identical']} differs={b['entries']['content_differs']} "
              f"non_meta_diff={len(b['entries']['content_differs_non_meta_inf'])} "
              f"only_new={len(b['entries']['only_in_new'])} only_base={len(b['entries']['only_in_baseline'])} "
              f"facts_identical={b['facts_identical']})")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
