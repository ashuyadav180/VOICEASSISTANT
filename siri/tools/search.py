"""Web search and research tools."""

from __future__ import annotations

import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def search_web(query: str, tavily_api_key: str = "") -> dict:
    if tavily_api_key:
        try:
            import urllib.request

            payload = json.dumps({
                "api_key": tavily_api_key,
                "query": query,
                "max_results": 5,
            }).encode()
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            results = [
                {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:300]}
                for r in data.get("results", [])
            ]
            return _ok({"answer": data.get("answer", ""), "results": results})
        except Exception as e:
            logger.warning("Tavily failed: %s", e)

    # Fallback: DuckDuckGo instant answer API
    try:
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return _ok({
            "answer": data.get("AbstractText", ""),
            "results": [{"title": data.get("Heading"), "url": data.get("AbstractURL"), "snippet": data.get("AbstractText")}],
        })
    except Exception as e:
        return _err(str(e))


def summarize_webpage(url: str) -> dict:
    try:
        import re

        with urllib.request.urlopen(url, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return _ok(text[:3000])
    except Exception as e:
        return _err(str(e))


def search_arxiv(query: str, max_results: int = 5) -> dict:
    try:
        url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query=all:{quote_plus(query)}&start=0&max_results={max_results}"
        )
        with urllib.request.urlopen(url, timeout=15) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            papers.append({
                "title": entry.find("atom:title", ns).text.strip().replace("\n", " "),
                "summary": entry.find("atom:summary", ns).text.strip()[:400],
                "url": entry.find("atom:id", ns).text.strip(),
                "published": entry.find("atom:published", ns).text.strip()[:10],
            })
        return _ok(papers)
    except Exception as e:
        return _err(str(e))


def search_github(query: str) -> dict:
    try:
        url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&per_page=5"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        repos = [
            {
                "name": r["full_name"],
                "url": r["html_url"],
                "stars": r["stargazers_count"],
                "description": r.get("description", ""),
            }
            for r in data.get("items", [])
        ]
        return _ok(repos)
    except Exception as e:
        return _err(str(e))


def translate_text(text: str, target_language: str) -> dict:
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single?"
            f"client=gtx&sl=auto&tl={quote_plus(target_language)}&dt=t&q={quote_plus(text)}"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        translated = "".join(part[0] for part in data[0] if part[0])
        return _ok(translated)
    except Exception as e:
        return _err(str(e))
