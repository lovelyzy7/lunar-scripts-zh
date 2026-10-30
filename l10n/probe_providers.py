#!/usr/bin/env python3
"""探测各翻译服务商密钥是否可用（最小字符量）。

支持 azure（多端点/多密钥矩阵）与 youdao。每次运行消耗少量额度（约 40 字符/组合）。

用法:
    python probe_providers.py                # 测全部
    python probe_providers.py azure_f0       # 只测某一家
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "providers.json"

TEST_TEXT = "The quick brown fox jumps over the lazy dog."


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def post(url: str, data: bytes, headers: dict, timeout: int = 40):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw, time.time() - t0
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return exc.code, raw, time.time() - t0


def azure_case(endpoint: str, key: str, region: str) -> dict:
    url = f"{endpoint.rstrip('/')}/translate?api-version=3.0&from=en&to=zh-Hans"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": key,
    }
    if region:
        headers["Ocp-Apim-Subscription-Region"] = region
    status, raw, elapsed = post(url, json.dumps([{"Text": TEST_TEXT}]).encode(), headers)
    translated = None
    try:
        parsed = json.loads(raw)
        translated = parsed[0]["translations"][0]["text"]
    except Exception:  # noqa: BLE001
        pass
    return {
        "endpoint": url,
        "status": status,
        "elapsed": round(elapsed, 2),
        "translated": translated,
        "error": raw[:400] if status != 200 else None,
    }


def youdao_case(cfg: dict, q: str = TEST_TEXT, to: str = "zh-CHS", secret_field: str = "app_secret") -> dict:
    url = "https://openapi.youdao.com/api"
    app_key = cfg["app_key"]
    app_secret = cfg[secret_field]
    salt = str(random.randint(10000, 99999))
    curtime = str(int(time.time()))
    input_q = q if len(q) <= 20 else q[:10] + str(len(q)) + q[-10:]
    sign = hashlib.sha256((app_key + input_q + salt + curtime + app_secret).encode()).hexdigest()
    body = urllib.parse.urlencode(
        {
            "q": q,
            "from": "en",
            "to": to,
            "appKey": app_key,
            "salt": salt,
            "sign": sign,
            "signType": "v3",
            "curtime": curtime,
        }
    ).encode()
    status, raw, elapsed = post(url, body, {"Content-Type": "application/x-www-form-urlencoded"})
    translated = None
    try:
        parsed = json.loads(raw)
        translated = parsed.get("translation")
    except Exception:  # noqa: BLE001
        parsed = None
    return {
        "secret_field": secret_field,
        "status": status,
        "elapsed": round(elapsed, 2),
        "translated": translated,
        "error": raw[:400] if status != 200 else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="只测指定 provider 名")
    args = ap.parse_args()

    cfg = load_config()
    providers = cfg.get("providers", {})
    failures = 0
    for name, pcfg in providers.items():
        if args.names and name not in args.names:
            continue
        print(f"\n### {name} ({pcfg.get('kind')})")
        kind = pcfg.get("kind")
        if kind == "azure":
            seen = set()
            for endpoint in pcfg.get("endpoints", []):
                for key in pcfg.get("keys", []):
                    tag = f"{endpoint} | key ...{key[-6:]}"
                    if tag in seen:
                        continue
                    seen.add(tag)
                    res = azure_case(endpoint, key, pcfg.get("region", ""))
                    print(json.dumps({"target": tag, **res}, ensure_ascii=False))
                    if res["status"] != 200:
                        failures += 1
        elif kind == "youdao":
            for secret_field in ("app_secret", "api_key"):
                if not pcfg.get(secret_field):
                    continue
                res = youdao_case(pcfg, secret_field=secret_field)
                print(json.dumps({"target": f"youdao:{secret_field}", **res}, ensure_ascii=False))
                if res["status"] != 200:
                    failures += 1
        else:
            print(f"unknown kind: {kind}")
            failures += 1

    print(f"\nSUMMARY: {'ALL OK' if failures == 0 else str(failures) + ' FAILED CASES'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
