# AgentOrchestrator

LLM Agent 编排框架，Python 写推理核心，Java 做管理后台。

## 为什么做这个

现有的 Agent 框架要么绑定特定模型，要么缺少管理界面。我想把 Python 生态的 LLM 能力和 Java 生态的后台管理结合起来，两边的优势都用上。

## 能做什么

- 创建 Agent，给它配工具、写 system prompt，让它执行任务
- Agent 支持 Function Calling，自动选择合适的工具
- 工具调用有超时控制、失败自动重试（指数退避）
- 多个 Agent 可以串行/并行编排成工作流
- 支持流式输出，SSE 透传
- 对接 OpenAI 兼容协议，百炼、DeepSeek 都能用

## 跑起来

需要 Python 3.10+ 和 Java 17+。

```bash
# 推理核心
cd agent-core
pip install -r requirements.txt
cp .env.example .env   # 填 API key
python main.py         # 跑在 :8000

# 管理后台（可选）
cd admin-server
./mvnw spring-boot:run # 跑在 :9090
```

Docker 的话直接 `docker compose up -d`。

## 怎么用

```python
from agent_core import Agent, Tool

# 定义一个工具
async def get_weather(city: str) -> str:
    return f"{city}今天晴天"

# 创建 Agent
agent = Agent(
    name="助手",
    system_prompt="你是一个有用的助手",
    tools=[Tool.from_function(get_weather)],
    max_iterations=5
)

# 跑任务
result = await agent.run("北京今天天气怎么样")
print(result.content)
```

## 项目结构

```
agent-core/          # Python FastAPI 推理核心
  agents/            # Agent 实现
  tools/             # 工具注册中心
  orchestration/     # 工作流编排
admin-server/        # Java Spring Boot 管理后台
docs/                # 文档
```

## TODO

- [ ] Web 管理面板
- [ ] RAG 记忆系统
- [ ] MCP 协议支持
- [ ] 更多内置工具

## License

MIT
