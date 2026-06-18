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


class WorkflowError(Exception):
    """工作流执行异常"""
    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message)
        self.errors = errors or []


class WorkflowEngine:
    """支持 DAG 依赖的工作流编排引擎"""

    def __init__(self):
        settings = get_settings()
        self.max_concurrent = settings.max_concurrent_agents
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    def _detect_cycle(self, steps: list[WorkflowStep]) -> bool:
        """使用 DFS 三色标记法检测有向图中的环"""
        graph = {}
        all_nodes = set()
        for s in steps:
            graph[s.step_name] = set(s.depends_on)
            all_nodes.add(s.step_name)
            all_nodes.update(s.depends_on)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in all_nodes}

        def dfs(node: str) -> bool:
            if node not in color:
                return False
            color[node] = GRAY
            for neighbor in graph.get(node, set()):
                if color.get(neighbor, BLACK) == GRAY:
                    return True
                if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for node in all_nodes:
            if color.get(node, WHITE) == WHITE and dfs(node):
                return True
        return False

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
        """并行执行多个 Agent（独立任务），失败不中断其他 Agent"""
        results = []
        errors = []

        async def _run_one(agent: BaseAgent):
            try:
                async with self.semaphore:
                    result = await agent.run(task)
                    results.append({"step": agent.config.name, "status": "success", "output": result})
            except Exception as e:
                errors.append({"step": agent.config.name, "error": str(e)})
                results.append({"step": agent.config.name, "status": "failed", "error": str(e)})

        await asyncio.gather(*[_run_one(a) for a in agents])

        if errors:
            raise WorkflowError(
                f"Parallel execution: {len(errors)}/{len(agents)} steps failed",
                errors=errors
            )
        return results

    async def run_dag(self, steps: list[WorkflowStep], initial_task: str) -> dict[str, dict]:
        """按 DAG 依赖执行工作流"""
        if self._detect_cycle(steps):
            raise WorkflowError("DAG contains a cycle, cannot execute")

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
                raise WorkflowError("Workflow deadlock: unresolved dependencies")

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
