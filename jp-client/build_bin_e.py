#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_bin_e.py — JP 客户端成对交付之 **bin.e 构建器**（汉化 masterdata + 可选编辑项）。

对齐「原 lunar-scripts 一样可以编辑 bin.e」：
  * **内容基** = 汉化 masterdata（权威汉化基 `bin_zh_fix6.bin.e` sha256 7dba416a…b664）。
    `--bin-e` 直接给汉化基，或给原版 + `--text-from <汉化基>` 逐字节移植 5 张文本表。
  * **可选编辑项**（`--bin-edit cfg.json`）逐项对应原版 `patch_masterdata.py`（lunar-scripts /
    lunar-scripts-jp 的 notebook「Patch Master Data」实际编辑面）：
      1. extend_end_dates        —— 31+ 张表 EndDatetime 类 date 列 2020-2029 → 2030-12-31
      2. empty_maintenance       —— m_maintenance 清空（维护横幅不再弹）
      3. add_labyrinth_unlock    —— m_event_quest_unlock_condition 补 1 行（迷宫进支线菜单）
      4. window_labyrinth_seasons—— m_event_quest_labyrinth_season 每章恰 1 个赛季开窗
      5. dedup_gimmick_schedules —— m_gimmick_sequence_schedule 每 FirstGimmickSequenceId 1 条活跃
    （m_omikuji 恒跳过 = 原版 SKIP_TABLES 语义。）

**编辑器语义遵守 bunker 核实结论**（zh-l10n\\work\\diag-lunar-base\\LUNAR-BASE-ANALYSIS.md）：
  * 格子不冲：未改表**字节照搬**；表内只对 int64(0xd3) **date 列**做原地手术；字符串列 walker
    直接 skip（文本格连解包重打包都不经历）；只在行数/列数不变时动值，补行=尾部追加原字节。
  * 文件会冲：输出整体是新文件（TOC 偏移重排 + AES 重加密）；**不要拿未汉化 bin 当输入基**。
  * 只动 date 列的坑：绝不改非日期列的编码宽度（对照 apply_order 的 uint16 重编码坑）。

输出后强制断言（任一失败 SystemExit）：
  A. 文本格 = 汉化基逐字节（5 张文本表 raw blob 全等；`--zh-base`，缺省 = 移植源或输入）
  B. 结构校验（AES/TOC/5 表/LZ4 全过）——对齐 bunker `android_patcher.validate_master` 口径
     （1–32MB、AES-256-CBC 解密、TOC 越界检查、m_costume/m_weapon/m_event_quest_chapter/
      m_shop/m_mom_banner 5 表齐全、逐表 LZ4 可解）+ 表块连续无空洞
  C. 与原版 bin.e 的 diff 只在预期表（`--orig-bin-e` 给原版 20240404193219.bin.e）：
     变化表 == {汉化基⊕原版 差异表} ∪ {本次编辑实际动到的表}，并逐表验证「只动 date 列 /
     尾部补行 / 指定表清空」三种白名单操作。

命令行（干净机器；依赖 pip install pycryptodome msgpack lz4）：
  python build_bin_e.py --bin-e bin_zh_fix6.bin.e --out-bin-e out/bin_zh_fix6.bin.e \\
      --bin-edit bin-edit.default.json \\
      --orig-bin-e 20240404193219.bin.e
  # 原版输入 + 汉化文本移植（成对交付推荐形态；文件名前后不变，输出=输入同名）：
  python build_bin_e.py --bin-e 20240404193219.bin.e --text-from bin_zh_fix6.bin.e \\
      --out-bin-e out/20240404193219.bin.e --bin-edit bin-edit.default.json \\
      --orig-bin-e 20240404193219.bin.e
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import lz4.block
    import msgpack
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少依赖：pip install pycryptodome msgpack lz4（bin.e 解析/重打包必需）。"
        f" 原始错误: {exc}"
    )

# --------------------------------------------------------------------------
# 常量（key/IV、文本表、结构校验 5 表 = 原版 dump_masterdata / bunker validate_master）
# --------------------------------------------------------------------------
KEY = bytes.fromhex("36436230313332314545356536624265")
IV = bytes.fromhex("45666341656634434165356536446141")

TEXT_TABLES = (
    "m_dokan_text",
    "m_gift_text",
    "m_navi_cut_in_text",
    "m_webview_mission_title_text",
    "m_webview_panel_mission_complete_flavor_text",
)
REQUIRED_TABLES = ("m_costume", "m_weapon", "m_event_quest_chapter", "m_shop", "m_mom_banner")

# 结构体积口径同 bunker android_patcher.validate_master（1–32MB）
MIN_BIN_BYTES = 1_000_000
MAX_BIN_BYTES = 32_000_000

# ---- 原版 patch_masterdata.py 编辑面（逐项对应；列号来自 schemas.json）----
TARGET_END_DT = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
TARGET_END_MS = int(TARGET_END_DT.timestamp() * 1000)
MIN_PATCH_MS = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MAX_PATCH_MS = int(datetime(2030, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

SKIP_TABLES = frozenset({"m_omikuji"})          # 原版恒跳过
EMPTY_TABLES = frozenset({"m_maintenance"})      # 原版清空
TABLE_ROW_ADDITIONS = {                          # 原版补行（幂等：键已存在则跳过）
    "m_event_quest_unlock_condition": [[12, 0, 0, 1, 21, 0]],
}
SCHEDULE_PATCH_CUTOFF_MS = int(datetime(2023, 2, 1, tzinfo=timezone.utc).timestamp() * 1000)
TABLE_PATCH_FILTERS = {"m_gimmick_sequence_schedule": (1, SCHEDULE_PATCH_CUTOFF_MS)}

PATCH_COLUMNS = {
    "m_appeal_dialog": [(5, "EndDatetime")],
    "m_big_hunt_schedule": [(3, "ChallengeEndDatetime")],
    "m_cage_ornament": [(2, "EndDatetime")],
    "m_consumable_item_term": [(2, "EndDatetime")],
    "m_costume_collection_bonus": [(6, "EndDatetime")],
    "m_dokan": [(4, "EndDatetime")],
    "m_enhance_campaign": [(5, "EndDatetime")],
    "m_event_quest_chapter": [(9, "EndDatetime")],
    "m_event_quest_daily_group": [(2, "EndDatetime")],
    "m_event_quest_guerrilla_free_open": [(4, "EndDatetime")],
    "m_event_quest_limit_content": [(6, "EndDatetime")],
    "m_event_quest_limit_content_deck_restriction": [(4, "EndDatetime")],
    "m_gacha_medal": [(4, "AutoConvertDatetime")],
    "m_gimmick_sequence_schedule": [(2, "EndDatetime")],
    "m_important_item_effect": [(6, "EndDatetime")],
    "m_login_bonus": [(5, "EndDatetime"), (6, "StampReceiveEndDatetime")],
    "m_mission_pass": [(2, "EndDatetime")],
    "m_mission_term": [(2, "EndDatetime")],
    "m_mom_banner": [(7, "EndDatetime")],
    "m_mom_point_banner": [(4, "EndDatetime")],
    "m_navi_cut_in": [(4, "EndDatetime")],
    "m_omikuji": [(2, "EndDatetime")],
    "m_portal_cage_access_point_function_group_schedule": [(5, "EndDatetime")],
    "m_possession_acquisition_route": [(7, "EndDatetime")],
    "m_premium_item": [(3, "EndDatetime")],
    "m_pvp_season": [(3, "SeasonEndDatetime")],
    "m_quest_bonus_term_group": [(3, "EndDatetime")],
    "m_quest_campaign": [(4, "EndDatetime")],
    "m_quest_schedule": [(3, "EndDatetime")],
    "m_shop": [(10, "EndDatetime")],
    "m_shop_item_cell_term": [(2, "EndDatetime")],
    "m_tip": [(6, "EndDatetime")],
    "m_title_flow_movie": [(3, "EndDatetime")],
    "m_webview_mission": [(5, "EndDatetime")],
    "m_webview_panel_mission": [(4, "EndDatetime")],
}

EDIT_KEYS = (
    "extend_end_dates",
    "empty_maintenance",
    "add_labyrinth_unlock",
    "window_labyrinth_seasons",
    "dedup_gimmick_schedules",
)
DEFAULT_EDITS = {k: True for k in EDIT_KEYS}


# --------------------------------------------------------------------------
# AES / 容器
# --------------------------------------------------------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def aes_decrypt(data: bytes) -> bytes:
    return unpad(AES.new(KEY, AES.MODE_CBC, IV).decrypt(data), AES.block_size)


def aes_encrypt(data: bytes) -> bytes:
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(data, AES.block_size))


class BinView:
    """一份 bin.e 的只读解析视图（解密 + TOC + 表块）。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        self.sha256 = sha256_bytes(self.raw)
        self.size = len(self.raw)
        try:
            self.decrypted = aes_decrypt(self.raw)
        except ValueError as exc:
            raise SystemExit(f"{self.path}: AES 解密失败（key/IV 不对或文件损坏）: {exc}")
        try:
            toc_raw = msgpack.unpackb(self.decrypted, raw=False, strict_map_key=False)
            blob = b""
            header_len = len(self.decrypted)
        except msgpack.ExtraData as exc:  # type: ignore[attr-defined]
            toc_raw = exc.unpacked
            blob = exc.extra
            header_len = len(self.decrypted) - len(blob)
        if not isinstance(toc_raw, dict):
            raise SystemExit(f"{self.path}: TOC 不是 map，而是 {type(toc_raw).__name__}")
        self.toc: dict[str, tuple[int, int]] = {
            str(k): (int(v[0]), int(v[1])) for k, v in toc_raw.items()
        }
        self.blob = blob
        self.header_len = header_len

    def part(self, name: str) -> bytes:
        off, length = self.toc[name]
        return self.blob[off:off + length]


# --------------------------------------------------------------------------
# msgpack 字节级 walker（与原版 patch_masterdata.py 同语义：不整表 unpack→pack）
# --------------------------------------------------------------------------
def skip_msgpack_value(data: bytes, pos: int) -> int:
    tag = data[pos]
    if tag <= 0x7f or tag >= 0xe0:
        return pos + 1
    if 0xa0 <= tag <= 0xbf:
        return pos + 1 + (tag & 0x1f)
    if 0x90 <= tag <= 0x9f:
        p = pos + 1
        for _ in range(tag & 0x0f):
            p = skip_msgpack_value(data, p)
        return p
    if 0x80 <= tag <= 0x8f:
        p = pos + 1
        for _ in range((tag & 0x0f) * 2):
            p = skip_msgpack_value(data, p)
        return p
    FIXED = {
        0xC0: 1, 0xC2: 1, 0xC3: 1,
        0xCA: 5, 0xCB: 9,
        0xCC: 2, 0xCD: 3, 0xCE: 5, 0xCF: 9,
        0xD0: 2, 0xD1: 3, 0xD2: 5, 0xD3: 9,
        0xD4: 3, 0xD5: 4, 0xD6: 6, 0xD7: 10, 0xD8: 18,
    }
    if tag in FIXED:
        return pos + FIXED[tag]
    LENGTH_PREFIXED = {
        0xC4: (1, "B"), 0xC5: (2, ">H"), 0xC6: (4, ">I"),
        0xD9: (1, "B"), 0xDA: (2, ">H"), 0xDB: (4, ">I"),
        0xC7: (1, "B"), 0xC8: (2, ">H"), 0xC9: (4, ">I"),
    }
    if tag in LENGTH_PREFIXED:
        sz_bytes, fmt = LENGTH_PREFIXED[tag]
        n = struct.unpack(fmt, data[pos + 1:pos + 1 + sz_bytes])[0]
        extra = 1 if tag in (0xC7, 0xC8, 0xC9) else 0
        return pos + 1 + sz_bytes + extra + n
    ARRAY_MAP = {0xDC: (2, ">H"), 0xDD: (4, ">I"), 0xDE: (2, ">H"), 0xDF: (4, ">I")}
    if tag in ARRAY_MAP:
        sz_bytes, fmt = ARRAY_MAP[tag]
        n = struct.unpack(fmt, data[pos + 1:pos + 1 + sz_bytes])[0]
        items = n * 2 if tag in (0xDE, 0xDF) else n
        p = pos + 1 + sz_bytes
        for _ in range(items):
            p = skip_msgpack_value(data, p)
        return p
    raise ValueError(f"未知 msgpack tag 0x{tag:02x} @ {pos}")


def read_array_len(data: bytes, pos: int):
    tag = data[pos]
    if 0x90 <= tag <= 0x9f:
        return (tag & 0x0f, pos + 1)
    if tag == 0xDC:
        return (struct.unpack(">H", data[pos + 1:pos + 3])[0], pos + 3)
    if tag == 0xDD:
        return (struct.unpack(">I", data[pos + 1:pos + 5])[0], pos + 5)
    raise ValueError(f"期望 array，tag=0x{tag:02x} @ {pos}")


def read_int(data: bytes, pos: int) -> int:
    tag = data[pos]
    if tag <= 0x7f:
        return tag
    if tag == 0xCC:
        return data[pos + 1]
    if tag == 0xCD:
        return struct.unpack(">H", data[pos + 1:pos + 3])[0]
    if tag == 0xCE:
        return struct.unpack(">I", data[pos + 1:pos + 5])[0]
    raise ValueError(f"read_int: 意外 tag 0x{tag:02x} @ {pos}")


def array_header(n: int) -> bytes:
    if n <= 0x0F:
        return bytes([0x90 | n])
    if n <= 0xFFFF:
        return b"\xdc" + struct.pack(">H", n)
    return b"\xdd" + struct.pack(">I", n)


def row_col_positions(table: bytes, row_pos: int):
    """返回 (row_end, [col_start, ...])。"""
    col_count, p = read_array_len(table, row_pos)
    cols = []
    for _ in range(col_count):
        cols.append(p)
        p = skip_msgpack_value(table, p)
    return p, cols


# --------------------------------------------------------------------------
# LZ4 表块（ExtType 99）编解码
# --------------------------------------------------------------------------
def read_lz4_ext_header(ext_data: bytes):
    tag = ext_data[0]
    if tag == 0xD2:
        return struct.unpack(">i", ext_data[1:5])[0], ext_data[5:]
    if tag == 0xCE:
        return struct.unpack(">I", ext_data[1:5])[0], ext_data[5:]
    if tag == 0xD1:
        return struct.unpack(">h", ext_data[1:3])[0], ext_data[3:]
    if tag == 0xCD:
        return struct.unpack(">H", ext_data[1:3])[0], ext_data[3:]
    if tag <= 0x7F:
        return tag, ext_data[1:]
    raise ValueError(f"LZ4 ext 头意外 tag 0x{tag:02x}")


def build_lz4_ext_blob(decompressed: bytes) -> bytes:
    compressed = lz4.block.compress(decompressed, store_size=False)
    header = b"\xd2" + struct.pack(">i", len(decompressed))
    return msgpack.packb(msgpack.ExtType(99, header + compressed), use_bin_type=True)


def decode_table_part(part: bytes) -> tuple[bool, bytes]:
    """返回 (was_lz4, 解压后的表字节)。小/空表可为未压缩的 msgpack list。"""
    obj = msgpack.unpackb(part, raw=True)
    if isinstance(obj, msgpack.ExtType) and obj.code == 99:
        ulen, lz4_data = read_lz4_ext_header(obj.data)
        return True, lz4.block.decompress(lz4_data, uncompressed_size=ulen)
    return False, part


# --------------------------------------------------------------------------
# 编辑实现（= 原版 patch_masterdata.py 逐函数同语义）
# --------------------------------------------------------------------------
def patch_table_blob(blob: bytearray, col_indices: set[int], row_filter=None):
    """表内只对 0xd3 int64 的目标列做原地写；其它列 walker 跳过（文本格字节照搬）。"""
    row_count, pos = read_array_len(blob, 0)
    patched = skipped = 0
    for _ in range(row_count):
        row_end, cols = row_col_positions(blob, pos)
        col_count = len(cols)
        skip_row = False
        if row_filter is not None:
            filter_col, filter_max = row_filter
            if filter_col < col_count and blob[cols[filter_col]] == 0xD3:
                fp = cols[filter_col]
                if struct.unpack(">q", blob[fp + 1:fp + 9])[0] >= filter_max:
                    skip_row = True
        if skip_row:
            skipped += 1
        else:
            for ci in range(col_count):
                p = cols[ci]
                if ci in col_indices and blob[p] == 0xD3:
                    val = struct.unpack(">q", blob[p + 1:p + 9])[0]
                    if MIN_PATCH_MS <= val <= MAX_PATCH_MS:
                        struct.pack_into(">q", blob, p + 1, TARGET_END_MS)
                        patched += 1
        pos = row_end
    return patched, skipped


def add_table_rows(blob: bytes, rows: list[list[int]], key_col: int = 0):
    """尾部补行（幂等）；既有行字节照搬，只重发外层 array 头。"""
    count, pos = read_array_len(blob, 0)
    existing = set()
    p = pos
    for _ in range(count):
        _, row_pos = read_array_len(blob, p)
        existing.add(read_int(blob, row_pos))
        p = skip_msgpack_value(blob, p)
    to_add = [r for r in rows if r[key_col] not in existing]
    if not to_add:
        return None
    new_rows = b"".join(msgpack.packb(r, use_bin_type=True) for r in to_add)
    return array_header(count + len(to_add)) + bytes(blob[pos:]) + new_rows


def patch_labyrinth_seasons(blob: bytearray) -> int:
    """每章恰 1 个赛季开窗（最高 SeasonNumber），其余 EndDatetime=0。只写 int64。"""
    row_count, pos = read_array_len(blob, 0)
    rows = []
    for _ in range(row_count):
        row_end, cols = row_col_positions(blob, pos)
        rows.append((read_int(blob, cols[0]), read_int(blob, cols[1]), cols[2], cols[3]))
        pos = row_end
    max_season: dict[int, int] = {}
    for chapter, season, _, _ in rows:
        if season > max_season.get(chapter, -1):
            max_season[chapter] = season
    written = 0
    for chapter, season, start_pos, end_pos in rows:
        if blob[start_pos] != 0xD3 or blob[end_pos] != 0xD3:
            continue
        if season == max_season[chapter]:
            struct.pack_into(">q", blob, start_pos + 1, MIN_PATCH_MS)
            struct.pack_into(">q", blob, end_pos + 1, TARGET_END_MS)
        else:
            struct.pack_into(">q", blob, end_pos + 1, 0)
        written += 1
    return written


def patch_gimmick_sequence_schedules(blob: bytearray) -> int:
    """每 FirstGimmickSequenceId 只留 1 条活跃（最低 StartDatetime 同 id 最小者），其余 End=0。"""
    row_count, pos = read_array_len(blob, 0)
    rows = []
    for _ in range(row_count):
        row_end, cols = row_col_positions(blob, pos)
        sched_id = read_int(blob, cols[0])
        start_dt = (struct.unpack(">q", blob[cols[1] + 1:cols[1] + 9])[0]
                    if blob[cols[1]] == 0xD3 else 0)
        first_seq = read_int(blob, cols[3])
        rows.append((first_seq, start_dt, sched_id, cols[2]))
        pos = row_end
    canonical: dict[int, tuple[int, int]] = {}
    for first_seq, start_dt, sched_id, _ in rows:
        cur = canonical.get(first_seq)
        if cur is None or (start_dt, sched_id) < cur:
            canonical[first_seq] = (start_dt, sched_id)
    zeroed = 0
    for first_seq, start_dt, sched_id, end_pos in rows:
        if (start_dt, sched_id) == canonical[first_seq]:
            continue
        if blob[end_pos] != 0xD3:
            continue
        struct.pack_into(">q", blob, end_pos + 1, 0)
        zeroed += 1
    return zeroed


# --------------------------------------------------------------------------
# 结构校验（AES/TOC/5 表/LZ4 + 连续布局）
# --------------------------------------------------------------------------
def validate_structure(view: BinView) -> dict:
    checks: dict = {"path": str(view.path), "sha256": view.sha256, "bytes": view.size, "ok": True}

    def fail(msg):
        checks["ok"] = False
        checks.setdefault("problems", []).append(msg)

    if not (MIN_BIN_BYTES < view.size < MAX_BIN_BYTES):
        fail(f"体积 {view.size} 不在 (1MB, 32MB)")
    checks["aes_ok"] = True  # 走到这一步解密+unpad 已成功

    missing = [t for t in REQUIRED_TABLES if t not in view.toc]
    checks["required_tables"] = {"expected": list(REQUIRED_TABLES), "missing": missing}
    if missing:
        fail(f"缺少必需表: {missing}")

    bad_bounds = []
    for name, (off, length) in view.toc.items():
        if off < 0 or length <= 0 or off + length > len(view.blob):
            bad_bounds.append(name)
    checks["toc_bounds_ok"] = not bad_bounds
    if bad_bounds:
        fail(f"TOC 越界: {bad_bounds[:5]}")

    ordered = sorted(view.toc.items(), key=lambda kv: kv[1][0])
    pos = 0
    gaps = []
    for name, (off, length) in ordered:
        if off != pos:
            gaps.append(f"{name}@{off} 期望 {pos}")
        pos = off + length
    checks["blob_contiguous"] = not gaps and pos == len(view.blob)
    if gaps or pos != len(view.blob):
        fail(f"表块不连续: {gaps[:5]} 尾部={pos}/{len(view.blob)}")

    lz4_fail = []
    lz4_tables = plain_tables = 0
    for name in view.toc:
        try:
            was_lz4, _tbl = decode_table_part(view.part(name))
            if was_lz4:
                lz4_tables += 1
            else:
                plain_tables += 1
        except Exception as exc:  # noqa: BLE001
            lz4_fail.append(f"{name}: {exc}")
    checks["lz4"] = {"lz4_tables": lz4_tables, "plain_tables": plain_tables,
                     "failures": lz4_fail[:5]}
    if lz4_fail:
        fail(f"表解压失败: {lz4_fail[:5]}")
    checks["table_count"] = len(view.toc)
    return checks


# --------------------------------------------------------------------------
# diff / 文本格 / 只动 date 列 断言
# --------------------------------------------------------------------------
def diff_tables(a: BinView, b: BinView) -> dict:
    names = sorted(set(a.toc) | set(b.toc))
    changed, only_a, only_b = [], [], []
    for n in names:
        if n not in a.toc:
            only_b.append(n)
        elif n not in b.toc:
            only_a.append(n)
        elif a.part(n) != b.part(n):
            changed.append(n)
    return {"changed": changed, "only_left": only_a, "only_right": only_b}


def assert_text_cells_equal(out: BinView, zh_base: BinView) -> dict:
    """断言 A：5 张文本表 raw blob 与汉化基逐字节一致（文本格字节照搬）。"""
    per = {}
    bad = []
    for name in TEXT_TABLES:
        if name not in out.toc or name not in zh_base.toc:
            per[name] = {"status": "missing"}
            bad.append(name)
            continue
        same = out.part(name) == zh_base.part(name)
        per[name] = {
            "status": "identical" if same else "DIFFERS",
            "out_sha256": sha256_bytes(out.part(name)),
            "zh_base_sha256": sha256_bytes(zh_base.part(name)),
        }
        if not same:
            bad.append(name)
    return {"tables": per, "identical": not bad, "bad_tables": bad}


def classify_table_change(before: bytes, after: bytes) -> dict:
    """对一张前后表做格子级分类：date-only / append-only / emptied / OTHER(违规)。"""
    try:
        was_lz4_b, tb = decode_table_part(before)
        was_lz4_a, ta = decode_table_part(after)
    except Exception as exc:  # noqa: BLE001
        return {"kind": "decode-error", "detail": str(exc)}
    rc_b, pos_b = read_array_len(tb, 0)
    rc_a, pos_a = read_array_len(ta, 0)
    rows_b, rows_a = [], []
    p = pos_b
    for _ in range(rc_b):
        end, cols = row_col_positions(tb, p)
        rows_b.append((p, end, cols))
        p = end
    p = pos_a
    for _ in range(rc_a):
        end, cols = row_col_positions(ta, p)
        rows_a.append((p, end, cols))
        p = end

    if rc_a == 0 and rc_b > 0:
        return {"kind": "emptied", "rows_before": rc_b}
    if rc_b == rc_a:
        date_cells = other_cells = 0
        viol = []
        for i, ((sb, eb, cb), (sa, ea, ca)) in enumerate(zip(rows_b, rows_a)):
            if len(cb) != len(ca):
                viol.append(f"row{i}: 列数 {len(cb)}->{len(ca)}")
                continue
            for ci in range(len(cb)):
                bcell = tb[cb[ci]:(cb[ci + 1] if ci + 1 < len(cb) else eb)]
                acell = ta[ca[ci]:(ca[ci + 1] if ci + 1 < len(ca) else ea)]
                if bcell == acell:
                    continue
                if bcell and acell and bcell[0] == 0xD3 and acell[0] == 0xD3:
                    date_cells += 1
                else:
                    other_cells += 1
                    viol.append(f"row{i} col{ci}: 非 date 列变化 tag 0x{bcell[0]:02x}->0x{acell[0]:02x}")
        return {"kind": "date-only" if not viol else "OTHER",
                "date_cells_changed": date_cells, "other_cells_changed": other_cells,
                "violations": viol[:8], "rows": rc_b}
    if rc_a > rc_b:
        # 尾部追加：前 rc_b 行字节必须原样
        viol = []
        for i, ((sb, eb, cb), (sa, ea, ca)) in enumerate(zip(rows_b, rows_a)):
            if tb[sb:eb] != ta[sa:ea]:
                viol.append(f"row{i}: 前缀行字节变化")
        return {"kind": "append-only" if not viol else "OTHER",
                "rows_before": rc_b, "rows_after": rc_a,
                "appended": rc_a - rc_b, "violations": viol[:8]}
    return {"kind": "OTHER", "detail": f"行数减少 {rc_b}->{rc_a}", "rows_before": rc_b, "rows_after": rc_a}


# --------------------------------------------------------------------------
# 构建
# --------------------------------------------------------------------------
def load_edit_config(path: Path | None) -> dict:
    cfg = {"edits": dict(DEFAULT_EDITS), "notes": "默认 = 原版 patch_masterdata.py 全量编辑面"}
    if path:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        edits = raw.get("edits", raw)
        for k in edits:
            if k in ("notes", "edits"):
                continue
            if k not in EDIT_KEYS:
                raise SystemExit(f"--bin-edit 未知编辑项 {k!r}；可选项 = {list(EDIT_KEYS)}")
        for k in EDIT_KEYS:
            if k in edits:
                cfg["edits"][k] = bool(edits[k])
        cfg["notes"] = raw.get("notes", cfg["notes"])
    return cfg


def apply_edits(parts: dict[str, bytes], toc: dict[str, tuple[int, int]],
                edits: dict[str, bool]) -> dict:
    """对表块字节做编辑；只把真正变化的表写回 parts。返回每项统计。"""
    stats: dict = {k: {"enabled": edits.get(k, False), "changed_tables": []} for k in EDIT_KEYS}

    def get_table(name: str) -> tuple[bool, bytearray]:
        was_lz4, tbl = decode_table_part(parts[name])
        return was_lz4, bytearray(tbl)

    def put_table(name: str, was_lz4: bool, tbl: bytes):
        parts[name] = build_lz4_ext_blob(tbl) if was_lz4 else bytes(tbl)

    # 1) extend_end_dates
    if edits.get("extend_end_dates"):
        total = 0
        for tname, columns in PATCH_COLUMNS.items():
            if tname in SKIP_TABLES or tname not in toc:
                continue
            was_lz4, tbl = get_table(tname)
            col_indices = {idx for idx, _ in columns}
            cnt, skip = patch_table_blob(tbl, col_indices, TABLE_PATCH_FILTERS.get(tname))
            if cnt > 0:
                put_table(tname, was_lz4, bytes(tbl))
                stats["extend_end_dates"]["changed_tables"].append(tname)
                total += cnt
        stats["extend_end_dates"]["values_patched"] = total

    # 2) empty_maintenance
    if edits.get("empty_maintenance"):
        for tname in sorted(EMPTY_TABLES):
            if tname not in toc:
                continue
            was_lz4, tbl = get_table(tname)
            rc, _ = read_array_len(tbl, 0)
            if rc > 0:
                parts[tname] = msgpack.packb([], use_bin_type=True)
                stats["empty_maintenance"]["changed_tables"].append(tname)
                stats["empty_maintenance"]["rows_before"] = rc

    # 3) add_labyrinth_unlock
    if edits.get("add_labyrinth_unlock"):
        for tname, rows in TABLE_ROW_ADDITIONS.items():
            if tname not in toc:
                continue
            was_lz4, tbl = get_table(tname)
            updated = add_table_rows(bytes(tbl), rows)
            if updated is not None:
                put_table(tname, was_lz4, updated)
                stats["add_labyrinth_unlock"]["changed_tables"].append(tname)
                stats["add_labyrinth_unlock"]["rows_added"] = len(rows)

    # 4) window_labyrinth_seasons
    if edits.get("window_labyrinth_seasons"):
        tname = "m_event_quest_labyrinth_season"
        if tname in toc:
            was_lz4, tbl = get_table(tname)
            written = patch_labyrinth_seasons(tbl)
            if written:
                put_table(tname, was_lz4, bytes(tbl))
                stats["window_labyrinth_seasons"]["changed_tables"].append(tname)
                stats["window_labyrinth_seasons"]["rows_windowed"] = written

    # 5) dedup_gimmick_schedules
    if edits.get("dedup_gimmick_schedules"):
        tname = "m_gimmick_sequence_schedule"
        if tname in toc:
            was_lz4, tbl = get_table(tname)
            zeroed = patch_gimmick_sequence_schedules(tbl)
            if zeroed:
                put_table(tname, was_lz4, bytes(tbl))
                stats["dedup_gimmick_schedules"]["changed_tables"].append(tname)
                stats["dedup_gimmick_schedules"]["rows_expired"] = zeroed

    return stats


def rebuild(parts: dict[str, bytes], toc: dict[str, tuple[int, int]]) -> bytes:
    """按原 offset 顺序重排表块 + 重发 TOC + AES 重加密（同原版 patch_masterdata 语义）。"""
    ordered = sorted(toc.items(), key=lambda kv: kv[1][0])
    new_toc: dict[str, tuple[int, int]] = {}
    blob_parts: list[bytes] = []
    off = 0
    for name, _ in ordered:
        part = parts[name]
        new_toc[name] = (off, len(part))
        blob_parts.append(part)
        off += len(part)
    header = msgpack.packb(new_toc, use_bin_type=True)
    return aes_encrypt(header + b"".join(blob_parts))


def build_bin_e(bin_e: Path, out_bin_e: Path, bin_edit: Path | None = None,
                text_from: Path | None = None, zh_base: Path | None = None,
                orig_bin_e: Path | None = None, report_path: Path | None = None,
                dry_run: bool = False) -> dict:
    t0 = time.time()
    bin_e = Path(bin_e)
    out_bin_e = Path(out_bin_e)
    # 硬性要求：bin.e 文件名前后不变（输出文件名 == 输入文件名；可改目录）
    if out_bin_e.name != bin_e.name:
        raise SystemExit(
            f"bin.e 文件名前后不变：输出名 {out_bin_e.name!r} != 输入名 {bin_e.name!r}"
            f"（可改目录，不可改文件名）")
    inp = BinView(bin_e)
    src_for_text = BinView(text_from) if text_from else inp
    zh_view = BinView(zh_base) if zh_base else src_for_text
    orig_view = BinView(orig_bin_e) if orig_bin_e else None

    cfg = load_edit_config(bin_edit)
    edits = cfg["edits"]

    parts: dict[str, bytes] = {name: inp.part(name) for name in inp.toc}
    transplanted = []
    if text_from:
        for name in TEXT_TABLES:
            if name not in src_for_text.toc:
                raise SystemExit(f"--text-from 缺少文本表 {name}")
            if parts.get(name) != src_for_text.part(name):
                parts[name] = src_for_text.part(name)
                transplanted.append(name)

    edit_stats = apply_edits(parts, inp.toc, edits)

    report: dict = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": "jp-client/build_bin_e.py",
        "input": {"path": str(inp.path), "bytes": inp.size, "sha256": inp.sha256},
        "text_from": ({"path": str(src_for_text.path), "sha256": src_for_text.sha256,
                       "transplanted_tables": transplanted} if text_from else None),
        "zh_base": {"path": str(zh_view.path), "sha256": zh_view.sha256},
        "orig_bin_e": ({"path": str(orig_view.path), "sha256": orig_view.sha256}
                       if orig_view else None),
        "edit_config": cfg,
        "edit_stats": edit_stats,
    }

    if dry_run:
        report["dry_run"] = True
        report["ok"] = True
        if report_path:
            Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        print("[build_bin_e] DRY RUN（未写出）")
        print(json.dumps(edit_stats, ensure_ascii=False, indent=2))
        return report

    out_bin_e = Path(out_bin_e)
    out_bin_e.parent.mkdir(parents=True, exist_ok=True)
    out_raw = rebuild(parts, inp.toc)
    out_bin_e.write_bytes(out_raw)
    out = BinView(out_bin_e)
    report["output"] = {"path": str(out.path), "bytes": out.size, "sha256": out.sha256}

    # ---- 断言 B：结构 ----
    report["structure"] = validate_structure(out)
    if not report["structure"]["ok"]:
        if report_path:
            Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        raise SystemExit("断言 B 失败：结构校验未过 → " + json.dumps(report["structure"],
                                                                   ensure_ascii=False))

    # ---- 断言 A：文本格 = 汉化基逐字节 ----
    report["text_cells"] = assert_text_cells_equal(out, zh_view)
    if not report["text_cells"]["identical"]:
        if report_path:
            Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        raise SystemExit("断言 A 失败：文本格与汉化基不一致 → "
                         + json.dumps(report["text_cells"], ensure_ascii=False))

    # ---- 断言 C：与原版 diff 只在预期表 ----
    edit_touched = sorted({t for s in edit_stats.values() for t in s.get("changed_tables", [])})
    zh_diff_tables = sorted(diff_tables(zh_view, orig_view)["changed"]) if orig_view else []
    if orig_view:
        d = diff_tables(out, orig_view)
        actual = sorted(d["changed"])
        expected_effective = sorted(set(zh_diff_tables) | set(edit_touched))
        expected_static = sorted(set(zh_diff_tables)
                                 | {t for k in EDIT_KEYS if edits.get(k)
                                    for t in (list(PATCH_COLUMNS) if k == "extend_end_dates"
                                              else list(EMPTY_TABLES) if k == "empty_maintenance"
                                              else list(TABLE_ROW_ADDITIONS) if k == "add_labyrinth_unlock"
                                              else ["m_event_quest_labyrinth_season"] if k == "window_labyrinth_seasons"
                                              else ["m_gimmick_sequence_schedule"])})
        unexpected = sorted(set(actual) - set(expected_static))
        report["diff_vs_orig"] = {
            "changed_tables": actual,
            "expected_effective": expected_effective,
            "expected_static": expected_static,
            "unexpected_tables": unexpected,
            "only_in_output": d["only_right"],
            "only_in_orig": d["only_left"],
            "ok": not unexpected and not d["only_left"] and not d["only_right"],
        }
        if unexpected or d["only_left"] or d["only_right"]:
            if report_path:
                Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
            raise SystemExit("断言 C 失败：diff 超出预期表 → "
                             + json.dumps(report["diff_vs_orig"], ensure_ascii=False))

    # ---- 只动 date 列 / 尾部补行 / 指定清空（编辑器语义守门）----
    cell_checks = {}
    for name in edit_touched:
        if name not in inp.toc or name not in out.toc:
            continue
        cell_checks[name] = classify_table_change(inp.part(name), out.part(name))
    report["cell_level_checks"] = cell_checks
    violations = {k: v for k, v in cell_checks.items() if v.get("kind") not in
                  ("date-only", "append-only", "emptied")}
    report["cell_level_ok"] = not violations
    if violations:
        if report_path:
            Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
        raise SystemExit("编辑器语义守门失败（出现非 date 列/非尾部补行/非清空的变化）→ "
                         + json.dumps(violations, ensure_ascii=False))

    report["ok"] = True
    report["elapsed_sec"] = round(time.time() - t0, 2)
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(f"[build_bin_e] OUT {out.size:,}B sha256={out.sha256}")
    print(f"[build_bin_e] 断言 A 文本格=汉化基 逐字节 OK（5/5）")
    print(f"[build_bin_e] 断言 B 结构（AES/TOC/{len(REQUIRED_TABLES)} 表/LZ4）OK "
          f"({report['structure']['lz4']['lz4_tables']} LZ4 表)")
    if orig_view:
        print(f"[build_bin_e] 断言 C diff vs 原版仅预期表 OK "
              f"({len(report['diff_vs_orig']['changed_tables'])} 表)")
    print(f"[build_bin_e] 编辑项: "
          + ", ".join(f"{k}={len(v.get('changed_tables', []))}表"
                      for k, v in edit_stats.items() if v.get("enabled")))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="JP 客户端 bin.e 构建（汉化 masterdata + 可选编辑项）")
    ap.add_argument("--bin-e", required=True, help="输入 bin.e（原版或汉化；只读）")
    ap.add_argument("--out-bin-e", required=True,
                    help="输出目标 bin.e（= 配套汉化 bin.e；硬性要求：文件名与输入一致，可改目录）")
    ap.add_argument("--bin-edit", default=None,
                    help=f"编辑配置 JSON（缺省 = 全量编辑面；可项 {list(EDIT_KEYS)}）")
    ap.add_argument("--text-from", default=None,
                    help="从该 bin.e 逐字节移植 5 张文本表（权威汉化基 bin_zh_fix6.bin.e）")
    ap.add_argument("--zh-base", default=None,
                    help="断言 A 参照的汉化基（缺省 = --text-from 或 --bin-e 自身）")
    ap.add_argument("--orig-bin-e", default=None,
                    help="断言 C 参照的原版 bin.e（20240404193219.bin.e）")
    ap.add_argument("--report", default=None, help="JSON 报告输出路径")
    ap.add_argument("--dry-run", action="store_true", help="只算编辑统计，不写输出")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    bin_e_in = Path(args.bin_e).resolve()
    bin_e_out = Path(args.out_bin_e).resolve()
    # 硬性要求：bin.e 文件名前后不变（输出文件名 == 输入文件名；可改目录）
    if bin_e_out.name != bin_e_in.name:
        raise SystemExit(
            f"bin.e 文件名前后不变：输出名 {bin_e_out.name!r} != 输入名 {bin_e_in.name!r}"
            f"（可改目录，不可改文件名）")

    build_bin_e(
        bin_e=bin_e_in,
        out_bin_e=bin_e_out,
        bin_edit=Path(args.bin_edit).resolve() if args.bin_edit else None,
        text_from=Path(args.text_from).resolve() if args.text_from else None,
        zh_base=Path(args.zh_base).resolve() if args.zh_base else None,
        orig_bin_e=Path(args.orig_bin_e).resolve() if args.orig_bin_e else None,
        report_path=Path(args.report).resolve() if args.report else None,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
