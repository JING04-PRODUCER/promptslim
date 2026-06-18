# PromptSlim 0.3.0：不只是"剃冗余"，这次连缓存钱也帮你省了

> 适合发布平台：**掘金**、**知乎**、**SegmentFault**

---

## 先看一组数据

我做了一个对比测试，用同一段文本分别跑旧版和 0.3.0 版：

| 场景 | 旧版删除率 | 0.3.0 删除率 | 变化 |
|------|:---------:|:----------:|------|
| 中文口语对话 | 33.3% | **66.7%** | 翻倍 |
| 中文技术讨论 | 22.5% | **75.0%** | 三倍 |
| 英文冗余句式 | 0% ❌ | **54.3%** | 从零覆盖 |
| Python 代码段 | 17.4% ❌破坏 | **0%** ✅保护 | 关键修复 |
| 中英混合内容 | 34.3% | **43.1%** | +26% |

旧版在代码场景下会**主动破坏你的 prompt**（把 `def fibonacci(n):` 里的单词当废话删了），0.3.0 彻底修了这个问题。

---

## 三个新功能，逐个说

### 1. 代码保护：别再破坏我的 prompt 了

很多人用 LLM 写代码，system prompt 里经常贴示例代码片段。旧版规则引擎不管这些，碰到 `return`、`import`、`class` 照样匹配删除。

0.3.0 新增了 `_is_code_like()` 检测函数：

```python
# 多行 + 缩进 + 强特征（def/class/{}）→ 判定为代码 → 跳过压缩
code_prompt = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
```

检测逻辑分两层：
- **强特征**：`def`/`class`/`{}`/`[]`/`->` 命中行 > 50% → 代码
- **弱特征**：4 空格/Tab 缩进行 > 40%（≥3 行）→ 代码
- **含中文 > 30%** 的文本不会被误判为代码

这样 prompt 里的示例代码安全了，自然语言照样压缩。

### 2. 上下文感知的英文规则

旧版把 `basically`/`actually`/`literally` 一刀切全删。这会导致 `"I actually think this is wrong"` 变成 `"I think this is wrong"`——实际上丢了一个强调语义，`actually` 在这里是内容词。

0.3.0 的策略：

```
句首/独立使用 → 填充词，删除：
  "Basically, this is wrong." → "this is wrong."

句中跟在 I 后面 → 删除填充词但保留动词：
  "I basically think..." → "I think..."

逗号包裹 → 删除：
  "This is, basically, wrong." → "This is wrong."
```

同时新增了 8 种英文冗余句式：`with regard to → regarding`、`it goes without saying that → ""`、`as a matter of fact → ""` 等。旧版这些一个都不认识。

### 3. Anthropic Prompt Caching 集成

这是最"省钱"的功能。如果你用 Claude API，Prompt Caching 能让你重复调用的 system prompt 以 **1/10 的价格**读取。

我在项目中加了 `cache.py` 模块，一行代码就能分析 prompt 缓存潜力：

```python
from promptslim import quick_slim

# 准备消息（模拟一个带长 system prompt 的 Agent 对话）
messages = [
    {"role": "system", "content": ("You are an expert code reviewer. " * 350)},
    {"role": "user", "content": "Review auth.py for security issues"},
]

# 瘦身 + 缓存分析一起
text = "\n".join(m["content"] for m in messages)
report = quick_slim(text, model="claude-opus-4-7", cache_messages=messages)
d = report.to_dict()

print(f"瘦身节省: {d['savings_pct']}%")
print(f"缓存命中后再省: {d['cache']['savings_per_cached_call_usd']:.6f} USD/次")
# 输出: 缓存命中后再省: 0.127453 USD/次
```

实际数据：一个 9900 token 的对话，system prompt 占 9441 token。缓存命中的读价是原价的 1/10，**单次调用省 85.3% input 费用**。

CLI 也支持了：

```bash
promptslim slim prompt.txt --cache messages.json
# 瘦身报告下方直接显示缓存分析表格
```

---

## 完整的省钱链路

现在 PromptSlim 覆盖了三种 Token 优化策略：

```
┌────────────────────────────────────────────────────┐
│              你的 Prompt（原始）                      │
└──────────────────┬─────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  规则去冗余 (V2)     │  离线、零延迟
         │  剃掉废话/口头禅     │  节省 5%~75%
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Prompt Caching     │  缓存稳定部分
         │  system prompt 复用  │  再省 10%~90%
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  LLM 智能压缩       │  语义保留压缩
         │  对话历史/长文档     │  大幅缩短上下文
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  AI Cost Sentinel   │  透明追踪实际消耗
         │  (配合使用)          │  
         └─────────────────────┘
```

---

## 安装使用

```bash
pip install git+https://github.com/JING04-PRODUCER/promptslim.git
```

```python
from promptslim import quick_slim, analyze_messages

# 快速瘦身
report = quick_slim("嗯，那个我想说的是，这个功能非常非常好用")
print(f"节省 {report.savings_pct}% Token")

# 分析缓存潜力
messages = [
    {"role": "system", "content": "你是专业的代码审查员..." * 300},
    {"role": "user", "content": "检查 auth.py 安全问题"},
]
cache = analyze_messages(messages, "claude-opus-4-7")
print(f"缓存命中后每次节省: ${cache.savings_per_cached_call:.6f}")
```

---

## 开源地址

GitHub：[https://github.com/JING04-PRODUCER/promptslim](https://github.com/JING04-PRODUCER/promptslim)

v0.3.0 改动总结：6 个文件、445 行新增、31 个测试全绿。

如果你也在用 LLM 做产品，给个 ⭐ Star，让更多人知道 Token 是可以省的。

---

*标签：Python · LLM · Token 优化 · Prompt Caching · 成本控制 · 开源工具*
