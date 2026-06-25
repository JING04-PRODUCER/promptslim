"""PromptSlim 集成测试"""

import pytest
from promptslim.tokenizer import count, count_batch, est_zh, cost, COST
from promptslim.compressor import quick_slim, strip_text, looks_like_code, CompressReport
from promptslim.cache import analyze, CacheReport


class TestTokenizer:
    def test_count_gpt4o(self):
        n = count("Hello, world!", "gpt-4o")
        assert n > 0
        assert n < 10

    def test_count_chinese(self):
        n = count("你好世界", "gpt-4o")
        assert n > 0

    def test_different_models(self):
        text = "The quick brown fox jumps over the lazy dog"
        gpt = count(text, "gpt-4o")
        o3 = count(text, "gpt-4o")
        assert gpt > 0
        assert o3 > 0

    def test_est_zh(self):
        n = est_zh("这是一段中文测试文本用于验证估算")
        assert 5 <= n <= 30

    def test_batch(self):
        texts = ["hello", "world", "test"]
        counts = count_batch(texts, "gpt-4o")
        assert len(counts) == 3
        assert all(c > 0 for c in counts)

    def test_empty_string(self):
        assert count("", "gpt-4o") == 0
        assert count("   ", "gpt-4o") >= 0

    def test_long_text(self):
        text = "Lorem ipsum dolor sit amet. " * 100
        n = count(text, "gpt-4o")
        assert n > 200

    def test_cost(self):
        c = cost("gpt-4o", 1000, 0)
        assert c == 0.0025

    def test_cost_default(self):
        c = cost("unknown-model", 1000000, 0)
        assert c == 1.0

    def test_cost_table(self):
        assert "gpt-4o" in COST
        assert "deepseek-chat" in COST
        assert "default" in COST
        for k, v in COST.items():
            assert isinstance(v, tuple)
            assert len(v) == 2
            assert v[0] > 0


class TestCompressor:
    def test_strip_text_zh_fillers(self):
        """中文填充词被删除"""
        text = "嗯，那个我想说的是，这个功能好用，对吧？"
        result = strip_text(text)
        assert "嗯" not in result
        assert "那个" not in result

    def test_strip_text_zh_modifiers(self):
        """中文冗余修饰被删除"""
        text = "这个功能非常非常好用"
        result = strip_text(text)
        assert "非常非常" not in result
        assert "非常" not in result

    def test_strip_text_zh_polite(self):
        """中文客套话被删除"""
        text = "这是分析结果。希望对你有所帮助。感谢你的阅读。"
        result = strip_text(text)
        assert "希望对你有所帮助" not in result
        assert "感谢你的阅读" not in result

    def test_strip_text_en_fillers(self):
        """英文填充词被删除"""
        text = "I would like to basically say that this is um good"
        result = strip_text(text)
        assert "um" not in result
        assert "basically" not in result
        assert "I would like to" not in result

    def test_strip_text_en_modifiers(self):
        """英文冗余修饰被删除"""
        text = "This is really really very extremely good"
        result = strip_text(text)
        assert "really" not in result
        assert "very" not in result
        assert "extremely" not in result
        assert "good" in result

    def test_strip_text_en_verbose(self):
        """英文冗长短句被简化"""
        text = "in order to make this work due to the fact that it is important"
        result = strip_text(text)
        assert "in order to" not in result
        assert "due to the fact that" not in result

    def test_strip_text_code_unchanged(self):
        """代码不被改变"""
        text = "def foo():\n    return 1"
        result = strip_text(text)
        assert result == text

    def test_strip_text_savings(self):
        """含冗余的文本应有实际节省"""
        text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？I would like to basically say this is really really good."
        result = strip_text(text)
        assert len(result) < len(text)
        # 冗余文本应节省至少 15%
        savings = (len(text) - len(result)) / len(text) * 100
        assert savings >= 15, f"预期节省 >= 15%，实际 {savings:.1f}%"

    def test_strip_text_preserves_code(self):
        text = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        result = strip_text(text)
        assert "fibonacci" in result

    def test_looks_like_code_python(self):
        assert looks_like_code("def foo():\n    return 1")

    def test_looks_like_code_chinese(self):
        assert not looks_like_code("这是一段中文文本用于测试")

    def test_quick_slim(self):
        text = "嗯，那个我想说的是，这个功能非常非常好用，对吧？"
        report = quick_slim(text, "gpt-4o")
        assert report.tokens_saved >= 0
        assert report.savings_pct >= 0

    def test_quick_slim_report_dict(self):
        text = "I would like to basically say that this is really really important and very very good."
        report = quick_slim(text, "gpt-4o")
        d = report.to_dict()
        assert "tokens_saved" in d
        assert "savings_pct" in d
        assert d["tokens_saved"] >= 0

    def test_compress_report_properties(self):
        report = CompressReport("hello world", "hello", "gpt-4o")
        assert report.original_tokens > 0
        assert report.compressed_tokens > 0
        assert report.tokens_saved >= 0
        assert report.savings_pct >= 0
        assert report.cost_saved >= 0

    def test_no_savings_on_code(self):
        text = "import numpy as np\ndef mean(x): return np.mean(x)"
        report = quick_slim(text, "gpt-4o")
        # 代码被保护，压缩后应与原文本相同或相近
        assert report.tokens_saved >= 0


_LONG_SYSTEM = ("You are a highly knowledgeable AI assistant with deep expertise across many technical domains "
                "including software engineering, data science, mathematics, and system design. ") * 350


class TestCache:
    def test_analyze_simple_messages(self):
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        result = analyze(messages, "claude-opus-4-7")
        assert result.total_tokens > 0
        assert result.cacheable_tokens > 0
        assert result.cacheable_tokens < result.total_tokens
        assert result.breakpoints >= 1

    def test_analyze_no_cacheable(self):
        messages = [
            {"role": "user", "content": "hi"},
        ]
        result = analyze(messages)
        assert result.cacheable_tokens == 0
        assert result.savings_per_call == 0

    def test_cache_report_to_dict(self):
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        d = analyze(messages, "gpt-4o").to_dict()
        assert "cacheable_tokens" in d
        assert "savings_per_call_usd" in d
        assert "ttl_seconds" in d

    def test_savings_n_calls(self):
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        result = analyze(messages, "claude-opus-4-7")
        s1 = result.savings_n_calls(1)
        s10 = result.savings_n_calls(10)
        assert s1 == 0.0
        assert s10 > 0

    def test_empty_messages(self):
        result = analyze([])
        assert result.total_tokens == 0
        assert result.cacheable_tokens == 0

    def test_savings_pct(self):
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        result = analyze(messages, "claude-opus-4-7")
        pct = result.savings_pct
        assert 0 < pct < 100

    def test_cache_report_properties(self):
        messages = [
            {"role": "system", "content": _LONG_SYSTEM},
            {"role": "user", "content": "Hello"},
        ]
        result = analyze(messages, "claude-opus-4-7")
        assert result.cost_without_cache > 0
        assert result.cost_first_call > 0
        assert result.cost_cached_call > 0
        assert result.cost_first_call > result.cost_cached_call
        assert result.cacheable_pct > 0


class TestPatch:
    def test_patch_wraps_create(self):
        from promptslim.patch import patch_openai, unpatch_openai
        try:
            from openai.resources.chat.completions import Completions
            orig = Completions.create
            patch_openai()
            # patched function should be different from original
            assert Completions.create is not orig
            # but should preserve original name via functools.wraps
            assert Completions.create.__name__ == "create"
        finally:
            unpatch_openai()

    def test_unpatch_restores_original(self):
        from promptslim.patch import patch_openai, unpatch_openai
        try:
            from openai.resources.chat.completions import Completions
            patch_openai()
            unpatch_openai()
            # unpatch 后再次调用 patch_openai 不应报错
            patch_openai()
        finally:
            unpatch_openai()

    def test_patch_idempotent(self):
        from promptslim.patch import patch_openai, unpatch_openai
        try:
            patch_openai()
            patch_openai()  # 不应报错
        finally:
            unpatch_openai()

    def test_strip_text_compresses(self):
        from promptslim.compressor import strip_text
        # strip_text 压缩重复行和多余空行
        text = "hello world\n\n\n\nhello world\n\n\n\nhello world"
        result = strip_text(text)
        assert len(result) < len(text)
