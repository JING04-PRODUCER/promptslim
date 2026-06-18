"""
RAG 记忆存储与检索 — 基于嵌入向量的语义记忆
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class MemoryEntry:
    id: str
    content: str
    vector: list[float]
    metadata: dict = field(default_factory=dict)


class MemoryStore:
    """简易向量存储 — 余弦相似度检索"""

    def __init__(self):
        self._entries: list[MemoryEntry] = []

    def add(self, entry_id: str, content: str, vector: list[float], metadata: dict | None = None):
        self._entries.append(MemoryEntry(
            id=entry_id,
            content=content,
            vector=vector,
            metadata=metadata or {},
        ))

    def search(self, query_vector: list[float], top_k: int = 5) -> list[MemoryEntry]:
        """余弦相似度检索"""
        if not self._entries:
            return []
        vecs = np.array([e.vector for e in self._entries])
        q = np.array(query_vector)
        # 归一化
        vecs_norm = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        scores = vecs_norm @ q_norm
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [self._entries[i] for i in top_idx if scores[i] > 0.3]

    def clear(self):
        self._entries.clear()

    def __len__(self):
        return len(self._entries)


class AgentMemory:
    """Agent 记忆管理器"""

    def __init__(self, base_url: str, api_key: str, model: str = "text-embedding-3-small"):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.store = MemoryStore()

    async def _embed(self, text: str) -> list[float]:
        """调用嵌入 API 生成向量"""
        import httpx

        url = f"{self.base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": text}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
            raise RuntimeError(f"Embedding API error: {resp.status_code}")

    async def remember(self, content: str, metadata: dict | None = None):
        """存储记忆"""
        import uuid
        vector = await self._embed(content)
        entry_id = metadata.get("id") if metadata else None
        self.store.add(entry_id or uuid.uuid4().hex[:12], content, vector, metadata)

    async def recall(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """语义检索相关记忆"""
        q_vec = await self._embed(query)
        return self.store.search(q_vec, top_k)

    async def recall_as_context(self, query: str, top_k: int = 5) -> str:
        """以文本格式返回检索结果，可直接注入 prompt"""
        entries = await self.recall(query, top_k)
        if not entries:
            return ""
        lines = ["## 相关记忆 (RAG)"]
        for i, e in enumerate(entries, 1):
            lines.append(f"{i}. {e.content}")
        return "\n".join(lines)


# 全局单例
memory_store: AgentMemory | None = None


def init_memory(base_url: str, api_key: str, model: str = "text-embedding-3-small") -> AgentMemory:
    global memory_store
    memory_store = AgentMemory(base_url, api_key, model)
    return memory_store
