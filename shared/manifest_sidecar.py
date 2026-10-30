#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manifest_sidecar.py — 产物 manifest sidecar 生成器（lunar-scripts-zh 双前端共用）。

每产物附 `<产物名>.manifest.json`（命名契约：产物名 nier-jp.apk → sidecar
`nier-jp.apk.manifest.json`），记录（BUNKER-ADAPT-PLAN §2.6 / §9.1 契约字段）：

* **region 三元组**     判定包名 + 期望 bytes/sha256 + 实测三元组（triple_ok）
* **sha256 / size**    产物 APK 的 sha256 与字节数
* **签名证书指纹**     apksigner 实测证书 SHA-256 + 与 region 预期比对结果
* **补丁计数**         fix3/fix3l/fix4 串计数、私服 IP 命中、字体/菜单注入计数
* **验证门结果**       各验证门 key→bool + 总 ok + 验证报告路径
* **构建时间**         build_time / generated_at
* **RVA 表版本占位**   rva_table_version（占位字段，定版后填表版本）
* **输入 APK sha**     input_apk.sha256（原版输入未改动断言的基线）

schema = "nier-product-manifest/v1"。
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

SCHEMA = "nier-product-manifest/v1"

# RVA 表版本占位（L3a 契约字段；RVA 表定版后填 jp:12/12 | en:13/13 表版本号）
RVA_TABLE_VERSION_PLACEHOLDER = {
    "value": None,
    "placeholder": True,
    "note": "RVA 表版本占位（L3a 契约字段；libil2cpp RVA 表定版后填版本号，"
            "JP=12/12 / EN=13/13 口径见 BUNKER-ADAPT-PLAN §3.1）",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def build_sidecar(
    product_apk: Path,
    *,
    region_info: dict,
    input_apk: Path | None,
    cert_sha256: str | None,
    patch_counts: dict,
    verify_gates: dict,
    verify_report: Path | None = None,
    build_started_at: str | None = None,
    bin_e: dict | None = None,
    extra: dict | None = None,
) -> dict:
    """组装 sidecar dict（不落盘；write_sidecar 落盘）。"""
    product_apk = Path(product_apk)
    detected = region_info.get("detected", {})
    expected_cert = region_info.get("cert_sha256")
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    sidecar = {
        "schema": SCHEMA,
        "generated_at": now,
        "build_time": build_started_at or now,
        "product": {
            "name": product_apk.name,
            "path": str(product_apk.resolve()),
            "bytes": product_apk.stat().st_size,
            "sha256": sha256_file(product_apk),
        },
        "region": {
            "client": region_info.get("region"),
            "package": region_info.get("package"),
            "triple": {
                "package": region_info.get("package"),
                "expected_bytes": region_info.get("bytes"),
                "expected_sha256": region_info.get("sha256"),
                "detected_package": detected.get("package"),
                "detected_bytes": detected.get("bytes"),
                "detected_sha256": detected.get("sha256"),
                "triple_ok": bool(detected.get("triple_ok")),
            },
            "product_name_contract": region_info.get("product_name"),
            "pipeline": region_info.get("pipeline"),
            "patch_set": region_info.get("patch_set"),
        },
        "input_apk": {
            "path": str(Path(input_apk).resolve()) if input_apk else None,
            "sha256": detected.get("sha256") or
                      (sha256_file(Path(input_apk)) if input_apk and Path(input_apk).is_file() else None),
            "bytes": detected.get("bytes"),
        },
        "signing": {
            "keystore": region_info.get("keystore_path") or region_info.get("keystore"),
            "alias": region_info.get("ks_alias"),
            "cert_sha256": cert_sha256,
            "expected_cert_sha256": expected_cert,
            "cert_matches_expected": (cert_sha256 == expected_cert) if cert_sha256 else None,
            "cert_colon": region_info.get("cert_colon"),
        },
        "patch_counts": patch_counts,
        "verify_gates": verify_gates,
        "verify_report": str(Path(verify_report).resolve()) if verify_report else None,
        "rva_table_version": dict(RVA_TABLE_VERSION_PLACEHOLDER),
        "bin_e": bin_e,
    }
    if extra:
        sidecar["extra"] = extra
    return sidecar


def write_sidecar(product_apk: Path, sidecar: dict) -> Path:
    """落盘 `<产物名>.manifest.json`（与产物同目录），返回 sidecar 路径。"""
    product_apk = Path(product_apk)
    out = product_apk.parent / (product_apk.name + ".manifest.json")
    out.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def verify_sidecar(sidecar_path: Path, product_apk: Path | None = None) -> dict:
    """sidecar 自检：schema/字段在位 + 产物 sha/size 一致 + 证书断言。"""
    sidecar_path = Path(sidecar_path)
    problems: list[str] = []
    if not sidecar_path.is_file():
        return {"ok": False, "problems": [f"sidecar 不存在: {sidecar_path}"]}
    sc = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if sc.get("schema") != SCHEMA:
        problems.append(f"schema 不符: {sc.get('schema')!r}")
    for key in ("product", "region", "input_apk", "signing", "patch_counts",
                "verify_gates", "build_time", "rva_table_version"):
        if key not in sc:
            problems.append(f"缺字段: {key}")
    prod = sc.get("product", {})
    if product_apk is not None:
        product_apk = Path(product_apk)
        got = sha256_file(product_apk)
        if prod.get("sha256") != got:
            problems.append(f"产物 sha256 不符: sidecar={prod.get('sha256')} actual={got}")
        if prod.get("bytes") != product_apk.stat().st_size:
            problems.append(f"产物 size 不符: sidecar={prod.get('bytes')} "
                            f"actual={product_apk.stat().st_size}")
    signing = sc.get("signing", {})
    if signing.get("cert_sha256") and signing.get("expected_cert_sha256"):
        if signing.get("cert_sha256") != signing.get("expected_cert_sha256"):
            problems.append("证书指纹与 region 预期不符")
    gates = sc.get("verify_gates", {}) or {}
    if gates.get("ok") is False:
        problems.append("verify_gates.ok=false（验证门未全过）")
    return {"ok": not problems, "problems": problems, "sidecar": sc}
