"""Agent 编排核心"""

from __future__ import annotations
import os
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tools.registry import ToolRegistry
from memory.rag import RAGMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tool_registry = ToolRegistry()
rag_memory = RAGMemory()


class AgentConfig(BaseModel):
    name: str
    model: str = "gpt-4o"
    system_prompt: str = ""
    tools: list[str] = []
    max_iterations: int = 5


class TaskRequest(BaseModel):
    task: str
    context: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await tool_registry.load_tools()
    logger.info("Agent Core 启动")
    yield
    logger.info("Agent Core 关闭")


app = FastAPI(title="Agent Core", version="0.1.0", lifespan=lifespan)


@app.post("/agents")
async def create_agent(config: AgentConfig):
    for tool_name in config.tools:
        if not tool_registry.has_tool(tool_name):
            raise HTTPException(status_code=400, detail=f"工具 {tool_name} 不存在")
    return {"status": "ok", "agent": config.dict()}


@app.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str, request: TaskRequest):
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise HTTPException(status_code=500, detail="未配置 OPENAI_API_KEY")

    relevant = await rag_memory.recall(request.task)
    messages = [
        {"role": "system", "content": "你是一个有用的 AI 助手。"},
        {"role": "user", "content": f"{request.task}\n\n相关上下文：{relevant}"},
    ]

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o",
                "messages": messages,
                "tools": tool_registry.get_openai_tools(),
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"LLM 调用失败: {resp.text}")
        data = resp.json()
        return {
            "status": "ok",
            "response": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
        }


@app.get("/health")
async def health():
    return {"status": "ok", "tools": len(tool_registry.list_tools())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
