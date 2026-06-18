"""
PromptSlim — AI 提示词瘦身工具包
从源头减少 Token 消耗，支持多模型、中英文、Prompt Caching。
"""

__version__ = "0.3.1"

from .compressor import quick_slim, smart_slim
from .tokenizer import count_tokens, cost_estimate, count_tokens_batch
from .redundancy import strip_redundancy, strip_redundancy_en, strip_redundancy_zh
from .reporter import SlimReport
from .cache import (
    CacheAnalysis,
    analyze_messages,
    build_cached_messages,
    estimate_cache_savings,
    CACHE_WRITE_MULTIPLIER,
    CACHE_READ_MULTIPLIER,
    CACHE_TTL_SECONDS,
)
