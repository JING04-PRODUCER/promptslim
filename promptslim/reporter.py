"""费用报告 — 模型价格表 ，压缩前后对比"""

from __future__ import annotations

# 每 Token 成本（USD），从 1M 定价换算而来
MODEL_COST_PER_TOKEN = {
    "gpt-4o": {"input": 0.0000025, "output": 0.00001},
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    "gpt-4-turbo": {"input": 0.00001, "output": 0.00003},
    "gpt-4": {"input": 0.00003, "output": 0.00006},
    "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
    "o4-mini": {"input": 0.0000011, "output": 0.0000044},
    "o3": {"input": 0.00001, "output": 0.00004},
    "claude-sonnet-4-6": {"input": 0.000003, "output": 0.000015},
    "claude-haiku-4-5": {"input": 0.0000008, "output": 0.000004},
    "claude-opus-4-7": {"input": 0.000015, "output": 0.000075},
    "deepseek-chat": {"input": 0.00000027, "output": 0.0000011},
    "deepseek-reasoner": {"input": 0.00000055, "output": 0.00000219},
    "qwen-plus": {"input": 0.0000008, "output": 0.0000028},
    "qwen-max": {"input": 0.0000024, "output": 0.0000096},
    "qwen-turbo": {"input": 0.0000003, "output": 0.0000006},
    "default": {"input": 0.000001, "output": 0.000004},
}


class SlimReport:
    """瘦身报告，可选附带缓存分析"""

    def __init__(self, original: str, slimmed: str, model: str, cache_analysis=None):
        from .tokenizer import count_tokens

        self.model = model
        self.original = original
        self.slimmed = slimmed
        self.original_len = len(original)
        self.slimmed_len = len(slimmed)
        self.original_tokens = count_tokens(original, model)
        self.slimmed_tokens = count_tokens(slimmed, model)

        self.chars_saved = self.original_len - self.slimmed_len
        self.tokens_saved = self.original_tokens - self.slimmed_tokens

        if self.original_tokens > 0:
            self.savings_pct = round(self.tokens_saved / self.original_tokens * 100, 1)
        else:
            self.savings_pct = 0.0

        cost = MODEL_COST_PER_TOKEN.get(model, MODEL_COST_PER_TOKEN["default"])
        self.cost_per_call_saved = round(self.tokens_saved * cost["input"], 6)

        # 缓存分析 (可选)
        self.cache = cache_analysis

    def to_dict(self) -> dict:
        d = {
            "model": self.model,
            "original_chars": self.original_len,
            "slimmed_chars": self.slimmed_len,
            "original_tokens": self.original_tokens,
            "slimmed_tokens": self.slimmed_tokens,
            "tokens_saved": self.tokens_saved,
            "savings_pct": self.savings_pct,
            "cost_per_call_saved_usd": self.cost_per_call_saved,
        }
        if self.cache is not None:
            d["cache"] = self.cache.to_dict()
            d["total_savings_with_cache_usd"] = round(
                self.cost_per_call_saved + self.cache.savings_per_cached_call, 6
            )
        return d
