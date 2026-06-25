"""文本压缩器 — 40+ 中英文冗余检测模式 + LLM 深度压缩"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

import httpx

from .tokenizer import cost, count

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════
# 代码检测
# ═══════════════════════════════════════════════════
_CODE_SIGNS = [
    re.compile(r"^\s*(def |class |import |from |return |func |var |let |const )", re.M),
    re.compile(r"[{}\[\]]"),
    re.compile(r"->\s*\w"),
]

# ═══════════════════════════════════════════════════
# 英文冗余模式
# ═══════════════════════════════════════════════════
_FILLERS_EN = re.compile(
    r'\b(um|uh|hmm|er|ah|eh|like|basically|literally|actually|you\s+know|i\s+mean|right|okay|so|well)\b[,\s]*',
    re.IGNORECASE,
)
_MODIFIERS_EN = re.compile(
    r'\b(very|really|extremely|absolutely|quite|rather|highly|totally|completely|definitely|certainly|obviously)\s+',
    re.IGNORECASE,
)
_VERBOSE_EN = [
    (re.compile(r'\bin order to\b', re.IGNORECASE), 'to'),
    (re.compile(r'\bdue to the fact that\b', re.IGNORECASE), 'because'),
    (re.compile(r'\bat this point in time\b', re.IGNORECASE), 'now'),
    (re.compile(r'\bat the present time\b', re.IGNORECASE), 'now'),
    (re.compile(r'\bin the event that\b', re.IGNORECASE), 'if'),
    (re.compile(r'\bon a daily basis\b', re.IGNORECASE), 'daily'),
    (re.compile(r'\bin the near future\b', re.IGNORECASE), 'soon'),
    (re.compile(r'\bthe majority of\b', re.IGNORECASE), 'most'),
    (re.compile(r'\ba large number of\b', re.IGNORECASE), 'many'),
    (re.compile(r'\ba lot of\b', re.IGNORECASE), 'many'),
    (re.compile(r'\bhas the ability to\b', re.IGNORECASE), 'can'),
    (re.compile(r'\bis able to\b', re.IGNORECASE), 'can'),
    (re.compile(r'\bwith regard to\b', re.IGNORECASE), 'about'),
    (re.compile(r'\bin regards to\b', re.IGNORECASE), 'about'),
    (re.compile(r'\bfor the purpose of\b', re.IGNORECASE), 'for'),
    (re.compile(r'\bin the process of\b', re.IGNORECASE), ''),
    (re.compile(r'\bit is important to note that\b', re.IGNORECASE), 'note:'),
    (re.compile(r'\bplease note that\b', re.IGNORECASE), 'note:'),
    (re.compile(r'\bit should be noted that\b', re.IGNORECASE), 'note:'),
    (re.compile(r'\bit is worth noting that\b', re.IGNORECASE), 'note:'),
    (re.compile(r'\bI would like to\b', re.IGNORECASE), 'I will'),
    (re.compile(r'\bI wanted to\b', re.IGNORECASE), 'I will'),
    (re.compile(r'\bjust wanted to\b', re.IGNORECASE), ''),
    (re.compile(r'\bas a matter of fact\b', re.IGNORECASE), ''),
    (re.compile(r'\bneedless to say\b', re.IGNORECASE), ''),
    (re.compile(r'\bit goes without saying that\b', re.IGNORECASE), ''),
    (re.compile(r'\ball things considered\b', re.IGNORECASE), ''),
    (re.compile(r'\bat the end of the day\b', re.IGNORECASE), 'ultimately'),
    (re.compile(r'\bwhen all is said and done\b', re.IGNORECASE), ''),
    (re.compile(r'\bwithout a doubt\b', re.IGNORECASE), ''),
]

# ═══════════════════════════════════════════════════
# 中文冗余模式
# ═══════════════════════════════════════════════════
_FILLERS_ZH = re.compile(r'[嗯啊哦呃呢吧呀嘛呐哈呵嘿哼]，?')
_MODIFIERS_ZH = re.compile(r'(非常|特别|极其|十分|超级|相当|格外|异常|无比|万分|极度)+')
_POLITE_ZH = re.compile(
    r'(希望对你有所帮助[。！]?|感谢你的阅读[。！]?|谢谢你的关注[。！]?'
    r'|如果[你有]?任何问题[，,]请[随时]?联系[我我们][。！]?'
    r'|希望以上[内容信息]?对[你有]?所帮助[。！]?'
    r'|以上[就是是]?[我对关于].*?的[一些]?(回答|解答|回复|想法|建议|分析)[。！]?'
    r'|欢迎[大家]?[提出]?([宝贵]?意见|指正|交流|讨论)[。！]?'
    r'|希望能够?帮到[你您][。！]?'
    r'|以上[。！]?)'
)
_MARKER_ZH = re.compile(r'[那个][啥么]?[,，]?')
_DUP_CHAR_ZH = re.compile(r'([，。！？；：""''【】（）《》—…\u4e00-\u9fff])\1{1,}')
_REPEAT_SENT = re.compile(r'(.{10,})\1{1,}')

# 基础清理
_BLANK = re.compile(r"\n{3,}")
_SPACE = re.compile(r" {2,}")
_DUP_PUNCT = re.compile(r"([！!？?。.，,])\1+")


def looks_like_code(text: str) -> bool:
    if not text.strip():
        return False
    zh = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if len(text) > 0 and zh / len(text) > 0.3:
        return False
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    code_lines = sum(1 for line in lines if any(p.search(line) for p in _CODE_SIGNS))
    if code_lines / len(lines) > 0.5:
        return True
    non_empty = [line for line in lines if line.strip()]
    if len(non_empty) >= 3:
        indented = sum(1 for line in non_empty if line.startswith(("    ", "\t")))
        if indented / len(non_empty) > 0.4:
            return True
    return False


def strip_text(text: str) -> str:
    """应用 40+ 中英文冗余检测模式，在保留语义的前提下精简文本"""
    if not text or looks_like_code(text):
        return text

    result = text

    # --- 英文模式 ---
    result = _FILLERS_EN.sub('', result)
    result = _MODIFIERS_EN.sub('', result)
    for pattern, replacement in _VERBOSE_EN:
        result = pattern.sub(replacement, result)

    # --- 中文模式 ---
    result = _FILLERS_ZH.sub('', result)
    result = _MODIFIERS_ZH.sub('', result)
    result = _POLITE_ZH.sub('', result)
    result = _MARKER_ZH.sub('', result)

    # --- 通用清理 ---
    # 重复行去重
    seen = set()
    lines = []
    for line in result.split("\n"):
        s = line.strip()
        if s and s not in seen:
            seen.add(s)
            lines.append(line)
        elif not s:
            lines.append(line)
    result = "\n".join(lines)

    # 多余空行、空格、重复标点
    result = _BLANK.sub("\n\n", result)
    result = _SPACE.sub(" ", result)
    result = _DUP_PUNCT.sub(r"\1", result)

    # 去除多余逗号句号
    result = re.sub(r'[,，]\s*[,，]', '，', result)
    result = re.sub(r'[。！!？?]\s*[。！!？?]', '。', result)

    # 清理空白行首尾
    result = result.strip()

    return result


def smart_compress(
    text: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
    base_url: str = "",
    api_key: str = "",
) -> str:
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError("需要 API 密钥")
    cleaned = strip_text(text)
    try:
        if looks_like_code(cleaned):
            sys_prompt = "你是代码摘要助手。保留关键逻辑、API 接口，删除冗余注释和示例。"
        else:
            sys_prompt = "你是文本压缩助手。保留所有关键信息，删除冗余表达。"
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"压缩以下文本到{max_tokens} tokens以内：\n\n{cleaned}"},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            compressed = resp.json()["choices"][0]["message"]["content"].strip()
            if len(compressed) < len(cleaned):
                return compressed
        return cleaned
    except Exception as e:
        logger.warning(f"LLM 压缩失败: {e}")
        return cleaned


@dataclass
class CompressReport:
    original: str
    compressed: str
    model: str
    metadata: dict = field(default_factory=dict)

    @property
    def original_tokens(self) -> int:
        return count(self.original, self.model)

    @property
    def compressed_tokens(self) -> int:
        return count(self.compressed, self.model)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return round(self.tokens_saved / self.original_tokens * 100, 1)

    @property
    def cost_saved(self) -> float:
        return cost(self.model, self.tokens_saved, 0)

    def to_dict(self) -> dict:
        return {
            "original_chars": len(self.original),
            "compressed_chars": len(self.compressed),
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "tokens_saved": self.tokens_saved,
            "savings_pct": self.savings_pct,
            "cost_saved_usd": round(self.cost_saved, 6),
            "model": self.model,
        }


def quick_slim(text: str, model: str = "gpt-4o") -> CompressReport:
    """快速瘦身：仅规则去冗余，离线执行无需 API"""
    cleaned = strip_text(text)
    return CompressReport(original=text, compressed=cleaned, model=model)
