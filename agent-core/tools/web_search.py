"""
Web 搜索工具 — 免费搜索，无需 API Key
"""

from tools.registry import ToolMetadata, ToolParameter, tool_registry


async def web_search(query: str, max_results: int = 5) -> dict:
    """使用 DuckDuckGo 搜索网页

    :param query: 搜索查询词
    :param max_results: 最大返回结果数 (1-20)
    :return: {"results": [{"title": ..., "url": ..., "snippet": ...}]}
    """
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
        return {"error": "duckduckgo_search 未安装，请运行 pip install duckduckgo-search"}
    except Exception as e:
        return {"error": f"搜索失败: {str(e)}"}


web_search_meta = ToolMetadata(
    name="web_search",
    description="搜索互联网获取最新信息，返回网页标题、URL和摘要",
    parameters=[
        ToolParameter("query", "string", "搜索查询词", required=True),
        ToolParameter("max_results", "integer", "最大返回结果数 (1-20)", required=False),
    ],
    category="web",
    timeout_seconds=15,
    max_retries=2,
)

tool_registry.register(web_search_meta, web_search)
