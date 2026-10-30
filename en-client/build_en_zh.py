#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
# 【归档副本 ARCHIVE】2026-10-29 归档
# 来源：E:\NieRReincarnation\zh-l10n\work\en-apk\build_en_zh.py
# 内容与来源一致（仅本头部注释为归档时添加，正文未改动）。
# 运行仍依赖 zh-l10n 工作区绝对路径（patch_fix3_en/ko、patch_fix3l、
# patch_fix4、fonts-fix4\out3\payload3、NieR-Re-In-carnation-Mod_Menu\en-client
# tools/keys 等），引用关系见同目录 README-EN.md。
# ---------------------------------------------------------------------
# 2026-10-29 L3a 客户端化落地（自此正文与归档源分叉）：
#   * MANIFEST 预检（en-client/MANIFEST.json + check_manifest）
#   * 客户端自动识别（shared/detect_client.py：region 三元组硬断言，误喂 JP/篡改 → fail-fast）
#   * 产物命名契约（缺省产物名 nier-en.apk；--out 语义保留）
#   * manifest sidecar（<产物名>.manifest.json，shared/manifest_sidecar.py）
#   * 验证门证书指纹断言（EN=7D:79:2C…A4:A1:73）
#   * 签名 key 收编：en-client/keys/nier-en.keystore（=debug.keystore 复制收编，原件保留）
#   * 私服补丁权威副本：en-client/patches/patch_apk_en.py + patch_auth_dynamic_en.py
# =====================================================================
"""build_en_zh.py — EN 汉化客户端离线构建驱动（私服补丁 → auth 动态 → fix3 内置串
→ fix3l 扩展键 → 四条目字体 payload3(Hangul) → EN mod 菜单 → en-client debug key 签名）。

抄 build_jp_zh.py 改（EN 侧）：
  * 复用 NieR-Re-In-carnation-Mod_Menu/en-client/tools 构建管线（EN RVA 菜单 + EN 注入）
  * 私服补丁 = lunar-scripts/android/patch_apk.py（EN 3.7.1 RVA；metadata host + NetworkConfig.get_ServerPort 端口同机制）
    + en-client/tools/patch_auth_dynamic_en.py（auth 动态化，同 build_all --auth-dynamic）
  * fix3 内置串 = zh-l10n/work/en-apk/patch_fix3_en.py（ui/titleflow EN 段按键名单→中文；
    metadata stringLiteral 同 JP 源串→中文，≤原字节）
    + zh-l10n/work/en-apk/patch_fix3_ko.py（**ko 段**同键→中文，与 EN 段同译文；
    T01 机制 len(new)<=len(old) 硬约束，2 条超长用 KO_OVERRIDE 短译 联系/去推特）
  * 字体 payload = zh-l10n/work/fonts-fix4/out2/payload2/assets/bin/Data（四条目一包齐；
    EN 容器按名+sha 对号入座，不一致时按 Font 角色回退重建，脚本全程校验 sha）
  * 签名 = en-client/keys/nier-en.keystore（L3a 收编 = debug.keystore；alias
    androiddebugkey / pass android；证书 7D:79:2C…A4:A1:73）按识别结果自动选；
    注意：覆盖官方 EN 安装会因签名不符失败，玩家需先卸载官方再安装（私服常态）。

用法（构建须用不受限解释器 + venv site-packages 挂 PYTHONPATH 取 UnityPy）：
  set PYTHONPATH=E:\\NieRReincarnation\\zh-l10n\\.venv\\Lib\\site-packages
  C:\\Python314\\python.exe build_en_zh.py --mode patched ^
      --apk "resources/NieR Re[in]carnation 3.7.1_EN.apk" ^
      --out "zh-l10n/work/en-apk/nier-mod-menu-en-font.apk" ^
      --work "NieR-Re-In-carnation-Mod_Menu/en-client/build/work_en_zh" --fresh ^
      --grpc 192.168.2.6:8003 --http 192.168.2.6:8080 --auth 192.168.2.6:3000

产物：APK + 构建日志 + evidence JSON（--out 所在目录/logs）。
"""
from __future__ import annotations

import argparse
import hashlib
import io
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
EN_LOCAL = Path(__file__).resolve().parent          # lunar-scripts-zh/en-client/
ZH_ROOT = EN_LOCAL.parent                          # lunar-scripts-zh/
sys.path.insert(0, str(ZH_ROOT / "shared"))
import detect_client  # noqa: E402
import manifest_sidecar  # noqa: E402

EN_CLIENT = ROOT / "NieR-Re-In-carnation-Mod_Menu" / "en-client"
TOOLS = EN_CLIENT / "tools"
# 私服补丁：en-client/patches/ 权威副本（L3a 收编；MANIFEST 登记 sha256）
PATCH_EN = EN_LOCAL / "patches" / "patch_apk_en.py"                 # 原 lunar-scripts patch_apk.py
AUTH_DYN = EN_LOCAL / "patches" / "patch_auth_dynamic_en.py"        # 原 en-client tools/ 同名
FIX3_EN = EN_LOCAL / "patch_fix3_en.py"                # en-client 本地副本（=zh-l10n 逐字节）
FIX3L = EN_LOCAL / "patch_fix3l.py"
FIX4 = EN_LOCAL / "patch_fix4.py"                      # 依赖 en-client/fix4_orig_en_values.json
FONT_PAYLOAD_DIR = ROOT / "zh-l10n" / "work" / "fonts-fix4" / "out3" / "payload3" / "assets" / "bin" / "Data"
VENV_SITE = ROOT / "zh-l10n" / ".venv" / "Lib" / "site-packages"
KEYSTORE = EN_LOCAL / "keys" / "nier-en.keystore"   # L3a 收编（= Mod_Menu debug.keystore）
MANIFEST = EN_LOCAL / "MANIFEST.json"
EXPECTED_CERT_SHA256 = "7d792c3cfefd73223764206edebd9526618638ff152165df5fbecd356aa4a173"

META_ENTRY = "assets/bin/Data/Managed/Metadata/global-metadata.dat"

# 四条目字体 payload：EN APK 内 Font 容器对号入座表（sha 实测 EN=JP 原版逐字节一致）。
# orig_* = EN 原版（注入前目标）；payload_* = payload2 文件。face_keywords 用于角色回退匹配。
FONT_TABLE = {
    "6f937efa0660c47f59d5215d276b1cbb": {
        "role": "UI(FOT-Rodin Pro DB -> Noto Sans CJK SC Medium 子集+Hangul)",
        "face_keywords": ["Rodin"],
        "orig_container_sha256": "6efd4e4238954b11d272a00936842f6c3d497053555ad2db884d8b6a55f86fe6",
        "orig_fontdata_sha256": "54e91901e29dd2c8f37a1675e873ca633bad7c68321cf19dfa4210808ff40591",
        "payload_sha256": "8c5827fcb21151787399cca61dd8b89a0e1101a9e1a5af2c4b27e0e1a9952233",
        "payload_fontdata_sha256": "27224151be7e42f58a88687990c2d7eef60f754f1c1ee042fdc6aae3a7da9199",
    },
    "7089ac60979c94824ac549baab08cfa7": {
        "role": "Story(A-OTF Talking Std R -> Noto Sans CJK SC Regular 子集+Hangul)",
        "face_keywords": ["Talking"],
        "orig_container_sha256": "0874af6d09293f6a2f9bcee2238b6e2e072350e8e142553a8de826dcdf63f9ca",
        "orig_fontdata_sha256": "be7a9a18e9eefe34e83b9d2ae16ec4e1c2b69f668ec6a9d9ca392c7a82a6c2a1",
        "payload_sha256": "c1907f2bad9d71738cc26a8cdb621d9370aeedbba479b01414da8139949621fc",
        "payload_fontdata_sha256": "e2a6cffb919130d6d9231979dd948c05659bc8fd3260f2423b0d4b17296f4194",
    },
    "ad1489eb70ff840d19d7d0841bcdd3a9": {
        "role": "YDHopeL(Applibot-YDHope M -> Noto Sans CJK SC Regular 子集+Hangul)",
        "face_keywords": ["YDHope"],
        "orig_container_sha256": "e16c851c0e1d53a32dea4cdc836b0b8a9ab509cb94f0ccc480405893c1463144",
        "orig_fontdata_sha256": "20dbc01e532ebde65fcfb68a6cca077fdbe5d53194ac5470aa0e4e8173db9162",
        "payload_sha256": "f08ba7ff06991072d928b52daf86c1a6bf226c59653d728cc71408c6242c1ae3",
        "payload_fontdata_sha256": "37d360aec2f4f6ed2040149e9e079834aaf73a43a6b43bd91e5721e341374f69",
    },
    "550e0743a6b6344cfa3380b9a07f58b6": {
        "role": "YDWingsM(Applibot-YDWings M -> Noto Sans CJK SC Medium 子集+Hangul)",
        "face_keywords": ["YDWings"],
        "orig_container_sha256": "f128a23b0e1ca27abf0435fee733daba7e0201f6ad755e9d97cd445301a6b56a",
        "orig_fontdata_sha256": "917148a37041222a9913e330220e09c74146b648ac572d8083ae548c8cc73b2c",
        "payload_sha256": "b18ee0b9b54472a3f6b8f6c5bb320fe42da3cc28b5034d4857519688ebbbf8ae",
        "payload_fontdata_sha256": "b973a96628222c68aa182b4aa89ae1cbe956e5a323eb05ed2431351cc40f7b44",
    },
}

# fix3-EN 自检抽查（EN TextAsset 内中文译文 + metadata 中文，UTF-8 子串）
FIX3_SPOT_ZH = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": [
        "公告", "联系我们", "数据继承", "数据修复", "其他信息", "删除数据",
        "关闭", "取消", "下载确认",
        "将进行数据修复。确定吗？", "数据修复已完成", "菜单", "删除", "同意",
        "结束游戏", "要结束游戏吗？", "返回标题", "错误", "维护中",
    ],
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": [
        "下载确认", "注册玩家名", "请输入玩家名",
        "将开始约{0}MB的数据下载", "下载设置",
        "网络错误", "重试", "序列号", "继续", "放弃",
    ],
}
FIX3_META_ZH = ["公告", "关闭", "取消", "播放影片", "播放影片中", "打开公告", "打开推特"]

# fix3l 扩展键抽查（EN+ko 双段；词取自对应表的实际值）
FIX3L_SPOT_ZH = {
    "assets/bin/Data/a1e9ec10c664743ac927859dda597701": [
        "是", "否", "确认", "成功", "传输完成。", "加载中",
    ],
    "assets/bin/Data/6c88814b67ea44496a219083a723a1e5": [
        "年龄确认", "广告", "卸载请求", "点击开始", "预下载",
    ],
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": [
        "是", "否", "确认", "成功", "传输完成。", "加载中",
    ],
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": [
        "年龄确认", "是否满16岁", "广告", "卸载请求", "点击开始", "预下载",
    ],
}

# fix3-ko（ko 段双改）：工具 + ko 载体抽查（含 2 条 KO_OVERRIDE 短译 联系/去推特）
FIX3_KO = EN_LOCAL / "patch_fix3_ko.py"
FIX3_SPOT_ZH_KO = {
    "assets/bin/Data/311a825b7b4ba4b7b854ee567c51d486": [
        "公告", "联系", "数据继承", "数据修复", "其他信息", "删除数据",
        "关闭", "取消", "下载确认",
        "将进行数据修复。确定吗？", "数据修复已完成", "菜单", "删除", "同意",
        "结束游戏", "要结束游戏吗？", "返回标题", "错误", "维护中",
    ],
    "assets/bin/Data/3286caf719be04314bd3208e16bc0e0e": [
        "下载确认", "注册玩家名", "请输入玩家名",
        "将开始约{0}MB的数据下载", "下载设置",
        "网络错误", "重试", "序列号", "继续", "放弃", "去推特",
    ],
}


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


def check_manifest() -> dict:
    """MANIFEST 预检（镜像 jp-client 口径）：en-client/ 权威副本 + 自撰文件 sha256 校验。"""
    if not MANIFEST.is_file():
        raise SystemExit(f"缺少 MANIFEST.json: {MANIFEST}")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = []
    for item in man["items"]:
        p = EN_LOCAL / item["path"]
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


def run_logged(cmd, log_path: Path, cwd=None, env=None) -> tuple[int, list[str]]:
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


def _fontdata_of(container_bytes: bytes) -> tuple[bytes | None, list[str]]:
    """返回 (m_FontData, face 名列表)；不唯一/缺失返回 (None, faces)。"""
    import UnityPy

    env = UnityPy.load(container_bytes)
    fds = []
    faces: list[str] = []
    for obj in env.objects:
        if obj.type.name != "Font":
            continue
        d = obj.read()
        fd = bytes(d.m_FontData)
        fds.append(fd)
        try:
            from fontTools.ttLib import TTFont
            tt = TTFont(io.BytesIO(fd), lazy=True)
            faces.append(tt["name"].getDebugName(1) or "")
            tt.close()
        except Exception:  # noqa: BLE001
            faces.append("")
    if len(fds) != 1:
        return None, faces
    return fds[0], faces


def font_payload_meta(payload_dir: Path) -> dict:
    files = {}
    for p in sorted(payload_dir.iterdir()):
        if p.is_file():
            files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    missing = [n for n in FONT_TABLE if n not in files]
    if missing:
        raise SystemExit(f"字体 payload 缺少必需文件: {missing}")
    for n, meta in FONT_TABLE.items():
        if files[n]["sha256"] != meta["payload_sha256"]:
            raise SystemExit(f"字体 payload sha 不符: {n} {files[n]['sha256']} != {meta['payload_sha256']}")
    return files


def inject_fonts_en(work: Path, payload_dir: Path) -> list[dict]:
    """四条目对号入座注入 EN 解包目录：
    1) 目标容器必须存在（替换不新增）；
    2) 目标 sha == 表内 orig_container_sha256（EN=JP 原版实测）→ 直接覆盖 payload 文件；
       否则回退：目标 Font 的 m_FontData/face 角色匹配 → 仅换 m_FontData 重建容器；
    3) 注入后 sha 复核（直接覆盖 = payload sha；重建 = 新 sha）+ m_FontData sha = payload 字体。"""
    dst_dir = work / "assets" / "bin" / "Data"
    if not dst_dir.is_dir():
        raise SystemExit(f"解包目录缺少 assets/bin/Data: {work}")
    results = []
    for name, t in FONT_TABLE.items():
        src = payload_dir / name
        dst = dst_dir / name
        if not dst.is_file():
            raise SystemExit(f"EN APK 内不存在字体容器（不能新增）: assets/bin/Data/{name}")
        r = {"name": name, "role": t["role"]}
        dst_sha = sha256_file(dst)
        r["target_orig_sha256"] = dst_sha
        r["target_orig_bytes"] = dst.stat().st_size
        r["matches_orig_table"] = dst_sha == t["orig_container_sha256"]
        if r["matches_orig_table"]:
            shutil.copy2(src, dst)
            r["mode"] = "direct-copy"
        else:
            # 角色回退：目标 Font m_FontData sha 或 face 关键字命中才允许重建
            fd, faces = _fontdata_of(dst.read_bytes())
            r["target_faces"] = faces
            r["target_fontdata_sha256"] = sha256_bytes(fd) if fd else None
            role_ok = (fd is not None and sha256_bytes(fd) == t["orig_fontdata_sha256"]) or \
                      any(k.lower() in (f or "").lower() for f in faces for k in t["face_keywords"])
            if fd is None or not role_ok:
                raise SystemExit(f"字体容器对号入座失败（sha/角色均不匹配）: {name} faces={faces}")
            pfd, _pfaces = _fontdata_of(src.read_bytes())
            if pfd is None or sha256_bytes(pfd) != t["payload_fontdata_sha256"]:
                raise SystemExit(f"payload 字体校验失败: {name}")
            import UnityPy
            env = UnityPy.load(dst.read_bytes())
            for obj in env.objects:
                if obj.type.name == "Font":
                    d = obj.read()
                    d.m_FontData = pfd
                    d.save()
                    break
            new_buf = list(env.files.values())[0].save()
            dst.write_bytes(new_buf)
            r["mode"] = "fontdata-rebuild"
        after_sha = sha256_file(dst)
        r["after_sha256"] = after_sha
        r["after_bytes"] = dst.stat().st_size
        if r["mode"] == "direct-copy":
            r["sha_matches_payload"] = after_sha == t["payload_sha256"]
        else:
            r["sha_matches_payload"] = True  # 重建态按 m_FontData 校验
        fd2, faces2 = _fontdata_of(dst.read_bytes())
        r["after_fontdata_sha256"] = sha256_bytes(fd2) if fd2 else None
        r["after_faces"] = faces2
        r["fontdata_matches_payload"] = r["after_fontdata_sha256"] == t["payload_fontdata_sha256"]
        if not (r["sha_matches_payload"] and r["fontdata_matches_payload"]):
            raise SystemExit(f"字体注入后校验失败: {name} {r}")
        print(f"  [font] {name[:8]}… {r['mode']} {t['role']} "
              f"{r['target_orig_bytes'] / 1048576:.2f}MB -> {r['after_bytes'] / 1048576:.2f}MB")
        results.append(r)
    return results


def app_original_hashes(apk: Path) -> dict:
    with zipfile.ZipFile(apk) as zf:
        out = {}
        for name in ("lib/arm64-v8a/libil2cpp.so", META_ENTRY, "AndroidManifest.xml"):
            out[name] = sha256_bytes(zf.read(name))
        for name in FONT_TABLE:
            out[f"assets/bin/Data/{name}"] = sha256_bytes(zf.read(f"assets/bin/Data/{name}"))
        return out


def verify_fix3_workdir(work: Path) -> dict:
    checks: dict = {"textassets": {}, "metadata": {}}
    spot = {**FIX3_SPOT_ZH, **FIX3_SPOT_ZH_KO, **FIX3L_SPOT_ZH}   # EN + ko + fix3l 抽查
    for rel, needles in spot.items():
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
        "hits": {n: (n.encode("utf-8") in blob) for n in FIX3_META_ZH},
    }
    checks["ok"] = bool(
        checks["metadata"]["exists"]
        and all(checks["metadata"]["hits"].values())
        and all(v["exists"] and all(v["hits"].values()) for v in checks["textassets"].values())
    )
    return checks


def verify_workdir(work: Path, payload: dict, mode: str, grpc_host: str, font_results: list[dict]) -> dict:
    checks: dict = {}
    data_dir = work / "assets" / "bin" / "Data"
    checks["font_files"] = {r["name"]: {
        "mode": r["mode"], "sha256": r["after_sha256"], "matches_payload": r["sha_matches_payload"],
        "fontdata_matches_payload": r["fontdata_matches_payload"],
    } for r in font_results}
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
    # 私服补丁标记（EN 侧）：metadata 内私服 host、AuthHost.smali、smali 内私服 IP
    checks["private_patch"] = {"mode": mode}
    if mode == "patched":
        meta = work / META_ENTRY
        meta_blob = meta.read_bytes() if meta.is_file() else b""
        auth_host = list(work.rglob("AuthHost.smali"))
        smali_ip_hits = []
        for entry in work.iterdir():
            if re.fullmatch(r"smali(?:_classes\d+)?", entry.name) and entry.is_dir():
                for smali in entry.rglob("*.smali"):
                    try:
                        if grpc_host.encode() in smali.read_bytes():
                            smali_ip_hits.append(str(smali.relative_to(work)))
                    except OSError:
                        continue
        checks["private_patch"].update({
            "metadata_has_grpc_host": grpc_host.encode() in meta_blob,
            "metadata_ip_hits": meta_blob.count(grpc_host.encode()),
            "authhost_smali": [str(p.relative_to(work)) for p in auth_host],
            "smali_ip_hits": smali_ip_hits[:20],
        })
    checks["ok"] = bool(
        all(v["matches_payload"] and v["fontdata_matches_payload"] for v in checks["font_files"].values())
        and checks["menu"]["main_smali"]
        and checks["menu"]["libniermenu_so"]
        and checks["manifest"]["has_system_alert_window"]
        and checks["manifest"]["has_menu_service"]
        and checks["start_call"]
        and (mode != "patched" or (
            checks["private_patch"]["metadata_has_grpc_host"]
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
        for name in FONT_TABLE:
            try:
                data = zf.read("assets/bin/Data/" + name)
                fd, faces = _fontdata_of(data)
                result["font_files"][name] = {
                    "bytes": len(data), "sha256": sha256_bytes(data),
                    "matches_payload": sha256_bytes(data) == FONT_TABLE[name]["payload_sha256"],
                    "fontdata_sha256": sha256_bytes(fd) if fd else None,
                    "fontdata_matches_payload": fd is not None and
                        sha256_bytes(fd) == FONT_TABLE[name]["payload_fontdata_sha256"],
                    "faces": faces,
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
                result["private_patch_libil2cpp_sha256"] = sha256_bytes(zf.read("lib/arm64-v8a/libil2cpp.so"))
            except KeyError:
                pass
        # 私服 IP 命中数（逐条目）
        ip = b"192.168.2.6"
        ip_hits = {}
        total = 0
        for n in zf.namelist():
            if n.endswith("/"):
                continue
            try:
                c = zf.read(n).count(ip)
            except Exception:  # noqa: BLE001
                continue
            if c:
                ip_hits[n] = c
                total += c
        result["private_ip_hits"] = {"total": total, "per_entry": ip_hits}
    return result


def verify_fix3_final_apk(apk: Path) -> dict:
    """从最终 APK 回读 fix3：EN TextAsset 键值=中文（68 键）+ metadata 中文 7 值
    + **ko 段** 键值=中文（68 键，含 2 短译）且旧 ko 值残留 0。"""
    import UnityPy

    sys.path.insert(0, str(HERE_DIR))
    import patch_fix3_en as F  # noqa: E402
    import patch_fix3_ko as K  # noqa: E402
    import patch_fix3l as L  # noqa: E402

    entries = F.load_entries("all")
    kmap = F.key_map(entries)
    mrep = F.meta_repl(entries)
    kmap_ko = K.key_map(K.load_entries("all"))
    kmap_l_en = {k: v["en"] for k, v in L.FIX3L_KEYS.items()}
    kmap_l_ko = {k: v["ko"] for k, v in L.FIX3L_KEYS.items()}
    old_ko = {}
    if K.APPLY_REPORT.is_file():
        old_ko = json.loads(K.APPLY_REPORT.read_text(encoding="utf-8")).get("old_ko_values", {})
    res = {"textassets": {}, "metadata": {}, "ko_textassets": {}}
    with zipfile.ZipFile(apk) as zf:
        total_keys, total_zh = 0, 0
        for entry, label in F.TS_EN.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = F._ta_text(obj.read())
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {}
            for k, zh in kmap.items():
                if k in kv:
                    hits[k] = {"is_zh": kv[k] == zh, "value_preview": kv[k][:24]}
            n_zh = sum(1 for v in hits.values() if v["is_zh"])
            total_keys += len(hits)
            total_zh += n_zh
            res["textassets"][label] = {"keys_found": len(hits), "zh_hits": n_zh,
                                        "bad": [k for k, v in hits.items() if not v["is_zh"]]}
        # ko 段回读：键值=中文 + 旧 ko 值残留 0
        ko_keys, ko_zh, ko_old = 0, 0, 0
        for entry, label in K.TS_KO.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = K._ta_text(obj.read())
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {}
            old_left = []
            for k, zh in kmap_ko.items():
                if k in kv:
                    hits[k] = {"is_zh": kv[k] == zh, "value_preview": kv[k][:24]}
                    if old_ko.get(k) is not None and kv[k] == old_ko[k]:
                        old_left.append(k)
            n_zh = sum(1 for v in hits.values() if v["is_zh"])
            ko_keys += len(hits)
            ko_zh += n_zh
            ko_old += len(old_left)
            res["ko_textassets"][label] = {"keys_found": len(hits), "zh_hits": n_zh,
                                           "bad": [k for k, v in hits.items() if not v["is_zh"]],
                                           "old_value_residual_keys": old_left}
        # fix3l 扩展键回读（EN 段 + ko 段）
        fix3l_res = {"en": {}, "ko": {}}
        fix3l_en_total, fix3l_en_zh = 0, 0
        for entry, label in L.TS_EN.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = L._ta_text(obj.read())
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {}
            for k, zh in kmap_l_en.items():
                if k in kv:
                    hits[k] = {"is_zh": kv[k] == zh, "value_preview": kv[k][:24]}
            n_zh = sum(1 for v in hits.values() if v["is_zh"])
            fix3l_en_total += len(hits)
            fix3l_en_zh += n_zh
            fix3l_res["en"][label] = {"keys_found": len(hits), "zh_hits": n_zh,
                                       "bad": [k for k, v in hits.items() if not v["is_zh"]]}
        fix3l_ko_total, fix3l_ko_zh = 0, 0
        for entry, label in L.TS_KO.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = L._ta_text(obj.read())
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {}
            for k, zh in kmap_l_ko.items():
                if k in kv:
                    hits[k] = {"is_zh": kv[k] == zh, "value_preview": kv[k][:24]}
            n_zh = sum(1 for v in hits.values() if v["is_zh"])
            fix3l_ko_total += len(hits)
            fix3l_ko_zh += n_zh
            fix3l_res["ko"][label] = {"keys_found": len(hits), "zh_hits": n_zh,
                                       "bad": [k for k, v in hits.items() if not v["is_zh"]]}
        res["fix3l_textassets"] = fix3l_res
        meta = zf.read(META_ENTRY)
        ents, sld, _ = F.meta_entries(meta)
        per = {}
        m_zh = 0
        for old, zh in mrep.items():
            ob, nb = old.encode("utf-8"), zh.encode("utf-8")
            old_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(ob) and meta[sld + e_idx:sld + e_idx + e_len] == ob)
            new_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(nb) and meta[sld + e_idx:sld + e_idx + e_len] == nb)
            per[f"{old}->{zh}"] = {"old_remaining": old_n, "new_hits": new_n, "ok": old_n == 0 and new_n >= 1}
            if per[f"{old}->{zh}"]["ok"]:
                m_zh += 1
        res["metadata"] = per
        res["totals"] = {"ta_keys": total_keys, "ta_zh_hits": total_zh,
                         "ko_ta_keys": ko_keys, "ko_ta_zh_hits": ko_zh,
                         "ko_old_value_residual": ko_old,
                         "fix3l_en_keys": fix3l_en_total, "fix3l_en_zh": fix3l_en_zh,
                         "fix3l_ko_keys": fix3l_ko_total, "fix3l_ko_zh": fix3l_ko_zh,
                         "meta_expected": len(mrep), "meta_zh_hits": m_zh,
                         "all_ta_zh": total_keys == total_zh and total_keys > 0,
                         "all_ko_ta_zh": ko_keys == ko_zh and ko_keys > 0 and ko_old == 0,
                         "all_fix3l_zh": fix3l_en_total == fix3l_en_zh and fix3l_en_total > 0
                                         and fix3l_ko_total == fix3l_ko_zh and fix3l_ko_total > 0,
                         "all_meta_zh": m_zh == len(mrep)}
        res["ok"] = (res["totals"]["all_ta_zh"] and res["totals"]["all_meta_zh"]
                     and res["totals"]["all_ko_ta_zh"] and res["totals"]["all_fix3l_zh"])
    return res


HERE_DIR = Path(__file__).resolve().parent


def verify_fix4_final_apk(apk: Path) -> dict:
    """从最终 APK 回读 fix4：EN 段 81 键=原版英文值 + metadata 中文 7 值
    + ko 段 68+13 键=中文 + ko 段 67 nt 键=中文。"""
    import UnityPy

    sys.path.insert(0, str(HERE_DIR))
    import patch_fix4 as P4  # noqa: E402

    orig_en = P4.load_orig_en()
    nt_ko = P4.NT_KO_TRANSLATIONS

    # metadata 7（同 fix3）
    entries_f3 = json.loads((ROOT / "zh-l10n" / "work" / "apk" / "fix3" / "builtin_strings.json")
                            .read_text(encoding="utf-8"))
    mrep = {}
    for e in entries_f3["entries"]:
        if e.get("expected_metadata") and e.get("target_zh"):
            s = e["source_ja"]
            if s.startswith("titleflow.dialog.termofservice"):
                continue
            mrep[s] = e["target_zh"]

    res = {"en_restore": {}, "metadata": {}, "ko_nt": {}, "ok": True}
    with zipfile.ZipFile(apk) as zf:
        # EN 段：81 键 = 原版英文
        en_total, en_match = 0, 0
        for entry, label in P4.TS_EN.items():
            buf = zf.read(entry)
            env = UnityPy.load(buf)
            kv = {}
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    text = P4._ta_text(obj.read())
                    for line in text.split("\n"):
                        sep = line.find(":")
                        if sep > 0:
                            kv[line[:sep]] = line[sep + 1:]
            hits = {}
            for k, expected in orig_en.items():
                if k in kv:
                    hits[k] = {"is_orig_en": kv[k] == expected, "value_preview": kv[k][:24]}
            n_match = sum(1 for v in hits.values() if v["is_orig_en"])
            en_total += len(hits)
            en_match += n_match
            res["en_restore"][label] = {"keys_found": len(hits), "en_match": n_match,
                                        "bad": [k for k, v in hits.items() if not v["is_orig_en"]]}
        # metadata 7
        meta = zf.read(META_ENTRY)
        ents, sld, _ = _meta_entries(meta)
        m_zh = 0
        per_meta = {}
        for old, zh in mrep.items():
            ob, nb = old.encode("utf-8"), zh.encode("utf-8")
            old_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(ob) and meta[sld + e_idx:sld + e_idx + e_len] == ob)
            new_n = sum(1 for (i, e_off, e_len, e_idx) in ents
                        if e_len == len(nb) and meta[sld + e_idx:sld + e_idx + e_len] == nb)
            ok = old_n == 0 and new_n >= 1
            per_meta[f"{old}->{zh}"] = {"old_remaining": old_n, "new_hits": new_n, "ok": ok}
            if ok:
                m_zh += 1
        res["metadata"] = per_meta
        # ko 段 nt：67 键 = 中文
        nt_ko_entry = "assets/bin/Data/d3f332a247d3c418d94d377ae81104c7"
        buf = zf.read(nt_ko_entry)
        env = UnityPy.load(buf)
        kv = {}
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                text = P4._ta_text(obj.read())
                for line in text.split("\n"):
                    sep = line.find(":")
                    if sep > 0:
                        kv[line[:sep]] = line[sep + 1:]
        hits = {}
        for k, spec in nt_ko.items():
            if k in kv:
                hits[k] = {"is_zh": kv[k] == spec["zh"], "value_preview": kv[k][:24]}
        nt_total = len(hits)
        nt_zh = sum(1 for v in hits.values() if v["is_zh"])
        res["ko_nt"] = {"keys_found": nt_total, "zh_hits": nt_zh,
                        "bad": [k for k, v in hits.items() if not v["is_zh"]]}
        res["totals"] = {
            "en_keys": en_total, "en_match": en_match,
            "meta_expected": len(mrep), "meta_zh_hits": m_zh,
            "ko_nt_keys": nt_total, "ko_nt_zh_hits": nt_zh,
            "all_en_restored": en_total == en_match and en_total > 0,
            "all_meta_zh": m_zh == len(mrep),
            "all_ko_nt_zh": nt_total == nt_zh and nt_total > 0,
        }
        res["ok"] = (res["totals"]["all_en_restored"] and res["totals"]["all_meta_zh"]
                     and res["totals"]["all_ko_nt_zh"])
    return res


def _meta_entries(data: bytes):
    import struct
    sl_off, sl_size = struct.unpack_from("<II", data, 8)
    sld_off, sld_size = struct.unpack_from("<II", data, 16)
    out = []
    for i in range(sl_size // 8):
        e_off = sl_off + i * 8
        e_len, e_idx = struct.unpack_from("<II", data, e_off)
        out.append((i, e_off, e_len, e_idx))
    return out, sld_off, sld_size


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["patched", "original"], default="patched")
    ap.add_argument("--apk", required=True, help="原版 EN APK（只读）")
    ap.add_argument("--out", default=None,
                    help="输出 APK 路径（缺省按命名契约 nier-en.apk；--out 语义保留）")
    ap.add_argument("--work", default=None,
                    help=f"apktool 解包目录（缺省 {EN_LOCAL / 'build' / 'work'}）")
    ap.add_argument("--font-payload", default=str(FONT_PAYLOAD_DIR))
    ap.add_argument("--grpc", default="192.168.2.6:8003")
    ap.add_argument("--http", default="192.168.2.6:8080")
    ap.add_argument("--auth", default="192.168.2.6:3000")
    ap.add_argument("--fresh", action="store_true", help="强制重新解包")
    ap.add_argument("--no-private-patch", action="store_true", help="同 --mode original")
    args = ap.parse_args()
    mode = "original" if args.no_private_patch else args.mode

    apk = Path(args.apk).resolve()
    # 客户端自动识别（L3a）：region 三元组硬断言，先于一切产物/日志路径；
    # 未知客户端 / 三元组不符 / 误喂 JP 包 → fail-fast（不产出任何文件）
    client = detect_client.detect_client(apk, expect="en")
    product_name = client["product_name"]
    key_info = detect_client.key_for_region(client["region"])
    out = Path(args.out).resolve() if args.out else (EN_LOCAL / "out" / product_name)
    work = Path(args.work).resolve() if args.work else (EN_LOCAL / "build" / "work")
    payload_dir = Path(args.font_payload).resolve()
    log_dir = out.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{stamp}-build-en-{mode}.log"

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
        build_started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        print(f"=== EN 汉化客户端构建 mode={mode} ===")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输入 APK: {apk}")
        print(f"输出 APK: {out}")
        print(f"解包目录: {work}")
        print(f"字体 payload: {payload_dir}")

        # ---- 0/7 预检（MANIFEST / 客户端识别 / 工具 / 输入）----
        print("=== 0/7 预检（MANIFEST / 客户端识别 / 工具 / 输入）===")
        man = check_manifest()
        print(f"  MANIFEST 校验 ok（{man['files']} 个权威副本 sha256 一致）")
        print(f"  客户端识别 ok: region={client['region']} package={client['package']}")
        print(f"  region 三元组硬断言 ok: {client['bytes']:,}B sha256={client['sha256'][:16]}…")
        print(f"  产物命名契约: {product_name}（--out 显式指定时以 --out 为准）")
        if out.name != product_name:
            print(f"  [!] --out 名 {out.name!r} 与契约名 {product_name!r} 不同"
                  f"（--out 语义保留；sidecar 仍按契约登记）")
        print(f"  签名 key 自动选: {key_info['keystore']} alias={key_info['alias']}"
              f"（L3a 收编 key）")
        print(f"  期望证书 SHA-256: {key_info['cert_sha256']}")
        if mode == "patched":
            print(f"私服地址: gRPC={args.grpc} HTTP={args.http} auth={args.auth}")

        # UnityPy 可用性（当前解释器 + venv site-packages 回退）
        fix3_env = os.environ.copy()
        try:
            import UnityPy  # noqa: F401
        except ImportError:
            if not VENV_SITE.is_dir():
                raise SystemExit(f"UnityPy 不可用，且 venv site-packages 不存在: {VENV_SITE}")
            fix3_env["PYTHONPATH"] = str(VENV_SITE) + os.pathsep + fix3_env.get("PYTHONPATH", "")

        sys.path.insert(0, str(TOOLS))
        import _common as C  # noqa: E402
        import build_menu  # noqa: E402
        import inject_modmenu  # noqa: E402

        try:
            C.init_log(f"zh-build-en-{mode}")
        except PermissionError:
            C.LOG_DIR = str(log_dir)
            C.init_log(f"zh-build-en-{mode}")

        # 工具链：沿用 jp-client toolpaths 的 java/apktool/SDK；签名 key 按识别结果自动选
        cfg = {
            "java": "java",
            "java_home": r"C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot",
            "android_home": r"C:\Users\Yu\AppData\Local\Android\Sdk",
            "apktool_jar": r"E:\NieRReincarnation\jp\apktool.jar",
            "keystore": key_info["keystore"],
            "ks_pass": key_info["pass"],
            "ks_alias": key_info["alias"],
        }
        tools = C.detect_tools(cfg)
        C.log(f"工具: apktool={C.local_path(tools['apktool_jar'])}")
        C.log(f"工具: build-tools={C.local_path(os.path.dirname(tools['zipalign']))}")
        C.log(f"工具: keystore={tools['keystore']} alias={tools['ks_alias']} (nier-en 收编 key)")

        if not apk.is_file():
            raise SystemExit(f"输入 APK 不存在: {apk}")
        original_hashes = app_original_hashes(apk)
        payload = font_payload_meta(payload_dir)
        for name, meta in payload.items():
            print(f"  字体 payload: {name} {meta['bytes']:,}B {meta['sha256']}")

        # ---- 1) 菜单编译 + extract（EN 菜单，EN RVA）----
        C.log("=== 1/7 编译/复用 EN 菜单 APK 并 extract ===")
        menu_apk = build_menu.build_apk(cfg, tools, auto_yes=True, no_input=True)
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
        C.log("=== 2/7 解包/复用目标 APK ===")
        inject_modmenu.ensure_work(apk, work, tools, args.fresh, True, True)

        # ---- 3) 私服补丁（en-client/patches/patch_apk_en.py 权威副本，EN 3.7.1 RVA）----
        if mode == "patched":
            C.log("=== 3/7 私服补丁（patches/patch_apk_en.py + patches/patch_auth_dynamic_en.py）===")
            if not PATCH_EN.is_file():
                raise SystemExit(f"私服补丁权威副本不存在: {PATCH_EN}")
            rc, lines = run_logged([
                sys.executable, PATCH_EN, str(work),
                "--grpc-addr", args.grpc, "--http-addr", args.http, "--auth-host", args.auth,
            ], log_path, cwd=PATCH_EN.parent, env=fix3_env)
            if rc != 0:
                raise SystemExit(f"私服补丁失败 exit={rc}")
            patch_tail = lines[-40:]
            # auth 动态化（同 en-client build_all --auth-dynamic；权威副本收编）
            C.log("=== 3.5/7 auth 地址动态化（patches/patch_auth_dynamic_en.py）===")
            if not AUTH_DYN.is_file():
                raise SystemExit(f"auth 动态化权威副本不存在: {AUTH_DYN}")
            rc, lines = run_logged([
                sys.executable, AUTH_DYN, str(work),
                "--auth-host", args.auth,
            ], log_path, cwd=AUTH_DYN.parent, env=fix3_env)
            if rc != 0:
                raise SystemExit(f"auth 动态化失败 exit={rc}")
            authdyn_tail = lines[-30:]
        else:
            C.log("=== 3/7 跳过私服补丁（mode=original）===")
            patch_tail = []
            authdyn_tail = []

        # ---- 4) fix3 内置弹窗串：EN 段 + ko 段双改（就地，私服后、字体前）----
        C.log("=== 4/7 fix3-EN 内置串补丁（patch_fix3_en.py apply，EN 段）===")
        if not FIX3_EN.is_file():
            raise SystemExit(f"fix3-EN 补丁脚本不存在: {FIX3_EN}")
        if not FIX3_KO.is_file():
            raise SystemExit(f"fix3-ko 补丁脚本不存在: {FIX3_KO}")
        fix3_py = Path(sys.executable)
        rc, lines = run_logged([
            fix3_py, FIX3_EN, "apply", "--work", str(work), "--tier", "all",
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit(f"fix3-EN 内置串补丁失败 exit={rc}")
        fix3_tail = lines[-40:]
        rc, lines = run_logged([
            fix3_py, FIX3_EN, "verify", "--work", str(work), "--tier", "all",
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit("fix3-EN verify 失败，拒绝重打包")
        fix3_report_path = HERE_DIR / "apply_report_en.json"
        fix3_report = (json.loads(fix3_report_path.read_text(encoding="utf-8"))
                       if fix3_report_path.is_file() else {})
        C.log("=== 4b/7 fix3-ko 内置串补丁（patch_fix3_ko.py apply，ko 段，≤原字节）===")
        rc, lines = run_logged([
            fix3_py, FIX3_KO, "apply", "--work", str(work), "--tier", "all",
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit(f"fix3-ko 内置串补丁失败 exit={rc}")
        fix3_ko_tail = lines[-40:]
        rc, lines = run_logged([
            fix3_py, FIX3_KO, "verify", "--work", str(work), "--tier", "all",
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit("fix3-ko verify 失败，拒绝重打包")
        fix3_ko_report_path = HERE_DIR / "apply_report_ko.json"
        fix3_ko_report = (json.loads(fix3_ko_report_path.read_text(encoding="utf-8"))
                          if fix3_ko_report_path.is_file() else {})
        C.log("=== 4c/7 fix3l 扩展键补丁（patch_fix3l.py apply，EN+ko 双段）===")
        if not FIX3L.is_file():
            raise SystemExit(f"fix3l 补丁脚本不存在: {FIX3L}")
        rc, lines = run_logged([
            fix3_py, FIX3L, "apply", "--work", str(work),
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit(f"fix3l 补丁失败 exit={rc}")
        fix3l_tail = lines[-40:]
        rc, lines = run_logged([
            fix3_py, FIX3L, "verify", "--work", str(work),
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit("fix3l verify 失败，拒绝重打包")
        fix3l_report_path = HERE_DIR / "apply_report_fix3l.json"
        fix3l_report = (json.loads(fix3l_report_path.read_text(encoding="utf-8"))
                        if fix3l_report_path.is_file() else {})
        fix3_checks = verify_fix3_workdir(work)
        C.log("fix3 EN+ko 自检: " + json.dumps(fix3_checks, ensure_ascii=False)[:800])
        if not (fix3_checks["ok"] and fix3_report.get("ok", True) and fix3_ko_report.get("ok", True)
                and fix3l_report.get("ok", True)):
            raise SystemExit("fix3 自检失败（EN/ko），拒绝重打包")

        # ---- 4d/7 fix4 纯净化：EN 段 81 键还原 + ko 段 67 nt 键翻译 ----
        C.log("=== 4d/7 fix4 纯净化（patch_fix4.py apply，EN 还原 + ko nt 翻译）===")
        if not FIX4.is_file():
            raise SystemExit(f"fix4 补丁脚本不存在: {FIX4}")
        rc, lines = run_logged([
            fix3_py, FIX4, "apply", "--work", str(work),
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit(f"fix4 补丁失败 exit={rc}")
        fix4_tail = lines[-40:]
        rc, lines = run_logged([
            fix3_py, FIX4, "verify", "--work", str(work),
        ], log_path, cwd=HERE_DIR, env=fix3_env)
        if rc != 0:
            raise SystemExit("fix4 verify 失败，拒绝重打包")
        fix4_report_path = HERE_DIR / "apply_report_fix4.json"
        fix4_report = (json.loads(fix4_report_path.read_text(encoding="utf-8"))
                       if fix4_report_path.is_file() else {})
        C.log("fix4 自检: " + json.dumps({k: v for k, v in fix4_report.items() if k != "files"},
                                         ensure_ascii=False)[:400])

        # ---- 5) 字体 payload 注入（四条目对号入座 + sha 校验）----
        C.log("=== 5/7 字体 payload 注入（四条目）===")
        font_results = inject_fonts_en(work, payload_dir)

        # ---- 6) mod 菜单注入（EN）----
        C.log("=== 6/7 EN mod 菜单注入 ===")
        inject_modmenu.inject_smali(work)
        inject_modmenu.inject_manifest(work)
        inject_modmenu.inject_start_call(work)

        work_checks = verify_workdir(work, payload, mode, args.grpc.split(":")[0], font_results)
        C.log("解包目录自检: " + json.dumps(work_checks, ensure_ascii=False)[:800])
        if not work_checks["ok"]:
            raise SystemExit("解包目录自检失败，拒绝重打包")

        # ---- 7) 重建 + zipalign + 签名（en-client debug key）----
        C.log("=== 7/7 重建 + 对齐 + 签名（en-client debug key / alias androiddebugkey / android）===")
        inject_modmenu.build_and_sign(tools, work, str(out))

        C.log("=== 产物验证 ===")
        verify = apksigner_verify(Path(tools["java"]), Path(C.local_path(tools["apksigner_jar"])),
                                  out, log_path)
        align = zipalign_check(Path(tools["zipalign"]), out, log_path)
        final = apk_final_check(out, payload, mode)
        fix4_final = verify_fix4_final_apk(out)
        print(f"签名证书 SHA-256: {verify['cert_sha256']}")
        print(f"apksigner: v2={verify['verified_v2']} v3={verify['verified_v3']} "
              f"cert_match={verify['cert_matches_expected']}")
        print(f"zipalign: {align['ok']}")
        print(f"fix4 EN restore+ko nt 回读: {json.dumps(fix4_final['totals'], ensure_ascii=False)}")
        print(f"私服 IP 命中: total={final['private_ip_hits']['total']} "
              f"per={json.dumps(final['private_ip_hits']['per_entry'], ensure_ascii=False)}")
        print(f"产物: {final['bytes']:,}B sha256={final['sha256']}")

        evidence = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "mode": mode,
            "client": "EN 3.7.1 (com.square_enix.android_googleplay.nierspww)",
            "apk_input": {
                "path": str(apk), "bytes": apk.stat().st_size, "sha256": sha256_file(apk),
                "untouched_hashes": original_hashes,
            },
            "font_payload": {"dir": str(payload_dir), "files": payload, "inject": font_results},
            "server_addresses": {"grpc": args.grpc, "http": args.http, "auth": args.auth}
            if mode == "patched" else None,
            "workspace": str(work),
            "menu_apk": str(menu_apk),
            "workdir_checks": work_checks,
            "private_patch_log_tail": patch_tail,
            "auth_dynamic_log_tail": authdyn_tail,
            "fix3_en": {
                "tool": str(FIX3_EN),
                "python": str(fix3_py),
                "report_path": str(fix3_report_path),
                "apply_report": fix3_report,
                "workdir_checks": fix3_checks,
                "final_apk_readback": fix4_final,
                "log_tail": fix3_tail,
            },
            "fix3_ko": {
                "tool": str(FIX3_KO),
                "python": str(fix3_py),
                "report_path": str(fix3_ko_report_path),
                "apply_report": fix3_ko_report,
                "workdir_checks": fix3_checks,
                "final_apk_readback": fix4_final,
                "log_tail": fix3_ko_tail,
                "length_rule": "T01 机制 len(new utf-8)<=len(old utf-8)；KO_OVERRIDE 短译 2 条（联系/去推特）",
            },
            "fix3l": {
                "tool": str(FIX3L),
                "python": str(fix3_py),
                "report_path": str(fix3l_report_path),
                "apply_report": fix3l_report,
                "log_tail": fix3l_tail,
                "keys_count": len(fix3l_report.get("keys", {})),
                "length_rule": "EN 段无约束；ko 段 len(new)<=len(old)；超长短译已记录",
            },
            "fix4": {
                "tool": str(FIX4),
                "python": str(fix3_py),
                "report_path": str(fix4_report_path),
                "apply_report": fix4_report,
                "log_tail": fix4_tail,
                "en_restore_keys": 81,
                "ko_nt_translate_keys": 67,
                "length_rule": "ko 段 len(new)<=len(old)；超长 SKIP_TOO_LONG",
            },
            "output": {
                "path": str(out),
                **final,
                "fix4_final_readback": fix4_final,
                "signature": verify,
                "zipalign": align,
            },
            "expected_cert_sha256": EXPECTED_CERT_SHA256,
            "signing_note": "en-client debug.keystore（alias androiddebugkey / pass android）签名；覆盖官方 EN 安装会因签名不符失败，玩家需卸载官方后安装。",
        }
        evidence_path = log_dir / f"{stamp}-evidence-en-{mode}.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"evidence: {evidence_path}")

        after = sha256_file(apk)
        print(f"输入 APK 未修改: {after == evidence['apk_input']['sha256']}")
        if after != evidence["apk_input"]["sha256"]:
            raise SystemExit("输入 APK 被修改！")

        # ---- 验证门证书指纹断言（L3a：EN=7D:79:2C…A4:A1:73）----
        cert_expect = key_info["cert_sha256"]
        cert_ok = verify["cert_sha256"] == cert_expect
        print(f"验证门证书断言: {verify['cert_sha256']} == {cert_expect} -> "
              f"{'PASS' if cert_ok else 'FAIL'}")
        if not cert_ok:
            raise SystemExit(f"验证门证书指纹比对失败: {verify['cert_sha256']} != {cert_expect}")

        gates_ok = bool(
            verify["verified_v2"] and verify["cert_matches_expected"] and align["ok"]
            and final["zip_ok"]
            and all(v.get("matches_payload") and v.get("fontdata_matches_payload")
                    for v in final["font_files"].values())
            and fix4_final["ok"] and cert_ok)
        if not gates_ok:
            raise SystemExit("产物验证未全部通过")

        # ---- manifest sidecar（L3a 契约：<产物名>.manifest.json）----
        t4 = fix4_final.get("totals", {})
        verify_gates = {
            "ok": gates_ok,
            "gates": {
                "1_signature_v2v3": bool(verify["verified_v2"] and verify["verified_v3"]),
                "1_cert_assertion": cert_ok,
                "2_fonts": all(v.get("matches_payload") and v.get("fontdata_matches_payload")
                               for v in final["font_files"].values()),
                "3_private_ip": (final.get("private_ip_hits", {}).get("total") or 0) > 0,
                "4_fix4_readback": bool(fix4_final.get("ok")),
                "4b_fix3_workdir_checks": bool(fix3_checks.get("ok")),
                "5_original_untouched": after == evidence["apk_input"]["sha256"],
                "6_package_zipalign": bool(final["zip_ok"] and align["ok"]),
            },
            "fix4_totals": t4,
            "report": str(evidence_path),
        }
        patch_counts = {
            "mode": mode,
            "fix3_en_keys": len(fix3_report.get("keys", {})),
            "fix3_en_metadata_repl": len(fix3_report.get("meta_repl", {})),
            "fix3_ko_keys": len(fix3_ko_report.get("keys", {})),
            "fix3l_keys": len(fix3l_report.get("keys", {})),
            "fix4_en_restore_keys": t4.get("en_keys"),
            "fix4_ko_nt_keys": t4.get("ko_nt_keys"),
            "metadata_zh_hits": t4.get("meta_zh_hits"),
            "private_ip_total_hits": final.get("private_ip_hits", {}).get("total"),
            "fonts_payload_files": len(payload),
            "menu_smali_files": len(work_checks.get("menu", {}).get("main_smali", [])),
            "menu_start_call_sites": len(work_checks.get("start_call", [])),
            "workdir_ok": work_checks.get("ok"),
        }
        sidecar = manifest_sidecar.build_sidecar(
            out, region_info=client, input_apk=apk, cert_sha256=verify["cert_sha256"],
            patch_counts=patch_counts, verify_gates=verify_gates,
            verify_report=evidence_path, build_started_at=build_started_at,
            extra={"pipeline": "en-client/build_en_zh.py", "mode": mode,
                   "signing_note": "nier-en.keystore（=debug.keystore 收编；alias androiddebugkey"
                                   " / pass android）签名；覆盖官方 EN 安装需先卸载。",
                   "server_addresses": {"grpc": args.grpc, "http": args.http, "auth": args.auth}
                   if mode == "patched" else None})
        sidecar_path = manifest_sidecar.write_sidecar(out, sidecar)
        sc_check = manifest_sidecar.verify_sidecar(sidecar_path, out)
        print(f"manifest sidecar: {sidecar_path}"
              f"（自检 {'ok' if sc_check['ok'] else sc_check['problems']}）")
        if not sc_check["ok"]:
            raise SystemExit("manifest sidecar 自检失败: " + json.dumps(sc_check["problems"]))
        # ---- L6 统一验证门（末步）：适用项 A1-A9 全量复核（MANIFEST 预检 /
        # 证书断言 / RVA 表版本位 / 字体 payload 四条目 / fix3 串 / region 匹配 /
        # RVA 表按客户端选对）。断言定义 shared/gate_defs.py、执行器
        # shared/verify_gate.py；与 bunker 侧 verify_gate_zh.py 同 schema
        # （nier-verify-gate/v1）。失败 fail-fast。
        import verify_gate as VG
        l6 = VG.run_gate(apk=out, bin_e=None, client="en",
                         sidecar=sidecar_path, manifest_dir=EN_LOCAL,
                         font_mode="zh", fix3_mode="required",
                         require_zh_text=True, gate_name="en-build-final")
        for line in l6.render_lines():
            print(line)
        l6_path = l6.write_json(out.parent / (out.stem + ".gate.json"))
        print(f"L6 统一验证门报告: {l6_path}")
        if not l6.ok:
            raise SystemExit("L6 统一验证门未通过（末步，fail-fast）")
        sidecar["l6_gate"] = l6.to_dict()
        print("=== BUILD OK ===")
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        log_file.close()


if __name__ == "__main__":
    main()
