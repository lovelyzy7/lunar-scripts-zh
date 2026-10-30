#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_fix3l.py — EN 客户端内置弹窗串补丁（**fix3l 扩展键**：漏译弹窗/按钮）。

背景（EN-APK-KO-REPORT §六遗留 + 真机实证）：
  上轮 fix3 覆盖 68 键后，仍有弹窗/按钮类键未译（年龄确认/确认按钮/广告追踪/传输完成 等）。
  本工具补充这些 fix3l 扩展键，EN 段 + ko 段双改。

载体（同 fix3）：
  EN 段: a1e9ec10(ui) / 6c88814b(titleflow) / 1dc4624c(nt)
  ko 段: 311a825b(ui) / 3286caf7(titleflow) / d3f332a2(nt)

长度约束（同前口径）：
  EN 段：无字节约束（上轮 EN 段 25 处增写）
  ko 段：len(new utf-8) <= len(old utf-8) 硬约束（T01 机制）；超长用短译并记录

不在内置表的目标（归 text 侧，本工具不处理）：
  - Confirm Skip / "Skip this story?"（跳过确认）
  - "Are you sure you want to return to the title screen?"（返回标题确认正文）
  - 3D 菜单按钮 Profile/Help/Settings/Official Twitter/Download Data/Credits
    （Title Screen 已由 S11 覆盖 = ui.Outgame.Menu.Title.Jump.Title）
  - 광고 영상 보기（观看广告）

用法：
  python patch_fix3l.py apply  --work DIR [--dry-run]
  python patch_fix3l.py verify --work DIR
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

TS_EN = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": "ui(en)",
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": "titleflow(en)",
}
TS_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": "ui(ko)",
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": "titleflow(ko)",
}

# fix3l 扩展键表：key -> {"en": EN段译文, "ko": ko段译文, "note": 说明}
# ko 段受 ≤原字节约束；超长时 ko 字段用短译并在 note 记录。
FIX3L_KEYS: dict[str, dict] = {
    # ---- 首启年龄确认弹窗 ----
    "titleflow.dialog.ageverification.title": {
        "en": "年龄确认",
        "ko": "年龄确认",
        "note": "Confirm Age / 연령 확인 → 年龄确认；ko 12B≤13B ✓",
    },
    "titleflow.dialog.ageverification.text": {
        "en": "您的年龄是否满16岁？",
        "ko": "是否满16岁？",
        "note": "Is your age 16 years or over? / 16세 이상입니까?；ko 22B 原文装不下「您的年龄是否满16岁？」29B，短译「是否满16岁？」17B",
    },
    # ---- 确认类按钮（上轮 68 键外漏网）----
    "ui.Outgame.Common.Yes": {
        "en": "是",
        "ko": "是",
        "note": "Yes / 예 → 是；ko 3B≤3B ✓",
    },
    "ui.Outgame.Common.No": {
        "en": "否",
        "ko": "否",
        "note": "No / 아니오 → 否；ko 3B≤9B ✓",
    },
    "ui.Outgame.Common.Ok": {
        "en": "确认",
        "ko": "确认",
        "note": "OK / 확인 → 确认；ko 6B≤6B ✓（확□ = 확인 漏网键）",
    },
    # ---- 广告追踪弹窗（광고 관련）----
    "titleflow.dialog.personalizeadd.title": {
        "en": "广告",
        "ko": "广告",
        "note": "Ad Tracking / 광고 → 广告；ko 6B≤6B ✓",
    },
    "titleflow.dialog.personalizeadd.text": {
        "en": (
            "是否愿意共享您的个人信息\\n"
            "以查看符合您兴趣的广告？\\n"
            "您可随时在[设置]菜单中\\n"
            "更改您的选择。\\n"
            "收集的数据详情及第三方广告\\n"
            "供应商的政策可"
            '<link="https://nierreincarnation.com/adpolicy"><color=#DD8888><u>在此</u></color></link>'
            "查看。"
        ),
        "ko": (
            "是否愿意共享您的个人信息\\n"
            "以查看符合您兴趣的广告？\\n"
            "您可随时在[设置]菜单中\\n"
            "更改您的选择。\\n"
            "收集的数据详情及第三方广告\\n"
            "供应商的政策可"
            '<link="https://nierreincarnation.com/adpolicy"><color=#DD8888><u>在此</u></color></link>'
            "查看。"
        ),
        "note": "广告个性化说明；保留 \\n 字面与 <link>/<color>/<u> 富文本标记",
    },
    # ---- 数据传输完成弹窗 ----
    "ui.Outgame.Menu.DataLinkage.TransferCompletedTitle": {
        "en": "成功",
        "ko": "成功",
        "note": "Success / 성공 → 成功；ko 6B≤6B ✓",
    },
    "ui.Outgame.Menu.DataLinkage.TransferCompletedDescription": {
        "en": "传输完成。",
        "ko": "传输完成。",
        "note": "Transfer completed. / 전송이 완료되었습니다. → 传输完成。；ko 15B≤32B ✓",
    },
    # ---- CBT 卸载请求弹窗 ----
    "titleflow.dialog.confirm.ban.cbt.title": {
        "en": "卸载请求",
        "ko": "卸载请求",
        "note": "Uninstallation Request / 삭제 요청 → 卸载请求；ko 12B≤13B ✓",
    },
    # ---- UI 标签 ----
    "ui.Loading.Text": {
        "en": "加载中...",
        "ko": "加载中",
        "note": "Loading... → 加载中；ko 原文 10B 装不下「加载中...」12B，短译「加载中」9B",
    },
    "titleflow.taptostart": {
        "en": "点击开始",
        "ko": "点击开始",
        "note": "TAP TO START → 点击开始；ko 12B≤12B ✓",
    },
    "titleflow.predownload.preceding": {
        "en": "预下载",
        "ko": "预下载",
        "note": "PREDOWNLOAD / PRECEDING DOWNLOAD → 预下载；ko 9B≤18B ✓",
    },
}

APPLY_REPORT = HERE / "apply_report_fix3l.json"
VERIFY_REPORT = HERE / "verify_report_fix3l.json"


def sha256(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def _ta_text(d) -> str:
    s = getattr(d, "m_Script", None)
    return s.decode("utf-8") if isinstance(s, bytes) else s


def patch_textasset(buf: bytes, kmap: dict[str, str], enforce_len: bool,
                    label: str) -> tuple[bytes, list[dict]]:
    """按键替换值；enforce_len=True 时强制 len(new)<=len(old)。"""
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
        changed, skipped = [], []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            sep = line.find(":")
            if sep <= 0:
                continue
            key, value = line[:sep], line[sep + 1:]
            if key not in kmap:
                continue
            new_val = kmap[key]
            if new_val == value:
                continue
            ob = value.encode("utf-8")
            nb = new_val.encode("utf-8")
            if enforce_len and len(nb) > len(ob):
                skipped.append({
                    "key": key, "old": value, "new": new_val, "status": "SKIP_TOO_LONG",
                    "old_bytes": len(ob), "new_bytes": len(nb),
                    "reason": "T01 机制 len(new)<=len(old) 未满足",
                })
                continue
            lines[i] = f"{key}:{new_val}"
            changed.append({
                "key": key, "old": value, "new": new_val,
                "old_bytes": len(ob), "new_bytes": len(nb),
            })
        if changed:
            any_change = True
            new_text = "\n".join(lines) + ("\n" if trailing else "")
            d.m_Script = new_text
            d.save()
        log.append({"asset": name, "label": label, "changed": changed, "skipped": skipped,
                    "changed_count": len(changed), "skipped_count": len(skipped)})
    if not any_change:
        return buf, log
    fobj = list(env.files.values())[0]
    return fobj.save(), log


def verify_textasset(new: bytes, kmap: dict[str, str], old_vals: dict[str, str]) -> dict:
    import UnityPy

    env = UnityPy.load(new)
    res: dict = {"ok": True, "checks": {}}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", None) or getattr(d, "name", None)
        text = _ta_text(d)
        lines = text.split("\n")
        kv = {}
        for line in lines:
            sep = line.find(":")
            if sep > 0:
                kv[line[:sep]] = line[sep + 1:]
        per, old_residual, bad = {}, [], []
        for k, zh in kmap.items():
            if k not in kv:
                continue
            is_zh = kv[k] == zh
            old_v = old_vals.get(k)
            old_left = (old_v is not None and kv[k] == old_v)
            per[k] = {"value": kv[k], "is_zh": is_zh, "old_value_residual": old_left}
            if not is_zh:
                bad.append(k)
            if old_left:
                old_residual.append(k)
        res["checks"][name] = {
            "keys_found": len(per), "zh_hits": sum(1 for v in per.values() if v["is_zh"]),
            "bad": bad, "old_value_residual_keys": old_residual,
            "old_value_residual_total": len(old_residual),
            "line_count": len(lines), "keys": per,
        }
        if bad or old_residual:
            res["ok"] = False
    return res


def cmd_apply(work: Path, dry_run: bool) -> int:
    en_map = {k: v["en"] for k, v in FIX3L_KEYS.items()}
    ko_map = {k: v["ko"] for k, v in FIX3L_KEYS.items()}
    print(f"[fix3l] keys={len(FIX3L_KEYS)} (EN+ko 双段)")
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": "patch_fix3l.py",
        "dry_run": dry_run, "keys": FIX3L_KEYS,
        "length_rule": "EN 段无约束；ko 段 len(new)<=len(old) 硬约束，超长短译已记录",
        "files": {}, "ok": True,
    }
    old_vals_all: dict[str, str] = {}

    # --- EN 段（无字节约束）---
    for entry, label in TS_EN.items():
        p = work / entry
        if not p.is_file():
            report["files"][entry] = {"missing": True}
            report["ok"] = False
            print(f"[fix3l] MISSING {entry}")
            continue
        raw = p.read_bytes()
        import UnityPy
        env = UnityPy.load(raw)
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            text = _ta_text(obj.read())
            for line in text.split("\n"):
                sep = line.find(":")
                if sep > 0 and line[:sep] in en_map:
                    old_vals_all[f"en:{line[:sep]}"] = line[sep + 1:]
        out, log = patch_textasset(raw, en_map, enforce_len=False, label=label)
        n = sum(x["changed_count"] for x in log)
        n_skip = sum(x["skipped_count"] for x in log)
        if n_skip:
            report["ok"] = False
        report["files"][entry] = {
            "label": label, "segment": "en", "sha256_before": sha256(raw),
            "sha256_after": sha256(out), "changed": raw != out,
            "changed_count": n, "skipped_count": n_skip, "log": log,
        }
        print(f"[fix3l] {label} changed_lines={n} skipped={n_skip}")
        if not dry_run and raw != out:
            p.write_bytes(out)

    # --- ko 段（≤原字节约束）---
    for entry, label in TS_KO.items():
        p = work / entry
        if not p.is_file():
            report["files"][entry] = {"missing": True}
            report["ok"] = False
            print(f"[fix3l] MISSING {entry}")
            continue
        raw = p.read_bytes()
        import UnityPy
        env = UnityPy.load(raw)
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            text = _ta_text(obj.read())
            for line in text.split("\n"):
                sep = line.find(":")
                if sep > 0 and line[:sep] in ko_map:
                    old_vals_all[f"ko:{line[:sep]}"] = line[sep + 1:]
        out, log = patch_textasset(raw, ko_map, enforce_len=True, label=label)
        n = sum(x["changed_count"] for x in log)
        n_skip = sum(x["skipped_count"] for x in log)
        if n_skip:
            report["ok"] = False
        report["files"][entry] = {
            "label": label, "segment": "ko", "sha256_before": sha256(raw),
            "sha256_after": sha256(out), "changed": raw != out,
            "changed_count": n, "skipped_count": n_skip, "log": log,
        }
        print(f"[fix3l] {label} changed_lines={n} skipped={n_skip}")
        if not dry_run and raw != out:
            p.write_bytes(out)

    report["old_values"] = old_vals_all
    report["changed_total"] = sum(v.get("changed_count", 0)
                                  for v in report["files"].values() if isinstance(v, dict))
    APPLY_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fix3l] report -> {APPLY_REPORT}")
    return 0 if report["ok"] else 1


def cmd_verify(work: Path) -> int:
    en_map = {k: v["en"] for k, v in FIX3L_KEYS.items()}
    ko_map = {k: v["ko"] for k, v in FIX3L_KEYS.items()}
    old_vals = {}
    if APPLY_REPORT.is_file():
        old_vals = json.loads(APPLY_REPORT.read_text(encoding="utf-8")).get("old_values", {})
    ok_all = True
    vreport = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "tool": "patch_fix3l.py verify", "files": {}}
    for entry, label in TS_EN.items():
        p = work / entry
        if not p.is_file():
            vreport["files"][label] = {"missing": True}
            ok_all = False
            continue
        res = verify_textasset(p.read_bytes(), en_map, {k[3:]: v for k, v in old_vals.items() if k.startswith("en:")})
        vreport["files"][label] = res
        for name, c in res["checks"].items():
            print(f"[verify-fix3l] {name}: keys={c['keys_found']} zh={c['zh_hits']} "
                  f"bad={len(c['bad'])} old_residual={c['old_value_residual_total']}")
        if not res["ok"]:
            ok_all = False
    for entry, label in TS_KO.items():
        p = work / entry
        if not p.is_file():
            vreport["files"][label] = {"missing": True}
            ok_all = False
            continue
        res = verify_textasset(p.read_bytes(), ko_map, {k[3:]: v for k, v in old_vals.items() if k.startswith("ko:")})
        vreport["files"][label] = res
        for name, c in res["checks"].items():
            print(f"[verify-fix3l] {name}: keys={c['keys_found']} zh={c['zh_hits']} "
                  f"bad={len(c['bad'])} old_residual={c['old_value_residual_total']}")
        if not res["ok"]:
            ok_all = False
    vreport["ok"] = ok_all
    VERIFY_REPORT.write_text(json.dumps(vreport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify-fix3l] ok={ok_all} report -> {VERIFY_REPORT}")
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
