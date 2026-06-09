"""AI Paper Summarizer."""

import json
import logging
import urllib.request
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}

def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}

def summarize_paper(doi_or_title: str) -> dict:
    """Fetch a paper and provide a summary."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(doi_or_title)}&limit=1&fields=title,abstract,tldr,authors,year,url"
        req = urllib.request.Request(url, headers={"User-Agent": "SIRI-Research-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            
        if not data.get("data"):
            return _err("Paper not found.")
            
        paper = data["data"][0]
        
        return _ok({
            "title": paper.get("title"),
            "year": paper.get("year"),
            "authors": [a.get("name") for a in paper.get("authors", [])],
            "tldr": paper.get("tldr", {}).get("text", "No TLDR available."),
            "abstract": paper.get("abstract"),
            "url": paper.get("url")
        })
    except Exception as e:
        return _err(f"Summarization failed: {e}")
