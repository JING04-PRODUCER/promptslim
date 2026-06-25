"""Anthropic Prompt Caching 分析"""

from __future__ import annotations

from dataclasses import dataclass

from .tokenizer import cost, count

CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.10
CACHE_TTL = 300
MIN_CACHE_TOKENS = 1024
MAX_BREAKPOINTS = 4


@dataclass
class CacheReport:
    model: str
    total_tokens: int
    cacheable_tokens: int
    blocks: list[dict]
    breakpoints: int

    @property
    def cacheable_pct(self) -> float:
        if self.total_tokens == 0:
            return 0.0
        return round(self.cacheable_tokens / self.total_tokens * 100, 1)

    @property
    def cost_without_cache(self) -> float:
        return cost(self.model, self.total_tokens, 0)

    @property
    def cost_first_call(self) -> float:
        uncacheable = self.total_tokens - self.cacheable_tokens
        return cost(self.model, int(self.cacheable_tokens * CACHE_WRITE_MULT), 0) + \
               cost(self.model, uncacheable, 0)

    @property
    def cost_cached_call(self) -> float:
        uncacheable = self.total_tokens - self.cacheable_tokens
        return cost(self.model, int(self.cacheable_tokens * CACHE_READ_MULT), 0) + \
               cost(self.model, uncacheable, 0)

    @property
    def savings_per_call(self) -> float:
        return round(self.cost_without_cache - self.cost_cached_call, 6)

    @property
    def savings_pct(self) -> float:
        if self.cost_without_cache == 0:
            return 0.0
        return round(self.savings_per_call / self.cost_without_cache * 100, 1)

    def savings_n_calls(self, n: int) -> float:
        if n <= 1:
            return 0.0
        total_without = self.cost_without_cache * n
        total_with = self.cost_first_call + self.cost_cached_call * (n - 1)
        return round(total_without - total_with, 6)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "cacheable_tokens": self.cacheable_tokens,
            "cacheable_pct": self.cacheable_pct,
            "blocks": len(self.blocks),
            "breakpoints": self.breakpoints,
            "cost_without_cache_usd": round(self.cost_without_cache, 6),
            "cost_first_call_usd": round(self.cost_first_call, 6),
            "cost_cached_call_usd": round(self.cost_cached_call, 6),
            "savings_per_call_usd": round(self.savings_per_call, 6),
            "savings_pct": self.savings_pct,
            "ttl_seconds": CACHE_TTL,
        }


def analyze(messages: list[dict], model: str = "claude-opus-4-7") -> CacheReport:
    total = 0
    cacheable = 0
    blocks = []
    bps = 0
    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        tokens = count(content, model)
        total += tokens
        can_cache = False
        reason = ""
        if role == "system" and tokens >= MIN_CACHE_TOKENS:
            can_cache = True
            reason = "system"
        elif role == "assistant" and i < len(messages) - 2:
            if tokens >= MIN_CACHE_TOKENS and bps < MAX_BREAKPOINTS - 1:
                can_cache = True
                reason = "early_assistant"
        elif role == "tool" and i < len(messages) - 3:
            if tokens >= MIN_CACHE_TOKENS and bps < MAX_BREAKPOINTS - 1:
                can_cache = True
                reason = "tool_result"
        if can_cache and bps < MAX_BREAKPOINTS:
            cacheable += tokens
            bps += 1
            blocks.append({"index": i, "role": role, "tokens": tokens, "reason": reason})
    return CacheReport(
        model=model,
        total_tokens=total,
        cacheable_tokens=cacheable,
        blocks=blocks,
        breakpoints=bps,
    )
