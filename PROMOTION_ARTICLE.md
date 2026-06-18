# 你的 AI 提示词浪费了多少 Token？一个开源工具帮你砍掉 5%~40%

> 适合发布平台：**掘金**、**知乎**、**SegmentFault**、**V2EX**

---

## 起因：我的 API 账单在滴血

上个月我看了眼 OpenAI 的账单，日均消耗 200 万 Token。仔细一查日志，发现大量请求里塞满了这种东西：

```
"嗯，那个我想说的是，这个功能真的非常非常好用，对吧？"
"In order to basically say that this is really very important and actually..."
"希望对你有所帮助，如有问题请随时联系！"
```

**这不是逻辑，这是垃圾。** 但每次人写的 prompt、对话历史、用户输入，天然就带着这些冗余。API 照单全收，按 Token 计费。

我算了一笔账：如果每天 200 万 Token 里有 20% 是废话，一天浪费 $1，一个月就是 $30，一年 $365。这还是一个人的量。

## 现有方案的坑

| 方案 | 问题 |
|------|------|
| 手动精简 | 每次写 prompt 都要仔细检查，效率太低 |
| 缩短 prompt | 删掉的可能是关键上下文，效果打折 |
| 用更便宜的模型 | 能力下降，该用 GPT-4o 的还得用 |
| LangSmith 等平台 | 只追踪不优化，治标不治本 |

我需要的是：**在请求发出之前，自动剃掉冗余，但不丢语义。**

## PromptSlim：给你的提示词"剃个胡子"

我写了一个开源工具专门干这件事，叫 **PromptSlim**。

```bash
pip install git+https://github.com/JING04-PRODUCER/promptslim.git
```

### 一行代码搞定

```python
from promptslim import quick_slim

text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
report = quick_slim(text)
print(f"节省 {report.savings_pct}% Token，省 ${report.cost_per_call_saved:.6f}")
```

### 实际效果

```
原始: In order to basically say that this is really very important
       and actually I think we should definitely consider it.

瘦身: say this is important and I think we should consider it.
节省: 31.3% Token ✅
```

```
原始: 嗯，那个我想说的是，这个功能非常非常非常好用，对吧？你知道吗？

瘦身: 我想说的是，这个功能好用。
节省: 40.0% Token ✅
```

## 它怎么做到的？

两层策略：

### 第一层：规则引擎（离线，零成本）

内置 40+ 条中英文冗余模式：

- 英文填充词：`um, uh, basically, literally, actually`
- 英文啰嗦句式：`in order to → to`, `due to the fact that → because`
- 中文语气填充：`嗯, 啊, 那个, 就是说`
- 中文礼貌废话：`希望对你有所帮助, 如有问题请随时联系`

规则的优点：**不需要 API 调用就能瘦身**，而且不会丢语义，只是剃掉真正的"废话"。

### 第二层：LLM 智能压缩（保留语义）

对于聊天历史、长文档，规则引擎不够用。这时候调用 LLM 做语义压缩：

```bash
promptslim smart long_chat.json -m gpt-4o-mini --max-tokens 512
```

这会把几千 Token 的对话历史压缩成一段摘要，保留关键信息和上下文。比直接截断智能得多。

## CLI 四件套

```bash
# 1. 看看到底多少 Token
promptslim count prompt.txt -m gpt-4o

# 2. 快速去冗余并保存
promptslim slim prompt.txt -o slimmed.txt

# 3. 智能压缩
promptslim smart long_chat.json -m gpt-4o-mini -o slimmed.txt

# 4. 对比两个版本
promptslim compare old.txt new.txt
```

## 和我另两个工具配合形成闭环

我做了三个开源工具，构成完整的 LLM 成本管控链路：

```
PromptSlim              AI Cost Sentinel         Agent部署
(调用前瘦身)     →      (调用中追踪)      →      (Agent编排)
节省 5-40% Token        实时费用仪表盘           多Agent协作
```

- **[PromptSlim](https://github.com/JING04-PRODUCER/promptslim)** — 本文主角，调用前瘦身
- **[AI Cost Sentinel](https://github.com/JING04-PRODUCER/ai-cost-sentinel)** — 透明代理，不改代码追踪实际消耗
- **[AgentOrchestrator](https://github.com/JING04-PRODUCER/agent-orchestrator)** — 跨语言 Agent 编排平台

一句话总结：**Slim before call, track after call, orchestrate at scale.**

## 开源地址

GitHub：[https://github.com/JING04-PRODUCER/promptslim](https://github.com/JING04-PRODUCER/promptslim)

如果这个工具帮你省了 Token，点个 ⭐ Star 就是最大的支持。有什么需求或建议欢迎提 Issue！

---

*标签：Python · LLM · Token 优化 · 成本控制 · 开源工具 · Prompt Engineering*
