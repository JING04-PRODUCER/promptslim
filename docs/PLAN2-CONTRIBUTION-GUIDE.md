# 方案2：AI Agent 框架轻量代码修复指南

> 目标：向 LangChain / LangGraph / CrewAI / Dify 等热门项目提交有含金量的 PR

---

## 一、可贡献项目速览

| 项目 | Stars | 语言 | 标签入口 | 适合你的场景 |
|------|-------|------|----------|:------------:|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 100k+ | Python | `good first issue` | Prompt/向量/工具链 |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 10k+ | Python | `good first issue` | Agent超时/重试/状态 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 25k+ | Python | `bug` | Agent调度/工具调用 |
| [langgenius/dify](https://github.com/langgenius/dify) | 60k+ | Python | `good first issue` | 工作流/插件系统 |
| [ag2ai/ag2](https://github.com/ag2ai/ag2) | 5k+ | Python | `good first issue` | 多Agent协同 |

---

## 二、精准猎物清单（已验证的开放 Issue）

### 策略 A：Prompt 拼接/模板错误

这类 bug 发生在 ChatPromptTemplate 处理花括号、变量插值、多消息拼接时。

#### 🔴 猎物#1 — LangChain #32702
**[ChatPromptTemplate 含 JSON 花括号时报错](https://github.com/langchain-ai/langchain/issues/32702)**

- **问题**：System prompt 中含 `{}`（如JSON示例）被误解析为模板变量
- **修复思路**：在 `_validate_and_interpolate` 中增加花括号转义检测，或提供 `safe_mode` 参数
- **难度**：⭐⭐ | **文件**：`langchain_core/prompts/chat.py`
- **修复后影响面**：所有使用 JSON 格式 prompt 的用户

#### 🔴 猎物#2 — LangChain #29034
**[BaseMessage 子类变量无法被 ChatPromptTemplate 插值](https://github.com/langchain-ai/langchain/issues/29034)**

- **问题**：`SystemMessage(content="{language}")` 在 `ChatPromptTemplate.from_messages()` 中变量不被替换
- **修复思路**：在 `format_messages()` 中增加对 `BaseMessage` 子类的 f-string 处理
- **难度**：⭐⭐ | **文件**：`langchain_core/prompts/chat.py`

#### 🔴 猎物#3 — CrewAI #2571
**[`system_prompt` 与部分模型不兼容](https://github.com/crewAIInc/crewAI/issues/2571)**

- **问题**：使用 `output_pydantic=True` 时内部重生成 prompt 强制使用 `system_prompt`，Mistral 等模型不支持
- **修复思路**：添加 `use_system_prompt` 检查逻辑，对不支持的模型回退到 user message
- **难度**：⭐⭐ | **文件**：crewAI 的 agent 核心模块

---

### 策略 B：工具超时无重试

这类 bug 涉及工具调用挂起、超时未处理、重试策略缺失。

#### 🔴 猎物#4 — LangGraph #6412 / LangChain PR #32935
**[ToolNode.ainvoke() 无超时机制](https://github.com/langchain-ai/langgraph/issues/6412)**

- **问题**：工具调用无超时，`sse_read_timeout` 配置不当会导致永久挂起
- **LangChain 侧已有关闭的 PR #32935**（功能被拒绝合入，改成在 LangGraph 侧实现）
- **正确贡献点**：在 LangGraph 的 `ToolNode` 中实现超时
- **难度**：⭐⭐⭐ | **语言**：Python asyncio
- **修复要点**：
  ```python
  # 核心改动：ToolNode._afunc() 中添加
  import asyncio
  result = await asyncio.wait_for(tool.ainvoke(input), timeout=timeout_seconds)
  ```

#### 🔴 猎物#5 — CrewAI #2379
**[`max_execution_time` 参数完全无效](https://github.com/crewAIInc/crewAI/issues/2379)**

- **问题**：设置 `max_execution_time=1` 后任务仍运行 37 秒，超时机制形同虚设
- **修复思路**：检查 Agent 执行循环中的超时检查点，使用 `signal.alarm` 或 `threading.Timer` 强制中断
- **难度**：⭐⭐ | **文件**：crewAI Agent 执行器
- **推荐指数**：★★★★★ — 功能明确存在但从未生效，修复后效果立竿见影

#### 🔴 猎物#6 — CrewAI #3871
**[`kickoff_for_each()` 完成后永不终止](https://github.com/crewAIInc/crewAI/issues/3871)**

- **问题**：批量任务执行完毕后进程不退出，挂起
- **修复思路**：检查事件循环清理、线程池关闭逻辑
- **难度**：⭐⭐ | **文件**：crewAI Crew 执行器

---

### 策略 C：向量检索参数硬编码

这类 bug 涉及向量数据库字段名、检索参数被写死。

#### 🔴 猎物#7 — LangChain #18731 ⭐ 替换 #32751 (已合入)
**[Azure AI Search 元数据字段硬编码为 "metadata"](https://github.com/langchain-ai/langchain/issues/18731)**
> 注意：此 issue 已有 PR #18938 尝试修复但可能不完整

- **问题**：`semantic_hybrid_search_with_score_and_rerank` 硬编码 `"metadata"` 字段，自定义索引结构用户报 KeyError
- **修复思路**：检查当前修复是否完整，或在 `AzureSearch` 构造函数中增加 `metadata_field_name` 参数
- **难度**：⭐⭐⭐ | **文件**：`libs/community/langchain_community/vectorstores/azuresearch.py`

---

### 策略 D：新增简单工具函数（高性价比 PR）

这类 PR 是**功能新增**而非 Bug 修复，但因为独立性强、改动边界清晰，容易被合并。

#### 🟢 工具#1：为 LangChain 添加 SQL 查询封装工具
```python
# 建议提交到 langchain_community.tools 的新工具
class SQLQueryTool(BaseTool):
    """安全的参数化 SQL 查询工具，支持连接池与结果缓存"""
    name = "sql_query"
    description = "Execute parameterized SQL query with connection pooling"
    
    # 核心卖点：
    # 1. 参数化查询防注入
    # 2. async/await + 连接池
    # 3. 结果自动缓存 (TTL可配置)
    # 4. 超时控制 + 自动重试
```

#### 🟢 工具#2：为 LangChain 添加本地文件读取工具
```python
class FileReaderTool(BaseTool):
    """支持多编码、大文件分块、多格式的结构化文件读取"""
    name = "file_reader"
    description = "Read files with auto-encoding detection and chunking"
    # 支持：txt, json, csv, yaml, markdown, pdf(文本提取)
```

---

## 三、一条龙贡献流程

### Step 1：Fork + Clone
```bash
# 以 LangChain 为例
gh repo fork langchain-ai/langchain --clone
cd langchain
pip install -e ".[dev,test]"
```

### Step 2：选择 Issue 并声明
在 Issue 下评论：
> "I'd like to work on this. Proposed approach: [一句话修复思路]. @maintainer would this be acceptable?"

### Step 3：编码规范
```python
# ✅ 好的 PR 特征
- 改动范围小（< 200 行核心代码）
- 不破坏现有 API
- 包含单元测试
- commit message 遵循项目规范
```

### Step 4：提交 PR
```bash
git checkout -b fix/tool-timeout-retry
# 编写修复代码 + 测试
git commit -m "fix: add timeout and retry to ToolNode async invoke"
git push origin fix/tool-timeout-retry
gh pr create --title "fix: add timeout to ToolNode ainvoke" --body "..."
```

---

## 四、Java 版本兼容代码策略

针对每个 Python 修复，可为 Java 生态做镜像贡献：

| Python 修复 | Java 镜像 | 目标项目 |
|------------|-----------|----------|
| LangChain ToolNode 超时 | Spring AI ToolCall timeout | Spring AI |
| SQL 查询工具 | JDBC Template 安全封装 | Spring AI |
| 向量参数可配置 | Spring AI VectorStore config | Spring AI |
| Prompt 花括号转义 | Spring AI PromptTemplate | Spring AI |

这样做的好处：
- **一份思路，两份贡献**
- **Python + Java 全覆盖**，与你的技术栈完全对齐
- **Java 版本改动通常更直观**（强类型 + 编译期检查）

---

## 五、推荐优先顺序

根据**修复难度 + 简历含金量 + 被合并概率**综合排序：

1. 🔥 **CrewAI #2379** — `max_execution_time` 无效（有3个重复 issue，说明大量用户受困）→ 改动小、效果显著
2. 🔥 **LangChain #32702** — Prompt 花括号误解析 → 影响面大
3. 🔥 **CrewAI #2571** — `system_prompt` 不兼容导致 Mistral 等模型崩溃 → 修复明确、含金量高
4. 🔧 **CrewAI #3871** — `kickoff_for_each` 挂起 → 体验改善
5. 🔧 **LangChain #18731** — Azure 向量搜索 metadata 硬编码 → 需调研当前修复完整性
6. 🔧 **新增工具函数** — SQL/文件读取工具 → 独立性强、加分项

---

## 六、时间规划建议

| 周次 | 任务 | 预期产出 |
|------|------|----------|
| 第1周 | Fork 项目 + 阅读源码 + 复现 bug | 3 个 issue 可复现 |
| 第2周 | 修复 #2379 + #32751 | 2 个 PR 提交 |
| 第3周 | 新增 SQL/文件工具 + 写测试 | 1-2 个功能 PR |
| 第4周 | 跟进 Review、修改、等待合入 | PR 状态追踪 |

---

> **核心原则**：选择 3-5 个边界清晰的小 bug，快速交付，提高命中率。不要在单个大 PR 上消耗过多时间。
