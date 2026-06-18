# AgentOrchestrator 🤖

**跨语言 AI Agent 调度平台 — Python FastAPI 推理核心 + Java Spring Boot 管理面板。分钟级构建带工具调用、多 Agent 工作流和可视化管理的 LLM Agent。**

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/java-21-orange.svg)](https://adoptium.net/)
[![Spring Boot](https://img.shields.io/badge/spring--boot-3.4-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/arch-cross--language-blueviolet)]()
![Category](https://img.shields.io/badge/category-ai--agent%20|%20llm--orchestration%20|%20tool--calling-orange)

> 🤖 **AI Agent · LLM 调度 · Function Calling · 多 Agent 工作流**

> [English](README.md)

## 为什么选择 AgentOrchestrator？

| 问题 | 现有方案 | 本项目 |
|------|----------|--------|
| Python 擅长 LLM 推理，但企业级管理弱 | FastAPI 缺乏内置管理后台 | FastAPI 推理 + Spring Boot 管理 |
| Java 生态成熟，但 LLM 整合碎片化 | Spring AI 仍在演进 | REST 桥接 Python LLM 能力 |
| Agent 框架锁定特定模型 | 多数绑定 OpenAI | OpenAI 兼容协议——任意模型 |
| 多 Agent 编排缺乏可见性 | 纯代码配置 | REST API + Web UI 路线图 |

## 架构

```
┌─────────────────────────────────────────────────┐
│           管理服务 (Spring Boot)                  │
│  Agent CRUD · 任务调度 · 监控                    │
│                    port 9090                     │
└────────────────────────┬────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────┐
│          Agent 核心 (Python FastAPI)             │
│  LLM Agent · 工具调用 · 重试 · 工作流             │
│                    port 8000                     │
└───────┬────────────┬────────────┬───────────────┘
        │            │            │
   ┌────▼───┐  ┌─────▼────┐ ┌───▼───────┐
   │ OpenAI │  │ 本地     │ │ PostgreSQL│
   │兼容接口│  │ 工具     │ │  + Redis  │
   └────────┘  └──────────┘ └───────────┘
```

## 快速开始

### 前置条件

- Python 3.12+
- Java 21+
- Docker & Docker Compose（推荐）
- OpenAI 兼容 API Key

### Docker（推荐）

```bash
git clone https://github.com/JING04-PRODUCER/agent-orchestrator.git
cd agent-orchestrator
cp .env.example .env  # 编辑并添加 OPENAI_API_KEY
docker compose up -d

# 验证
curl http://localhost:8000/health              # Agent 核心
curl http://localhost:9090/api/admin/health     # 管理服务
```

### 本地开发

```bash
# Agent 核心 (Python)
cd agent-core
pip install -r requirements.txt
python main.py                 # http://localhost:8000

# 管理服务 (Java)
cd admin-server
./mvnw spring-boot:run         # http://localhost:9090
```

## 核心功能

### 创建并运行 Agent

```bash
# 创建
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "system_prompt": "你是一位代码审查专家...",
    "tools": ["read_file", "execute_sql"],
    "max_iterations": 5
  }'

# 执行
curl -X POST http://localhost:8000/api/agents/code-reviewer/run \
  -H "Content-Type: application/json" \
  -d '{"task": "审查 app.py 的安全问题"}'
```

### 多 Agent 工作流

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["analyzer", "reviewer", "tester"],
    "task": "分析此项目的代码质量",
    "mode": "sequential"
  }'
```

## 内置工具

| 工具 | 描述 | 分类 |
|------|------|:----:|
| `read_file` | 多编码文件读取 (txt/json/csv/md) | file |
| `execute_sql` | 安全参数化 SQL 查询（仅 SELECT） | database |
| `list_tables` | 数据库结构查看 | database |
| `web_search` | DuckDuckGo 网页搜索（免费，无需 API Key） | web |

> 通过插件注册中心扩展——分钟级添加自定义工具。

## RAG 记忆系统

```bash
# 初始化记忆
curl -X POST http://localhost:8000/api/memory/init

# 存储上下文
curl -X POST http://localhost:8000/api/memory/remember \
  -H "Content-Type: application/json" \
  -d '{"content": "认证模块使用 JWT，密钥轮换周期为 7 天...", "metadata": {"topic": "auth"}}'

# 语义检索
curl -X POST http://localhost:8000/api/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "登录是怎么实现的？"}'
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| AI 推理 | Python FastAPI + OpenAI SDK | LLM 调用、Function Calling |
| 工具系统 | 插件注册 + asyncio | 超时控制、自动重试 |
| 工作流 | DAG 编排 + 并行调度 | 多 Agent 协同 |
| 管理后台 | Java 21 + Spring Boot 3.4 | REST API、JPA |
| 存储 | PostgreSQL 16 + Redis 7 | 状态持久化、缓存 |
| 部署 | Docker Compose | 一行启动 |

## 路线图

- [x] LLM Agent 核心（OpenAI 兼容）
- [x] 工具注册与调用
- [x] 多 Agent 工作流引擎
- [x] Spring Boot 管理后台
- [x] Web Search 工具（DuckDuckGo）
- [x] RAG 记忆系统
- [ ] Web UI 仪表盘 (Vue 3)
- [ ] Code Executor 工具
- [ ] MCP 协议支持
- [ ] 监控告警 (Prometheus + Grafana)

## 参与贡献

欢迎 Issue 和 PR！详见[贡献指南](docs/PLAN2-CONTRIBUTION-GUIDE.md)。

## 许可证

MIT — 详见 [LICENSE](LICENSE)
