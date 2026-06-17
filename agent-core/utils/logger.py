"""
日志配置 - 结构化日志、自动轮转、多级别输出
"""

import sys
from loguru import logger
from config import get_settings


def setup_logger() -> None:
    """配置全局日志"""
    settings = get_settings()

    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.debug else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
    )

    # 文件输出 (ERROR 级别)
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )

    # 文件输出 (全量)
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        level="INFO",
        rotation="50 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
    )


setup_logger()
