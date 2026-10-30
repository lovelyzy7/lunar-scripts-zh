#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
# 【归档副本 ARCHIVE】2026-10-29 归档
# 来源：E:\NieRReincarnation\zh-l10n\work\en-apk\verify_en_build.py
# 归档时正文未改动；2026-10-30 L6 扩展：尾部追加统一验证门四项（MANIFEST 预检 /
# 证书断言 / bin.e 文件名不变 / RVA 表版本位），来源侧无此段。
# EN 构建产物独立验证脚本（签名/字体 sha/私服 IP/builtin 回读/原版 sha/打包完整性），
# 运行仍依赖 zh-l10n 工作区绝对路径，详见同目录 README-EN.md。
# =====================================================================
"""verify_en_build.py — EN 构建产物独立验证（①-⑥ + ④b ko 段回读 + ④c fix3l 回读），产出 build-en-verify*.json。

  ① apksigner v2+v3 且证书 7D:79:2C…（= en-client debug key）
  ② 字体四条目 sha256 = payload3（容器 + m_FontData 双校验）
  ③ 私服 IP 192.168.2.6 命中数（逐条目）
  ④ fix3 EN 串回读（EN→中：TextAsset 键值 + metadata stringLiteral）
  ④b fix3 **ko 段**回读（ko→中：68 键值命中 + 旧 ko 值残留 0）
  ④c fix3l 扩展键回读（EN+ko 双段：13 键值命中）
  ⑤ 原版 APK sha256 未动
  ⑥ 打包完整性（zip testzip + 条目数 + zipalign -c）

用法：python verify_en_build.py [--apk PATH] [--report PATH]
     [--bin-e PATH] [--expect-bin-e-name NAME] [--sidecar PATH]
（尾部 L6 统一验证门四项：MANIFEST 预检 / 证书断言 / bin.e 文件名不变 /
 RVA 表版本位——断言定义 shared/gate_defs.py，执行器 shared/verify_gate.py。）
"""
from __future__ import annotations
import argparse, hashlib, io, json, re, struct, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
HERE = ROOT / "zh-l10n" / "work" / "en-apk"
APK = HERE / "nier-mod-menu-en-font-fix3l.apk"
REPORT = HERE / "build-en-verify-fix3l.json"
ORIG = ROOT / "resources" / "NieR Re[in]carnation 3.7.1_EN.apk"
ORIG_SHA256 = "9ded0797ee607b6892b531ba3a02f4c4510774f5fe098ccada78ccff881c9209"
EXPECTED_CERT = "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173"
PAY = ROOT / "zh-l10n" / "work" / "fonts-fix4" / "out3" / "payload3" / "assets" / "bin" / "Data"
FONT_TABLE = {
    "6f937efa0660c47f59d5215d276b1cbb": ("8c5827fcb21151787399cca61dd8b89a0e1101a9e1a5af2c4b27e0e1a9952233",
                                        "27224151be7e42f58a88687990c2d7eef60f754f1c1ee042fdc6aae3a7da9199"),
    "7089ac60979c94824ac549baab08cfa7": ("c1907f2bad9d71738cc26a8cdb621d9370aeedbba479b01414da8139949621fc",
                                        "e2a6cffb919130d6d9231979dd948c05659bc8fd3260f2423b0d4b17296f4194"),
    "ad1489eb70ff840d19d7d0841bcdd3a9": ("f08ba7ff06991072d928b52daf86c1a6bf226c59653d728cc71408c6242c1ae3",
                                        "37d360aec2f4f6ed2040149e9e079834aaf73a43a6b43bd91e5721e341374f69"),
    "550e0743a6b6344cfa3380b9a07f58b6": ("b18ee0b9b54472a3f6b8f6c5bb320fe42da3cc28b5034d4857519688ebbbf8ae",
                                        "b973a96628222c68aa182b4aa89ae1cbe956e5a323eb05ed2431351cc40f7b44"),
}
JAVA = Path(r"C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot\bin\java.exe")
APKSIGNER = Path(r"C:\Users\Yu\AppData\Local\Android\Sdk\build-tools\37.0.0\lib\apksigner.jar")
ZIPALIGN = Path(r"C:\Users\Yu\AppData\Local\Android\Sdk\build-tools\37.0.0\zipalign.exe")
META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
TS_EN = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
    "assets/bin/Data/1dc4624c9ddde409fb4ffb1b0cb2faeb": "nt(en)",
}
TS_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
    "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7": "nt(ko)",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fontdata_of(buf):
    import UnityPy
    env = UnityPy.load(buf)
    for o in env.objects:
        if o.type.name == "Font":
            return bytes(o.read().m_FontData)
    return None


def meta_entries(data):
    sl_off, sl_size = struct.unpack_from("<II", data, 8)
    sld_off, _ = struct.unpack_from("<II", data, 16)
    out = []
    for i in range(sl_size // 8):
        e_off = sl_off + i * 8
        e_len, e_idx = struct.unpack_from("<II", data, e_off)
        out.append((i, e_len, e_idx))
    return out, sld_off


def main():
    global APK, REPORT
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", default=str(APK), help="待验证 APK（默认上轮产物）")
    ap.add_argument("--report", default=str(REPORT), help="输出 JSON（默认 build-en-verify.json）")
    ap.add_argument("--bin-e", default=None,
                    help="配套 bin.e（统一门 A3 文件名不变量；缺省跳过）")
    ap.add_argument("--expect-bin-e-name", default=None,
                    help="bin.e 期望文件名（默认 20240404193219.bin.e）")
    ap.add_argument("--sidecar", default=None,
                    help="manifest sidecar 路径（统一门 A4 rva_table_version 槽位）")
    args = ap.parse_args()
    APK = Path(args.apk).resolve()
    REPORT = Path(args.report).resolve()
    sys.path.insert(0, str(HERE))
    import patch_fix3_en as F

    res = {"apk": str(APK), "apk_bytes": APK.stat().st_size, "apk_sha256": sha(APK.read_bytes())}
    checks = {}

    # ① 签名
    out = subprocess.run([str(JAVA), "-jar", str(APKSIGNER), "verify", "-v", "--print-certs", str(APK)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    text = out.stdout + out.stderr
    m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F:]+)", text)
    cert = m.group(1).replace(":", "").lower() if m else None
    checks["1_signature"] = {
        "ok": ("Verified using v2 scheme (APK Signature Scheme v2): true" in text
               and "Verified using v3 scheme (APK Signature Scheme v3): true" in text
               and cert == EXPECTED_CERT),
        "v2": "Verified using v2 scheme (APK Signature Scheme v2): true" in text,
        "v3": "Verified using v3 scheme (APK Signature Scheme v3): true" in text,
        "cert_sha256": cert, "expected": EXPECTED_CERT,
    }
    print("[1] signature:", checks["1_signature"]["ok"], cert)

    with zipfile.ZipFile(APK) as zf:
        # ② 字体
        fonts = {}
        for name, (p_sha, fd_sha) in FONT_TABLE.items():
            data = zf.read("assets/bin/Data/" + name)
            pay = (PAY / name).read_bytes()
            fd, pfd = fontdata_of(data), fontdata_of(pay)
            fonts[name] = {
                "bytes": len(data), "sha256": sha(data),
                "matches_payload2": sha(data) == p_sha,
                "payload2_file_sha256": sha(pay),
                "fontdata_sha256": sha(fd) if fd else None,
                "fontdata_matches_payload2": fd is not None and sha(fd) == fd_sha,
                "payload2_fontdata_sha256": sha(pfd) if pfd else None,
            }
        checks["2_fonts"] = {"ok": all(v["matches_payload2"] and v["fontdata_matches_payload2"]
                                       for v in fonts.values()), "files": fonts}
        print("[2] fonts:", checks["2_fonts"]["ok"],
              {k[:8]: v["matches_payload2"] and v["fontdata_matches_payload2"] for k, v in fonts.items()})

        # ③ 私服 IP
        ip = b"192.168.2.6"
        per = {}
        total = 0
        for n in zf.namelist():
            if n.endswith("/"):
                continue
            c = zf.read(n).count(ip)
            if c:
                per[n] = c
                total += c
        checks["3_private_ip"] = {"ok": total > 0, "total": total, "per_entry": per}
        print("[3] private ip:", total, per)

        # ④ fix3 EN 回读
        entries = F.load_entries("all")
        kmap = F.key_map(entries)
        mrep = F.meta_repl(entries)
        ta = {}
        total_keys = total_zh = 0
        for entry, label in TS_EN.items():
            env_txt = fontdata_of  # noqa
            import UnityPy
            env = UnityPy.load(zf.read(entry))
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    s = obj.read().m_Script
                    text2 = s.decode("utf-8") if isinstance(s, bytes) else s
                    for line in text2.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {k: (kv[k] == zh) for k, zh in kmap.items() if k in kv}
            n_zh = sum(1 for v in hits.values() if v)
            total_keys += len(hits)
            total_zh += n_zh
            ta[label] = {"keys_found": len(hits), "zh_hits": n_zh,
                         "bad": [k for k, v in hits.items() if not v]}
            print(f"[4] {label}: keys={len(hits)} zh={n_zh}")
        meta = zf.read(META_ENTRY)
        ents, sld = meta_entries(meta)
        per_meta = {}
        m_ok = 0
        for old, zh in mrep.items():
            ob, nb = old.encode("utf-8"), zh.encode("utf-8")
            old_n = sum(1 for (i, e_len, e_idx) in ents
                        if e_len == len(ob) and meta[sld + e_idx:sld + e_idx + e_len] == ob)
            new_n = sum(1 for (i, e_len, e_idx) in ents
                        if e_len == len(nb) and meta[sld + e_idx:sld + e_idx + e_len] == nb)
            ok = old_n == 0 and new_n >= 1
            m_ok += ok
            per_meta[f"{old}->{zh}"] = {"old_remaining": old_n, "new_hits": new_n, "ok": ok}
        checks["4_fix3_en"] = {
            "ok": total_keys == total_zh and total_keys == 68 and m_ok == len(mrep),
            "ta_keys": total_keys, "ta_zh": total_zh, "ta": ta,
            "meta_expected": len(mrep), "meta_zh": m_ok, "meta": per_meta,
        }
        print("[4] fix3-en: ta", total_zh, "/", total_keys, "meta", m_ok, "/", len(mrep))

        # ④b fix3 ko 段回读（68 键值=中文 + 旧 ko 值残留 0）
        import patch_fix3_ko as K
        kmap_ko = K.key_map(K.load_entries("all"))
        old_ko = {}
        if K.APPLY_REPORT.is_file():
            old_ko = json.loads(K.APPLY_REPORT.read_text(encoding="utf-8")).get("old_ko_values", {})
        ko_ta = {}
        ko_keys = ko_zh = ko_old_left = 0
        for entry, label in TS_KO.items():
            import UnityPy
            env = UnityPy.load(zf.read(entry))
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    s = obj.read().m_Script
                    text2 = s.decode("utf-8") if isinstance(s, bytes) else s
                    for line in text2.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {k: (kv[k] == zh) for k, zh in kmap_ko.items() if k in kv}
            old_left = [k for k in kmap_ko
                        if k in kv and old_ko.get(k) is not None and kv[k] == old_ko[k]]
            n_zh = sum(1 for v in hits.values() if v)
            ko_keys += len(hits)
            ko_zh += n_zh
            ko_old_left += len(old_left)
            ko_ta[label] = {"keys_found": len(hits), "zh_hits": n_zh,
                            "bad": [k for k, v in hits.items() if not v],
                            "old_value_residual_keys": old_left,
                            "short_values": {k: kv[k] for k in K.KO_OVERRIDE if k in kv}}
            print(f"[4b] {label}: keys={len(hits)} zh={n_zh} old_residual={len(old_left)}")
        checks["4b_fix3_ko"] = {
            "ok": ko_keys == ko_zh and ko_keys == 68 and ko_old_left == 0,
            "ta_keys": ko_keys, "ta_zh": ko_zh,
            "old_value_residual_total": ko_old_left,
            "overrides": {k: v["zh"] for k, v in K.KO_OVERRIDE.items()},
            "ta": ko_ta,
        }
        print("[4b] fix3-ko:", ko_zh, "/", ko_keys, "old_residual", ko_old_left)

        # ④c fix3l 扩展键回读（EN+ko 双段）
        sys.path.insert(0, str(HERE))
        import patch_fix3l as L
        lmap_en = {k: v["en"] for k, v in L.FIX3L_KEYS.items()}
        lmap_ko = {k: v["ko"] for k, v in L.FIX3L_KEYS.items()}
        l_en_keys, l_en_zh, l_ko_keys, l_ko_zh = 0, 0, 0, 0
        l_ta = {}
        for entry, label in L.TS_EN.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    s = obj.read().m_Script
                    text2 = s.decode("utf-8") if isinstance(s, bytes) else s
                    for line in text2.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {k: (kv[k] == zh) for k, zh in lmap_en.items() if k in kv}
            n_zh = sum(1 for v in hits.values() if v)
            l_en_keys += len(hits)
            l_en_zh += n_zh
            l_ta[f"en:{label}"] = {"keys_found": len(hits), "zh_hits": n_zh,
                                    "bad": [k for k, v in hits.items() if not v]}
            print(f"[4c-en] {label}: keys={len(hits)} zh={n_zh}")
        for entry, label in L.TS_KO.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    s = obj.read().m_Script
                    text2 = s.decode("utf-8") if isinstance(s, bytes) else s
                    for line in text2.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {k: (kv[k] == zh) for k, zh in lmap_ko.items() if k in kv}
            n_zh = sum(1 for v in hits.values() if v)
            l_ko_keys += len(hits)
            l_ko_zh += n_zh
            l_ta[f"ko:{label}"] = {"keys_found": len(hits), "zh_hits": n_zh,
                                    "bad": [k for k, v in hits.items() if not v]}
            print(f"[4c-ko] {label}: keys={len(hits)} zh={n_zh}")
        checks["4c_fix3l"] = {
            "ok": l_en_keys == l_en_zh and l_en_keys > 0 and l_ko_keys == l_ko_zh and l_ko_keys > 0,
            "en_keys": l_en_keys, "en_zh": l_en_zh,
            "ko_keys": l_ko_keys, "ko_zh": l_ko_zh,
            "keys_defined": len(L.FIX3L_KEYS),
            "ta": l_ta,
        }
        print("[4c] fix3l:", l_en_zh, "/", l_en_keys, "EN +", l_ko_zh, "/", l_ko_keys, "ko")

        # ⑥ 打包完整性
        checks["6_package"] = {
            "ok": zf.testzip() is None,
            "zip_ok": zf.testzip() is None,
            "entries": len(zf.namelist()),
            "has_libil2cpp": "lib/arm64-v8a/libil2cpp.so" in zf.namelist(),
            "has_libniermenu": "lib/arm64-v8a/libniermenu.so" in zf.namelist(),
            "has_metadata": META_ENTRY in zf.namelist(),
        }
        print("[6] package:", checks["6_package"]["ok"], checks["6_package"]["entries"], "entries")

    # ⑤ 原版未动
    oh = hashlib.sha256()
    with ORIG.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            oh.update(chunk)
    orig_sha = oh.hexdigest()
    checks["5_original_untouched"] = {"ok": orig_sha == ORIG_SHA256,
                                      "sha256": orig_sha, "expected": ORIG_SHA256}
    print("[5] original untouched:", checks["5_original_untouched"]["ok"], orig_sha)

    # zipalign
    al = subprocess.run([str(ZIPALIGN), "-c", "-p", "4", str(APK)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    checks["zipalign"] = {"ok": al.returncode == 0, "exit_code": al.returncode}
    print("[+] zipalign:", checks["zipalign"]["ok"])

    # ---- L6 统一验证门四项（MANIFEST 预检 / 证书断言 / bin.e 文件名不变 /
    # RVA 表版本位）：断言定义 shared/gate_defs.py，执行器 shared/verify_gate.py，
    # 与 bunker 侧 verify_gate_zh.py 同 schema（nier-verify-gate/v1）。
    # MANIFEST 预检对象 = 本脚本所在 en-client 权威副本（非 HERE 归档工作区）。
    EN_CLIENT = Path(__file__).resolve().parent
    sys.path.insert(0, str(EN_CLIENT.parent / "shared"))
    import verify_gate as VG
    apk_p = Path(args.apk).resolve()
    ug: list[dict] = []

    def _ug(cid, s, d, expected=None, actual=None):
        row = {"id": cid, "status": s, "detail": d}
        if expected is not None:
            row["expected"] = expected
        if actual is not None:
            row["actual"] = actual
        ug.append(row)

    s, d, det = VG.check_manifest_precheck(EN_CLIENT)
    _ug("manifest_precheck", s, d, actual=det)
    s, d, det = VG.check_cert_assertion(apk_p, "en")
    _ug("cert_assertion", s, d, expected=VG.G.CLIENTS["en"]["cert_sha256"],
        actual=det.get("actual"))
    bin_e = Path(args.bin_e).resolve() if args.bin_e else None
    if bin_e and bin_e.is_file():
        s, d, det = VG.check_bin_e_filename(
            bin_e, args.expect_bin_e_name or "20240404193219.bin.e")
        _ug("bin_e_filename", s, d, actual=det.get("name"))
    else:
        _ug("bin_e_filename", "skip", "未给 --bin-e（或文件不存在）", None)
    sidecar = (Path(args.sidecar).resolve() if args.sidecar
               else Path(str(apk_p) + ".manifest.json"))
    s, d, det = VG.check_rva_table_version(
        sidecar if sidecar.is_file() else None, "en")
    _ug("rva_table_version", s, d,
        expected=VG.G.CLIENTS["en"]["rva_table_version"], actual=det.get("slot"))
    res["unified_gate"] = {"schema": "nier-verify-gate/v1", "checks": ug,
                           "ok": all(c["status"] != "fail" for c in ug)}
    checks["unified_gate"] = {"ok": res["unified_gate"]["ok"],
                              "checks": res["unified_gate"]["checks"]}
    print("[u] unified_gate:", res["unified_gate"]["ok"], " ".join(
        f"{c['id']}={'Y' if c['status'] == 'pass' else ('-' if c['status'] == 'skip' else 'N')}"
        for c in ug))

    res["checks"] = checks
    res["ok"] = all(c.get("ok") for c in checks.values())
    REPORT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("report ->", REPORT)
    print("=== VERIFY", "OK" if res["ok"] else "FAILED", "===")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
