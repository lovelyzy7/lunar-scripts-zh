#!/usr/bin/env python3
"""probe_bundle_repack.py — NieR Re[in]carnation 文本 assetbundle 写回 PoC 工具。

角色：验证 "解密 octo 文本包 -> 改 TextAsset 文本 -> 重存 UnityFS -> 重新加密 ->
用 lunar-base 现有读取器读回逐 key 校验" 这条链路是否可行。

本脚本只操作显式指定的拷贝文件；不会改写 lunar-tear/server 下的原始文件。
加密/解密/SerializedFile 解析复用 lunar-base 已验证实现（--lunar-base 指向
lunar-base 根目录，默认 <repo>/lunar-base）；UnityFS 重存使用 UnityPy。

依赖：
  * python: zh-l10n/.venv/Scripts/python.exe（Python 3.14 + UnityPy 1.25.4）
  * lunar-base/.venv 中有 lz4（本脚本直接 import extract_names 时需要）
  注：本脚本也可以只用 lunar-base/.venv 运行 inspect/verify，但 repack 需要 UnityPy。

子命令（详细示例见 --help 与 A-assetbundle-writeback.md）：
  inspect   打印 bundle 头部/流/TextAsset 概况，可选导出 key:value
  repack    对 TextAsset 应用文本编辑（改值/追加 key），重存 + 重加密 + 进程内校验
  verify    独立进程校验：只用 lunar-base 读取器读回一个已写出的 .assetbundle
  roundtrip 批量回环测试：解密->UnityPy 重存->加密->读回，比较每个 TextAsset 文本
  selftest  一键复现完整 PoC（默认样本 ui_0130310），产物写入 work/repack/

用法示例：
  python probe_bundle_repack.py inspect \
      --bundle "lunar-tear/server/assets/revisions/0/assetbundle/text/ja/ui/ui_0130310.assetbundle"

  python probe_bundle_repack.py repack \
      --bundle ".../ja/ui/ui_0130310.assetbundle" \
      --out work/repack/out/ja/ui/ui_0130310.assetbundle \
      --edits work/repack/edits_ui_0130310.json --report work/repack/logs/repack_ui_0130310.json

  python probe_bundle_repack.py verify \
      --bundle work/repack/out/ja/ui/ui_0130310.assetbundle \
      --edits work/repack/edits_ui_0130310.json

  python probe_bundle_repack.py roundtrip --lang ja --limit 200 \
      --json-out work/repack/logs/roundtrip_ja_200.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # E:\NieRReincarnation
DEFAULT_LUNAR_BASE = REPO_ROOT / "lunar-base"
DEFAULT_TEXT_ROOT = (
    REPO_ROOT
    / "lunar-tear"
    / "server"
    / "assets"
    / "revisions"
    / "0"
    / "assetbundle"
    / "text"
)
DEFAULT_WORKDIR = REPO_ROOT / "zh-l10n" / "work" / "repack"


# ---------------------------------------------------------------------------
# lunar-base 读取器/加解密接入
# ---------------------------------------------------------------------------
def _lunar_modules(lunar_base: Path):
    """import lunar-base 的 extract_names 与 assetbundle_crypt/encrypt_assetbundle。"""
    for sub in ("tools", "scripts/assetbundles"):
        path = str(lunar_base / sub)
        if path not in sys.path:
            sys.path.insert(0, path)
    import extract_names as reader  # noqa: E402
    from assetbundle_crypt import derive_mask_name, string_to_mask_bytes  # noqa: E402
    from encrypt_assetbundle import encrypt_bundle  # noqa: E402

    return reader, derive_mask_name, string_to_mask_bytes, encrypt_bundle


def decrypt_file(path: Path, lunar_base: Path, mask_name: str | None = None) -> tuple[bytes, str]:
    reader, derive_mask_name, _, _ = _lunar_modules(lunar_base)
    raw = path.read_bytes()
    mask = mask_name or derive_mask_name(str(path))
    if not mask:
        raise SystemExit(f"cannot derive octo mask name from path: {path}")
    decrypted = reader.decrypt_text_bundle(raw, mask)
    if decrypted[:7] != b"UnityFS":
        raise SystemExit(
            f"decrypt failed: decrypted header is {decrypted[:8]!r}, expected b'UnityFS'\n"
            f"  file={path}\n  mask={mask}"
        )
    return decrypted, mask


def encrypt_bytes(
    raw_unityfs: bytes,
    mask_name: str,
    lunar_base: Path,
    original_first_byte: int = 0x32,
) -> bytes:
    """按原文件格式重新加密（保留 octo 版本字节：
    0x31=v1 仅加密头部 256B；0x32=v1full 全文件；0x55=未加密裸 UnityFS）。"""
    _, _, _, encrypt_bundle = _lunar_modules(lunar_base)
    if original_first_byte == 0x55:
        return raw_unityfs
    version = 0x31 if original_first_byte == 0x31 else 0x32
    return encrypt_bundle(raw_unityfs, mask_name, version=version)


# ---------------------------------------------------------------------------
# UnityFS / SerializedFile 观察
# ---------------------------------------------------------------------------
def parse_unityfs_header(raw: bytes) -> dict[str, Any]:
    """解析 UnityFS 头部字段（与 extract_names.extract_bundle_streams 同源规则）。"""

    class R:
        def __init__(self, data: bytes) -> None:
            self.d = data
            self.p = 0

        def cstr(self) -> str:
            end = self.d.index(0, self.p)
            value = self.d[self.p : end].decode("utf-8", "replace")
            self.p = end + 1
            return value

        def u32(self) -> int:
            import struct

            value = struct.unpack(">I", self.d[self.p : self.p + 4])[0]
            self.p += 4
            return value

        def i64(self) -> int:
            import struct

            value = struct.unpack(">q", self.d[self.p : self.p + 8])[0]
            self.p += 8
            return value

    r = R(raw)
    header: dict[str, Any] = {"signature": r.cstr(), "format_version": r.u32()}
    header["unity_player_version"] = r.cstr()
    header["unity_engine_version"] = r.cstr()
    header["bundle_size_field"] = r.i64()
    header["blocks_info_compressed_size"] = r.u32()
    header["blocks_info_uncompressed_size"] = r.u32()
    flags = r.u32()
    header["flags"] = flags
    header["blocks_info_compression"] = flags & 0x3F
    header["blocks_at_end"] = bool(flags & 0x40)
    header["block_info_at_end"] = bool(flags & 0x80)
    if header["format_version"] >= 7:
        r.p = (r.p + 15) & ~15
    header["blocks_info_offset"] = r.p
    return header


def unitypy_env(raw_unityfs: bytes):
    import UnityPy  # 延迟导入：inspect/verify 不需要

    env = UnityPy.load(raw_unityfs)
    bundle_file = next(iter(env.files.values()))
    return env, bundle_file


def parse_blocks_info(raw: bytes, lunar_base: Path) -> dict[str, Any]:
    """解析 UnityFS 数据块表 + 目录节点表。"""
    reader, _, _, _ = _lunar_modules(lunar_base)
    header = parse_unityfs_header(raw)
    import struct as _struct

    offset = header["blocks_info_offset"]
    compressed = raw[offset : offset + header["blocks_info_compressed_size"]]
    compression = header["blocks_info_compression"]
    data = compressed
    if compression in (2, 3):
        data = reader.decompress_lz4(compressed, header["blocks_info_uncompressed_size"])

    class R:
        def __init__(self, buf: bytes) -> None:
            self.b = buf
            self.p = 0

        def u32(self) -> int:
            value = _struct.unpack(">I", self.b[self.p : self.p + 4])[0]
            self.p += 4
            return value

        def u16(self) -> int:
            value = _struct.unpack(">H", self.b[self.p : self.p + 2])[0]
            self.p += 2
            return value

        def u64(self) -> int:
            value = _struct.unpack(">Q", self.b[self.p : self.p + 8])[0]
            self.p += 8
            return value

        def read(self, n: int) -> bytes:
            value = self.b[self.p : self.p + n]
            self.p += n
            return value

        def cstring(self) -> str:
            end = self.b.index(0, self.p)
            value = self.b[self.p : end].decode("utf-8", "replace")
            self.p = end + 1
            return value

    r = R(data)
    r.read(16)  # uncompressedDataHash（本作全部为 0）
    count = r.u32()
    blocks = [(r.u32(), r.u32(), r.u16()) for _ in range(count)]
    node_count = r.u32()
    nodes = []
    for _ in range(node_count):
        node = {"offset": r.u64(), "size": r.u64(), "flags": r.u32()}
        node["path"] = r.cstring()
        nodes.append(node)
    return {
        "count": count,
        "max_uncompressed": max((block[0] for block in blocks), default=0),
        "uncompressed_total": sum(block[0] for block in blocks),
        "block_flags": sorted({block[2] for block in blocks}),
        "nodes": nodes,
    }


def describe_bundle(raw_unityfs: bytes, lunar_base: Path | None = None) -> dict[str, Any]:
    """结构化描述 UnityFS / SerializedFile 关键字段，用于对比重存前后是否兼容。

    只记录"客户端加载依赖的稳定结构"（版本号、目录节点、块数量、
    SerializedFile 版本/平台/对象清单/path_id），不记录字节偏移等易变细节。
    """
    env, bundle_file = unitypy_env(raw_unityfs)
    header = parse_unityfs_header(raw_unityfs)
    blocks_info = parse_blocks_info(raw_unityfs, lunar_base) if lunar_base is not None else {}
    result: dict[str, Any] = {
        "unityfs": {
            "format_version": header["format_version"],
            "unity_player_version": header["unity_player_version"],
            "unity_engine_version": header["unity_engine_version"],
            "flags": header["flags"],
        },
        "directory_nodes": blocks_info.get("nodes", []),
        "data_blocks": blocks_info,
        "serialized_files": [],
    }
    # BundleFile.files 里嵌套的是 SerializedFile（env.files 本身只有 BundleFile）
    serialized = [f for f in getattr(bundle_file, "files", {}).values() if type(f).__name__ == "SerializedFile"]
    for sf in serialized:
        obj_inventory = []
        for obj in sf.objects.values():
            obj_inventory.append(
                {
                    "type": obj.type.name,
                    "path_id": int(obj.path_id),
                }
            )
        sf_header = getattr(sf, "header", None)
        sf_info: dict[str, Any] = {
            "name": getattr(sf, "name", None),
            "format_version": getattr(sf_header, "version", None) if sf_header is not None else None,
            "target_platform": getattr(sf, "target_platform", None),
            "unity_version": getattr(sf, "unity_version", None),
            "enable_type_tree": bool(getattr(sf, "_enable_type_tree", False)),
            "big_id_enabled": getattr(sf, "big_id_enabled", None),
            "externals": [getattr(ext, "name", str(ext)) for ext in (getattr(sf, "externals", []) or [])],
            "object_count": len(sf.objects),
            "objects": sorted(obj_inventory, key=lambda item: item["path_id"]),
            "asset_bundle_name": None,
        }
        for obj in sf.objects.values():
            if obj.type.name == "AssetBundle":
                data = obj.read()
                sf_info["asset_bundle_name"] = getattr(data, "m_Name", None)
                sf_info["asset_bundle_assets"] = list(getattr(data, "m_AssetBundleNames", []) or [])
                break
        result["serialized_files"].append(sf_info)
    return result


def text_assets_of(env) -> list[tuple[Any, Any]]:
    """返回 [(ObjectReader, TextAsset实例)]，按 read() 顺序。"""
    result = []
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            result.append((obj, data))
    return result


def _as_text(m_script: Any) -> str:
    if isinstance(m_script, bytes):
        return m_script.decode("utf-8", "replace")
    return m_script


def parse_key_values(text: str) -> dict[str, str]:
    """文本包格式 == extract_names.parse_text_asset_lines：每行 key:value，# 开头跳过。"""
    entries: dict[str, str] = {}
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        separator = line.find(":")
        if separator <= 0:
            continue
        entries[line[:separator]] = line[separator + 1 :]
    return entries


def serialize_key_values(entries: dict[str, str]) -> str:
    return "\n".join(f"{k}:{v}" for k, v in entries.items())


def compare_structure(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """比较重存前后客户端加载所依赖的稳定结构字段。"""
    diffs: list[str] = []
    for key in ("format_version", "unity_engine_version", "flags"):
        if before["unityfs"].get(key) != after["unityfs"].get(key):
            diffs.append(f"unityfs.{key}: {before['unityfs'].get(key)!r} != {after['unityfs'].get(key)!r}")
    before_nodes = [(node.get("path"), node.get("flags")) for node in before["directory_nodes"]]
    after_nodes = [(node.get("path"), node.get("flags")) for node in after["directory_nodes"]]
    if before_nodes != after_nodes:
        diffs.append(f"directory_nodes: {before_nodes!r} != {after_nodes!r}")
    if len(before["serialized_files"]) != len(after["serialized_files"]):
        diffs.append(
            f"serialized_file_count: {len(before['serialized_files'])} != {len(after['serialized_files'])}"
        )
    for idx, (sf_before, sf_after) in enumerate(zip(before["serialized_files"], after["serialized_files"])):
        for key in (
            "name",
            "format_version",
            "target_platform",
            "unity_version",
            "enable_type_tree",
            "big_id_enabled",
            "externals",
            "object_count",
            "asset_bundle_name",
        ):
            if sf_before.get(key) != sf_after.get(key):
                diffs.append(f"serialized_files[{idx}].{key}: {sf_before.get(key)!r} != {sf_after.get(key)!r}")
        if sf_before.get("objects") != sf_after.get("objects"):
            diffs.append(f"serialized_files[{idx}].objects 清单/path_id 不一致")
    return {"ok": not diffs, "diffs": diffs}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------
def cmd_inspect(args: argparse.Namespace) -> int:
    lunar_base = Path(args.lunar_base)
    path = Path(args.bundle)
    raw = path.read_bytes()
    decrypted, mask = decrypt_file(path, lunar_base)
    reader, _, _, _ = _lunar_modules(lunar_base)
    streams = reader.extract_bundle_streams(decrypted)
    report = {
        "bundle": str(path),
        "on_disk_bytes": len(raw),
        "on_disk_first_byte": f"0x{raw[0]:02x}",
        "mask_name": mask,
        "unityfs": parse_unityfs_header(decrypted),
        "decrypted_bytes": len(decrypted),
        "streams": [len(s) for s in streams],
        "text_assets": [],
    }
    for stream in streams:
        try:
            assets = reader.extract_text_assets(stream)
        except (ValueError, EOFError):
            continue
        for name, text in assets:
            entries = parse_key_values(text)
            report["text_assets"].append(
                {
                    "name": name,
                    "chars": len(text),
                    "keys": len(entries),
                    "first_entries": dict(list(entries.items())[: args.sample]),
                }
            )
    if args.dump_keyvalues:
        out = Path(args.dump_keyvalues)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {}
        for stream in streams:
            try:
                for name, text in reader.extract_text_assets(stream):
                    payload[name] = parse_key_values(text)
            except (ValueError, EOFError):
                continue
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        report["dump_keyvalues"] = str(out)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# repack
# ---------------------------------------------------------------------------
def load_edits(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("edits json must be an object")
    payload.setdefault("text_asset", None)
    payload.setdefault("set", {})
    payload.setdefault("append", {})
    payload.setdefault("raw_append", None)
    payload.setdefault("raw_prepend", None)
    return payload


def apply_edits_to_text(text: str, edits: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """把 edits 应用到一份 TextAsset 文本，返回 (新文本, 变更摘要)。

    按"行"编辑以保留 `//` 注释行、空行和原始顺序 —— 这一点很重要：游戏文本包
    里含大量注释/分组行，整份 parse+serialize 会丢掉它们（实测 2582 字符 ->
    2458 字符），虽然游戏不读注释，但保留原格式可让 7012 个包的 diff 最小、
    也避免将来排查时看不出改了什么。
    """
    # 保留原始行结构与结尾换行风格
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines = lines[:-1]

    def line_key(line: str) -> str | None:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            return None
        sep = stripped.find(":")
        if sep <= 0:
            return None
        return stripped[:sep]

    index_by_key: dict[str, int] = {}
    for i, line in enumerate(lines):
        key = line_key(line)
        if key is not None and key not in index_by_key:
            index_by_key[key] = i

    changed_keys: list[str] = []
    added_keys: list[str] = []
    appended_lines: list[str] = []
    for key, value in edits.get("set", {}).items():
        new_line = f"{key}:{value}"
        if key in index_by_key:
            if lines[index_by_key[key]] != new_line:
                changed_keys.append(key)
            lines[index_by_key[key]] = new_line
        else:
            added_keys.append(key)
            appended_lines.append(new_line)
    for key, value in edits.get("append", {}).items():
        new_line = f"{key}:{value}"
        if key in index_by_key:
            if lines[index_by_key[key]] != new_line:
                changed_keys.append(key)
            lines[index_by_key[key]] = new_line
        else:
            added_keys.append(key)
            appended_lines.append(new_line)

    lines.extend(appended_lines)
    prepend = edits.get("raw_prepend")
    append = edits.get("raw_append")
    if prepend:
        lines.insert(0, prepend)
    if append:
        lines.append(append)
    new_text = "\n".join(lines)
    if trailing_newline:
        new_text += "\n"

    summary = {
        "old_chars": len(text),
        "new_chars": len(new_text),
        "changed_keys": changed_keys,
        "added_keys": added_keys,
        "total_keys_before": sum(1 for line in text.split("\n") if line_key(line) is not None),
        "total_keys_after": sum(1 for line in new_text.split("\n") if line_key(line) is not None),
    }
    return new_text, summary


def cmd_repack(args: argparse.Namespace) -> int:
    started = time.time()
    lunar_base = Path(args.lunar_base)
    bundle_path = Path(args.bundle)
    out_path = Path(args.out)
    edits = load_edits(Path(args.edits)) if args.edits else {"set": {}, "append": {}}
    target_asset = edits.get("text_asset")

    original_disk = bundle_path.read_bytes()
    decrypted, mask = decrypt_file(bundle_path, lunar_base)
    env, bundle_file = unitypy_env(decrypted)
    assets = text_assets_of(env)
    if not assets:
        raise SystemExit(f"no TextAsset in bundle: {bundle_path}")
    if target_asset:
        candidates = [(o, d) for (o, d) in assets if getattr(d, "m_Name", None) == target_asset]
        if not candidates:
            raise SystemExit(f"TextAsset not found: {target_asset!r}; present={[d.m_Name for _, d in assets]}")
    else:
        candidates = assets[:1]

    edit_summaries: dict[str, Any] = {}
    original_texts: dict[str, str] = {}
    for obj, data in candidates:
        name = getattr(data, "m_Name", "?")
        old_text = _as_text(data.m_Script)
        original_texts[name] = old_text
        new_text, summary = apply_edits_to_text(old_text, edits)
        if summary["changed_keys"] or summary["added_keys"] or summary["old_chars"] != summary["new_chars"]:
            data.m_Script = new_text
            data.save()
            edit_summaries[name] = summary
        else:
            edit_summaries[name] = {**summary, "noop": True}

    is_changed = getattr(bundle_file, "is_changed", None)
    raw_new = bundle_file.save(packer=args.packer)
    encrypted = encrypt_bytes(raw_new, mask, lunar_base, original_disk[0])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(encrypted)

    # 进程内自检：用 lunar-base 读取器读回（原始文本 + key:value）
    reader, _, _, _ = _lunar_modules(lunar_base)
    dec2, _ = decrypt_file(out_path, lunar_base, mask_name=mask)
    streams_new = reader.extract_bundle_streams(dec2)
    readback_texts: dict[str, str] = {}
    readback: dict[str, dict[str, str]] = {}
    for stream in streams_new:
        for name, text in reader.extract_text_assets(stream):
            readback_texts[name] = text
            readback[name] = parse_key_values(text)

    # 期望值：对每个编辑过的 asset 检查
    #   1) set/append 的 key 读回值 == 期望值
    #   2) 读回的 TextAsset 原始文本 == 我们写入的文本（逐字符一致，含注释行）
    #   3) 未编辑 key 逐条保持原值
    expected_checks: dict[str, Any] = {}
    edited_new_texts: dict[str, str] = {}
    for obj, data in candidates:
        name = getattr(data, "m_Name", "?")
        edited_new_texts[name] = _as_text(data.m_Script)
    for name, summary in edit_summaries.items():
        if name not in readback:
            expected_checks[name] = {"present": False}
            continue
        checks: dict[str, Any] = {
            "present": True,
            "set_ok": True,
            "append_ok": True,
            "text_exact_ok": readback_texts.get(name) == edited_new_texts.get(name),
        }
        for key, value in edits.get("set", {}).items():
            if readback[name].get(key) != value:
                checks["set_ok"] = False
                checks.setdefault("set_mismatches", {})[key] = readback[name].get(key)
        for key, value in edits.get("append", {}).items():
            if readback[name].get(key) != value:
                checks["append_ok"] = False
                checks.setdefault("append_mismatches", {})[key] = readback[name].get(key)
        if summary["old_chars"] == summary["new_chars"] and not summary["changed_keys"] and not summary["added_keys"]:
            checks["noop"] = True

        original_entries = parse_key_values(original_texts[name])
        touched = set(edits.get("set", {})) | set(edits.get("append", {}))
        untouched = [k for k in original_entries if k not in touched]
        bad = [k for k in untouched if readback[name].get(k) != original_entries[k]]
        checks["untouched_keys_ok"] = not bad
        checks["untouched_keys_checked"] = len(untouched)
        if bad:
            checks["untouched_mismatches"] = bad[:10]

        def format_stats(value: str) -> dict[str, int]:
            lines = value.split("\n")
            return {
                "lines": len(lines),
                "comment_lines": sum(1 for line in lines if line.strip().startswith("//")),
                "blank_lines": sum(1 for line in lines if not line.strip()),
                "chars": len(value),
            }

        checks["format_before"] = format_stats(original_texts[name])
        checks["format_after"] = format_stats(readback_texts.get(name, ""))
        expected_checks[name] = checks
    expected_checks["all_ok"] = all(
        v.get("present", False)
        and v.get("set_ok", True)
        and v.get("append_ok", True)
        and v.get("text_exact_ok", True)
        and v.get("untouched_keys_ok", True)
        for v in expected_checks.values()
        if isinstance(v, dict)
    )

    # 结构级对比：确保 UnityFS/SerializedFile 的客户端加载依赖字段未变
    structure_input = describe_bundle(decrypted, lunar_base)
    structure_output = describe_bundle(raw_new, lunar_base)
    structure_check = compare_structure(structure_input, structure_output)
    expected_checks["structure_ok"] = structure_check["ok"]
    expected_checks["structure_diffs"] = structure_check["diffs"]
    expected_checks["all_ok"] = (
        expected_checks["all_ok"] and structure_check["ok"] and encrypted[0] == original_disk[0]
    )

    report = {
        "bundle": str(bundle_path),
        "output": str(out_path),
        "mask_name": mask,
        "octo_version_input": f"0x{original_disk[0]:02x}",
        "octo_version_output": f"0x{encrypted[0]:02x}",
        "octo_version_preserved": encrypted[0] == original_disk[0],
        "packer": args.packer,
        "timings_sec": {},
        "sizes": {
            "input_on_disk_bytes": len(original_disk),
            "input_unityfs_bytes": len(decrypted),
            "output_unityfs_bytes": len(raw_new),
            "output_on_disk_bytes": len(encrypted),
        },
        "sha256": {
            "input_on_disk": sha256(original_disk),
            "input_unityfs": sha256(decrypted),
            "output_on_disk": sha256(encrypted),
            "output_unityfs": sha256(raw_new),
        },
        "unityfs_input": parse_unityfs_header(decrypted),
        "unityfs_output": parse_unityfs_header(raw_new),
        "structure_input": structure_input,
        "structure_output": structure_output,
        "structure_check": structure_check,
        "serialized_files_input": len(getattr(env, "files", {})),
        "streams_input": [len(s) for s in reader.extract_bundle_streams(decrypted)],
        "bundle_file_is_changed": is_changed,
        "text_assets": [getattr(d, "m_Name", "?") for _, d in assets],
        "edit_summaries": edit_summaries,
        "readback_assets": {name: len(entries) for name, entries in readback.items()},
        "verification": expected_checks,
    }
    report["timings_sec"]["total"] = round(time.time() - started, 3)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verification"]["all_ok"] else 2


# ---------------------------------------------------------------------------
# verify（独立进程、只用 lunar-base 读取器，不启用 UnityPy）
# ---------------------------------------------------------------------------
def cmd_verify(args: argparse.Namespace) -> int:
    lunar_base = Path(args.lunar_base)
    reader, derive_mask_name, _, _ = _lunar_modules(lunar_base)
    bundle_path = Path(args.bundle)
    raw = bundle_path.read_bytes()
    mask = args.mask_name or derive_mask_name(str(bundle_path))
    decrypted = reader.decrypt_text_bundle(raw, mask)
    result: dict[str, Any] = {
        "bundle": str(bundle_path),
        "mask_name": mask,
        "on_disk_bytes": len(raw),
        "unityfs_header_ok": decrypted[:7] == b"UnityFS",
        "read_ok": False,
        "text_assets": {},
        "checks": {},
    }
    if not result["unityfs_header_ok"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    entries_by_asset: dict[str, dict[str, str]] = {}
    streams = reader.extract_bundle_streams(decrypted)
    result["streams"] = [len(s) for s in streams]
    for stream in streams:
        for name, text in reader.extract_text_assets(stream):
            entries_by_asset[name] = parse_key_values(text)
            result["text_assets"][name] = len(entries_by_asset[name])
    result["read_ok"] = bool(entries_by_asset)

    edits = load_edits(Path(args.edits)) if args.edits else None
    if edits:
        target = edits.get("text_asset")
        names = [target] if target else list(entries_by_asset)
        ok = True
        for name in names:
            entries = entries_by_asset.get(name, {})
            checks = {"present": name in entries_by_asset, "set_ok": True, "append_ok": True}
            for key, value in edits.get("set", {}).items():
                if entries.get(key) != value:
                    checks["set_ok"] = False
                    checks.setdefault("set_mismatches", {})[key] = entries.get(key)
            for key, value in edits.get("append", {}).items():
                if entries.get(key) != value:
                    checks["append_ok"] = False
                    checks.setdefault("append_mismatches", {})[key] = entries.get(key)
            result["checks"][name] = checks
            ok = ok and checks["present"] and checks["set_ok"] and checks["append_ok"]
        result["all_ok"] = ok
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 2
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# roundtrip：批量无损回环
# ---------------------------------------------------------------------------
def iter_bundles(text_root: Path, lang: str, limit: int | None, pattern: str | None) -> Iterable[Path]:
    root = text_root / lang
    if not root.is_dir():
        raise SystemExit(f"text root not found: {root}")
    files = sorted(root.rglob("*.assetbundle"))
    if pattern:
        files = [f for f in files if pattern in str(f)]
    if limit:
        step = max(1, len(files) // limit)
        files = files[::step][:limit]
    return files


def cmd_roundtrip(args: argparse.Namespace) -> int:
    lunar_base = Path(args.lunar_base)
    text_root = Path(args.text_root)
    reader, derive_mask_name, _, _ = _lunar_modules(lunar_base)
    results: list[dict[str, Any]] = []
    ok_count = 0
    fail_count = 0
    t0 = time.time()
    for bundle_path in iter_bundles(text_root, args.lang, args.limit, args.pattern):
        entry: dict[str, Any] = {"bundle": str(bundle_path.relative_to(text_root))}
        mask = derive_mask_name(str(bundle_path))
        entry["mask"] = mask
        try:
            raw = bundle_path.read_bytes()
            decrypted = reader.decrypt_text_bundle(raw, mask)
            if decrypted[:7] != b"UnityFS":
                raise ValueError(f"decrypt bad header {decrypted[:8]!r}")
            env, bundle_file = unitypy_env(decrypted)
            before: dict[str, str] = {}
            expected: dict[str, str] = {}
            changed_assets = 0
            edit = None
            if args.append_key:
                edit = {"append": {args.append_key: args.append_value or ""}}
            for obj in env.objects:
                if obj.type.name != "TextAsset":
                    continue
                data = obj.read()
                name = getattr(data, "m_Name", "?")
                old_text = _as_text(data.m_Script)
                before[name] = old_text
                if edit:
                    new_text, summary = apply_edits_to_text(old_text, edit)
                    if summary["added_keys"]:
                        data.m_Script = new_text
                        data.save()
                        changed_assets += 1
                    expected[name] = new_text
                else:
                    expected[name] = old_text
            saved = bundle_file.save(packer=args.packer)
            encrypted = encrypt_bytes(saved, mask, lunar_base, raw[0])
            version_preserved = encrypted[0] == raw[0]
            dec2 = reader.decrypt_text_bundle(encrypted, mask)
            streams = reader.extract_bundle_streams(dec2)
            after: dict[str, str] = {}
            for stream in streams:
                for name, text in reader.extract_text_assets(stream):
                    after[name] = text
            # 无损模式：全部文本逐字符相同；改写模式：读回文本 == 期望改写文本
            identical = after == expected
            mode_ok = identical and version_preserved
            if edit and identical:
                for name, text in after.items():
                    if args.append_key not in parse_key_values(text):
                        mode_ok = False
                        break
            entry.update(
                {
                    "ok": mode_ok,
                    "input_bytes": len(raw),
                    "unityfs_in": len(decrypted),
                    "unityfs_out": len(saved),
                    "output_bytes": len(encrypted),
                    "assets": len(before),
                    "changed_assets": changed_assets,
                    "string_identical": identical,
                    "octo_version": f"0x{raw[0]:02x}",
                    "octo_version_preserved": version_preserved,
                }
            )
            if not mode_ok:
                entry["assets_before"] = sorted(before)
                entry["assets_after"] = sorted(after)
                entry["diff_assets"] = sorted(set(before) ^ set(after))
                if identical and edit:
                    entry["append_key_missing"] = True
            ok_count += 1 if mode_ok else 0
            fail_count += 0 if mode_ok else 1
        except Exception as exc:  # noqa: BLE001 — 需要记录每个样本的失败原因
            entry.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            fail_count += 1
        results.append(entry)
    summary = {
        "lang": args.lang,
        "packer": args.packer,
        "mode": "append-edit" if args.append_key else "lossless-roundtrip",
        "append_key": args.append_key,
        "samples": len(results),
        "ok": ok_count,
        "fail": fail_count,
        "elapsed_sec": round(time.time() - t0, 2),
        "failures": [r for r in results if not r.get("ok")][:20],
        "results": results,
    }
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    printable = {k: v for k, v in summary.items() if k != "results"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0 if fail_count == 0 else 2


# ---------------------------------------------------------------------------
# selftest：一键复现完整 PoC
# ---------------------------------------------------------------------------
def cmd_selftest(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir)
    lunar_base = Path(args.lunar_base)
    text_root = Path(args.text_root)
    src = text_root / "ja" / "ui" / "ui_0130310.assetbundle"
    if not src.is_file():
        raise SystemExit(f"sample bundle not found: {src}")
    edits_path = workdir / "edits_ui_0130310.json"
    out_path = workdir / "out" / "text" / "ja" / "ui" / "ui_0130310.assetbundle"
    report_path = workdir / "logs" / "selftest_repack_report.json"
    verify_path = workdir / "logs" / "selftest_verify_report.json"

    # 选一条现有 key 做长度变化的改写，并追加一个新 key
    decrypted, mask = decrypt_file(src, lunar_base)
    reader = _lunar_modules(lunar_base)[0]
    streams = reader.extract_bundle_streams(decrypted)
    name0, text0 = reader.extract_text_assets(streams[0])[0]
    entries = parse_key_values(text0)
    existing_key = next(iter(entries))
    edits = {
        "bundle": str(src),
        "text_asset": name0,
        "set": {
            existing_key: entries[existing_key] + "【汉化写回测试·长度变化】",
        },
        "append": {
            "probe.appended.key_0001": "追加键值：用于验证 text asset 写入后能被 lunar-base 读取器逐 key 读回。",
        },
    }
    edits_path.parent.mkdir(parents=True, exist_ok=True)
    edits_path.write_text(json.dumps(edits, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[selftest] sample     = {src}")
    print(f"[selftest] edits      = {edits_path}")
    print(f"[selftest] output     = {out_path}")
    rc_repack = cmd_repack(
        argparse.Namespace(
            bundle=str(src),
            out=str(out_path),
            edits=str(edits_path),
            report=str(report_path),
            packer="original",
            lunar_base=str(lunar_base),
        )
    )
    print(f"[selftest] repack rc  = {rc_repack}")
    print(f"[selftest] verify: independent process would be run manually; in-process readback above.")
    # 再跑一次独立 verify 路径（同一进程但不复用 UnityPy 状态）
    rc_verify = cmd_verify(
        argparse.Namespace(
            bundle=str(out_path),
            edits=str(edits_path),
            mask_name=mask,
            lunar_base=str(lunar_base),
            json_out=str(verify_path),
        )
    )
    print(f"[selftest] verify rc  = {rc_verify}")
    print(f"[selftest] report     = {report_path}")
    print(f"[selftest] verify json= {verify_path}")
    return 0 if rc_repack == 0 and rc_verify == 0 else 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="NieR Re[in]carnation 文本 assetbundle 写回 PoC（只动拷贝文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--lunar-base", default=str(DEFAULT_LUNAR_BASE), help="lunar-base 根目录")
    parser.add_argument("--text-root", default=str(DEFAULT_TEXT_ROOT), help="服务端 text assetbundle 根目录")
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR), help="测试产物目录")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ins = sub.add_parser("inspect", help="打印 bundle 结构/TextAsset 概况")
    p_ins.add_argument("--bundle", required=True)
    p_ins.add_argument("--sample", type=int, default=5, help="每个 TextAsset 打印前 N 个 key:value")
    p_ins.add_argument("--dump-keyvalues", help="把全部 key:value 导出为该 JSON 路径")
    p_ins.set_defaults(func=cmd_inspect)

    p_rep = sub.add_parser("repack", help="改 TextAsset 文本并重存/重加密")
    p_rep.add_argument("--bundle", required=True)
    p_rep.add_argument("--out", required=True, help="输出 .assetbundle 路径（拷贝，不动原文件）")
    p_rep.add_argument("--edits", help="edits JSON（set/append/raw_append/raw_prepend/text_asset）")
    p_rep.add_argument("--report", help="写出详细 JSON 报告")
    p_rep.add_argument(
        "--packer",
        default="original",
        choices=["original", "none", "lz4", "lz4hc", "lzma"],
        help="UnityFS 重存压缩方式（original=保持原 flags）",
    )
    p_rep.set_defaults(func=cmd_repack)

    p_ver = sub.add_parser("verify", help="独立校验已写出的 bundle（仅 lunar-base 读取器）")
    p_ver.add_argument("--bundle", required=True)
    p_ver.add_argument("--edits", help="edits JSON；给出时校验 set/append 是否生效")
    p_ver.add_argument("--mask-name", help="覆盖 octo mask 名（默认从路径推导）")
    p_ver.add_argument("--json-out")
    p_ver.set_defaults(func=cmd_verify)

    p_rt = sub.add_parser("roundtrip", help="批量无损回环测试（不改文本）")
    p_rt.add_argument("--lang", default="ja", choices=["ja", "en", "ko"])
    p_rt.add_argument("--limit", type=int, default=200, help="均匀抽样数量；0=全部")
    p_rt.add_argument("--pattern", default=None, help="只测路径包含该子串的 bundle")
    p_rt.add_argument("--packer", default="original")
    p_rt.add_argument("--append-key", help="改写模式：给每个 TextAsset 追加该 key（用于批量验证文本写入链路）")
    p_rt.add_argument("--append-value", default="", help="改写模式：追加 key 的值（默认空）")
    p_rt.add_argument("--json-out")
    p_rt.set_defaults(func=cmd_roundtrip)

    p_st = sub.add_parser("selftest", help="一键复现完整 PoC（默认 ui_0130310）")
    p_st.set_defaults(func=cmd_selftest)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
