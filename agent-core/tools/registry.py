"""工具注册表"""

from __future__ import annotations
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolParameter:
    """工具参数描述"""
    name: str
    type: str
    description: str
    required: bool = False


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    category: str = ""
    timeout_seconds: int = 30
    max_retries: int = 1


@dataclass
class Tool:
    """简单工具描述（函数签名自动推断）"""
    name: str
    description: str
    func: Callable
    parameters: dict


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._entries: dict[str, tuple[ToolMetadata, Callable]] = {}

    def reset(self):
        """重置所有工具注册（用于测试）"""
        self._tools.clear()
        self._entries.clear()

    async def load_tools(self):
        """加载所有工具"""
        # 内置函数式工具
        from .builtin import read_file, execute_sql, web_search
        self.register(read_file)
        self.register(execute_sql)
        self.register(web_search)

        # 元数据式工具（导入时自动注册）
        try:
            from .file_reader import read_file as _rf  # noqa: F811
        except ImportError:
            pass
        try:
            from .sql_query import execute_sql as _es  # noqa: F811
        except ImportError:
            pass
        try:
            from .web_search import web_search as _ws  # noqa: F811
        except ImportError:
            pass

    def register(self, meta_or_func, handler=None):
        """注册工具 - 支持两种方式:

        1. register(func) - 函数签名自动推断参数
        2. register(meta, handler) - 使用 ToolMetadata + 处理函数
        """
        if handler is not None:
            # 元数据 + 处理器方式
            meta = meta_or_func
            self._entries[meta.name] = (meta, handler)
            # 同时在 _tools 中也存储一份 OpenAPI 兼容格式
            params = {
                "type": "object",
                "properties": {
                    p.name: {"type": p.type, "description": p.description}
                    for p in meta.parameters
                },
                "required": [p.name for p in meta.parameters if p.required],
            }
            self._tools[meta.name] = Tool(
                name=meta.name,
                description=meta.description,
                func=handler,
                parameters=params,
            )
        else:
            # 函数签名推断方式
            func = meta_or_func
            sig = inspect.signature(func)
            doc = inspect.getdoc(func) or ""
            self._tools[func.__name__] = Tool(
                name=func.__name__,
                description=doc.split("\n")[0] if doc else "",
                func=func,
                parameters={
                    "type": "object",
                    "properties": {n: {"type": "string"} for n in sig.parameters},
                    "required": [
                        n for n, p in sig.parameters.items()
                        if p.default == inspect.Parameter.empty
                    ],
                },
            )

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get(self, name: str) -> tuple[ToolMetadata, Callable] | None:
        """兼容旧 API：返回 (meta, handler) 或 None"""
        if name in self._entries:
            return self._entries[name]
        tool = self._tools.get(name)
        if tool:
            # 从 Tool 自动构建 ToolMetadata
            params = [
                ToolParameter(
                    name=n,
                    type=p.get("type", "string"),
                    description=p.get("description", ""),
                    required=n in tool.parameters.get("required", []),
                )
                for n, p in tool.parameters.get("properties", {}).items()
            ]
            meta = ToolMetadata(
                name=tool.name,
                description=tool.description,
                parameters=params,
            )
            return (meta, tool.func)
        return None

    def to_openai_tools(self) -> list[dict]:
        """兼容旧 API：返回 OpenAI Function Calling 格式"""
        return self.get_openai_tools()

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def list(self, category: str | None = None) -> list[ToolMetadata]:
        """列出工具，支持按类别过滤"""
        metas = []
        for name in self._tools:
            entry = self.get(name)
            if entry:
                meta, _ = entry
                if category is None or meta.category == category:
                    metas.append(meta)
        return metas

    def get_openai_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"工具 {name} 不存在")
        handler = tool.func
        if inspect.iscoroutinefunction(handler):
            return await handler(**kwargs)
        return handler(**kwargs)


# 模块级工具注册中心实例
tool_registry = ToolRegistry()
