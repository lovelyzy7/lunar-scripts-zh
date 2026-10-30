#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_android_lunar_zh.py — 生成 `android_lunar_zh.ipynb`（Colab 成对构建笔记本）。

改编基线（实测逐 cell 对齐）：
  * 原版 lunar-scripts `android/lunar_tear_patcher.ipynb`（gitlab walter-sparrow-group/lunar-scripts）
    —— 操作流程骨架：Configuration → Install dependencies → Patch APK → Patch Master Data；
  * lunar-scripts-jp `colab/lunar-scripts-jp.ipynb` —— 加固点：_run 子进程流式日志/失败即停、
    Save to Google Drive、fail-fast 依赖检查、nier-jp keystore 统一签名。

改编点（输出带汉化、成对两文件）：
  * APK 侧 = 私服补丁 + fix3 内置串 + 字体 payload + mod 菜单（jp-client 一件套）；
  * bin.e 侧 = 汉化 masterdata（文本格=汉化基逐字节）+ 可选编辑项（原版编辑面）；
  * 依赖装载：原版 notebook 用 git clone 拉脚本 → 本 notebook 用 **Drive 的
    jp-client-payload.zip**（脚本/表/字体/modmenu/keystore 全量）；大件（字体 28MB /
    modmenu 1.5MB）不进 notebook（base64 会把 notebook 膨胀到 40MB+），路径参数化 + 一键打包
    脚本 `make_payload_zip.ps1`，用法写在 cell 0。

生成：python gen_android_lunar_zh.py   （输出与本脚本同目录的 android_lunar_zh.ipynb）
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "android_lunar_zh.ipynb"

CELL_MD_INTRO = """\
# Lunar Tear Patcher (JP + 简体中文汉化) — 成对构建 APK + bin.e

把 NieR Re\\[in\\]carnation **JP** 客户端 APK 与 master data（bin.e）补丁成
**私服 + 汉化**的目标件：一次跑完得到 **两个目标文件**（目标 APK + 配套汉化 bin.e）。

**操作流程（与原版 android_lunar 系列一致，未改变）：**
1. 把本 ipynb 上传到 [Google Colab](https://colab.research.google.com/)；
2. **配置**：填原 APK、bin.e（masterdata）在 Google Drive 的路径（以及补丁包 zip 路径）；
3. **填写局域网 IP**（grpc / http / auth，默认 `192.168.2.6`）；
4. 从上到下运行各 cell（或 **Runtime → Run all**）；
5. 最后产出 **两个目标文件**：`nier-jp.apk`（目标 APK，L3a 产物命名契约：JP 客户端→nier-jp.apk）+ 配套汉化 bin.e（**文件名前后不变**：
   输入 bin.e 叫什么，产出就叫什么，如 `20240404193219.bin.e`），自动存回 Google Drive / 浏览器下载。

**补丁包（payload）装载方案**：脚本/表/字体/modmenu/keystore 全部从 Drive 的
`jp-client-payload.zip` 装载（对应原版 notebook 的 `git clone` 依赖装载；28MB 字体与
modmenu 大件**不进 notebook**——base64 内嵌会把 notebook 膨胀到 40MB+ 且上传慢）。
在本机 `jp-client/` 目录一键打包：

```powershell
pwsh -File jp-client\\colab\\make_payload_zip.ps1 -OutZip <本机输出>\\jp-client-payload.zip
# 上传 jp-client-payload.zip 到 Google Drive，Configuration 里填它的 Drive 路径
```

**各项内容**：
| 输出 | 内容 |
|---|---|
| 目标 APK | 私服补丁（局域网 IP）+ fix3 内置串汉化 + 四字体容器 + mod 菜单，nier-jp key 签名 |
| 配套 bin.e | 汉化 masterdata（文本格=汉化基逐字节）+ 可选编辑项（对齐原版 lunar-scripts 编辑面：时间戳延长/清维护/迷宫解锁/迷宫赛季窗口/黑鸟去重），结构 AES/TOC/5 表/LZ4 全过、与原版 diff 只在预期表 |

> 各 section 相互独立：只补 APK 就跳过 bin.e cell，反之亦然。
"""

CELL_CODE_CONFIG = r'''#@title Configuration

#@markdown ### Source Mode
use_gdrive = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### File Sources（Google Drive 路径，相对于 /content/drive/；URL 模式填下载链接）
apk_source = "MyDrive/NieR Re[in]carnation_3.7.1_JP.apk" #@param {type:"string"}
masterdata_source = "MyDrive/bin_zh_fix6.bin.e" #@param {type:"string"}
#@markdown 补丁包 zip（脚本/表/字体/modmenu/keystore；用 jp-client/colab/make_payload_zip.ps1 生成）
payload_zip = "MyDrive/jp-client-payload.zip" #@param {type:"string"}
#@markdown 可选：原版 bin.e（20240404193219.bin.e，断言 C「与原版 diff 只在预期表」的参照；留空跳过）
orig_bin_e_source = "MyDrive/20240404193219.bin.e" #@param {type:"string"}

#@markdown ---
#@markdown ### bin.e 可选编辑项（逐项对应原版 lunar-scripts patch_masterdata.py 编辑面）
edit_extend_end_dates = True #@param {type:"boolean"}
edit_empty_maintenance = True #@param {type:"boolean"}
edit_add_labyrinth_unlock = True #@param {type:"boolean"}
edit_window_labyrinth_seasons = True #@param {type:"boolean"}
edit_dedup_gimmick_schedules = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### Server Settings（局域网 IP，例如 192.168.2.6）
grpc_addr = "192.168.2.6:8003" #@param {type:"string"}
http_addr = "192.168.2.6:8080" #@param {type:"string"}
auth_host = "192.168.2.6:3000" #@param {type:"string"}

#@markdown ---
#@markdown ### Outputs（Google Drive 落盘路径；留空则只在 /content 并浏览器下载）
#@markdown 配套 bin.e **文件名前后不变**：此路径只可改目录，文件名会被自动纠正为输入同名。
output_apk_drive_path = "MyDrive/nier-jp.apk" #@param {type:"string"}
output_bin_drive_path = "MyDrive/20240404193219.bin.e" #@param {type:"string"}

import json
import os
import shutil

IN_COLAB = os.path.isdir("/content")
WORK = "/content" if IN_COLAB else os.path.join(os.path.dirname(os.path.abspath("__file__")), "_colab_work")
os.makedirs(WORK, exist_ok=True)
JP_ROOT = os.path.join(WORK, "jp-client")


def drive_path(src):
    """Drive 相对路径 → 绝对路径；URL 原样返回（由下载步骤处理）。"""
    if not src:
        return ""
    if src.startswith(("http://", "https://")):
        return src
    return os.path.join("/content/drive", src)


def load_config():
    """收集所有 Configuration 参数为 dict（notebook 关键函数之一，本地可测）。"""
    edits = {
        "extend_end_dates": bool(edit_extend_end_dates),
        "empty_maintenance": bool(edit_empty_maintenance),
        "add_labyrinth_unlock": bool(edit_add_labyrinth_unlock),
        "window_labyrinth_seasons": bool(edit_window_labyrinth_seasons),
        "dedup_gimmick_schedules": bool(edit_dedup_gimmick_schedules),
    }
    cfg = {
        "use_gdrive": bool(use_gdrive),
        "apk_source": apk_source,
        "masterdata_source": masterdata_source,
        "payload_zip": payload_zip,
        "orig_bin_e_source": orig_bin_e_source,
        "edits": edits,
        "grpc_addr": grpc_addr,
        "http_addr": http_addr,
        "auth_host": auth_host,
        "out_apk_drive": output_apk_drive_path,
        "out_bin_drive": output_bin_drive_path,
        "work": WORK,
        "jp_root": JP_ROOT,
        "in_colab": IN_COLAB,
    }
    return cfg


def check_config(cfg):
    """配置预检：路径/必填项检查（fail-fast，notebook 关键函数之一）。"""
    problems = []
    if not cfg["apk_source"]:
        problems.append("apk_source 未设置")
    if not cfg["masterdata_source"]:
        problems.append("masterdata_source 未设置")
    if not cfg["payload_zip"]:
        problems.append("payload_zip 未设置（补丁包 zip，见 cell 0 说明）")
    for key, label in (("grpc_addr", "gRPC"), ("http_addr", "HTTP")):
        if not cfg[key]:
            problems.append(f"{label} 地址未设置（填写局域网 IP，例如 192.168.2.6:8003）")
    if cfg["use_gdrive"]:
        if not IN_COLAB:
            problems.append("use_gdrive=True 但不在 Colab 环境（本地测试请置 use_gdrive=False 或用 fixtures）")
        elif not os.path.isdir("/content/drive"):
            problems.append("Google Drive 未挂载（先运行下方挂载逻辑）")
    if problems:
        raise RuntimeError("配置检查未过：\n  - " + "\n  - ".join(problems))
    return True


if use_gdrive and IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    print("Google Drive mounted at /content/drive\n")
    for label, src in [("APK", apk_source), ("Master data (bin.e)", masterdata_source),
                       ("Payload zip", payload_zip), ("Orig bin.e (optional)", orig_bin_e_source)]:
        if not src:
            print(f"  {label}: (not set)")
            continue
        path = drive_path(src)
        if os.path.isfile(path):
            print(f"  {label}: {path} -> OK ({os.path.getsize(path) / 1048576:.1f} MB)")
        else:
            print(f"  {label}: {path} -> NOT FOUND")
else:
    print("URL/本地模式：文件将在补丁步骤按需获取。")

print("Configuration ready.")
if IN_COLAB:
    cfg = load_config()
    check_config(cfg)
'''

CELL_CODE_INSTALL = r'''#@title Install dependencies
import os
import shutil
import subprocess
import sys


def _run(cmd, label):
    """流式子进程（Jupyter 下 stdout 不直达 cell；失败即停）——原版 lunar-scripts-jp 同款。"""
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    p = subprocess.Popen(cmd, shell=isinstance(cmd, str), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", bufsize=1, env=env)
    for line in p.stdout:
        print(line, end="", flush=True)
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"{label} failed (exit code {p.returncode}) -> see the output above.")


def install_dependencies(online=True):
    """Colab 构建依赖：pycryptodome/msgpack/lz4/UnityPy + apktool + zipalign + apksigner。"""
    if online:
        _run(f"{sys.executable} -m pip install -q pycryptodome msgpack lz4 UnityPy", "pip install")
        _run("apt-get -qq update", "apt-get update")
        if not shutil.which("apktool"):
            _run("wget -q -O /usr/local/bin/apktool.jar "
                 "https://github.com/iBotPeaches/Apktool/releases/download/v2.11.1/apktool_2.11.1.jar",
                 "wget apktool.jar")
            _run("wget -q -O /usr/local/bin/apktool "
                 "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool",
                 "wget apktool")
            _run("chmod +x /usr/local/bin/apktool", "chmod apktool")
        if not shutil.which("zipalign") or not shutil.which("apksigner"):
            _run("apt-get -qq install -y zipalign apksigner", "apt-get install zipalign apksigner")
    tools = {}
    for tool in ("apktool", "zipalign", "apksigner", "keytool"):
        tools[tool] = shutil.which(tool) or "NOT FOUND"
        print(f"  {tool}: {tools[tool]}")
    missing = [k for k, v in tools.items() if v == "NOT FOUND"]
    if missing:
        raise RuntimeError("工具缺失: " + ", ".join(missing))
    return tools


if IN_COLAB:
    COLAB_TOOLS = install_dependencies(online=True)
else:
    print("本地环境：跳过在线安装（测试 harness 会提供工具路径）。")
    COLAB_TOOLS = None
'''

CELL_CODE_PAYLOAD = r'''#@title Load patch payload（补丁包装载：Drive zip -> /content/jp-client）
import os
import shutil
import sys
import zipfile

_REQUIRED = [
    "build_jp_client.py",
    "build_bin_e.py",
    "bin-edit.default.json",
    "patches/patch_apk_jp.py",
    "fix3/patch_fix3.py",
    "fix3/builtin_strings.json",
    "fix3/builtin_strings.tsv",
    "keys/nier-jp.keystore",
    "fonts/payload/assets/bin/Data/6f937efa0660c47f59d5215d276b1cbb",
    "fonts/payload/assets/bin/Data/7089ac60979c94824ac549baab08cfa7",
    "fonts/payload/assets/bin/Data/ad1489eb70ff840d19d7d0841bcdd3a9",
    "fonts/payload/assets/bin/Data/550e0743a6b6344cfa3380b9a07f58b6",
    "modmenu-payload/lib/arm64-v8a/libniermenu.so",
    # L3a 共享模块（zip 根 shared/，与 jp-client/ 同级；build_jp_client.py 从 ../shared 引用）
    "../shared/detect_client.py",
    "../shared/manifest_sidecar.py",
]


def load_payload(cfg):
    """解压 Drive 的 jp-client-payload.zip 到 <work>/jp-client 并 fail-fast 校验清单。"""
    root = cfg["jp_root"]
    src = cfg["payload_zip"]
    if cfg["use_gdrive"] and not src.startswith(("http://", "https://")):
        src = drive_path(src)
    if not os.path.isfile(src) and os.path.isfile(cfg["payload_zip"]):
        src = cfg["payload_zip"]
    if not os.path.isfile(src):
        raise RuntimeError("补丁包 zip 未找到: " + str(src) +
                           "（用 jp-client/colab/make_payload_zip.ps1 生成后上传 Drive）")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root, exist_ok=True)
    with zipfile.ZipFile(src) as zf:
        zf.extractall(root)
    # 兼容 zip 根多一层 jp-client/ 的情况
    if not os.path.isfile(os.path.join(root, "build_jp_client.py")) and \
            os.path.isfile(os.path.join(root, "jp-client", "build_jp_client.py")):
        root = os.path.join(root, "jp-client")
        cfg["jp_root"] = root
    missing = [f for f in _REQUIRED if not os.path.isfile(os.path.join(root, f))]
    if missing:
        raise RuntimeError("补丁包不完整，缺少: " + ", ".join(missing) +
                           "（重新打包 jp-client-payload.zip 后再跑）")
    sys.path.insert(0, root)
    print(f"payload loaded: {root} ({len(_REQUIRED)}/{len(_REQUIRED)} required files ok)")
    return root


if IN_COLAB:
    PAYLOAD_ROOT = load_payload(cfg)
'''

CELL_CODE_PATCH_APK = r'''#@title Patch APK（私服补丁 + fix3 + 字体 + mod 菜单 -> 目标 APK）
import importlib.util
import os
import shutil
import subprocess
import sys
import urllib.request


def _run(cmd, label, cwd=None):
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    p = subprocess.Popen(cmd, shell=isinstance(cmd, str), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", bufsize=1, env=env, cwd=cwd)
    for line in p.stdout:
        print(line, end="", flush=True)
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"{label} failed (exit code {p.returncode}) -> see the output above.")


def _cmd(parts):
    """拼 shell 命令：嵌套列表拍平（工具前缀如 [java, -jar, xx.jar]）、含空格/方括号的参数加引号。"""
    flat = []

    def _walk(x):
        if isinstance(x, (list, tuple)):
            for y in x:
                _walk(y)
        else:
            flat.append(x)

    _walk(parts)
    return " ".join(f'"{p}"' if (" " in str(p) or "[" in str(p)) else str(p) for p in flat)


def _fetch_source(src, dst, label, use_gdrive):
    """三态取源：http(s) 下载 / Drive 相对路径 / 本地绝对路径（本地 fixtures 可测）。"""
    if src.startswith(("http://", "https://")):
        print(f"Downloading {label} from {src} ...")
        urllib.request.urlretrieve(src, dst)
        print(f"  Downloaded {os.path.getsize(dst) / 1048576:.1f} MB")
        return
    path = drive_path(src) if use_gdrive else src
    if not os.path.isfile(path) and os.path.isfile(src):
        path = src
    if not os.path.isfile(path):
        raise RuntimeError(f"{label} not found: {path}")
    shutil.copy2(path, dst)
    print(f"{label} copied from {path} ({os.path.getsize(dst) / 1048576:.1f} MB)")


def patch_apk_flow(cfg, tools=None):
    """APK 侧全流程：解包 -> 私服补丁 -> fix3 -> 字体 -> mod 菜单 -> 重建/对齐/签名。

    tools: 命令前缀 dict（apktool/zipalign/apksigner/python）；缺省按 PATH 探测（Colab）。
    返回目标 APK 路径。
    """
    root = cfg["jp_root"]
    work = os.path.join(cfg["work"], "apk-work")
    out_apk = os.path.join(cfg["work"], "nier-jp.apk")
    tools = tools or {
        "apktool": "apktool",
        "zipalign": "zipalign",
        "apksigner": "apksigner",
        "python": sys.executable,
    }

    assert os.path.isfile(os.path.join(root, "patches", "patch_apk_jp.py")), \
        "Patch scripts not found - run the 'Load patch payload' cell first."
    assert cfg["apk_source"], "Set apk_source in the Configuration cell first."
    assert cfg["grpc_addr"] and cfg["http_addr"], "Fill the LAN IP (grpc_addr/http_addr) first."

    orig_apk = os.path.join(cfg["work"], "original.apk")
    _fetch_source(cfg["apk_source"], orig_apk, "APK", cfg["use_gdrive"])

    print("\nDecompiling ...")
    _run(_cmd([tools["apktool"], "d", orig_apk, "-o", work, "-f"]), "apktool decompile")

    print("\n[1/4] Private-server patch ...")
    patch_args = [tools["python"], os.path.join(root, "patches", "patch_apk_jp.py"), work,
                  "--grpc-addr", cfg["grpc_addr"], "--http-addr", cfg["http_addr"]]
    if cfg.get("auth_host"):
        patch_args += ["--auth-host", cfg["auth_host"]]
    _run(_cmd(patch_args), "patch_apk_jp")

    print("\n[2/4] fix3 builtin strings ...")
    fix3 = os.path.join(root, "fix3")
    _run(_cmd([tools["python"], os.path.join(fix3, "patch_fix3.py"), "apply",
               "--work", work, "--tier", "all"]), "patch_fix3", cwd=fix3)

    print("\n[3/4] Fonts payload ...")
    spec = importlib.util.spec_from_file_location(
        "bjc", os.path.join(root, "build_jp_client.py"))
    bjc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bjc)
    work_p = bjc.Path(work)  # build_jp_client 的 inject_* 接收 pathlib.Path
    bjc.inject_fonts(work_p, bjc.Path(os.path.join(root, "fonts", "payload", "assets", "bin", "Data")))

    print("\n[4/4] Mod menu ...")
    bjc.MENU_PAYLOAD = bjc.Path(os.path.join(root, "modmenu-payload"))
    bjc.inject_menu(work_p)
    bjc.inject_manifest(work_p)
    bjc.inject_start_call(work_p)

    print("\nRebuilding ...")
    unaligned = os.path.join(cfg["work"], "target-unaligned.apk")
    _run(_cmd([tools["apktool"], "b", work, "-o", unaligned]), "apktool rebuild")
    print("\nAligning ...")
    _run(_cmd([tools["zipalign"], "-p", "-f", "4", unaligned, out_apk]), "zipalign")

    keystore = os.path.join(root, "keys", "nier-jp.keystore")
    if not os.path.isfile(keystore):
        raise RuntimeError("Keystore not found: " + keystore + " (ships in the payload zip)")
    print("\nSigning (nier-jp key) ...")
    _run(_cmd([tools["apksigner"], "sign", "--ks", keystore, "--ks-pass", "pass:lunar-jp",
               "--ks-key-alias", "nier", "--key-pass", "pass:lunar-jp", out_apk]), "apksigner")

    size_mb = os.path.getsize(out_apk) / 1048576
    print(f"\nDone! Patched APK: {out_apk} ({size_mb:.1f} MB)")
    return out_apk


if IN_COLAB:
    APK_OUT = patch_apk_flow(cfg)
'''

CELL_CODE_PATCH_BIN = r'''#@title Patch Master Data（bin.e：汉化 masterdata + 可选编辑项 -> 配套 bin.e）
import importlib.util
import json
import os
import sys
import urllib.request


def patch_bin_e_flow(cfg):
    """bin.e 侧全流程：汉化基内容（文本格逐字节）+ 可选编辑项 + 三重断言。

    返回 (输出路径, 报告 dict)。断言不过即抛异常（不落盘）。
    """
    root = cfg["jp_root"]
    spec = importlib.util.spec_from_file_location(
        "bbe", os.path.join(root, "build_bin_e.py"))
    bbe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bbe)

    src = cfg["masterdata_source"]
    # 硬性要求：bin.e 文件名前后不变——输出名取输入配置路径的 basename
    bin_name = os.path.basename(cfg["masterdata_source"].rstrip("/")) or "20240404193219.bin.e"
    if src.startswith(("http://", "https://")):
        src = os.path.join(cfg["work"], "masterdata.bin.e")
        urllib.request.urlretrieve(cfg["masterdata_source"], src)
    else:
        path = drive_path(src) if cfg["use_gdrive"] else src
        if not os.path.isfile(path) and os.path.isfile(cfg["masterdata_source"]):
            path = cfg["masterdata_source"]
        src = path
    if not os.path.isfile(src):
        raise RuntimeError("Master data (bin.e) not found: " + str(src))
    out_bin = os.path.join(cfg["work"], bin_name)
    edit_cfg = os.path.join(cfg["work"], "bin-edit.json")
    with open(edit_cfg, "w", encoding="utf-8") as fh:
        json.dump({"notes": "generated by android_lunar_zh.ipynb", "edits": cfg["edits"]},
                  fh, ensure_ascii=False, indent=2)

    orig = cfg.get("orig_bin_e_source") or ""
    if orig and not orig.startswith(("http://", "https://")):
        orig_path = drive_path(orig) if cfg["use_gdrive"] else orig
        if not os.path.isfile(orig_path) and os.path.isfile(orig):
            orig_path = orig
        orig = orig_path
    orig = orig if orig and os.path.isfile(orig) else None

    report = bbe.build_bin_e(
        bin_e=src,
        out_bin_e=out_bin,
        bin_edit=edit_cfg,
        text_from=None,
        zh_base=src,
        orig_bin_e=orig,
        report_path=os.path.join(cfg["work"], "bin-e-report.json"),
    )
    size_kb = os.path.getsize(out_bin) / 1024
    print(f"\nDone! Paired master data: {out_bin} ({size_kb:.1f} KB)")
    return out_bin, report


if IN_COLAB:
    BIN_OUT, BIN_REPORT = patch_bin_e_flow(cfg)
'''

CELL_CODE_SAVE = r'''#@title Save to Google Drive（产出两个目标文件）
import os
import shutil


def save_to_drive(src, dst, label, use_gdrive):
    if not dst:
        print(f"{label}: skipped (path not set)")
        return
    if not os.path.exists(src):
        print(f"{label}: not found at {src} - ensure the previous cell ran successfully.")
        return
    if use_gdrive:
        destination_path = drive_path(dst)
        destination_dir = os.path.dirname(destination_path)
        if destination_dir and not os.path.exists(destination_dir):
            print(f"Creating directory: {destination_dir}")
            os.makedirs(destination_dir)
        try:
            shutil.copy2(src, destination_path)
            size_mb = os.path.getsize(destination_path) / 1048576
            print(f"{label}: saved to Google Drive: {destination_path} ({size_mb:.1f} MB)")
        except Exception as e:  # noqa: BLE001
            print(f"{label}: error copying file to Google Drive: {e}")
    else:
        print(f"{label}: local mode -> left at {src}")


def save_outputs(cfg, apk_path=None, bin_path=None):
    """两个目标文件落盘：目标 APK + 配套 bin.e（Drive 优先；Colab 同时浏览器下载）。

    硬性要求：bin.e 文件名前后不变——Drive 输出路径只可改目录，文件名自动纠正为输入同名。
    """
    bin_name = os.path.basename(cfg["masterdata_source"].rstrip("/")) or "20240404193219.bin.e"
    apk_path = apk_path or os.path.join(cfg["work"], "nier-jp.apk")
    bin_path = bin_path or os.path.join(cfg["work"], bin_name)
    out_bin_drive = cfg.get("out_bin_drive") or ""
    if out_bin_drive:
        drv_dir = os.path.dirname(out_bin_drive)
        fixed = (drv_dir + "/" if drv_dir else "") + bin_name
        if os.path.basename(out_bin_drive.rstrip("/")) != bin_name:
            print(f"bin.e 文件名前后不变：Drive 输出名已纠正 "
                  f"{os.path.basename(out_bin_drive.rstrip('/'))!r} -> {bin_name!r}")
            out_bin_drive = fixed
    save_to_drive(apk_path, cfg["out_apk_drive"], "Target APK", cfg["use_gdrive"])
    save_to_drive(bin_path, out_bin_drive, "Paired bin.e", cfg["use_gdrive"])
    if cfg["in_colab"]:
        try:
            from google.colab import files
            for p in (apk_path, bin_path):
                if os.path.isfile(p):
                    files.download(p)
        except Exception as e:  # noqa: BLE001
            print("browser download skipped:", e)
    return apk_path, bin_path


print("Save functions ready - run after the two patch cells.")
if IN_COLAB:
    save_outputs(cfg)
'''


def build_notebook() -> dict:
    cells = [
        {"cell_type": "markdown", "metadata": {}, "id": "md-intro", "source": CELL_MD_INTRO},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "cfg-config",
         "outputs": [], "source": CELL_CODE_CONFIG},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "cfg-deps",
         "outputs": [], "source": CELL_CODE_INSTALL},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "cfg-payload",
         "outputs": [], "source": CELL_CODE_PAYLOAD},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "patch-apk",
         "outputs": [], "source": CELL_CODE_PATCH_APK},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "patch-bine",
         "outputs": [], "source": CELL_CODE_PATCH_BIN},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "id": "save-outputs",
         "outputs": [], "source": CELL_CODE_SAVE},
    ]
    # Jupyter source 存储为逐行列表（含换行），便于 diff 工具阅读
    for c in cells:
        src = c["source"]
        lines = src.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            pass  # 最后一行可不带换行（nbformat 允许）
        c["source"] = lines

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "colab": {"provenance": [], "name": "android_lunar_zh.ipynb"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    return nb


def main():
    nb = build_notebook()
    try:
        import sys
        sys.path.insert(0, r"E:\NieRReincarnation\tmp_u_heuristics\pypkgs")
        import nbformat
        nbformat.validate(nbformat.from_dict(nb))
        print("nbformat validate: OK (pre-write)")
    except ImportError:
        print("nbformat 不可用（仅影响写前校验；写后用 test_colab_functions.py 的 T0 校验）")
    OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} cells={len(nb['cells'])} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
