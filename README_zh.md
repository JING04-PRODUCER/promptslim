# PromptSlim 🪒

**AI 提示词瘦身工具包 — 在每次 API 调用前，从源头减少 Token 消耗。**

[![PyPI](https://img.shields.io/badge/pip-install-blue)](https://pypi.org)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model](https://img.shields.io/badge/models-GPT|Claude|DeepSeek|Qwen-green)]()
![Category](https://img.shields.io/badge/category-llm--tools%20|%20token--optimization%20|%20prompt--engineering-orange)

> 🎯 **Token 优化 · 成本节省 · Prompt 工程 · LLM 工具**

> [English](README.md) | 📖 [掘金详解 v0.3.0](https://juejin.cn/post/7652277909156790272)

## 解决什么问题？

你发给 LLM 的每一个词都花钱。填充词、冗余表达、礼貌废话在悄悄消耗你的预算。大多数开发者没意识到，5%~40% 的 Token 开销是浪费。

**PromptSlim** 在 prompt 层面剥离冗余——在请求到达 API 之前——零代码侵入，免费节省。

[![PyPI version](https://img.shields.io/pypi/v/promptslim?style=flat-square)](https://pypi.org/project/promptslim/)

## 快速开始

```bash
pip install promptslim
```

### Python SDK

```python
from promptslim import quick_slim

text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
report = quick_slim(text)
print(f"节省 Token: {report.savings_pct}% | 节省费用: ${report.cost_saved:.6f}/次")
```

### 一行代码接入 OpenAI

```python
import promptslim
promptslim.patch_openai()  # 一行代码，自动压缩所有 prompt

from openai import OpenAI
client = OpenAI()
# 所有调用自动压缩 — 无需改动业务代码
response = client.chat.completions.create(model="gpt-4o", messages=[...])
```

### CLI

```bash
# 统计 Token 数
promptslim count "Hello world" -m gpt-4o

# 快速去冗余（规则引擎，无需 API）
promptslim slim prompt.txt -o slimmed.txt

# 智能压缩（LLM 语义压缩）
promptslim smart long_chat.json -m gpt-4o-mini --max-tokens 512 -o slimmed.txt

# 对比两个文本
promptslim compare old.txt new.txt
```

## 效果演示

![PromptSlim CLI Demo](demo.gif)

```
原始: In order to basically say that this is really very important
      and actually I think we should definitely consider it.
瘦身: say this is important and I think we should consider it.
节省: 31.3% Token

原始: 嗯，那个我想说的是，这个功能非常非常非常好用，对吧？你知道吗？
瘦身: 我想说的是，这个功能好用。
节省: 40.0% Token
```

## 真实 Benchmark

| 场景 | 原始 Token | 压缩后 | 节省比例 | 语义保留 |
|------|-----------|--------|---------|---------|
| 客服对话历史 | 15,432 | 9,871 | 36.0% | ✅ |
| 代码审查提示词 | 2,847 | 1,923 | 32.5% | ✅ 代码受保护 |
| 会议记录 | 8,210 | 5,416 | 34.0% | ✅ |
| 多轮对话上下文 | 4,560 | 3,102 | 32.0% | ✅ |
| 技术文档 | 1,200 | 1,080 | 10.0% | ✅ |

## 功能

| 功能 | 描述 |
|------|------|
| 🔍 **冗余检测** | 40+ 条中英文冗余模式——填充词/修饰词/啰嗦句式 |
| 📝 **智能压缩** | LLM 语义压缩对话历史，防止上下文溢出 |
| 📊 **对比报告** | 瘦身前后的 Token 数、费用、节省比例一目了然 |
| 🎯 **多模型分词** | tiktoken 精确计数 GPT / Claude / DeepSeek / Qwen |
| 🔧 **Python SDK** | 一行：`from promptslim import quick_slim` |
| ⚡ **OpenAI 集成** | 零代码：`promptslim.patch_openai()` 自动压缩所有调用 |
| 🌐 **双语支持** | 中英文文本均可处理 |
| ⚡ **Anthropic 缓存分析** | 分析 Prompt Caching 节省潜力，缓存命中再省 90% |
| 🛡️ **代码保护** | 自动检测代码片段，跳过压缩避免破坏 |

## 冗余模式覆盖

| 类型 | 示例 |
|------|------|
| 英文填充词 | `um, uh, hmm, basically, literally, actually` |
| 英文修饰词 | `very, really, extremely, absolutely` |
| 英文啰嗦句式 | `in order to → to`, `due to the fact that → because` |
| 中文填充词 | `嗯, 啊, 哦, 那个, 就是说` |
| 中文修饰词 | `非常, 特别, 极其, 十分, 超级` |
| 礼貌废话 | `希望对你有所帮助, 如有问题请随时联系` |
| 重复标点 | `！！→！`, `？？→？` |

## 与 AI Cost Sentinel 配合

**调用前瘦身 → 调用中追踪。** 形成完整的成本优化闭环。

> 详见 [ai-cost-sentinel](https://github.com/JING04-PRODUCER/ai-cost-sentinel)

## 项目结构

```
promptslim/
├── promptslim/
│   ├── __init__.py        # 公共 API
│   ├── cli.py             # CLI 入口
│   ├── compressor.py      # 压缩器（规则 + LLM）
│   ├── cache.py           # Anthropic Prompt Caching 分析
│   ├── redundancy.py      # 冗余检测模式
│   ├── reporter.py        # 报告生成 + 价格表
│   └── tokenizer.py       # 多模型 Token 计数
├── tests/
│   └── test_prompslim.py
├── pyproject.toml
└── README.md
```

## 路线图

- [ ] Web 在线体验（粘贴文本，实时看节省）
- [ ] VS Code 插件（保存时自动瘦身）
- [ ] 自定义正则规则
- [ ] 批量处理目录
- [ ] LangChain / LlamaIndex 集成

## 许可证

MIT — 详见 [LICENSE](LICENSE)
