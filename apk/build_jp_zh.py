#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_jp_zh.py — JP 汉化客户端构建驱动（私服补丁 → fix3 内置串 → 字体 payload → mod 菜单 → 签名）。

复用 NieR-Re-In-Carnation-Mod_Menu/jp-client/tools 的构建管线：
  * 菜单编译/extract:        build_menu.build_apk / build_menu.extract
  * 解包/注入/重建/对齐/签名:  inject_modmenu.* （含本任务新增的 inject_fonts）
  * 工具/密钥配置:            jp-client/tools/toolpaths.json（apktool / Android SDK / nier-jp.keystore）

两种模式：
  * patched （推荐/可部署）：原版 APK → lunar-scripts-jp 私服补丁 → fix3 内置串补丁
    （fix3/patch_fix3.py apply --tier all，就地，含 supplement 8 条）→ 字体 payload
    → mod 菜单注入 → apktool b → zipalign → apksigner（nier-jp key）
  * original（字面任务基线）：原版 APK → 字体 payload → mod 菜单注入 → 签名（不含私服补丁）

用法：
  python build_jp_zh.py --mode patched \
      --apk "resources/NieR Re[in]carnation_3.7.1_JP.apk" \
      --out "zh-l10n/work/apk/nier-mod-menu-jp-font-fix3.apk" \
      --work "NieR-Re-In-Carnation-Mod_Menu/jp-client/build/work_jp_zh_patched" \
      --font-payload "zh-l10n/work/fonts/out/payload" \
      --grpc 192.168.2.6:8003 --http 192.168.2.6:8080 --auth 192.168.2.6:3000

产物：APK + 构建日志 + evidence JSON（均在 --out 所在目录/logs）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(r"E:\NieRReincarnation")
JP_CLIENT = ROOT / "NieR-Re-In-Carnation-Mod_Menu" / "jp-client"
TOOLS = JP_CLIENT / "tools"
PATCH_JP = ROOT / "lunar-scripts-jp" / "android" / "patch_apk_jp.py"
FONT_SETS = {
    # APK 内字体 SerializedFile 条目名 → 角色
    "6f937efa0660c47f59d5215d276b1cbb": "RodinPro-UI(Medium 子集)",
    "7089ac60979c94824ac549baab08cfa7": "TalkingStd-Story(Regular 子集)",
}
EXPECTED_CERT_SHA256 = "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe"
# fix3 内置串补丁（zh-l10n\work\apk\fix3）：就地 apply 于解包目录（私服补丁后、字体前）
FIX3_DIR = ROOT / "zh-l10n" / "work" / "apk" / "fix3"
FIX3_PATCHER = FIX3_DIR / "patch_fix3.py"
VENV_PY = ROOT / "zh-l10n" / ".venv" / "Scripts" / "python.exe"  # UnityPy 所在 venv（缺 UnityPy 时挂其 site-packages）
FIX3_TIER = "all"  # apply 15 条 + supplement 8 条
# fix3 自检抽查：解包目录内各载体必须命中的译文（UTF-8 子串）
FIX3_SPOT_CHECKS = {
    "assets/bin/Data/35005335013ad4314b0ac8afbfe27b9c": [  # TextAsset "ui"
        "公告", "联系我们", "数据继承", "数据修复", "其他信息", "删除数据",
        "关闭", "取消", "下载确认",                              # T01-T08/T15
        "将进行数据修复。确定吗？", "数据修复已完成", "菜单", "删除", "同意",  # S04-S08
        "结束游戏", "要结束游戏吗？", "返回标题", "错误", "维护中",  # S09-S14 fix3b 漏译弹窗
    ],
    "assets/bin/Data/5296ae89c03c14825a9f664b0c355ccc": [  # TextAsset "titleflow"
        "下载确认", "注册玩家名", "请输入玩家名",                  # T08/T11/T12
        "将开始约{0}MB的数据下载", "下载设置",                    # S01/S03
        "网络错误", "重试", "序列号", "继续", "放弃",              # S26-S30/S37 fix3b
    ],
}
FIX3_META_SPOT = ["公告", "关闭", "取消",                        # stringLiteral T01/T07/T15
                  "播放影片", "播放影片中", "打开公告", "打开推特"]  # fix3b S43-S46


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            try:
                stream.write(text)
            except Exception:  # noqa: BLE001
                pass

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:  # noqa: BLE001
                pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_logged(cmd, log_path: Path, cwd=None, env=None) -> tuple[int, list[str]]:
    """运行外部命令，stdout/stderr 同时写日志并返回最后若干行。"""
    lines: list[str] = []
    with log_path.open("a", encoding="utf-8", errors="replace") as log:
        log.write("\n$ " + " ".join(str(c) for c in cmd) + "\n")
        log.flush()
        proc = subprocess.Popen([str(c) for c in cmd], cwd=cwd, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace")
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            log.write(line)
            lines.append(line.rstrip("\n"))
        rc = proc.wait()
    return rc, lines


def font_payload_meta(payload_dir: Path) -> dict:
    files = {}
    for p in sorted(payload_dir.iterdir()):
        if p.is_file():
            files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    if not files:
        raise SystemExit(f"字体 payload 为空: {payload_dir}")
    missing = [name for name in FONT_SETS if name not in files]
    if missing:
        raise SystemExit(f"字体 payload 缺少必需文件: {missing}")
    return files


def app_original_hashes(apk: Path) -> dict:
    with zipfile.ZipFile(apk) as zf:
        out = {}
        for name in ("lib/arm64-v8a/libil2cpp.so",
                     "assets/bin/Data/Managed/Metadata/global-metadata.dat",
                     "AndroidManifest.xml"):
            out[name] = sha256_bytes(zf.read(name))
        return out


def verify_fix3_workdir(work: Path) -> dict:
    """fix3 就地补丁自检：TextAsset 译文 + metadata stringLiteral 抽查。"""
    checks: dict = {"textassets": {}, "metadata": {}}
    for rel, needles in FIX3_SPOT_CHECKS.items():
        p = work / rel
        blob = p.read_bytes() if p.is_file() else b""
        checks["textassets"][rel] = {
            "exists": p.is_file(),
            "hits": {n: (n.encode("utf-8") in blob) for n in needles},
        }
    meta = work / "assets" / "bin" / "Data" / "Managed" / "Metadata" / "global-metadata.dat"
    blob = meta.read_bytes() if meta.is_file() else b""
    checks["metadata"] = {
        "exists": meta.is_file(),
        "hits": {n: (n.encode("utf-8") in blob) for n in FIX3_META_SPOT},
    }
    checks["ok"] = bool(
        checks["metadata"]["exists"]
        and all(checks["metadata"]["hits"].values())
        and all(v["exists"] and all(v["hits"].values()) for v in checks["textassets"].values())
    )
    return checks


def verify_workdir(work: Path, payload: dict, mode: str, grpc_host: str) -> dict:
    checks: dict = {}
    data_dir = work / "assets" / "bin" / "Data"
    checks["font_files"] = {}
    for name, meta in payload.items():
        dst = data_dir / name
        checks["font_files"][name] = {
            "exists": dst.is_file(),
            "sha256": sha256_file(dst) if dst.is_file() else None,
            "matches_payload": dst.is_file() and sha256_file(dst) == meta["sha256"],
        }
    # 菜单注入产物
    support_smali = []
    for entry in work.iterdir():
        if re.fullmatch(r"smali(?:_classes\d+)?", entry.name) and entry.is_dir():
            p = entry / "com" / "android" / "support" / "Main.smali"
            if p.is_file():
                support_smali.append(str(p.relative_to(work)))
    checks["menu"] = {
        "main_smali": support_smali,
        "libniermenu_so": (work / "lib" / "arm64-v8a" / "libniermenu.so").is_file(),
        "libniermenu_so_bytes": (work / "lib" / "arm64-v8a" / "libniermenu.so").stat().st_size
        if (work / "lib" / "arm64-v8a" / "libniermenu.so").is_file() else None,
    }
    manifest = (work / "AndroidManifest.xml").read_text(encoding="utf-8", errors="replace")
    checks["manifest"] = {
        "has_system_alert_window": "SYSTEM_ALERT_WINDOW" in manifest,
        "has_menu_service": "com.android.support.Launcher" in manifest,
    }
    # 启动注入标记
    start_mark = "Lcom/android/support/Main;->Start(Landroid/content/Context;)V"
    start_hits = []
    for entry in work.iterdir():
        if re.fullmatch(r"smali(?:_classes\d+)?", entry.name) and entry.is_dir():
            for smali in entry.rglob("*.smali"):
                try:
                    if start_mark in smali.read_text(encoding="utf-8", errors="ignore"):
                        start_hits.append(str(smali.relative_to(work)))
                except OSError:
                    continue
    checks["start_call"] = start_hits
    # 私服补丁标记
    checks["private_patch"] = {"mode": mode}
    if mode == "patched":
        net_cfg = []
        for p in data_dir.iterdir():
            if p.is_file() and p.stat().st_size < 65536:
                try:
                    blob = p.read_bytes()
                except OSError:
                    continue
                if b"network_config" in blob and b"2019.4.29f1" in blob:
                    net_cfg.append({"file": p.name, "has_grpc_host": grpc_host.encode() in blob})
        auth_host = list(work.rglob("AuthHost.smali"))
        checks["private_patch"].update({
            "network_config": net_cfg,
            "authhost_smali": [str(p.relative_to(work)) for p in auth_host],
        })
    checks["ok"] = bool(
        all(v["matches_payload"] for v in checks["font_files"].values())
        and checks["menu"]["main_smali"]
        and checks["menu"]["libniermenu_so"]
        and checks["manifest"]["has_system_alert_window"]
        and checks["manifest"]["has_menu_service"]
        and checks["start_call"]
        and (mode != "patched" or (
            checks["private_patch"]["network_config"]
            and any(x["has_grpc_host"] for x in checks["private_patch"]["network_config"])
            and checks["private_patch"]["authhost_smali"]
        ))
    )
    return checks


def apksigner_verify(java: Path, apksigner_jar: Path, apk: Path, log_path: Path) -> dict:
    rc, lines = run_logged([java, "-jar", apksigner_jar, "verify", "-v", "--print-certs", apk], log_path)
    text = "\n".join(lines)
    cert = None
    m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F:]+)", text)
    if m:
        cert = m.group(1).replace(":", "").lower()
    return {
        "exit_code": rc,
        "verified_v2": "Verified using v2 scheme (APK Signature Scheme v2): true" in text,
        "verified_v3": "Verified using v3 scheme (APK Signature Scheme v3): true" in text,
        "cert_sha256": cert,
        "cert_matches_expected": cert == EXPECTED_CERT_SHA256,
        "output_tail": lines[-12:],
    }


def zipalign_check(zipalign: Path, apk: Path, log_path: Path) -> dict:
    rc, lines = run_logged([zipalign, "-c", "-p", "4", apk], log_path)
    return {"exit_code": rc, "ok": rc == 0, "output_tail": lines[-5:]}


def apk_final_check(apk: Path, payload: dict, mode: str) -> dict:
    result: dict = {"bytes": apk.stat().st_size, "sha256": sha256_file(apk)}
    with zipfile.ZipFile(apk) as zf:
        result["zip_ok"] = zf.testzip() is None
        result["entries"] = len(zf.namelist())
        result["signature_meta"] = sorted(n for n in zf.namelist()
                                          if n.startswith("META-INF/") and n.upper().endswith(
                                              (".SF", ".RSA", ".DSA", ".EC", "MANIFEST.MF")))
        result["font_files"] = {}
        for name, meta in payload.items():
            try:
                data = zf.read("assets/bin/Data/" + name)
                result["font_files"][name] = {
                    "bytes": len(data), "sha256": sha256_bytes(data),
                    "matches_payload": sha256_bytes(data) == meta["sha256"],
                }
            except KeyError:
                result["font_files"][name] = {"missing": True}
        try:
            so = zf.read("lib/arm64-v8a/libniermenu.so")
            result["libniermenu_so"] = {"bytes": len(so), "sha256": sha256_bytes(so)[:16]}
        except KeyError:
            result["libniermenu_so"] = {"missing": True}
        if mode == "patched":
            try:
                result["private_patch_libil2cpp_sha256"] = sha256_bytes(
                    zf.read("lib/arm64-v8a/libil2cpp.so"))
            except KeyError:
                pass
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["patched", "original"], default="patched")
    ap.add_argument("--apk", required=True, help="原版 JP APK（只读）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--font-payload", required=True)
    ap.add_argument("--grpc", default="192.168.2.6:8003")
    ap.add_argument("--http", default="192.168.2.6:8080")
    ap.add_argument("--auth", default="192.168.2.6:3000")
    ap.add_argument("--fresh", action="store_true", help="强制重新解包")
    ap.add_argument("--no-private-patch", action="store_true", help="同 --mode original")
    args = ap.parse_args()
    mode = "original" if args.no_private_patch else args.mode

    apk = Path(args.apk).resolve()
    out = Path(args.out).resolve()
    work = Path(args.work).resolve()
    payload_dir = Path(args.font_payload).resolve()
    log_dir = out.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{stamp}-build-jp-{mode}.log"

    # Windows 控制台默认 GBK：统一 UTF-8，避免中文乱码/UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    # 控制台 + 文件双写
    log_file = log_path.open("w", encoding="utf-8")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(old_stdout, log_file)
    sys.stderr = Tee(old_stderr, log_file)
    try:
        print(f"=== JP 汉化客户端构建 mode={mode} ===")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输入 APK: {apk}")
        print(f"输出 APK: {out}")
        print(f"解包目录: {work}")
        print(f"字体 payload: {payload_dir}")
        if mode == "patched":
            print(f"私服地址: gRPC={args.grpc} HTTP={args.http} auth={args.auth}")

        sys.path.insert(0, str(TOOLS))
        import _common as C  # noqa: E402
        import build_menu  # noqa: E402
        import inject_modmenu  # noqa: E402

        try:
            C.init_log(f"zh-build-jp-{mode}")
        except PermissionError:
            # 某些 Windows 环境下 jp-client/build/logs 偶发被锁；退回本任务日志目录
            C.LOG_DIR = str(log_dir)
            C.init_log(f"zh-build-jp-{mode}")

        cfg = C.load_toolpaths()
        tools = C.detect_tools(cfg)
        C.log(f"工具: apktool={C.local_path(tools['apktool_jar'])}")
        C.log(f"工具: build-tools={C.local_path(os.path.dirname(tools['zipalign']))}")
        C.log(f"工具: keystore={tools['keystore']} alias={tools['ks_alias']}")

        if not apk.is_file():
            raise SystemExit(f"输入 APK 不存在: {apk}")
        original_hashes = app_original_hashes(apk)
        payload = font_payload_meta(payload_dir)
        for name, meta in payload.items():
            print(f"  字体 payload: {name} {meta['bytes']:,}B {meta['sha256']}")

        # ---- 1) 菜单编译 + extract（复用缓存/已有 app-debug.apk）----
        C.log("=== 1/6 编译/复用菜单 APK 并 extract ===")
        menu_apk = build_menu.build_apk(cfg, tools, auto_yes=True, no_input=True)
        # Windows 上 apktool 刚退出的瞬间，build/menu_apktool 里的 so 可能被
        # Defender/句柄短暂锁住，rmtree 会 WinError 5；重试几次即可。
        for attempt in range(1, 7):
            try:
                build_menu.extract(cfg, tools, menu_apk)
                break
            except PermissionError as exc:
                C.log(f"菜单 extract 被占用（第 {attempt}/6 次），2 秒后重试: {exc}")
                time.sleep(2)
        else:
            raise SystemExit("菜单 extract 连续失败（文件被占用）")

        # ---- 2) 解包目标 APK ----
        C.log("=== 2/6 解包/复用目标 APK ===")
        inject_modmenu.ensure_work(apk, work, tools, args.fresh, True, True)

        # ---- 3) 私服补丁（可选）----
        if mode == "patched":
            C.log("=== 3/6 私服补丁（lunar-scripts-jp patch_apk_jp.py）===")
            rc, lines = run_logged([
                sys.executable, PATCH_JP, str(work),
                "--grpc-addr", args.grpc, "--http-addr", args.http, "--auth-host", args.auth,
            ], log_path, cwd=ROOT / "lunar-scripts-jp")
            if rc != 0:
                raise SystemExit(f"私服补丁失败 exit={rc}")
            patch_tail = lines[-40:]
        else:
            C.log("=== 3/6 跳过私服补丁（mode=original）===")
            patch_tail = []

        # ---- 3.5/6 fix3 内置串补丁（就地 apply，私服补丁后、字体前）----
        C.log(f"=== 3.5/6 fix3 内置串补丁（patch_fix3.py apply --tier {FIX3_TIER}）===")
        if not FIX3_PATCHER.is_file():
            raise SystemExit(f"fix3 补丁脚本不存在: {FIX3_PATCHER}")
        # TextAsset 重写需 UnityPy：用当前解释器（与构建其余步骤同权限）执行 apply；
        # 当前解释器缺 UnityPy 时，把 venv site-packages 挂进 PYTHONPATH（UnityPy 仍取自 venv）。
        venv_site = VENV_PY.parent.parent / "Lib" / "site-packages"
        fix3_env = os.environ.copy()
        try:
            import UnityPy  # noqa: F401
        except ImportError:
            if not venv_site.is_dir():
                raise SystemExit(f"UnityPy 不可用，且 venv site-packages 不存在: {venv_site}")
            fix3_env["PYTHONPATH"] = str(venv_site) + os.pathsep + fix3_env.get("PYTHONPATH", "")
        fix3_py = Path(sys.executable)
        print(f"  fix3 python: {fix3_py}")
        rc, lines = run_logged([
            fix3_py, FIX3_PATCHER, "apply", "--work", str(work), "--tier", FIX3_TIER,
        ], log_path, cwd=FIX3_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit(f"fix3 内置串补丁失败 exit={rc}")
        fix3_tail = lines[-40:]
        fix3_report_path = FIX3_DIR / "apply_report.json"
        fix3_report = (json.loads(fix3_report_path.read_text(encoding="utf-8"))
                       if fix3_report_path.is_file() else {})
        fix3_checks = verify_fix3_workdir(work)
        C.log("fix3 自检: " + json.dumps(fix3_checks, ensure_ascii=False)[:800])
        if not (fix3_checks["ok"] and fix3_report.get("ok", True)):
            raise SystemExit("fix3 自检失败，拒绝重打包")

        # ---- 4) 字体资源替换 ----
        C.log("=== 4/6 字体资源替换 ===")
        copied = inject_modmenu.inject_fonts(work, str(payload_dir))

        # ---- 5) mod 菜单注入 ----
        C.log("=== 5/6 mod 菜单注入 ===")
        inject_modmenu.inject_smali(work)
        inject_modmenu.inject_manifest(work)
        inject_modmenu.inject_start_call(work)

        work_checks = verify_workdir(work, payload, mode, args.grpc.split(":")[0])
        C.log("解包目录自检: " + json.dumps(work_checks, ensure_ascii=False)[:800])
        if not work_checks["ok"]:
            raise SystemExit("解包目录自检失败，拒绝重打包")

        # ---- 6) 重建 + zipalign + 签名 ----
        C.log("=== 6/6 重建 + 对齐 + 签名（nier-jp key）===")
        inject_modmenu.build_and_sign(tools, work, str(out))

        C.log("=== 产物验证 ===")
        verify = apksigner_verify(Path(tools["java"]), Path(C.local_path(tools["apksigner_jar"])),
                                  out, log_path)
        align = zipalign_check(Path(tools["zipalign"]), out, log_path)
        final = apk_final_check(out, payload, mode)
        print(f"签名证书 SHA-256: {verify['cert_sha256']}")
        print(f"apksigner: v2={verify['verified_v2']} v3={verify['verified_v3']} "
              f"cert_match={verify['cert_matches_expected']}")
        print(f"zipalign: {align['ok']}")
        print(f"产物: {final['bytes']:,}B sha256={final['sha256']}")

        evidence = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "mode": mode,
            "apk_input": {
                "path": str(apk), "bytes": apk.stat().st_size, "sha256": sha256_file(apk),
                "untouched_hashes": original_hashes,
            },
            "font_payload": payload,
            "server_addresses": {"grpc": args.grpc, "http": args.http, "auth": args.auth}
            if mode == "patched" else None,
            "workspace": str(work),
            "menu_apk": str(menu_apk),
            "workdir_checks": work_checks,
            "private_patch_log_tail": patch_tail,
            "fix3": {
                "tool": str(FIX3_PATCHER),
                "tier": FIX3_TIER,
                "python": str(fix3_py),
                "report_path": str(fix3_report_path),
                "apply_report": fix3_report,
                "workdir_checks": fix3_checks,
                "log_tail": fix3_tail,
            },
            "output": {
                "path": str(out),
                **final,
                "signature": verify,
                "zipalign": align,
            },
            "expected_cert_sha256": EXPECTED_CERT_SHA256,
        }
        evidence_path = log_dir / f"{stamp}-evidence-jp-{mode}.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"evidence: {evidence_path}")

        # 输入 APK 未被修改
        after = sha256_file(apk)
        print(f"输入 APK 未修改: {after == evidence['apk_input']['sha256']}")
        if after != evidence["apk_input"]["sha256"]:
            raise SystemExit("输入 APK 被修改！")
        if not (verify["verified_v2"] and verify["cert_matches_expected"] and align["ok"]
                and final["zip_ok"] and all(v.get("matches_payload") for v in final["font_files"].values())):
            raise SystemExit("产物验证未全部通过")
        print("=== BUILD OK ===")
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        log_file.close()


if __name__ == "__main__":
    main()
