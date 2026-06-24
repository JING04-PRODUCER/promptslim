# AgentOrchestrator

一个 Agent 编排框架，Python 写推理核心，Java Spring Boot 做管理后台，用 REST API 把两部分连起来。支持 Tool Calling、多 Agent 工作流、RAG 记忆。

[![CI](https://github.com/JING04-PRODUCER/agent-orchestrator/actions/workflows/python-test.yml/badge.svg)](https://github.com/JING04-PRODUCER/agent-orchestrator/actions/workflows/python-test.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/java-17-orange.svg)](https://adoptium.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 为什么写这个

LangChain 和 LangGraph 概念太多，学起来费劲。CrewAI 功能全但太重了。我就想要一个自己能完全掌控的轻量框架，Agent 定义、工具注册、工作流编排都通过 API 来，再配个管理后台方便查看状态。

模型不挑——只要是 OpenAI 兼容的 API 都能接。

## 跑起来

需要 Python 3.12+、Java 21+。

```bash
git clone https://github.com/JING04-PRODUCER/agent-orchestrator.git
cd agent-orchestrator
cp .env.example .env   # 填上你的 OPENAI_API_KEY
docker compose up -d

curl http://localhost:8000/health
curl http://localhost:9090/api/admin/health
```

不用 Docker 的话：

```bash
cd agent-core
pip install -r requirements.txt
python main.py          # Agent Core → :8000

cd admin-server
./mvnw spring-boot:run  # Admin Server → :9090
```

## 怎么用

先创建一个 Agent，给它配好系统提示词和工具，然后发任务让它执行。

```bash
# 创建一个代码审查 Agent
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "system_prompt": "你是一个代码审查专家，关注安全漏洞和性能问题。",
    "tools": ["read_file", "web_search"],
    "max_iterations": 5
  }'

# 让它审查代码
curl -X POST http://localhost:8000/api/agents/code-reviewer/run \
  -H "Content-Type: application/json" \
  -d '{"task": "检查 app.py 有没有 SQL 注入和 XSS 漏洞"}'

# 查看结果
curl http://localhost:8000/api/agents/code-reviewer/status
```

多个 Agent 可以串成工作流：

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["analyzer", "code-reviewer", "tester"],
    "task": "全面审查 auth 模块的代码质量",
    "mode": "sequential"
  }'
```

管理后台在 `http://localhost:9090`，可以看到所有 Agent 的状态和任务执行情况。

## 内置工具

| 工具 | 做什么 |
|------|--------|
| `read_file` | 读取文件，支持 txt/json/csv/md，自动检测编码 |
| `execute_sql` | 执行 SQL 查询（只允许 SELECT），防注入 |
| `list_tables` | 查看数据库有哪些表 |
| `web_search` | 用 DuckDuckGo 搜网页，免费不用 API Key |

想加自己的工具？在 `tools/` 目录下写个 Python 文件注册就行。

## 架构

```
Admin Server (Spring Boot, :9090)  ← 管理后台
        ↓ REST API
Agent Core (Python FastAPI, :8000) ← 推理引擎
        ↓
OpenAI 兼容 API · 本地工具 · PostgreSQL + Redis
```

## 已知问题

- RAG 记忆目前是内存存储，重启就没了。后面会接向量数据库
- 工作流里上游 Agent 的输出目前是拼字符串传给下游，不够结构化
- API 没有鉴权，只能内网用
- 新工具要写代码注册，还没做 MCP 协议支持

上面这些都是当前实际情况，不是 bug。欢迎 PR。

## License

MIT
