"""
PromptSlim — AI 提示词瘦身工具包
从源头减少 Token 消耗，支持多模型、中英文。
"""

__version__ = "0.1.0"

from .compressor import quick_slim, smart_slim
from .tokenizer import count_tokens, cost_estimate, count_tokens_batch
from .redundancy import strip_redundancy
from .reporter import SlimReport
