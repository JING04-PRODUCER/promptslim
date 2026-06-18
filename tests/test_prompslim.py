"""PromptSlim 集成测试"""

import pytest
from promptslim.tokenizer import count_tokens, estimate_zh_tokens, count_tokens_batch
from promptslim.redundancy import strip_redundancy, strip_redundancy_en, strip_redundancy_zh
from promptslim.compressor import quick_slim
from promptslim.reporter import SlimReport, MODEL_COST_PER_TOKEN


class TestTokenizer:
    def test_count_gpt4o(self):
        n = count_tokens("Hello, world!", "gpt-4o")
        assert n > 0
        assert n < 10

    def test_count_chinese(self):
        n = count_tokens("你好世界", "gpt-4o")
        assert n > 0

    def test_different_models(self):
        text = "The quick brown fox jumps over the lazy dog"
        gpt = count_tokens(text, "gpt-4o")
        o3 = count_tokens(text, "o3")
        # 不同编码可能不同，但都应该 > 0
        assert gpt > 0
        assert o3 > 0

    def test_estimate_zh(self):
        n = estimate_zh_tokens("这是一段中文测试文本用于验证估算")
        assert 5 <= n <= 30

    def test_batch(self):
        texts = ["hello", "world", "test"]
        counts = count_tokens_batch(texts, "gpt-4o")
        assert len(counts) == 3
        assert all(c > 0 for c in counts)

    def test_empty_string(self):
        assert count_tokens("", "gpt-4o") == 0
        assert count_tokens("   ", "gpt-4o") >= 0

    def test_long_text(self):
        text = "Lorem ipsum dolor sit amet. " * 100
        n = count_tokens(text, "gpt-4o")
        assert n > 200  # 约 200+ tokens


class TestRedundancy:
    def test_english_fillers(self):
        text = "Um, I just basically really think that this is very important. Actually, I mean it."
        slim, chars, words = strip_redundancy_en(text)
        assert len(slim) < len(text)
        assert chars > 0

    def test_chinese_fillers(self):
        text = "嗯，那个我觉得这个非常非常重要，实际上就是说，对吧？"
        slim, chars, _ = strip_redundancy_zh(text)
        assert len(slim) < len(text)

    def test_auto_detect_chinese(self):
        text = "你好，那个我想说的是这个功能非常非常好用"
        slim, chars, _ = strip_redundancy(text)
        assert len(slim) < len(text)

    def test_auto_detect_english(self):
        text = "I would like to basically say that this is really really good"
        slim, chars, _ = strip_redundancy(text)
        assert len(slim) < len(text)

    def test_no_change_on_clean_text(self):
        """干净文本不应被破坏"""
        text = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        slim, _, _ = strip_redundancy(text)
        assert slim.strip() == text.strip()

    def test_double_punctuation_removal(self):
        text = "你好！！这是真的吗？？太棒了。。。"
        slim, chars, _ = strip_redundancy_zh(text)
        assert slim.count("！！") == 0
        assert slim.count("？？") == 0

    def test_in_order_to(self):
        text = "In order to save tokens, we remove redundancy."
        slim, _, _ = strip_redundancy_en(text)
        assert "In order to" not in slim.lower()

    def test_mixed_chinese_english(self):
        """混合中英文应同时触发两种规则"""
        text = "嗯，那个就是说 In order to basically say this is very very good 对吧"
        slim, chars, _ = strip_redundancy(text)
        # 中文规则应去掉 "嗯"、"就是说" 等
        # 英文规则应去掉 "In order to"、"basically"、"very" 等
        assert chars > 10
        assert "In order to" not in slim.lower()

    def test_preserve_english_spaces_in_mixed_text(self):
        """混合文本中英文单词间的空格应保留"""
        text = "你好 world 你好 very good 对吧"
        slim, _, _ = strip_redundancy(text)
        # 英文单词之间应有空格
        assert " world " in slim or " world" in slim
        # 不应把所有英文单词粘在一起


class TestCompressor:
    def test_quick_slim(self):
        text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
        report = quick_slim(text, "gpt-4o")
        assert report.tokens_saved > 0
        assert report.savings_pct > 0

    def test_quick_slim_report_dict(self):
        text = "I would like to basically say that this is really really important and very very good."
        report = quick_slim(text, "gpt-4o")
        d = report.to_dict()
        assert "tokens_saved" in d
        assert "savings_pct" in d
        assert d["tokens_saved"] > 0

    def test_no_savings_on_clean_code(self):
        text = "import numpy as np\ndef mean(x): return np.mean(x)"
        report = quick_slim(text, "gpt-4o")
        # 代码不应被"瘦身"，节省应为 0
        assert report.savings_pct == 0.0


# 用于缓存测试的长文本 (~4600 tokens with cl100k)
_LONG_SYSTEM = ("You are a highly knowledgeable AI assistant with deep expertise across many technical domains "
                "including software engineering, data science, mathematics, and system design. ") * 350


class TestCache:
    def test_analyze_simple_messages(self):
        from promptslim.cache import analyze_messages
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        analysis = analyze_messages(messages, "claude-opus-4-7")
        assert analysis.total_tokens > 0
        assert analysis.cacheable_tokens > 0
        assert analysis.cacheable_tokens < analysis.total_tokens
        assert analysis.breakpoints_used >= 1

    def test_analyze_no_cacheable(self):
        from promptslim.cache import analyze_messages
        messages = [
            {"role": "user", "content": "hi"},
        ]
        analysis = analyze_messages(messages)
        assert analysis.cacheable_tokens == 0
        assert analysis.savings_per_cached_call == 0

    def test_cache_analysis_to_dict(self):
        from promptslim.cache import analyze_messages
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        d = analyze_messages(messages, "gpt-4o").to_dict()
        assert "cacheable_tokens" in d
        assert "savings_per_cached_call_usd" in d
        assert "ttl_seconds" in d

    def test_estimate_cache_savings(self):
        from promptslim.cache import estimate_cache_savings
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "What is 2+2?"},
        ]
        result = estimate_cache_savings(messages, "claude-opus-4-7", calls_per_window=5)
        assert result["calls_per_window"] == 5
        assert result["total_savings_in_window_usd"] >= 0

    def test_build_cached_messages(self):
        from promptslim.cache import build_cached_messages
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        cached, analysis = build_cached_messages(messages)
        assert len(cached) == 2
        system_content = cached[0]["content"]
        assert isinstance(system_content, list)
        assert "cache_control" in system_content[0]

    def test_slimreport_with_cache(self):
        from promptslim import quick_slim
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Review this code."},
        ]
        text = "\n".join(m["content"] for m in messages)
        report = quick_slim(text, "claude-opus-4-7", cache_messages=messages)
        d = report.to_dict()
        assert "cache" in d
        assert "total_savings_with_cache_usd" in d

    def test_savings_over_n_calls(self):
        from promptslim.cache import analyze_messages
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        analysis = analyze_messages(messages, "claude-opus-4-7")
        s1 = analysis.savings_over_n_calls(1)
        s10 = analysis.savings_over_n_calls(10)
        assert s1 == 0.0
        assert s10 > 0

    def test_empty_messages(self):
        from promptslim.cache import analyze_messages
        analysis = analyze_messages([])
        assert analysis.total_tokens == 0
        assert analysis.cacheable_tokens == 0

    def test_savings_pct_calculation(self):
        from promptslim.cache import analyze_messages
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        analysis = analyze_messages(messages, "claude-opus-4-7")
        pct = analysis.savings_pct_per_call()
        assert 0 < pct < 100


class TestReporter:
    def test_slim_report(self):
        report = SlimReport("hello world", "hello", "gpt-4o")
        d = report.to_dict()
        assert d["original_tokens"] > d["slimmed_tokens"]
        assert d["tokens_saved"] > 0
        assert d["savings_pct"] > 0

    def test_cost_table(self):
        assert "gpt-4o" in MODEL_COST_PER_TOKEN
        assert "deepseek-chat" in MODEL_COST_PER_TOKEN
        assert "default" in MODEL_COST_PER_TOKEN
        for k, v in MODEL_COST_PER_TOKEN.items():
            assert "input" in v
            assert "output" in v
            assert v["input"] > 0

    def test_cost_per_call(self):
        text = "hello " * 1000
        from promptslim.tokenizer import count_tokens
        tokens = count_tokens(text, "gpt-4o")
        expected_cost = tokens * MODEL_COST_PER_TOKEN["gpt-4o"]["input"]
        report = SlimReport(text, "hello", "gpt-4o")
        assert report.cost_per_call_saved >= 0
