#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""detect_client.py — 客户端自动识别（lunar-scripts-zh 双前端共用）。

按 **region 三元组**（axml 包名 + 文件字节数 + 文件 sha256）判定输入 APK 属于
JP 还是 EN 客户端，**fail-fast 未知客户端**（无默认分支、不猜测）：

| region | 包名（axml） | bytes | sha256 | 产物名 | 签名 key | 证书 SHA-256 |
|---|---|---|---|---|---|---|
| jp | com.square_enix.android_googleplay.nierspjp | 254,131,762 | 25b6326c…653609 | nier-jp.apk | jp-client/keys/nier-jp.keystore（nier / lunar-jp） | EE:C2:3B…98A2FE |
| en | com.square_enix.android_googleplay.nierspww | 263,571,029 | 9ded0797…c9209 | nier-en.apk | en-client/keys/nier-en.keystore（androiddebugkey / android） | 7D:79:2C…A4:A1:73 |

libil2cpp.so 3.7.1（APK 内 lib/arm64-v8a/）：jp=126,216,336 B / en=127,359,872 B（`libil2cpp_size`）。
bunker display_patch.c 的 detect_client 按「包名 / 清单 org.veritr1x.bunker.REGION meta / 本表三元组」
与 so 大小交叉核对选 RVA 表（region_for_lib_size 同口径），不一致 fail-fast 拒补丁。

判定流程（口径同 BUNKER-ADAPT-PLAN §3.2）：
  1. 包名判定（解包前）：解析 APK 内 AndroidManifest.xml（axml 二进制）的
     package 属性 → 匹配 REGIONS；未知即 SystemExit；
  2. 三元组硬断言：包名匹配后核对 bytes+sha256 与事实表一致——不符拒建
     （含「改 1 字节」篡改：sha256 必变 → fail-fast）；
  3. metadata 特征佐证（可选，verify_metadata_markers）：解包后按 metadata
     host 特征二次复核（JP=api.app.nierreincarnation.jp / EN=…com 等）；
  4. 产出留档：返回值含判定三元组 + 选择的前端/补丁集/产物名/key 证书，
     由流水线写入 evidence 与 manifest sidecar。

被 jp-client/build_jp_client.py 与 en-client/build_en_zh.py 调用：
  识别 → 选 key / 补丁集 / 产物名（未知 → SystemExit，不产出任何文件）。

用法（CLI 自测）：
  python shared/detect_client.py <apk>            # 打印判定 JSON，exit 0
  python shared/detect_client.py <apk> --expect jp  # 契约断言（region 不符即 exit 1）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

SHARED = Path(__file__).resolve().parent
ZH_ROOT = SHARED.parent                      # lunar-scripts-zh/

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"

# ---------------------------------------------------------------- REGIONS 事实表
REGIONS: dict[str, dict] = {
    "jp": {
        "region": "jp",
        "client": "jp",
        "package": "com.square_enix.android_googleplay.nierspjp",
        "bytes": 254131762,
        # lib/arm64-v8a/libil2cpp.so 3.7.1 文件大小（display_patch.c 运行时选表用，双表同源）
        "libil2cpp_size": 126216336,
        "sha256": "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609",
        "sha256_short": "25b6326c…653609",
        "product_name": "nier-jp.apk",
        "pipeline": "jp-client/build_jp_client.py",
        "patch_set": ["jp-client/patches/patch_apk_jp.py"],
        "keystore": "jp-client/keys/nier-jp.keystore",
        "ks_alias": "nier",
        "ks_pass": "lunar-jp",
        "cert_sha256": "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe",
        "cert_colon": "EE:C2:3B:E0:CB:20:5C:40:17:91:BE:3D:4B:82:E8:85:15:60:F5:C2:"
                      "AE:D3:EC:64:41:66:09:3D:3D:98:A2:FE",
        "metadata_markers": [
            "api.app.nierreincarnation.jp",   # metadata host 特征（JP=…jp）
            "2019.4.29f1",                    # network_config 资产特征
        ],
    },
    "en": {
        "region": "en",
        "client": "en",
        "package": "com.square_enix.android_googleplay.nierspww",
        "bytes": 263571029,
        # lib/arm64-v8a/libil2cpp.so 3.7.1 文件大小（display_patch.c 运行时选表用，双表同源）
        "libil2cpp_size": 127359872,
        "sha256": "9ded0797ee607b6892b531ba3a02f4c4510774f5fe098ccada78ccff881c9209",
        "sha256_short": "9ded0797…c9209",
        "product_name": "nier-en.apk",
        "pipeline": "en-client/build_en_zh.py",
        "patch_set": ["en-client/patches/patch_apk_en.py",
                      "en-client/patches/patch_auth_dynamic_en.py"],
        "keystore": "en-client/keys/nier-en.keystore",
        "ks_alias": "androiddebugkey",
        "ks_pass": "android",
        "cert_sha256": "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173",
        "cert_colon": "7D:79:2C:3C:FE:FD:73:22:37:64:20:6E:DE:BD:95:26:61:86:38:FF:"
                      "15:21:65:DF:5F:BE:CD:35:6A:A4:A1:73",
        "metadata_markers": [
            "api.app.nierreincarnation.com",  # metadata host 特征（EN=…com）
        ],
    },
}

PRODUCT_NAMES = {r: v["product_name"] for r, v in REGIONS.items()}


# ---------------------------------------------------------------- AXML（最小解析）
def _decode_u8_len(data: bytes, i: int) -> tuple[int, int]:
    b0 = data[i]
    if b0 & 0x80:
        return ((b0 & 0x7F) << 8) | data[i + 1], i + 2
    return b0, i + 1


def _decode_u16_len(data: bytes, i: int) -> tuple[int, int]:
    (c0,) = struct.unpack_from("<H", data, i)
    if c0 & 0x8000:
        (c1,) = struct.unpack_from("<H", data, i + 2)
        return ((c0 & 0x7FFF) << 16) | c1, i + 4
    return c0, i + 2


def parse_axml_strings(data: bytes, off: int) -> list[str]:
    """解析 ResStringPool 块（UTF-8 / UTF-16 双制式），返回字符串表。"""
    _typ, header_size, _size = struct.unpack_from("<HHI", data, off)
    str_count, _style_count, flags, strings_start, _styles_start = \
        struct.unpack_from("<IIIII", data, off + 8)
    utf8 = bool(flags & 0x100)
    out: list[str] = []
    base = off + strings_start
    for n in range(str_count):
        (rel,) = struct.unpack_from("<I", data, off + header_size + n * 4)
        i = base + rel
        if utf8:
            _chars, i = _decode_u8_len(data, i)
            blen, i = _decode_u8_len(data, i)
            out.append(data[i:i + blen].decode("utf-8", "replace"))
        else:
            clen, i = _decode_u16_len(data, i)
            out.append(data[i:i + clen * 2].decode("utf-16-le", "replace"))
    return out


def axml_package_name(axml: bytes) -> str | None:
    """从二进制 AndroidManifest.xml 提取 <manifest package="…">；失败返回 None。"""
    if len(axml) < 8:
        return None
    typ, header_size, _total = struct.unpack_from("<HHI", axml, 0)
    if typ != 0x0003:                      # RES_XML_TYPE
        return None
    strings: list[str] = []
    off = header_size
    while off + 8 <= len(axml):
        ctype, chsize, csize = struct.unpack_from("<HHI", axml, off)
        if csize < 8 or off + csize > len(axml):
            return None
        if ctype == 0x0001:                # RES_STRING_POOL_TYPE
            try:
                strings = parse_axml_strings(axml, off)
            except (struct.error, IndexError, UnicodeDecodeError):
                return None
        elif ctype == 0x0102 and strings:  # RES_XML_START_ELEMENT_TYPE
            # ResXMLTree_node(16B) + ResXMLTree_attrExt(20B) + attrs(20B each)
            if chsize < 16 or csize < 16 + 20:
                off += csize
                continue
            (_ns, name_idx, attr_start, attr_size, attr_count, _id, _cls, _sty) = \
                struct.unpack_from("<IIHHHHHH", axml, off + 16)
            if name_idx >= len(strings) or strings[name_idx] != "manifest":
                off += csize
                continue
            base = off + 16 + attr_start
            for a in range(attr_count):
                p = base + a * attr_size
                if p + 20 > off + csize:
                    break
                (_ans, aname, raw, _vsz, _res0, dtype, dval) = \
                    struct.unpack_from("<IIIHBBI", axml, p)
                if aname < len(strings) and strings[aname] == "package":
                    if raw != 0xFFFFFFFF and raw < len(strings):
                        return strings[raw]
                    if dtype == 0x03 and dval < len(strings):   # TYPE_STRING
                        return strings[dval]
                    return None
            return None
        off += csize
    return None


# ---------------------------------------------------------------- 文件事实
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def apk_package_name(apk: Path) -> str | None:
    with zipfile.ZipFile(apk) as zf:
        return axml_package_name(zf.read("AndroidManifest.xml"))


# ---------------------------------------------------------------- 识别主入口
class ClientDetectError(SystemExit):
    """fail-fast：未知客户端 / 三元组断言失败即拒建（SystemExit 语义）。"""

    def __init__(self, msg: str):
        super().__init__(f"[detect_client] {msg}")


def detect_client(apk: Path | str, expect: str | None = None) -> dict:
    """识别输入 APK 客户端（region 三元组硬断言，fail-fast）。

    返回判定档案 dict（含三元组、产物名、key、补丁集、证书）；任何不符
    抛 ClientDetectError（=SystemExit），流水线随之中止、不产出任何文件。

    expect: 可选契约断言——判定 region 必须等于 expect（如 jp-client 流水线
    传 "jp"），不符即 fail-fast（防误喂 EN 包给 JP 流水线）。
    """
    apk = Path(apk).resolve()
    if not apk.is_file():
        raise ClientDetectError(f"输入 APK 不存在: {apk}")

    size = apk.stat().st_size
    digest = sha256_file(apk)
    try:
        pkg = apk_package_name(apk)
    except Exception:  # noqa: BLE001 — 非 APK/损坏 zip 一律视为未知客户端
        pkg = None

    # 1) 包名判定（axml）
    matched = [r for r, v in REGIONS.items() if v["package"] == pkg]
    if not matched:
        raise ClientDetectError(
            f"未知客户端（包名不在 REGIONS）: package={pkg!r} "
            f"apk={apk} bytes={size} sha256={digest}")
    region = matched[0]
    info = dict(REGIONS[region])

    # 2) 三元组硬断言（bytes + sha256）
    if size != info["bytes"] or digest != info["sha256"]:
        problems = []
        if size != info["bytes"]:
            problems.append(f"bytes {size} != 期望 {info['bytes']}")
        if digest != info["sha256"]:
            problems.append(f"sha256 {digest} != 期望 {info['sha256']}")
        raise ClientDetectError(
            f"三元组硬断言失败（{region} 客户端，{' / '.join(problems)}）: {apk}")

    # 3) 契约断言（--expect / 流水线 region 自检）
    if expect and region != expect:
        raise ClientDetectError(
            f"region 矛盾即拒: 判定 region={region} 与流水线期望 {expect} 不符（{apk}）")

    info = {
        **info,
        "keystore_path": str((ZH_ROOT / info["keystore"]).resolve()),
        "patch_set_paths": [str((ZH_ROOT / p).resolve()) for p in info["patch_set"]],
        "detected": {
            "path": str(apk),
            "package": pkg,
            "bytes": size,
            "sha256": digest,
            "triple_ok": True,
        },
    }
    return info


def region_of_apk(apk: Path | str) -> str:
    """bunker region.py 同名口径：仅返回 region（"jp"/"en"），fail-fast 未知。"""
    return detect_client(apk)["region"]


def region_for_lib_size(size: int) -> str | None:
    """按 libil2cpp.so 文件大小判定 region（display_patch.c detect_client 同口径）。

    运行时选表的共享判定：bunker display_patch.c 的 detect_client 用同一套
    JP/EN 事实表（package / libil2cpp_size）做「包名 / 清单 REGION meta / 三元组
    与 so 大小」一致性交叉核对，不一致 fail-fast 拒补丁。未知大小返回 None。
    """
    for key, v in REGIONS.items():
        if v.get("libil2cpp_size") == size:
            return key
    return None


def key_for_region(region: str) -> dict:
    """按 region 选签名 key（jp→nier-jp / en→nier-en / 未知→fail-fast）。"""
    if region not in REGIONS:
        raise ClientDetectError(f"未知 region（无默认分支）: {region!r}")
    v = REGIONS[region]
    return {
        "region": region,
        "keystore": str((ZH_ROOT / v["keystore"]).resolve()),
        "alias": v["ks_alias"],
        "pass": v["ks_pass"],
        "cert_sha256": v["cert_sha256"],
        "cert_colon": v["cert_colon"],
    }


def product_name_for_region(region: str) -> str:
    """按 region 选产物名（jp→nier-jp.apk / en→nier-en.apk）。"""
    if region not in REGIONS:
        raise ClientDetectError(f"未知 region（无默认分支）: {region!r}")
    return REGIONS[region]["product_name"]


def verify_metadata_markers(region: str, meta_blob: bytes) -> dict:
    """二级复核（可选）：metadata host 特征佐证（解包后调用）。"""
    markers = REGIONS.get(region, {}).get("metadata_markers", [])
    hits = {m: (m.encode("utf-8") in meta_blob) for m in markers}
    return {"region": region, "markers": hits, "ok": all(hits.values())}


def verify_apk_package(apk: Path | str, region: str) -> dict:
    """对**成品/输入** APK 做包名级 region 自检（不解包）。"""
    pkg = apk_package_name(Path(apk))
    ok = pkg == REGIONS[region]["package"]
    return {"region": region, "expected_package": REGIONS[region]["package"],
            "actual_package": pkg, "ok": ok}


# ---------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description="客户端自动识别（region 三元组硬断言）")
    ap.add_argument("apk", help="输入 APK")
    ap.add_argument("--expect", choices=sorted(REGIONS), default=None,
                    help="契约断言：判定 region 必须等于该值")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    try:
        info = detect_client(args.apk, expect=args.expect)
    except ClientDetectError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    printable = {k: v for k, v in info.items()}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
