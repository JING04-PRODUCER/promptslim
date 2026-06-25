"""OpenAI SDK monkey-patch — 一行代码自动压缩所有 prompt"""

from __future__ import annotations

import functools
import logging

logger = logging.getLogger(__name__)

_original_create = None
_original_async_create = None
_patched = False


def patch_openai(aggressive: bool = False):
    """安装 monkey-patch：自动压缩所有 OpenAI SDK 发出的消息

    import promptslim
    promptslim.patch_openai()

    # 之后所有调用自动压缩
    client = OpenAI()
    client.chat.completions.create(model="gpt-4o", messages=[...])
    """
    global _patched
    if _patched:
        return

    from .compressor import looks_like_code, strip_text

    def _compress_messages(messages: list[dict]) -> list[dict]:
        compressed = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                role = msg.get("role", "")
                if role == "system":
                    compressed.append(msg)
                elif not looks_like_code(content):
                    compressed.append({**msg, "content": strip_text(content)})
                else:
                    compressed.append(msg)
            else:
                compressed.append(msg)
        return compressed

    try:
        from openai.resources.chat.completions import Completions

        _original_create = Completions.create

        @functools.wraps(_original_create)
        def _patched_create(self, **kwargs):
            if "messages" in kwargs:
                kwargs["messages"] = _compress_messages(kwargs["messages"])
            return _original_create(self, **kwargs)

        Completions.create = _patched_create
    except ImportError:
        pass

    try:
        from openai.resources.chat.completions import AsyncCompletions

        _original_async_create = AsyncCompletions.create

        @functools.wraps(_original_async_create)
        async def _patched_async_create(self, **kwargs):
            if "messages" in kwargs:
                kwargs["messages"] = _compress_messages(kwargs["messages"])
            return await _original_async_create(self, **kwargs)

        AsyncCompletions.create = _patched_async_create
    except ImportError:
        pass

    _patched = True
    logger.info("PromptSlim patch 已安装 — OpenAI SDK 调用将自动压缩")


def unpatch_openai():
    """卸载 monkey-patch，恢复原始行为"""
    global _patched
    if not _patched:
        return

    try:
        from openai.resources.chat.completions import Completions

        if _original_create:
            Completions.create = _original_create
    except ImportError:
        pass

    try:
        from openai.resources.chat.completions import AsyncCompletions

        if _original_async_create:
            AsyncCompletions.create = _original_async_create
    except ImportError:
        pass

    _patched = False
    logger.info("PromptSlim patch 已卸载")
