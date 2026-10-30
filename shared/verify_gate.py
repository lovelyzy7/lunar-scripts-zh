#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_gate.py — L6 统一验证门执行器（bunker 侧与 lunar-scripts-zh 侧共用）。

断言定义/期望值/报告口径全部来自同目录 gate_defs.py（单一事实源）。本模块实现
各断言的检查过程，并提供 CLI 与库 API 两种形态：

  # zh 侧（verify_* / build 流水线末步）
  python shared/verify_gate.py --client jp --apk out/nier-jp.apk \\
      --sidecar out/nier-jp.apk.manifest.json --out-json out/nier-jp.gate.json
  python shared/verify_gate.py --bin-e bin_zh_fix6.bin.e --expect-bin-e-name bin_zh_fix6.bin.e

  # bunker 侧（bunker/android/tools/verify_gate_zh.py 转调本模块）

适用性：给了 apk → A2/A4/A6/A7/A8/A9；给了 bin.e → A3/A5；给了 --manifest-dir
（或 --client）→ A1。未给目标的断言记 skip（不计入 fail）。

依赖：APK 域断言纯 stdlib；bin.e 域断言需 msgpack/lz4/pycryptodome（与
build_bin_e.py 同依赖面，缺依赖时该断言 fail 并注明）。产物只读。
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

SHARED = Path(__file__).resolve().parent
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

import gate_defs as G  # noqa: E402
import detect_client as DC  # noqa: E402

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
LIB_ENTRY = "lib/arm64-v8a/libil2cpp.so"
FONT_ENTRY_PREFIX = "assets/bin/Data/"


# ---------------------------------------------------------------- bin.e 域
def _ensure_bin_deps():
    """msgpack/lz4/pycryptodome（同 build_bin_e 依赖面）；附 toolpaths 提示路径。"""
    try:
        import lz4.block  # noqa: F401
        import msgpack  # noqa: F401
        from Crypto.Cipher import AES  # noqa: F401
        return
    except ImportError:
        pass
    cands = []
    tp = SHARED.parent / "jp-client" / "toolpaths.json"
    if tp.is_file():
        try:
            cfg = json.loads(tp.read_text(encoding="utf-8"))
            site = cfg.get("bin_e_site_packages")
            if site:
                cands.append(Path(site))
        except Exception:  # noqa: BLE001
            pass
    cands.append(Path(r"E:\NieRReincarnation\lunar-base\.venv\Lib\site-packages"))
    for c in cands:
        if c.is_dir() and (c / "msgpack").is_dir() and str(c) not in sys.path:
            sys.path.insert(0, str(c))
    try:
        import lz4.block  # noqa: F401
        import msgpack  # noqa: F401
        from Crypto.Cipher import AES  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            f"bin.e 断言需要 msgpack/lz4/pycryptodome（同 build_bin_e 依赖面）: {exc}")


def bin_e_view(path: Path):
    """AES-256-CBC 解密 + msgpack TOC → (toc, blob, raw_bytes)。只读。"""
    _ensure_bin_deps()
    import msgpack
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    raw = Path(path).read_bytes()
    key = bytes.fromhex("36436230313332314545356536624265")
    iv = bytes.fromhex("45666341656634434165356536446141")
    dec = unpad(AES.new(key, AES.MODE_CBC, IV=iv).decrypt(raw), 16)
    try:
        toc_raw = msgpack.unpackb(dec, raw=False, strict_map_key=False)
        blob = b""
    except msgpack.ExtraData as exc:
        toc_raw = exc.unpacked
        blob = exc.extra
    if not isinstance(toc_raw, dict):
        raise ValueError(f"TOC 不是 map，而是 {type(toc_raw).__name__}")
    toc = {str(k): (int(v[0]), int(v[1])) for k, v in toc_raw.items()}
    return toc, blob, raw


def _decode_part(part: bytes) -> bytes:
    """LZ4 ext（code 99）解压；否则原样。同 build_bin_e.decode_table_part。"""
    _ensure_bin_deps()
    import lz4.block
    import msgpack
    obj = msgpack.unpackb(part, raw=True)
    if isinstance(obj, msgpack.ExtType) and obj.code == 99:
        ext = obj.data
        tag = ext[0]
        if tag == 0xD2:
            ulen = struct.unpack(">i", ext[1:5])[0]
            data = ext[5:]
        elif tag == 0xCE:
            ulen = struct.unpack(">I", ext[1:5])[0]
            data = ext[5:]
        elif tag == 0xD1:
            ulen = struct.unpack(">h", ext[1:3])[0]
            data = ext[3:]
        elif tag == 0xCD:
            ulen = struct.unpack(">H", ext[1:3])[0]
            data = ext[3:]
        elif tag <= 0x7F:
            ulen = tag
            data = ext[1:]
        else:
            raise ValueError(f"LZ4 ext 头意外 tag 0x{tag:02x}")
        return lz4.block.decompress(data, uncompressed_size=ulen)
    return part


def check_bin_e_text_zh(bin_e: Path, require_zh: bool = True):
    """A5：5 文本表在位 + 逐表 CJK + （require_zh 时）聚合简体标记 ≥20。"""
    try:
        toc, blob, _ = bin_e_view(bin_e)
    except Exception as exc:  # noqa: BLE001 — 解析失败即门拒
        return "fail", f"bin.e 解析失败（改 1 字节/损坏即拒）: {exc}", {"parsed": False}
    per = {}
    missing = []
    total_cjk = 0
    total_zh = 0
    for name in G.TEXT_TABLES:
        if name not in toc:
            missing.append(name)
            continue
        off, length = toc[name]
        raw_part = blob[off:off + length]
        try:
            data = _decode_part(raw_part)
        except Exception:  # noqa: BLE001
            data = raw_part
        cjk = len(re.findall(G.CJK_RE, data))
        zh = sum(data.count(m.encode("utf-8")) for m in G.ZH_MARKERS)
        per[name] = {"cjk": cjk, "zh_markers": zh}
        total_cjk += cjk
        total_zh += zh
    detail = {"tables": per, "missing_tables": missing,
              "total_cjk": total_cjk, "total_zh_markers": total_zh,
              "table_count": len(toc)}
    if missing:
        return "fail", f"文本表缺表: {missing}（缺表即拒）", detail
    no_cjk = [n for n, v in per.items() if v["cjk"] < 1]
    if no_cjk:
        return "fail", f"文本表无 CJK: {no_cjk}", detail
    if require_zh and total_zh < 20:
        return "fail", (f"简体标记不足（zh 强度）: {total_zh} < 20 "
                        f"（5 表 CJK={total_cjk}）"), detail
    note = f"5/5 表在位 CJK={total_cjk} 简体标记={total_zh}"
    return "pass", note, detail


def check_bin_e_filename(bin_e: Path, expect_name: str | None):
    """A3：bin.e 文件名不变（输出名==输入名；单文件时==期望名）。"""
    name = Path(bin_e).name
    if not name.endswith(".bin.e"):
        return "fail", f"文件名非 .bin.e: {name}", {"name": name}
    if expect_name is not None and name != expect_name:
        return "fail", f"文件名不符: {name!r} != 期望 {expect_name!r}（不变量）", \
            {"name": name, "expect": expect_name}
    return "pass", f"文件名不变量 OK: {name}", {"name": name, "expect": expect_name}


# ---------------------------------------------------------------- APK 域
def apk_cert_sha256(apk: Path) -> str | None:
    """纯 python 解析 APK 签名块 v2/v3 证书 sha256（无需 java/apksigner）。"""
    with open(apk, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 66000))
        tail = f.read()
        idx = tail.rfind(b"PK\x05\x06")
        if idx < 0:
            return None
        cd_off = struct.unpack_from("<I", tail, idx + 16)[0]
        f.seek(cd_off - 24)
        hdr = f.read(24)
        block_size = struct.unpack_from("<Q", hdr, 0)[0]
        if hdr[8:] != b"APK Sig Block 42":
            return None
        block_start = cd_off - block_size - 8
        f.seek(block_start)
        data = f.read(block_size + 8)
        pairs = data[8:]
        end = len(data) - 24
        pos = 0
        while pos < end:
            pair_len = struct.unpack_from("<Q", pairs, pos)[0]
            pair_id = struct.unpack_from("<I", pairs, pos + 8)[0]
            value = pairs[pos + 12:pos + 8 + pair_len]
            if pair_id in (0x7109871A, 0xF05368C0):
                seq_len = struct.unpack_from("<I", value, 0)[0]
                sp = 4
                while sp < 4 + seq_len:
                    signer_len = struct.unpack_from("<I", value, sp)[0]
                    signer = value[sp + 4:sp + 4 + signer_len]
                    sp += 4 + signer_len
                    sd_len = struct.unpack_from("<I", signer, 0)[0]
                    sd = signer[4:4 + sd_len]
                    dig_len = struct.unpack_from("<I", sd, 0)[0]
                    p = 4 + dig_len
                    certs_len = struct.unpack_from("<I", sd, p)[0]
                    cp = p + 4
                    cend = cp + certs_len
                    while cp < cend:
                        c_len = struct.unpack_from("<I", sd, cp)[0]
                        cert = sd[cp + 4:cp + 4 + c_len]
                        return G.sha256_bytes(cert)
                        # 首张证书即签名证书
            pos += 8 + pair_len
    return None


def check_cert_assertion(apk: Path, client: str):
    """A2：签名证书 sha256 == 客户端期望。"""
    expect = G.CLIENTS[client]["cert_sha256"]
    got = apk_cert_sha256(apk)
    if got is None:
        return "fail", "无法解析签名块证书", {"expect": expect, "actual": None}
    if got != expect:
        return "fail", f"证书指纹不符: {got[:16]}… != 期望 {expect[:16]}…", \
            {"expect": expect, "actual": got}
    return "pass", f"证书指纹 OK: {got[:16]}…", {"expect": expect, "actual": got}


def check_font_payload(apk: Path, client: str, mode: str = "zh"):
    """A6：字体 payload 四条目在位且 sha256 == 期望（zh=汉化 payload；known=zh 或原版）。"""
    zh = G.CLIENTS[client]["fonts_zh"]
    orig = G.FONTS_ORIGINAL
    got = {}
    problems = []
    with zipfile.ZipFile(apk) as zf:
        names = set(zf.namelist())
        for n in G.FONT_NAMES:
            entry = FONT_ENTRY_PREFIX + n
            if entry not in names:
                problems.append(f"缺条目 {n[:8]}")
                continue
            h = G.sha256_bytes(zf.read(entry))
            got[n] = h
            if h == zh.get(n):
                continue
            if mode == "known" and h == orig.get(n):
                continue
            problems.append(f"{n[:8]} sha 不符: {h[:16]}…")
    detail = {"mode": mode, "entries": {k[:8]: v[:16] for k, v in got.items()}}
    if problems:
        return "fail", f"字体 payload 四条目: {'; '.join(problems)}", detail
    which = "zh payload" if all(v == zh[k] for k, v in got.items()) else "原版"
    return "pass", f"字体 payload 四条目 OK（{which}）", detail


def check_fix3_strings(apk: Path, mode: str = "required"):
    """A7：fix3 汉化 spot 串原始字节命中（metadata + hashed TextAsset 域）。"""
    hits = {s: 0 for s in G.FIX3_SPOTS}
    scanned = 0
    with zipfile.ZipFile(apk) as zf:
        for name in zf.namelist():
            if name == META_ENTRY or re.fullmatch(r"assets/bin/Data/[0-9a-f]{32}", name):
                try:
                    data = zf.read(name)
                except Exception:  # noqa: BLE001
                    continue
                scanned += 1
                for s in G.FIX3_SPOTS:
                    hits[s] += data.count(s.encode("utf-8"))
    missing = [s for s, c in hits.items() if c < 1]
    detail = {"hits": hits, "scanned_entries": scanned}
    if missing:
        if mode == "optional":
            return "skip", f"fix3 串缺 {missing}（本产物未含 fix3 集，optional）", detail
        return "fail", f"fix3 串缺: {missing}", detail
    return "pass", f"fix3 串 {len(hits)}/{len(hits)} 全命中（{scanned} entries）", detail


def check_region_match(apk: Path, client: str):
    """A8：axml 包名 == 客户端期望包名（detect_client 同口径）。"""
    expect = G.CLIENTS[client]["package"]
    try:
        pkg = DC.apk_package_name(Path(apk))
    except Exception as exc:  # noqa: BLE001
        return "fail", f"包名解析失败: {exc}", {"expect": expect, "actual": None}
    if pkg != expect:
        return "fail", f"包名不符: {pkg!r} != 期望 {expect!r}", \
            {"expect": expect, "actual": pkg}
    return "pass", f"region 匹配 OK: {pkg}", {"expect": expect, "actual": pkg}


def check_rva_table_client(apk: Path, client: str):
    """A9：RVA 表按客户端选对（RVA-AUTOSELECT 产物验证清单并入项）。

    (a) libil2cpp.so 大小 == 客户端事实表，且 detect_client.region_for_lib_size
        同口径判回同一 client（RVA-AUTOSELECT 任务的选表交叉核对）；
    (b) 客户端补丁表逐站点字节命中（期望12/12 jp｜13/13 en）；
    (c) 反向核对：另一客户端表的哨兵站点不命中（两表不可互换）。
    """
    sites = G.CLIENTS[client]["rva_sites"]
    other = "en" if client == "jp" else "jp"
    other_sites = G.CLIENTS[other]["rva_sites"][:3]
    detail = {"client": client, "sites": [], "other_sentinels": []}
    try:
        with zipfile.ZipFile(apk) as zf, zf.open(LIB_ENTRY) as so:
            so.seek(0, 2)
            size = so.tell()
            detail["libil2cpp_size"] = size
            if size != G.CLIENTS[client]["libil2cpp_size"]:
                return "fail", (f"libil2cpp.so 大小不符: {size} != "
                                f"{G.CLIENTS[client]['libil2cpp_size']}"), detail
            mapped = DC.region_for_lib_size(size)
            detail["region_for_lib_size"] = mapped
            if mapped != client:
                return "fail", (f"so 大小→region_for_lib_size 判为 {mapped!r}，"
                                f"与期望 client {client!r} 不符（选表矛盾）"), detail
            matched = 0
            for rva, exp in sites:
                so.seek(rva)
                b = so.read(8)
                w = struct.unpack("<I", b[:4])[0]
                if isinstance(exp, str):
                    ok = b[:len(exp) // 2].hex() == exp
                else:
                    _, rd, ret_after = exp
                    ok = (w & 0xFFE0001F) == (0x52800000 | rd)
                    if ok and ret_after:
                        ok = struct.unpack("<I", b[4:8])[0] == 0xD65F03C0
                matched += int(ok)
                detail["sites"].append({"rva": hex(rva), "match": bool(ok),
                                        "got": b.hex()[:16]})
            detail["sites_matched"] = f"{matched}/{len(sites)}"
            cross = 0
            for rva, exp in other_sites:
                if isinstance(exp, str):
                    so.seek(rva)
                    if so.read(len(exp) // 2).hex() == exp:
                        cross += 1
            detail["other_sentinels_matched"] = cross
    except KeyError:
        return "fail", f"产物缺 {LIB_ENTRY}", detail
    if matched != len(sites):
        return "fail", (f"客户端补丁表站点命中 {matched}/{len(sites)}（期望 "
                        f"{G.CLIENTS[client]['rva_table_version']}）"), detail
    if cross:
        return "fail", f"另一客户端表哨兵命中 {cross}/3（两表不可互换）", detail
    return "pass", (f"RVA 表选对 OK: {matched}/{len(sites)} 站点命中，"
                    f"交叉表 0/{len(other_sites)}，so 大小→{mapped}"), detail


def check_rva_table_version(sidecar: Path | None, client: str, computed: str | None = None):
    """A4：sidecar rva_table_version 槽位在位；填值须==客户端期望（占位期注明）。"""
    expect = G.CLIENTS[client]["rva_table_version"]
    if sidecar is None or not Path(sidecar).is_file():
        return "skip", "无 manifest sidecar（rva_table_version 槽位不适用）", {}
    sc = json.loads(Path(sidecar).read_text(encoding="utf-8"))
    slot = sc.get("rva_table_version")
    if slot is None:
        return "fail", "sidecar 缺 rva_table_version 槽位", {"expect": expect}
    detail = {"slot": slot, "expect": expect, "computed": computed}
    if slot.get("placeholder"):
        note = "占位（RVA-AUTOSELECT 定版后填值）"
        if computed and computed != expect:
            return "fail", f"槽位占位但实测版本 {computed} != 期望 {expect}", detail
        return "pass", f"rva_table_version 槽位在位（{note}；期望 {expect}）", detail
    val = slot.get("value")
    if val != expect:
        return "fail", f"rva_table_version 值 {val!r} != 期望 {expect!r}", detail
    if computed and computed != val:
        return "fail", f"rva_table_version 值 {val!r} != 实测 {computed!r}", detail
    return "pass", f"rva_table_version OK: {val}", detail


def check_manifest_precheck(manifest_dir: Path):
    """A1：MANIFEST 预检（权威副本 items sha256 逐项核对，漂移即 fail）。"""
    manifest_dir = Path(manifest_dir)
    man_path = manifest_dir / "MANIFEST.json"
    if not man_path.is_file():
        return "fail", f"缺 MANIFEST.json: {man_path}", {}
    man = json.loads(man_path.read_text(encoding="utf-8"))
    bad = []
    for item in man.get("items", []):
        p = manifest_dir / item["path"]
        if not p.is_file():
            bad.append({"path": item["path"], "reason": "missing"})
            continue
        # 摘要对 LF 归一：Windows（autocrlf）检出为 CRLF、CI 为 LF，同一内容
        # 必须同摘要；MANIFEST.json 的期望值按同式生成，跨平台自洽。
        got = G.sha256_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
        if got != item["sha256"]:
            bad.append({"path": item["path"], "reason": "sha256",
                        "expected": item["sha256"][:16], "actual": got[:16]})
    detail = {"manifest": str(man_path), "items": len(man.get("items", [])), "bad": bad}
    if bad:
        return "fail", (f"MANIFEST 预检失败（{len(bad)} 项漂移）: "
                        + json.dumps(bad[:3], ensure_ascii=False)), detail
    return "pass", f"MANIFEST 预检 OK（{len(man.get('items', []))} items）", detail


# ---------------------------------------------------------------- 统一门
def detect_client_of(apk: Path) -> str:
    pkg = DC.apk_package_name(Path(apk))
    for key, v in G.CLIENTS.items():
        if v["package"] == pkg:
            return key
    raise SystemExit(f"未知客户端（包名不在门事实表）: {pkg!r}")


def run_gate(apk: Path | None = None, bin_e: Path | None = None,
             client: str | None = None, expect_bin_e_name: str | None = None,
             sidecar: Path | None = None, manifest_dir: Path | None = None,
             font_mode: str = "zh", fix3_mode: str = "required",
             require_zh_text: bool = True, gate_name: str = "unified",
             manifest: bool = True) -> G.GateReport:
    """跑适用断言，返回统一报告（nier-verify-gate/v1）。"""
    if apk is None and bin_e is None:
        raise SystemExit("run_gate: 需要 --apk 或 --bin-e")
    if apk is not None:
        client = client or detect_client_of(apk)
    if client is None:
        client = "jp"
    rep = G.GateReport(gate=gate_name, target={
        "client": client,
        "apk": str(Path(apk).resolve()) if apk else None,
        "bin_e": str(Path(bin_e).resolve()) if bin_e else None,
        "sidecar": str(Path(sidecar).resolve()) if sidecar else None,
    })

    # A1 MANIFEST 预检
    if manifest and manifest_dir is not None:
        s, d, det = check_manifest_precheck(manifest_dir)
        rep.add("manifest_precheck", s, d, actual=det)
    else:
        rep.add("manifest_precheck", "skip", "未给 --manifest-dir", None)

    if apk is not None:
        apk = Path(apk)
        s, d, det = check_cert_assertion(apk, client)
        rep.add("cert_assertion", s, d, expected=G.CLIENTS[client]["cert_sha256"],
                actual=det.get("actual"))
        s, d, det = check_font_payload(apk, client, mode=font_mode)
        rep.add("font_payload", s, d, actual=det)
        s, d, det = check_fix3_strings(apk, mode=fix3_mode)
        rep.add("fix3_strings", s, d, actual=det)
        s, d, det = check_region_match(apk, client)
        rep.add("region_match", s, d, expected=G.CLIENTS[client]["package"],
                actual=det.get("actual"))
        s, d, det = check_rva_table_client(apk, client)
        rep.add("rva_table_client", s, d,
                expected=G.CLIENTS[client]["rva_table_version"],
                actual=det.get("sites_matched"))
        computed = det.get("sites_matched")
        if sidecar is None:
            guess = Path(str(apk) + ".manifest.json")
            sidecar = guess if guess.is_file() else None
        s, d, det = check_rva_table_version(sidecar, client, computed=computed)
        rep.add("rva_table_version", s, d, expected=G.CLIENTS[client]["rva_table_version"],
                actual=det.get("slot"))
    else:
        for cid in ("cert_assertion", "font_payload", "fix3_strings",
                    "region_match", "rva_table_client", "rva_table_version"):
            rep.add(cid, "skip", "未给 --apk（本目标不适用）", None)

    if bin_e is not None:
        bin_e = Path(bin_e)
        s, d, det = check_bin_e_filename(bin_e, expect_bin_e_name)
        rep.add("bin_e_filename", s, d, expected=expect_bin_e_name,
                actual=det.get("name"))
        s, d, det = check_bin_e_text_zh(bin_e, require_zh=require_zh_text)
        rep.add("bin_e_text_zh", s, d, actual=det)
    else:
        rep.add("bin_e_filename", "skip", "未给 --bin-e（本目标不适用）", None)
        rep.add("bin_e_text_zh", "skip", "未给 --bin-e（本目标不适用）", None)
    return rep


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="L6 统一验证门（bunker/zh 两侧共用）")
    p.add_argument("--apk", type=Path, default=None, help="APK 产物（只读）")
    p.add_argument("--bin-e", type=Path, default=None, help="bin.e 产物（只读）")
    p.add_argument("--client", choices=("jp", "en"), default=None)
    p.add_argument("--expect-bin-e-name", default=None,
                   help="bin.e 文件名不变量期望名（默认 20240404193219.bin.e）")
    p.add_argument("--sidecar", type=Path, default=None,
                   help="manifest sidecar 路径（默认 <apk>.manifest.json）")
    p.add_argument("--manifest-dir", type=Path, default=None,
                   help="MANIFEST 预检目录（jp-client / en-client）")
    p.add_argument("--no-manifest", action="store_true", help="跳过 MANIFEST 预检")
    p.add_argument("--font-mode", choices=("zh", "known"), default="zh")
    p.add_argument("--fix3-mode", choices=("required", "optional"), default="required")
    p.add_argument("--no-require-zh-text", action="store_true",
                   help="bin.e 文本只要求 CJK（非 zh 交付物用）")
    p.add_argument("--gate-name", default="unified")
    p.add_argument("--out-json", type=Path, default=None)
    args = p.parse_args(argv)

    expect_name = args.expect_bin_e_name
    if expect_name is None and args.bin_e is not None:
        expect_name = "20240404193219.bin.e"
    manifest_dir = args.manifest_dir
    if manifest_dir is None and args.client and not args.no_manifest:
        manifest_dir = SHARED.parent / f"{args.client}-client"
        if not manifest_dir.is_dir():
            manifest_dir = None
    rep = run_gate(
        apk=args.apk, bin_e=args.bin_e, client=args.client,
        expect_bin_e_name=expect_name, sidecar=args.sidecar,
        manifest_dir=manifest_dir, font_mode=args.font_mode,
        fix3_mode=args.fix3_mode, require_zh_text=not args.no_require_zh_text,
        gate_name=args.gate_name, manifest=not args.no_manifest)
    for line in rep.render_lines():
        print(line)
    if args.out_json:
        rep.write_json(args.out_json)
        print(f"[{rep.gate}] report: {args.out_json}")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
