# PromptSlim 🪒

**AI 提示词瘦身工具包 — 从源头减少 Token 消耗**

每次 API 调用前自动检测并剔除冗余内容，Token 消耗立减 5%~40%，与 [AI Cost Sentinel](https://github.com/JING04-PRODUCER/ai-cost-sentinel) 形成闭环：**调用前省钱 → 调用后追踪**。

## 快速开始

```bash
pip install git+https://github.com/JING04-PRODUCER/promptslim.git
```

### 一行瘦身

```python
from promptslim import quick_slim

text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
report = quick_slim(text)
print(f"Token 节省 {report.savings_pct}%，每次省 ${report.cost_per_call_saved:.6f}")
```

### CLI 使用

```bash
# 统计 Token 数
promptslim count "你好世界" -m gpt-4o

# 快速去冗余
promptslim slim prompt.txt -o slimmed.txt

# 智能压缩（调用 LLM）
promptslim smart long_chat.json -m gpt-4o-mini --max-tokens 512

# 对比两个文本
promptslim compare old.txt new.txt
```

## 功能

| 功能 | 说明 |
|------|------|
| 🔍 **冗余检测** | 中英文双语言，识别并剔除 40+ 种废话模式 |
| 📝 **智能压缩** | 调用 LLM 保留语义压缩（聊天历史超限前自动精简） |
| 📊 **对比报告** | 压缩前后 Token/费用/节省比例一目了然 |
| 🎯 **多模型支持** | GPT / Claude / DeepSeek / 百炼 tiktoken 精确计数 |
| 🔧 **Python SDK** | `from promptslim import quick_slim` 一行集成 |

## 瘦身示例

```
原始：In order to basically say that this is really very important
      and actually I think we should definitely consider it.

瘦身：say this is important and I think we should consider it.
节省：31.3% Token
```

```
原始：嗯，那个我想说的是，这个功能非常非常非常好用，对吧？你知道吗？

瘦身：我想说的是，这个功能好用。
节省：40.0% Token
```

## 冗余检测规则

| 类型 | 示例 |
|------|------|
| 英文填充词 | `um, uh, hmm, basically, literally, actually` |
| 英文冗余修饰 | `very, really, extremely, absolutely` |
| 英文啰嗦句式 | `in order to → to`, `due to the fact that → because` |
| 中文语气填充 | `嗯, 啊, 哦, 额, 那个, 就是说` |
| 中文冗余修饰 | `非常, 特别, 极其, 十分, 超级` |
| 中文礼貌用语(冗余) | `希望对你有所帮助, 如有问题请随时联系` |
| 重复标点 | `！！→！`, `？？→？` |

## 与 AI Cost Sentinel 配合

```python
import openai
from promptslim import quick_slim

# 1. 调用前瘦身
text = load_prompt()
report = quick_slim(text)
slim_text = trim(text)

# 2. 发送请求（通过 Sentinel 代理追踪成本）
client = openai.OpenAI(base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": slim_text}]
)

# 3. 查看实际消耗（Sentinel 自动注入响应头）
print(f"预估节省: ${report.cost_per_call_saved:.6f}/次")
```

## 项目结构

```
promptslim/
├── promptslim/
│   ├── __init__.py
│   ├── cli.py          # 命令行入口
│   ├── compressor.py   # 压缩器（规则 + LLM）
│   ├── redundancy.py   # 冗余检测规则
│   ├── reporter.py     # 报告生成 + 价格表
│   └── tokenizer.py    # 多模型 Token 计数
├── tests/
│   └── test_prompslim.py
├── pyproject.toml
└── README.md
```

## License

MIT
