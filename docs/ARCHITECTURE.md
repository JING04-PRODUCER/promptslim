# AgentOrchestrator 架构设计

## 设计目标

1. **跨语言协作**：Python 负责性能敏感的 LLM 推理，Java 提供企业级后台管理
2. **插件化工具**：工具按分类注册，Agent 按需挂载，支持热扩展
3. **容错设计**：工具调用内置超时 + 指数退避重试，避免单点故障
4. **工作流编排**：支持顺序、并行、DAG 三种多 Agent 协作模式

## 核心模块设计

### 1. Agent 模块 (`agent-core/agents/`)

```
BaseAgent (抽象基类)
  ├── AgentConfig (配置: 名称/提示词/工具/超时/温度)
  ├── AgentStatus (状态机: IDLE→RUNNING→COMPLETED/FAILED/TIMEOUT)
  └── AgentEvent (事件记录: 思考/动作/工具调用/结果)

LLMAgent (BaseAgent 实现)
  ├── OpenAI 兼容 API 调用
  ├── Function Calling 自动工具选择
  ├── 主循环: 调用LLM → 解析工具 → 执行工具 → 反馈结果
  └── 退出条件: 达到最大迭代 或 LLM无工具调用
```

### 2. 工具模块 (`agent-core/tools/`)

```
ToolRegistry (单例注册中心)
  ├── register(meta, handler) → 注册工具
  ├── get(name) → 获取工具
  ├── list(category) → 按分类列出
  └── to_openai_tools() → 转为 OpenAI Function Call 格式

ToolMetadata (工具描述)
  ├── name, description, version
  ├── parameters: list[ToolParameter]
  ├── category: file | database | web | system | custom
  ├── timeout_seconds: 超时时间
  └── max_retries: 最大重试次数
```

### 3. 工作流引擎 (`agent-core/orchestration/`)

```
WorkflowEngine
  ├── run_sequential(agents, task) → 顺序执行，失败即停
  ├── run_parallel(agents, task) → 并发执行，Semaphore 限流
  └── run_dag(steps, task) → DAG 拓扑排序执行
      └── WorkflowStep { agent, depends_on[], step_name }
```

### 4. 管理后台 (`admin-server/`)

Spring Boot 作为管理入口，通过 REST 与 Python 推理核心通信：

```
AdminController → AgentService → RestTemplate → Python AgentCore
     ↓                                       ↓
   PostgreSQL (Agent元数据)               内存 (Agent运行时)
```

## 数据流

### 单 Agent 执行流程

```
1. Client → POST /api/agents/{name}/run { task }
2. FastAPI → LLMAgent.run(task)
3. Agent 构建 messages → 调用 LLM (OpenAI API)
4. LLM 返回 function_call → Agent 解析工具名+参数
5. Agent → ToolRegistry.get(tool_name) → 获取 handler
6. Agent → await handler(**args) [with timeout]
7. 工具结果 → feedback to messages → 再次调用 LLM
8. LLM 返回最终文本 → Agent 返回结果
9. FastAPI → JSON Response → Client
```

### 多 Agent 工作流

```
Client → POST /api/workflows { agents: [A,B,C], task, mode }

mode=sequential:
  A.run(task) → result_A
  B.run(task + context_A) → result_B
  C.run(task + context_A_B) → result_C

mode=parallel:
  A.run(task) ─┐
  B.run(task) ─┤→ await asyncio.gather() → [result_A, result_B, result_C]
  C.run(task) ─┘
```

## 错误处理策略

| 场景 | 策略 |
|------|------|
| LLM API 调用失败 | tenacity 指数退避重试 (3次) |
| 工具调用超时 | asyncio.wait_for + 重试 (3次, 1.5^n 退避) |
| 工具执行出错 | 错误信息反馈给 LLM，由 LLM 决定下一步 |
| Agent 达到最大迭代 | 返回 FAILED 状态 + 错误信息 |
| 并行工作流部分失败 | 不阻塞其他 Agent，收集全部结果后返回 |
