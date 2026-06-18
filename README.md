# PromptSlim 🪒

**AI Prompt Slimming Toolkit — reduce token consumption at the source before every API call.**

[🌐 English](README.md) | [中文](README_zh.md)

[![PyPI](https://img.shields.io/badge/pip-install-blue)](https://pypi.org)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model](https://img.shields.io/badge/models-GPT|Claude|DeepSeek|Qwen-green)]()
![Category](https://img.shields.io/badge/category-llm--tools%20|%20token--optimization%20|%20prompt--engineering-orange)

> 🎯 **Token Optimization · Cost Saving · Prompt Engineering · LLM Tools**

> 📖 **掘金详解 v0.3.0：** [给你的 AI 提示词剃得再干净一点](https://juejin.cn/post/7652277909156790272)

## What Problem Does This Solve?

Every word you send to an LLM costs money. Filler words, redundant phrases, and polite fluff silently drain your budget. Most developers don't realize 5-40% of their token spend is waste.

**PromptSlim** strips redundancy at the prompt level — before it reaches the API — giving you free savings with zero code changes to your app logic.

## Quick Start

```bash
pip install git+https://github.com/JING04-PRODUCER/promptslim.git
```

### Python SDK

```python
from promptslim import quick_slim

text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
report = quick_slim(text)
print(f"Token saved: {report.savings_pct}% | Cost saved: ${report.cost_per_call_saved:.6f}/call")
```

### CLI

```bash
# Count tokens
promptslim count "Hello world" -m gpt-4o

# Quick slim (rule-based, no API required)
promptslim slim prompt.txt -o slimmed.txt

# Smart compression (LLM-powered, preserves semantics)
promptslim smart long_chat.json -m gpt-4o-mini --max-tokens 512 -o slimmed.txt

# Compare two texts
promptslim compare old.txt new.txt
```

## Demo

```
Original: In order to basically say that this is really very important
          and actually I think we should definitely consider it.
Slimmed:  say this is important and I think we should consider it.
Saved:    31.3% tokens

Original: 嗯，那个我想说的是，这个功能非常非常非常好用，对吧？你知道吗？
Slimmed:  我想说的是，这个功能好用。
Saved:    40.0% tokens
```

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Redundancy Detection** | 40+ patterns in Chinese & English — filler words, redundant modifiers, verbose phrases |
| 📝 **Smart Compression** | LLM-powered semantic compression for chat history before context overflow |
| 📊 **Comparison Reports** | Before/after token count, cost, and savings percentage at a glance |
| 🎯 **Multi-Model Tokenizer** | Accurate tiktoken counting for GPT / Claude / DeepSeek / Qwen |
| 🔧 **Python SDK** | One-line integration: `from promptslim import quick_slim` |
| 🌐 **Bilingual** | Works with both Chinese and English text |

## Redundancy Patterns

| Type | Examples |
|------|----------|
| English fillers | `um, uh, hmm, basically, literally, actually` |
| English modifiers | `very, really, extremely, absolutely` |
| English verbose phrases | `in order to → to`, `due to the fact that → because` |
| Chinese fillers | `嗯, 啊, 哦, 那个, 就是说` |
| Chinese modifiers | `非常, 特别, 极其, 十分, 超级` |
| Polite fluff | `希望对你有所帮助, 如有问题请随时联系` |
| Repeated punctuation | `！！→！`, `？？→？` |

## Paired with AI Cost Sentinel

**Slim before call → Track after call.** Form a complete cost optimization loop.

```python
import openai
from promptslim import quick_slim

# 1. Slim before sending
text = load_prompt()
report = quick_slim(text)

# 2. Send through Sentinel proxy (tracks actual cost)
client = openai.OpenAI(base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": report.slimmed}]
)

# 3. See estimated savings
print(f"Estimated savings: ${report.cost_per_call_saved:.6f}/call")
```

## Project Structure

```
promptslim/
├── promptslim/
│   ├── __init__.py        # Public API exports
│   ├── cli.py             # CLI entry point
│   ├── compressor.py      # Compressors (rule-based + LLM)
│   ├── redundancy.py      # Redundancy detection patterns
│   ├── reporter.py        # Report generation + pricing table
│   └── tokenizer.py       # Multi-model token counting
├── tests/
│   └── test_prompslim.py
├── pyproject.toml
└── README.md
```

## Roadmap

- [ ] Web playground (paste text, see savings live)
- [ ] VS Code extension (slim on save)
- [ ] Custom regex rules
- [ ] Batch processing directory
- [ ] LangChain / LlamaIndex integration

## AI Assistance

This project was developed with Claude (Anthropic) as a coding assistant. AI contributions include code structure suggestions, test generation, and documentation drafts. All AI-generated code has been reviewed and verified by the developer. Design decisions and core logic are independently authored.

## License

MIT — see [LICENSE](LICENSE)
