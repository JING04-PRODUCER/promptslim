"""冗余检测与剔除 — 中英文废话模式识别"""

from __future__ import annotations

import re

# 英文冗余模式
EN_REDUNDANCY = [
    # 填充词
    (r"\b(um|uh|er|ah|hmm|mmm)\b", ""),
    # 冗余修饰
    (r"\b(very|really|quite|extremely|highly|absolutely|totally|completely|definitely)\s+", ""),
    (r"\b(basically|literally|actually|honestly|frankly|obviously|clearly|surely|just|simply|somehow)\s+", ""),
    # 重复强调
    (r"\b(please note that|it is worth noting that|it should be noted that|it is important to note that)\s*", ""),
    (r"\b(I would like to|I want to|I need to|I must)\s+", ""),
    (r"\b(in order to)\s+", "to "),
    (r"\b(due to the fact that)\b", "because"),
    (r"\b(at this point in time)\b", "now"),
    (r"\b(in the event that)\b", "if"),
    (r"\b(has the ability to)\b", "can"),
    (r"\b(in a timely manner)\b", "quickly"),
    (r"\b(take into consideration)\b", "consider"),
    # 多余的开场/结尾
    (r"\b(Thank you for your question|Thanks for asking|Great question)\s*[,.!]\s*", ""),
    (r"\b(I hope this helps|Let me know if you have questions|Please let me know|Hope that helps)\s*[.!]?\s*$", ""),
    (r"\b(Of course|Certainly|Sure thing|Absolutely)\s*[,.!]\s*", ""),
]

# 中文冗余模式（保守策略：只删除明确的废话，不删内容词）
ZH_REDUNDANCY = [
    # 纯粹的语气填充词（独立出现时）
    (r"\b[嗯啊哦额呃唉哎啧呵哈]{1,2}\b", ""),
    # 口头禅（独立使用时删除，复合句中保留）
    (r"(?<![的得地])就是说(?![的得地])", ""),
    (r"(?<![的得地])怎么说呢(?![的得地])", ""),
    # 双重冗余修饰（保留单个修饰词，只删除重复堆砌的第二个）
    (r"(非常|特别|极其|十分|相当|超级)\1+", r"\1"),
    (r"(真的)\1+", r"\1"),
    (r"(完全|彻底|绝对)\1+", r"\1"),
    # 纯粹的语气后缀（不承载语义内容）
    (r"对吧$", ""),
    (r"是吧$", ""),
    (r"你懂的$", ""),
    (r"你知道吗$", ""),
    # 完全多余的句式前缀
    (r"^(需要注意的是[，,]?|值得注意的是[，,]?|值得关注的是[，,]?)", ""),
    # 固定礼貌结束语（长匹配，不易误伤）
    (r"希望对你有所帮助[。！]?", ""),
    (r"希望能帮到你[。！]?", ""),
    (r"如有问题请随时联系[。！]?", ""),
    (r"真的非常感谢[！!。]?", ""),
    # 重复标点
    (r"([。！？，,\.\!\?])\1+", r"\1"),
    # 多余空白
    (r"\s{2,}", " "),
]

# 中文修饰词被删除后可能产生的多余空格/标点
ZH_CLEANUP = [
    (r"的的", "的"),
    (r"地地", "地"),
    (r"了了", "了"),
    (r"，，", "，"),
    (r"，,", "，"),
    (r"，\s+", "，"),
    (r"\s+", ""),
]


def strip_redundancy_en(text: str) -> tuple[str, int, int]:
    """移除英文冗余词，返回 (处理后文本, 移除字符数, 移除词数)"""
    original = text
    removed_words = 0
    for pattern, replacement in EN_REDUNDANCY:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        removed_words += len(matches)
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip()
    removed_chars = len(original) - len(text)
    return text, removed_chars, removed_words


def strip_redundancy_zh(text: str) -> tuple[str, int, int]:
    """移除中文冗余词"""
    original = text
    for pattern, replacement in ZH_REDUNDANCY:
        text = re.sub(pattern, replacement, text)
    for pattern, replacement in ZH_CLEANUP:
        text = re.sub(pattern, replacement, text)
    text = text.strip()
    removed_chars = len(original) - len(text)
    return text, removed_chars, 0


def strip_redundancy(text: str) -> tuple[str, int, int]:
    """自动检测语言并移除冗余，返回 (处理后文本, 移除字符数, 移除词数)"""
    zh_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if zh_count > len(text) * 0.3:
        return strip_redundancy_zh(text)
    return strip_redundancy_en(text)
