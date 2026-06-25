"""
PromptSlim — AI 提示词瘦身工具包
从源头减少 Token 消耗，支持多模型、中英文、Prompt Caching。
"""

__version__ = "0.4.1"

from .cache import CacheReport, analyze  # noqa: F401
from .compressor import CompressReport, quick_slim, smart_compress, strip_text  # noqa: F401
from .patch import patch_openai, unpatch_openai  # noqa: F401
from .tokenizer import COST, cost, count, count_batch, est_zh  # noqa: F401
