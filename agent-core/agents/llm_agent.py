"""
LLM Agent - 基于 OpenAI 兼容 API 的大模型推理 Agent
支持 Function Calling、工具自动选择、重试机制
"""

import json
import asyncio
from typing import Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from agents.base import BaseAgent, AgentConfig, AgentEvent, AgentStatus
from tools.registry import tool_registry
from config import get_settings


class ToolTimeoutError(Exception):
    """工具调用超时异常"""

    pass


class LLMAgent(BaseAgent):
    """基于 LLM 的 Function Calling Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.llm_model
        self.tool_timeout = settings.tool_timeout_seconds
        self.max_retries = settings.tool_max_retries
        self.retry_backoff = settings.tool_retry_backoff

    async def run(self, task: str, context: Optional[dict] = None) -> dict:
        """执行 Agent 任务的主循环"""
        self.status = AgentStatus.RUNNING
        self._iteration_count = 0
        self.events.clear()

        self.add_event("start", f"Agent {self.config.name} starting task: {task}")

        messages = self._build_messages(task)

        try:
            while self._should_continue():
                self._iteration_count += 1

                # 构建可用工具列表
                available_tools = [t for t in self.config.tools if tool_registry.get(t)]
                openai_tools = None
                if available_tools:
                    # 从注册中心获取工具的 OpenAI 格式
                    all_tool_defs = tool_registry.to_openai_tools()
                    openai_tools = [t for t in all_tool_defs if t["function"]["name"] in available_tools]

                # 调用 LLM
                response = await self._call_llm(messages, openai_tools)
                assistant_msg = response.choices[0].message

                # 无工具调用 → 最终回复
                if not assistant_msg.tool_calls:
                    final_text = assistant_msg.content or ""
                    self.add_event("final", final_text)
                    self.add_to_history("assistant", final_text)
                    self.status = AgentStatus.COMPLETED
                    return {"success": True, "result": final_text, "iterations": self._iteration_count}

                # 处理工具调用
                for tool_call in assistant_msg.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    self.add_event("tool_call", f"Calling {tool_name}", args=tool_args)
                    self.add_to_history("assistant", f"[Tool Call: {tool_name}]")

                    # 执行工具 (带超时和重试)
                    tool_result = await self._execute_tool_with_retry(tool_name, tool_args)
                    self.add_event("tool_result", str(tool_result))

                    # 将工具结果反馈给 LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })

            # 达到最大迭代次数
            self.status = AgentStatus.FAILED
            return {"success": False, "error": "Max iterations exceeded", "iterations": self._iteration_count}

        except ToolTimeoutError as e:
            self.status = AgentStatus.TIMEOUT
            self.add_event("timeout", str(e))
            return {"success": False, "error": f"Tool timeout: {str(e)}", "iterations": self._iteration_count}

        except Exception as e:
            self.status = AgentStatus.FAILED
            self.add_event("error", str(e))
            return {"success": False, "error": str(e), "iterations": self._iteration_count}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception_type((ToolTimeoutError, ConnectionError, TimeoutError)),
    )
    async def _call_llm(self, messages: list[dict], tools: Optional[list[dict]] = None):
        """调用 LLM API (带自动重试)"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return await self.client.chat.completions.create(**kwargs)

    async def _execute_tool_with_retry(self, tool_name: str, args: dict) -> dict:
        """执行工具调用 (带超时 + 重试)"""
        entry = tool_registry.get(tool_name)
        if not entry:
            return {"error": f"Unknown tool: {tool_name}"}

        meta, handler = entry

        for attempt in range(self.max_retries):
            try:
                # 超时保护
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(handler(**args), timeout=self.tool_timeout)
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(handler, **args), timeout=self.tool_timeout
                    )
                return {"tool": tool_name, "result": result, "attempt": attempt + 1}

            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    delay = self.retry_backoff ** attempt
                    self.add_event("retry", f"{tool_name} timeout, retry {attempt + 1}/{self.max_retries} in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    raise ToolTimeoutError(f"{tool_name} timed out after {self.max_retries} retries")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_backoff ** attempt
                    await asyncio.sleep(delay)
                else:
                    return {"tool": tool_name, "error": str(e), "attempt": attempt + 1}

        return {"tool": tool_name, "error": "Max retries exceeded"}
