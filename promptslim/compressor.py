"""文本压缩器"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

import httpx

from .tokenizer import cost, count

logger = logging.getLogger(__name__)

_REPEAT = re.compile(r"(.{10,})\1{2,}")
_BLANK = re.compile(r"\n{3,}")
_SPACE = re.compile(r" {2,}")
_DUP_PUNCT = re.compile(r"([！!？?。.，,])\1+")
_CODE_SIGNS = [
    re.compile(r"^\s*(def |class |import |from |return |func |var |let |const )", re.M),
    re.compile(r"[{}\[\]]"),
    re.compile(r"->\s*\w"),
]


def looks_like_code(text: str) -> bool:
    if not text.strip():
        return False
    zh = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if len(text) > 0 and zh / len(text) > 0.3:
        return False
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    code_lines = sum(1 for line in lines if any(p.search(line) for p in _CODE_SIGNS))
    if code_lines / len(lines) > 0.5:
        return True
    non_empty = [line for line in lines if line.strip()]
    if len(non_empty) >= 3:
        indented = sum(1 for line in non_empty if line.startswith(("    ", "\t")))
        if indented / len(non_empty) > 0.4:
            return True
    return False


def strip_text(text: str) -> str:
    if not text or looks_like_code(text):
        return text
    seen = set()
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if s and s not in seen:
            seen.add(s)
            lines.append(line)
        elif not s:
            lines.append(line)
    result = "\n".join(lines)
    result = _BLANK.sub("\n\n", result)
    result = _SPACE.sub(" ", result)
    result = _DUP_PUNCT.sub(r"\1", result)
    return result


def smart_compress(
    text: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
    base_url: str = "",
    api_key: str = "",
) -> str:
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError("需要 API 密钥")
    cleaned = strip_text(text)
    try:
        if looks_like_code(cleaned):
            sys_prompt = "你是代码摘要助手。保留关键逻辑、API 接口，删除冗余注释和示例。"
        else:
            sys_prompt = "你是文本压缩助手。保留所有关键信息，删除冗余表达。"
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"压缩以下文本到{max_tokens} tokens以内：\n\n{cleaned}"},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            compressed = resp.json()["choices"][0]["message"]["content"].strip()
            if len(compressed) < len(cleaned):
                return compressed
        return cleaned
    except Exception as e:
        logger.warning(f"LLM 压缩失败: {e}")
        return cleaned


@dataclass
class CompressReport:
    original: str
    compressed: str
    model: str
    metadata: dict = field(default_factory=dict)

    @property
    def original_tokens(self) -> int:
        return count(self.original, self.model)

    @property
    def compressed_tokens(self) -> int:
        return count(self.compressed, self.model)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return round(self.tokens_saved / self.original_tokens * 100, 1)

    @property
    def cost_saved(self) -> float:
        return cost(self.model, self.tokens_saved, 0)

    def to_dict(self) -> dict:
        return {
            "original_chars": len(self.original),
            "compressed_chars": len(self.compressed),
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "tokens_saved": self.tokens_saved,
            "savings_pct": self.savings_pct,
            "cost_saved_usd": round(self.cost_saved, 6),
            "model": self.model,
        }


def quick_slim(text: str, model: str = "gpt-4o") -> CompressReport:
    """快速瘦身：仅规则去冗余，离线执行无需 API"""
    cleaned = strip_text(text)
    return CompressReport(original=text, compressed=cleaned, model=model)
