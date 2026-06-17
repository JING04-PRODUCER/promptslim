"""
Pytest 配置文件
"""
import os
import sys

# 添加 agent-core 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 从 .env 文件加载环境变量（不硬编码 API Key）
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
