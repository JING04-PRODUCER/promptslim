"""
SQL 查询工具 - 安全的参数化查询封装、连接池、自动重试
"""

from __future__ import annotations

from typing import Optional, Any

from tools.registry import ToolMetadata, ToolParameter, tool_registry

# 延迟导入避免数据库未连接时崩溃
_db_engine = None


def _get_engine():
    """延迟获取数据库引擎（首次调用时创建连接池）"""
    global _db_engine
    if _db_engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
        from config import get_settings

        settings = get_settings()
        _db_engine = create_async_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.debug,
        )
    return _db_engine


async def execute_sql(
    query: str,
    params: Optional[dict[str, Any]] = None,
    max_rows: int = 100,
) -> dict:
    """
    执行参数化 SQL 查询（只读）

    :param query: SQL 查询语句（仅支持 SELECT，阻止写操作）
    :param params: 参数字典（参数化查询防注入）
    :param max_rows: 最大返回行数
    :return: {"columns": [...], "rows": [...], "row_count": int}
    """
    # 安全检查：仅允许只读操作
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
        return {"error": "Only SELECT queries are allowed for safety"}

    if any(kw in query_upper for kw in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]):
        return {"error": "Write operations are not allowed"}

    try:
        from sqlalchemy import text

        engine = _get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            rows = result.fetchmany(max_rows)
            columns = list(result.keys())
            return {
                "columns": columns,
                "rows": [[str(v) for v in row] for row in rows],
                "row_count": len(rows),
            }
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}


async def list_tables() -> dict:
    """列出数据库中所有表及其结构"""
    try:
        from sqlalchemy import text

        engine = _get_engine()
        async with engine.connect() as conn:
            # PostgreSQL 系统表查询
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result.fetchall()]
            return {"tables": tables}
    except Exception as e:
        return {"error": f"List tables failed: {str(e)}"}


# 注册
sql_exec_meta = ToolMetadata(
    name="execute_sql",
    description="执行只读SQL查询（SELECT），支持参数化查询防SQL注入",
    parameters=[
        ToolParameter("query", "string", "SQL查询语句（仅允许SELECT）", required=True),
        ToolParameter("params", "object", "查询参数字典，如 {\"user_id\": 123}", required=False),
        ToolParameter("max_rows", "integer", "最大返回行数，默认100", required=False),
    ],
    category="database",
    timeout_seconds=15,
    max_retries=2,
)

list_tables_meta = ToolMetadata(
    name="list_tables",
    description="列出数据库中的所有表和视图",
    parameters=[],
    category="database",
)

tool_registry.register(sql_exec_meta, execute_sql)
tool_registry.register(list_tables_meta, list_tables)
