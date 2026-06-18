"""多模型 Tokenizer — 支持 GPT / Claude / DeepSeek / 百炼"""

from __future__ import annotations

import tiktoken

# OpenAI / Anthropic / DeepSeek 常用编码
# gpt-4o/gpt-4-turbo/gpt-3.5-turbo: cl100k_base
# claude 系列近似用 cl100k_base（编码风格接近）
# deepseek 近似用 cl100k_base
ENCODINGS = {
    "gpt-4o": "cl100k_base",
    "gpt-4o-mini": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "o4-mini": "o200k_base",
    "o3": "o200k_base",
    "claude-sonnet-4-6": "cl100k_base",
    "claude-haiku-4-5": "cl100k_base",
    "claude-opus-4-7": "cl100k_base",
    "deepseek-chat": "cl100k_base",
    "deepseek-reasoner": "cl100k_base",
    "qwen-plus": "cl100k_base",
    "qwen-max": "cl100k_base",
    "qwen-turbo": "cl100k_base",
}

# 中文 Token 估算系数（约 1.5~2 字符 = 1 token，中文用 cl100k 大约是 1.3~1.6）
ZH_CHAR_PER_TOKEN = 1.5

_caches: dict[str, tiktoken.Encoding] = {}


def _get_encoding(model: str) -> tiktoken.Encoding:
    enc_name = ENCODINGS.get(model, "cl100k_base")
    if enc_name not in _caches:
        _caches[enc_name] = tiktoken.get_encoding(enc_name)
    return _caches[enc_name]


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """精确计数文本的 Token 数量"""
    enc = _get_encoding(model)
    return len(enc.encode(text))


def estimate_zh_tokens(text: str) -> int:
    """快速估算中文 Token 数（不加载模型，适合大文本粗略估算）"""
    zh_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return int(zh_chars / ZH_CHAR_PER_TOKEN)


def count_tokens_batch(texts: list[str], model: str = "gpt-4o") -> list[int]:
    """批量计数"""
    enc = _get_encoding(model)
    tokens = enc.encode_ordinary_batch(texts)
    return [len(t) for t in tokens]


def cost_estimate(text: str, model: str, is_input: bool = True) -> float:
    """快速费用估算"""
    from .reporter import MODEL_COST_PER_TOKEN

    tokens = count_tokens(text, model)
    cost_info = MODEL_COST_PER_TOKEN.get(model, MODEL_COST_PER_TOKEN["default"])
    rate = cost_info["input"] if is_input else cost_info["output"]
    return round(tokens * rate, 6)
