"""工具注册表"""

from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: dict


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    async def load_tools(self):
        from .builtin import read_file, execute_sql, web_search
        self.register(read_file)
        self.register(execute_sql)
        self.register(web_search)

    def register(self, func: Callable):
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

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

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
        if inspect.iscoroutinefunction(tool.func):
            return await tool.func(**kwargs)
        return tool.func(**kwargs)
