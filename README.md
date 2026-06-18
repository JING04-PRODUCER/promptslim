# AgentOrchestrator

**Cross-language AI Agent orchestration platform — Python FastAPI inference core + Java Spring Boot admin panel. Build LLM agents with tool calling, multi-agent workflows, and visual management in minutes.**

[🌐 English](README.md) | [中文](README_zh.md)

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/java-17-orange.svg)](https://adoptium.net/)
[![Spring Boot](https://img.shields.io/badge/spring--boot-3.4-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/arch-cross--language-blueviolet)]()
![Category](https://img.shields.io/badge/category-ai--agent%20|%20llm--orchestration%20|%20tool--calling-orange)

> 🤖 **AI Agent · LLM Orchestration · Function Calling · Multi-Agent Workflow**

## Why AgentOrchestrator?

| Problem | Existing Solutions | This Project |
|---------|-------------------|--------------|
| Python is great for LLM inference, weak for enterprise management | FastAPI lacks built-in admin | FastAPI inference + Spring Boot admin |
| Java ecosystem mature but LLM integration is fragmented | Spring AI still evolving | REST bridge to Python LLM capabilities |
| Agent frameworks lock you into specific models | Most bind to OpenAI | OpenAI-compatible protocol — any model works |
| Multi-agent orchestration lacks visibility | Code-only configuration | REST API with Web UI roadmap |

## Why AgentOrchestrator?

| Need | LangGraph | CrewAI | AgentOrchestrator |
|------|-----------|--------|-------------------|
| Python LLM inference | ✅ | ✅ | ✅ |
| Enterprise admin (RBAC, audit) | ❌ | ❌ | ✅ Spring Boot |
| Java ecosystem integration | ❌ | ❌ | ✅ |
| Visual workflow management | ❌ | ❌ | ✅ Roadmap |
| Multi-agent DAG workflow | ✅ | ✅ | ✅ |
| Tool plugin registry | ✅ | ✅ | ✅ |
| RAG memory system | ✅ | ✅ | ✅ |

## Architecture

```mermaid
graph TB
    Client[Client / SDK]
    Admin[Spring Boot Admin<br/>port :9090]
    Gateway[FastAPI Gateway<br/>port :8000]
    Orchestrator[Agent Orchestrator]
    Agent1[Agent 1]
    Agent2[Agent 2]
    ToolReg[Tool Registry]
    WebSearch[Web Search]
    FileReader[File Reader]
    SQLExec[SQL Executor]
    RAG[RAG Memory]
    DB[(PostgreSQL)]
    Redis[(Redis)]
    AI[OpenAI-compatible API]

    Client --> Admin
    Client --> Gateway
    Admin -->|REST API| Gateway
    Gateway --> Orchestrator
    Orchestrator --> Agent1
    Orchestrator --> Agent2
    Agent1 --> ToolReg
    Agent2 --> ToolReg
    ToolReg --> WebSearch
    ToolReg --> FileReader
    ToolReg --> SQLExec
    Agent1 --> RAG
    Agent2 --> RAG
    Gateway --> DB
    Gateway --> Redis
    Gateway --> AI
```

```
┌─────────────────────────────────────────────────┐
│           Admin Server (Spring Boot)             │
│  Agent CRUD · Task Scheduling · Monitoring       │
│                    port 9090                     │
└────────────────────────┬────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────┐
│          Agent Core (Python FastAPI)             │
│  LLM Agent · Tool Calling · Retry · Workflow     │
│                    port 8000                     │
└───────┬────────────┬────────────┬───────────────┘
        │            │            │
   ┌────▼───┐  ┌─────▼────┐ ┌───▼───────┐
   │ OpenAI │  │ Local    │ │ PostgreSQL│
   │Compat. │  │ Tools    │ │  + Redis  │
   └────────┘  └──────────┘ └───────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Java 21+
- Docker & Docker Compose (recommended)
- OpenAI-compatible API key

### Docker (recommended)

```bash
git clone https://github.com/JING04-PRODUCER/agent-orchestrator.git
cd agent-orchestrator
cp .env.example .env  # Edit and add your OPENAI_API_KEY
docker compose up -d

# Verify
curl http://localhost:8000/health       # Agent Core
curl http://localhost:9090/api/admin/health  # Admin Server
```

### Local Development

```bash
# Agent Core (Python)
cd agent-core
pip install -r requirements.txt
python main.py                 # http://localhost:8000

# Admin Server (Java)
cd admin-server
./mvnw spring-boot:run         # http://localhost:9090
```

## Core Features

### Create & Run an Agent

```bash
# Create
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "system_prompt": "You are a code review expert...",
    "tools": ["read_file", "execute_sql"],
    "max_iterations": 5
  }'

# Execute
curl -X POST http://localhost:8000/api/agents/code-reviewer/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Review app.py for security issues"}'
```

### Multi-Agent Workflow

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["analyzer", "reviewer", "tester"],
    "task": "Analyze code quality for this project",
    "mode": "sequential"
  }'
```

## Built-in Tools

| Tool | Description | Category |
|------|-------------|:--------:|
| `read_file` | Multi-encoding file reader (txt/json/csv/md) | file |
| `execute_sql` | Safe parameterized SQL queries (SELECT only) | database |
| `list_tables` | Database schema inspection | database |
| `web_search` | DuckDuckGo web search (free, no API key) | web |

> Extend via plugin registry — add your own tools in minutes.

## End-to-End Example

### 1. Create a Code Review Agent

```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "model": "claude-sonnet-4-6",
    "system_prompt": "You are a senior code reviewer. Focus on security, performance, and best practices.",
    "tools": ["read_file", "web_search"],
    "max_iterations": 5
  }'
```

### 2. Submit a Review Task

```bash
curl -X POST http://localhost:8000/api/agents/code-reviewer/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Review app.py for SQL injection and XSS vulnerabilities"}'
```

### 3. Check Results

```bash
curl http://localhost:8000/api/agents/code-reviewer/status
```

### 4. Multi-Agent Pipeline

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["analyzer", "code-reviewer", "tester"],
    "task": "Full code quality audit for the auth module",
    "mode": "sequential"
  }'
```

### 5. View in Dashboard

Open `http://localhost:9090` to see agents, tasks, and workflow status in the Spring Boot admin panel.

## RAG Memory System

```bash
# Initialize memory
curl -X POST http://localhost:8000/api/memory/init

# Store context
curl -X POST http://localhost:8000/api/memory/remember \
  -H "Content-Type: application/json" \
  -d '{"content": "The authentication module uses JWT...", "metadata": {"topic": "auth"}}'

# Semantic recall
curl -X POST http://localhost:8000/api/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "How does login work?"}'
```

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| AI Inference | Python FastAPI + OpenAI SDK | LLM calls, Function Calling |
| Tool System | Plugin registry + asyncio | Timeout control, auto-retry |
| Workflow | DAG orchestration + parallel scheduling | Multi-agent collaboration |
| Admin | Java 21 + Spring Boot 3.4 | REST API, JPA |
| Storage | PostgreSQL 16 + Redis 7 | State persistence, caching |
| Deployment | Docker Compose | One-command startup |

## Roadmap

- [x] LLM Agent core (OpenAI compatible)
- [x] Tool registry & invocation
- [x] Multi-agent workflow engine
- [x] Spring Boot admin backend
- [x] Web Search tool (DuckDuckGo)
- [x] RAG memory system
- [ ] Web UI dashboard (Vue 3)
- [ ] Code Executor tool
- [ ] MCP protocol support
- [ ] Monitoring & alerts (Prometheus + Grafana)

## Contributing

Issues and PRs welcome! See [contribution guide](docs/PLAN2-CONTRIBUTION-GUIDE.md) for getting started.

## AI Assistance

This project was developed with Claude (Anthropic) as a coding assistant. AI contributions include code structure suggestions, test generation, and documentation drafts. All AI-generated code has been reviewed and verified by the developer. Design decisions and core logic are independently authored.

## License

MIT — see [LICENSE](LICENSE)
