#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_defs.py — L6 统一验证门断言目录 + 报告口径（bunker 侧与 lunar-scripts-zh 侧共用）。

单一事实源（BUNKER-ADAPT-PLAN §2.4 双账本/验证门 + LUNARBASE-CHANGES §L6）：
两侧验证门共享本目录的断言定义与期望值，报告格式一致（pass/fail 逐项）。

断言目录（id → 名义/适用面）：

  A1 manifest_precheck    MANIFEST 预检      module   权威副本 items sha256 逐项核对
  A2 cert_assertion       证书断言           apk      签名块 v2/v3 证书 sha256 == 客户端期望
  A3 bin_e_filename       bin.e 文件名不变   bin_e    输出名==输入名（或==期望名）
  A4 rva_table_version    RVA 表版本位       apk      sidecar rva_table_version 槽位存在且一致
  A5 bin_e_text_zh        bin.e 文本表带 zh  bin_e    5 文本表在位 + 各带 CJK + 简体标记强度
  A6 font_payload         字体 payload 四条目 apk     4 字体条目 sha256 == 期望（zh/原版）
  A7 fix3_strings         fix3 串            apk      汉化 spot 串逐条命中（原始字节扫描）
  A8 region_match         region 匹配        apk      包名 == 客户端期望包名（detect_client 同口径）
  A9 rva_table_client     RVA 表按客户端选对 apk      so 大小→region_for_lib_size 一致 +
                                                      客户端补丁表逐站点字节命中（12/12 jp｜13/13 en）

RVA-AUTOSELECT 协同点：A9 合并「libil2cpp.so 大小交叉核对选 RVA 表」（shared/detect_client.py
region_for_lib_size 同口径，RVA-AUTOSELECT 任务的产物验证清单）与补丁站点字节清单；
A4 消费 manifest sidecar 的 rva_table_version 槽（该任务定版后填 12/12｜13/13，占位期按
placeholder 处理并在报告中明示）。

报告 schema：nier-verify-gate/v1 —— {schema, gate, target, checks:[{id,name,status,detail}], ok}
status ∈ pass | fail | skip；ok = 无 fail（skip 不计）。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "nier-verify-gate/v1"

# ---------------------------------------------------------------- 断言目录
CHECKS: dict[str, dict] = {
    "manifest_precheck": {
        "name": "MANIFEST 预检",
        "applies_to": "module",
        "description": "MANIFEST.json 权威副本 items sha256 逐项核对（漂移即 fail）",
    },
    "cert_assertion": {
        "name": "证书断言",
        "applies_to": "apk",
        "description": "APK 签名块 v2/v3 证书 sha256 == 客户端期望指纹（纯 python 解析，无需 java）",
    },
    "bin_e_filename": {
        "name": "bin.e 文件名不变",
        "applies_to": "bin_e",
        "description": "输出名==输入名（成对交付硬性规则）；单文件时==期望名",
    },
    "rva_table_version": {
        "name": "RVA 表版本位",
        "applies_to": "apk",
        "description": "manifest sidecar rva_table_version 槽位在位；定版后值==客户端期望（jp 12/12｜en 13/13）",
    },
    "bin_e_text_zh": {
        "name": "bin.e 文本表带 zh",
        "applies_to": "bin_e",
        "description": "5 张文本表在位、逐表 CJK≥1、聚合简体标记 ≥20（zh 强度证据逐表计数）",
    },
    "font_payload": {
        "name": "字体 payload 四条目",
        "applies_to": "apk",
        "description": "assets/bin/Data 四字体条目 sha256 == 期望（zh payload 或原版，按 expect_zh_assets）",
    },
    "fix3_strings": {
        "name": "fix3 串",
        "applies_to": "apk",
        "description": "fix3 汉化 spot 串原始字节逐条命中（metadata + TextAsset 域）",
    },
    "region_match": {
        "name": "region 匹配",
        "applies_to": "apk",
        "description": "axml 包名 == 客户端期望包名（detect_client 同口径，未知即 fail）",
    },
    "rva_table_client": {
        "name": "RVA 表按客户端选对",
        "applies_to": "apk",
        "description": "libil2cpp.so 大小→region_for_lib_size 一致 + 客户端补丁表逐站点字节命中",
    },
}

# ---------------------------------------------------------------- 期望值（按客户端）
FONT_NAMES = (
    "6f937efa0660c47f59d5215d276b1cbb",
    "7089ac60979c94824ac549baab08cfa7",
    "ad1489eb70ff840d19d7d0841bcdd3a9",
    "550e0743a6b6344cfa3380b9a07f58b6",
)

# 原版游戏四字体条目（jp/en 共用同一原版内容）
FONTS_ORIGINAL = {
    "6f937efa0660c47f59d5215d276b1cbb": "6efd4e4238954b11d272a00936842f6c3d497053555ad2db884d8b6a55f86fe6",
    "7089ac60979c94824ac549baab08cfa7": "0874af6d09293f6a2f9bcee2238b6e2e072350e8e142553a8de826dcdf63f9ca",
    "ad1489eb70ff840d19d7d0841bcdd3a9": "e16c851c0e1d53a32dea4cdc836b0b8a9ab509cb94f0ccc480405893c1463144",
    "550e0743a6b6344cfa3380b9a07f58b6": "f128a23b0e1ca27abf0435fee733daba7e0201f6ad755e9d97cd445301a6b56a",
}

# zh 字体 payload（jp=payload2 / en=payload3；容器 sha256）
# 恢复原样口径重建后（源字体完整 cmap ∪ 请求集 − 控制符 + 原字体独有字形移植），
# 双端字节一致。
FONTS_ZH_JP = {
    "6f937efa0660c47f59d5215d276b1cbb": "b33053c0700670284dd2c0a7663f01d23a3beaa817b77c4bbd823b779cac4011",
    "7089ac60979c94824ac549baab08cfa7": "ea2a7f7c92e02d084bc75406c6a89f54ecf8a497891d451b4807cab86b7ae2dc",
    "ad1489eb70ff840d19d7d0841bcdd3a9": "1d740b08cdaf6428950e0a0fa092a12f80eaa51104dbf76f89d7049d380fee05",
    "550e0743a6b6344cfa3380b9a07f58b6": "6197fd2feaad22af8b542450ad99f45a14dc707954aa29083ec1d946e0a7e4be",
}
FONTS_ZH_EN = {
    "6f937efa0660c47f59d5215d276b1cbb": "b33053c0700670284dd2c0a7663f01d23a3beaa817b77c4bbd823b779cac4011",
    "7089ac60979c94824ac549baab08cfa7": "ea2a7f7c92e02d084bc75406c6a89f54ecf8a497891d451b4807cab86b7ae2dc",
    "ad1489eb70ff840d19d7d0841bcdd3a9": "1d740b08cdaf6428950e0a0fa092a12f80eaa51104dbf76f89d7049d380fee05",
    "550e0743a6b6344cfa3380b9a07f58b6": "6197fd2feaad22af8b542450ad99f45a14dc707954aa29083ec1d946e0a7e4be",
}

# fix3 汉化 spot 串（jp/en 产物均已实测命中；原始字节扫描用）
FIX3_SPOTS = ("公告", "联系我们", "数据继承", "关闭", "取消", "播放影片")
META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"

# bin.e 文本表（build_bin_e.TEXT_TABLES 同口径）
TEXT_TABLES = (
    "m_dokan_text",
    "m_gift_text",
    "m_navi_cut_in_text",
    "m_webview_mission_title_text",
    "m_webview_panel_mission_complete_flavor_text",
)
# 简体专用字形（日文汉字不用的字形）——zh 强度证据
ZH_MARKERS = "们说这过还个东车门页贝风气长么时从让对开闭关"
CJK_RE = rb"[\xe4-\xe9][\x80-\xbf]{2}"

# 客户端事实表（与 shared/detect_client.py REGIONS 同源字段 + 门专用期望）
CLIENTS: dict[str, dict] = {
    "jp": {
        "package": "com.square_enix.android_googleplay.nierspjp",
        "product_name": "nier-jp.apk",
        "cert_sha256": "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe",
        "fonts_zh": FONTS_ZH_JP,
        "libil2cpp_size": 126216336,
        "rva_table_version": "12/12",
        # patch_apk_jp.IL2CPP_PATCHES 逐站点（rva, 期望字节 hex 或 ("movz_w", rd)）
        "rva_sites": [
            (0x3622514, "000080d2c0035fd6"),   # ToNativeCredentials: mov x0,0; ret
            (0x274AC64, "e00301aac0035fd6"),   # HandleNet.Encrypt: mov x0,x1; ret
            (0x274AD64, "e00301aac0035fd6"),   # HandleNet.Decrypt
            (0x4B55B5C, "000080d2c0035fd6"),   # OctoManager.GetListAes
            (0x2834E9C, "20008052c0035fd6"),   # Purchaser.IsExistProduct: mov w0,1; ret
            (0x2838858, "1f2003d5"),           # DarkPurchase.Initialize cbz → nop
            (0x2839CCC, "1f2003d5"),           # PurchaseRealProductAsync cbz → nop
            (0x2839CD0, "19000014"),           # skip CheckPurchasingAlert: b +0x64
            (0x283C04C, "751600b4"),           # BuyProduct null controller: cbz x21
            (0x304F32C, "c0035fd6"),           # TitleScreen.InitializeMenuButton: ret
            (0x3F4A250, "c0035fd6"),           # Adjust.start: ret
            (0x3F4A574, "c0035fd6"),           # AdjustAndroid.Start: ret
        ],
    },
    "en": {
        "package": "com.square_enix.android_googleplay.nierspww",
        "product_name": "nier-en.apk",
        "cert_sha256": "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173",
        "fonts_zh": FONTS_ZH_EN,
        "libil2cpp_size": 127359872,
        "rva_table_version": "13/13",
        # patch_apk_en.IL2CPP_PATCHES：10 静态站点 + 3 端口覆盖站点（gp!=443 时追加）
        "rva_sites": [
            (0x35C8670, "000080d2c0035fd6"),   # ToNativeCredentials
            (0x279410C, "e00301aac0035fd6"),   # HandleNet.Encrypt
            (0x279420C, "e00301aac0035fd6"),   # HandleNet.Decrypt
            (0x4C27038, "000080d2c0035fd6"),   # OctoManager.GetListAes
            (0x2831CA8, "1f2003d5"),           # PurchaseRealProductAsync cbz → nop
            (0x282CE78, "20008052c0035fd6"),   # Purchaser.IsExistProduct
            (0x2834028, "751600b4"),           # BuyProduct: cbz x21
            (0x2831CAC, "19000014"),           # skip CheckPurchasingAlert: b +0x64
            (0x2830834, "1f2003d5"),           # Initialize cbz → nop
            (0x2F11900, "c0035fd6"),           # TitleScreen.InitializeMenuButton
            (0x361D548, ("movz_w", 0, True)),  # NetworkConfig.get_ServerPort: movz w0,#port; ret
            (0x2DEAF68, ("movz_w", 2, False)), # InitializeApiClient port override
            (0x2E1B278, ("movz_w", 20, False)),# CalculatorNetworking port override
        ],
    },
}

FONT_ENTRY_PREFIX = "assets/bin/Data/"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- 报告口径
@dataclass
class GateReport:
    """统一报告（nier-verify-gate/v1）：pass/fail 逐项。"""
    gate: str
    target: dict = field(default_factory=dict)
    checks: list = field(default_factory=list)

    def add(self, check_id: str, status: str, detail, expected=None, actual=None) -> None:
        assert status in ("pass", "fail", "skip"), status
        assert check_id in CHECKS, f"unknown check id: {check_id}"
        row = {"id": check_id, "name": CHECKS[check_id]["name"], "status": status, "detail": detail}
        if expected is not None:
            row["expected"] = expected
        if actual is not None:
            row["actual"] = actual
        self.checks.append(row)

    @property
    def ok(self) -> bool:
        return all(c["status"] != "fail" for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "gate": self.gate,
            "target": self.target,
            "checks": self.checks,
            "ok": self.ok,
            "summary": {
                "pass": sum(1 for c in self.checks if c["status"] == "pass"),
                "fail": sum(1 for c in self.checks if c["status"] == "fail"),
                "skip": sum(1 for c in self.checks if c["status"] == "skip"),
            },
        }

    def render_lines(self) -> list:
        """pass/fail 逐项文本行（两侧门同口径）。"""
        lines = []
        for c in self.checks:
            tag = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[c["status"]]
            lines.append(f"[{self.gate}] {tag}  {c['id']:<20} {c['name']} — {c['detail']}")
        s = self.to_dict()["summary"]
        lines.append(f"[{self.gate}] overall: {'PASS' if self.ok else 'FAIL'} "
                     f"(pass={s['pass']} fail={s['fail']} skip={s['skip']})")
        return lines

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
