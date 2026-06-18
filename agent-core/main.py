"""
AgentOrchestrator - Python Agent Core

FastAPI 服务入口，提供：
- Agent 创建与执行 API
- 工具注册与发现 API
- 工作流编排 API
- 健康检查与状态监控
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_settings
from agents.base import AgentConfig, AgentStatus
from agents.llm_agent import LLMAgent
from tools.registry import tool_registry
from orchestration.workflow import WorkflowStep, workflow_engine
from utils.logger import setup_logger
from memory.rag import memory_store, init_memory

# ==================== 数据模型 ====================

class CreateAgentRequest(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = "You are a helpful AI assistant."
    tools: list[str] = []
    max_iterations: int = 10
    temperature: float = 0.7

class RunAgentRequest(BaseModel):
    agent_name: str
    task: str

class WorkflowRequest(BaseModel):
    agents: list[str]  # Agent 名称列表
    task: str
    mode: str = "sequential"  # sequential, parallel

class AgentInfo(BaseModel):
    name: str
    status: str
    description: str
    tools: list[str]


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    settings = get_settings()
    from loguru import logger
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title="AgentOrchestrator Core",
    version="0.1.0",
    description="跨语言 AI Agent 调度平台 - Python 推理核心",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Agent 运行时存储 ====================
_agents: dict[str, LLMAgent] = {}


# 注册内置工具
import tools.web_search  # noqa: E402 — 导入时自动注册

# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "model": settings.llm_model,
        "tools_count": len(tool_registry.list()),
    }


# ==================== 工具 API ====================

@app.get("/api/tools")
async def list_tools(category: Optional[str] = None):
    """列出所有可用工具"""
    return {"tools": tool_registry.list(category)}


@app.get("/api/tools/{tool_name}")
async def get_tool(tool_name: str):
    """获取单个工具的详细信息"""
    entry = tool_registry.get(tool_name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    meta, _ = entry
    return {
        "name": meta.name,
        "description": meta.description,
        "category": meta.category,
        "parameters": [
            {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
            for p in meta.parameters
        ],
    }


# ==================== Agent API ====================

@app.post("/api/agents", status_code=201)
async def create_agent(req: CreateAgentRequest):
    """创建一个 Agent 实例"""
    config = AgentConfig(
        name=req.name,
        description=req.description,
        system_prompt=req.system_prompt,
        tools=req.tools,
        max_iterations=req.max_iterations,
        temperature=req.temperature,
    )
    agent = LLMAgent(config)
    _agents[req.name] = agent
    return {"message": f"Agent '{req.name}' created", "tools": req.tools}


@app.get("/api/agents")
async def list_agents():
    """列出所有已创建的 Agent"""
    return {
        "agents": [
            AgentInfo(
                name=a.config.name,
                status=a.status.value,
                description=a.config.description,
                tools=a.config.tools,
            )
            for a in _agents.values()
        ]
    }


@app.get("/api/agents/{agent_name}")
async def get_agent(agent_name: str):
    """获取 Agent 详情"""
    agent = _agents.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {
        "name": agent.config.name,
        "status": agent.status.value,
        "description": agent.config.description,
        "tools": agent.config.tools,
        "history": agent.history[-10:],  # 最近 10 条
        "events": [
            {"type": e.event_type, "content": e.content, "time": e.timestamp}
            for e in agent.events[-20:]  # 最近 20 条事件
        ],
    }


@app.post("/api/agents/{agent_name}/run")
async def run_agent(agent_name: str, req: RunAgentRequest):
    """执行 Agent 任务"""
    agent = _agents.get(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")
    result = await agent.run(req.task)
    return result


@app.delete("/api/agents/{agent_name}")
async def delete_agent(agent_name: str):
    """删除 Agent"""
    if agent_name not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    del _agents[agent_name]
    return {"message": f"Agent '{agent_name}' deleted"}


# ==================== 工作流 API ====================

@app.post("/api/workflows")
async def run_workflow(req: WorkflowRequest):
    """执行多 Agent 工作流"""
    agents = []
    for name in req.agents:
        agent = _agents.get(name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
        agents.append(agent)

    if req.mode == "parallel":
        results = await workflow_engine.run_parallel(agents, req.task)
    else:
        results = await workflow_engine.run_sequential(agents, req.task)

    return {"mode": req.mode, "agents": req.agents, "results": results}


# ==================== Memory / RAG API ====================

class RememberRequest(BaseModel):
    content: str
    metadata: dict | None = None


class RecallRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/api/memory/init")
async def init_memory_endpoint():
    """初始化 RAG 记忆系统"""
    settings = get_settings()
    global memory_store
    memory_store = init_memory(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
    return {"message": "Memory system initialized", "model": "text-embedding-3-small"}


@app.post("/api/memory/remember")
async def remember(req: RememberRequest):
    """存储记忆"""
    if memory_store is None:
        raise HTTPException(status_code=400, detail="Memory not initialized. POST /api/memory/init first")
    await memory_store.remember(req.content, req.metadata)
    return {"message": "Memory stored"}


@app.post("/api/memory/recall")
async def recall(req: RecallRequest):
    """检索相关记忆"""
    if memory_store is None:
        raise HTTPException(status_code=400, detail="Memory not initialized")
    entries = await memory_store.recall(req.query, req.top_k)
    return {"results": [{"id": e.id, "content": e.content, "metadata": e.metadata} for e in entries]}


@app.post("/api/memory/recall-context")
async def recall_context(req: RecallRequest):
    """检索并返回可注入 prompt 的文本"""
    if memory_store is None:
        raise HTTPException(status_code=400, detail="Memory not initialized")
    context = await memory_store.recall_as_context(req.query, req.top_k)
    return {"context": context}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
