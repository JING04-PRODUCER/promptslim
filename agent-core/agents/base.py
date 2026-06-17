"""
Agent 基类 - 定义所有 Agent 的通用接口和生命周期
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentConfig:
    """Agent 通用配置"""
    name: str
    description: str = ""
    max_iterations: int = 10
    timeout_seconds: int = 300
    temperature: float = 0.7
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)  # 工具名称列表


@dataclass
class AgentEvent:
    """Agent 执行过程中产生的事件"""
    agent_name: str
    event_type: str  # "thought", "action", "tool_call", "tool_result", "final"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.history: list[dict] = []
        self.events: list[AgentEvent] = []
        self._iteration_count = 0

    @abstractmethod
    async def run(self, task: str, context: Optional[dict] = None) -> dict:
        """执行 Agent 任务，返回结果字典"""
        ...

    def add_event(self, event_type: str, content: str, **metadata) -> None:
        """记录执行事件"""
        self.events.append(AgentEvent(
            agent_name=self.config.name,
            event_type=event_type,
            content=content,
            metadata=metadata,
        ))

    def add_to_history(self, role: str, content: str) -> None:
        """添加到对话历史"""
        self.history.append({"role": role, "content": content})

    def _build_messages(self, task: str) -> list[dict]:
        """构建 LLM 对话消息列表"""
        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.extend(self.history)
        messages.append({"role": "user", "content": task})
        return messages

    def _should_continue(self) -> bool:
        """判断是否应继续迭代"""
        return (
            self.status == AgentStatus.RUNNING
            and self._iteration_count < self.config.max_iterations
        )
