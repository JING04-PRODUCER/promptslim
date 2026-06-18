"""智能压缩 — 保留语义的去冗余压缩"""

from __future__ import annotations

from .redundancy import strip_redundancy
from .reporter import SlimReport


def quick_slim(
    text: str,
    model: str = "gpt-4o",
    cache_messages: list[dict] | None = None,
) -> SlimReport:
    """快速瘦身：仅规则去冗余，离线执行无需 API

    Args:
        text: 待瘦身文本
        model: 模型名
        cache_messages: 可选的消息列表，用于分析缓存节省潜力
    """
    slimmed, _, _ = strip_redundancy(text)
    cache_analysis = None
    if cache_messages is not None:
        from .cache import analyze_messages
        cache_analysis = analyze_messages(cache_messages, model)
    return SlimReport(text, slimmed, model, cache_analysis=cache_analysis)


def smart_slim(
    text: str | list[dict],
    model: str = "gpt-4o",
    max_output_tokens: int = 2048,
    base_url: str | None = None,
    api_key: str | None = None,
) -> SlimReport:
    """智能瘦身：调用 LLM 压缩文本，保留核心语义

    Args:
        text: 纯文本 或 OpenAI 格式的 messages 列表
        model: 模型名
        max_output_tokens: 压缩后最大 token 数
        base_url: API 地址（默认从环境变量读取）
        api_key: API 密钥（默认从环境变量读取）
    """
    import os

    base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    if isinstance(text, list):
        original = "\n".join(m.get("content", "") for m in text)
        messages = text + [{
            "role": "system",
            "content": f"将以上对话历史压缩为不超过 {max_output_tokens} tokens 的摘要，保留所有关键信息、决策和上下文。输出纯摘要内容。"
        }]
    else:
        original = text
        messages = [
            {"role": "system", "content": "你是一个文本压缩工具。将以下文本压缩为更短的版本，保留所有关键信息。只输出压缩后的文本。"},
            {"role": "user", "content": text},
        ]

    # 先用规则快速去冗余
    quick, _, _ = strip_redundancy(original)

    try:
        import httpx

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_output_tokens,
            "temperature": 0.1,
        }

        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            slimmed = data["choices"][0]["message"]["content"]
            return SlimReport(original, slimmed.strip(), model)

    except Exception:
        pass

    # API 不可用时回退到规则瘦身
    return SlimReport(original, quick, model)
