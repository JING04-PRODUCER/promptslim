"""
文件读取工具 - 支持多编码自动检测、大文件分块、多格式解析
"""

import json
import csv
import os
from pathlib import Path
from typing import Optional

from tools.registry import ToolMetadata, ToolParameter, tool_registry


def _detect_encoding(file_path: str) -> str:
    """自动检测文件编码 (优先 UTF-8，回退到常见中文编码)"""
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "utf-8"


def read_file(
    file_path: str,
    start_line: int = 0,
    max_lines: int = 500,
    encoding: Optional[str] = None,
) -> dict:
    """
    通用文件读取

    :param file_path: 文件绝对路径
    :param start_line: 起始行号 (0-indexed)
    :param max_lines: 最大读取行数 (防止超长)
    :param encoding: 编码（留空自动检测）
    :return: {"content": str, "line_count": int, "encoding": str, "size_bytes": int}
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    if path.stat().st_size > 50 * 1024 * 1024:
        return {"error": "File too large (>50MB), use chunked reading"}

    enc = encoding or _detect_encoding(file_path)
    suffix = path.suffix.lower()

    try:
        # JSON 结构化读取
        if suffix == ".json":
            with open(file_path, "r", encoding=enc) as f:
                data = json.load(f)
            return {
                "content": json.dumps(data, ensure_ascii=False, indent=2),
                "type": "json",
                "encoding": enc,
                "size_bytes": path.stat().st_size,
            }

        # CSV 结构化读取
        if suffix == ".csv":
            rows = []
            with open(file_path, "r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= max_lines:
                        break
                    rows.append(row)
            return {
                "content": rows,
                "type": "csv",
                "row_count": len(rows),
                "encoding": enc,
                "size_bytes": path.stat().st_size,
            }

        # 纯文本读取
        lines = []
        with open(file_path, "r", encoding=enc) as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                if i >= start_line + max_lines:
                    break
                lines.append(line.rstrip("\n"))

        return {
            "content": "\n".join(lines),
            "type": "text",
            "line_count": len(lines),
            "encoding": enc,
            "size_bytes": path.stat().st_size,
        }

    except Exception as e:
        return {"error": f"Read failed: {str(e)}"}


# 注册到工具注册中心
file_reader_meta = ToolMetadata(
    name="read_file",
    description="读取本地文件内容，支持 txt/json/csv/md/yaml 等格式，自动检测编码",
    parameters=[
        ToolParameter("file_path", "string", "文件绝对路径", required=True),
        ToolParameter("start_line", "integer", "起始行号（0开始），默认0", required=False),
        ToolParameter("max_lines", "integer", "最大读取行数，默认500", required=False),
        ToolParameter("encoding", "string", "文件编码，留空自动检测", required=False),
    ],
    category="file",
)

tool_registry.register(file_reader_meta, read_file)
