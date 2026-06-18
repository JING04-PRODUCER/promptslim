"""
工具注册中心 - 管理所有可用工具的注册、发现和元数据
"""

from __future__ import annotations

from typing import Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[str] = None


@dataclass
class ToolMetadata:
    """工具元数据，描述一个可被 Agent 调用的工具"""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    version: str = "0.1.0"
    author: str = ""
    category: str = "general"  # file, database, web, system, custom
    timeout_seconds: int = 30
    max_retries: int = 3


class ToolRegistry:
    """全局工具注册中心 (单例)"""

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}  # 实例变量
        return cls._instance

    def reset(self) -> None:
        """重置注册中心 (仅用于测试)"""
        self._tools = {}

    def register(self, metadata: ToolMetadata, handler: Callable) -> None:
        """注册一个工具"""
        self._tools[metadata.name] = (metadata, handler)

    def get(self, name: str) -> Optional[tuple[ToolMetadata, Callable]]:
        """获取工具元数据和处理器"""
        return self._tools.get(name)

    def list(self, category: Optional[str] = None) -> list[dict]:
        """列出所有已注册工具（可按分类过滤）"""
        result = []
        for meta, _ in self._tools.values():
            if category and meta.category != category:
                continue
            result.append({
                "name": meta.name,
                "description": meta.description,
                "category": meta.category,
                "parameters": [
                    {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                    for p in meta.parameters
                ],
            })
        return result

    def to_openai_tools(self) -> list[dict]:
        """转换为 OpenAI function calling 格式"""
        tools = []
        for meta, _ in self._tools.values():
            properties = {}
            required = []
            for p in meta.parameters:
                properties[p.name] = {"type": p.type, "description": p.description}
                if p.required:
                    required.append(p.name)

            tools.append({
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            })
        return tools


# 全局单例
tool_registry = ToolRegistry()
