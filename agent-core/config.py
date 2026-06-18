"""
AgentOrchestrator - Python Agent Core 配置模块

管理所有环境变量和应用配置，支持 .env 文件覆盖。
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用
    app_name: str = "AgentOrchestrator"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据库
    database_url: str = "postgresql+asyncpg://ao_user:changeme@localhost:5432/agent_orchestrator"
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 工具执行
    tool_timeout_seconds: int = 30
    tool_max_retries: int = 3
    tool_retry_backoff: float = 1.5

    # 工作流
    max_concurrent_agents: int = 10
    workflow_checkpoint_ttl: int = 3600

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
