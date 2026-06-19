"""内置工具函数"""


async def read_file(filepath: str) -> dict:
    """读取文件内容，返回文本"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filepath": filepath, "content": content}
    except Exception as e:
        return {"error": str(e)}


async def execute_sql(query: str) -> dict:
    """执行 SQL 查询，返回结果"""
    return {"query": query, "result": "SQL 执行暂未实现"}


async def web_search(query: str, max_results: int = 5) -> dict:
    """搜索互联网获取最新信息，返回网页标题、URL和摘要"""
    max_results = min(max(max_results, 1), 20)
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:300],
                })
        return {"results": results, "query": query}
    except ImportError:
        return {"error": "duckduckgo_search 未安装"}
    except Exception as e:
        return {"error": f"搜索失败: {str(e)}"}
