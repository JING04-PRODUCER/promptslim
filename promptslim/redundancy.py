"""冗余检测与剔除 v2 — 代码保护 + 上下文感知

改进点:
1. 代码/结构化文本保护：检测代码特征，跳过压缩
2. 上下文感知的英文填充词删除：actually/basically 等在句首/独立使用时删除
3. 更激进的中文口语规则：删除"那个"、"就是"等口头禅（含前后逗号的场景）
4. 中文冗余句式压缩：更多废话句式 → 简洁表达
5. 智能标点压缩：连续逗号、多余句号等
"""

from __future__ import annotations

import re


# ============================================================
# 代码/结构化文本检测
# ============================================================

_STRONG_CODE_PATTERNS = [
    r"^\s*(def |class |import |from |return |func |var |let |const |public |private |void |int |float |double |string |bool )",
    r"[{}\[\]]",
    r"->\s*\w",
    r":\s*\w.*[,)]",
]


def _is_code_like(text: str) -> bool:
    """检测文本是否像代码或结构化内容，如果是则跳过压缩"""
    if not text.strip():
        return False

    zh_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if len(text) > 0 and zh_count / len(text) > 0.3:
        return False

    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False

    strong_match_lines = 0
    for line in lines:
        for pattern in _STRONG_CODE_PATTERNS:
            if re.search(pattern, line):
                strong_match_lines += 1
                break

    if strong_match_lines / len(lines) > 0.5:
        return True

    non_empty_lines = [l for l in lines if l.strip()]
    if not non_empty_lines:
        return False
    indented = sum(1 for l in non_empty_lines if l.startswith(("    ", "\t")))
    if len(non_empty_lines) >= 3 and indented / len(non_empty_lines) > 0.4:
        return True

    return False


# ============================================================
# 英文冗余模式 v2 — 上下文感知
# ============================================================

EN_REDUNDANCY_V2 = [
    # 纯填充词（始终删除）
    (r"\b(um|uh|er|ah|hmm|mmm)\b[,.]?\s*", ""),

    # 冗余开场句式（始终删除）
    (r"\b(please note that|it is worth noting that|it should be noted that|it is important to note that)\s*", ""),
    (r"\b(I would like to|I want to|I need to|I must)\s+", "I "),
    (r"\b(in order to)\s+", "to "),
    (r"\b(due to the fact that)\b", "because"),
    (r"\b(at this point in time)\b", "now"),
    (r"\b(in the event that)\b", "if"),
    (r"\b(has the ability to)\b", "can"),
    (r"\b(in a timely manner)\b", "quickly"),
    (r"\b(take into consideration)\b", "consider"),
    (r"\b(for the purpose of)\b", "to"),
    (r"\b(in spite of the fact that)\b", "although"),
    (r"\b(on account of the fact that)\b", "because"),
    (r"\b(with regard to|with respect to|in relation to)\b", "regarding"),
    (r"\b(it goes without saying that)\b", ""),
    (r"\b(as a matter of fact)\b", ""),
    (r"\b(at the end of the day)\b", ""),
    (r"\b(needless to say)\b", ""),

    # 上下文感知：句首/独立使用的填充词
    (r"(?:^|[.!?]\s*)(basically|literally|honestly|frankly|obviously|clearly|surely)\s+", ""),
    (r"(?:^|[.!?]\s*)actually\s+", ""),
    (r"(?:^|[.!?]\s*)(just|simply)\s+", ""),
    # 逗号包裹的填充词
    (r"[,]\s*(basically|literally|honestly|frankly|actually|just|simply|really)\s*[,]\s*", ", "),

    # I + 填充词 + verb
    (r"\bI\s+(basically|literally|honestly|frankly|just|simply|really|kind of|sort of)\s+", "I "),
    (r"\bI\s+actually\s+", "I "),

    # 重复修饰词（始终删除）
    (r"\b(very|really|quite|extremely|highly|absolutely|totally|completely|definitely|super|incredibly)\s+", ""),

    # 多余开场/结尾
    (r"\b(Thank you for your question|Thanks for asking|Great question)\s*[,.!]\s*", ""),
    (r"\b(I hope this helps|Let me know if you have questions|Please let me know|Hope that helps|Feel free to ask|Don't hesitate to ask)\s*[.!]?\s*", ""),
    (r"\b(Of course|Certainly|Sure thing|Absolutely)\s*[,.!]\s*", ""),
    (r"\bI think that\s+", "I think "),
    (r"\bI believe that\s+", "I believe "),
    (r"\bI feel like\s+", ""),

    # kind of / sort of
    (r"\b(kind of|sort of)\s+", ""),

    # 重复词
    (r"\b(very)\s+(very)\s+", "very "),
    (r"\b(really)\s+(really)\s+", "really "),
    (r"\b(so)\s+(so)\s+", "so "),
]

EN_CLEANUP_V2 = [
    (r"\s{2,}", " "),
    (r"^\s+", ""),
    (r"\s+$", ""),
    (r"\s([,.!?;:])", r"\1"),
]


# ============================================================
# 中文冗余模式 v2 — 更激进但安全
# ============================================================

ZH_REDUNDANCY_V2 = [
    # 纯语气填充词
    (r"[嗯啊哦额呃唉哎啧]", ""),
    (r"哈{2,}", ""),

    # 口头禅（含逗号包裹的也删除）
    (r"[，,]?\s*那个\s*[，,]?", ""),
    (r"[，,]?\s*就是说\s*[，,]?", ""),
    (r"[，,]?\s*怎么说呢\s*[，,]?", ""),
    (r"[，,]?\s*然后呢\s*[，,]?", ""),
    (r"[，,]?\s*对吧\s*[，,?？]?", ""),
    (r"[，,]?\s*是吧\s*[，,?？]?", ""),
    (r"[，,]?\s*你知道吧\s*[，,?？]?", ""),
    (r"[，,]?\s*你懂吧\s*[，,?？]?", ""),
    (r"[，,]?\s*你懂的\s*[，,?？]?", ""),
    (r"[，,]?\s*你知道吗\s*[，,?？]?", ""),
    (r"[，,]?\s*其实吧\s*[，,]?", ""),
    (r"[，,]?\s*说实话\s*[，,]?", ""),
    (r"[，,]?\s*老实说\s*[，,]?", ""),

    # 双重/三重冗余修饰
    (r"(非常|特别|极其|十分|相当|超级|特别地|极其地)\1+", r"\1"),
    (r"(真的)\1+", r"\1"),
    (r"(完全|彻底|绝对)\1+", r"\1"),
    (r"(好)\1{2,}", r"好"),

    # 冗余句式压缩
    (r"我想说的是[，,]?", ""),
    (r"我觉得吧[，,]?", "我觉得"),
    (r"需要注意的是[，,]?", ""),
    (r"值得注意的是[，,]?", ""),
    (r"值得关注的是[，,]?", ""),
    (r"事实上[，,]?", ""),
    (r"实际上[，,]?", ""),
    (r"客观来讲[，,]?", ""),
    (r"严格来说[，,]?", ""),
    (r"总的来说[，,]?", ""),
    (r"总而言之[，,]?", ""),
    (r"一言以蔽之[，,]?", ""),

    # 长匹配礼貌结束语
    (r"希望对你有所帮助[。！!？?]*", ""),
    (r"希望能帮到你[。！!？?]*", ""),
    (r"如有问题请随时联系[。！!？?]*", ""),
    (r"如有疑问请随时联系[。！!？?]*", ""),
    (r"欢迎随时提问[。！!？?]*", ""),
    (r"欢迎随时咨询[。！!？?]*", ""),
    (r"真的非常感谢[！!。]*", ""),
    (r"感谢您的帮助[。！!]*", ""),
    (r"感谢您的耐心[。！!]*", ""),
    (r"如有不当之处还请多多指教[。！!]*", ""),
    (r"如有不当之处，还请多多指教[。！!]*", ""),

    # 重复标点
    (r"([。！？，,\.\!\?])\1+", r"\1"),

    # 多余空白
    (r"\s{2,}", " "),
]

ZH_CLEANUP_V2 = [
    (r"的的", "的"),
    (r"地地", "地"),
    (r"了了", "了"),
    (r"，,", "，"),
    (r"，，{2,}", "，"),
    # CJK 字符间空白删除
    (r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", ""),
    (r"(?<=[\u4e00-\u9fff])\s+(?=[，。！？、；：""''）】》])", ""),
    (r"(?<=[，。！？])\s+(?=[，。！？])", ""),
    # 逗号开头
    (r"^[，,]\s*", ""),
    # 连续逗号
    (r"，{2,}", "，"),
    # 逗号后紧跟句号
    (r"，。", "。"),
]


# ============================================================
# 公共 API — 保持向后兼容
# ============================================================

def strip_redundancy_en(text: str) -> tuple[str, int, int]:
    """移除英文冗余词 v2 — 上下文感知"""
    original = text
    removed_words = 0
    for pattern, replacement in EN_REDUNDANCY_V2:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        removed_words += len(matches)
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    for pattern, replacement in EN_CLEANUP_V2:
        text = re.sub(pattern, replacement, text)
    removed_chars = len(original) - len(text)
    return text, removed_chars, removed_words


def strip_redundancy_zh(text: str) -> tuple[str, int, int]:
    """移除中文冗余词 v2 — 更激进但安全"""
    original = text
    for pattern, replacement in ZH_REDUNDANCY_V2:
        text = re.sub(pattern, replacement, text)
    for pattern, replacement in ZH_CLEANUP_V2:
        text = re.sub(pattern, replacement, text)
    text = text.strip()
    removed_chars = len(original) - len(text)
    return text, removed_chars, 0


def strip_redundancy(text: str) -> tuple[str, int, int]:
    """自动检测语言并移除冗余 v2 — 含代码保护"""
    if not text or not text.strip():
        return text, 0, 0

    # 代码检测
    if _is_code_like(text):
        return text, 0, 0

    zh_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    total = len(text)
    if total == 0:
        return text, 0, 0
    zh_ratio = zh_count / total

    if 0.1 < zh_ratio < 0.9:
        t1, c1, w1 = strip_redundancy_zh(text)
        t2, c2, w2 = strip_redundancy_en(t1)
        return t2, c1 + c2, w1 + w2
    elif zh_ratio >= 0.9:
        return strip_redundancy_zh(text)
    else:
        return strip_redundancy_en(text)
