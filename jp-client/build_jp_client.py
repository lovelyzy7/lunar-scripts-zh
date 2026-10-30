#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_jp_client.py — JP 客户端一条流水线：原版 APK → 私服补丁 → fix3 内置串 →
字体 payload → mod 菜单注入 → apktool 重建 → zipalign → nier-jp 签名 → 验证门
→ **bin.e 成对构建**（汉化 masterdata + 可选编辑项，见 build_bin_e.py）。

与历史流水线（zh-l10n\\work\\apk\\build_jp_zh.py）产物等价（= 现网 fix3c），
但自包含于 lunar-scripts-zh/jp-client/：
  * fix3 表/补丁器         jp-client/fix3/（builtin_strings.json/tsv + patch_fix3.py）
  * 字体 payload（四条目）  jp-client/fonts/payload/assets/bin/Data/
  * 私服补丁               jp-client/patches/patch_apk_jp.py（lunar-scripts-jp 副本）
  * mod 菜单注入件         jp-client/modmenu-payload/（smali + libniermenu.so，免 Gradle/NDK）
  * keystore               jp-client/keys/nier-jp.keystore（alias nier / pass lunar-jp）
  * 验证门                 jp-client/verify_jp_client.py（①-⑥ + fix3c 等价性对照）
  * bin.e 成对构建         jp-client/build_bin_e.py + bin-edit.default.json（可选编辑面
                           逐项对应原版 lunar-scripts patch_masterdata.py；文本格=汉化基
                           逐字节、结构 AES/TOC/5 表/LZ4、diff 只在预期表三重断言）

一条命令（干净机器；只给原版 APK 路径即可）：
  python build_jp_client.py --apk "resources\\NieR Re[in]carnation_3.7.1_JP.apk"

成对交付（目标 APK + 配套汉化 bin.e 一次产出）：
  python build_jp_client.py --apk <原版.apk> --out <目标.apk> \\
      --bin-e <原版或汉化bin.e> [--out-bin-e <同名.bin.e>] \\
      [--bin-edit jp-client/bin-edit.default.json] \\
      [--text-from <bin_zh_fix6.bin.e>] [--orig-bin-e <20240404193219.bin.e>]

入参=原版 JP APK（只读，sha256 25b6326c…653609）；
出参=签好的汉化客户端 APK + verify 报告 + 构建日志/evidence（--out 所在目录）；
给了 --bin-e 时追加产出配套 bin.e + build_bin_e 报告（三重断言全过才落盘）。
每步失败即停（SystemExit），全程日志落盘。

L3a 客户端化契约（BUNKER-ADAPT-PLAN §8/§9）：
  * 客户端自动识别：shared/detect_client.py 按 region 三元组（axml 包名+size+sha256）
    硬断言输入必须是 JP 客户端（未知/篡改/误喂 EN 包 → fail-fast，不产出任何文件）；
  * 产物命名契约：缺省产物名 **nier-jp.apk**（--out 语义保留，显式指定时以 --out 为准）；
  * manifest sidecar：每产物附 `<产物名>.manifest.json`（region 三元组/sha256/size/
    签名证书指纹/补丁计数/验证门结果/构建时间/RVA 表版本占位/输入 APK sha）；
  * 签名 key 自动选：region=jp → jp-client/keys/nier-jp.keystore（证书 EE:C2:3B…98A2FE，
    验证门证书指纹比对）；bin.e 仍「文件名前后不变」。

依赖：Python 3.11+（本机用 C:\\Python314\\python.exe）、UnityPy（可经
toolpaths.json 的 unitypy_site_packages 挂 zh-l10n\\.venv）、JDK 21、Android SDK
build-tools（zipalign/apksigner）、apktool.jar。**不需要** Gradle/NDK。
bin.e 侧另需 pycryptodome/msgpack/lz4（可经 toolpaths.json 的 bin_e_site_packages
挂 lunar-base\\.venv，或 pip install pycryptodome msgpack lz4）。
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

JP = Path(__file__).resolve().parent
SHARED = JP.parent / "shared"
sys.path.insert(0, str(SHARED))
import detect_client  # noqa: E402
import manifest_sidecar  # noqa: E402

FIX3_DIR = JP / "fix3"
PATCHES_DIR = JP / "patches"
FONTS_PAYLOAD = JP / "fonts" / "payload" / "assets" / "bin" / "Data"
MENU_PAYLOAD = JP / "modmenu-payload"
KEYSTORE = JP / "keys" / "nier-jp.keystore"
MANIFEST = JP / "MANIFEST.json"
TOOLPATHS = JP / "toolpaths.json"
VERIFY_SCRIPT = JP / "verify_jp_client.py"
BUILD_BIN_E = JP / "build_bin_e.py"
BIN_EDIT_DEFAULT = JP / "bin-edit.default.json"

EXPECTED_ORIG_SHA256 = "25b6326c610290dd1f581fc3b41e60efb1126172aae45804d5345caa0b653609"
EXPECTED_CERT_SHA256 = "eec23be0cb205c401791be3d4b82e8851560f5c2aed3ec644166093d3d98a2fe"
KS_ALIAS = "nier"
KS_PASS = "lunar-jp"
META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"

FONT_ENTRIES = {
    "6f937efa0660c47f59d5215d276b1cbb": "UI RodinPro→Medium+ExtA 子集",
    "7089ac60979c94824ac549baab08cfa7": "STORY TalkingStd→Regular 子集",
    "ad1489eb70ff840d19d7d0841bcdd3a9": "FOTK-YDHopeL→Regular 子集",
    "550e0743a6b6344cfa3380b9a07f58b6": "FOTK-YDWingsM→Medium 子集",
}

# fix3 就地补丁自检抽查（口径同 build_jp_zh.py）
FIX3_SPOT_CHECKS = {
    "assets/bin/Data/35005335013ad4314b0ac8afbfe27b9c": [
        "公告", "联系我们", "数据继承", "数据修复", "其他信息", "删除数据",
        "关闭", "取消", "下载确认",
        "将进行数据修复。确定吗？", "数据修复已完成", "菜单", "删除", "同意",
        "结束游戏", "要结束游戏吗？", "返回标题", "错误", "维护中",
    ],
    "assets/bin/Data/5296ae89c03c14825a9f664b0c355ccc": [
        "下载确认", "注册玩家名", "请输入玩家名",
        "将开始约{0}MB的数据下载", "下载设置",
        "网络错误", "重试", "序列号", "继续", "放弃",
    ],
}
FIX3_META_SPOT = ["公告", "关闭", "取消",
                  "播放影片", "播放影片中", "打开公告", "打开推特"]

# mod 菜单注入（口径同 NieR-Re-In-Carnation-Mod_Menu/jp-client/tools/inject_modmenu.py）
PERMISSION_LINE = '    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>\n'
SERVICE_LINE = ('    <service android:name="com.android.support.Launcher" android:enabled="true" '
                'android:exported="false" android:stopWithTask="true" />\n')
START_CALL = "    invoke-static {p0}, Lcom/android/support/Main;->Start(Landroid/content/Context;)V\n"
START_MARK = "Lcom/android/support/Main;->Start(Landroid/content/Context;)V"


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
    """外部命令：stdout/stderr 同时进日志与控制台，返回 (rc, 行)。"""
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


# ---------------------------------------------------------------- tools
def load_toolpaths() -> dict:
    if TOOLPATHS.is_file():
        return json.loads(TOOLPATHS.read_text(encoding="utf-8-sig"))
    return {}


def latest_build_tools(android_home: str) -> str | None:
    base = Path(android_home) / "build-tools"
    if not base.is_dir():
        return None

    def key(name: str):
        m = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", name)
        return tuple(int(x) for x in m.groups() if x) if m else ()

    dirs = sorted([d for d in base.iterdir() if d.is_dir()], key=lambda d: key(d.name))
    for d in reversed(dirs):
        if (d / "zipalign.exe").is_file() or (d / "zipalign").is_file():
            return str(d)
    return None


def detect_tools(cfg: dict, client: dict | None = None) -> dict:
    tools: dict = {}
    java = cfg.get("java") or ""
    jh = cfg.get("java_home") or os.environ.get("JAVA_HOME") or ""
    if not java and jh:
        for name in ("java.exe", "java"):
            p = Path(jh) / "bin" / name
            if p.is_file():
                java = str(p)
                break
    tools["java"] = java or "java"

    apktool = cfg.get("apktool_jar") or os.environ.get("APKTOOL_JAR") or ""
    if not apktool or not Path(apktool).is_file():
        raise SystemExit(f"未找到 apktool.jar：请在 toolpaths.json 配置 apktool_jar（当前={apktool!r}）")
    tools["apktool_jar"] = str(Path(apktool).resolve())

    android_home = cfg.get("android_home") or os.environ.get("ANDROID_HOME") \
        or os.environ.get("ANDROID_SDK_ROOT") or ""
    bt = latest_build_tools(android_home) if android_home else None
    if not bt:
        raise SystemExit(f"未找到 Android build-tools（android_home={android_home!r}）")
    tools["build_tools"] = bt

    zipalign = cfg.get("zipalign") or ""
    if not zipalign or not Path(zipalign).is_file():
        for name in ("zipalign.exe", "zipalign"):
            p = Path(bt) / name
            if p.is_file():
                zipalign = str(p)
                break
    if not zipalign or not Path(zipalign).is_file():
        raise SystemExit(f"未找到 zipalign（build-tools={bt}）")
    tools["zipalign"] = zipalign

    apksigner = cfg.get("apksigner_jar") or ""
    if not apksigner or not Path(apksigner).is_file():
        for p in (Path(bt) / "lib" / "apksigner.jar", Path(bt) / "apksigner.jar"):
            if p.is_file():
                apksigner = str(p)
                break
    if not apksigner or not Path(apksigner).is_file():
        raise SystemExit(f"未找到 apksigner.jar（build-tools={bt}）")
    tools["apksigner_jar"] = apksigner

    if not KEYSTORE.is_file():
        raise SystemExit(f"未找到 keystore: {KEYSTORE}")
    # 签名 key 按客户端自动选（L3a：jp→nier-jp；cfg 的 ks_alias/ks_pass 仅覆盖口令位）
    tools["keystore"] = (client or {}).get("keystore_path") or str(KEYSTORE)
    tools["ks_alias"] = cfg.get("ks_alias") or (client or {}).get("ks_alias") or KS_ALIAS
    tools["ks_pass"] = cfg.get("ks_pass") or (client or {}).get("ks_pass") or KS_PASS
    tools["expect_cert_sha256"] = (client or {}).get("cert_sha256") or EXPECTED_CERT_SHA256
    return tools


def ensure_unitypy(venv_site: str | None) -> dict:
    """UnityPy 可用化（进程内 + 子进程 PYTHONPATH），返回补丁后的 env 基底。"""
    env = os.environ.copy()
    try:
        import UnityPy  # noqa: F401
        return env
    except ImportError:
        pass
    cands = [Path(venv_site)] if venv_site else []
    cands.append(Path(r"E:\NieRReincarnation\zh-l10n\.venv\Lib\site-packages"))
    for c in cands:
        if c and c.is_dir() and (c / "UnityPy").is_dir():
            env["PYTHONPATH"] = str(c) + os.pathsep + env.get("PYTHONPATH", "")
            sys.path.insert(0, str(c))
            import UnityPy  # noqa: F401
            return env
    raise SystemExit("UnityPy 不可用：pip install UnityPy，或在 toolpaths.json 配置 unitypy_site_packages")


def ensure_bin_deps(env: dict, bin_e_site: str | None) -> dict:
    """bin.e 依赖（pycryptodome/msgpack/lz4）可用化：本进程 import + 子进程 PYTHONPATH。

    干净机器：pip install pycryptodome msgpack lz4；
    本机缺包时按 toolpaths.json 的 bin_e_site_packages → lunar-base\\.venv 兜底。
    """
    def _try_import() -> bool:
        try:
            import lz4.block  # noqa: F401
            import msgpack  # noqa: F401
            from Crypto.Cipher import AES  # noqa: F401
            return True
        except ImportError:
            return False

    if _try_import():
        return env
    cands = [Path(bin_e_site)] if bin_e_site else []
    cands.append(Path(r"E:\NieRReincarnation\lunar-base\.venv\Lib\site-packages"))
    for c in cands:
        if c and c.is_dir() and (c / "Crypto").is_dir() and (c / "msgpack").is_dir():
            env["PYTHONPATH"] = str(c) + os.pathsep + env.get("PYTHONPATH", "")
            sys.path.insert(0, str(c))
            if _try_import():
                return env
    raise SystemExit("bin.e 依赖不可用：pip install pycryptodome msgpack lz4，"
                     "或在 toolpaths.json 配置 bin_e_site_packages")


# ---------------------------------------------------------------- checks
def check_manifest() -> dict:
    if not MANIFEST.is_file():
        raise SystemExit(f"缺少 MANIFEST.json: {MANIFEST}")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = []
    for item in man["items"]:
        p = JP / item["path"]
        if not p.is_file():
            bad.append({"path": item["path"], "reason": "missing"})
            continue
        got = sha256_file(p)
        if got != item["sha256"]:
            bad.append({"path": item["path"], "reason": "sha256 mismatch",
                        "expected": item["sha256"], "actual": got})
    if bad:
        raise SystemExit("MANIFEST 校验失败（权威副本被改动）: " + json.dumps(bad[:5], ensure_ascii=False))
    return {"files": len(man["items"]), "ok": True}


def font_payload_meta(payload_dir: Path) -> dict:
    files = {}
    for p in sorted(payload_dir.iterdir()):
        if p.is_file():
            files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    if not files:
        raise SystemExit(f"字体 payload 为空: {payload_dir}")
    missing = [name for name in FONT_ENTRIES if name not in files]
    if missing:
        raise SystemExit(f"字体 payload 缺少必需文件: {missing}")
    return files


def app_original_hashes(apk: Path) -> dict:
    with zipfile.ZipFile(apk) as zf:
        return {name: sha256_bytes(zf.read(name))
                for name in ("lib/arm64-v8a/libil2cpp.so",
                             "assets/bin/Data/Managed/Metadata/global-metadata.dat",
                             "AndroidManifest.xml")}


def verify_fix3_workdir(work: Path) -> dict:
    checks: dict = {"textassets": {}, "metadata": {}}
    for rel, needles in FIX3_SPOT_CHECKS.items():
        p = work / rel
        blob = p.read_bytes() if p.is_file() else b""
        checks["textassets"][rel] = {
            "exists": p.is_file(),
            "hits": {n: (n.encode("utf-8") in blob) for n in needles},
        }
    meta = work / META_ENTRY
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
    support_smali = []
    for entry in work.iterdir():
        if re.fullmatch(r"smali(?:_classes\d+)?", entry.name) and entry.is_dir():
            p = entry / "com" / "android" / "support" / "Main.smali"
            if p.is_file():
                support_smali.append(str(p.relative_to(work)))
    checks["menu"] = {
        "main_smali": support_smali,
        "libniermenu_so": (work / "lib" / "arm64-v8a" / "libniermenu.so").is_file(),
    }
    manifest = (work / "AndroidManifest.xml").read_text(encoding="utf-8", errors="replace")
    checks["manifest"] = {
        "has_system_alert_window": "SYSTEM_ALERT_WINDOW" in manifest,
        "has_menu_service": "com.android.support.Launcher" in manifest,
    }
    start_hits = []
    for entry in work.iterdir():
        if re.fullmatch(r"smali(?:_classes\d+)?", entry.name) and entry.is_dir():
            for smali in entry.rglob("*.smali"):
                try:
                    if START_MARK in smali.read_text(encoding="utf-8", errors="ignore"):
                        start_hits.append(str(smali.relative_to(work)))
                except OSError:
                    continue
    checks["start_call"] = start_hits
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


# ---------------------------------------------------------------- injection
def inject_fonts(work: Path, payload_dir: Path) -> list[str]:
    dst_dir = work / "assets" / "bin" / "Data"
    if not dst_dir.is_dir():
        raise SystemExit(f"解包目录缺少 assets/bin/Data: {work}")
    copied = []
    for fn in sorted(os.listdir(payload_dir)):
        src = payload_dir / fn
        if not src.is_file():
            continue
        dst = dst_dir / fn
        if not dst.is_file():
            raise SystemExit(f"字体 payload 文件在目标 APK 中不存在（只能替换不能新增）: {fn}")
        before = dst.stat().st_size
        shutil.copy2(src, dst)
        print(f"  字体资源已替换 assets/bin/Data/{fn} ({before/1048576:.2f}MB -> {dst.stat().st_size/1048576:.2f}MB)")
        copied.append(fn)
    if not copied:
        raise SystemExit("字体 payload 目录为空")
    return copied


def pick_smali_dir(work: Path) -> Path:
    best, best_idx = None, -1
    for name in os.listdir(work):
        m = re.fullmatch(r"smali(?:_classes(\d+))?", name)
        if m and (work / name).is_dir():
            idx = int(m.group(1)) if m.group(1) else 1
            if idx > best_idx:
                best, best_idx = work / name, idx
    if not best:
        raise SystemExit("目标 APK 未找到 smali 目录")
    return best


def inject_menu(work: Path) -> None:
    target_root = pick_smali_dir(work)
    dst = target_root / "com" / "android" / "support"
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for sub in ("smali_classes2", "smali"):
        src = MENU_PAYLOAD / sub / "com" / "android" / "support"
        if src.is_dir():
            for fn in sorted(os.listdir(src)):
                if fn.endswith(".smali"):
                    shutil.copy2(src / fn, dst / fn)
                    n += 1
    if n == 0:
        raise SystemExit(f"菜单注入件中未找到 smali: {MENU_PAYLOAD}")
    print(f"  菜单 smali 已注入 {target_root.name}/com/android/support（{n} 个文件）")

    so_src = MENU_PAYLOAD / "lib" / "arm64-v8a" / "libniermenu.so"
    if not so_src.is_file():
        raise SystemExit(f"缺少 libniermenu.so: {so_src}")
    lib_dst = work / "lib" / "arm64-v8a"
    lib_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(so_src, lib_dst / "libniermenu.so")
    print("  libniermenu.so 已注入 lib/arm64-v8a/")


def inject_manifest(work: Path) -> None:
    path = work / "AndroidManifest.xml"
    text = path.read_text(encoding="utf-8", errors="ignore")
    changed = False
    if "SYSTEM_ALERT_WINDOW" not in text:
        i = text.find("<application")
        if i < 0:
            raise SystemExit("清单中未找到 <application>")
        ls = text.rfind("\n", 0, i) + 1
        text = text[:ls] + PERMISSION_LINE + text[ls:]
        changed = True
        print("  已加入悬浮窗权限")
    if "com.android.support.Launcher" not in text:
        i = text.rfind("</application>")
        if i < 0:
            raise SystemExit("清单中未找到 </application>")
        ls = text.rfind("\n", 0, i) + 1
        text = text[:ls] + SERVICE_LINE + text[ls:]
        changed = True
        print("  已加入 Launcher service")
    if changed:
        path.write_text(text, encoding="utf-8")


def find_launcher_activity(work: Path) -> str:
    xml = (work / "AndroidManifest.xml").read_text(encoding="utf-8", errors="ignore")
    pkg = re.search(r'package="([^"]+)"', xml)
    pkg = pkg.group(1) if pkg else ""
    for m in re.finditer(r'<activity\b[^>]*?android:name="([^"]+)"[^>]*>(.*?)</activity>', xml, re.S):
        name, body = m.group(1), m.group(2)
        if "android.intent.action.MAIN" in body and "LAUNCHER" in body:
            return pkg + name if name.startswith(".") else name
    for m in re.finditer(r'<activity\b[^>]*?android:name="([^"]+)"[^>]*>(.*?)</activity>', xml, re.S):
        if "android.intent.action.MAIN" in m.group(2):
            name = m.group(1)
            return pkg + name if name.startswith(".") else name
    raise SystemExit("未找到 Launcher Activity")


def inject_start_call(work: Path) -> None:
    activity = find_launcher_activity(work)
    rel = activity.replace(".", "/") + ".smali"
    target = None
    for d in os.listdir(work):
        if re.fullmatch(r"smali(?:_classes\d+)?", d):
            p = work / d / rel
            if p.is_file():
                target = p
                break
    if not target:
        raise SystemExit("未找到启动 Activity 的 smali: " + rel)
    text = target.read_text(encoding="utf-8", errors="ignore")
    if START_MARK in text:
        print(f"  启动注入已存在，跳过（{activity}）")
        return
    m = re.search(r"(\.method\s+[^\n]*?\bonCreate\(Landroid/os/Bundle;\)V\n)", text)
    if not m:
        raise SystemExit("该 Activity 没有 onCreate(Bundle)，需要手动注入")
    body_start = m.end()
    sup = re.search(r"[ \t]*invoke-super\s+\{p0, p1\},\s+[^\n]*->onCreate\(Landroid/os/Bundle;\)V\n",
                    text[body_start:])
    if not sup:
        raise SystemExit("onCreate 内未找到 invoke-super ...->onCreate，需要手动注入")
    pos = body_start + sup.end()
    text = text[:pos] + "\n" + START_CALL + text[pos:]
    target.write_text(text, encoding="utf-8")
    print(f"  已注入 Main->Start 到 {activity}")


# ---------------------------------------------------------------- pipeline
def main() -> None:
    ap = argparse.ArgumentParser(description="JP 客户端一条流水线（私服补丁+汉化+mod 菜单+签名）")
    ap.add_argument("--apk", required=True, help="原版 JP APK（只读；sha256 25b6326c…653609）")
    ap.add_argument("--out", default=str(JP / "out" / "nier-jp.apk"),
                    help="输出 APK 路径（缺省按命名契约 nier-jp.apk；--out 语义保留，"
                         "显式指定时以 --out 为准）")
    ap.add_argument("--work", default=str(JP / "build" / "work"), help="apktool 解包目录")
    ap.add_argument("--logs", default=None, help="日志目录（默认 --out 同级 logs/）")
    ap.add_argument("--mode", choices=["patched", "original"], default="patched")
    ap.add_argument("--grpc", default="192.168.2.6:8003")
    ap.add_argument("--http", default="192.168.2.6:8080")
    ap.add_argument("--auth", default="192.168.2.6:3000")
    ap.add_argument("--fresh", action="store_true", help="强制重新解包（默认同）")
    ap.add_argument("--reuse-work", action="store_true", help="解包目录未变时复用缓存")
    ap.add_argument("--baseline", default=r"E:\NieRReincarnation\zh-l10n\work\apk\nier-mod-menu-jp-font-fix3c.apk",
                    help="等价性对照基准 APK（fix3c）；传空字符串跳过")
    ap.add_argument("--no-verify", action="store_true", help="跳过验证门（不推荐）")
    ap.add_argument("--bin-e", default=None,
                    help="成对交付：输入 bin.e（原版或汉化；给定则追加构建配套汉化 bin.e）")
    ap.add_argument("--out-bin-e", default=None,
                    help="输出目标 bin.e（缺省 = --out 同级 + 与 --bin-e 同名；"
                         "硬性要求：文件名前后不变，显式指定时文件名也必须与输入一致）")
    ap.add_argument("--bin-edit", default=str(BIN_EDIT_DEFAULT),
                    help="bin.e 可选编辑项配置 JSON（缺省 bin-edit.default.json = 原版编辑面）")
    ap.add_argument("--text-from", default=None,
                    help="从该 bin.e 逐字节移植 5 张文本表（权威汉化基 bin_zh_fix6.bin.e）")
    ap.add_argument("--orig-bin-e", default=None,
                    help="bin.e 断言 C 参照的原版 bin.e（20240404193219.bin.e）")
    args = ap.parse_args()

    apk = Path(args.apk).resolve()
    out = Path(args.out).resolve()
    work = Path(args.work).resolve()
    log_dir = Path(args.logs).resolve() if args.logs else out.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{stamp}-build-jpclient.log"

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    log_file = log_path.open("w", encoding="utf-8")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(old_stdout, log_file)
    sys.stderr = Tee(old_stderr, log_file)
    try:
        t0 = time.time()
        build_started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        print(f"=== JP 客户端构建（jp-client 一条流水线）mode={args.mode} ===")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"python: {sys.executable}")
        print(f"输入 APK: {apk}")
        print(f"输出 APK: {out}")
        print(f"解包目录: {work}")
        print(f"日志目录: {log_dir}")

        # ---- 0) 预检 ----
        print("=== 0/8 预检（MANIFEST / 客户端识别 / 工具 / UnityPy / 输入）===")
        man = check_manifest()
        print(f"  MANIFEST 校验 ok（{man['files']} 个权威副本 sha256 一致）")
        if not apk.is_file():
            raise SystemExit(f"输入 APK 不存在: {apk}")

        # 客户端自动识别（L3a：region 三元组硬断言；未知/篡改/误喂 EN 包 → fail-fast）
        client = detect_client.detect_client(apk, expect="jp")
        print(f"  客户端识别 ok: region={client['region']} package={client['package']}")
        print(f"  region 三元组硬断言 ok: {client['bytes']:,}B sha256={client['sha256'][:16]}…")
        print(f"  产物命名契约: {client['product_name']}（--out 显式指定时以 --out 为准）")
        if out.name != client["product_name"]:
            print(f"  [!] --out 名 {out.name!r} 与契约名 {client['product_name']!r} 不同"
                  f"（--out 语义保留；sidecar 仍按契约登记）")
        cfg = load_toolpaths()
        tools = detect_tools(cfg, client)
        print(f"  java={tools['java']}")
        print(f"  apktool={tools['apktool_jar']}")
        print(f"  build-tools={tools['build_tools']}")
        print(f"  keystore={tools['keystore']} alias={tools['ks_alias']}（按 region 自动选）")
        print(f"  期望证书 SHA-256={tools['expect_cert_sha256']}")
        env = ensure_unitypy(cfg.get("unitypy_site_packages"))
        print(f"  UnityPy ok（PYTHONPATH={env.get('PYTHONPATH', '')!s}"[:120] + "）")
        if args.bin_e:
            env = ensure_bin_deps(env, cfg.get("bin_e_site_packages"))
            print("  bin.e 依赖（pycryptodome/msgpack/lz4）ok")

        input_sha = client["detected"]["sha256"]
        print(f"  输入 APK sha256={input_sha}")
        original_hashes = app_original_hashes(apk)
        payload = font_payload_meta(FONTS_PAYLOAD)
        for name, meta in payload.items():
            print(f"  字体 payload: {name} {meta['bytes']:,}B {meta['sha256'][:16]}…")

        # ---- 1) 解包 ----
        print("=== 1/8 解包目标 APK（apktool d）===")
        stamp_txt = f"{os.path.abspath(apk)}|{apk.stat().st_size}|{int(apk.stat().st_mtime)}"
        stamp_file = work / ".source_stamp"
        reusable = (args.reuse_work and work.is_dir() and (work / "apktool.yml").is_file()
                    and stamp_file.is_file() and stamp_file.read_text().strip() == stamp_txt)
        if reusable:
            print("  复用解包缓存")
        else:
            if work.is_dir():
                shutil.rmtree(work)
            work.parent.mkdir(parents=True, exist_ok=True)
            rc, _ = run_logged([tools["java"], "-jar", tools["apktool_jar"], "d", str(apk),
                                "-o", str(work), "-f"], log_path)
            if rc != 0 or not (work / "apktool.yml").is_file():
                raise SystemExit(f"apktool 解包失败 exit={rc}")
            stamp_file.write_text(stamp_txt)

        # ---- 2) 私服补丁 ----
        if args.mode == "patched":
            print("=== 2/8 私服补丁（patches/patch_apk_jp.py）===")
            rc, lines = run_logged([
                sys.executable, PATCHES_DIR / "patch_apk_jp.py", str(work),
                "--grpc-addr", args.grpc, "--http-addr", args.http, "--auth-host", args.auth,
            ], log_path, env=env)
            if rc != 0:
                raise SystemExit(f"私服补丁失败 exit={rc}")
            patch_tail = lines[-40:]
        else:
            print("=== 2/8 跳过私服补丁（mode=original）===")
            patch_tail = []

        # ---- 3) fix3 内置串补丁 ----
        print("=== 3/8 fix3 内置串补丁（patch_fix3.py apply --tier all）===")
        fix3_run = log_dir / "fix3-run"
        fix3_run.mkdir(parents=True, exist_ok=True)
        for fn in ("patch_fix3.py", "builtin_strings.json", "builtin_strings.tsv"):
            shutil.copy2(FIX3_DIR / fn, fix3_run / fn)
        rc, lines = run_logged([
            sys.executable, fix3_run / "patch_fix3.py", "apply",
            "--work", str(work), "--tier", "all",
        ], log_path, cwd=fix3_run, env=env)
        if rc != 0:
            raise SystemExit(f"fix3 内置串补丁失败 exit={rc}")
        fix3_tail = lines[-40:]
        fix3_report_path = fix3_run / "apply_report.json"
        fix3_report = (json.loads(fix3_report_path.read_text(encoding="utf-8"))
                       if fix3_report_path.is_file() else {})
        fix3_checks = verify_fix3_workdir(work)
        print("  fix3 自检: " + json.dumps(fix3_checks, ensure_ascii=False)[:600])
        if not (fix3_checks["ok"] and fix3_report.get("ok", True)):
            raise SystemExit("fix3 自检失败，拒绝重打包")

        # ---- 4) 字体 payload ----
        print("=== 4/8 字体 payload 注入 ===")
        inject_fonts(work, FONTS_PAYLOAD)

        # ---- 5) mod 菜单注入 ----
        print("=== 5/8 mod 菜单注入（modmenu-payload）===")
        inject_menu(work)
        inject_manifest(work)
        inject_start_call(work)

        work_checks = verify_workdir(work, payload, args.mode, args.grpc.split(":")[0])
        print("  解包目录自检: " + json.dumps(work_checks, ensure_ascii=False)[:600])
        if not work_checks["ok"]:
            raise SystemExit("解包目录自检失败，拒绝重打包")

        # ---- 6) 重建 + 对齐 + 签名 ----
        print("=== 6/8 重建 + zipalign + 签名（nier-jp key）===")
        tmp_dir = log_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        unsigned = tmp_dir / "_unsigned.apk"
        aligned = tmp_dir / "_aligned.apk"
        for p in (unsigned, aligned):
            if p.is_file():
                p.unlink()
        rc, _ = run_logged([tools["java"], "-jar", tools["apktool_jar"], "b", str(work),
                            "-o", str(unsigned)], log_path)
        if rc != 0 or not unsigned.is_file():
            raise SystemExit(f"apktool 重建失败 exit={rc}")
        rc, _ = run_logged([tools["zipalign"], "-p", "-f", "4", str(unsigned), str(aligned)], log_path)
        if rc != 0 or not aligned.is_file():
            raise SystemExit(f"zipalign 失败 exit={rc}")
        rc, _ = run_logged([tools["java"], "-jar", tools["apksigner_jar"], "sign",
                            "--ks", tools["keystore"], "--ks-key-alias", tools["ks_alias"],
                            "--ks-pass", "pass:" + tools["ks_pass"],
                            "--out", str(out), str(aligned)], log_path)
        if rc != 0 or not out.is_file():
            raise SystemExit(f"签名失败 exit={rc}")
        for p in (unsigned, aligned):
            try:
                p.unlink()
            except OSError:
                pass

        # ---- 7) 验证门 ----
        verify_json = out.parent / (out.stem + "-verify.json")
        evidence_path = log_dir / f"{stamp}-evidence-jpclient.json"
        if not args.no_verify:
            print("=== 7/8 验证门（①-⑦ + ⑧ fix3c 等价性对照）===")
            cmd = [sys.executable, VERIFY_SCRIPT,
                   "--apk", str(out),
                   "--orig-apk", str(apk),
                   "--payload", str(FONTS_PAYLOAD),
                   "--fix3-dir", str(FIX3_DIR),
                   "--expect-input-sha", input_sha,
                   "--out-json", str(verify_json)]
            if (args.baseline or "").strip():
                cmd += ["--baseline", args.baseline]
            else:
                cmd += ["--baseline", ""]
            rc, _ = run_logged(cmd, log_path, env=env)
            if rc != 0:
                raise SystemExit(f"验证门未通过 exit={rc}（报告: {verify_json}）")
        else:
            print("=== 7/8 跳过验证门（--no-verify）===")

        # ---- 8) bin.e 成对构建（可选）----
        bin_e_report = None
        bin_e_out = None
        bin_e_in = None
        if args.bin_e:
            print("=== 8/8 bin.e 成对构建（build_bin_e.py：汉化 masterdata + 编辑项）===")
            env = ensure_bin_deps(env, cfg.get("bin_e_site_packages"))
            bin_e_in = Path(args.bin_e).resolve()
            if not bin_e_in.is_file():
                raise SystemExit(f"--bin-e 不存在: {bin_e_in}")
            bin_e_out = (Path(args.out_bin_e).resolve() if args.out_bin_e
                         else out.parent / bin_e_in.name)
            # 硬性要求：bin.e 文件名前后不变（输出文件名 == 输入文件名）
            if bin_e_out.name != bin_e_in.name:
                raise SystemExit(
                    f"bin.e 文件名前后不变：输出名 {bin_e_out.name!r} != 输入名 {bin_e_in.name!r}"
                    f"（可改目录，不可改文件名）")
            bin_e_report_path = log_dir / f"{stamp}-bin-e-report.json"
            cmd = [sys.executable, BUILD_BIN_E,
                   "--bin-e", str(bin_e_in),
                   "--out-bin-e", str(bin_e_out),
                   "--report", str(bin_e_report_path)]
            if args.bin_edit:
                cmd += ["--bin-edit", str(Path(args.bin_edit).resolve())]
            if args.text_from:
                cmd += ["--text-from", str(Path(args.text_from).resolve())]
            if args.orig_bin_e:
                cmd += ["--orig-bin-e", str(Path(args.orig_bin_e).resolve())]
            rc, _ = run_logged(cmd, log_path, env=env)
            if rc != 0:
                raise SystemExit(f"bin.e 构建失败 exit={rc}（报告: {bin_e_report_path}）")
            bin_e_report = (json.loads(bin_e_report_path.read_text(encoding="utf-8"))
                            if bin_e_report_path.is_file() else {})
            if not bin_e_report.get("ok"):
                raise SystemExit("bin.e 报告 ok=false（三重断言未全过）")
            print(f"  配套 bin.e: {bin_e_out} {bin_e_out.stat().st_size:,}B "
                  f"sha256={sha256_file(bin_e_out)}")
        else:
            print("=== 8/8 跳过 bin.e 成对构建（未给 --bin-e）===")

        # ---- 产物事实 + evidence ----
        after = sha256_file(apk)
        if after != input_sha:
            raise SystemExit("输入 APK 在构建期间被修改！")
        final = {"path": str(out), "bytes": out.stat().st_size, "sha256": sha256_file(out)}
        with zipfile.ZipFile(out) as zf:
            final["zip_ok"] = zf.testzip() is None
            final["entries"] = len(zf.namelist())
            final["font_files"] = {name: sha256_bytes(zf.read("assets/bin/Data/" + name))
                                   for name in FONT_ENTRIES}

        # ---- 证书指纹断言 + manifest sidecar（L3a 契约）----
        print("=== 证书指纹比对（验证门：JP=EE:C2:3B…98A2FE）===")
        verify_res = (json.loads(verify_json.read_text(encoding="utf-8"))
                      if verify_json.is_file() else {})
        cert_now = (verify_res.get("apksigner") or {}).get("cert_sha256")
        if not cert_now:
            rc, lines = run_logged([tools["java"], "-jar", tools["apksigner_jar"],
                                    "verify", "-v", "--print-certs", str(out)], log_path)
            m = re.search(r"SHA-256 digest:\s*([0-9a-fA-F:]+)", "\n".join(lines))
            cert_now = m.group(1).replace(":", "").lower() if m else None
        cert_ok = cert_now == tools["expect_cert_sha256"]
        print(f"  实测证书={cert_now}")
        print(f"  期望证书={tools['expect_cert_sha256']}")
        print(f"  证书比对: {'PASS' if cert_ok else 'FAIL'}")
        if not cert_ok:
            raise SystemExit(f"验证门证书指纹比对失败: {cert_now} != {tools['expect_cert_sha256']}")

        fhs = verify_res.get("fix3_hit_summary") or {}
        verify_gates = {
            "ok": verify_res.get("ok") if verify_res else None,
            "gates": verify_res.get("gates", {}),
            "cert_assertion": {"expected": tools["expect_cert_sha256"],
                               "actual": cert_now, "ok": cert_ok},
            "fix3c_baseline_equivalence": (verify_res.get("baseline") or {}).get("equivalent"),
            "report": str(verify_json) if verify_json.is_file() else None,
        }
        patch_counts = {
            "mode": args.mode,
            "fix3_entries_checked": fhs.get("entries_checked"),
            "fix3_entries_ok": fhs.get("entries_ok"),
            "fix3_textasset_hits": fhs.get("total_textasset_hits"),
            "fix3_metadata_hits": fhs.get("total_metadata_hits"),
            "private_ip_total_hits": (verify_res.get("private_server") or {}).get("total_hits"),
            "fonts_payload_files": len(payload),
            "menu_smali_files": len(work_checks.get("menu", {}).get("main_smali", [])),
            "menu_start_call_sites": len(work_checks.get("start_call", [])),
            "fix3_workdir_ok": fix3_checks.get("ok"),
            "workdir_ok": work_checks.get("ok"),
        }
        bin_e_info = None
        if bin_e_out is not None and bin_e_in is not None:
            bin_e_info = {"name": bin_e_in.name, "path": str(bin_e_out),
                          "bytes": bin_e_out.stat().st_size,
                          "sha256": sha256_file(bin_e_out),
                          "filename_unchanged": bin_e_out.name == bin_e_in.name}
        sidecar = manifest_sidecar.build_sidecar(
            out, region_info=client, input_apk=apk, cert_sha256=cert_now,
            patch_counts=patch_counts, verify_gates=verify_gates,
            verify_report=verify_json if verify_json.is_file() else None,
            build_started_at=build_started_at, bin_e=bin_e_info,
            extra={"pipeline": "jp-client/build_jp_client.py", "mode": args.mode,
                   "server_addresses": {"grpc": args.grpc, "http": args.http,
                                        "auth": args.auth}
                   if args.mode == "patched" else None})
        sidecar_path = manifest_sidecar.write_sidecar(out, sidecar)
        sc_check = manifest_sidecar.verify_sidecar(sidecar_path, out)
        print(f"  manifest sidecar: {sidecar_path}（自检 {'ok' if sc_check['ok'] else sc_check['problems']}）")
        if not sc_check["ok"]:
            raise SystemExit("manifest sidecar 自检失败: " + json.dumps(sc_check["problems"]))
        final["manifest_sidecar"] = str(sidecar_path)

        # ---- 9) L6 统一验证门（末步）：适用项 A1-A9 全量复核（MANIFEST 预检 /
        # 证书断言 / bin.e 文件名不变 / RVA 表版本位 / bin.e 文本表带 zh / 字体
        # payload 四条目 / fix3 串 / region 匹配 / RVA 表按客户端选对）。断言定义
        # shared/gate_defs.py、执行器 shared/verify_gate.py；与 bunker 侧
        # verify_gate_zh.py 同 schema（nier-verify-gate/v1）。失败 fail-fast。
        sys.path.insert(0, str(JP.parent / "shared"))
        import verify_gate as VG
        l6 = VG.run_gate(apk=out, bin_e=bin_e_out, client="jp",
                         expect_bin_e_name=(bin_e_in.name if bin_e_out is not None else None),
                         sidecar=sidecar_path, manifest_dir=JP,
                         font_mode="zh", fix3_mode="required",
                         require_zh_text=True, gate_name="jp-build-final")
        for line in l6.render_lines():
            print(line)
        l6_path = l6.write_json(out.parent / (out.stem + ".gate.json"))
        print(f"  L6 统一验证门报告: {l6_path}")
        if not l6.ok:
            raise SystemExit("L6 统一验证门未通过（末步，fail-fast）")
        final["l6_gate"] = l6.to_dict()
        evidence = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "pipeline": "jp-client/build_jp_client.py",
            "mode": args.mode,
            "apk_input": {"path": str(apk), "bytes": apk.stat().st_size,
                          "sha256": input_sha, "untouched_hashes": original_hashes},
            "font_payload": payload,
            "server_addresses": {"grpc": args.grpc, "http": args.http, "auth": args.auth}
            if args.mode == "patched" else None,
            "workspace": str(work),
            "workdir_checks": work_checks,
            "private_patch_log_tail": patch_tail,
            "fix3": {"tool": str(FIX3_DIR / "patch_fix3.py"), "tier": "all",
                     "report_path": str(fix3_report_path), "apply_report": fix3_report,
                     "workdir_checks": fix3_checks, "log_tail": fix3_tail},
            "output": final,
            "bin_e": ({"tool": str(BUILD_BIN_E), "input": args.bin_e,
                       "output": str(bin_e_out) if bin_e_out else None,
                       "report": bin_e_report} if bin_e_report else None),
            "verify_json": str(verify_json) if verify_json.is_file() else None,
            "expected_cert_sha256": EXPECTED_CERT_SHA256,
            "elapsed_sec": round(time.time() - t0, 1),
            "log": str(log_path),
        }
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"产物: {final['bytes']:,}B sha256={final['sha256']}")
        if bin_e_out is not None:
            print(f"配套 bin.e 产物: {bin_e_out.stat().st_size:,}B sha256={sha256_file(bin_e_out)}")
        print(f"evidence: {evidence_path}")
        print(f"verify 报告: {verify_json}")
        print(f"日志: {log_path}")
        print(f"=== BUILD OK（{evidence['elapsed_sec']}s）===")
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        log_file.close()


if __name__ == "__main__":
    main()
