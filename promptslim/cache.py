"""Anthropic Prompt Caching 分析 — 标记可缓存区域，估算缓存节省

Anthropic Prompt Caching 定价:
  - 缓存写入: 基础 input 价格 × 1.25
  - 缓存读取: 基础 input 价格 × 0.10
  - TTL: 5 分钟 (ephemeral)
  - 最大断点数: 4
  - 最小可缓存: ~1024 tokens (Opus 4.7 建议 ≥4096)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from .tokenizer import count_tokens
from .reporter import MODEL_COST_PER_TOKEN

# 缓存定价系数
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10

# 缓存 TTL (秒)
CACHE_TTL_SECONDS = 300

# 最小可缓存 token 数
MIN_CACHEABLE_TOKENS = 1024
MIN_CACHEABLE_TOKENS_OPUS = 4096

# 最大 cache_control 断点数
MAX_BREAKPOINTS = 4


@dataclass
class CacheAnalysis:
    """Prompt 缓存分析报告"""

    model: str
    total_tokens: int
    cacheable_tokens: int
    uncacheable_tokens: int
    cacheable_blocks: list[dict]
    breakpoints_used: int
    # 费用估算 (单次调用)
    cost_without_cache: float   # 无缓存时的 input 费用
    cost_first_call: float      # 首次调用 (缓存写入)
    cost_cached_call: float     # 缓存命中后单次费用
    savings_per_cached_call: float  # 每次缓存命中节省

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "cacheable_tokens": self.cacheable_tokens,
            "uncacheable_tokens": self.uncacheable_tokens,
            "cacheable_blocks": len(self.cacheable_blocks),
            "breakpoints_used": self.breakpoints_used,
            "cost_without_cache_usd": round(self.cost_without_cache, 6),
            "cost_first_call_usd": round(self.cost_first_call, 6),
            "cost_cached_call_usd": round(self.cost_cached_call, 6),
            "savings_per_cached_call_usd": round(self.savings_per_cached_call, 6),
            "cache_write_multiplier": CACHE_WRITE_MULTIPLIER,
            "cache_read_multiplier": CACHE_READ_MULTIPLIER,
            "ttl_seconds": CACHE_TTL_SECONDS,
        }

    def savings_over_n_calls(self, n: int, first_call_included: bool = True) -> float:
        """估算 N 次调用的总缓存节省 (含首次写入)"""
        if n <= 1:
            return 0.0
        if first_call_included:
            # 首次写入 + (n-1) 次缓存命中
            total_without = self.cost_without_cache * n
            total_with = self.cost_first_call + self.cost_cached_call * (n - 1)
            return round(total_without - total_with, 6)
        else:
            return round(self.savings_per_cached_call * n, 6)

    def savings_pct_per_call(self) -> float:
        """缓存命中后单次节省百分比"""
        if self.cost_without_cache <= 0:
            return 0.0
        return round(self.savings_per_cached_call / self.cost_without_cache * 100, 1)


def analyze_messages(
    messages: list[dict],
    model: str = "claude-opus-4-7",
    min_cacheable: int | None = None,
) -> CacheAnalysis:
    """分析 messages 列表，识别可缓存部分并估算节省

    Args:
        messages: OpenAI 格式消息列表 [{"role": "...", "content": "..."}]
        model: 模型名
        min_cacheable: 最小可缓存 token 阈值，默认自动选择

    Returns:
        CacheAnalysis 报告

    缓存策略:
      1. system prompt → 最先缓存 (最稳定)
      2. 静态 tool 定义 → 可缓存
      3. 历史对话中较早的 assistant 消息 → 可缓存 (如果足够长)
      4. 最近的 user/assistant 消息 → 不缓存
    """
    if min_cacheable is None:
        min_cacheable = MIN_CACHEABLE_TOKENS_OPUS if "opus" in model.lower() else MIN_CACHEABLE_TOKENS

    input_cost = _get_input_cost(model)
    total_tokens = 0
    cacheable_tokens = 0
    cacheable_blocks = []
    breakpoints_used = 0

    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        tokens = count_tokens(content, model)
        total_tokens += tokens

        can_cache = False
        reason = ""

        if role == "system":
            # system prompt 是最理想的缓存目标
            if tokens >= min_cacheable:
                can_cache = True
                reason = "system_prompt"
        elif role == "assistant" and i < len(messages) - 2:
            # 较早的 assistant 回复，且后面还有多轮对话
            if tokens >= min_cacheable and breakpoints_used < MAX_BREAKPOINTS - 1:
                can_cache = True
                reason = "early_assistant"
        elif role == "tool" and i < len(messages) - 3:
            # tool 调用结果，较早期
            if tokens >= min_cacheable and breakpoints_used < MAX_BREAKPOINTS - 1:
                can_cache = True
                reason = "tool_result"

        if can_cache and breakpoints_used < MAX_BREAKPOINTS:
            cacheable_tokens += tokens
            breakpoints_used += 1
            cacheable_blocks.append({
                "index": i,
                "role": role,
                "tokens": tokens,
                "reason": reason,
                "preview": content[:80] + "..." if len(content) > 80 else content,
            })

    uncacheable_tokens = total_tokens - cacheable_tokens

    # 费用计算
    cost_without_cache = round(total_tokens * input_cost, 6)
    # 首次: 缓存部分 × 1.25 + 非缓存部分 × 1.0
    cost_first_call = round(cacheable_tokens * input_cost * CACHE_WRITE_MULTIPLIER
                            + uncacheable_tokens * input_cost, 6)
    # 命中: 缓存部分 × 0.1 + 非缓存部分 × 1.0
    cost_cached_call = round(cacheable_tokens * input_cost * CACHE_READ_MULTIPLIER
                             + uncacheable_tokens * input_cost, 6)
    savings_per_call = round(cost_without_cache - cost_cached_call, 6)

    return CacheAnalysis(
        model=model,
        total_tokens=total_tokens,
        cacheable_tokens=cacheable_tokens,
        uncacheable_tokens=uncacheable_tokens,
        cacheable_blocks=cacheable_blocks,
        breakpoints_used=breakpoints_used,
        cost_without_cache=cost_without_cache,
        cost_first_call=cost_first_call,
        cost_cached_call=cost_cached_call,
        savings_per_cached_call=max(savings_per_call, 0),
    )


def build_cached_messages(
    messages: list[dict],
    model: str = "claude-opus-4-7",
    min_cacheable: int | None = None,
) -> tuple[list[dict], CacheAnalysis]:
    """为 messages 添加 Anthropic cache_control 断点

    返回 (带缓存标记的 Anthropic 格式 messages, 分析报告)

    输出格式适配 Anthropic Messages API:
      - system 转为顶层参数
      - content 转为 content block 列表
      - 缓存块添加 cache_control: {"type": "ephemeral"}
    """
    analysis = analyze_messages(messages, model, min_cacheable)
    cache_indices = {b["index"] for b in analysis.cacheable_blocks}

    cached = []
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        block = {"type": "text", "text": content}
        if i in cache_indices:
            block["cache_control"] = {"type": "ephemeral"}
        cached.append({"role": msg.get("role", "user"), "content": [block]})

    return cached, analysis


def estimate_cache_savings(
    messages: list[dict],
    model: str = "claude-opus-4-7",
    calls_per_window: int = 3,
) -> dict:
    """快速估算在 5 分钟缓存窗口内的节省

    Args:
        messages: 消息列表
        model: 模型名
        calls_per_window: 5 分钟内预计调用次数

    Returns:
        包含 savings 摘要的 dict
    """
    analysis = analyze_messages(messages, model)
    total_saved = analysis.savings_over_n_calls(calls_per_window)

    return {
        "model": model,
        "cacheable_tokens": analysis.cacheable_tokens,
        "total_tokens": analysis.total_tokens,
        "cacheable_pct": round(analysis.cacheable_tokens / analysis.total_tokens * 100, 1)
        if analysis.total_tokens > 0 else 0,
        "savings_per_call_usd": analysis.savings_per_cached_call,
        "savings_pct_per_call": analysis.savings_pct_per_call(),
        "calls_per_window": calls_per_window,
        "total_savings_in_window_usd": total_saved,
        "ttl_seconds": CACHE_TTL_SECONDS,
    }


def _get_input_cost(model: str) -> float:
    """获取模型 input token 单价"""
    cost_info = MODEL_COST_PER_TOKEN.get(model, MODEL_COST_PER_TOKEN["default"])
    return cost_info["input"]
