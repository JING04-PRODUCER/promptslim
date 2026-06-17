"""
Agent 模块集成测试 - 使用百炼 API (qwen-plus)
"""
from __future__ import annotations

import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置百炼 API
os.environ.setdefault("OPENAI_API_KEY", "sk-ws-H.REPMMPD.YY6S.MEQCIF3XAMIciVIYF7CLTne19PdWXxB0_73hznQJx-dVFYspAiA42uASWTUxPXvA7FJ7cnICsU396hMwj1HkpddtQ94qCw")
os.environ.setdefault("OPENAI_BASE_URL", "https://ws-eq9tcvlhw5m65ftm.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
os.environ.setdefault("LLM_MODEL", "qwen-plus")

from agents.base import AgentConfig, AgentStatus
from agents.llm_agent import LLMAgent
from tools.registry import tool_registry


class TestAgentConfig:
    """Agent 配置测试"""

    def test_default_config(self):
        config = AgentConfig(name="test")
        assert config.max_iterations == 10
        assert config.temperature == 0.7
        assert config.tools == []

    def test_custom_config(self):
        config = AgentConfig(
            name="analyst",
            description="数据分析师",
            system_prompt="你是一个数据分析专家",
            tools=["execute_sql", "list_tables"],
            max_iterations=5,
            temperature=0.3,
        )
        assert config.name == "analyst"
        assert len(config.tools) == 2
        assert config.max_iterations == 5


class TestLLMAgent:
    """LLM Agent 集成测试 (调用真实 API)"""

    def test_simple_chat(self):
        """测试简单对话（无工具调用）"""
        config = AgentConfig(
            name="helper",
            system_prompt="你是一个有帮助的助手，回答要简洁。",
            tools=[],
            max_iterations=3,
        )
        agent = LLMAgent(config)
        result = asyncio.run(agent.run("请用一句话回答：1+1等于几？"))

        assert result["success"] is True
        content = str(result["result"]).lower()
        assert "2" in content or "二" in content
        assert result["iterations"] <= 3
        assert agent.status == AgentStatus.COMPLETED

    def test_agent_with_tools(self):
        """测试带工具调用的 Agent"""
        config = AgentConfig(
            name="file-reader-agent",
            system_prompt="你是一个文件处理助手。当用户要求读取文件时，使用 read_file 工具。",
            tools=["read_file"],
            max_iterations=5,
        )
        agent = LLMAgent(config)
        result = asyncio.run(agent.run("请读取 C:/Windows/System32/drivers/etc/hosts 文件的内容（如果存在）"))

        assert result["success"] is True
        assert len(agent.events) > 0
        tool_events = [e for e in agent.events if e.event_type == "tool_call"]
        assert len(tool_events) >= 1

    def test_events_recording(self):
        """测试事件记录功能"""
        config = AgentConfig(
            name="event-test",
            system_prompt="你是一个助手",
            tools=[],
            max_iterations=2,
        )
        agent = LLMAgent(config)
        asyncio.run(agent.run("说hello"))

        assert len(agent.events) > 0
        assert agent.events[0].event_type == "start"
        final_events = [e for e in agent.events if e.event_type == "final"]
        assert len(final_events) >= 1

    def test_max_iterations(self):
        """测试达到最大迭代次数时正确退出"""
        config = AgentConfig(
            name="loop-test",
            system_prompt="你是一个助手。无论用户问什么，先调用 read_file 读取任意文件，再回答。",
            tools=["read_file"],
            max_iterations=2,
        )
        agent = LLMAgent(config)
        result = asyncio.run(agent.run("今天的天气怎么样？"))

        assert "iterations" in result
        assert result["iterations"] <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
