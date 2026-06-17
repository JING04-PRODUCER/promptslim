"""
工具模块单元测试
"""
from __future__ import annotations

import json
import tempfile
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registry import ToolRegistry, ToolMetadata, ToolParameter, tool_registry
from tools.file_reader import read_file, _detect_encoding


class TestToolRegistry:
    """工具注册中心测试"""

    def setup_method(self):
        ToolRegistry.reset()

    def test_register_and_get(self):
        meta = ToolMetadata(name="test_tool", description="A test tool")
        handler = lambda x: x

        tool_registry.register(meta, handler)
        entry = tool_registry.get("test_tool")

        assert entry is not None
        assert entry[0].name == "test_tool"
        assert entry[0].description == "A test tool"

    def test_list_by_category(self):
        tool_registry.register(
            ToolMetadata(name="db1", description="DB tool", category="database"),
            lambda: None,
        )
        tool_registry.register(
            ToolMetadata(name="file1", description="File tool", category="file"),
            lambda: None,
        )

        db_tools = tool_registry.list(category="database")
        assert len(db_tools) == 1
        assert db_tools[0]["name"] == "db1"

        all_tools = tool_registry.list()
        assert len(all_tools) == 2

    def test_to_openai_tools(self):
        meta = ToolMetadata(
            name="search",
            description="Search the web",
            parameters=[
                ToolParameter("query", "string", "Search query", required=True),
                ToolParameter("limit", "integer", "Max results", required=False),
            ],
        )
        tool_registry.register(meta, lambda q, limit=10: "results")

        openai_format = tool_registry.to_openai_tools()
        assert len(openai_format) == 1
        func = openai_format[0]["function"]
        assert func["name"] == "search"
        assert "query" in func["parameters"]["required"]


class TestFileReader:
    """文件读取工具测试"""

    def test_read_text_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("line1\nline2\nline3\nline4\nline5")
            tmp = f.name

        try:
            result = read_file(tmp, max_lines=3)
            assert result["type"] == "text"
            assert result["line_count"] == 3
            assert "line1" in result["content"]
            assert "line4" not in result["content"]
        finally:
            os.unlink(tmp)

    def test_read_json_file(self):
        data = {"name": "test", "value": 42}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            tmp = f.name

        try:
            result = read_file(tmp)
            assert result["type"] == "json"
            assert '"name": "test"' in result["content"]
        finally:
            os.unlink(tmp)

    def test_read_nonexistent_file(self):
        result = read_file("/nonexistent/path/file.txt")
        assert "error" in result

    def test_encoding_detection(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="gbk") as f:
            f.write("中文测试")
            tmp = f.name

        try:
            enc = _detect_encoding(tmp)
            assert enc in ("gbk", "gb2312", "gb18030", "utf-8")
        finally:
            os.unlink(tmp)

    def test_start_line_offset(self):
        content = "\n".join(f"line{i}" for i in range(10))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name

        try:
            result = read_file(tmp, start_line=5, max_lines=3)
            assert "line5" in result["content"]
            assert "line7" in result["content"]
            assert "line8" not in result["content"]
        finally:
            os.unlink(tmp)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
