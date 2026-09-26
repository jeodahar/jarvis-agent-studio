"""
Custom tools for the agent:
- TavilySearchTool  -> FIND: searches the web, returns top links + snippets
- FirecrawlScrapeTool -> SEE: reads/extracts full clean text from a given URL
"""

import os
from crewai.tools import BaseTool
from tavily import TavilyClient
from firecrawl import FirecrawlApp


class TavilySearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for a query. Returns a list of relevant URLs with "
        "short snippets. Use this first to find sources on a topic."
    )

    def _run(self, query: str) -> str:
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        results = client.search(query=query, max_results=5)
        lines = []
        for r in results.get("results", []):
            lines.append(f"- {r['title']} ({r['url']})\n  {r['content'][:200]}")
        return "\n".join(lines) if lines else "No results found."


class FirecrawlScrapeTool(BaseTool):
    name: str = "read_webpage"
    description: str = (
        "Given a single URL, fetches and returns the full readable text "
        "content of that page. Use this after web_search to read a source "
        "in detail."
    )

    def _run(self, url: str) -> str:
        app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
        result = app.scrape_url(url, formats=["markdown"])
        content = result.markdown if hasattr(result, "markdown") else str(result)
        return content[:6000]  # keep it manageable for the LLM
