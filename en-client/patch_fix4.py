#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_fix4.py — EN 客户端内置表纯净化（en-fix4）。

任务：
  A. EN 段还原：81 键（68 fix3 + 13 fix3l）还原为原版英文值（从原版 EN APK 提取）；
     metadata 7 串保持中文（用户默认裁定=目标态纯净优先，可否决还原）。
  B. ko 段 67 nt 键翻译：将 nt(ko) 段 67 个韩文网络错误串译为中文（≤原字节约束）。
  C. 3D 菜单按钮：不在内置表（已查证），归 text 侧，本工具不处理。

载体：
  EN 段: a1e9ec10(ui) / 6c88814b(titleflow) / 1dc4624c(nt)
  ko 段: 311a825b(ui) / 3286caf7(titleflow) / d3f332a2(nt)

用法：
  python patch_fix4.py apply  --work DIR [--dry-run]
  python patch_fix4.py verify --work DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

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

# 原版 EN 值（从原版 EN APK 提取，fix4_orig_en_values.json）
ORIG_EN_JSON = HERE / "fix4_orig_en_values.json"

# ---- ko 段 67 nt 键翻译表 ----
# key -> {"zh": 中文译文, "note": 说明}
# 约束：len(zh utf-8) <= len(ko 原值 utf-8)；超长用短译或 SKIP。
NT_KO_TRANSLATIONS: dict[str, dict] = {
    "nt.Network.1020013": {
        "zh": "此存档仅供CBT测试使用。\\n请卸载本应用后重新安装NieR Re[in]carnation以体验正式版。",
        "note": "CBT 专用提示",
    },
    "nt.Network.Error.Title.DataUpdate": {
        "zh": "刷新",
        "note": "Refresh → 刷新",
    },
    "nt.Network.Error.Message.Default": {
        "zh": "发生错误。\\n【{0}】",
        "note": "通用错误",
    },
    "nt.Network.Error.Message.NoTransition": {
        "zh": "功能错误。无跳转目标。{0}",
        "note": "无跳转目标",
    },
    "nt.Network.Error.Message.LackCapacity": {
        "zh": "设备存储空间不足，\\n无法运行游戏。\\n\\n请删除不必要的应用或数据\\n以腾出空间。",
        "note": "存储不足",
    },
    "nt.Network.Error.Message.FatalDownload": {
        "zh": "下载失败。",
        "note": "下载失败",
    },
    "nt.Network.Error.Message.MasterDownload": {
        "zh": "获取新数据失败。",
        "note": "主数据下载失败",
    },
    "nt.Network.Error.Message.AssetLoad": {
        "zh": "数据下载失败。",
        "note": "资源加载失败",
    },
    "nt.Network.Error.Message.AssetFatalError": {
        "zh": "数据下载失败。\\n返回标题画面。",
        "note": "资源致命错误",
    },
    "nt.Network.Error.Message.BridgeUser": {
        "zh": "玩家数据继承失败。",
        "note": "数据继承失败",
    },
    "nt.Network.Error.Message.Connect": {
        "zh": "通信失败。",
        "note": "连接失败",
    },
    "nt.Network.Error.Message.PermissionDenied": {
        "zh": "您所在的国家或地区无法使用本应用。",
        "note": "地区限制",
    },
    "nt.Network.100000": {
        "zh": "目前正在进行维护。",
        "note": "维护中",
    },
    "nt.Network.100001": {
        "zh": "目前正在进行维护。",
        "note": "维护中",
    },
    "nt.Network.101003": {
        "zh": "包含不可使用的词语。",
        "note": "敏感词",
    },
    "nt.Network.102002": {
        "zh": "检测到异常存档。\\n已暂停使用。\\n如有疑问请联系：",
        "note": "异常存档",
    },
    "nt.Network.103000": {
        "zh": "发现新版本。\\n请通过商店更新游戏。",
        "note": "版本更新",
    },
    "nt.Network.103001": {
        "zh": "返回标题画面。",
        "note": "返回标题",
    },
    "nt.Network.104000": {
        "zh": "新数据已更新。返回标题画面。",
        "note": "数据更新完成",
    },
    "nt.Network.105000": {
        "zh": "不在活动期间。",
        "note": "时间限制",
    },
    "nt.Network.105001": {
        "zh": "活动已结束，无法领取奖励。",
        "note": "活动结束",
    },
    "nt.Network.200011": {
        "zh": "需要等待一段时间后\\n才能再次修改玩家名称。",
        "note": "改名冷却",
    },
    "nt.Network.200012": {
        "zh": "需要等待一段时间后\\n才能再次修改评论。",
        "note": "改评论冷却",
    },
    "nt.Network.200013": {
        "zh": "需要等待一段时间后\\n才能再次修改收藏。",
        "note": "改收藏冷却",
    },
    "nt.Network.200018": {
        "zh": "体力不足。",
        "note": "体力不足",
    },
    "nt.Network.200019": {
        "zh": "体力已满。",
        "note": "体力已满",
    },
    "nt.Network.200021": {
        "zh": "BP不足。",
        "note": "BP不足",
    },
    "nt.Network.200022": {
        "zh": "BP已满。",
        "note": "BP已满",
    },
    "nt.Network.201001": {
        "zh": "日期已变更，商品已刷新。\\n请重新尝试。",
        "note": "商店刷新",
    },
    "nt.Network.201002": {
        "zh": "已达持有上限，无法继续购买。",
        "note": "持有上限",
    },
    "nt.Network.201003": {
        "zh": "因已购买过该商品，\\n无法领取。",
        "note": "重复购买",
    },
    "nt.Network.201100": {
        "zh": "因已购买过该商品，\\n无法领取。\\n请通过菜单咨询。",
        "note": "重复购买+咨询",
    },
    "nt.Network.202001": {
        "zh": "该任务不存在。",
        "note": "任务不存在",
    },
    "nt.Network.202002": {
        "zh": "该任务已完成。",
        "note": "任务已完成",
    },
    "nt.Network.202004": {
        "zh": "该任务尚未解锁。",
        "note": "任务未解锁",
    },
    "nt.Network.202005": {
        "zh": "今日通关次数已用完。",
        "note": "次数用完",
    },
    "nt.Network.203001": {
        "zh": "有尚未领取的礼物。",
        "note": "未领礼物",
    },
    "nt.Network.204001": {
        "zh": "已向该玩家发送过好友申请。",
        "note": "重复申请",
    },
    "nt.Network.204002": {
        "zh": "好友数量已达上限。",
        "note": "好友上限",
    },
    "nt.Network.204003": {
        "zh": "该玩家已是您的好友。",
        "note": "已是好友",
    },
    "nt.Network.204004": {
        "zh": "找不到该玩家。",
        "note": "找不到玩家",
    },
    "nt.Network.204005": {
        "zh": "已发送过声援。",
        "note": "重复声援",
    },
    "nt.Network.204006": {
        "zh": "找不到该玩家。",
        "note": "找不到玩家",
    },
    "nt.Network.204007": {
        "zh": "已收到过声援。",
        "note": "重复收声援",
    },
    "nt.Network.204008": {
        "zh": "对方好友数已达上限，\\n无法发送申请。",
        "note": "对方好友上限",
    },
    "nt.Network.204009": {
        "zh": "发送申请的玩家好友数已达上限。",
        "note": "对方好友上限",
    },
    "nt.Network.204010": {
        "zh": "今日次数已达上限，\\n无法继续发送声援。",
        "note": "声援次数上限",
    },
    "nt.Network.204011": {
        "zh": "今日次数已达上限，\\n无法继续接收声援。",
        "note": "收声援次数上限",
    },
    "nt.Network.205001": {
        "zh": "角色未编入队伍。",
        "note": "角色未编入",
    },
    "nt.Network.290000": {
        "zh": "当前访问拥挤，请稍后重试。",
        "note": "访问拥挤",
    },
    "nt.Network.290021": {
        "zh": "检测到异常存档。\\n已暂停使用。\\n如有疑问请联系：",
        "note": "异常存档",
    },
    "nt.Network.290024": {
        "zh": "创建玩家失败。",
        "note": "创建玩家失败",
    },
    "nt.Network.290030": {
        "zh": "宝石不足。",
        "note": "宝石不足",
    },
    "nt.Network.290043": {
        "zh": "消费金额已达上限。",
        "note": "消费上限",
    },
    "nt.Network.400000": {
        "zh": "暂无公告。",
        "note": "无公告",
    },
    "nt.Network.900000": {
        "zh": "处理失败。返回标题画面。",
        "note": "处理失败",
    },
    "nt.Network.900001": {
        "zh": "连接失败。正在重试。",
        "note": "连接失败重试",
    },
    "nt.Network.900002": {
        "zh": "处理失败。",
        "note": "处理失败",
    },
    "nt.Network.menu": {
        "zh": "菜单界面发生通信错误。",
        "note": "菜单通信错误",
    },
    "nt.Network.home_top": {
        "zh": "主页界面发生通信错误。",
        "note": "主页通信错误",
    },
    "nt.Network.organization": {
        "zh": "编队界面发生通信错误。",
        "note": "编队通信错误",
    },
    "nt.Network.arena_top": {
        "zh": "竞技场界面发生通信错误。",
        "note": "竞技场通信错误",
    },
    "nt.Network.enhance_top": {
        "zh": "强化界面发生通信错误。",
        "note": "强化通信错误",
    },
    "nt.Network.shop_top": {
        "zh": "商店界面发生通信错误。",
        "note": "商店通信错误",
    },
    "nt.Network.gacha_top": {
        "zh": "扭蛋界面发生通信错误。",
        "note": "扭蛋通信错误",
    },
    "nt.Network.quest_top": {
        "zh": "任务界面发生通信错误。",
        "note": "任务通信错误",
    },
    "nt.Network.search_top": {
        "zh": "探索界面发生通信错误。",
        "note": "探索通信错误",
    },
}

APPLY_REPORT = HERE / "apply_report_fix4.json"
VERIFY_REPORT = HERE / "verify_report_fix4.json"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_orig_en() -> dict[str, str]:
    if not ORIG_EN_JSON.is_file():
        raise FileNotFoundError(f"原版 EN 值文件不存在: {ORIG_EN_JSON}")
    return json.loads(ORIG_EN_JSON.read_text(encoding="utf-8"))


def _ta_text(d) -> str:
    s = getattr(d, "m_Script", None)
    return s.decode("utf-8") if isinstance(s, bytes) else s


def patch_textasset_keyed(buf: bytes, kmap: dict[str, str],
                          length_constraint: bool = False) -> tuple[bytes, list[dict]]:
    """按 key 列表替换值。length_constraint=True 时强制 len(new) <= len(old)。"""
    import UnityPy

    env = UnityPy.load(buf)
    log: list[dict] = []
    any_change = False
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", None) or getattr(d, "name", None)
        text = _ta_text(d)
        trailing = text.endswith("\n")
        lines = text.split("\n")
        if trailing and lines and lines[-1] == "":
            lines = lines[:-1]
        changed = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            sep = line.find(":")
            if sep <= 0:
                continue
            key, value = line[:sep], line[sep + 1:]
            if key in kmap:
                new_val = kmap[key]
                if length_constraint and len(new_val.encode("utf-8")) > len(value.encode("utf-8")):
                    changed.append({"key": key, "old": value[:40], "new": new_val[:40],
                                    "status": "SKIP_TOO_LONG",
                                    "old_bytes": len(value.encode("utf-8")),
                                    "new_bytes": len(new_val.encode("utf-8"))})
                    continue
                new_line = f"{key}:{new_val}"
                if new_line != line:
                    lines[i] = new_line
                    changed.append({"key": key, "old": value[:40], "new": new_val[:40],
                                    "status": "PATCHED"})
        if any(c.get("status") == "PATCHED" for c in changed):
            any_change = True
            new_text = "\n".join(lines) + ("\n" if trailing else "")
            d.m_Script = new_text
            d.save()
        log.append({"asset": name, "changed": changed, "changed_count": len(changed)})
    if not any_change:
        return buf, log
    fobj = list(env.files.values())[0]
    return fobj.save(), log


def cmd_apply(work: Path, dry_run: bool) -> int:
    orig_en = load_orig_en()
    print(f"[fix4] EN 段还原 {len(orig_en)} 键")
    print(f"[fix4] ko 段 nt 翻译 {len(NT_KO_TRANSLATIONS)} 键")

    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": "patch_fix4.py",
              "dry_run": dry_run, "en_restore": {"keys": len(orig_en)},
              "ko_nt_translate": {"keys": len(NT_KO_TRANSLATIONS)},
              "files": {}, "ok": True}

    # ---- EN 段还原：81 键 → 原版英文 ----
    for entry, label in TS_EN.items():
        p = work / entry
        if not p.is_file():
            report["files"][entry] = {"missing": True}
            report["ok"] = False
            print(f"[fix4] MISSING {entry}")
            continue
        raw = p.read_bytes()
        out, log = patch_textasset_keyed(raw, orig_en)
        n = sum(x["changed_count"] for x in log)
        report["files"][entry] = {"label": label, "action": "en_restore",
                                  "sha256_before": sha256(raw), "sha256_after": sha256(out),
                                  "changed": raw != out, "changed_count": n, "log": log}
        print(f"[fix4] {label} EN restore changed={n}")
        if not dry_run and raw != out:
            p.write_bytes(out)

    # ---- ko 段 nt 翻译：67 键 → 中文（≤原字节约束）----
    nt_ko_entry = "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7"
    p = work / nt_ko_entry
    if not p.is_file():
        report["files"][nt_ko_entry] = {"missing": True}
        report["ok"] = False
        print(f"[fix4] MISSING {nt_ko_entry}")
    else:
        raw = p.read_bytes()
        out, log = patch_textasset_keyed(raw, {k: v["zh"] for k, v in NT_KO_TRANSLATIONS.items()},
                                         length_constraint=True)
        n = sum(x["changed_count"] for x in log)
        n_patched = sum(1 for x in log for c in x["changed"] if c.get("status") == "PATCHED")
        n_skip = sum(1 for x in log for c in x["changed"] if c.get("status") == "SKIP_TOO_LONG")
        report["files"][nt_ko_entry] = {"label": "nt(ko)", "action": "ko_nt_translate",
                                        "sha256_before": sha256(raw), "sha256_after": sha256(out),
                                        "changed": raw != out,
                                        "changed_count": n, "patched": n_patched, "skipped": n_skip,
                                        "log": log}
        print(f"[fix4] nt(ko) translate patched={n_patched} skipped={n_skip}")
        if not dry_run and raw != out:
            p.write_bytes(out)

    (HERE / "apply_report_fix4.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fix4] report -> {APPLY_REPORT}")
    return 0 if report["ok"] else 1


def cmd_verify(work: Path) -> int:
    import UnityPy

    orig_en = load_orig_en()
    ok_all = True
    vreport = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": {}}

    # ---- EN 段回读：81 键 = 原版英文值 ----
    for entry, label in TS_EN.items():
        p = work / entry
        if not p.is_file():
            vreport["files"][label] = {"missing": True}
            ok_all = False
            continue
        raw = p.read_bytes()
        env = UnityPy.load(raw)
        kv = {}
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                text = _ta_text(obj.read())
                for line in text.split("\n"):
                    sep = line.find(":")
                    if sep > 0:
                        kv[line[:sep]] = line[sep + 1:]
        hits = {}
        for k, expected in orig_en.items():
            if k in kv:
                hits[k] = {"value": kv[k][:40], "is_orig_en": kv[k] == expected}
        bad = [k for k, v in hits.items() if not v["is_orig_en"]]
        missing = [k for k in orig_en if k not in hits]
        vreport["files"][label] = {"action": "en_restore", "hits": len(hits),
                                   "bad": bad, "missing_keys_count": len(missing)}
        print(f"[verify] {label} EN restore: hits={len(hits)} bad={len(bad)}")
        if bad:
            ok_all = False

    # ---- ko 段 nt 回读：67 键 = 中文 ----
    nt_ko_entry = "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7"
    p = work / nt_ko_entry
    if p.is_file():
        raw = p.read_bytes()
        env = UnityPy.load(raw)
        kv = {}
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                text = _ta_text(obj.read())
                for line in text.split("\n"):
                    sep = line.find(":")
                    if sep > 0:
                        kv[line[:sep]] = line[sep + 1:]
        hits = {}
        for k, spec in NT_KO_TRANSLATIONS.items():
            if k in kv:
                hits[k] = {"value": kv[k][:40], "is_zh": kv[k] == spec["zh"]}
        bad = [k for k, v in hits.items() if not v["is_zh"]]
        vreport["files"]["nt(ko)"] = {"action": "ko_nt_translate", "hits": len(hits),
                                      "bad": bad}
        print(f"[verify] nt(ko) translate: hits={len(hits)} bad={len(bad)}")
        if bad:
            ok_all = False

    vreport["ok"] = ok_all
    VERIFY_REPORT.write_text(json.dumps(vreport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify] ok={ok_all}")
    return 0 if ok_all else 1


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--work", required=True)
    p_apply.add_argument("--dry-run", action="store_true")
    p_ver = sub.add_parser("verify")
    p_ver.add_argument("--work", required=True)
    args = ap.parse_args()
    if args.cmd == "apply":
        return cmd_apply(Path(args.work).resolve(), args.dry_run)
    return cmd_verify(Path(args.work).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
