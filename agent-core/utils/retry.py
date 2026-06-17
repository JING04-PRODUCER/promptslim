"""
通用重试工具 - 指数退避、抖动、条件重试
"""

import asyncio
import random
import functools
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
):
    """
    通用重试装饰器，支持指数退避 + 随机抖动

    使用示例:
        @with_retry(max_attempts=3, retryable_exceptions=(TimeoutError, ConnectionError))
        async def call_api(url: str): ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (backoff_multiplier ** attempt), max_delay)
                        if jitter:
                            delay *= random.uniform(0.5, 1.5)
                        await asyncio.sleep(delay)
            raise last_exception  # type: ignore

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (backoff_multiplier ** attempt), max_delay)
                        if jitter:
                            delay *= random.uniform(0.5, 1.5)
                        import time
                        time.sleep(delay)
            raise last_exception  # type: ignore

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
