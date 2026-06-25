"""Token 计数与成本估算"""

from __future__ import annotations

import re

import tiktoken

_enc_cache = {}
_zh = re.compile(r"[\u4e00-\u9fff]")
_en = re.compile(r"[a-zA-Z0-9]+")

COST = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-7": (15.00, 75.00),
    "claude-haiku-4-5": (0.80, 4.00),
    "deepseek-chat": (0.27, 1.10),
    "deepseek-reasoner": (0.55, 2.19),
    "qwen-plus": (0.80, 2.80),
    "qwen-turbo": (0.30, 0.60),
    "qwen-max": (2.40, 9.60),
    "default": (1.00, 3.00),
}


def _enc(model: str) -> tiktoken.Encoding:
    name = "cl100k_base"
    if "o200k" in model.lower() or "gpt-4o" in model.lower():
        name = "o200k_base"
    if name not in _enc_cache:
        _enc_cache[name] = tiktoken.get_encoding(name)
    return _enc_cache[name]


def count(text: str, model: str = "gpt-4o") -> int:
    return len(_enc(model).encode(text))


def count_batch(texts: list[str], model: str = "gpt-4o") -> list[int]:
    enc = _enc(model)
    return [len(enc.encode(t)) for t in texts]


def est_zh(text: str) -> int:
    zh = len(_zh.findall(text))
    en = len(_en.findall(text))
    return int(zh / 1.5 + en / 4)


def cost(model: str, input_t: int, output_t: int) -> float:
    in_c, out_c = COST.get(model, COST["default"])
    return input_t * in_c / 1e6 + output_t * out_c / 1e6
