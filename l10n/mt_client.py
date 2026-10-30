#!/usr/bin/env python3
"""NieR Re[in]carnation 汉化 —— 可复用机器翻译客户端（Python 3 标准库，无第三方依赖）。

封装三家服务商，供批量汉化流水线调用：
  * azure_s0 : Azure Translator 标准付费层（translator-for-nier / japaneast）
  * youdao   : 有道智云文本翻译
  * azure_f0 : Azure Translator 免费层（free-f0 / global，兜底）

核心能力
--------
1. 统一接口  translate(texts, src, dst) -> list[str]（import 或 CLI）；
2. 占位符保护：.NET 占位（{0}/{0:N0}/{name}）、尖括号标签（<color=...> 等）、
   字面 \\n/\\t/\\r、自定义 [[P0]]、真实换行。还原后逐个校验，数量不符→单条重试→未翻译并记录；
3. 去重（同批相同原文只翻一次）+ 本地 JSON 缓存 + 断点续跑（重跑同命令自动跳过已完成）；
4. 重试（429/5xx/超时/网络异常，指数退避 + 尊重 Retry-After）、provider 依次降级、
   单条失败不中断；
5. 速率控制（串行；可选并发 1~2）、用量统计（请求数/字符数/缓存命中/失败/费用估算）；
6. 付费保护：默认顺序 azure_s0 → youdao → azure_f0；大批量走付费 S0 前需 --allow-paid。

快速使用（Windows）
-------------------
  set PY=E:\\NieRReincarnation\\lunar-base\\.venv\\Scripts\\python.exe
  %PY% zh-l10n\\tools\\mt_client.py providers
  %PY% zh-l10n\\tools\\mt_client.py check
  %PY% zh-l10n\\tools\\mt_client.py text --text "Hello, world." --providers azure_f0
  %PY% zh-l10n\\tools\\mt_client.py translate --in  zh-l10n\\work\\text_en.jsonl ^
        --out zh-l10n\\work\\text_en.zh.jsonl --src en --dst zh-Hans --dry-run
  %PY% zh-l10n\\tools\\mt_client.py translate --in ... --out ... --allow-paid

输入/输出
---------
* --in  .jsonl：每行一个 JSON 对象，默认翻 "value" 字段（--field 可改）；
  输出 JSONL = 原字段 + translated + mt_provider + mt_src + mt_dst（失败另有 mt_error）。
* --in  .txt  ：每行一条文本；--out .txt 逐行输出译文，--out .jsonl 输出 {"src","translated"}。
* 断点续跑：--out 已存在时，先解析其中成功的译文（jsonl 按原文匹配），只翻剩余部分，最后整体重写。

退出码：0 成功（可能含个别失败，见统计）；2 配置/参数错误；3 付费保护拦截；4 全部 provider 失败。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

TOOL_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent          # zh-l10n/
DEFAULT_CONFIG = ROOT / "config" / "providers.json"


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def _reconfigure_stdio() -> None:
    """避免 Windows GBK 控制台在输出 ⟦/日文/emoji 时抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass


def eprint(*args: Any, **kwargs: Any) -> None:
    kwargs.setdefault("flush", True)
    print(*args, file=sys.stderr, **kwargs)


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mask_secret(secret: str) -> str:
    if not secret:
        return "(空)"
    return "***" + secret[-4:] if len(secret) > 8 else "***"


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def parse_provider_list(raw: str | None, default_order: Sequence[str]) -> list[str]:
    if not raw:
        return list(default_order)
    names = [x.strip() for x in raw.replace("，", ",").split(",") if x.strip()]
    if not names:
        return list(default_order)
    return names


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
class ConfigError(Exception):
    pass


def load_config(path: str | Path | None = None) -> dict:
    cfg_path = resolve_path(path) if path else DEFAULT_CONFIG
    if not cfg_path.is_file():
        raise ConfigError(f"配置文件不存在: {cfg_path}")
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件不是合法 JSON: {exc}") from exc
    if "providers" not in cfg or not isinstance(cfg["providers"], dict):
        raise ConfigError("配置缺少 providers 段")
    cfg["_path"] = str(cfg_path)
    return cfg


def get_default_order(cfg: dict) -> list[str]:
    order = cfg.get("default_order")
    if not order:
        order = [n for n, p in cfg["providers"].items() if p.get("kind") != "youdao"] + \
                [n for n, p in cfg["providers"].items() if p.get("kind") == "youdao"]
    known = [n for n in order if n in cfg["providers"]]
    return known or list(cfg["providers"].keys())


def get_provider_cfg(cfg: dict, name: str) -> dict:
    if name not in cfg["providers"]:
        raise ConfigError(
            f"未知 provider: {name}；已配置: {', '.join(cfg['providers'])}"
        )
    return cfg["providers"][name]


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
def new_stats() -> dict:
    return {
        "requests": 0,
        "items": 0,
        "chars": 0,
        "retries": 0,
        "errors": {},
        "disabled": False,
        "request_time_s": 0.0,
    }


class Stats:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.started_at = time.time()
        self.records = 0
        self.unique_texts = 0
        self.cache_hits = 0
        self.output_hits = 0
        self.empty_skips = 0
        self.no_translatable = 0
        self.protected_tokens = 0
        self.ph_mismatch = 0
        self.failed = 0
        self.ok = 0
        self.provider: dict[str, dict] = {}
        self.request_time_s = 0.0
        self.last_request_id = ""

    def p_add(self, name: str, *, requests: int = 0, items: int = 0, chars: int = 0,
              retries: int = 0, error: str | None = None, request_seconds: float = 0.0) -> None:
        with self.lock:
            st = self.provider.setdefault(name, new_stats())
            st["requests"] += requests
            st["items"] += items
            st["chars"] += chars
            st["retries"] += retries
            st["request_time_s"] += request_seconds
            self.request_time_s += request_seconds
            if error:
                st["errors"][error] = st["errors"].get(error, 0) + 1

    def disable(self, name: str) -> None:
        with self.lock:
            self.provider.setdefault(name, new_stats())["disabled"] = True

    def summary(self, cfg: dict, elapsed_s: float) -> dict:
        providers = {}
        total_cost: dict[str, float] = {}
        for name, st in self.provider.items():
            pcfg = cfg["providers"].get(name, {})
            billing = pcfg.get("billing") or {}
            cost = None
            currency = billing.get("currency")
            if billing and billing.get("unit_chars"):
                cost = round(st["chars"] * float(billing.get("price", 0.0)) / float(billing["unit_chars"]), 6)
                total_cost[currency or "?"] = round(total_cost.get(currency or "?", 0.0) + cost, 6)
            providers[name] = {
                "requests": st["requests"],
                "items": st["items"],
                "chars": st["chars"],
                "retries": st["retries"],
                "disabled": st["disabled"],
                "errors": dict(st["errors"]),
                "request_time_s": round(st["request_time_s"], 3),
                "estimated_cost": cost,
                "currency": currency,
            }
        return {
            "tool_version": TOOL_VERSION,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.started_at)),
            "elapsed_s": round(elapsed_s, 3),
            "records": self.records,
            "unique_texts": self.unique_texts,
            "ok": self.ok,
            "failed": self.failed,
            "cache_hits": self.cache_hits,
            "output_hits": self.output_hits,
            "empty_skips": self.empty_skips,
            "no_translatable": self.no_translatable,
            "protected_tokens": self.protected_tokens,
            "placeholder_mismatch": self.ph_mismatch,
            "providers": providers,
            "estimated_cost_total": total_cost,
            "queued_chars_s": round(
                sum(p["chars"] for p in providers.values()) / elapsed_s, 1) if elapsed_s > 0 else None,
        }


# ---------------------------------------------------------------------------
# 占位符保护
# ---------------------------------------------------------------------------
@dataclass
class ProtectedText:
    source: str
    text: str
    tokens: list[tuple[int, str]] = field(default_factory=list)


class PlaceholderProtector:
    """把不可翻译片段换成哨兵 ⟦i⟧，翻译后逐项还原并校验。

    默认保护（可在 providers.json 的 placeholder 段关闭/扩展）：
      real_newline          \\r\\n / \\n / \\r（默认关闭：有道把真实换行当多行查询，
                            含真实换行的文本由 provider 层单独请求；Azure 可直接承载）
      literal_escape        字面 \\n \\r \\t（两个字符）
      backslash_run         其余连续反斜杠（避免与哨兵相邻时被引擎吞掉）
      square_placeholder    [[P0]] 等
      angle_tag             <color=#ff0000> </color> <b> <br/> 等
      dotnet_placeholder    {0} {0:N0} {PlayerName} 等
      extra_patterns        配置里的额外正则
    """

    DEFAULT_SENTINEL = "{ph{i}}"  # 实测：Azure/有道 在紧邻与相邻上下文都能原样保留（花括号占位形态）

    def __init__(self, cfg: dict) -> None:
        ph = cfg.get("placeholder") or {}
        fmt = ph.get("sentinel_format") or self.DEFAULT_SENTINEL
        if "{i}" not in fmt:
            raise ConfigError(f"placeholder.sentinel_format 必须包含 {{i}}: {fmt!r}")
        self.prefix, self.suffix = fmt.split("{i}", 1)
        self._counter = 0
        self._lock = threading.Lock()

        patterns: list[tuple[str, str]] = []
        if ph.get("protect_real_newlines", True):
            patterns.append(("real_newline", r"\r\n|\r|\n"))
        if ph.get("protect_literal_escapes", True):
            patterns.append(("literal_escape", r"\\[nrt]"))
        if ph.get("protect_backslash_runs", True):
            patterns.append(("backslash_run", r"\\+"))
        if ph.get("protect_square_placeholders", True):
            patterns.append(("square_placeholder", r"\[\[[^\[\]\r\n]{1,64}\]\]"))
        if ph.get("protect_angle_tags", True):
            patterns.append(("angle_tag", r"</?[A-Za-z][A-Za-z0-9]*(?:\s*=\s*[^<>\r\n]{0,64})?\s*/?>"))
        if ph.get("protect_dotnet_placeholders", True):
            patterns.append(("dotnet_placeholder", r"\{[A-Za-z0-9_]+(?:[,:][^{}\r\n<>{]{0,32})?\}"))
        for extra in ph.get("extra_patterns") or []:
            patterns.append(("extra", str(extra)))

        self._kinds = [kind for kind, _ in patterns]
        self._regex: re.Pattern[str] | None = None
        if patterns:
            parts = [f"(?P<g{i}>{pat})" for i, (_, pat) in enumerate(patterns)]
            try:
                self._regex = re.compile("|".join(parts))
            except re.error as exc:
                raise ConfigError(f"占位符正则无效: {exc}") from exc
        self._sentinel_re = re.compile(
            self._flexible(self.prefix) + r"\s*(\d+)\s*" + self._flexible(self.suffix),
            re.IGNORECASE,
        )

    @staticmethod
    def _flexible(literal: str) -> str:
        """把哨兵的字面片段编译成允许引擎插入空格/大小写变化的宽松正则。"""
        if not literal:
            return ""
        return r"\s*".join(re.escape(ch) for ch in literal)

    # -- 生成不冲突的哨兵编号 ------------------------------------------------
    def _next_id(self, text: str) -> int:
        with self._lock:
            while True:
                idx = self._counter
                self._counter += 1
                sentinel = self.prefix + str(idx) + self.suffix
                if sentinel not in text:
                    return idx

    def protect(self, text: str) -> ProtectedText:
        if self._regex is None or not text:
            return ProtectedText(text, text, [])
        tokens: list[tuple[int, str]] = []
        out_parts: list[str] = []
        last = 0
        for m in self._regex.finditer(text):
            out_parts.append(text[last:m.start()])
            idx = self._next_id(text)
            sentinel = self.prefix + str(idx) + self.suffix
            tokens.append((idx, m.group(0)))
            out_parts.append(sentinel)
            last = m.end()
        if not tokens:
            return ProtectedText(text, text, [])
        out_parts.append(text[last:])
        return ProtectedText(text, "".join(out_parts), tokens)

    # -- 还原 ---------------------------------------------------------------
    def restore(self, translated: str, tokens: Sequence[tuple[int, str]]) -> tuple[str, str | None]:
        """返回 (还原后的文本, 错误描述或 None)。

        校验：每个哨兵必须恰好出现一次；缺失/重复/多出都算失败（由调用方重试/兜底）。
        """
        if not tokens:
            return translated, None
        found: dict[int, list[str]] = {}
        for m in self._sentinel_re.finditer(translated):
            idx = int(m.group(1))
            found.setdefault(idx, []).append(m.group(0))
        expected = {idx for idx, _ in tokens}
        missing = sorted(expected - set(found))
        duplicated = sorted(idx for idx in expected if len(found.get(idx, [])) > 1)
        unexpected = sorted(set(found) - expected)
        if missing or duplicated or unexpected:
            detail = []
            if missing:
                detail.append(f"丢失 {missing}")
            if duplicated:
                detail.append(f"重复 {duplicated}")
            if unexpected:
                detail.append(f"多出 {unexpected}")
            return translated, "占位符还原失败(" + "; ".join(detail) + ")"
        out = translated
        for idx, original in tokens:
            occurrence = found[idx][0]
            out = out.replace(occurrence, original, 1)
        return out, None


# ---------------------------------------------------------------------------
# 缓存
# ---------------------------------------------------------------------------
class Cache:
    """JSON 缓存：键 = sha256(src \\0 dst \\0 原文)，值 = {t: 译文, p: provider, ts: 时间}。

    默认 work/mt-cache.json；--no-cache 关闭。写入为临时文件 + 原子替换。
    """

    def __init__(self, path: Path | None, enabled: bool = True) -> None:
        self.path = path
        self.enabled = enabled and path is not None
        self.lock = threading.Lock()
        self.data: dict[str, dict] = {}
        self.dirty = 0
        self.last_flush = time.time()
        if self.enabled and self.path and self.path.is_file():  # type: ignore[union-attr]
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))  # type: ignore[union-attr]
                entries = raw.get("entries", raw)
                if isinstance(entries, dict):
                    self.data = entries
                eprint(f"[cache] 载入 {len(self.data)} 条: {self.path}")
            except Exception as exc:  # noqa: BLE001 - 缓存损坏不阻断
                corrupt = self.path.with_suffix(self.path.suffix + f".corrupt-{int(time.time())}")  # type: ignore[union-attr]
                try:
                    os.replace(self.path, corrupt)  # type: ignore[arg-type]
                except OSError:
                    pass
                eprint(f"[cache] 缓存损坏({exc})，已移到 {corrupt.name}，从空缓存开始")
                self.data = {}

    @staticmethod
    def key(src: str, dst: str, text: str) -> str:
        return sha256_text(f"{src}\x00{dst}\x00{text}")

    def get(self, src: str, dst: str, text: str) -> str | None:
        if not self.enabled:
            return None
        with self.lock:
            entry = self.data.get(self.key(src, dst, text))
        if isinstance(entry, dict):
            value = entry.get("t")
            return value if isinstance(value, str) else None
        return None

    def put(self, src: str, dst: str, text: str, translation: str, provider: str) -> None:
        if not self.enabled:
            return
        with self.lock:
            self.data[self.key(src, dst, text)] = {
                "t": translation, "p": provider, "ts": int(time.time()),
            }
            self.dirty += 1

    def flush(self, force: bool = False) -> None:
        if not self.enabled or self.path is None:
            return
        with self.lock:
            if not self.dirty and not force:
                return
            payload = {
                "version": 1,
                "generated_at": iso_now(),
                "entries": self.data,
            }
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")  # type: ignore[union-attr]
            try:
                tmp.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]
                tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")  # type: ignore[union-attr]
                os.replace(tmp, self.path)  # type: ignore[arg-type]
                self.dirty = 0
                self.last_flush = time.time()
            except OSError as exc:  # 磁盘/权限问题：只告警，不阻断翻译
                eprint(f"[cache] 写入失败: {exc}")

    def maybe_flush(self, every_entries: int = 300, every_seconds: float = 120.0) -> None:
        if self.dirty >= every_entries or (time.time() - self.last_flush) >= every_seconds:
            self.flush()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def http_post(
    url: str,
    data: bytes,
    headers: dict[str, str],
    timeout: float,
) -> tuple[int, dict[str, str], str, float, Exception | None]:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, body, time.perf_counter() - t0, None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, body, time.perf_counter() - t0, None
    except Exception as exc:  # noqa: BLE001 - 超时/DNS/TLS 等统一按可重试处理
        return -1, {}, "", time.perf_counter() - t0, exc


# ---------------------------------------------------------------------------
# Provider 异常
# ---------------------------------------------------------------------------
class ProviderError(Exception):
    pass


class RetryableError(ProviderError):
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class SplitError(ProviderError):
    """整批请求被拒（批量过大/格式问题），应拆小重试。"""


class FatalError(ProviderError):
    """provider 不可再用（鉴权/额度/配置错误）。"""


class UnsupportedError(ProviderError):
    """该 provider 无法处理这批文本（如单条超长）。"""


class AllProvidersFailed(ProviderError):
    def __init__(self, message: str, causes: list[str] | None = None) -> None:
        super().__init__(message)
        self.causes = causes or []


# ---------------------------------------------------------------------------
# Provider 基类
# ---------------------------------------------------------------------------
class BaseProvider:
    kind = "base"

    def __init__(self, name: str, pcfg: dict, gcfg: dict, stats: Stats,
                 src: str, dst: str, *, delay: float | None = None) -> None:
        self.name = name
        self.pcfg = pcfg
        self.gcfg = gcfg
        self.stats = stats
        self.src = src
        self.dst = dst
        self.max_items = int(pcfg.get("batch_max_items", pcfg.get("batch_max_lines", 50)))
        self.max_chars = int(pcfg.get("batch_max_chars", 45000))
        self.max_single_chars = int(pcfg.get("max_single_chars", self.max_chars))
        self.timeout = float(pcfg.get("request_timeout_s", 60))
        self.max_retries = int(pcfg.get("max_retries", 3))
        self.min_interval = float(delay if delay is not None else pcfg.get("min_interval_s", 0.0) or 0.0)
        self._rate_lock = threading.Lock()
        self._last_request = 0.0

    # -- 限流 ----------------------------------------------------------------
    def _rate_wait(self) -> None:
        if self.min_interval <= 0:
            return
        with self._rate_lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    # -- 分批 ----------------------------------------------------------------
    def plan(self, texts: Sequence[str]) -> list[list[str]]:
        chunks: list[list[str]] = []
        cur: list[str] = []
        chars = 0
        for text in texts:
            n = len(text)
            if n > self.max_single_chars:
                raise UnsupportedError(
                    f"{self.name} 单条上限 {self.max_single_chars} 字符，本条 {n} 字符")
            if cur and (len(cur) >= self.max_items or chars + n > self.max_chars):
                chunks.append(cur)
                cur, chars = [], 0
            cur.append(text)
            chars += n
        if cur:
            chunks.append(cur)
        return chunks

    def translate_batch(self, texts: Sequence[str]) -> list[str]:
        result: list[str] = []
        for chunk in self.plan(texts):
            result.extend(self._translate_chunk(list(chunk)))
        return result

    def _translate_chunk(self, chunk: list[str], attempt: int = 0) -> list[str]:
        try:
            return self._request(chunk)
        except SplitError as exc:
            if len(chunk) <= 1:
                raise UnsupportedError(f"{self.name} 单条请求仍失败: {exc}") from exc
            mid = max(1, len(chunk) // 2)
            eprint(f"[{self.name}] 批量被拒({exc})，拆分为 {mid}+{len(chunk) - mid} 重试")
            return self._translate_chunk(chunk[:mid]) + self._translate_chunk(chunk[mid:])
        except RetryableError as exc:
            if attempt >= self.max_retries:
                raise
            delay = exc.retry_after if exc.retry_after is not None else min(2.0 ** attempt + random.uniform(0, 0.3), 30.0)
            with self.stats.lock:
                st = self.stats.provider.setdefault(self.name, new_stats())
                st["retries"] += 1
            eprint(f"[{self.name}] 可重试错误({exc})，{delay:.1f}s 后第 {attempt + 1}/{self.max_retries} 次重试")
            time.sleep(max(0.0, delay))
            return self._translate_chunk(chunk, attempt + 1)

    def _request(self, texts: list[str]) -> list[str]:
        raise NotImplementedError

    # -- 供 CLI/文档使用 -----------------------------------------------------
    def describe(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "max_items_per_request": self.max_items,
            "max_chars_per_request": self.max_chars,
            "max_single_chars": self.max_single_chars,
            "min_interval_s": self.min_interval,
            "billing": self.pcfg.get("billing"),
        }


# ---------------------------------------------------------------------------
# Azure Translator
# ---------------------------------------------------------------------------
AZURE_FATAL_400 = {400003, 400004, 400005, 400006, 400018, 400019, 400021, 400023,
                   400035, 400036, 400042, 400043, 400064, 400070, 400071, 400073,
                   400074, 400075, 400079, 400080}
AZURE_SPLIT_400 = {400020, 400050, 400072, 400077}
AZURE_RETRY_CODES = {408001, 408002, 429000, 429001, 429002, 500000, 503000}


class AzureProvider(BaseProvider):
    kind = "azure"

    def __init__(self, name: str, pcfg: dict, gcfg: dict, stats: Stats,
                 src: str, dst: str, *, delay: float | None = None) -> None:
        super().__init__(name, pcfg, gcfg, stats, src, dst, delay=delay)
        self.region = str(pcfg.get("region", "") or "")
        self.api_version = str(pcfg.get("api_version", "3.0"))
        self.endpoints = self._normalize_endpoints(pcfg.get("endpoints") or [])
        if not self.endpoints:
            raise ConfigError(f"{name} 未配置 endpoints")
        self.keys = [k for k in (pcfg.get("keys") or []) if isinstance(k, str) and k]
        if not self.keys:
            raise ConfigError(f"{name} 未配置 keys")
        self._lock = threading.Lock()
        self._ep_idx = 0
        self._key_idx = 0
        self._bad_keys: set[int] = set()

    @staticmethod
    def _normalize_endpoints(raw: Iterable[Any]) -> list[str]:
        out = []
        for item in raw:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict) and item.get("url"):
                out.append(str(item["url"]))
        return out

    def _current_endpoint(self) -> str:
        with self._lock:
            return self.endpoints[self._ep_idx]

    def _advance_endpoint(self) -> bool:
        with self._lock:
            if self._ep_idx + 1 < len(self.endpoints):
                self._ep_idx += 1
                return True
            return False

    def _current_key(self) -> str | None:
        with self._lock:
            for i in range(len(self.keys)):
                idx = (self._key_idx + i) % len(self.keys)
                if idx not in self._bad_keys:
                    self._key_idx = idx
                    return self.keys[idx]
            return None

    def _rotate_key(self) -> bool:
        with self._lock:
            self._bad_keys.add(self._key_idx)
            for i in range(1, len(self.keys) + 1):
                idx = (self._key_idx + i) % len(self.keys)
                if idx not in self._bad_keys:
                    self._key_idx = idx
                    return True
            return False

    def _build_url(self, base: str) -> str:
        parsed = urllib.parse.urlsplit(base)
        query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("api-version", self.api_version)
        query["from"] = self.src
        query["to"] = self.dst
        return urllib.parse.urlunsplit((
            parsed.scheme, parsed.netloc, parsed.path,
            urllib.parse.urlencode(query), parsed.fragment,
        ))

    def _request(self, texts: list[str]) -> list[str]:
        self._rate_wait()
        payload = json.dumps([{"Text": t} for t in texts], ensure_ascii=False).encode("utf-8")
        ep_tries = 0
        while ep_tries < len(self.endpoints):
            key = self._current_key()
            if key is None:
                raise FatalError(f"{self.name} 所有密钥认证失败")
            url = self._build_url(self._current_endpoint())
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Ocp-Apim-Subscription-Key": key,
            }
            if self.region:
                headers["Ocp-Apim-Subscription-Region"] = self.region
            status, resp_headers, body, elapsed, net_exc = http_post(url, payload, headers, self.timeout)
            self.stats.p_add(self.name, request_seconds=elapsed)
            if net_exc is not None:
                raise RetryableError(f"{self.name} 网络异常: {type(net_exc).__name__}: {net_exc}")
            req_id = resp_headers.get("x-requestid", "")
            if req_id:
                self.stats.last_request_id = req_id

            if status == 200:
                return self._parse_success(body, len(texts), texts)

            code, message = self._parse_error(body)
            msg = f"HTTP {status} code={code} {message}"
            if req_id:
                msg += f" (X-RequestId={req_id})"

            if status == 404:
                if self._advance_endpoint():
                    eprint(f"[{self.name}] 端点 404，切换下一个端点: {self.endpoints[self._ep_idx]}")
                    ep_tries += 1
                    continue
                raise FatalError(f"{self.name} 所有端点均 404: {msg}")
            if status == 401 or code in (401000, 401015):
                if self._rotate_key():
                    eprint(f"[{self.name}] 密钥 401，切换备用密钥")
                    continue
                raise FatalError(f"{self.name} 密钥无效或全部失效: {msg}")
            if status == 403 or code == 403001:
                hint = "（F0 免费额度用尽或资源未授权）" if self.name.endswith("_f0") else "（额度/权限问题，可能产生费用）"
                raise FatalError(f"{self.name} 403 拒绝{hint}: {msg}")
            if status == 429 or code in (429000, 429001, 429002):
                retry_after = self._retry_after(resp_headers)
                raise RetryableError(f"{self.name} 限流: {msg}", retry_after=retry_after)
            if status in (408, 500, 502, 503, 504) or code in AZURE_RETRY_CODES:
                raise RetryableError(f"{self.name} 服务暂时不可用: {msg}")
            if status == 400:
                if code in AZURE_SPLIT_400:
                    raise SplitError(msg)
                raise FatalError(f"{self.name} 请求参数/配置错误: {msg}")
            raise RetryableError(f"{self.name} 未知错误: {msg}")
        raise FatalError(f"{self.name} 所有端点不可用")

    @staticmethod
    def _retry_after(headers: dict[str, str]) -> float | None:
        raw = headers.get("retry-after")
        if raw:
            try:
                return min(float(raw), 120.0)
            except ValueError:
                pass
        return None

    def _parse_success(self, body: str, expected: int, texts: list[str]) -> list[str]:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RetryableError(f"{self.name} 响应不是 JSON: {exc}") from exc
        if not isinstance(parsed, list) or len(parsed) != expected:
            raise RetryableError(
                f"{self.name} 响应条数异常: 期望 {expected}, 实际 {len(parsed) if isinstance(parsed, list) else type(parsed).__name__}")
        out: list[str] = []
        for idx, item in enumerate(parsed):
            try:
                out.append(str(item["translations"][0]["text"]))
            except (KeyError, IndexError, TypeError) as exc:
                raise RetryableError(f"{self.name} 第 {idx} 条响应缺少译文字段: {exc}") from exc
        self.stats.p_add(
            self.name,
            requests=1,
            items=expected,
            chars=sum(len(t) for t in texts),
        )
        return out

    @staticmethod
    def _parse_error(body: str) -> tuple[int | None, str]:
        try:
            parsed = json.loads(body)
            err = parsed.get("error") or {}
            code = err.get("code")
            message = str(err.get("message", ""))[:400]
            return (int(code) if code is not None else None), message
        except Exception:  # noqa: BLE001
            return None, body[:400].replace("\n", " ")


# ---------------------------------------------------------------------------
# 有道智云
# ---------------------------------------------------------------------------
class YoudaoProvider(BaseProvider):
    kind = "youdao"

    YOUDAO_RETRY = {"411", "412", "301", "302", "303", "304", "207"}
    YOUDAO_FATAL = {"202", "108", "110", "111", "401", "105", "104", "106", "107", "109", "112", "203", "205"}

    def __init__(self, name: str, pcfg: dict, gcfg: dict, stats: Stats,
                 src: str, dst: str, *, delay: float | None = None) -> None:
        super().__init__(name, pcfg, gcfg, stats, src, dst, delay=delay)
        self.url = str(pcfg.get("endpoint") or "https://openapi.youdao.com/api")
        self.app_key = str(pcfg.get("app_key") or "")
        self.app_secret = str(pcfg.get("app_secret") or "")
        if not self.app_key or not self.app_secret:
            raise ConfigError(f"{name} 缺少 app_key/app_secret")
        lang_map = pcfg.get("lang_map") or {}
        self.src_lang = str(lang_map.get(src, src))
        self.dst_lang = str(lang_map.get(dst, dst))
        self.use_utf16_len = str(pcfg.get("sign_length_unit", "utf16")) == "utf16"

    # -- 签名 ----------------------------------------------------------------
    def _sign(self, q: str, salt: str, curtime: str) -> str:
        if self.use_utf16_len:
            length = len(q.encode("utf-16-le")) // 2
        else:
            length = len(q)
        sign_input = q if length <= 20 else (q[:10] + str(length) + q[-10:])
        raw = self.app_key + sign_input + salt + curtime + self.app_secret
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _request(self, texts: list[str]) -> list[str]:
        # 有道把 q 里的真实换行当"多行查询"：含换行的文本逐条单独请求，其余照常合批，
        # 避免多行对齐错乱；单条文本含换行时直接按单条查询（引擎会保留/合并其中的换行）。
        if len(texts) > 1 and any("\n" in t or "\r" in t for t in texts):
            normal = [t for t in texts if "\n" not in t and "\r" not in t]
            special = [t for t in texts if "\n" in t or "\r" in t]
            out: list[str] = []
            if normal:
                out.extend(self._request(normal))
            for text in special:
                out.extend(self._request([text]))
            return out
        q = "\n".join(texts)
        salt = str(random.randint(100000, 999999))
        curtime = str(int(time.time()))
        form = {
            "q": q,
            "from": self.src_lang,
            "to": self.dst_lang,
            "appKey": self.app_key,
            "salt": salt,
            "sign": self._sign(q, salt, curtime),
            "signType": "v3",
            "curtime": curtime,
        }
        body = urllib.parse.urlencode(form).encode("utf-8")
        self._rate_wait()
        status, resp_headers, resp, elapsed, net_exc = http_post(
            self.url, body, {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, self.timeout)
        self.stats.p_add(self.name, request_seconds=elapsed)
        if net_exc is not None:
            raise RetryableError(f"{self.name} 网络异常: {type(net_exc).__name__}: {net_exc}")
        if status != 200:
            raise RetryableError(f"{self.name} HTTP {status}: {resp[:300]}")
        try:
            parsed = json.loads(resp)
        except json.JSONDecodeError as exc:
            raise RetryableError(f"{self.name} 响应不是 JSON: {exc}") from exc
        error_code = str(parsed.get("errorCode", ""))
        if error_code == "0":
            translations = parsed.get("translation") or []
            if not translations:
                raise RetryableError(f"{self.name} 响应无 translation 字段")
            merged = str(translations[0])
            if len(texts) == 1:
                out = [merged]
            else:
                lines = [ln[:-1] if ln.endswith("\r") else ln for ln in merged.split("\n")]
                if len(lines) != len(texts):
                    raise SplitError(
                        f"{self.name} 多行返回 {len(lines)} 行，与请求 {len(texts)} 行不一致")
                out = lines
            self.stats.p_add(self.name, requests=1, items=len(texts), chars=len(q))
            return out

        message = f"{self.name} errorCode={error_code} {resp[:300]}"
        if error_code == "103":
            raise SplitError(message)
        if error_code in self.YOUDAO_RETRY:
            raise RetryableError(message)
        if error_code in self.YOUDAO_FATAL:
            raise FatalError(message)
        raise RetryableError(message)


# ---------------------------------------------------------------------------
# Provider 池（降级）
# ---------------------------------------------------------------------------
def build_provider(name: str, gcfg: dict, stats: Stats, src: str, dst: str,
                   delay: float | None = None) -> BaseProvider:
    pcfg = get_provider_cfg(gcfg, name)
    kind = str(pcfg.get("kind", "")).lower()
    if kind == "azure":
        return AzureProvider(name, pcfg, gcfg, stats, src, dst, delay=delay)
    if kind == "youdao":
        return YoudaoProvider(name, pcfg, gcfg, stats, src, dst, delay=delay)
    raise ConfigError(f"未知 provider 类型: {name}.kind={kind}")


class ProviderPool:
    def __init__(self, gcfg: dict, stats: Stats, order: Sequence[str], src: str, dst: str,
                 delay: float | None = None) -> None:
        self.gcfg = gcfg
        self.stats = stats
        self.order = list(order)
        self.providers: dict[str, BaseProvider] = {}
        for name in self.order:
            self.providers[name] = build_provider(name, gcfg, stats, src, dst, delay=delay)
        self.disabled: dict[str, str] = {}
        self.lock = threading.Lock()
        self.error_log: list[str] = []

    def disable(self, name: str, reason: str) -> None:
        with self.lock:
            if name in self.disabled:
                return
            self.disabled[name] = reason
            self.stats.disable(name)
        eprint(f"[降级] 停用 provider {name}: {reason}")

    def usable(self) -> list[str]:
        with self.lock:
            return [n for n in self.order if n not in self.disabled]

    def translate(self, texts: Sequence[str]) -> tuple[list[str], str]:
        """按顺序尝试 provider；返回 (译文列表, 实际 provider 名)。"""
        errors: list[str] = []
        for name in self.usable():
            provider = self.providers[name]
            try:
                out = provider.translate_batch(texts)
                return out, name
            except FatalError as exc:
                self.disable(name, str(exc))
                errors.append(f"{name}: {exc}")
            except UnsupportedError as exc:
                errors.append(f"{name}: {exc}")
            except RetryableError as exc:
                errors.append(f"{name}: {exc}")
            except SplitError as exc:  # 理论上已在 provider 内部处理
                errors.append(f"{name}: {exc}")
        with self.lock:
            self.error_log.extend(errors)
        raise AllProvidersFailed("所有 provider 均失败: " + " | ".join(errors), errors)


# ---------------------------------------------------------------------------
# 结果记录
# ---------------------------------------------------------------------------
@dataclass
class Translation:
    source: str
    translated: str | None
    provider: str | None
    error: str | None = None


# ---------------------------------------------------------------------------
# 翻译调度
# ---------------------------------------------------------------------------
def _remove_sentinels(text: str, protector: PlaceholderProtector, tokens: Sequence[tuple[int, str]]) -> str:
    if not tokens:
        return text
    out = text
    for idx, _original in tokens:
        out = out.replace(protector.prefix + str(idx) + protector.suffix, "")
    return out


def _chunk_units(items: list[Any], items_per_unit: int, chars_per_unit: int,
                 text_getter) -> list[list[Any]]:
    units: list[list[Any]] = []
    cur: list[Any] = []
    chars = 0
    for item in items:
        text = text_getter(item)
        if cur and (len(cur) >= items_per_unit or chars + len(text) > chars_per_unit):
            units.append(cur)
            cur, chars = [], 0
        cur.append(item)
        chars += len(text)
    if cur:
        units.append(cur)
    return units


def run_translation(
    unique_texts: list[str],
    *,
    protector: PlaceholderProtector,
    cache: Cache,
    pool: ProviderPool,
    stats: Stats,
    src: str,
    dst: str,
    on_fail: str = "source",
    work_unit_items: int = 100,
    work_unit_chars: int = 20000,
    concurrency: int = 1,
    verbose: bool = False,
    dry_run: bool = False,
) -> dict[str, Translation]:
    """对去重后的文本执行翻译，返回 原文 -> Translation。"""
    results: dict[str, Translation] = {}
    pending: list[ProtectedText] = []

    for text in unique_texts:
        if text == "" or not text.strip():
            results[text] = Translation(text, text, None, None)
            stats.empty_skips += 1
            continue
        cached = cache.get(src, dst, text)
        if cached is not None:
            results[text] = Translation(text, cached, "(cache)", None)
            stats.cache_hits += 1
            continue
        protected = protector.protect(text)
        if protected.tokens:
            stats.protected_tokens += len(protected.tokens)
        if not _remove_sentinels(protected.text, protector, protected.tokens).strip():
            results[text] = Translation(text, text, None, None)
            stats.no_translatable += 1
            continue
        pending.append(protected)

    unique_pending_chars = sum(len(p.text) for p in pending)
    if dry_run:
        return results

    units = _chunk_units(pending, work_unit_items, work_unit_chars, lambda p: p.text)
    total_units = len(units)
    done_units = 0
    done_lock = threading.Lock()
    started = time.time()

    def process_unit(unit: list[ProtectedText]) -> list[tuple[ProtectedText, str | None, str | None, str | None]]:
        protected_texts = [p.text for p in unit]
        try:
            translated, provider = pool.translate(protected_texts)
            providers = [provider] * len(unit)
        except AllProvidersFailed:
            translated, providers = [], []
            for p in unit:
                try:
                    one, pv = pool.translate([p.text])
                    translated.append(one[0])
                    providers.append(pv)
                except AllProvidersFailed:
                    translated.append(None)
                    providers.append(None)
        out: list[tuple[ProtectedText, str | None, str | None, str | None]] = []
        for p, tr, pv in zip(unit, translated, providers):
            if tr is None:
                out.append((p, None, pv, "all_providers_failed"))
                continue
            restored, ph_err = protector.restore(tr, p.tokens)
            if ph_err:
                # 占位符异常：单条再用完整降级链重试一次
                try:
                    one, pv2 = pool.translate([p.text])
                    restored2, err2 = protector.restore(one[0], p.tokens)
                    if not err2:
                        out.append((p, restored2, pv2, None))
                        continue
                    ph_err = ph_err + "；重试后仍异常"
                except AllProvidersFailed:
                    ph_err = ph_err + "；重试请求失败"
                out.append((p, None, pv, "placeholder_mismatch: " + ph_err))
                continue
            out.append((p, restored, pv, None))
        return out

    def handle_done(batch: list[tuple[ProtectedText, str | None, str | None, str | None]]) -> None:
        nonlocal done_units
        for p, tr, pv, err in batch:
            if tr is None:
                stats.failed += 1
                if err and err.startswith("placeholder_mismatch"):
                    stats.ph_mismatch += 1
                fallback = p.source if on_fail == "source" else None
                results[p.source] = Translation(p.source, fallback, pv, err or "untagged_failure")
            else:
                stats.ok += 1
                results[p.source] = Translation(p.source, tr, pv, None)
                cache.put(src, dst, p.source, tr, pv or "?")
        cache.maybe_flush()
        with done_lock:
            done_units += 1
            current = done_units
        if total_units and (current == total_units or current % max(1, total_units // 20) == 0):
            elapsed = time.time() - started
            eprint(f"[mt] 单元 {current}/{total_units}，已完成 {len(results)}/{len(unique_texts)} 条，"
                   f"{elapsed:.1f}s")

    try:
        if concurrency <= 1:
            for unit in units:
                handle_done(process_unit(unit))
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as ex:
                for batch in ex.map(process_unit, units):
                    handle_done(batch)
    finally:
        cache.flush(force=True)

    return results


# ---------------------------------------------------------------------------
# 统一 Python 接口
# ---------------------------------------------------------------------------
def translate(
    texts: Sequence[str],
    src: str = "en",
    dst: str = "zh-Hans",
    providers: Sequence[str] | None = None,
    *,
    config_path: str | Path | None = None,
    cache_path: str | Path | None = None,
    use_cache: bool = True,
    on_fail: str = "source",
    concurrency: int = 1,
) -> list[str]:
    """统一接口：translate(texts, src, dst) -> list[str]。

    供流水线 import 使用；返回与输入等长的译文列表（失败项按 on_fail 返回原文或空串）。
    """
    cfg = load_config(config_path)
    order = list(providers) if providers else get_default_order(cfg)
    stats = Stats()
    protector = PlaceholderProtector(cfg)
    cache_file = resolve_path(cache_path) if cache_path else resolve_path(
        cfg.get("cache_path") or "work/mt-cache.json")
    cache = Cache(cache_file, enabled=use_cache)
    pool = ProviderPool(cfg, stats, order, src, dst)
    unique = list(dict.fromkeys(texts))
    sched = cfg.get("scheduler") or {}
    stats.records = len(texts)
    stats.unique_texts = len(unique)
    results = run_translation(
        unique, protector=protector, cache=cache, pool=pool, stats=stats,
        src=src, dst=dst, on_fail=on_fail,
        work_unit_items=int(sched.get("work_unit_items", 100)),
        work_unit_chars=int(sched.get("work_unit_chars", 20000)),
        concurrency=concurrency,
    )
    cache.flush(force=True)
    out: list[str] = []
    for text in texts:
        item = results.get(text)
        if item is None or item.translated is None:
            out.append(text if on_fail == "source" else "")
        else:
            out.append(item.translated)
    return out


# ---------------------------------------------------------------------------
# 输入/输出
# ---------------------------------------------------------------------------
def is_jsonl(path: Path, fmt: str | None = None) -> bool:
    if fmt:
        return fmt == "jsonl"
    return path.suffix.lower() in (".jsonl", ".json", ".ndjson")


def read_input_texts(path: Path, fmt: str | None = None, field_name: str = "value",
                     limit: int | None = None) -> list[str]:
    if not path.is_file():
        raise ConfigError(f"输入文件不存在: {path}")
    jsonl = is_jsonl(path, fmt)
    texts: list[str] = []
    if jsonl:
        with path.open("r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                raw = raw.rstrip("\n")
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ConfigError(f"{path} 第 {lineno} 行不是合法 JSON: {exc}") from exc
                if field_name not in obj:
                    raise ConfigError(f"{path} 第 {lineno} 行缺少字段 {field_name!r}")
                value = obj[field_name]
                texts.append(value if isinstance(value, str) else str(value))
                if limit and len(texts) >= limit:
                    break
    else:
        with path.open("r", encoding="utf-8", newline="") as fh:
            content = fh.read()
        for line in content.split("\n"):
            if line.endswith("\r"):
                line = line[:-1]
            texts.append(line)
        if texts and texts[-1] == "" and not content.endswith("\n"):
            pass
        elif texts and texts[-1] == "":
            texts.pop()
        if limit:
            texts = texts[:limit]
    return texts


def scan_output(path: Path, fmt: str | None = None, field_name: str = "value",
                jsonl_out: bool = True) -> tuple[dict[str, str], list[str]]:
    """读取已有输出，返回 (原文->译文 映射, 文本模式下已有的译文行列表)。"""
    if not path.is_file():
        return {}, []
    done: dict[str, str] = {}
    lines: list[str] = []
    if jsonl_out:
        with path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # 中断留下的半行
                src_text = obj.get(field_name)
                translated = obj.get("translated")
                if isinstance(src_text, str) and isinstance(translated, str):
                    done[src_text] = translated
    else:
        with path.open("r", encoding="utf-8", newline="") as fh:
            content = fh.read()
        lines = content.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
    return done, lines


def write_output(
    in_path: Path,
    out_path: Path,
    texts: list[str],
    results: dict[str, Translation],
    *,
    src: str,
    dst: str,
    field_name: str = "value",
    out_jsonl: bool = True,
    input_jsonl: bool = True,
    write_value: bool = False,
    on_fail: str = "source",
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")

    def failure_value(source_text: str) -> str | None:
        return source_text if on_fail == "source" else None

    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        if input_jsonl and not out_jsonl:
            for text in texts:
                item = results.get(text)
                translated = item.translated if item and item.translated is not None else failure_value(text)
                fh.write((translated if translated is not None else text) + "\n")
        elif input_jsonl:
            written = 0
            with in_path.open("r", encoding="utf-8") as src_fh:
                for raw in src_fh:
                    if written >= len(texts):
                        break
                    if not raw.strip():
                        continue
                    obj = json.loads(raw)
                    source_text = obj[field_name] if isinstance(obj.get(field_name), str) else str(obj.get(field_name, ""))
                    item = results.get(source_text)
                    row = dict(obj)
                    if item is None:
                        row["translated"] = failure_value(source_text)
                        row["mt_error"] = "missing_result"
                    else:
                        row["translated"] = item.translated if item.translated is not None else failure_value(source_text)
                        if item.provider:
                            row["mt_provider"] = item.provider
                        row["mt_src"] = src
                        row["mt_dst"] = dst
                        if item.error:
                            row["mt_error"] = item.error
                    if write_value and isinstance(row.get("translated"), str):
                        row[field_name] = row["translated"]
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    written += 1
        else:
            for idx, text in enumerate(texts):
                item = results.get(text)
                translated = item.translated if item and item.translated is not None else failure_value(text)
                if out_jsonl:
                    row = {"i": idx, "src": text, "translated": translated,
                           "mt_src": src, "mt_dst": dst}
                    if item and item.provider:
                        row["mt_provider"] = item.provider
                    if item and item.error:
                        row["mt_error"] = item.error
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                else:
                    fh.write((translated if translated is not None else text) + "\n")
    os.replace(tmp, out_path)


# ---------------------------------------------------------------------------
# 费用/配额估算
# ---------------------------------------------------------------------------
def estimate_all(cfg: dict, names: Sequence[str], chars: int) -> list[dict]:
    rows = []
    for name in names:
        pcfg = cfg["providers"].get(name)
        if not pcfg:
            continue
        billing = pcfg.get("billing") or {}
        price = billing.get("price")
        unit = billing.get("unit_chars")
        currency = billing.get("currency", "")
        cost = round(chars * float(price) / float(unit), 4) if price is not None and unit else None
        rows.append({
            "provider": name,
            "chars": chars,
            "estimated_cost": cost,
            "currency": currency,
            "free_chars_per_month": billing.get("free_chars_per_month"),
            "paid": name in (cfg.get("paid_providers") or []),
        })
    return rows


def print_estimate(cfg: dict, names: Sequence[str], chars: int) -> None:
    eprint(f"[估算] 待翻译源码字符: {chars:,}（按各 provider 单独承担时的费用）")
    for row in estimate_all(cfg, names, chars):
        cost = "免费" if row["estimated_cost"] == 0 else (
            f"{row['estimated_cost']} {row['currency']}" if row["estimated_cost"] is not None else "未知")
        tag = "（付费层）" if row["paid"] else ""
        free = f"，月免费 {row['free_chars_per_month']:,} 字符" if row.get("free_chars_per_month") else ""
        eprint(f"  - {row['provider']}{tag}: {cost}{free}")


# ---------------------------------------------------------------------------
# CLI 子命令
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mt_client.py",
        description="NieR Re[in]carnation 汉化机器翻译客户端（Azure Translator / 有道智云）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  mt_client.py providers\n"
            "  mt_client.py check\n"
            "  mt_client.py text --text \"Hello, world.\" --providers azure_f0\n"
            "  mt_client.py translate --in zh-l10n/work/text_en.jsonl --out zh-l10n/work/text_en.zh.jsonl "
            "--src en --dst zh-Hans --dry-run\n"
            "  mt_client.py translate --in ... --out ... --allow-paid\n"
            "\n默认 provider 顺序: azure_s0 → youdao → azure_f0（配置 config/providers.json 的 default_order）"
        ),
    )
    parser.add_argument("--config", default=None, help="providers.json 路径（默认 zh-l10n/config/providers.json）")
    parser.add_argument("--version", action="version", version=f"mt_client {TOOL_VERSION}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # providers -----------------------------------------------------------
    sp = sub.add_parser("providers", help="列出已配置的 provider（离线，不消耗额度）")
    sp.set_defaults(func=cmd_providers)

    # check ---------------------------------------------------------------
    sp = sub.add_parser("check", help="逐个 provider 发一条 5 字符健康检查（消耗极少字符）")
    sp.add_argument("--providers", default=None, help="逗号分隔，默认按 default_order")
    sp.add_argument("--text", default="Hello", help="检查用文本（默认 Hello，勿改长文本）")
    sp.add_argument("--src", default="en")
    sp.add_argument("--dst", default="zh-Hans")
    sp.set_defaults(func=cmd_check)

    # text ----------------------------------------------------------------
    sp = sub.add_parser("text", help="单条文本翻译测试（默认不走缓存）")
    sp.add_argument("--text", required=True)
    sp.add_argument("--src", default="en")
    sp.add_argument("--dst", default="zh-Hans")
    sp.add_argument("--providers", default=None, help="逗号分隔，默认按 default_order 依次降级")
    sp.add_argument("--cache-file", default=None, help="缓存文件（默认不启用）")
    sp.set_defaults(func=cmd_text)

    # translate -----------------------------------------------------------
    sp = sub.add_parser("translate", help="批量翻译 jsonl/txt")
    sp.add_argument("--in", dest="input", required=True, help="输入文件 .jsonl 或 .txt")
    sp.add_argument("--out", dest="output", required=True, help="输出文件（.jsonl 保留结构；.txt 只写译文）")
    sp.add_argument("--src", default="en")
    sp.add_argument("--dst", default="zh-Hans")
    sp.add_argument("--providers", default=None,
                    help="逗号分隔的降级顺序，默认 azure_s0,youdao,azure_f0")
    sp.add_argument("--field", default="value", help="jsonl 输入里要翻译的字段名（默认 value）")
    sp.add_argument("--limit", type=int, default=0, help="只处理前 N 条（调试用）")
    sp.add_argument("--cache-file", default=None, help="缓存文件（默认 config.cache_path）")
    sp.add_argument("--no-cache", action="store_true", help="禁用本地缓存")
    sp.add_argument("--overwrite", action="store_true", help="忽略已存在的输出文件，从头翻译")
    sp.add_argument("--concurrency", type=int, default=1, choices=[1, 2], help="并发请求数（1~2，默认 1）")
    sp.add_argument("--delay", type=float, default=None, help="每次请求前的固定间隔秒数（默认取各 provider 配置）")
    sp.add_argument("--allow-paid", action="store_true", help="允许大批量使用付费层（azure_s0）")
    sp.add_argument("--max-chars", type=int, default=0, help="待翻译字符数硬上限，超过则拒绝执行（测试保护）")
    sp.add_argument("--on-fail", choices=["source", "null"], default="source",
                    help="单条彻底失败时的输出：source=原文（默认），null=null")
    sp.add_argument("--write-value", action="store_true", help="同时把 translated 写回 --field 字段")
    sp.add_argument("--dry-run", action="store_true", help="只统计待翻译量与费用估算，不调用任何 API")
    sp.add_argument("--stats-out", default=None, help="把统计结果写成 JSON 文件")
    sp.add_argument("--verbose", action="store_true")
    sp.set_defaults(func=cmd_translate)

    return parser


def cmd_providers(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    eprint(f"配置文件: {cfg['_path']}")
    eprint(f"默认顺序: {' → '.join(get_default_order(cfg))}")
    eprint("")
    for name, pcfg in cfg["providers"].items():
        kind = pcfg.get("kind", "?")
        print(f"## {name}  [{kind}]")
        print(f"   label    : {pcfg.get('label', '')}")
        if kind == "azure":
            print(f"   region   : {pcfg.get('region', '')}  api-version: {pcfg.get('api_version', '3.0')}")
            for ep in pcfg.get("endpoints", []):
                url = ep if isinstance(ep, str) else ep.get("url", "")
                print(f"   endpoint : {url}")
            print(f"   keys     : {len(pcfg.get('keys', []))} 把（{', '.join(mask_secret(k) for k in pcfg.get('keys', []))}）")
            print(f"   批量限制 : ≤{pcfg.get('batch_max_items')} 条 / ≤{pcfg.get('batch_max_chars')} 字符每请求")
        elif kind == "youdao":
            print(f"   endpoint : {pcfg.get('endpoint')}")
            print(f"   appKey   : {pcfg.get('app_key')}  (secret: {mask_secret(str(pcfg.get('app_secret', '')))})")
            print(f"   批量限制 : 多行 q，≤{pcfg.get('batch_max_lines')} 行 / ≤{pcfg.get('batch_max_chars')} 字符每请求")
        billing = pcfg.get("billing") or {}
        if billing:
            free = f"，月免费 {billing.get('free_chars_per_month'):,}" if billing.get("free_chars_per_month") else ""
            print(f"   计费     : {billing.get('price')} {billing.get('currency')}/百万字符{free}")
        if name in (cfg.get("paid_providers") or []):
            print("   ! 付费层 : 批量使用前需 --allow-paid，且会产生真实费用")
        print("")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    order = parse_provider_list(args.providers, get_default_order(cfg))
    stats = Stats()
    protector = PlaceholderProtector(cfg)
    pool = ProviderPool(cfg, stats, order, args.src, args.dst)
    rows = []
    eprint(f"[check] 逐家健康检查，文本 {args.text!r}（约 {len(args.text)} 字符/provider）")
    for name in order:
        provider = pool.providers[name]
        t0 = time.time()
        try:
            out = provider.translate_batch([args.text])
            restored, ph_err = protector.restore(out[0], [])
            rows.append({"provider": name, "ok": ph_err is None, "translated": restored,
                         "error": ph_err, "elapsed_s": round(time.time() - t0, 3)})
        except ProviderError as exc:
            rows.append({"provider": name, "ok": False, "translated": None,
                         "error": f"{type(exc).__name__}: {exc}", "elapsed_s": round(time.time() - t0, 3)})
        print(json.dumps(rows[-1], ensure_ascii=False))
    ok_count = sum(1 for r in rows if r["ok"])
    eprint(f"[check] {ok_count}/{len(rows)} 家可用")
    return 0 if ok_count else 4


def cmd_text(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    order = parse_provider_list(args.providers, get_default_order(cfg))
    stats = Stats()
    protector = PlaceholderProtector(cfg)
    cache = Cache(Path(args.cache_file).expanduser() if args.cache_file else None,
                  enabled=bool(args.cache_file))
    pool = ProviderPool(cfg, stats, order, args.src, args.dst)
    t0 = time.time()
    try:
        protected = protector.protect(args.text)
        out, provider = pool.translate([protected.text])
        restored, ph_err = protector.restore(out[0], protected.tokens)
        payload = {
            "provider": provider,
            "src": args.src,
            "dst": args.dst,
            "source": args.text,
            "protected": protected.text,
            "translated": restored,
            "placeholder_error": ph_err,
            "elapsed_s": round(time.time() - t0, 3),
            "stats": stats.summary(cfg, time.time() - t0),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if ph_err is None else 1
    except AllProvidersFailed as exc:
        eprint(f"[text] 失败: {exc}")
        return 4
    finally:
        cache.flush(force=True)


def cmd_translate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    in_path = Path(args.input).expanduser()
    out_path = Path(args.output).expanduser()
    if in_path.resolve() == out_path.resolve():
        raise ConfigError("--in 与 --out 不能是同一个文件")
    input_jsonl = is_jsonl(in_path)
    out_jsonl = output_is_jsonl(out_path, input_jsonl)
    if input_jsonl and out_path.suffix.lower() == ".txt":
        out_jsonl = False

    order = parse_provider_list(args.providers, get_default_order(cfg))
    for name in order:
        get_provider_cfg(cfg, name)
    stats = Stats()
    protector = PlaceholderProtector(cfg)
    cache_path = None
    if not args.no_cache:
        cache_path = (Path(args.cache_file).expanduser() if args.cache_file
                      else resolve_path(cfg.get("cache_path") or "work/mt-cache.json"))
    cache = Cache(cache_path, enabled=not args.no_cache)

    texts = read_input_texts(in_path, None, args.field, args.limit or None)
    stats.records = len(texts)
    unique_texts = list(dict.fromkeys(texts))
    stats.unique_texts = len(unique_texts)

    # 断点续跑：解析已有输出
    resume_done: dict[str, str] = {}
    if out_path.is_file() and not args.overwrite:
        resume_done, _existing_lines = scan_output(out_path, None, args.field, out_jsonl)
        if resume_done:
            eprint(f"[resume] 检测到已完成输出 {len(resume_done)} 条，将跳过这些原文: {out_path}")
    stats.output_hits = len(resume_done)

    # 预计算待翻译量（cache/输出/空值之后）
    pending: list[str] = []
    seen: set[str] = set()
    for text in unique_texts:
        if text == "" or not text.strip():
            continue
        if text in resume_done:
            continue
        if cache.enabled and cache.get(args.src, args.dst, text) is not None:
            continue
        if text in seen:
            continue
        seen.add(text)
        pending.append(text)
    pending_chars = sum(len(protector.protect(t).text) for t in pending)

    eprint(f"[plan] 记录 {stats.records} 条 / 唯一原文 {stats.unique_texts} 条 / "
           f"待翻译 {len(pending)} 条 / 约 {pending_chars:,} 字符（保护后）")
    print_estimate(cfg, order, pending_chars)

    if args.max_chars and pending_chars > args.max_chars:
        eprint(f"[拒绝] 待翻译 {pending_chars:,} 字符超过 --max-chars {args.max_chars:,}")
        return 2

    if args.dry_run:
        eprint("[dry-run] 未调用任何 API。")
        summary = stats.summary(cfg, 0.0)
        summary["pending_texts"] = len(pending)
        summary["pending_chars"] = pending_chars
        summary["order"] = order
        if args.stats_out:
            stats_path = Path(args.stats_out)
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            stats_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    paid_in_order = [n for n in order if n in (cfg.get("paid_providers") or [])]
    threshold = int(cfg.get("paid_confirm_chars", 50000))
    if (not args.allow_paid) and paid_in_order and pending_chars > threshold:
        eprint(f"[付费保护] 本次将使用付费 provider {paid_in_order}，待翻译 {pending_chars:,} 字符 > 阈值 {threshold:,}")
        eprint("  如确认付费请加 --allow-paid；想零费用可改用 --providers azure_f0,youdao")
        return 3

    pool = ProviderPool(cfg, stats, order, args.src, args.dst, delay=args.delay)
    sched = cfg.get("scheduler") or {}
    t0 = time.time()
    try:
        results = run_translation(
            unique_texts,
            protector=protector,
            cache=cache,
            pool=pool,
            stats=stats,
            src=args.src,
            dst=args.dst,
            on_fail=args.on_fail,
            work_unit_items=int(sched.get("work_unit_items", 100)),
            work_unit_chars=int(sched.get("work_unit_chars", 20000)),
            concurrency=args.concurrency,
            verbose=args.verbose,
        )
    finally:
        cache.flush(force=True)

    # 输出（重写整份文件，保证断点续跑不重复）
    final_results: dict[str, Translation] = {}
    for text in unique_texts:
        if text in resume_done:
            final_results[text] = Translation(text, resume_done[text], "(resume)", None)
        elif text in results:
            final_results[text] = results[text]
        else:
            final_results[text] = Translation(text, text if args.on_fail == "source" else None,
                                              None, "missing_result")
    write_output(in_path, out_path, texts, final_results,
                 src=args.src, dst=args.dst, field_name=args.field,
                 out_jsonl=out_jsonl, input_jsonl=input_jsonl,
                 write_value=args.write_value, on_fail=args.on_fail)

    elapsed = time.time() - t0
    summary = stats.summary(cfg, elapsed)
    summary["output"] = str(out_path)
    summary["resume_done"] = len(resume_done)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.stats_out:
        stats_path = Path(args.stats_out)
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    eprint(f"[done] 输出: {out_path}  成功 {stats.ok} / 失败 {stats.failed} / "
           f"缓存命中 {stats.cache_hits} / 续跑 {len(resume_done)} / 耗时 {elapsed:.1f}s")
    failures = summary["failed"]
    return 0 if failures == 0 else (0 if summary["ok"] > 0 else 4)


def output_is_jsonl(out_path: Path, input_jsonl: bool) -> bool:
    suffix = out_path.suffix.lower()
    if suffix == ".jsonl":
        return True
    if suffix == ".txt":
        return False
    return input_jsonl


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv: Sequence[str] | None = None) -> int:
    _reconfigure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        eprint(f"[配置错误] {exc}")
        return 2
    except AllProvidersFailed as exc:
        eprint(f"[失败] {exc}")
        return 4
    except KeyboardInterrupt:
        eprint("\n[中断] 已停止；缓存已尽量保存。重跑同一条命令即可续跑。")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
