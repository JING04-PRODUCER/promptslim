"""
工作流编排引擎 - 支持顺序/并行多 Agent 调度
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from agents.base import BaseAgent, AgentStatus
from config import get_settings


@dataclass
class WorkflowStep:
    """工作流中的一步"""
    agent: BaseAgent
    depends_on: list[str] = field(default_factory=list)  # 依赖步骤的名称
    step_name: str = ""


class WorkflowEngine:
    """支持 DAG 依赖的工作流编排引擎"""

    def __init__(self):
        settings = get_settings()
        self.max_concurrent = settings.max_concurrent_agents
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def run_sequential(self, agents: list[BaseAgent], task: str) -> list[dict]:
        """顺序执行多个 Agent"""
        results = []
        for agent in agents:
            result = await agent.run(task)
            results.append({"agent": agent.config.name, "result": result})
            if not result.get("success"):
                results.append({"warning": "Stopping workflow due to agent failure"})
                break
        return results

    async def run_parallel(self, agents: list[BaseAgent], task: str) -> list[dict]:
        """并行执行多个 Agent（独立任务）"""
        async def _run_one(agent: BaseAgent):
            async with self.semaphore:
                result = await agent.run(task)
                return {"agent": agent.config.name, "result": result}

        return await asyncio.gather(*[_run_one(a) for a in agents])

    async def run_dag(self, steps: list[WorkflowStep], initial_task: str) -> dict[str, dict]:
        """按 DAG 依赖执行工作流"""
        results: dict[str, dict] = {}
        running: dict[str, asyncio.Task] = {}

        pending = list(steps)

        while pending:
            # 找出所有依赖已满足的步骤
            ready = [
                s for s in pending
                if all(dep in results for dep in s.depends_on)
            ]

            if not ready and not running:
                raise RuntimeError("Workflow deadlock: unresolved dependencies")

            # 并行执行就绪步骤
            async def _execute_step(step: WorkflowStep):
                async with self.semaphore:
                    # 将前置步骤的输出拼入 task 上下文
                    context = {
                        dep: results[dep]["result"]
                        for dep in step.depends_on
                        if dep in results
                    }
                    task_with_context = f"{initial_task}\n\nContext from previous steps:\n{context}"
                    return step.step_name, await step.agent.run(task_with_context, context)

            ready_tasks = [_execute_step(s) for s in ready]
            for s in ready:
                pending.remove(s)

            batch_results = await asyncio.gather(*ready_tasks)
            for step_name, result in batch_results:
                results[step_name] = result

        return results


# 全局工作流引擎
workflow_engine = WorkflowEngine()
