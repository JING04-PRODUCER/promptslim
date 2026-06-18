"""
工作流引擎单元测试
"""
from __future__ import annotations

import os
import sys
import pytest
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("OPENAI_API_KEY", "dummy")
os.environ.setdefault("OPENAI_BASE_URL", "https://dummy.example.com/v1")
os.environ.setdefault("LLM_MODEL", "qwen-plus")

from agents.base import BaseAgent, AgentConfig, AgentStatus
from orchestration.workflow import WorkflowEngine, WorkflowStep


class MockAgent(BaseAgent):
    """用于测试的模拟 Agent"""

    def __init__(self, config: AgentConfig, response: dict = None):
        super().__init__(config)
        self._response = response or {"success": True, "result": f"Mock response from {config.name}"}

    async def run(self, task, context=None):
        self.status = AgentStatus.RUNNING
        self._iteration_count = 1
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.status = AgentStatus.COMPLETED
        return self._response


class TestWorkflowEngine:
    """工作流引擎测试"""

    def test_sequential(self):
        agents = [
            MockAgent(AgentConfig(name="step1")),
            MockAgent(AgentConfig(name="step2")),
            MockAgent(AgentConfig(name="step3")),
        ]

        engine = WorkflowEngine()
        results = asyncio.run(engine.run_sequential(agents, "test task"))

        assert len(results) == 3
        assert results[0]["agent"] == "step1"
        assert results[1]["agent"] == "step2"
        assert results[2]["agent"] == "step3"

    def test_parallel(self):
        agents = [
            MockAgent(AgentConfig(name="worker_a")),
            MockAgent(AgentConfig(name="worker_b")),
            MockAgent(AgentConfig(name="worker_c")),
        ]

        engine = WorkflowEngine()
        results = asyncio.run(engine.run_parallel(agents, "parallel task"))

        assert len(results) == 3
        names = {r["step"] for r in results}
        assert names == {"worker_a", "worker_b", "worker_c"}

    def test_dag_workflow(self):
        """测试 DAG 依赖工作流"""
        agent_a = MockAgent(AgentConfig(name="collector"), {"success": True, "result": "data collected"})
        agent_b = MockAgent(AgentConfig(name="analyzer"), {"success": True, "result": "analysis done"})
        agent_c = MockAgent(AgentConfig(name="reporter"), {"success": True, "result": "report generated"})

        steps = [
            WorkflowStep(agent=agent_a, step_name="collect", depends_on=[]),
            WorkflowStep(agent=agent_b, step_name="analyze", depends_on=["collect"]),
            WorkflowStep(agent=agent_c, step_name="report", depends_on=["analyze"]),
        ]

        engine = WorkflowEngine()
        results = asyncio.run(engine.run_dag(steps, "full pipeline"))

        assert "collect" in results
        assert "analyze" in results
        assert "report" in results
        assert results["collect"]["success"] is True

    def test_sequential_stops_on_failure(self):
        """顺序模式：第一个失败后停止"""
        agents = [
            MockAgent(AgentConfig(name="ok_step")),
            MockAgent(AgentConfig(name="fail_step"), {"success": False, "error": "something wrong"}),
            MockAgent(AgentConfig(name="skipped_step")),
        ]

        engine = WorkflowEngine()
        results = asyncio.run(engine.run_sequential(agents, "task"))

        # 前两个执行了，第三个被跳过
        assert len(results) >= 2
        assert results[0]["agent"] == "ok_step"
        assert results[1]["agent"] == "fail_step"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
