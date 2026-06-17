# PromptSlim

提示词瘦身工具。调 API 之前去掉废话，省 Token。

## 为什么做

经常写 prompt 的时候不自觉地加了很多"嗯""那个""非常非常"之类的词，这些词吃 Token 但对语义没什么贡献。另外聊天记录一长，Token 数就爆了。

## 能做什么

**规则模式**（离线，不调 API）：
- 中英文 40 多种冗余模式，正则匹配去掉
- 纯语气词、重复修饰词、啰嗦句式、固定礼貌结束语
- 用 tiktoken 精确算 Token 数，支持 GPT/Claude/DeepSeek/百炼

**智能模式**（调 LLM 压缩）：
- 调 API 做语义级压缩，保留关键信息，适合长文本和聊天历史

实测：中文口语省 34%，英文口语省 59%。

## 安装

```bash
pip install git+https://github.com/JING04-PRODUCER/promptslim.git
```

## 怎么用

Python 里一行：

```python
from promptslim import quick_slim

report = quick_slim("嗯那个我想说的是这个功能非常非常好用对吧")
print(f"省了 {report.savings_pct}% Token")
```

命令行：

```bash
promptslim count "你好世界" -m gpt-4o       # 看 Token 数
promptslim slim prompt.txt -o slimmed.txt     # 规则瘦身
promptslim smart long_text.txt -m gpt-4o-mini # 智能压缩
promptslim compare old.txt new.txt            # 对比
```

## 和 AI Cost Sentinel 配合

调 API 前先用 PromptSlim 瘦身，省 Token。调 API 时走 Sentinel 代理，追踪实际费用。一个省钱一个记账。

## 项目结构

```
promptslim/
  __init__.py
  cli.py          # 命令行
  compressor.py   # 规则 + LLM 双模式压缩
  redundancy.py   # 冗余检测规则
  reporter.py     # 费用报告
  tokenizer.py    # 多模型 Token 计数
tests/
```

## License

MIT
