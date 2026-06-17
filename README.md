# AgentOrchestrator

跨语言 AI Agent 调度平台 — Python FastAPI 大模型推理核心 + Java Spring Boot 管理后台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Java 21](https://img.shields.io/badge/java-21-orange.svg)](https://adoptium.net/)
[![Spring Boot 3.4](https://img.shields.io/badge/spring--boot-3.4-brightgreen.svg)](https://spring.io/projects/spring-boot)

## 项目简介

AgentOrchestrator 是一个跨语言架构的 AI Agent 调度平台，目标是让开发者用最少的代码搭建起 **LLM推理 + 工具调用 + 多Agent编排 + 可视化管理** 的完整链路。

### 为什么选择这个项目？

| 问题 | 现有方案 | 本方案 |
|------|---------|--------|
| Python 推理性能好，但企业级管理弱 | FastAPI 缺乏后台管理 | Python FastAPI 推理 + Spring Boot 管理 |
| Java 生态成熟，但 LLM 集成复杂 | Spring AI 尚不完善 | 通过 REST 桥接 Python LLM 能力 |
| 开源 Agent 框架绑定特定模型 | 多数绑定 OpenAI | 兼容 OpenAI 协议，任意模型可接入 |
| 多 Agent 编排缺少可视化 | 纯代码配置 | REST API + 未来 Web UI 规划 |

## 架构概览

```
┌─────────────────────────────────────────────────┐
│              管理后台 (Spring Boot)              │
│  Agent CRUD │ 任务调度 │ 状态监控 │ 日志查询    │
│                    port 9090                     │
└────────────────────┬────────────────────────────┘
                     │ REST API (HTTP)
┌────────────────────▼────────────────────────────┐
│            推理核心 (Python FastAPI)             │
│  LLM Agent │ 工具调用 │ 重试机制 │ 工作流引擎   │
│                    port 8000                     │
└───────┬────────────┬────────────┬───────────────┘
        │            │            │
   ┌────▼───┐  ┌─────▼────┐ ┌───▼───────┐
   │ OpenAI │  │ 本地工具  │ │ PostgreSQL│
   │ 兼容API│  │ 文件/SQL  │ │  + Redis  │
   └────────┘  └──────────┘ └───────────┘
```

## 快速开始

### 前提条件

- Python 3.12+
- Java 21+
- Docker & Docker Compose (推荐)
- OpenAI 兼容 API Key

### Docker 一键部署 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/agent-orchestrator.git
cd agent-orchestrator

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# 3. 启动所有服务
docker compose up -d

# 4. 验证
curl http://localhost:8000/health       # Agent Core
curl http://localhost:9090/api/admin/health  # Admin Server
```

### 本地开发

```bash
# -------- Agent Core (Python) --------
cd agent-core
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # 填入 OPENAI_API_KEY
python main.py            # http://localhost:8000

# -------- Admin Server (Java) --------
cd admin-server
./mvnw spring-boot:run    # http://localhost:9090
```

## 核心功能

### Agent 创建与执行

```bash
# 创建 Agent
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "system_prompt": "你是一个代码审查专家...",
    "tools": ["read_file", "execute_sql"],
    "max_iterations": 5
  }'

# 执行任务
curl -X POST http://localhost:8000/api/agents/code-reviewer/run \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "code-reviewer", "task": "审查 app.py 的代码安全性"}'
```

### 多 Agent 工作流

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["analyzer", "reviewer", "tester"],
    "task": "分析这个项目的代码质量",
    "mode": "sequential"
  }'
```

## 项目结构

```
agent-orchestrator/
├── README.md
├── LICENSE
├── docker-compose.yml
├── agent-core/                    # Python 推理核心
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── agents/                    # Agent 实现
│   │   ├── base.py                # Agent 基类
│   │   └── llm_agent.py           # LLM Function Calling Agent
│   ├── tools/                     # 工具系统
│   │   ├── registry.py            # 工具注册中心
│   │   ├── file_reader.py         # 文件读取工具
│   │   └── sql_query.py           # SQL 查询工具
│   ├── orchestration/             # 工作流编排
│   │   └── workflow.py            # 顺序/并行/DAG 编排引擎
│   └── utils/                     # 工具函数
│       ├── retry.py               # 通用重试装饰器
│       └── logger.py              # 结构化日志
├── admin-server/                  # Java 管理后台
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/java/com/agentorchestrator/
│       ├── Application.java
│       ├── model/                 # Agent, Task 数据模型
│       ├── controller/            # REST 控制器
│       ├── service/               # 业务逻辑
│       └── config/                # 配置类
└── docs/                          # 文档
    ├── ARCHITECTURE.md            # 架构设计
    ├── DEPLOY.md                  # 部署指南
    ├── API.md                     # API 文档
    └── PLAN2-CONTRIBUTION-GUIDE.md # 开源贡献指南
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| AI 推理 | Python FastAPI + OpenAI SDK | LLM 调用、Function Calling |
| 工具系统 | 插件化注册 + asyncio | 超时控制、自动重试 |
| 工作流 | DAG 编排 + 并行调度 | 多 Agent 协作 |
| 管理后台 | Java 21 + Spring Boot 3.4 | REST API、JPA |
| 数据库 | PostgreSQL 16 + Redis 7 | 状态持久化、缓存 |
| 部署 | Docker Compose | 一键启动 |

## 内置工具

| 工具 | 功能 | 分类 |
|------|------|:--:|
| `read_file` | 多编码自动检测文件读取 (txt/json/csv/md) | file |
| `execute_sql` | 安全的参数化SQL查询 (仅SELECT) | database |
| `list_tables` | 数据库表结构查询 | database |

> 更多工具通过插件机制自行注册。

## 路线图 (Roadmap)

- [x] LLM Agent 核心 (OpenAI 兼容)
- [x] 工具注册与调用 (超时+重试)
- [x] 多 Agent 工作流编排
- [x] Spring Boot 管理后台
- [ ] Web UI 管理面板 (Vue 3)
- [ ] 更多内置工具 (Web Search, Code Executor)
- [ ] MCP 协议支持
- [ ] RAG 记忆系统
- [ ] 监控与告警 (Prometheus + Grafana)

## 贡献

欢迎提交 Issue 和 Pull Request！

推荐贡献路径：阅读 [开源贡献指南](docs/PLAN2-CONTRIBUTION-GUIDE.md) 了解如何从 AI Agent 框架中选择并修复简单 Bug。

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
